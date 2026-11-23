#!/usr/bin/env python3
"""Cut one clip per beat from a rendered film, with a poster, and write renders/clips.json for deck-craft.

Usage:
  export_beats.py <motion-root> --cut film-60 [--storyboard <cut>/STORYBOARD.md]
                  [--film renders/<cut>.mp4] [--out renders/beats] [--beats B02,B12]
                  [--ffmpeg /path/to/ffmpeg]

Reads the frames of STORYBOARD.md (beat, start, duration; a missing start = sum of the
previous durations), cuts [start, start + duration) of each frame from the film with a
re-encode (H.264 -preset veryfast, yuv420p, AAC if the film has sound, +faststart) and writes
<out>/<beat>.mp4 plus <out>/<beat>.jpg (first stable, non-black frame from ~0.3 s in).
Merges the entries into <motion-root>/renders/clips.json (same beat + cut replaced, others
kept, sorted by cut then beat). Paths in clips.json are relative to the motion root.

audio field: "none" when the film has no audio stream, else frontmatter `audio:` of
STORYBOARD.md (none | music | vo | vo+music), default "music".

Prints one line per clip (`B02 · 6.0 s · renders/beats/B02.mp4`); problems as
`id · problem → fix`. Exit 0 = all clips written, 1 = error. Stdlib only; needs ffmpeg + ffprobe.
"""
import argparse
import json
import math
import os
import re
import shutil
import subprocess
import sys

AUDIO_VALUES = ("none", "music", "vo", "vo+music")
BEAT_RE = re.compile(r"^B\d\d$")
FRAME_RE = re.compile(r"^##\s+Frame\s+(\d+)\s*(?:[—–-]\s*(.*))?$")
BULLET_RE = re.compile(r"^\s*[-*]\s+([A-Za-z_][\w-]*)\s*:\s*(.*)$")
END_TOLERANCE_S = 0.1  # film may be this much shorter than the storyboard before it is an error


class StoryboardError(Exception):
    pass


# ---------------------------------------------------------------- storyboard

def _unquote(value):
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        return value[1:-1]
    return value


def parse_seconds(value):
    """'6s', '6.4 s', '0:06.5', '6' -> float seconds; None for empty."""
    if value is None:
        return None
    v = _unquote(str(value)).strip().lower()
    if not v:
        return None
    m = re.match(r"^(\d+):(\d+(?:\.\d+)?)$", v)
    if m:
        return int(m.group(1)) * 60 + float(m.group(2))
    m = re.match(r"^(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds)?$", v)
    if m:
        return float(m.group(1))
    m = re.match(r"^(\d+(?:\.\d+)?)\s*ms$", v)
    if m:
        return float(m.group(1)) / 1000.0
    raise ValueError(f"cannot read a time from {value!r}")


def parse_frontmatter(text):
    """Top-level `key: value` scalars of a YAML frontmatter block (nested blocks are skipped)."""
    lines = text.splitlines()
    meta = {}
    if not lines or lines[0].strip() != "---":
        return meta, 0
    for i in range(1, len(lines)):
        line = lines[i]
        if line.strip() == "---":
            return meta, i + 1
        if not line or line[0].isspace() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^([A-Za-z_][\w-]*)\s*:\s*(.*)$", line)
        if m:
            meta[m.group(1)] = _unquote(m.group(2).split(" #")[0]) if m.group(2) else ""
    raise StoryboardError("frontmatter is not closed with ---")


