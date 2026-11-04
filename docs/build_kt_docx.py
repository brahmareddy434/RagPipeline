"""Render the Week 6 and Week 7 KT Markdown files as styled .docx hand-offs.

    .\.venv\Scripts\python.exe docs/build_kt_docx.py

The Markdown files in docs/ are the source of truth; these .docx files are a convenience
for handing to a mentor. Supports the subset of Markdown the KT documents actually use:
ATX headings, paragraphs, bullet and numbered lists, pipe tables, fenced code blocks,
blockquotes, horizontal rules, and inline **bold** / *italic* / `code`.
"""
import re
import sys
from pathlib import Path

from docx import Document
from docx.enum.table import WD_CELL_VERTICAL_ALIGNMENT, WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt, RGBColor

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
SOURCES = [
    ("KT_Week6_Evals_and_Judges.md", "Week 6 KT — Evals and Error Analysis", "Track C · HR policy"),
    ("KT_Week7_Agent_Loops.md", "Week 7 KT — Agent Loops and When Not to Use Them", "Track C · HR policy"),
    ("DEMO_Week6_Evals.md", "Week 6 Demo Guide — Evals", "Track C · HR policy · Mentor walkthrough"),
    ("DEMO_Week7_Agents.md", "Week 7 Demo Guide — Agents", "Track C · HR policy · Mentor walkthrough"),
]
INLINE = re.compile(r"(\*\*.+?\*\*|`[^`]+`|\*[^*]+\*)")


def shade(cell, fill: str) -> None:
    element = OxmlElement("w:shd")
    element.set(qn("w:fill"), fill)
    cell._tc.get_or_add_tcPr().append(element)


def borders(table) -> None:
    box = OxmlElement("w:tblBorders")
    for edge in ("top", "left", "bottom", "right", "insideH", "insideV"):
        line = OxmlElement(f"w:{edge}")
        line.set(qn("w:val"), "single")
        line.set(qn("w:sz"), "4")
        line.set(qn("w:color"), "D9D9D9")
        box.append(line)
    table._tbl.tblPr.append(box)


def write_inline(paragraph, text: str, size: float = 10.5) -> None:
    """Apply bold, italic and inline code within one paragraph."""
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**") and len(part) > 4:
            run = paragraph.add_run(part[2:-2]); run.bold = True
        elif part.startswith("`") and part.endswith("`") and len(part) > 2:
            run = paragraph.add_run(part[1:-1])
            run.font.name = "Consolas"
            run.font.size = Pt(size - 1)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            run = paragraph.add_run(part[1:-1]); run.italic = True
        else:
            run = paragraph.add_run(part)
        if run.font.size is None:
            run.font.size = Pt(size)


def split_row(line: str) -> list[str]:
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def add_table(doc, rows: list[list[str]]) -> None:
    header, body = rows[0], rows[1:]
    table = doc.add_table(rows=1, cols=len(header))
    table.alignment = WD_TABLE_ALIGNMENT.CENTER
    width = 6.9 / len(header)
    for index, label in enumerate(header):
        cell = table.rows[0].cells[index]
        cell.text = ""
        cell.width = Inches(width)
        shade(cell, "1F4E78")
        run = cell.paragraphs[0].add_run(re.sub(r"[*`]", "", label))
        run.bold = True
        run.font.color.rgb = RGBColor(255, 255, 255)
        run.font.size = Pt(8.5)
    for number, row in enumerate(body):
        cells = table.add_row().cells
        for index, value in enumerate(row[:len(header)]):
            cell = cells[index]
            cell.text = ""
            cell.width = Inches(width)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.CENTER
            if number % 2:
                shade(cell, "EAF2F8")
            paragraph = cell.paragraphs[0]
            paragraph.paragraph_format.space_after = Pt(0)
            write_inline(paragraph, value, 8.5)
    borders(table)
    doc.add_paragraph()


