import asyncio
from app.domain.ports import ChunkSink
from pathlib import PurePosixPath
from app.rag.grounding import ABSTENTION, validate_grounded_answer
from app.schemas import AnswerResponse, GroundedAnswer, RetrievalOptions
from app.legacy.leave_totals import annual_leave_total


class IngestionService:
    def __init__(self, loader, chunker, store: ChunkSink, max_chars=1_000_000):
        self.loader, self.chunker, self.store, self.max_chars = loader, chunker, store, max_chars

    async def ingest(self, files):
        chunks = []
        seen = set()
        for filename, content in files:
            filename = PurePosixPath(filename.replace("\\", "/")).name
            if not filename or len(filename) > 255 or filename in seen:
                raise ValueError("Each file must have a distinct filename of at most 255 characters.")
            seen.add(filename)
            pages = await asyncio.to_thread(self.loader.load, filename, content)
            if sum(len(text) for _, text in pages) > self.max_chars:
                raise ValueError("Extracted document exceeds the character limit.")
            pieces = await asyncio.to_thread(self.chunker.split, filename, pages)
            if not pieces:
                raise ValueError(f"No readable text in {filename}; scanned PDFs need OCR.")
            chunks.extend(pieces)
        await self.store.upsert(chunks)
        return len(chunks)