def read_storyboard(path):
    """Return (meta, frames). Each frame: {n, title, beat, start, duration, end, statement, ...}."""
    if not os.path.isfile(path):
        raise StoryboardError(f"no storyboard at {path}")
    with open(path, encoding="utf-8") as f:
        text = f.read()
    meta, body_start = parse_frontmatter(text)
    frames, cur = [], None
    for line in text.splitlines()[body_start:]:
        m = FRAME_RE.match(line.strip())
        if m:
            cur = {"n": int(m.group(1)), "title": (m.group(2) or "").strip()}
            frames.append(cur)
            continue
        if line.startswith("## "):
            cur = None
            continue
        if cur is not None:
            b = BULLET_RE.match(line)
            if b and b.group(1).lower() not in cur:
                cur[b.group(1).lower()] = _unquote(b.group(2))
    if not frames:
        raise StoryboardError(f"{path}: no '## Frame N — Title' sections")
    t = 0.0
    seen = set()
    for fr in frames:
        label = f"Frame {fr['n']}"
        beat = fr.get("beat", "").split()[0] if fr.get("beat") else ""
        if not BEAT_RE.match(beat):
            raise StoryboardError(f"{label} · beat {fr.get('beat')!r} missing or not shaped B01 → add '- beat: B02'")
        if beat in seen:
            raise StoryboardError(f"{label} · beat {beat} appears twice → one frame per beat")
        seen.add(beat)
        fr["beat"] = beat
        try:
            dur = parse_seconds(fr.get("duration"))
            start = parse_seconds(fr.get("start"))
        except ValueError as e:
            raise StoryboardError(f"{beat} · {e} → write times as '6s' or '6.4s'")
        if not dur or dur <= 0:
            raise StoryboardError(f"{beat} · duration missing or zero → add '- duration: \"6s\"'")
        fr["start"] = t if start is None else start
        fr["duration"] = dur
        fr["end"] = fr["start"] + dur
        t = fr["end"]
    return meta, frames


def storyboard_end(frames):
    return max(fr["end"] for fr in frames)


# ---------------------------------------------------------------- ffmpeg helpers

def find_tools(ffmpeg_arg=None):
    ffmpeg = ffmpeg_arg or shutil.which("ffmpeg")
    if not ffmpeg or not (os.path.isfile(ffmpeg) or shutil.which(ffmpeg)):
        raise RuntimeError("ffmpeg not found → install it or pass --ffmpeg /path/to/ffmpeg")
    ffprobe = None
    cand = os.path.join(os.path.dirname(ffmpeg), "ffprobe")
    if os.path.dirname(ffmpeg) and os.path.isfile(cand):
        ffprobe = cand
    ffprobe = ffprobe or shutil.which("ffprobe")
    if not ffprobe:
        raise RuntimeError("ffprobe not found → install it next to ffmpeg")
    return ffmpeg, ffprobe


def run(cmd, capture=True):
    p = subprocess.run(cmd, stdout=subprocess.PIPE if capture else None, stderr=subprocess.PIPE)
    if p.returncode != 0:
        tail = p.stderr.decode("utf-8", "replace").strip().splitlines()[-3:]
        raise RuntimeError(f"{os.path.basename(cmd[0])} failed: {' | '.join(tail)}")
    return p


def probe(ffprobe, path):
    """{'duration', 'video': {...}, 'audio': {...} or None} from ffprobe."""
    p = run([ffprobe, "-v", "error", "-print_format", "json", "-show_format", "-show_streams", path])
    data = json.loads(p.stdout.decode("utf-8"))
    video = next((s for s in data.get("streams", []) if s.get("codec_type") == "video"), None)
    audio = next((s for s in data.get("streams", []) if s.get("codec_type") == "audio"), None)
    dur = None
    for src in (video or {}, data.get("format", {})):
        try:
            dur = float(src["duration"])
            break
        except (KeyError, TypeError, ValueError):
            continue
    fps = None
    if video and video.get("avg_frame_rate", "0/0") not in ("0/0", ""):
        num, den = video["avg_frame_rate"].split("/")
        fps = float(num) / float(den) if float(den) else None
    return {"duration": dur, "format_duration": float(data.get("format", {}).get("duration", 0) or 0),
            "video": video, "audio": audio, "fps": fps}


