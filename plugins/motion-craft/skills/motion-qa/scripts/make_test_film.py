#!/usr/bin/env python3
"""Build a synthetic TEST FIXTURE film for a STORYBOARD.md, so export and checks can run without a real render.

Usage:
  make_test_film.py <motion-root> --cut film-60 [--storyboard <cut>/STORYBOARD.md]
                    [--out renders/<cut>.mp4] [--size 1280x720] [--fps 25] [--no-audio]
                    [--ffmpeg /path/to/ffmpeg]

One coloured segment per frame (in storyboard order, frame duration), labelled
"TEST FIXTURE", the beat ID and the statement (drawtext when ffmpeg has it, else no text),
a small moving marker so no segment is frozen, and a quiet sine tone (unless --no-audio).
Total length = sum of the frame durations. H.264 yuv420p, AAC, +faststart.

This stands in for a HyperFrames render when the build backend is not available. It is a
test fixture, not a generated clip: never ship it, never put it in a deck.
Exit 0 = film written, 1 = error. Stdlib only; needs ffmpeg.
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_beats import StoryboardError, frame_window, read_storyboard, run  # noqa: E402

COLOURS = ["0x1f3a5f", "0xb8860b", "0x3a1f5f", "0x2e8b57", "0x404040", "0xa0522d"]  # alternating luma, so cuts are detectable
FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    "/Library/Fonts/Arial.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]


def has_filter(ffmpeg, name):
    p = subprocess.run([ffmpeg, "-hide_banner", "-filters"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return any(line.split()[1:2] == [name] for line in p.stdout.decode("utf-8", "replace").splitlines()
               if len(line.split()) > 1)


def _esc(path):
    """Escape a path for use inside a filtergraph option value."""
    return path.replace("\\", "/").replace(":", "\\:").replace("'", "\\'")


def build(ffmpeg, frames, out, size, fps, audio=True):
    w, h = (int(x) for x in size.lower().split("x"))
    total = frame_window(frames[-1]["start"], frames[-1]["duration"], fps)[1] / fps
    use_text = has_filter(ffmpeg, "drawtext")
    font = next((f for f in FONT_CANDIDATES if os.path.isfile(f)), None)
    tmp = tempfile.mkdtemp(prefix="testfilm-")
    try:
        inputs, chains = [], []
        for i, fr in enumerate(frames):
            colour = COLOURS[i % len(COLOURS)]
            first, end = frame_window(fr["start"], fr["duration"], fps)
            if i + 1 < len(frames):  # segments follow on, so the film's cuts land on the storyboard frames
                end = max(first + 1, frame_window(frames[i + 1]["start"], 1, fps)[0])
            nframes = end - first
            inputs += ["-f", "lavfi", "-i", f"color=c={colour}:s={w}x{h}:r={fps}"]
            chain = f"[{i}:v]trim=end_frame={nframes},setpts=PTS-STARTPTS,setsar=1"
            if use_text:
                texts = [("TEST FIXTURE", h // 24, h // 12),
                         (f"{fr['beat']} · Frame {fr['n']}", h // 9, h // 3),
                         ((fr.get("statement") or fr.get("title") or "")[:70], h // 18, h // 2)]
                for j, (txt, fs, y) in enumerate(texts):
                    if not txt:
                        continue
                    tf = os.path.join(tmp, f"t{i}_{j}.txt")
                    with open(tf, "w", encoding="utf-8") as f:
                        f.write(txt)
                    opts = [f"textfile='{_esc(tf)}'", "fontcolor=white", f"fontsize={fs}",
                            "x=(w-text_w)/2", f"y={y}"]
                    if font:
                        opts.insert(0, f"fontfile='{_esc(font)}'")
                    chain += ",drawtext=" + ":".join(opts)
            chains.append(chain + f"[s{i}]")
        n = len(frames)
        marker = n
        inputs += ["-f", "lavfi", "-i", f"color=c=white:s={max(8, h // 18)}x{max(8, h // 18)}:r={fps}:d={total:.3f}"]
        graph = ";".join(chains)
        graph += ";" + "".join(f"[s{i}]" for i in range(n)) + f"concat=n={n}:v=1:a=0[bg]"
        graph += f";[bg][{marker}:v]overlay=x='mod(t*{w // 5},W-w)':y=H-h-{h // 20}:shortest=1,format=yuv420p[v]"
        maps = ["-map", "[v]"]
        if audio:
            inputs += ["-f", "lavfi", "-i", f"sine=frequency=440:sample_rate=48000:duration={total:.3f}"]
            graph += f";[{n + 1}:a]volume=2.5,aformat=channel_layouts=stereo[a]"
            maps += ["-map", "[a]", "-c:a", "aac", "-b:a", "128k"]
        os.makedirs(os.path.dirname(os.path.abspath(out)), exist_ok=True)
        cmd = [ffmpeg, "-v", "error", "-y"] + inputs + ["-filter_complex", graph] + maps + [
            "-c:v", "libx264", "-preset", "veryfast", "-r", str(fps), "-t", f"{total:.3f}",
            "-movflags", "+faststart", "-metadata", "comment=motion-qa test fixture, not a real render", out]
        run(cmd)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return total, use_text


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", help="motion project root")
    ap.add_argument("--cut", required=True)
    ap.add_argument("--storyboard", help="default <root>/<cut>/STORYBOARD.md")
    ap.add_argument("--out", help="default <root>/renders/<cut>.mp4")
    ap.add_argument("--size", default="1280x720")
    ap.add_argument("--fps", type=int, default=25)
    ap.add_argument("--no-audio", action="store_true", help="write a film without an audio stream")
    ap.add_argument("--ffmpeg", default=shutil.which("ffmpeg"))
    a = ap.parse_args(argv)
    root = os.path.abspath(a.root)
    sb = a.storyboard or os.path.join(a.cut, "STORYBOARD.md")
    sb = sb if os.path.isabs(sb) else os.path.join(root, sb)
    out = a.out or os.path.join("renders", a.cut + ".mp4")
    out = out if os.path.isabs(out) else os.path.join(root, out)
    if not a.ffmpeg:
        print("– · ffmpeg not found → install it or pass --ffmpeg")
        return 1
    try:
        _, frames = read_storyboard(sb)
        gaps = [fr["beat"] for prev, fr in zip(frames, frames[1:]) if abs(fr["start"] - prev["end"]) > 0.01]
        if gaps:
            print(f"{gaps[0]} · frame starts do not follow on from the previous frame → test film assumes back-to-back frames")
        total, text = build(a.ffmpeg, frames, out, a.size, a.fps, audio=not a.no_audio)
    except (StoryboardError, RuntimeError, ValueError) as e:
        print(f"– · {e}")
        return 1
    print(f"test fixture · {len(frames)} frames · {total:.1f} s · {os.path.relpath(out, root)}"
          + ("" if text else " · no drawtext, segments unlabelled"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
