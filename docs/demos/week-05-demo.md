# Week 05 - private trace replay and human review

Objective: W05 tooling; human open coding, taxonomy and dated prediction remain pending authentic human work.

## Start and show
Use Week 03 backend/frontend commands. Ask a policy question, then open `/#/traces`. The tenant-scoped reader shows the latest redacted trace. Raw prompts, retrieved context, schema, model/options, output and usage are captured by the provider at each actual call; request/response trace data preserves the evidence without requiring the live index.

CLI, from root:
```powershell
.\.venv\Scripts\python.exe -m course.claims_review sample logs/ask_traces.jsonl logs/claims-review --seed 42
.\.venv\Scripts\python.exe -m course.claims_review replay logs/claims-review/sample.json logs/claims-replay.json
# A human fills each human_observation, without categories or fixes, then:
.\.venv\Scripts\python.exe -m course.claims_review verify logs/claims-review
```
Sampling refuses fewer than 20 records and never invents more. Use a new directory for each attempt. It records the population, seed, sample/input hashes and source revision. Verification rejects source edits or changed samples during open coding. After observations are sealed, the human writes 4-7 modes with counts/20, percentages, severity and example IDs; commits a dated falsifiable one-mode delta prediction before a fix, plus three benchmark-limit sentences. No such notes or prediction are claimed here.

## Files, privacy and limitations
`infrastructure/redaction.py` handles CLM identifiers, configured names, structured identity fields, bearer credentials and emails recursively before `TraceLogger.write`. `REDACT_NAMES` supplies known free-text names. Arbitrary unlabelled names are not reliably recognized; production entity recognition/retention approval remains pending. Existing logs are not rewritten; export redacts them again. `/traces` and `/traces/{uuid}` use the same tenant dependency and a bounded 8MB tail. The React reader does not expose files through static URLs.

`course/claims_review.py` samples with a seeded reservoir, leaves human notes blank and replays saved model payloads only. Redacted identities and external tool state cannot be restored; replay output can differ. No new database or library. Tests exercise nested/error/raw-field redaction, bounded reads and reproducible sampling over 1,100 synthetic records; that test volume is not a claim of 1,100 real traces. See completion report for executed counts and live replay evidence.

Talk track: Capture enough context to inspect failures, remove known identifiers before saving, freeze the sample, and let a human describe what happened before choosing a fix.
