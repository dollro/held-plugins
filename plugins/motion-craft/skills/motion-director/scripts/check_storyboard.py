"""check_storyboard.py: check a motion-craft STORYBOARD.md against its story-craft narrative.md.

Usage: python check_storyboard.py STORYBOARD.md [--narrative narrative.md]
The narrative defaults to the `narrative:` path in the storyboard's frontmatter, resolved
relative to the storyboard. Needs PyYAML (pip install pyyaml).

Errors (exit 1):
  frontmatter keys format, duration, message, arc, audience, cut, narrative, brand_lock present;
  narrative.md found, its ## Review says Verdict: PASS, the cut exists in its `cuts:`;
  every frame (`## Frame N — Title`) has beat, medium and duration; medium is
  motion | generated | ui | mixed; duration and start parse as seconds; status (if given) is
  outline | built | animated;
  exactly one frame per beat of the cut, in cut order (no missing, extra, duplicate or
  out-of-order beats).
Warnings (exit 0):
  sum of frame durations more than 15% off the cut runtime; a start that leaves a gap or an
  overlap; a medium that breaks the rule for the beat's role; frame numbers not 1..N;
  message not the narrative headline; missing statement; brand_lock file not found.
Each finding prints as `id · problem → fix`.
"""
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("PyYAML missing: pip install pyyaml (or: uv run --with pyyaml python check_storyboard.py ...)")
    sys.exit(1)

FRONT_KEYS = ["format", "duration", "message", "arc", "audience", "cut", "narrative", "brand_lock"]
MEDIA = {"motion", "generated", "ui", "mixed"}
STATUS = {"outline", "built", "animated"}
# role -> media allowed by the medium rule (references/launch-rules.md)
MEDIUM_RULE = {
    "moment": {"generated", "motion", "mixed"},
    "villain": {"generated", "motion", "mixed"},
    "outcome": {"generated", "motion", "mixed"},
    "reveal": {"motion"},
    "pillar": {"motion"},
    "proof": {"ui", "mixed"},
    "star": {"ui", "mixed"},
    "cost": {"motion"},
    "versus": {"motion"},
    "voice": {"motion", "mixed"},
    "close": {"motion"},
    "turn": {"motion"},
    "objection": {"motion"},
}
TOLERANCE = 0.15
FRAME_RE = re.compile(r"^#{2,3}\s+(?:Frame|Beat|Scene)\s+(\d+)\s*(?:[—–:-]\s*(.*))?$")
BULLET_RE = re.compile(r"^-\s+([A-Za-z_]+)\s*:\s*(.*)$")


def split_frontmatter(text):
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)$", text, re.S)
    if not m:
        raise ValueError("no YAML frontmatter between --- lines")
    return yaml.safe_load(m.group(1)) or {}, m.group(2)


def seconds(value):
    """'6s', '6.5 s', '60 s', '1 min', 6 -> float seconds, or None."""
    m = re.match(r"^\s*\"?(\d+(?:\.\d+)?)\s*(s|sec|secs|seconds|min)?\"?\s*$", str(value))
    if not m:
        return None
    n = float(m.group(1))
    return n * 60 if m.group(2) == "min" else n


def parse_frames(body):
    """Return a list of frames: {number, title, keys: {...}, line}."""
    frames, current, in_bullets = [], None, False
    for no, line in enumerate(body.splitlines(), 1):
        head = FRAME_RE.match(line.strip())
        if head:
            current = {"number": int(head.group(1)), "title": (head.group(2) or "").strip(),
                       "keys": {}, "line": no}
            frames.append(current)
            in_bullets = True
            continue
        if line.startswith("#"):
            current, in_bullets = None, False
            continue
        if current is None or not in_bullets:
            continue
        bullet = BULLET_RE.match(line.strip())
        if bullet:
            current["keys"][bullet.group(1).lower()] = bullet.group(2).strip().strip('"')
        elif line.strip() and not line.startswith(" "):
            in_bullets = False  # free-form narrative starts; bullets end
    return frames


def review_verdict(text):
    inside = False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip().lower() == "## review"
            continue
        if inside:
            m = re.match(r"^\s*Verdict:\s*([A-Z]+)", line)
            if m:
                return m.group(1)
    return None


def cut_beats(nfm, cut_name, beats_by_id):
    cut = (nfm.get("cuts") or {}).get(cut_name)
    if cut is None:
        return None, None
    ids = cut.get("beats")
    if ids == "all":
        ids = list(beats_by_id)
    return list(ids or []), seconds(cut.get("runtime"))


