#!/usr/bin/env python3
"""md2docx -> docx-to-md round trip and md2pdf render."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SCRIPTS = REPO / "scripts"


def load(name):
    spec = importlib.util.spec_from_file_location(name.replace("-", "_"), SCRIPTS / f"{name}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


SAMPLE = """# Lease summary

Short version first. This line
continues the same paragraph.

## Terms

| Item | Value |
|---|---|
| Rent | **$2,600** per month |
| Link | [listing](https://example.com/listing) |

- First point with *italic* and `code`
  - Nested point
1. Step one
2. Step two

> A quoted note
> that spans two lines.

**Next steps**

Call the plumber.
"""


class TestRoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        (self.tmp / "in.md").write_text(SAMPLE)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def test_md_docx_md(self):
        try:
            import docx  # noqa: F401
        except ImportError:
            self.skipTest("python-docx not installed (pip install python-docx)")
        load("md2docx").convert(str(self.tmp / "in.md"), str(self.tmp / "out.docx"))
        md = load("docx-to-md").convert(self.tmp / "out.docx", self.tmp / "back.md")
        for want in ("# Lease summary", "## Terms", "| Rent | $2,600 per month |",
                     "Short version first. This line continues the same paragraph.",
                     "*italic*", "- Nested point", "1. Step one", "2. Step two",
                     "Call the plumber."):
            self.assertIn(want, md, f"missing after round trip: {want!r}")
        import docx
        d = docx.Document(str(self.tmp / "out.docx"))
        styles = [p.style.name for p in d.paragraphs]
        self.assertIn("List Bullet 2", styles)
        cell = d.tables[0].rows[1].cells[1].paragraphs[0]
        self.assertTrue(any(r.bold and "$2,600" in r.text for r in cell.runs), "table cell bold lost")
        rels = [r.target_ref for r in d.part.rels.values() if r.is_external]
        self.assertIn("https://example.com/listing", rels)

    def test_md2pdf_renders(self):
        m = load("md2pdf")
        try:
            m.find_browser()
        except SystemExit:
            self.skipTest("no Chromium on this machine")
        r = subprocess.run([sys.executable, str(SCRIPTS / "md2pdf.py"), str(self.tmp / "in.md"),
                            str(self.tmp / "out.pdf"), "Lease summary"], capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        pdf = (self.tmp / "out.pdf").read_bytes()
        self.assertTrue(pdf.startswith(b"%PDF"))
        self.assertGreater(len(pdf), 5000)
        html = (self.tmp / "out.html").read_text()
        self.assertIn("<table>", html)
        self.assertNotIn("#ff9900", html)


if __name__ == "__main__":
    unittest.main()
