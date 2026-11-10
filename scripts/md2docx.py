#!/usr/bin/env python3
"""md2docx.py - Markdown -> .docx for deliverables (python-docx, no pandoc).

Structure handling (headings, lists, tables), italic, bold-italic and blockquotes, plus paragraph
joining (consecutive plain lines become one paragraph, as in markdown).

Handles: ATX headings (# to ######, Word levels capped at 4), whole-line **bold** as a
section heading, inline ***bold italic***, **bold**, *italic* / _italic_, `code`,
[text](url) links (body and table cells), pipe tables, fenced code blocks, bullets with
one nesting level, numbered lists, > blockquotes, --- rules (skipped).

Usage: python3 scripts/md2docx.py INPUT.md OUTPUT.docx
Python with python-docx: system python3 or any venv that has it (pip install python-docx).
Sibling tools: scripts/md2pdf.py (PDF), scripts/docx-to-md.py (reverse).
"""
import re
import sys

from docx import Document
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Pt

INLINE = re.compile(
    r"\*\*\*(?P<bi>.+?)\*\*\*"
    r"|\*\*(?P<b>.+?)\*\*"
    r"|(?<![\w*])\*(?P<i>[^*\s][^*]*?)\*(?![\w*])"
    r"|(?<!\w)_(?P<u>[^_\s][^_]*?)_(?!\w)"
    r"|`(?P<c>[^`]+)`"
    r"|\[(?P<lt>[^\]]+)\]\((?P<lu>[^)]+)\)"
)
BLOCK_START = re.compile(r"^\s*(#{1,6}\s|[-*]\s|\d+\.\s|>|```|\||---\s*$)")


def add_hyperlink(paragraph, url, text):
    r_id = paragraph.part.relate_to(
        url, "http://schemas.openxmlformats.org/officeDocument/2006/relationships/hyperlink",
        is_external=True)
    link = OxmlElement("w:hyperlink")
    link.set(qn("r:id"), r_id)
    run = OxmlElement("w:r")
    rpr = OxmlElement("w:rPr")
    color = OxmlElement("w:color")
    color.set(qn("w:val"), "0563C1")
    under = OxmlElement("w:u")
    under.set(qn("w:val"), "single")
    rpr.append(color)
    rpr.append(under)
    run.append(rpr)
    t = OxmlElement("w:t")
    t.text = text
    t.set(qn("xml:space"), "preserve")
    run.append(t)
    link.append(run)
    paragraph._p.append(link)


def add_inline(paragraph, text, italic=False):
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            paragraph.add_run(text[pos:m.start()]).italic = italic or None
        if m.group("bi") is not None:
            r = paragraph.add_run(m.group("bi"))
            r.bold = r.italic = True
        elif m.group("b") is not None:
            r = paragraph.add_run(m.group("b"))
            r.bold = True
            r.italic = italic or None
        elif m.group("i") is not None or m.group("u") is not None:
            paragraph.add_run(m.group("i") if m.group("i") is not None else m.group("u")).italic = True
        elif m.group("c") is not None:
            r = paragraph.add_run(m.group("c"))
            r.font.name = "Consolas"
            r.font.size = Pt(9.5)
        elif m.group("lt") is not None:
            add_hyperlink(paragraph, m.group("lu"), m.group("lt"))
        pos = m.end()
    if pos < len(text):
        paragraph.add_run(text[pos:]).italic = italic or None


def is_table_row(line):
    s = line.strip()
    return s.startswith("|") and s.endswith("|")


def is_sep_row(line):
    return bool(re.match(r"^\s*\|[\s:|-]+\|\s*$", line))


def split_row(line):
    return [c.strip() for c in re.split(r"(?<!\\)\|", line.strip().strip("|"))]


def convert(src, dst):
    with open(src, encoding="utf-8") as f:
        lines = f.read().replace("\r\n", "\n").split("\n")
    doc = Document()
    doc.styles["Normal"].font.name = "Calibri"
    doc.styles["Normal"].font.size = Pt(11)

    i, n = 0, len(lines)
    while i < n:
        line = lines[i]
        s = line.strip()
        if not s or re.fullmatch(r"-{3,}", s):
            i += 1
            continue

        if s.startswith("```"):
            i += 1
            code = []
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            for j, cl in enumerate(code):
                r = p.add_run(cl)
                r.font.name = "Consolas"
                r.font.size = Pt(9)
                if j < len(code) - 1:
                    r.add_break()
            continue

        if is_table_row(line) and i + 1 < n and is_sep_row(lines[i + 1]):
            header = split_row(line)
            i += 2
            rows = []
            while i < n and is_table_row(lines[i]):
                rows.append(split_row(lines[i]))
                i += 1
            t = doc.add_table(rows=1, cols=len(header))
            t.style = "Table Grid"
            for k, h in enumerate(header):
                para = t.rows[0].cells[k].paragraphs[0]
                add_inline(para, h)
                for run in para.runs:
                    run.bold = True
            for row in rows:
                cells = t.add_row().cells
                for k, val in enumerate(row[:len(cells)]):
                    add_inline(cells[k].paragraphs[0], val)
            continue

        mh = re.match(r"^(#{1,6})\s+(.*)$", s)
        if mh:
            h = doc.add_heading("", level=min(len(mh.group(1)), 4))
            add_inline(h, mh.group(2))
            i += 1
            continue

        mb = re.match(r"^\*\*([^*]+)\*\*:?$", s)
        if mb:
            doc.add_heading(mb.group(1), level=3)
            i += 1
            continue

        if s.startswith(">"):
            buf = []
            while i < n and lines[i].strip().startswith(">"):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            p = doc.add_paragraph()
            p.paragraph_format.left_indent = Pt(18)
            add_inline(p, " ".join(buf), italic=True)
            continue

        mn = re.match(r"^\s*\d+\.\s+(.*)$", line)
        if mn:
            add_inline(doc.add_paragraph(style="List Number"), mn.group(1))
            i += 1
            continue

        mbul = re.match(r"^(\s*)[-*]\s+(.*)$", line)
        if mbul:
            style = "List Bullet 2" if len(mbul.group(1)) >= 2 else "List Bullet"
            add_inline(doc.add_paragraph(style=style), mbul.group(2))
            i += 1
            continue

        buf = [s]
        i += 1
        while i < n and lines[i].strip() and not BLOCK_START.match(lines[i]):
            buf.append(lines[i].strip())
            i += 1
        add_inline(doc.add_paragraph(), " ".join(buf))

    doc.save(dst)
    return dst


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit("Usage: python3 scripts/md2docx.py INPUT.md OUTPUT.docx")
    print("wrote", convert(sys.argv[1], sys.argv[2]))
