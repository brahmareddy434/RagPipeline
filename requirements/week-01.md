# Week 01 — How a language model works

Status: v0.1 scope execution authorized by the user's "Implement Week 01" instruction on 2026-11-05. Theory materials and assistant-run evidence delivered; learner explanation and mentor acceptance pending. Original acceptance criteria are unchanged.

## 1. Week and objective
Explain next-token prediction, uncertainty, context and cost before writing application code.

## 2. Business requirements
Enable a mentor to assess the learner's model of AI limitations and appropriate model selection.

## 3. Functional requirements
Explain tokens/context limits; compare greedy and sampled decoding, temperature/top-p/top-k; distinguish static/contextual embeddings and encoder/decoder models; record a small repeatable prompting experiment.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. Theory only; no product feature introduced.

## 5. Technical requirements
Concepts include Word2Vec/GloVe, modern contextual embeddings and GPT/Claude/LLaMA families. Use the existing learning guide; date any provider/model/pricing claims and cite their source.

## 6. Backend requirements
None. No backend code or endpoint change is required in theory Week 01.

## 7. Frontend requirements
None. Existing reading pages may be used; a React application is outside this week's implementation scope.

## 8. Database requirements
None; no schema, index or dataset migration.

## 9. AI Agent requirements
Explain that an agent is application orchestration; the language model predicts outputs and does not itself execute code.

## 10. RAG requirements
Explain embedding meaning and why company facts need external evidence; no ingestion implementation.

## 11. API requirements
No API implementation; optional existing model interface experiments only.

## 12. Security requirements
Use fictional/non-sensitive prompts. Never include tokens or claimant records in learning notes.

## 13. Performance requirements
Record input/output token estimates and observed latency if measured; distinguish a reference price calculation from an actual invoice.

## 14. Dependencies on previous weeks
Initial repository/architecture review; existing course guide is a reference, not proof of learner understanding.

## 15. Acceptance criteria
- **W01-AC01**: Explain next-token prediction and give a confident-but-wrong example without claiming the model is a database.
- **W01-AC02**: Explain tokens, context window, embeddings and encoder/decoder distinctions in the learner's own words.
- **W01-AC03**: Record a prompt/temperature comparison with model/configuration and observed variability; acknowledge repeatability limits.
- **W01-AC04**: Show a worked input/output token-cost calculation with dated assumptions and distinguish local hardware cost.
- **W01-AC05**: Make no application code change for this theory-only week.

## 16. Test scenarios and traceability
Mentor oral explanation, recorded experiment review, arithmetic/citation review. Automated application tests are not required for theory notes.

| Criterion / verification | Evidence and actual status (2026-11-05) |
|---|---|
| W01-AC01 / W01-V01 | Demo concept table explains prediction and an explicitly illustrative unsupported coverage claim. Material reviewed; learner oral explanation pending. |
| W01-AC02 / W01-V02 | Demo and existing guide cover tokens/context, static/contextual embeddings, encoder/decoder and model choice. Assistant explanations supplied; learner's own words and mentor assessment pending. |
| W01-AC03 / W01-V03 | Four live local chat calls: temperatures 0, 0, 0.8, 0.8; unique answers 1/2 versus 2/2. Prompt, options, versions, digests, raw answers/counts and limitations saved in the evidence JSON. One three-text embedding batch also recorded. |
| W01-AC04 / W01-V04 | Existing cost helper: 2,000 input and 500 output tokens at hypothetical $1/$4 per million gives $0.004; 1,000 calls gives $4. Arithmetic verified; local operating cost unmeasured. |
| W01-AC05 / W01-V05 | File-hash comparison to the starting working tree verifies no application/helper/test/config/dependency or prior Week 9 evidence changes. Documentation and reviewed experimental evidence only. |

Files: [mentor guide](../docs/demos/week-01-demo.md), [experiment and verification record](../docs/demos/evidence/week-01-experiments.json), existing `course/guides/01_language_models.md` and `course/labs/foundations.py`.

Current status: **Agent-deliverable theory material and experiments complete; W01-AC01/02 human understanding and mentor acceptance remain pending.** See [cross-week traceability](../docs/architecture/traceability.md). A generic test-suite pass does not replace acceptance evidence.

## 17. Out-of-scope items
Document ingestion, tools, React implementation, database migrations, agent frameworks and cloud provisioning.

## 18. Risks and assumptions
Actual model prices change; verify if using paid comparisons. Theory cannot be certified by an autogenerated checklist.

Amend approved scope using [change control](README.md).

## Execution amendment - 2026-11-05
The explicit Week 01 instruction activates the existing theory-only scope, not later-week implementation. W01-AC01 through W01-AC05 are unchanged; their planned checks now link to actual evidence or explicit human-review gaps. No API, UI, database or runtime behavior change. Existing helpers are used as optional demonstrations, with no new application code and no claim that an assistant can certify learner understanding.
