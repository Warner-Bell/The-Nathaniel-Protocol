#!/usr/bin/env python3
"""docx -> Markdown, faithful conversion for working documents.

Preserves: heading levels, bullet and numbered lists (by paragraph style), tables (first row as
header), inline bold/italic, hyperlinks (as [text](url)), and callout paragraphs (as blockquotes).
Body order is preserved (paragraphs and tables interleaved as in the source).

Sibling tools: scripts/md2docx.py, scripts/md2pdf.py.

Usage: python3 scripts/docx-to-md.py INPUT.docx [OUTPUT.md]
Default output: same path with .md extension. Requires python-docx (pip install python-docx).
"""
import re
import sys
from pathlib import Path

import docx
from docx.oxml.ns import qn
from docx.table import Table
from docx.text.paragraph import Paragraph

W = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
R_ID = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}id"


def run_text(r):
    """Text of a w:r including tabs/breaks."""
    out = []
    for child in r:
        tag = child.tag
        if tag == W + "t":
            out.append(child.text or "")
        elif tag == W + "tab":
            out.append("\t")
        elif tag in (W + "br", W + "cr"):
            out.append("\n")
    return "".join(out)


def run_md(r):
    t = run_text(r)
    if not t:
        return ""
    rpr = r.find(W + "rPr")
    bold = italic = False
    if rpr is not None:
        b = rpr.find(W + "b")
        i = rpr.find(W + "i")
        bold = b is not None and b.get(W + "val", "true") not in ("0", "false")
        italic = i is not None and i.get(W + "val", "true") not in ("0", "false")
    stripped = t.strip()
    if not stripped:
        return t
    lead = t[: len(t) - len(t.lstrip())]
    trail = t[len(t.rstrip()):]
    if bold and italic:
        stripped = f"***{stripped}***"
    elif bold:
        stripped = f"**{stripped}**"
    elif italic:
        stripped = f"*{stripped}*"
    return lead + stripped + trail


def para_md(p, rels):
    """Inline markdown for a paragraph, walking runs and hyperlinks in order."""
    parts = []
    for child in p._p:
        if child.tag == W + "r":
            parts.append(run_md(child))
        elif child.tag == W + "hyperlink":
            text = "".join(run_text(r) for r in child.findall(W + "r"))
            rid = child.get(R_ID)
            url = rels.get(rid)
            parts.append(f"[{text}]({url})" if url else text)
    s = "".join(parts)
    # merge adjacent bold/italic markers split across runs: **a****b** -> **ab**
    s = re.sub(r"\*\*\*\*", "", s)
    s = re.sub(r"(?<!\*)\*\*(?!\*)", "**", s)
    return s.strip()


def table_md(t):
    rows = []
    for row in t.rows:
        cells = []
        for c in row.cells:
            txt = " ".join(x.strip() for x in c.text.split("\n") if x.strip())
            cells.append(txt.replace("|", "\\|"))
        rows.append(cells)
    if not rows:
        return []
    width = max(len(r) for r in rows)
    rows = [r + [""] * (width - len(r)) for r in rows]
    out = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
    out += ["| " + " | ".join(r) + " |" for r in rows[1:]]
    return out


def convert(src: Path, dst: Path):
    d = docx.Document(str(src))
    rels = {rid: rel.target_ref for rid, rel in d.part.rels.items() if rel.is_external}
    lines = []
    num_counter = 0
    prev_kind = None
    for child in d.element.body.iterchildren():
        if child.tag == W + "p":
            p = Paragraph(child, d)
            style = (p.style.name if p.style is not None else "Normal") or "Normal"
            text = para_md(p, rels)
            if not text:
                prev_kind = None
                continue
            m = re.match(r"Heading (\d)", style)
            if m:
                lines += ["", "#" * int(m.group(1)) + " " + text, ""]
                kind = "heading"
                num_counter = 0
            elif "Bullet" in style:
                if prev_kind not in ("bullet",):
                    lines.append("")
                lines.append(f"- {text}")
                kind = "bullet"
            elif "Number" in style:
                if prev_kind != "number":
                    lines.append("")
                    num_counter = 0
                num_counter += 1
                lines.append(f"{num_counter}. {text}")
                kind = "number"
            elif "Callout" in style or "Quote" in style:
                lines += ["", f"> {text}", ""]
                kind = "callout"
            else:
                lines += ["", text, ""]
                kind = "para"
            prev_kind = kind
        elif child.tag == W + "tbl":
            lines += [""] + table_md(Table(child, d)) + [""]
            prev_kind = "table"
    # collapse 3+ blank lines to one blank line
    text = re.sub(r"\n{3,}", "\n\n", "\n".join(lines)).strip() + "\n"
    dst.write_text(text, encoding="utf-8")
    return text


if __name__ == "__main__":
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    src = Path(sys.argv[1])
    dst = Path(sys.argv[2]) if len(sys.argv) > 2 else src.with_suffix(".md")
    out = convert(src, dst)
    print(f"wrote {dst} ({len(out.splitlines())} lines)")