def frame_luma(ffmpeg, path, t, w=64, h=36):
    """Mean luma (0-255) and the raw grey thumbnail of the frame at t seconds, or (None, None)."""
    p = subprocess.run([ffmpeg, "-v", "error", "-ss", f"{t:.3f}", "-i", path, "-frames:v", "1",
                        "-vf", f"scale={w}:{h},format=gray", "-f", "rawvideo", "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    buf = p.stdout
    if p.returncode != 0 or len(buf) < w * h:
        return None, None
    buf = buf[:w * h]
    return sum(buf) / len(buf), buf


def pick_poster_time(ffmpeg, clip, duration, start=0.3, step=0.2, min_luma=24.0, max_diff=6.0):
    """First sample from ~0.3 s that is not black and barely differs from the next sample;
    falls back to the middle of the clip."""
    times = []
    t = min(start, duration / 2)
    while t < duration - 0.05:
        times.append(round(t, 3))
        t += step
    prev = None
    for t in times:  # sampled lazily: stop at the first stable frame
        luma, buf = frame_luma(ffmpeg, clip, t)
        if prev and prev[1] is not None and buf is not None and prev[1] >= min_luma:
            diff = sum(abs(a - b) for a, b in zip(prev[2], buf)) / len(buf)
            if diff <= max_diff:
                return prev[0], "stable"
        prev = (t, luma, buf)
    return round(duration / 2, 3), "middle (no stable frame found)"


# ---------------------------------------------------------------- clips.json

def merge_clips(path, new_entries):
    clips = []
    if os.path.isfile(path):
        with open(path, encoding="utf-8") as f:
            try:
                clips = json.load(f)
            except json.JSONDecodeError as e:
                raise RuntimeError(f"{path} is not valid JSON ({e}) → fix or delete it")
        if not isinstance(clips, list):
            raise RuntimeError(f"{path} is not a JSON list → fix or delete it")
    keys = {(c["beat"], c["cut"]) for c in new_entries}
    kept = [c for c in clips if (c.get("beat"), c.get("cut")) not in keys]
    merged = sorted(kept + list(new_entries), key=lambda c: (str(c.get("cut")), str(c.get("beat"))))
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write("\n")
    os.replace(tmp, path)
    return merged


def rel(path, root):
    return os.path.relpath(os.path.abspath(path), os.path.abspath(root)).replace(os.sep, "/")


# ---------------------------------------------------------------- export

def frame_window(start, duration, fps):
    """First and end (exclusive) frame index of [start, start + duration): a frame belongs to the
    window when its timestamp k / fps falls inside it."""
    eps = 1e-6
    first = int(math.ceil(start * fps - eps))
    end = int(math.ceil((start + duration) * fps - eps))
    return first, max(first + 1, end)


def export_clip(ffmpeg, film, start, duration, out_mp4, has_audio, fps=None):
    """Frame-accurate cut: take the frames whose timestamps fall in [start, start + duration),
    seeking half a frame early so the boundary frame is kept, and trim the sound to match."""
    fps = fps or 25.0
    first, end = frame_window(start, duration, fps)
    nframes = end - first
    ss = max(0.0, (first - 0.5) / fps)
    lead = first / fps - ss
    duration = nframes / fps
    cmd = [ffmpeg, "-v", "error", "-y", "-ss", f"{ss:.4f}", "-accurate_seek", "-i", film,
           "-map", "0:v:0", "-vf", "setpts=PTS-STARTPTS", "-frames:v", str(nframes),
           "-c:v", "libx264", "-preset", "veryfast", "-crf", "18", "-pix_fmt", "yuv420p"]
    if has_audio:
        cmd += ["-map", "0:a:0", "-af", f"atrim=start={lead:.4f}:duration={duration:.4f},asetpts=PTS-STARTPTS",
                "-c:a", "aac", "-b:a", "192k"]
    else:
        cmd += ["-an"]
    cmd += ["-movflags", "+faststart", "-sn", "-dn", "-map_metadata", "-1", out_mp4]
    run(cmd)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("root", help="motion project root (holds <cut>/STORYBOARD.md and renders/)")
    ap.add_argument("--cut", required=True, help="cut name, e.g. film-60")
    ap.add_argument("--storyboard", help="default <root>/<cut>/STORYBOARD.md")
    ap.add_argument("--film", help="default <root>/renders/<cut>.mp4")
    ap.add_argument("--out", help="clip folder, default <root>/renders/beats")
    ap.add_argument("--beats", help="comma list of beats to export, default all frames")
    ap.add_argument("--ffmpeg", help="path to ffmpeg (ffprobe is looked up next to it)")
    a = ap.parse_args(argv)

    root = os.path.abspath(a.root)
    resolve = lambda p, default: os.path.abspath(p if p and os.path.isabs(p) else os.path.join(root, p or default))
    sb_path = resolve(a.storyboard, os.path.join(a.cut, "STORYBOARD.md"))
    film = resolve(a.film, os.path.join("renders", a.cut + ".mp4"))
    out_dir = resolve(a.out, os.path.join("renders", "beats"))
    clips_json = os.path.join(root, "renders", "clips.json")

    try:
        ffmpeg, ffprobe = find_tools(a.ffmpeg)
        meta, frames = read_storyboard(sb_path)
    except (RuntimeError, StoryboardError) as e:
        print(f"– · {e}")
        return 1

    errors = []
    if meta.get("cut") and meta["cut"] != a.cut:
        errors.append(f"– · storyboard says cut {meta['cut']!r}, export asked for {a.cut!r} → pass the matching --cut")
    audio_meta = (meta.get("audio") or "music").strip().lower()
    if audio_meta not in AUDIO_VALUES:
        errors.append(f"– · frontmatter audio {audio_meta!r} unknown → one of {', '.join(AUDIO_VALUES)}")
    by_beat = {fr["beat"]: fr for fr in frames}
    wanted = [b.strip() for b in a.beats.split(",") if b.strip()] if a.beats else [fr["beat"] for fr in frames]
    for b in wanted:
        if b not in by_beat:
            errors.append(f"{b} · not a frame of {rel(sb_path, root)} → export only beats of cut {a.cut}")
    if not os.path.isfile(film):
        errors.append(f"– · no film at {rel(film, root)} → render the cut first (or pass --film)")
    if errors:
        print("\n".join(errors))
        return 1

    try:
        info = probe(ffprobe, film)
    except RuntimeError as e:
        print(f"– · {e}")
        return 1
    if not info["video"]:
        print(f"– · {rel(film, root)} has no video stream → check the render")
        return 1
    film_len = info["format_duration"] or info["duration"] or 0.0
    sb_end = storyboard_end(frames)
    if film_len + END_TOLERANCE_S < sb_end:
        print(f"– · film is {film_len:.2f} s, storyboard ends at {sb_end:.2f} s → re-render, or fix the frame times")
        return 1
    has_audio = info["audio"] is not None
    audio_field = audio_meta if has_audio else "none"

    os.makedirs(out_dir, exist_ok=True)
    entries, failed = [], 0
    for b in wanted:
        fr = by_beat[b]
        mp4 = os.path.join(out_dir, f"{b}.mp4")
        jpg = os.path.join(out_dir, f"{b}.jpg")
        try:
            export_clip(ffmpeg, film, fr["start"], fr["duration"], mp4, has_audio, info["fps"])
            dur = probe(ffprobe, mp4)["duration"] or fr["duration"]
            t, how = pick_poster_time(ffmpeg, mp4, dur)
            run([ffmpeg, "-v", "error", "-y", "-ss", f"{t:.3f}", "-i", mp4, "-frames:v", "1", "-q:v", "2", jpg])
        except RuntimeError as e:
            print(f"{b} · {e} → check the film and ffmpeg")
            failed += 1
            continue
        if abs(dur - fr["duration"]) > 0.15:
            print(f"{b} · clip is {dur:.2f} s, storyboard says {fr['duration']:.2f} s → check fps and frame times")
        entries.append({"beat": b, "cut": a.cut, "file": rel(mp4, root), "poster": rel(jpg, root),
                        "duration_s": round(dur, 2), "audio": audio_field, "loopable": False})
        note = "" if how == "stable" else f" · poster: {how}"
        print(f"{b} · {dur:.1f} s · {rel(mp4, root)}{note}")

    if entries:
        try:
            merge_clips(clips_json, entries)
        except RuntimeError as e:
            print(f"– · {e}")
            return 1
        print(f"clips.json · {len(entries)} clip(s) for {a.cut} · {rel(clips_json, root)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
