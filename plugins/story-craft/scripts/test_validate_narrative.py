"""Tests for validate_narrative.py against the atlas example.

Usage: python test_validate_narrative.py   (needs PyYAML)
"""
import os
import shutil
import tempfile
import unittest

import validate_narrative as vn

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, "..", "examples", "atlas")


class AtlasTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        for f in ("intake.md", "narrative.md"):
            shutil.copy(os.path.join(ATLAS, f), self.tmp)
        self.narrative = os.path.join(self.tmp, "narrative.md")

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def mutate(self, *pairs):
        text = open(self.narrative, encoding="utf-8").read()
        for old, new in pairs:
            self.assertIn(old, text)
            text = text.replace(old, new, 1)
        open(self.narrative, "w", encoding="utf-8").write(text)

    def test_example_passes(self):
        errors, warnings = vn.validate(self.narrative)
        self.assertEqual(errors, [])
        self.assertEqual(warnings, [])

    def test_mutated_example_fails_with_three_findings(self):
        self.mutate(
            ("evidence: E4,", "evidence: E3,"),                              # B10 proof on missing evidence
            ("id: B07, act: 2, side: could, role: pillar,", "id: B07, act: 2, side: could, role: reveal,"),
            ("beats: [B02, B06, B12, B17]", "beats: [B02, B06, B12]"),
        )
        errors, _ = vn.validate(self.narrative)
        problems = [p for _, p, _ in errors]
        self.assertEqual(len(errors), 3, problems)
        self.assertTrue(any("E3" in p and "missing" in p for p in problems))
        self.assertTrue(any("2 reveal beats" in p for p in problems))
        self.assertTrue(any("teaser-20 has no close" in p for p in problems))

    def test_out_of_order_and_unknown_beat(self):
        self.mutate(("beats: [B02, B06, B12, B17]", "beats: [B06, B02, B99, B12, B17]"))
        problems = [p for _, p, _ in vn.validate(self.narrative)[0]]
        self.assertTrue(any("out of narrative order" in p for p in problems))
        self.assertTrue(any("does not exist" in p for p in problems))

    def test_long_cut_warns(self):
        self.mutate(("beats: [B02, B06, B12, B17]", "beats: [B01, B02, B03, B05, B06, B12, B17]"))
        errors, warnings = vn.validate(self.narrative)
        self.assertEqual(errors, [])
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
