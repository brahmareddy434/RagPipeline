import io
import re
from pathlib import Path
from bs4 import BeautifulSoup
from docx import Document
from docx.table import Table
from pypdf import PdfReader


class UnsupportedFile(ValueError):
    pass


# Markdown syntax is formatting, not content. Leaving "**2.1 Annual leave.**" in a chunk
# makes an exact quote hard for a small model: it quotes the prose it can read and then
# fails the quote-membership check against the stored text. We already strip tags from
# HTML; do the same for Markdown so the stored chunk is the sentence a human would read.
_MD_PATTERNS = (
    (re.compile(r"^\s{0,3}#{1,6}\s+", re.M), ""),        # headings
    (re.compile(r"\*\*(.+?)\*\*", re.S), r"\1"),          # bold
    (re.compile(r"(?<!\w)__(.+?)__(?!\w)", re.S), r"\1"),  # bold, underscores
    (re.compile(r"(?<![\w*])\*(?!\s)(.+?)(?<!\s)\*(?![\w*])", re.S), r"\1"),  # italics
    (re.compile(r"`([^`]+)`"), r"\1"),                    # inline code
    (re.compile(r"^\s{0,3}>\s?", re.M), ""),              # block quotes
    (re.compile(r"\[([^\]]+)\]\([^)]*\)"), r"\1"),        # links keep their text
)


def strip_markdown(text: str) -> str:
    for pattern, replacement in _MD_PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class DocumentLoader:
    supported = {".pdf", ".docx", ".txt", ".md", ".html", ".htm"}

    def load(self, filename: str, content: bytes) -> list[tuple[int | None, str]]:
        suffix = Path(filename).suffix.lower()
        if suffix not in self.supported:
            raise UnsupportedFile(f"Unsupported type {suffix}. Use PDF, DOCX, TXT, MD, or HTML.")
        if suffix == ".pdf":
            reader = PdfReader(io.BytesIO(content))
            return [(number, page.extract_text() or "") for number, page in enumerate(reader.pages, 1)]
        if suffix == ".docx":
            def text_of(container):
                for block in container.iter_inner_content():
                    if isinstance(block, Table):
                        for row in block.rows:
                            yield " | ".join(" ".join(text_of(cell)) for cell in row.cells)
                    else:
                        yield block.text
            return [(None, "\n".join(text_of(Document(io.BytesIO(content)))))]
        text = content.decode("utf-8", errors="replace")
        if suffix in {".html", ".htm"}:
            soup = BeautifulSoup(text, "html.parser")
            for node in soup(["script", "style", "noscript"]):
                node.decompose()
            text = soup.get_text("\n")
        elif suffix == ".md":
            text = strip_markdown(text)
        return [(None, text)]
