import hashlib
import re

from app.models import Chunk


class TextChunker:
    """Splits text near paragraph/sentence boundaries with overlap."""

    def __init__(self, chunk_size: int, overlap: int):
        if chunk_size <= 0 or overlap < 0 or overlap >= chunk_size:
            raise ValueError("overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.overlap = overlap

    def split(self, source: str, pages: list[tuple[int | None, str]]) -> list[Chunk]:
        chunks: list[Chunk] = []
        for page, raw in pages:
            text = re.sub(r"\s+", " ", raw).strip()
            start = 0
            while start < len(text):
                end = min(start + self.chunk_size, len(text))
                if end < len(text):
                    boundary = text.rfind(". ", start, end)
                    if boundary <= start + self.chunk_size // 2:
                        boundary = text.rfind(" ", start, end)
                    if boundary > start + self.chunk_size // 2:
                        end = boundary + 1
                piece = text[start:end].strip()
                if piece:
                    digest = hashlib.sha256(f"{source}:{page}:{start}:{piece}".encode()).hexdigest()[:20]
                    chunks.append(Chunk(id=digest, text=piece, source=source, page=page))
                if end == len(text):
                    break
                start = max(end - self.overlap, start + 1)
        return chunks