def check(storyboard_path, narrative_path=None):
    errors, warnings = [], []
    err = lambda i, p, f: errors.append((i, p, f))
    warn = lambda i, p, f: warnings.append((i, p, f))

    try:
        fm, body = split_frontmatter(open(storyboard_path, encoding="utf-8").read())
    except (OSError, ValueError, yaml.YAMLError) as e:
        err("storyboard", f"unreadable: {e}", "start from assets/STORYBOARD-template.md")
        return errors, warnings

    for key in FRONT_KEYS:
        if fm.get(key) in (None, ""):
            err("frontmatter", f"`{key}` missing", f"add `{key}:` (see assets/STORYBOARD-template.md)")

    here = os.path.dirname(os.path.abspath(storyboard_path))
    if fm.get("brand_lock"):
        if not os.path.exists(os.path.join(here, str(fm["brand_lock"]))):
            warn("brand_lock", f"{fm['brand_lock']} not found",
                 "export it with deck-craft:deck-design-guide or write it from the brand-lock template")

    if narrative_path is None and fm.get("narrative"):
        narrative_path = os.path.join(here, str(fm["narrative"]))
    if not narrative_path or not os.path.exists(narrative_path):
        err("narrative", f"narrative.md not found ({narrative_path})",
            "fix the `narrative:` path, or write the story first with story-craft:narrative")
        return errors, warnings

    ntext = open(narrative_path, encoding="utf-8").read()
    try:
        nfm, _ = split_frontmatter(ntext)
    except (ValueError, yaml.YAMLError) as e:
        err("narrative", f"frontmatter unreadable: {e}", "run story-craft's validate_narrative.py")
        return errors, warnings
    verdict = review_verdict(ntext)
    if verdict != "PASS":
        err("narrative", f"review verdict is {verdict or 'missing'}",
            "run story-craft:story-review until Verdict: PASS")

    beats_by_id = {b.get("id"): b for b in nfm.get("beats") or []}
    if fm.get("message") and nfm.get("headline") and str(fm["message"]).strip() != str(nfm["headline"]).strip():
        warn("frontmatter", "message differs from the narrative headline", f"message: \"{nfm['headline']}\"")

    cut_name = fm.get("cut")
    expected, runtime = cut_beats(nfm, cut_name, beats_by_id)
    if expected is None:
        err("cut", f"cut `{cut_name}` not in narrative cuts {sorted((nfm.get('cuts') or {}))}",
            "pick a cut that exists, or add it to narrative.md")
        return errors, warnings

    frames = parse_frames(body)
    if not frames:
        err("frames", "no `## Frame N — Title` sections", "one frame per beat of the cut")
        return errors, warnings

    total, cursor = 0.0, 0.0
    for i, fr in enumerate(frames, 1):
        fid = f"Frame {fr['number']}"
        k = fr["keys"]
        if fr["number"] != i:
            warn(fid, f"numbered {fr['number']}, expected {i}", "number frames 1..N in film order")
        for key in ("beat", "medium", "duration"):
            if not k.get(key):
                err(fid, f"`{key}` missing", f"add `- {key}: …`")
        if k.get("medium") and k["medium"] not in MEDIA:
            err(fid, f"medium `{k['medium']}` unknown", "use motion | generated | ui | mixed")
        if k.get("status") and k["status"] not in STATUS:
            err(fid, f"status `{k['status']}` unknown", "use outline | built | animated")
        dur = seconds(k["duration"]) if k.get("duration") else None
        if k.get("duration") and dur is None:
            err(fid, f"duration `{k['duration']}` not in seconds", "write it like `6s`")
        if k.get("start"):
            start = seconds(k["start"])
            if start is None:
                err(fid, f"start `{k['start']}` not in seconds", "write it like `12.0s`")
            elif abs(start - cursor) > 0.05:
                kind = "gap" if start > cursor else "overlap"
                warn(fid, f"starts at {start:g}s, previous frame ends at {cursor:g}s ({kind})",
                     f"start: {cursor:g}s, or change the previous duration")
                cursor = start
        if dur:
            total += dur
            cursor += dur
        if not k.get("statement"):
            warn(fid, "no `statement`", "put the beat statement (verbatim or shortened) on the frame")
        beat = beats_by_id.get(k.get("beat"))
        if k.get("beat") and beat is None:
            err(fid, f"beat {k['beat']} not in the narrative", "use a beat ID from narrative.md")
        if beat and k.get("medium") in MEDIA:
            allowed = MEDIUM_RULE.get(beat.get("role"), MEDIA)
            if k["medium"] not in allowed:
                warn(fid, f"{k['beat']} is a {beat.get('role')} beat shown as `{k['medium']}`",
                     f"medium rule: {' or '.join(sorted(allowed))}")

    got = [fr["keys"].get("beat") for fr in frames if fr["keys"].get("beat")]
    for b in sorted(set(got)):
        if got.count(b) > 1:
            err(b, f"{got.count(b)} frames carry this beat", "one frame per beat; merge them")
        if b not in expected and b in beats_by_id:
            err(b, f"not in cut {cut_name}", "drop the frame, or add the beat to the cut in narrative.md")
    for b in expected:
        if b not in got:
            err(b, f"no frame for this beat of {cut_name}", "add a frame tagged `- beat: " + b + "`")
    seen = [b for b in dict.fromkeys(got) if b in expected]
    want = [b for b in expected if b in seen]
    if seen != want:
        for pos, (s, w) in enumerate(zip(seen, want), 1):
            if s != w:
                err(s, f"out of cut order at frame position {pos} (expected {w})",
                    "frames follow the cut order: " + ", ".join(expected))
                break

    if runtime:
        drift = (total - runtime) / runtime
        if abs(drift) > TOLERANCE:
            warn("duration", f"frames sum to {total:g}s, cut runtime {runtime:g}s ({drift:+.0%})",
                 f"bring the sum within ±{TOLERANCE:.0%} of {runtime:g}s")
    return errors, warnings


def main(argv):
    args = [a for a in argv[1:]]
    narrative = None
    if "--narrative" in args:
        i = args.index("--narrative")
        narrative = args[i + 1] if i + 1 < len(args) else None
        del args[i:i + 2]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(__doc__)
        return 1
    errors, warnings = check(args[0], narrative)
    for i, p, f in errors:
        print(f"ERROR {i} · {p} → {f}")
    for i, p, f in warnings:
        print(f"WARN  {i} · {p} → {f}")
    print(f"{len(errors)} errors, {len(warnings)} warnings → {'FAIL' if errors else 'PASS'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
