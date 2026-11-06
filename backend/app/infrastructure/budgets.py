"""Per-run provider admission control; deadlines also wrap tools and memory in the host."""
import json
from contextvars import ContextVar
from app.schemas import usd_cost

active_budget=ContextVar("active_budget",default=None)

class BudgetExceeded(Exception):
    def __init__(self,reason): self.reason=reason; super().__init__(reason)

class ProviderBudget:
    def __init__(self,budget,metrics): self.budget,self.metrics=budget,metrics

    def admit(self,path,payload):
        if path not in {"/api/chat","/api/embed"}: return payload,0,0
        used_prompt=sum(m.get("prompt_eval_count") or 0 for m in self.metrics)
        used_output=sum(m.get("eval_count") or 0 for m in self.metrics)
        # UTF-8 bytes plus template allowance deliberately overestimate supported local
        # byte-tokenizers. It is an admission bound, not a claimed measured prompt count.
        prompt=len(json.dumps({k:v for k,v in payload.items() if k in {"messages","format","input"}},ensure_ascii=False).encode())+512
        remaining=self.budget.max_tokens-used_prompt-used_output-prompt
        if remaining<=0: raise BudgetExceeded("token_budget")
        cost_left=self.budget.max_cost_usd-usd_cost(used_prompt+prompt,used_output)
        if cost_left<=0: raise BudgetExceeded("cost_budget")
        if path=="/api/chat":
            cap=min(payload.get("options",{}).get("num_predict",1200),remaining,int(cost_left/0.0000006))
            if cap<1: raise BudgetExceeded("cost_budget")
            payload={**payload,"options":{**payload.get("options",{}),"num_predict":cap}}
            return payload,prompt,cap
        return payload,prompt,0
