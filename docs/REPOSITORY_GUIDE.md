# Repository contents

Start with [the project README](../README.md) for installation, architecture,
and usage, then [the course README](../course/README.md) for learning exercises.

## Files included in Git

- `app/`: FastAPI application, RAG pipeline, agent tools, and browser interfaces.
- `tests/`: automated tests.
- `course/`: course code, reading guides, fictional sample policies, and scenarios.
- `evaluation/`: evaluation scripts, rubrics, sample cases, and saved inputs used
  for repeatable exercises. The Week 6 answers and sealed labels are retained
  together because the agreement workflow reads and validates them.
- `docs/`: explanatory Markdown, task sets, demo instructions, and the Postman
  collection. Markdown is the source for generated document handouts.
- `requirements*.txt`, `pytest.ini`, and PowerShell scripts: dependencies and
  local run configuration.
- `.env.example`: safe settings template; copy it to `.env` for local changes.

## Files kept local

`.gitignore` excludes virtual environments, Python caches, `.env` secrets,
backups, Chroma databases under `data/`, uploaded documents, logs, generated
`course/results/` reports, document exports, and local editor settings.
Ignoring these paths does not delete their contents from your computer.

After cloning, install dependencies and copy `.env.example` to `.env` as shown
in the project README. Ensure the configured Ollama model names match the
models you have downloaded. Re-index sample policies or upload your own
documents to populate the local database. Run exercises to recreate reports.

Some older course links and the document export script refer to historical
Week 6/7 guides that are absent from the current working tree. Local backups
are deliberately excluded; those historical links may need updating before
using the older handout-generation workflow.
