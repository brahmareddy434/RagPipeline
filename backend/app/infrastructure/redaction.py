"""Pre-persistence redaction with an explicit identifier/field contract.

Free-text names require operator-supplied names or a structured claimant field.
This is not general-purpose entity recognition; real-data release needs that review.
"""
import re

PRIVATE_FIELDS = {"claimant_name", "insured_name", "policyholder_name", "full_name", "email", "phone", "address"}
SECRET_FIELDS = {"authorization", "token", "access_token", "api_key", "password", "secret"}


def redact(value, names=()):
    identifiers = set(n for n in names if isinstance(n,str) and len(n)>1)
    def collect(node):
        if isinstance(node,dict):
            for key,item in node.items():
                if key.lower() in PRIVATE_FIELDS | SECRET_FIELDS and isinstance(item,str) and len(item)>1:
                    identifiers.add(item)
                collect(item)
        elif isinstance(node,list):
            for item in node: collect(item)
    collect(value)
    def clean(text):
        for name in sorted(identifiers,key=len,reverse=True):
            text=re.sub(re.escape(name),"[REDACTED]",text,flags=re.I)
        text=re.sub(r"\bCLM[- _]?\d{4}[- _]?\d{4,}\b","[CLAIM_ID]",text,flags=re.I)
        text=re.sub(r"\bBearer\s+[A-Za-z0-9._~+/=-]+","Bearer [REDACTED]",text,flags=re.I)
        text=re.sub(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b","[EMAIL]",text,flags=re.I)
        return text
    def walk(node):
        if isinstance(node,dict):
            return {clean(str(k)): "[REDACTED]" if str(k).lower() in PRIVATE_FIELDS | SECRET_FIELDS else walk(v) for k,v in node.items()}
        if isinstance(node,list): return [walk(v) for v in node]
        if isinstance(node,tuple): return [walk(v) for v in node]
        return clean(node) if isinstance(node,str) else node
    return walk(value)
