"""Tests for validate_shots.py against the atlas example.

Usage: python test_validate_shots.py   (stdlib only; uses jsonschema if installed)
"""
import copy
import json
import os
import shutil
import tempfile
import unittest

import validate_shots as vs

HERE = os.path.dirname(os.path.abspath(__file__))
EXAMPLE = os.path.join(HERE, "..", "examples", "atlas", "shots", "shots.json")

STORYBOARD = """---
format: 1920x1080
cut: film-60
---

## Frame 1 — The evening pile
- beat: B02
- medium: generated
- duration: "6s"

## Frame 2 — Six and a half hours
- beat: B03
- medium: motion

## Frame 7 — Car park
- beat: B15
- medium: mixed

## Frame 8 — Home on time
- beat: B16
- medium: generated
"""


class ShotsTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.data = json.load(open(EXAMPLE, encoding="utf-8"))

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def write(self, data, name="shots.json"):
        path = os.path.join(self.tmp, name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f) if name.endswith(".json") else f.write(data)
        return path

    def test_example_passes(self):
        self.assertEqual(vs.validate(EXAMPLE), [])

    def test_example_passes_storyboard_cross_check(self):
        sb = self.write(STORYBOARD, "STORYBOARD.md")
        self.assertEqual(vs.validate(EXAMPLE, sb), [])

    def test_ui_in_prompt_fails(self):
        data = copy.deepcopy(self.data)
        data["shots"][0]["prompt"] += " Close on the phone screen showing the photo gallery."
        errors = vs.validate(self.write(data))
        self.assertEqual(len(errors), 1, errors)
        sid, problem, _ = errors[0]
        self.assertEqual(sid, "S01")
        self.assertIn("prompt asks for", problem)
        self.assertIn("'screen'", problem)

    def test_missing_duration_fails(self):
        data = copy.deepcopy(self.data)
        del data["shots"][1]["duration_s"]
        errors = vs.validate(self.write(data))
        self.assertTrue(any(s == "S02" and "duration_s missing" in p for s, p, _ in errors), errors)

    def test_word_boundaries(self):
        self.assertEqual(vs.ui_hits("phone in pocket, rain on the windscreen, textured concrete"), [])
        self.assertTrue(vs.ui_hits("phone screen"))
        self.assertTrue(vs.ui_hits("typing on a laptop"))
        self.assertTrue(vs.ui_hits("a sign with the company logo"))
        self.assertTrue(vs.ui_hits("the app dashboard"))

    def test_shape_rules(self):
        data = copy.deepcopy(self.data)
        data["shots"][1]["id"] = "S01"          # duplicate
        data["shots"][2]["beat"] = "B2"         # bad beat
        data["shots"][3]["duration_s"] = 12     # too long
        problems = [p for _, p, _ in vs.validate(self.write(data))]
        self.assertTrue(any("duplicate id" in p for p in problems), problems)
        self.assertTrue(any("not shaped B02" in p for p in problems), problems)
        self.assertTrue(any("outside 2-10" in p for p in problems), problems)

    def test_storyboard_medium_mismatch_fails(self):
        data = copy.deepcopy(self.data)
        data["shots"][0]["beat"], data["shots"][0]["frame"] = "B03", 2
        sb = self.write(STORYBOARD, "STORYBOARD.md")
        errors = vs.validate(self.write(data), sb)
        self.assertTrue(any(s == "S01" and "medium motion" in p for s, p, _ in errors), errors)

    def test_cli_exit_codes(self):
        self.assertEqual(vs.main([EXAMPLE]), 0)
        data = copy.deepcopy(self.data)
        data["shots"][0]["subject"] = "a man typing on a laptop"
        self.assertEqual(vs.main([self.write(data)]), 1)


if __name__ == "__main__":
    unittest.main()
