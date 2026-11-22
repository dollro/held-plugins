"""Tests for check_storyboard.py against the atlas film-60 example.

Usage: python test_check_storyboard.py   (needs PyYAML)
"""
import os
import re
import shutil
import tempfile
import unittest

import check_storyboard as cs

HERE = os.path.dirname(os.path.abspath(__file__))
PLUGIN = os.path.join(HERE, "..", "..", "..")
STORYBOARD = os.path.join(PLUGIN, "examples", "atlas", "film-60", "STORYBOARD.md")
NARRATIVE = os.path.join(PLUGIN, "..", "story-craft", "examples", "atlas", "narrative.md")


class AtlasFilm60Test(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "STORYBOARD.md")
        shutil.copy(STORYBOARD, self.path)

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_check(self):
        return cs.check(self.path, NARRATIVE)

    def edit(self, fn):
        text = open(self.path, encoding="utf-8").read()
        new = fn(text)
        self.assertNotEqual(new, text)
        open(self.path, "w", encoding="utf-8").write(new)

    def test_example_passes(self):
        errors, warnings = cs.check(STORYBOARD)
        self.assertEqual(errors, [])

    def test_missing_frame_and_wrong_order_fail(self):
        def mutate(text):
            # drop frame 5 (B09); swap the beats of frames 2 and 3
            text = re.sub(r"## Frame 5 — .*?(?=## Frame 6)", "", text, flags=re.S)
            return text.replace("- beat: B03", "- beat: TMP").replace("- beat: B05", "- beat: B03") \
                       .replace("- beat: TMP", "- beat: B05")
        self.edit(mutate)
        errors, _ = self.run_check()
        problems = " ".join(f"{i} {p}" for i, p, _ in errors)
        self.assertIn("B09 no frame", problems)
        self.assertIn("out of cut order", problems)

    def test_missing_keys_fail(self):
        self.edit(lambda t: t.replace("- medium: motion\n- start: 7.0s", "- start: 7.0s", 1))
        errors, _ = self.run_check()
        self.assertTrue(any("`medium` missing" in p for _, p, _ in errors))

    def test_medium_rule_warns(self):
        self.edit(lambda t: t.replace("- beat: B12\n- medium: ui", "- beat: B12\n- medium: motion", 1))
        errors, warnings = self.run_check()
        self.assertEqual(errors, [])
        self.assertTrue(any("star beat shown as `motion`" in p for _, p, _ in warnings))

    def test_runtime_drift_warns(self):
        self.edit(lambda t: t.replace("- duration: 14s", "- duration: 34s", 1))
        errors, warnings = self.run_check()
        self.assertEqual(errors, [])
        self.assertTrue(any(i == "duration" for i, _, _ in warnings))

    def test_frontmatter_key_missing_fails(self):
        self.edit(lambda t: t.replace("cut: film-60\n", "", 1))
        errors, _ = self.run_check()
        self.assertTrue(any("`cut` missing" in p for _, p, _ in errors))


if __name__ == "__main__":
    unittest.main()
