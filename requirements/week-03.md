# Week 03 — Retrieval and RAG

Status: draft v0.1; approval pending. Source: user requirements, 2026-11-05. Initial extraction; no approved prior specification changed.

## 1. Week and objective
Answer questions from authorized documents with traceable citations and safe abstention.

## 2. Business requirements
Make policy-backed answers depend on actual policy evidence rather than pretrained guesses.

## 3. Functional requirements
Load PDF/DOCX/TXT/MD/HTML; extract and chunk with overlap; embed/store/search top-k; filter metadata; form grounded context; cite exact evidence and abstain when unsupported; compare at least two chunk sizes.

## 4. Non-functional requirements
Preserve prior behavior, reproducible evidence, safe failures and maintainable boundaries. High audit findings block real-data production release; no automated coverage decision or payout is authorized.

## 5. Technical requirements
Reuse DocumentLoader, TextChunker, Chroma, existing embedding/provider adapters and grounding validation. Teach bi-/cross-encoders, HNSW and candidate embedding/storage choices without installing them all.

## 6. Backend requirements
Separate ingestion, retrieval, answer and source-resolution use cases; enforce upload limits, provider failure handling and tenant scoping before real documents.

## 7. Frontend requirements
React document upload/list, Q&A and clickable evidence; loading/progress, empty-index and error states; preserve old UI until parity.

## 8. Database requirements
Document/version/chunk IDs, source/page/edition metadata and embedding revision. Preserve Chroma during packaging; do not replace a populated embedding model silently.

## 9. AI Agent requirements
No agent loop required; a straightforward retrieve-then-generate workflow is sufficient.

## 10. RAG requirements
Evaluate chunk size/overlap while freezing other variables. Source links must resolve to the cited authorized version, including after safe re-indexing behavior is defined.

## 11. API requirements
Preserve /documents, /ask and /sources/{chunk_id}; add versioned aliases only during requested API migration.

## 12. Security requirements
Bound size/types, sanitize untrusted text, authorize ingestion/search/source retrieval; originals and notes must not be exposed through static routes.

## 13. Performance requirements
Record indexing and query latency, embedding batch size and retrieval k; do not promise a threshold without a declared environment/load.

## 14. Dependencies on previous weeks
Weeks 01–02; authorized corpus and chosen embedding model.

## 15. Acceptance criteria
- **W03-AC01**: Ingest an approved document corpus and answer supported questions using retrieved facts only.
- **W03-AC02**: Every supported answer has resolvable source provenance; unknown questions abstain.
- **W03-AC03**: Compare two chunk sizes with the same questions/model and retain observed results.
- **W03-AC04**: Invalid/oversized files, empty content and provider errors fail safely without corrupting the existing index.
- **W03-AC05**: Access checks cover both retrieval and direct source lookup before real-user release.

## 16. Test scenarios and traceability
Reuse test_chunker.py, test_grounded_calculations.py, test_answer_quality.py and test_course.py; add scoped source/ingestion cases in the implementation increment.

- W03-AC01 -> planned W03-V01: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W03-AC02 -> planned W03-V02: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W03-AC03 -> planned W03-V03: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W03-AC04 -> planned W03-V04: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.
- W03-AC05 -> planned W03-V05: verify the stated artifact/behavior, provenance and failure case; record actual results on execution.

Reusable source/evidence: app/document_loader.py, chunker.py, vector_store.py, retrieval.py, services.py; existing document/ask browser screen.

Current status: **Fictional claims RAG, document/source lifecycle and React views delivered; local browser journeys passed.** Real claims documents/provenance and production multi-user storage remain pending. See [cross-week traceability](../docs/architecture/traceability.md).

## 17. Out-of-scope items
OCR, malware-service selection, distributed vector deployment and a paid reranker unless separately justified.

## 18. Risks and assumptions
No approved insurance corpus supplied. Existing HR documents and small insurance fixtures cannot be described as real company coverage wording.

Amend approved scope using [change control](README.md).

## Execution amendment - 2026-11-05
Authorized implementation adds React upload/list/delete/Q&A/source views, version metadata, DOCX expansion limit and isolated live chunking comparison. W03-AC02-05 map to tests/test_claims_documents.py, tests/test_access.py, frontend/e2e/journeys.spec.ts and docs/demos/week-03-demo.md. W03-AC01 is demonstrated with explicitly fictional wording; real approved insurance wording remains an external input. Exact live outputs and limitations are retained, including the less focused 400-character answer.
