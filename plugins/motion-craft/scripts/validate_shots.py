"""validate_shots.py: check shot-forge's shots.json before anything is generated.

Usage: python validate_shots.py motion/shots/shots.json [--storyboard motion/film-60/STORYBOARD.md]
Stdlib only. If jsonschema is importable, the file is also checked against
skills/shot-forge/schemas/shots.schema.json.

Errors (exit 1):
  project, cut, aspect and a non-empty shots list present; aspect one of 16:9, 9:16, 1:1, 4:5;
  every shot has id, beat, frame, subject, action, camera, light, duration_s, prompt;
  ids unique and shaped S01, S02, ...; beat shaped B02; frame a positive integer;
  duration_s a number from 2 to 10; max_takes (if set) 1-5;
  subject, action, light or prompt asks for something on a screen, readable text,
  a logo or a UI gesture (generated shots stay clean; screens are composited later);
  with --storyboard: the shot's beat has a frame with medium generated or mixed,
  and the shot's frame number belongs to that beat.
Each finding prints as `S03 · problem → fix`.

Adapted in part from an Apache-2.0 shot validator (rules rewritten for video shots,
no-UI word list and storyboard cross-check added); attribution in the plugin README.
"""
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SCHEMA = os.path.join(HERE, "..", "skills", "shot-forge", "schemas", "shots.schema.json")

REQUIRED = ("id", "beat", "frame", "subject", "action", "camera", "light", "duration_s", "prompt")
ASPECTS = {"16:9", "9:16", "1:1", "4:5"}
CHECKED_FIELDS = ("subject", "action", "light", "prompt")  # `negative` may name what to avoid
ID_RE = re.compile(r"^S\d{2}$")
BEAT_RE = re.compile(r"^B\d{2}$")

# (pattern, what it asks the model to draw). Word boundaries keep "phone in pocket",
# "windscreen" and "textured" clean; "phone screen", "app" and "logo" are caught.
_UI = [
    (r"screens?|touch\s*screens?|displays?|monitors?|laptops?|tablets?|computers?|tv|television", "a screen"),
    (r"(?:showing|displaying)\s+(?:the\s+|an?\s+)?(?:photos?|images?|pictures?|report|map|chart|graph|data)", "screen content"),
    (r"apps?|application|interface|ui|gui|ux|dashboards?|websites?|web\s*pages?|webpage|browser|"
     r"homepage|menus?|buttons?|icons?|cursor|notifications?|pop-?ups?|widgets?|toolbar", "a UI element"),
    (r"photo\s+gallery|gallery|camera\s+roll|thumbnails?|inbox|e-?mails?|spreadsheets?|chat\s+window|"
     r"text\s+messages?|pdf", "app content"),
    (r"typing(?:\s+on)?|types?\s+(?:on|into)|keyboards?|texting|scrolling|scrolls?(?:\s+through)?|"
     r"swip(?:e|es|ing)", "a UI gesture"),
    (r"texts?|captions?|subtitles?|title\s+card|lower\s+third|overlays?|headlines?|labels?|"
     r"signage|street\s+signs?|billboards?|posters?|banners?|stickers?", "text in frame"),
    (r"readable|legible|words?|letters?|lettering|handwriting|handwritten|written|numbers?|digits?|"
     r"font|typography|writing\s+on", "readable text"),
    (r"logos?|brand(?:ed|ing)?|wordmarks?|trademarks?|watermarks?", "a logo"),
]
UI_PATTERNS = [(re.compile(r"\b(?:%s)\b" % p, re.I), label) for p, label in _UI]


def ui_hits(text):
    """Return [(matched words, label)] for UI, screen, text or logo mentions in text."""
    hits = []
    for rx, label in UI_PATTERNS:
        for m in rx.finditer(text or ""):
            hits.append((m.group(0), label))
    return hits


def storyboard_frames(path):
    """Return {frame number: {"beat": "B02", "medium": "generated", "title": ...}}."""
    frames, current = {}, None
    head = re.compile(r"^##\s+Frame\s+(\d+)\b\s*(?:[—–-]\s*(.*))?$")
    bullet = re.compile(r"^\s*[-*]\s*(beat|medium)\s*:\s*(.+?)\s*$", re.I)
    for line in open(path, encoding="utf-8"):
        m = head.match(line.rstrip())
        if m:
            current = int(m.group(1))
            frames[current] = {"beat": None, "medium": None, "title": (m.group(2) or "").strip()}
            continue
        if line.startswith("## "):
            current = None
            continue
        b = bullet.match(line)
        if current is not None and b:
            value = b.group(2).strip().strip("\"'`")
            key = b.group(1).lower()
            if key == "beat":
                value = (re.match(r"B\d{2}", value) or [value])[0]
            else:
                value = value.split()[0].lower()
            frames[current][key] = value
    return frames


def schema_findings(data):
    try:
        import jsonschema  # optional
    except ImportError:
        return []
    try:
        schema = json.load(open(SCHEMA, encoding="utf-8"))
    except OSError:
        return []
    out = []
    validator = jsonschema.Draft202012Validator(schema)
    for err in sorted(validator.iter_errors(data), key=lambda e: list(e.path)):
        path = list(err.path)
        sid = "shots.json"
        if len(path) >= 2 and path[0] == "shots" and isinstance(path[1], int):
            sid = str((data["shots"][path[1]] or {}).get("id", "shot %d" % (path[1] + 1)))
        loc = "/".join(str(p) for p in path) or "(root)"
        out.append((sid, "schema: %s: %s" % (loc, err.message), "fix the field as shots.schema.json says"))
    return out


