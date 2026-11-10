#!/usr/bin/env python3
"""scripts/lint-deliverables.py: rules fire, internal refs are this ecosystem's."""
import importlib.util
import shutil
import tempfile
import unittest
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
_spec = importlib.util.spec_from_file_location("lint_deliverables", REPO / "scripts" / "lint-deliverables.py")
lint = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(lint)


class TestLint(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def msgs(self, text, email=False):
        p = self.tmp / "d.md"
        p.write_text(text)
        return [(sev, m) for sev, _, m in lint.lint(str(p), email)]

    def test_internal_references(self):
        out = self.msgs("Per know-2266 and session-2026-11-10-001, see Nate's-kb/notes and cred-016.\n")
        hits = [m for s, m in out if s == "FAIL" and "internal reference" in m]
        self.assertGreaterEqual(len(hits), 4)

    def test_mechanical_rules(self):
        text = ("Purpose: test.\nWe leverage a seamless approach \u2014 truly.\n"
                "Happy to jump on a call. Say the word and I'll run it.\n"
                "Due 2026-11-14. Next steps: none.\n")
        out = " | ".join(m for _, m in self.msgs(text))
        for want in ("banned buzzword 'leverage'", "em dash", "call/meeting offered",
                     "self-service labor offer", "ISO date in prose", "first person in a report"):
            self.assertIn(want, out)

    def test_email_relaxes_first_person(self):
        out = self.msgs("Hi Sam, I hope your week is going well. I'll send the lease Friday.\n", email=True)
        self.assertFalse(any("first person" in m for _, m in out))

    def test_code_spans_and_fences_not_linted(self):
        out = self.msgs("Purpose: x. Next steps: y.\n\n```\nleverage know-1 \u2014\n```\n")
        self.assertFalse(any("leverage" in m or "em dash" in m for _, m in out))


if __name__ == "__main__":
    unittest.main()
