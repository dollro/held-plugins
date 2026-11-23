#!/usr/bin/env python3
"""Tests for export_beats.py (with make_test_film.py as the fixture builder).

Usage:  python test_export_beats.py   (needs ffmpeg + ffprobe on PATH; skipped without them)
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import export_beats  # noqa: E402
import make_test_film  # noqa: E402

HAVE_FFMPEG = bool(shutil.which("ffmpeg") and shutil.which("ffprobe"))

STORYBOARD = """---
format: 1280x720
duration: "4.7s"
message: "Site reports, finally done on site."
cut: film-60
narrative: ../narrative.md
audio: {audio}
---

## Frame 1 — The evening pile
- beat: B02
- status: built
- duration: "1.5s"
- medium: motion
- statement: "47 photos. 3 voice memos. Zero report."

Free text below the bullets is ignored.

## Frame 2 — The reveal
- beat: B06
- duration: "2s"
- statement: "atlas"

## Frame 3 — Close
- beat: B17
- start: "3.5s"
- duration: "1.2s"
- statement: "Start a free 30-day pilot."
"""
EXPECTED = {"B02": 1.5, "B06": 2.0, "B17": 1.2}
FIELDS = {"beat", "cut", "file", "poster", "duration_s", "audio", "loopable"}


def ffprobe_duration(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=duration", "-of", "csv=p=0", path], stdout=subprocess.PIPE).stdout
    return float(out.decode().strip())


def has_audio(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "a", "-show_entries",
                          "stream=index", "-of", "csv=p=0", path], stdout=subprocess.PIPE).stdout
    return bool(out.decode().strip())


class StoryboardParsing(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="motion-qa-sb-")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, text):
        path = os.path.join(self.tmp, "STORYBOARD.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        return path

    def test_cumulative_and_explicit_start(self):
        meta, frames = export_beats.read_storyboard(self.write(STORYBOARD.format(audio="vo+music")))
        self.assertEqual(meta["cut"], "film-60")
        self.assertEqual(meta["audio"], "vo+music")
        self.assertEqual([f["beat"] for f in frames], ["B02", "B06", "B17"])
        self.assertEqual([f["start"] for f in frames], [0.0, 1.5, 3.5])
        self.assertAlmostEqual(export_beats.storyboard_end(frames), 4.7)

    def test_missing_beat_is_an_error(self):
        bad = STORYBOARD.format(audio="music").replace("- beat: B06\n", "")
        with self.assertRaises(export_beats.StoryboardError):
            export_beats.read_storyboard(self.write(bad))

    def test_missing_duration_is_an_error(self):
        bad = STORYBOARD.format(audio="music").replace('- duration: "2s"\n', "")
        with self.assertRaises(export_beats.StoryboardError):
            export_beats.read_storyboard(self.write(bad))

    def test_parse_seconds(self):
        self.assertEqual(export_beats.parse_seconds('"6s"'), 6.0)
        self.assertEqual(export_beats.parse_seconds("6.4 s"), 6.4)
        self.assertEqual(export_beats.parse_seconds("1:02.5"), 62.5)
        self.assertIsNone(export_beats.parse_seconds(""))

    def test_frame_window(self):
        self.assertEqual(export_beats.frame_window(0.0, 1.5, 25), (0, 38))
        self.assertEqual(export_beats.frame_window(1.5, 2.0, 25), (38, 88))
        self.assertEqual(export_beats.frame_window(4.0, 2.0, 25), (100, 150))


@unittest.skipUnless(HAVE_FFMPEG, "ffmpeg/ffprobe not on PATH")
class ExportBeats(unittest.TestCase):
    def setUp(self):
        self.root = tempfile.mkdtemp(prefix="motion-qa-export-")
        os.makedirs(os.path.join(self.root, "film-60"))
        self.set_storyboard("vo+music")

    def tearDown(self):
        shutil.rmtree(self.root, ignore_errors=True)

    def set_storyboard(self, audio):
        with open(os.path.join(self.root, "film-60", "STORYBOARD.md"), "w", encoding="utf-8") as f:
            f.write(STORYBOARD.format(audio=audio))

    def make_film(self, *extra):
        self.assertEqual(make_test_film.main([self.root, "--cut", "film-60", *extra]), 0)

    def export(self, *extra):
        return export_beats.main([self.root, "--cut", "film-60", *extra])

    def clips(self):
        with open(os.path.join(self.root, "renders", "clips.json"), encoding="utf-8") as f:
            return json.load(f)

    def test_export_all_beats(self):
        self.make_film()
        self.assertEqual(self.export(), 0)
        clips = self.clips()
        self.assertEqual([c["beat"] for c in clips], ["B02", "B06", "B17"])
        for c in clips:
            self.assertEqual(set(c), FIELDS)
            self.assertEqual(c["cut"], "film-60")
            self.assertEqual(c["audio"], "vo+music")
            self.assertIs(c["loopable"], False)
            for key in ("file", "poster"):
                self.assertFalse(os.path.isabs(c[key]), c[key])
                self.assertTrue(c[key].startswith("renders/beats/"), c[key])
                self.assertTrue(os.path.isfile(os.path.join(self.root, c[key])), c[key])
            mp4 = os.path.join(self.root, c["file"])
            self.assertAlmostEqual(ffprobe_duration(mp4), EXPECTED[c["beat"]], delta=0.15)
            self.assertAlmostEqual(c["duration_s"], EXPECTED[c["beat"]], delta=0.15)
            self.assertTrue(has_audio(mp4))
            self.assertGreater(os.path.getsize(os.path.join(self.root, c["poster"])), 1000)

    def test_poster_is_not_black(self):
        self.make_film()
        self.assertEqual(self.export("--beats", "B06"), 0)
        jpg = os.path.join(self.root, "renders", "beats", "B06.jpg")
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", jpg, "-vf", "scale=64:36,format=gray",
                              "-f", "rawvideo", "-"], stdout=subprocess.PIPE, check=True).stdout
        self.assertEqual(len(raw), 64 * 36)
        self.assertGreater(sum(raw) / len(raw), 24)

    def test_no_audio_film_gives_audio_none(self):
        self.make_film("--no-audio")
        self.assertEqual(self.export("--beats", "B02"), 0)
        clip = self.clips()[0]
        self.assertEqual(clip["audio"], "none")
        self.assertFalse(has_audio(os.path.join(self.root, clip["file"])))

    def test_default_audio_is_music(self):
        with open(os.path.join(self.root, "film-60", "STORYBOARD.md"), "w", encoding="utf-8") as f:
            f.write(STORYBOARD.format(audio="x").replace("audio: x\n", ""))
        self.make_film()
        self.assertEqual(self.export("--beats", "B17"), 0)
        self.assertEqual(self.clips()[0]["audio"], "music")

    def test_merge_replaces_same_beat_and_cut_keeps_others(self):
        self.make_film()
        renders = os.path.join(self.root, "renders")
        old = [{"beat": "B02", "cut": "teaser-20", "file": "renders/teaser/B02.mp4", "poster": "renders/teaser/B02.jpg",
                "duration_s": 3.0, "audio": "music", "loopable": False},
               {"beat": "B06", "cut": "film-60", "file": "stale.mp4", "poster": "stale.jpg",
                "duration_s": 9.9, "audio": "vo", "loopable": False}]
        with open(os.path.join(renders, "clips.json"), "w", encoding="utf-8") as f:
            json.dump(old, f)
        self.assertEqual(self.export("--beats", "B06,B02"), 0)
        clips = self.clips()
        self.assertEqual([(c["cut"], c["beat"]) for c in clips],
                         [("film-60", "B02"), ("film-60", "B06"), ("teaser-20", "B02")])
        b06 = next(c for c in clips if c["beat"] == "B06" and c["cut"] == "film-60")
        self.assertEqual(b06["file"], "renders/beats/B06.mp4")
        self.assertAlmostEqual(b06["duration_s"], 2.0, delta=0.15)
        self.assertEqual(clips[2], old[0])
        # a second export of another beat keeps the first ones
        self.assertEqual(self.export("--beats", "B17"), 0)
        self.assertEqual(len(self.clips()), 4)

    def test_unknown_beat_is_an_error(self):
        self.make_film()
        self.assertEqual(self.export("--beats", "B02,B99"), 1)
        self.assertFalse(os.path.exists(os.path.join(self.root, "renders", "clips.json")))

    def test_film_shorter_than_storyboard_is_an_error(self):
        self.make_film()
        film = os.path.join(self.root, "renders", "film-60.mp4")
        short = os.path.join(self.root, "renders", "short.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", film, "-t", "3", "-c", "copy", short], check=True)
        self.assertEqual(self.export("--film", "renders/short.mp4"), 1)

    def test_missing_film_is_an_error(self):
        self.assertEqual(self.export(), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)