def add_code(doc, lines: list[str]) -> None:
    paragraph = doc.add_paragraph()
    paragraph.paragraph_format.left_indent = Inches(0.25)
    paragraph.paragraph_format.space_before = Pt(4)
    paragraph.paragraph_format.space_after = Pt(8)
    run = paragraph.add_run("\n".join(lines))
    run.font.name = "Consolas"
    run.font.size = Pt(9)


def convert(doc, markdown: str) -> None:
    lines = markdown.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if stripped.startswith("```"):
            block, index = [], index + 1
            while index < len(lines) and not lines[index].strip().startswith("```"):
                block.append(lines[index])
                index += 1
            add_code(doc, block)
            index += 1
            continue

        if stripped.startswith("|") and index + 1 < len(lines) and re.fullmatch(r"\|[\s:|-]+\|", lines[index + 1].strip()):
            rows = [split_row(stripped)]
            index += 2
            while index < len(lines) and lines[index].strip().startswith("|"):
                rows.append(split_row(lines[index]))
                index += 1
            add_table(doc, rows)
            continue

        if not stripped or stripped in {"---", "***"} or stripped.startswith("<!--"):
            index += 1
            continue

        if stripped.startswith("#"):
            level = len(stripped) - len(stripped.lstrip("#"))
            # Word headings carry their own emphasis, so drop the Markdown markers
            # rather than printing literal backticks and asterisks in the heading.
            doc.add_heading(re.sub(r"[*`]", "", stripped.lstrip("# ").strip()), min(level, 3))
            index += 1
            continue

        if stripped.startswith(("- ", "* ")):
            paragraph = doc.add_paragraph(style="List Bullet")
            write_inline(paragraph, stripped[2:])
            index += 1
            continue

        if re.match(r"^\d+\.\s", stripped):
            paragraph = doc.add_paragraph(style="List Number")
            write_inline(paragraph, re.sub(r"^\d+\.\s", "", stripped))
            index += 1
            continue

        if stripped.startswith("> "):
            paragraph = doc.add_paragraph()
            paragraph.paragraph_format.left_indent = Inches(0.3)
            run = paragraph.add_run(re.sub(r"[*`]", "", stripped[2:]))
            run.italic = True
            index += 1
            continue

        paragraph = doc.add_paragraph()
        write_inline(paragraph, stripped)
        index += 1


def build(source: str, title: str, subtitle: str) -> Path:
    markdown = (DOCS / source).read_text(encoding="utf-8")
    doc = Document()
    section = doc.sections[0]
    section.page_width, section.page_height = Inches(8.5), Inches(11)
    section.top_margin = section.bottom_margin = Inches(0.7)
    section.left_margin = section.right_margin = Inches(0.8)
    doc.styles["Normal"].font.name = "Aptos"
    doc.styles["Normal"].font.size = Pt(10.5)
    doc.styles["Normal"].paragraph_format.space_after = Pt(6)
    for name, size in (("Title", 24), ("Heading 1", 16), ("Heading 2", 13), ("Heading 3", 11.5)):
        doc.styles[name].font.name = "Aptos Display"
        doc.styles[name].font.size = Pt(size)
        doc.styles[name].font.color.rgb = RGBColor(0, 0, 0)

    heading = doc.add_paragraph(style="Title")
    heading.alignment = WD_ALIGN_PARAGRAPH.CENTER
    heading.add_run(title)
    tagline = doc.add_paragraph()
    tagline.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = tagline.add_run(subtitle + "  |  Local Ollama FastAPI RAG application")
    run.bold = True
    run.font.size = Pt(11.5)

    # Drop the Markdown's own H1 and byline; the cover block above replaces them.
    body = markdown.split("\n")
    while body and (body[0].startswith("#") or body[0].startswith("**") or not body[0].strip()):
        body.pop(0)
    convert(doc, "\n".join(body))

    target = DOCS / (Path(source).stem + ".docx")
    doc.save(target)
    return target


def main() -> int:
    for source, title, subtitle in SOURCES:
        if not (DOCS / source).exists():
            print(f"missing {source}", file=sys.stderr)
            return 1
        print("wrote", build(source, title, subtitle))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
