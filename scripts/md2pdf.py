#!/usr/bin/env python3
"""Markdown to PDF (styled HTML -> headless Chromium).

Neutral styling; the browser is resolved from $CHROME or a local Playwright Chromium.
This is the toolchain writing-protocol.md's Consumable Output Standard points at for the
"clean, readable PDF" on hand-off deliverables. Siblings: md2docx.py, docx-to-md.py.

Preserves headers, tables, ordered/unordered lists, bold, italic, inline code, links,
blockquotes, and horizontal rules. Writes <output>.html beside the PDF (kept: the editable
source stays the .md; the HTML is the render input).

Browser: $CHROME if set, else the newest Playwright Chromium under ~/.cache/ms-playwright,
else google-chrome / chromium on PATH.

Usage: python3 scripts/md2pdf.py <input.md> <output.pdf> ["Doc Title"]
"""
import html
import os
import re
import subprocess
import sys
import glob
import shutil


def inline(text):
    """Apply inline markdown to an already HTML-escaped string."""
    # links [text](url)  -- run before code so URLs aren't mangled
    text = re.sub(r'\[([^\]]+)\]\((https?://[^)]+)\)',
                  r'<a href="\2">\1</a>', text)
    # inline code
    text = re.sub(r'`([^`]+)`', r'<code>\1</code>', text)
    # bold
    text = re.sub(r'\*\*([^*]+)\*\*', r'<strong>\1</strong>', text)
    # italic (underscore or single star), avoid touching ** already consumed
    text = re.sub(r'(?<!\w)_([^_]+)_(?!\w)', r'<em>\1</em>', text)
    text = re.sub(r'(?<!\*)\*([^*]+)\*(?!\*)', r'<em>\1</em>', text)
    return text


def cell(text):
    return inline(html.escape(text.strip()))


def convert(md):
    lines = md.split('\n')
    out = []
    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        stripped = line.strip()

        # horizontal rule
        if re.fullmatch(r'-{3,}', stripped):
            out.append('<hr>')
            i += 1
            continue

        # headers
        m = re.match(r'(#{1,6})\s+(.*)', stripped)
        if m:
            level = len(m.group(1))
            out.append(f'<h{level}>{inline(html.escape(m.group(2)))}</h{level}>')
            i += 1
            continue

        # table: a line with | followed by a separator row of ---|---
        if '|' in line and i + 1 < n and re.match(r'^\s*\|?[\s:|-]+\|[\s:|-]*$', lines[i + 1]):
            header = [c for c in re.split(r'(?<!\\)\|', stripped.strip('|'))]
            out.append('<table><thead><tr>')
            for c in header:
                out.append(f'<th>{cell(c)}</th>')
            out.append('</tr></thead><tbody>')
            i += 2
            while i < n and '|' in lines[i]:
                cells = [c for c in re.split(r'(?<!\\)\|', lines[i].strip().strip('|'))]
                out.append('<tr>')
                for c in cells:
                    out.append(f'<td>{cell(c)}</td>')
                out.append('</tr>')
                i += 1
            out.append('</tbody></table>')
            continue

        # blockquote
        if stripped.startswith('>'):
            buf = []
            while i < n and lines[i].strip().startswith('>'):
                buf.append(lines[i].strip()[1:].strip())
                i += 1
            out.append(f'<blockquote>{inline(html.escape(" ".join(buf)))}</blockquote>')
            continue

        # unordered list
        if re.match(r'^\s*[-*]\s+', line):
            out.append('<ul>')
            while i < n and re.match(r'^\s*[-*]\s+', lines[i]):
                item = re.sub(r'^\s*[-*]\s+', '', lines[i])
                out.append(f'<li>{inline(html.escape(item))}</li>')
                i += 1
            out.append('</ul>')
            continue

        # ordered list
        if re.match(r'^\s*\d+\.\s+', line):
            out.append('<ol>')
            while i < n and re.match(r'^\s*\d+\.\s+', lines[i]):
                item = re.sub(r'^\s*\d+\.\s+', '', lines[i])
                out.append(f'<li>{inline(html.escape(item))}</li>')
                i += 1
            out.append('</ol>')
            continue

        # blank line
        if stripped == '':
            i += 1
            continue

        # paragraph (gather consecutive non-blank, non-block lines)
        buf = [stripped]
        i += 1
        while i < n and lines[i].strip() != '' and not re.match(
                r'^\s*(#{1,6}\s|[-*]\s|\d+\.\s|>|-{3,}$)', lines[i]) and '|' not in lines[i]:
            buf.append(lines[i].strip())
            i += 1
        out.append(f'<p>{inline(html.escape(" ".join(buf)))}</p>')

    return '\n'.join(out)


