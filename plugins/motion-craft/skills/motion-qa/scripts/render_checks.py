#!/usr/bin/env python3
"""Measure a rendered cut against its STORYBOARD.md and the delivery targets.

Usage:
  render_checks.py <render.mp4> [--storyboard <cut>/STORYBOARD.md] [--loudness web|vo|-14]
                   [--ffmpeg /path/to/ffmpeg]

Reports codec, resolution, fps, pixel format, faststart; duration against the storyboard
(±10 %); black stretches (blackdetect); frozen stretches over 2 s (freezedetect; the end-card
hold in the last frame is allowed); integrated loudness and true peak (ebur128) against the
target (web -14 LUFS, vo -16 LUFS, ±1 LU; true peak ≤ -1 dBTP); and scene cuts against the
storyboard's frame boundaries.

Findings print as `id · problem → fix` (id = beat of the frame the time falls in, else –).
Exit 0 = clean, 1 = error (fix before delivery, or the check could not run),
2 = needs human review (look at the moment, then fix or accept with a reason).
Measures only: a clean run does not replace watching the film. Stdlib only; needs ffmpeg + ffprobe.
"""
import argparse
import os
import re
import subprocess
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from export_beats import StoryboardError, find_tools, parse_seconds, probe, read_storyboard  # noqa: E402

LOUDNESS_TARGETS = {"web": -14.0, "vo": -16.0}
LOUDNESS_TOLERANCE_LU = 1.0
TRUE_PEAK_MAX = -1.0
FREEZE_MAX_S = 2.0
BLACK_MAX_S = 0.5
DURATION_TOLERANCE = 0.10
STANDARD_FPS = (23.976, 24, 25, 29.97, 30, 50, 59.94, 60)


class Report:
    def __init__(self):
        self.errors, self.review, self.notes = [], [], []

    def error(self, line):
        self.errors.append(line)

    def warn(self, line):
        self.review.append(line)

    def note(self, line):
        self.notes.append(line)

    def print(self):
        for title, lines in (("Errors (fix before delivery)", self.errors),
                             ("Review (look at the moment, then fix or accept with a reason)", self.review),
                             ("Notes", self.notes)):
            if lines:
                print(f"\n{title}:")
                for line in lines:
                    print(line)
        code = 1 if self.errors else 2 if self.review else 0
        print(f"\nresult · {len(self.errors)} error(s), {len(self.review)} to review · exit {code}")
        return code


def beat_at(frames, t):
    for fr in frames or []:
        if fr["start"] <= t < fr["end"]:
            return fr["beat"]
    return "–"


def is_faststart(path):
    """True when the moov box comes before mdat (playback starts before the whole file loads)."""
    try:
        with open(path, "rb") as f:
            while True:
                head = f.read(8)
                if len(head) < 8:
                    return None
                size = int.from_bytes(head[:4], "big")
                kind = head[4:8]
                if kind == b"moov":
                    return True
                if kind == b"mdat":
                    return False
                if size == 1:
                    size = int.from_bytes(f.read(8), "big")
                    f.seek(size - 16, 1)
                elif size < 8:
                    return None
                else:
                    f.seek(size - 8, 1)
    except OSError:
        return None


def video_pass(ffmpeg, path):
    """One decode for blackdetect, freezedetect and scene cuts."""
    vf = ("scale=640:-2,blackdetect=d=0.1:pix_th=0.10,freezedetect=n=-60dB:d=%s,"
          "select='gt(scene\\,0.3)',showinfo" % FREEZE_MAX_S)
    p = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", path, "-an", "-vf", vf, "-f", "null", "-"],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = p.stderr.decode("utf-8", "replace")
    if p.returncode != 0:
        raise RuntimeError("ffmpeg video analysis failed: " + " | ".join(log.strip().splitlines()[-2:]))
    blacks = [(float(a), float(b)) for a, b in re.findall(r"black_start:\s*([\d.]+)\s+black_end:\s*([\d.]+)", log)]
    starts = [float(x) for x in re.findall(r"freeze_start:\s*([\d.]+)", log)]
    ends = [float(x) for x in re.findall(r"freeze_end:\s*([\d.]+)", log)]
    freezes = [(s, ends[i] if i < len(ends) else None) for i, s in enumerate(starts)]
    cuts = [float(x) for x in re.findall(r"pts_time:\s*([\d.]+)", log)]
    return blacks, freezes, cuts


