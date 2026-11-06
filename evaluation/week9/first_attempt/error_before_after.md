# Same failing call: before / after

The harness calls read_policy(POL20240001) in both arms. This first call is controlled, not model-chosen.
Subsequent steps below are unedited live model outputs when --live is used. No improvement is assumed.

## before

Description returned by tools/list:
```text
Read the policy.
```
Actual tools/call error:
```text
Error executing tool read_policy: Error 3
```
Unedited model continuation:
```json
{
  "task": "What is the damage reporting deadline for policy POL20240001? A previous tool call was replayed by the test harness, not chosen by you: {\"tool\": \"policy__read_policy\", \"arguments\": {\"policy_number\": \"POL20240001\"}}. Its actual server error was: Error executing tool read_policy: Error 3\nContinue from that error using the tool description. Never guess policy facts.",
  "session_id": null,
  "answer": "I don't know based on the uploaded documents.",
  "citations": [],
  "confidence": "low",
  "abstained": true,
  "validation_issues": [],
  "evidence": [
    {
      "id": "resource-9bd29a89f8dbb8d65ff5",
      "text": "Fictional exclusions schedule: wear and tear, deliberate damage, and pre-existing damage are excluded. This context does not decide coverage for any individual claim. Never infer approval from a claim status or an adjuster note.",
      "source": "mcp-resource:policy:policy://exclusions",
      "page": null,
      "metadata": {
        "origin": "tool"
      },
      "score": 1.0,
      "rank": 1,
      "retrieval_method": "tool",
      "semantic_score": 0.0,
      "keyword_score": 0.0,
      "fusion_score": 0.0,
      "rerank_score": null
    },
    {
      "id": "mcp-a65bb504958aee3ea37f",
      "text": "[policy:POL-2024-0002] Policy POL-2024-0002 is a fictional home policy. Report escape-of-water damage within 14 days. Submit photographs and the plumber's report. An adjuster must review the evidence before a coverage decision.\n[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "source": "mcp:policy__search_policy_documents",
      "page": null,
      "metadata": {
        "origin": "tool"
      },
      "score": 1.0,
      "rank": 2,
      "retrieval_method": "tool",
      "semantic_score": 0.0,
      "keyword_score": 0.0,
      "fusion_score": 0.0,
      "rerank_score": null
    }
  ],
  "steps": [
    {
      "index": 1,
      "thought": "Error 3 indicates a policy not found, so we need to find the policy document to understand the reporting deadline.",
      "tool": "policy__search_policy_documents",
      "arguments": {
        "query": "What is the damage reporting deadline for POL20240001?"
      },
      "observation": "[policy:POL-2024-0002] Policy POL-2024-0002 is a fictional home policy. Report escape-of-water damage within 14 days. Submit photographs and the plumber's report. An adjuster must review the evidence before a coverage decision.\n[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "ok": true,
      "latency_ms": 15372.71,
      "prompt_tokens": 525,
      "completion_tokens": 66
    },
    {
      "index": 2,
      "thought": "We have found the policy documents, but the damage reporting deadline is not explicitly stated. We need to find the specific section or clause that outlines the deadline.",
      "tool": "policy__search_policy_documents",
      "arguments": {
        "query": "What is the damage reporting deadline for POL20240001?"
      },
      "observation": "You already ran this exact call. Its result is unchanged:\n[policy:POL-2024-0002] Policy POL-2024-0002 is a fictional home policy. Report escape-of-water damage within 14 days. Submit photographs and the plumber's report. An adjuster must review the evidence before a coverage decision.\n[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "ok": true,
      "latency_ms": 14147.04,
      "prompt_tokens": 684,
      "completion_tokens": 74
    },
    {
      "index": 3,
      "thought": "We have gathered two pieces of evidence, but neither explicitly states the damage reporting deadline. We need to find a specific section or clause that outlines the deadline.",
      "tool": "policy__search_policy_documents",
      "arguments": {
        "query": "What is the damage reporting deadline for POL20240001?"
      },
      "observation": "You already ran this exact call. Its result is unchanged:\n[policy:POL-2024-0002] Policy POL-2024-0002 is a fictional home policy. Report escape-of-water damage within 14 days. Submit photographs and the plumber's report. An adjuster must review the evidence before a coverage decision.\n[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "ok": true,
      "latency_ms": 14495.31,
      "prompt_tokens": 868,
      "completion_tokens": 66
    }
  ],
  "stop_reason": "repeated_call",
  "stop_detail": "The agent kept requesting the same call.",
  "completed": false,
  "recalled_memory": [],
  "memory_summarisations": 0,
  "scratchpad_summary": "",
  "budget": {
    "max_steps": 4,
    "max_seconds": 600.0,
    "max_tokens": 16000,
    "max_cost_usd": 0.02,
    "max_tool_errors": 3,
    "max_repeats": 2,
    "scratchpad_chars": 6000
  },
  "usage": {
    "steps": 3,
    "model_calls": 5,
    "prompt_tokens": 4167,
    "completion_tokens": 337,
    "total_tokens": 4504,
    "cost_usd": 0.0010356,
    "tool_errors": 0,
    "repeated_calls": 2,
    "latency_ms": 66595.3
  }
}
```

