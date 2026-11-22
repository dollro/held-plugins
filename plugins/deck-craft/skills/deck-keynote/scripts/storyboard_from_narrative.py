"""storyboard_from_narrative.py: draft a keynote storyboard.md from a story-craft narrative.md.

Usage:
  python storyboard_from_narrative.py narrative.md [storyboard.md] [--cut keynote] [--clips clips.json]
  python storyboard_from_narrative.py --check storyboard.md narrative.md [--cut keynote]

Draft: one row per beat of the cut (beats: all = every beat), slide type from the beat role
(deck-keynote SKILL.md section 0), notes from the beat line, fine print from the proof ledger.
Beats with a clip in clips.json get type `video`. The draft is a start: edit wording and types by
hand, never the order. --check confirms the Beat column lists the cut's beats in order (exit 1 if not).
Needs PyYAML (pip install pyyaml).
"""
import json
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("PyYAML missing: pip install pyyaml")
    sys.exit(2)

TYPE_BY_ROLE = {"moment": "statement", "villain": "statement", "turn": "statement", "outcome": "statement",
                "cost": "big_number", "proof": "big_number", "pillar": "reveal", "objection": "three",
                "versus": "versus", "voice": "quote", "reveal": "image_slide", "star": "statement",
                "close": "closing"}


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        sys.exit(f"{path}: no YAML frontmatter")
    return yaml.safe_load(m.group(1)), text


def ledger(text):
    """Beat -> fine print hint from the Proof ledger table (evidence, strength, wording)."""
    out, inside = {}, False
    for line in text.splitlines():
        if line.startswith("## "):
            inside = line.strip().lower() == "## proof ledger"
            continue
        if inside and line.startswith("| B"):
            c = [x.strip() for x in line.strip().strip("|").split("|")]
            out[c[0]] = f"{c[2]} ({c[3]}): {c[4]}" if len(c) >= 5 else c[-1]
    return out


def cut_beats(fm, cut):
    cuts = fm.get("cuts") or {}
    if cut not in cuts:
        sys.exit(f"cut '{cut}' not in narrative (has: {', '.join(cuts)})")
    listed = cuts[cut].get("beats")
    all_ids = [b["id"] for b in fm["beats"]]
    return all_ids if listed == "all" else [str(x) for x in listed]


def draft(narrative, out, cut, clips_path):
    fm, text = frontmatter(narrative)
    beats = {b["id"]: b for b in fm["beats"]}
    fine = ledger(text)
    clips = {}
    if clips_path:
        clips = {c["beat"]: c for c in json.load(open(clips_path, encoding="utf-8"))}
    review = re.search(r"^Verdict:\s*(\w+)", text, re.M)
    rows = [f"| 1 | – | – | – | {fm.get('headline', '')} | title | Open on the event or product family. | Illustrative example if sample data |"]
    for n, bid in enumerate(cut_beats(fm, cut), start=2):
        b = beats[bid]
        kind = "video" if bid in clips else TYPE_BY_ROLE.get(b.get("role"), "statement")
        on_screen = b.get("statement", "")
        if kind == "video":
            on_screen = f"{on_screen} (clip {os.path.basename(clips[bid]['file'])})"
        rows.append(f"| {n} | {bid} | {b.get('act', '')} | {b.get('side', '')} | {on_screen} | {kind} | "
                    f"{b.get('line', '')} | {fine.get(bid, '-')} |")
    head = [f"# {fm.get('product', '')} keynote · headline: \"{fm.get('headline', '')}\"",
            f"Audience: see intake.md | Duration: {fm['cuts'][cut].get('runtime', '')} | Template: <file or none> | Stage: master",
            f"Narrative: {os.path.basename(narrative)} (cut {cut}, review {review.group(1) if review else 'none'})",
            f"Villain: {fm.get('villain', '')} | Promise: {fm.get('promise', '')} | STAR moment: {fm.get('star', '')}",
            "",
            "| # | Beat | Act | Side | On screen (≤ 8 words, [[accent]]) | Type | Notes (spoken) | Proof / fine print |",
            "|---|---|---|---|---|---|---|---|"]
    open(out, "w", encoding="utf-8").write("\n".join(head + rows) + "\n")
    print(f"storyboard: {out} ({len(rows)} slides, {sum(1 for r in rows if '| video |' in r)} video)")


def check(storyboard, narrative, cut):
    fm, _ = frontmatter(narrative)
    expected = cut_beats(fm, cut)
    got = []
    for line in open(storyboard, encoding="utf-8"):
        c = [x.strip() for x in line.strip().strip("|").split("|")]
        if len(c) > 2 and re.match(r"^\d+$", c[0]) and re.match(r"^B\d+$", c[1]):
            got.append(c[1])
    if got == expected:
        print(f"OK · Beat column matches cut {cut} ({len(got)} beats)")
        return 0
    missing = [b for b in expected if b not in got]
    extra = [b for b in got if b not in expected]
    print(f"MISMATCH · cut {cut}: missing {missing or '-'}, not in cut {extra or '-'}, order ok: {[b for b in got if b in expected] == [b for b in expected if b in got]}")
    return 1


def main(argv):
    cut = argv[argv.index("--cut") + 1] if "--cut" in argv else "keynote"
    clips = argv[argv.index("--clips") + 1] if "--clips" in argv else None
    args = [a for a in argv if not a.startswith("--") and a not in (cut, clips)]
    if "--check" in argv and len(args) == 2:
        return check(args[0], args[1], cut)
    if not args:
        print(__doc__)
        return 2
    out = args[1] if len(args) > 1 else os.path.join(os.path.dirname(os.path.abspath(args[0])), "storyboard.md")
    draft(args[0], out, cut, clips)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