def loudness_pass(ffmpeg, path):
    p = subprocess.run([ffmpeg, "-hide_banner", "-nostats", "-i", path, "-vn", "-af", "ebur128=peak=true",
                        "-f", "null", "-"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    log = p.stderr.decode("utf-8", "replace")
    summary = log[log.rfind("Summary:"):] if "Summary:" in log else log
    i = re.search(r"I:\s*(-?[\d.]+|-inf)\s*LUFS", summary)
    tp = re.search(r"True peak:\s*\n\s*Peak:\s*(-?[\d.]+|-inf)\s*dBFS", summary)
    val = lambda m: None if not m else (-99.0 if m.group(1) == "-inf" else float(m.group(1)))
    return val(i), val(tp)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("render")
    ap.add_argument("--storyboard", help="STORYBOARD.md of the cut (enables duration, format and cut checks)")
    ap.add_argument("--loudness", default="web", help="web (-14 LUFS), vo (-16 LUFS) or a number")
    ap.add_argument("--ffmpeg")
    a = ap.parse_args(argv)
    r = Report()

    try:
        ffmpeg, ffprobe = find_tools(a.ffmpeg)
        if not os.path.isfile(a.render):
            raise RuntimeError(f"no render at {a.render}")
        info = probe(ffprobe, a.render)
        meta, frames = read_storyboard(a.storyboard) if a.storyboard else ({}, [])
        target = LOUDNESS_TARGETS.get(a.loudness)
        target = float(a.loudness) if target is None else target
    except (RuntimeError, StoryboardError, ValueError) as e:
        print(f"– · {e}")
        return 1

    v, au = info["video"], info["audio"]
    if not v:
        print("– · render has no video stream → check the render")
        return 1
    dur = info["format_duration"] or info["duration"] or 0.0
    fps = info["fps"] or 0
    w, h = v.get("width"), v.get("height")
    print(f"render · {v.get('codec_name')} {v.get('profile', '')} · {w}x{h} · {fps:.3f} fps · "
          f"{v.get('pix_fmt')} · {dur:.2f} s · audio {au.get('codec_name') + ' ' + str(au.get('sample_rate')) + ' Hz' if au else 'none'}")

    # delivery basics
    if v.get("codec_name") != "h264":
        r.warn(f"– · video codec is {v.get('codec_name')} → H.264 for web, deck and social copies (keep other codecs for masters only)")
    if v.get("pix_fmt") != "yuv420p":
        r.error(f"– · pixel format {v.get('pix_fmt')} does not play everywhere → re-encode with -pix_fmt yuv420p")
    if fps and not any(abs(fps - s) < 0.01 for s in STANDARD_FPS):
        r.warn(f"– · {fps:.3f} fps is not a standard rate → render at 25, 30 or the rate the brief names")
    fs = is_faststart(a.render)
    if fs is False:
        r.warn("– · moov atom after mdat (no faststart) → re-mux with -movflags +faststart")
    if w and h and (w % 2 or h % 2):
        r.error(f"– · odd frame size {w}x{h} → use even dimensions")
    fmt = (meta.get("format") or "").lower().replace(" ", "")
    if fmt and re.match(r"^\d+x\d+$", fmt) and fmt != f"{w}x{h}":
        r.error(f"– · render is {w}x{h}, storyboard format is {fmt} → render at the storyboard format")

    # duration
    if frames:
        sb_end = max(fr["end"] for fr in frames)
        planned = parse_seconds(meta.get("duration")) if meta.get("duration") else sb_end
        if dur + 0.1 < sb_end:
            r.error(f"– · render is {dur:.2f} s, the last frame ends at {sb_end:.2f} s → re-render or fix frame times (beat export will fail)")
        if planned and abs(dur - planned) > DURATION_TOLERANCE * planned:
            r.warn(f"– · render is {dur:.1f} s, storyboard plans {planned:.1f} s (more than ±10 %) → retime or update the storyboard")

    # picture
    try:
        blacks, freezes, cuts = video_pass(ffmpeg, a.render)
    except RuntimeError as e:
        r.error(f"– · {e} → check the file plays")
        return r.print()
    for s, e in blacks:
        length = e - s
        if s < 0.05:
            r.warn(f"{beat_at(frames, s)} · frame 0 is black ({length:.2f} s) → open on a finished frame")
        elif e >= dur - 0.05:
            if length > 1.0:
                r.warn(f"– · {length:.1f} s of black at the end → end on the end card, trim the tail")
        elif length > BLACK_MAX_S:
            r.warn(f"{beat_at(frames, s)} · black from {s:.2f} to {e:.2f} s → shorten the dip or confirm it is a planned fade")
    last = frames[-1] if frames else None
    for s, e in freezes:
        e = dur if e is None else e
        in_end_card = (last and s >= last["start"] - 0.05) or (not last and e >= dur - 0.05 and e - s <= 4.0)
        if in_end_card:
            r.note(f"{beat_at(frames, s) if frames else '–'} · end-card hold {e - s:.1f} s from {s:.1f} s · CTA should be held 1.5-3 s")
            continue
        r.warn(f"{beat_at(frames, s)} · nothing moves from {s:.1f} to {e:.1f} s ({e - s:.1f} s) → add a slow move or cut sooner")

    # cuts against the storyboard
    if frames and fps:
        frame_t = 1.0 / fps
        bounds = [(fr["start"], fr["beat"]) for fr in frames[1:]]
        for c in cuts:
            if c < 0.05:
                continue
            near = min(bounds, key=lambda b: abs(b[0] - c)) if bounds else None
            d = abs(near[0] - c) if near else None
            if near and d <= 1.5 * frame_t:
                continue
            if near and d <= 0.5:
                r.warn(f"{near[1]} · cut at {c:.2f} s, frame starts at {near[0]:.2f} s ({d / frame_t:.0f} frames off) → retime the frame or the cut")
            else:
                r.note(f"{beat_at(frames, c)} · cut at {c:.2f} s inside the frame → confirm it is a planned shot change")
        missing = [b for t, b in bounds if not any(abs(t - c) <= 0.5 for c in cuts)]
        if missing:
            r.note(f"{', '.join(missing)} · no hard cut found at the frame start → fine for soft transitions; check the beat change reads")
    elif cuts:
        r.note(f"– · {len(cuts)} scene cut(s) at " + ", ".join(f"{c:.1f}" for c in cuts[:12]) + " s")

    # sound
    if not au:
        if (meta.get("audio") or "").lower() != "none":
            r.warn("– · no audio stream → fine for a muted teaser; otherwise mux the mix")
    else:
        integrated, peak = loudness_pass(ffmpeg, a.render)
        if integrated is None:
            r.error("– · loudness could not be measured → check the audio stream")
        else:
            print(f"loudness · {integrated:.1f} LUFS integrated (target {target:.0f}) · true peak "
                  f"{'n/a' if peak is None else f'{peak:.1f} dBTP'}")
            if integrated < -60:
                r.warn("– · audio track is silent → remove it or mux the mix")
            elif abs(integrated - target) > LOUDNESS_TOLERANCE_LU:
                r.warn(f"– · {integrated:.1f} LUFS, target {target:.0f} LUFS → apply loudnorm=I={target:.0f}:TP=-1.5:LRA=11 to the mix")
            if peak is not None and peak > TRUE_PEAK_MAX:
                r.error(f"– · true peak {peak:.1f} dBTP above {TRUE_PEAK_MAX:.0f} dBTP → limit the mix (loudnorm TP=-1.5 or a true-peak limiter)")
    return r.print()


if __name__ == "__main__":
    sys.exit(main())
