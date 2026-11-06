# Week 03 - documents and grounded answers

Objective: W03-AC01-05 on a labelled fictional corpus. Real company policy acceptance needs an authorized corpus.

## Start and show
1. Root: `.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000`. Frontend: `cd frontend; npm run dev`. Ollama needs the configured chat and embedding models.
2. Open `http://127.0.0.1:5173/#/documents`; upload `course/insurance/claims-policy-2026.txt`. The table reports indexed chunks.
3. Open Policy Q&A. Ask `What is the standard motor deductible?`. The response contains answer, citations, confidence, abstained and validation_issues. Click a source to read its exact version through the authenticated client.
4. Ask about lunar spacecraft coverage. Expected behavior is abstention, not invented coverage. Delete only the demo document when finished.
5. Show `.\.venv\Scripts\python.exe -m course.claims_retrieval chunking` and the dated evidence under `docs/demos/evidence/claims-retrieval`.

## Implementation and evidence
`services/ingestion.py` extracts/chunks before writing, hashes document versions and records chunk settings. `repositories/vector_store.py` preserves embedding revision and source metadata. `rag/loading.py` bounds DOCX expansion. React document/ask views share the API client and show empty/error/loading/results. Chroma and existing HTTP contracts remain; no relational database or new library was introduced.

Live run `20261105T145741390840Z`: 400/80 produced 12 chunks; 900/80 produced five. Both scored 12/12 hit@3. Warm retrieval p50 was 3.32ms/3.80ms. Both abstained on spacecraft coverage. The 400 answer duplicated a motor fact and added an irrelevant home deductible; the 900 answer contained the requested motor deductible only. This is a small fictional comparison, not a general quality claim. Source/fixture hashes and full outputs are saved.

26 targeted backend tests passed; five frontend tests and production build passed. Browser results are in the completion report. Separate self-review checked metadata, re-index invalidation, provider failure preservation and token-bearing source retrieval. A replaced source intentionally returns 404; originals are not retained. Crash-atomic multi-batch Chroma writes and arbitrary-PDF resource isolation remain production limitations.

Talk track: Documents become versioned chunks. Retrieval supplies the model with evidence, and Python validates quotes and creates source links. Tests establish isolation and safe failures; live evidence shows both useful answers and quality limits.