## after

Description returned by tools/list:
```text
Read one policy's exact wording using its policy number.
        Use this when a user names a policy, not for claim status or adjuster notes.
        Pass the supplied identifier first. If the error gives a separator-only correction,
        retry that correction once. Otherwise ask the user to confirm the identifier.
        Never guess policy facts after a failed lookup and never decide claim coverage.
        
```
Actual tools/call error:
```text
Error executing tool read_policy: Policy 'POL20240001' not found. Policy numbers look like POL-YYYY-nnnn. Retry once with POL-2024-0001; only separators change.
```
Unedited model continuation:
```json
{
  "task": "What is the damage reporting deadline for policy POL20240001? A previous tool call was replayed by the test harness, not chosen by you: {\"tool\": \"policy__read_policy\", \"arguments\": {\"policy_number\": \"POL20240001\"}}. Its actual server error was: Error executing tool read_policy: Policy 'POL20240001' not found. Policy numbers look like POL-YYYY-nnnn. Retry once with POL-2024-0001; only separators change.\nContinue from that error using the tool description. Never guess policy facts.",
  "session_id": null,
  "answer": "I don't know based on the uploaded documents.",
  "citations": [],
  "confidence": "low",
  "abstained": true,
  "validation_issues": [],
  "evidence": [
    {
      "id": "resource-9bd29a89f8dbb8d65ff5",
      "text": "Fictional exclusions schedule: wear and tear, deliberate damage, and pre-existing damage are excluded. This context does not decide coverage for any individual claim. Never infer approval from a claim status or an adjuster note.",
      "source": "mcp-resource:policy:policy://exclusions",
      "page": null,
      "metadata": {
        "origin": "tool"
      },
      "score": 1.0,
      "rank": 1,
      "retrieval_method": "tool",
      "semantic_score": 0.0,
      "keyword_score": 0.0,
      "fusion_score": 0.0,
      "rerank_score": null
    },
    {
      "id": "mcp-d98e46a953286b28a8a8",
      "text": "[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "source": "mcp:policy__search_policy_documents",
      "page": null,
      "metadata": {
        "origin": "tool"
      },
      "score": 1.0,
      "rank": 2,
      "retrieval_method": "tool",
      "semantic_score": 0.0,
      "keyword_score": 0.0,
      "fusion_score": 0.0,
      "rerank_score": null
    }
  ],
  "steps": [
    {
      "index": 1,
      "thought": "The policy number provided may have incorrect separators, so we need to retry the policy__read_policy tool with a corrected policy number.",
      "tool": "policy__search_policy_documents",
      "arguments": {
        "query": "POL-2024-0001"
      },
      "observation": "[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "ok": true,
      "latency_ms": 16895.08,
      "prompt_tokens": 630,
      "completion_tokens": 65
    },
    {
      "index": 2,
      "thought": "The policy number provided may have incorrect separators, so we need to retry the policy__read_policy tool with a corrected policy number.",
      "tool": "policy__search_policy_documents",
      "arguments": {
        "query": "POL-2024-0001"
      },
      "observation": "You already ran this exact call. Its result is unchanged:\n[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "ok": true,
      "latency_ms": 12548.5,
      "prompt_tokens": 732,
      "completion_tokens": 65
    },
    {
      "index": 3,
      "thought": "The policy number provided may have incorrect separators, so we need to retry the policy__read_policy tool with a corrected policy number.",
      "tool": "policy__search_policy_documents",
      "arguments": {
        "query": "POL-2024-0001"
      },
      "observation": "You already ran this exact call. Its result is unchanged:\n[policy:POL-2024-0001] Policy POL-2024-0001 is a fictional motor policy. Report accidental vehicle damage within 7 days. Submit photographs and a repair estimate. A claim status is administrative progress, not a coverage decision.",
      "ok": true,
      "latency_ms": 11170.21,
      "prompt_tokens": 851,
      "completion_tokens": 56
    }
  ],
  "stop_reason": "repeated_call",
  "stop_detail": "The agent kept requesting the same call.",
  "completed": false,
  "recalled_memory": [],
  "memory_summarisations": 0,
  "scratchpad_summary": "",
  "budget": {
    "max_steps": 4,
    "max_seconds": 600.0,
    "max_tokens": 16000,
    "max_cost_usd": 0.02,
    "max_tool_errors": 3,
    "max_repeats": 2,
    "scratchpad_chars": 6000
  },
  "usage": {
    "steps": 3,
    "model_calls": 5,
    "prompt_tokens": 4267,
    "completion_tokens": 335,
    "total_tokens": 4602,
    "cost_usd": 0.0010544,
    "tool_errors": 0,
    "repeated_calls": 2,
    "latency_ms": 70412.83
  }
}
```

Unique successful policy reads in the model continuation: 0 before -> 0 after (cached repeated steps count once).
If both recover, report that honestly: clearer errors are not proof of an accuracy gain.