def validate(path, storyboard=None):
    """Return a list of (id, problem, fix) findings. Empty list = valid."""
    try:
        data = json.load(open(path, encoding="utf-8"))
    except (OSError, ValueError) as e:
        return [("shots.json", "cannot read JSON: %s" % e, "write valid JSON")]
    errors = []

    def err(sid, problem, fix):
        errors.append((sid, problem, fix))

    if not isinstance(data, dict):
        return [("shots.json", "top level is not an object", "use {project, cut, aspect, characters, shots}")]
    for key in ("project", "cut"):
        if not data.get(key):
            err("shots.json", "%s missing" % key, "add %s (e.g. %s)" % (key, "atlas" if key == "project" else "film-60"))
    if data.get("aspect") not in ASPECTS:
        err("shots.json", "aspect %r not one of %s" % (data.get("aspect"), ", ".join(sorted(ASPECTS))),
            "set the cut's aspect, e.g. 16:9")
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        err("shots.json", "no shots", "add at least one shot, or skip shot-forge for this cut")
        shots = []

    frames = storyboard_frames(storyboard) if storyboard else None
    seen = set()
    for n, shot in enumerate(shots, 1):
        if not isinstance(shot, dict):
            err("shot %d" % n, "not an object", "write the shot as {id, beat, frame, ...}")
            continue
        sid = str(shot.get("id") or "shot %d" % n)
        for key in REQUIRED:
            if shot.get(key) in (None, ""):
                hint = "2-10 seconds, the length used in the edit" if key == "duration_s" else "fill it from the storyboard frame"
                err(sid, "%s missing" % key, "add %s (%s)" % (key, hint))
        if "id" in shot:
            if not ID_RE.match(str(shot["id"])):
                err(sid, "id %r not shaped S01" % shot["id"], "number shots S01, S02, ...")
            elif shot["id"] in seen:
                err(sid, "duplicate id", "give each shot its own id")
            seen.add(shot["id"])
        if shot.get("beat") not in (None, "") and not BEAT_RE.match(str(shot["beat"])):
            err(sid, "beat %r not shaped B02" % shot["beat"], "use the beat ID from narrative.md")
        frame = shot.get("frame")
        if frame is not None and (isinstance(frame, bool) or not isinstance(frame, int) or frame < 1):
            err(sid, "frame %r is not a positive integer" % (frame,), "use N from '## Frame N' in STORYBOARD.md")
        dur = shot.get("duration_s")
        if dur not in (None, ""):
            if isinstance(dur, bool) or not isinstance(dur, (int, float)):
                err(sid, "duration_s %r is not a number" % (dur,), "write seconds as a number, e.g. 5")
            elif not 2 <= dur <= 10:
                err(sid, "duration_s %g outside 2-10 s" % dur,
                    "split a longer shot into two clips with a cut; merge a shorter one into its neighbour")
        mt = shot.get("max_takes")
        if mt is not None and (isinstance(mt, bool) or not isinstance(mt, int) or not 1 <= mt <= 5):
            err(sid, "max_takes %r not 1-5" % (mt,), "cap takes at 3 unless the user approved more")
        for field in CHECKED_FIELDS:
            hits = ui_hits(str(shot.get(field) or ""))
            if hits:
                words = ", ".join(sorted({"'%s'" % w.lower() for w, _ in hits}))
                kinds = ", ".join(sorted({k for _, k in hits}))
                err(sid, "%s asks for %s (%s)" % (field, kinds, words),
                    "describe the person, light and place only; keep phones face down, in a pocket or below frame; "
                    "composite real UI recordings later (negatives go in `negative`)")
        if frames is not None and BEAT_RE.match(str(shot.get("beat") or "")):
            beat = shot["beat"]
            beat_frames = {k: v for k, v in frames.items() if v["beat"] == beat}
            usable = {k: v for k, v in beat_frames.items() if v["medium"] in ("generated", "mixed")}
            if not beat_frames:
                err(sid, "beat %s has no frame in the storyboard" % beat,
                    "use a beat of this cut, or add the frame with motion-director")
            elif not usable:
                media = ", ".join(sorted({str(v["medium"]) for v in beat_frames.values()}))
                err(sid, "beat %s frame is medium %s, not generated or mixed" % (beat, media),
                    "drop the shot, or change the frame's medium in STORYBOARD.md and get it re-approved")
            elif isinstance(frame, int) and not isinstance(frame, bool) and frame not in beat_frames:
                err(sid, "frame %d does not belong to beat %s (its frames: %s)" % (
                    frame, beat, ", ".join(str(k) for k in sorted(beat_frames))),
                    "set frame to the storyboard frame of beat %s" % beat)
    if not errors:
        errors.extend(schema_findings(data))
    return errors


def main(argv):
    args = list(argv)
    storyboard = None
    if "--storyboard" in args:
        i = args.index("--storyboard")
        if i + 1 >= len(args):
            print(__doc__)
            return 1
        storyboard = args[i + 1]
        del args[i:i + 2]
    if len(args) != 1 or args[0] in ("-h", "--help"):
        print(__doc__)
        return 1
    if storyboard and not os.path.isfile(storyboard):
        print("STORYBOARD.md · not found: %s → pass the cut's STORYBOARD.md" % storyboard)
        return 1
    findings = validate(args[0], storyboard)
    for sid, problem, fix in findings:
        print("%s · %s → %s" % (sid, problem, fix))
    n = len(json.load(open(args[0], encoding="utf-8")).get("shots") or []) if not findings else None
    print("%d errors" % len(findings) if findings else "OK · %d shots" % n)
    return 1 if findings else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