TEMPLATE = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><title>{title}</title>
<style>
  @page {{ size: Letter; margin: 16mm 15mm; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: "Segoe UI","Helvetica Neue",Arial,sans-serif; color:#16191f;
         font-size:11px; line-height:1.5; }}
  h1 {{ font-size:20px; color:#1f2937; border-bottom:3px solid #2563eb;
        padding-bottom:8px; margin:0 0 14px; }}
  h2 {{ font-size:15px; color:#1f2937; margin:20px 0 8px;
        border-bottom:1px solid #e4e7ea; padding-bottom:4px; }}
  h3 {{ font-size:12.5px; color:#1f2937; margin:14px 0 6px; }}
  p {{ margin:0 0 9px; }}
  ul,ol {{ margin:0 0 9px 22px; }}
  li {{ margin:2px 0; }}
  a {{ color:#0972d3; text-decoration:none; }}
  code {{ font-family:"Cascadia Code",Consolas,monospace; background:#f1f3f4;
          padding:1px 4px; border-radius:3px; font-size:10px; }}
  strong {{ color:#1f2937; }}
  blockquote {{ border-left:3px solid #2563eb; background:#eff6ff; margin:0 0 9px;
                padding:7px 12px; color:#3f4b5b; }}
  hr {{ border:none; border-top:1px solid #e4e7ea; margin:16px 0; }}
  table {{ border-collapse:collapse; width:100%; margin:0 0 12px; font-size:10px; }}
  th {{ background:#1f2937; color:#fff; text-align:left; padding:6px 9px;
        font-weight:600; }}
  td {{ border:1px solid #e4e7ea; padding:6px 9px; vertical-align:top; }}
  tbody tr:nth-child(even) {{ background:#f7f8fa; }}
</style></head><body>
{body}
</body></html>"""


def find_browser():
    """$CHROME, else newest Playwright Chromium, else a browser on PATH."""
    if os.environ.get('CHROME') and os.path.exists(os.environ['CHROME']):
        return os.environ['CHROME']
    found = glob.glob(os.path.expanduser('~/.cache/ms-playwright/chromium-*/chrome-linux*/chrome'))
    if found:
        return max(found, key=lambda p: int(re.search(r'chromium-(\d+)', p).group(1)))
    for name in ('google-chrome', 'chromium', 'chromium-browser'):
        if shutil.which(name):
            return shutil.which(name)
    sys.exit('md2pdf: no Chromium found. Set $CHROME or run: npx playwright install chromium')


def main():
    if len(sys.argv) < 3:
        sys.exit(__doc__)
    src, pdf = sys.argv[1], sys.argv[2]
    with open(src, encoding='utf-8') as f:
        md = f.read()
    title = sys.argv[3] if len(sys.argv) > 3 else os.path.basename(src)
    doc = TEMPLATE.format(title=html.escape(title), body=convert(md))

    html_path = os.path.splitext(pdf)[0] + '.html'
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(doc)

    chrome = find_browser()
    subprocess.run([chrome, '--headless=new', '--no-sandbox', '--disable-gpu',
                    '--no-pdf-header-footer', f'--print-to-pdf={pdf}',
                    f'file://{os.path.abspath(html_path)}'],
                   check=True, capture_output=True)
    print(f'HTML: {html_path}')
    print(f'PDF:  {pdf}')


if __name__ == '__main__':
    main()
