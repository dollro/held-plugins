"""check_deck.py: automated checks for a deck-craft deck.

Usage: python check_deck.py deck.pptx [--mode consult|keynote]
Mode is read from the deck's keywords (set by deckkit.new_deck) unless given.
Exit code 1 if any ERROR.

consult: action titles present, sentence-like, <= 95 characters, unique; source line on every
         slide with data; Illustrative labels when the cover says sample data; one chart per slide;
         <= 5 bullets per box; text >= 12 pt outside labels; one font family; overflow estimate.
keynote: <= 20 words on a slide (excluding fine print), type >= 18 pt outside fine print,
         no bullets, one number per BigNumber slide with fine print, speaker notes present,
         no leftover image placeholders.
video:   every embedded or linked movie has its media (ERROR if missing) and a poster frame
         (WARN if only the default loudspeaker icon); WARN above 60 s or 50 MB.
both:    shapes inside the slide, title not overlapping body shapes, overflow estimate.
It cannot judge whether the argument is right: read the titles (or statements) in order.
"""
import os
import re
import struct
import sys

from pptx import Presentation
from pptx.util import Emu

TOPIC_WORDS = {"overview", "analysis", "summary", "background", "agenda", "update", "results",
               "überblick", "analyse", "zusammenfassung", "hintergrund", "ergebnisse", "status",
               "next steps", "nächste schritte", "introduction", "einleitung", "questions", "fragen"}
MAX_TITLE_CHARS = 95
LABEL_SHAPES = {"Source", "Footnote", "PageNumber", "Tracker", "Navigator", "Illustrative", "Unit",
                "CoverNote", "Confidence", "DividerAgenda", "Label", "Context", "Sub", "AxisLabel"}
KEYNOTE_SMALL_OK = {"Source", "Footnote", "PageNumber", "CoverNote", "Navigator", "Tracker", "Illustrative",
                    "ImagePlaceholder", "AxisLabel"}
KEYNOTE_FLOOR_PT = 18      # secondary lines; statements and numbers run 40-200 pt
KEYNOTE_WORD_BUDGET = 20   # everything visible except fine print; the talk lives in the notes
NOT_DATA = {"NextSteps"}
A_NS = "{http://schemas.openxmlformats.org/drawingml/2006/main}"


def named(slide, name):
    return [s for s in slide.shapes if s.name == name]


def has_data(slide):
    return any((s.has_chart or s.has_table) and s.name not in NOT_DATA for s in slide.shapes)


def run_sizes(shape):
    sizes = []
    for p in shape.text_frame.paragraphs:
        for r in p.runs:
            if r.font.size and r.text.strip():
                sizes.append(r.font.size.pt)
    return sizes


def estimate_overflow(shape):
    """Rough: average glyph width ~0.5 em (Arial), line height 1.2 em."""
    if not shape.has_text_frame or not shape.width or not shape.height or not shape.text_frame.text.strip():
        return False
    width_pt, height_pt = Emu(shape.width).pt, Emu(shape.height).pt
    needed = 0.0
    for p in shape.text_frame.paragraphs:
        size = None
        for r in p.runs:
            if r.font.size:
                size = r.font.size.pt
        size = size or 18
        chars = len("".join(r.text for r in p.runs))
        per_line = max(1, int(width_pt / (size * 0.5)))
        lines = max(1, -(-chars // per_line))
        needed += lines * size * 1.2 + (p.space_after.pt if p.space_after else 0)
    return needed > height_pt * 1.08


def box(shape):
    x, y, w, h = shape.left or 0, shape.top or 0, shape.width or 0, shape.height or 0
    rot = getattr(shape, "rotation", 0) or 0
    if round(rot) % 180 == 90:          # rotated a quarter turn: bounds swap around the centre
        cx, cy = x + w / 2, y + h / 2
        x, y, w, h = cx - h / 2, cy - w / 2, h, w
    return (x, y, x + w, y + h)


def overlap(a, b):
    ax0, ay0, ax1, ay1 = box(a)
    bx0, by0, bx1, by1 = box(b)
    w = min(ax1, bx1) - max(ax0, bx0)
    h = min(ay1, by1) - max(ay0, by0)
    return w > 0 and h > Emu(int(914400 * 0.05))


def words(shape):
    return len(re.findall(r"[\w%€$£¥.,+\-]+", shape.text_frame.text)) if shape.has_text_frame else 0


def bullets_in(shape):
    return [p for p in shape.text_frame.paragraphs
            if p._p.pPr is not None and p._p.pPr.find(A_NS + "buChar") is not None]


MAX_CLIP_S = 60
MAX_CLIP_MB = 50
R_NS = "{http://schemas.openxmlformats.org/officeDocument/2006/relationships}"


def mp4_seconds(blob):
    """Duration from the mp4 mvhd box, or None."""
    i = blob.find(b"mvhd")
    if i < 0:
        return None
    version = blob[i + 4]
    if version == 1:
        timescale, duration = struct.unpack(">IQ", blob[i + 24:i + 36])
    else:
        timescale, duration = struct.unpack(">II", blob[i + 16:i + 24])
    return duration / timescale if timescale else None


def movie_findings(slide, n, deck_dir):
    """(errors, warnings, count) for movie shapes on a slide."""
    errors, warnings, count = [], [], 0
    try:
        from pptx.media import SPEAKER_IMAGE_BYTES
    except ImportError:
        SPEAKER_IMAGE_BYTES = None
    for shape in slide.shapes:
        video = shape._element.find(".//" + A_NS + "videoFile")
        if video is None:
            continue
        count += 1
        label = shape.name if shape.name != "Clip" else "clip"
        rid = video.get(R_NS + "link")
        rel = slide.part.rels.get(rid) if rid else None
        blob = None
        if rel is None:
            errors.append(f"slide {n}: {label} has no media relationship")
        elif rel.is_external:
            path = os.path.join(deck_dir, rel.target_ref.replace("file:///", "/"))
            if not os.path.exists(path):
                errors.append(f"slide {n}: linked clip missing: {rel.target_ref}")
            else:
                blob = open(path, "rb").read()
        else:
            blob = rel.target_part.blob
            if not blob:
                errors.append(f"slide {n}: embedded clip is empty")
        blip = shape._element.find(".//" + A_NS + "blip")
        poster_rid = blip.get(R_NS + "embed") if blip is not None else None
        poster = slide.part.rels.get(poster_rid) if poster_rid else None
        if poster is None or (SPEAKER_IMAGE_BYTES and poster.target_part.blob == SPEAKER_IMAGE_BYTES):
            warnings.append(f"slide {n}: {label} has no poster frame; PowerPoint shows a loudspeaker icon before play")
        if blob:
            mb = len(blob) / 1e6
            secs = mp4_seconds(blob)
            if mb > MAX_CLIP_MB:
                warnings.append(f"slide {n}: {label} is {mb:.0f} MB (max {MAX_CLIP_MB}); re-encode or shorten")
            if secs and secs > MAX_CLIP_S:
                warnings.append(f"slide {n}: {label} runs {secs:.0f} s (max {MAX_CLIP_S}); cut to the beat")
    return errors, warnings, count


def main(path, mode=None):
    prs = Presentation(path)
    kw = prs.core_properties.keywords or ""
    mode = mode or ("keynote" if "keynote" in kw else "consult")
    sw, sh = prs.slide_width, prs.slide_height
    errors, warnings, fonts, spine = [], [], set(), []
    cover_note = " ".join(s.text_frame.text for sl in prs.slides for s in named(sl, "CoverNote"))
    illustrative_deck = "illustrativ" in cover_note.lower()

    for n, slide in enumerate(prs.slides, start=1):
        is_cover = bool(named(slide, "CoverTitle"))
        is_divider = bool(named(slide, "DividerTitle"))
        total_words, numbers = 0, 0

        for shape in slide.shapes:
            x0, y0, x1, y1 = box(shape)
            if x0 < -10 or y0 < -10 or x1 > sw + 10 or y1 > sh + 10:
                if shape.name != "Hero":
                    errors.append(f"slide {n}: '{shape.name}' extends beyond the slide edge")
            if not shape.has_text_frame:
                continue
            for p in shape.text_frame.paragraphs:
                for r in p.runs:
                    if r.font.name:
                        fonts.add(r.font.name)
            if shape.name not in ("Title", "CoverTitle") and estimate_overflow(shape):
                warnings.append(f"slide {n}: text in '{shape.name}' may overflow its box")
            sizes = run_sizes(shape)
            if mode == "consult":
                if len(bullets_in(shape)) > 5:
                    warnings.append(f"slide {n}: {len(bullets_in(shape))} bullets in one box (max 5)")
                if sizes and min(sizes) < 12 and shape.name not in LABEL_SHAPES:
                    warnings.append(f"slide {n}: {min(sizes):.0f} pt text in '{shape.name}' (floor 12 pt; cut words, not size)")
            else:
                if bullets_in(shape):
                    warnings.append(f"slide {n}: bullets on a keynote slide; use reveal() or three() instead")
                if sizes and min(sizes) < KEYNOTE_FLOOR_PT and shape.name not in KEYNOTE_SMALL_OK:
                    warnings.append(f"slide {n}: {min(sizes):.0f} pt text in '{shape.name}' (keynote floor {KEYNOTE_FLOOR_PT} pt)")
                if shape.name not in KEYNOTE_SMALL_OK and shape.name != "Revealed":
                    total_words += words(shape)
                if shape.name == "BigNumber":
                    numbers += 1

        e, w, clips = movie_findings(slide, n, os.path.dirname(os.path.abspath(path)))
        errors += e
        warnings += w

        if mode == "keynote":
            if not is_cover and total_words > KEYNOTE_WORD_BUDGET:
                warnings.append(f"slide {n}: {total_words} words on a keynote slide (budget {KEYNOTE_WORD_BUDGET}; move the rest to notes)")
            if named(slide, "BigNumber") and not named(slide, "Source"):
                warnings.append(f"slide {n}: number claim without fine print (source or test conditions)")
            if numbers > 1:
                warnings.append(f"slide {n}: {numbers} hero numbers; one number per slide")
            if named(slide, "ImagePlaceholder"):
                warnings.append(f"slide {n}: image placeholder still in the deck")
            notes = slide.notes_slide.notes_text_frame.text.strip() if slide.has_notes_slide else ""
            if not is_cover and not notes:
                warnings.append(f"slide {n}: no speaker notes; the talk lives in the notes")
            st = named(slide, "Statement") or named(slide, "CoverTitle") or named(slide, "Title")
            spine.append((n, st[0].text_frame.text.replace("\n", " ").strip() if st else ("(video)" if clips else "(visual)")))

        if has_data(slide) and not named(slide, "Source"):
            (errors if mode == "consult" else warnings).append(f"slide {n}: chart or table without a source line")
        if illustrative_deck and has_data(slide) and not named(slide, "Illustrative"):
            errors.append(f"slide {n}: deck is marked illustrative but this data slide has no Illustrative label")
        charts = [s for s in slide.shapes if s.has_chart]
        if len(charts) > 1:
            warnings.append(f"slide {n}: {len(charts)} charts; one message, one exhibit")

        titles = named(slide, "Title")
        if titles:
            body = [s for s in slide.shapes if s.name not in {"Title", "Source", "PageNumber", "Footnote"} and (s.has_chart or s.has_table or s.has_text_frame) and not (s.has_text_frame and not s.text_frame.text.strip())]
            for s in body:
                if overlap(titles[0], s):
                    warnings.append(f"slide {n}: title overlaps '{s.name}'; move the body down (y=) or shorten the title")
                    break

        if mode != "consult" or is_cover:
            continue
        if is_divider:
            spine.append((n, "§ " + named(slide, "DividerTitle")[0].text_frame.text.strip()))
            continue
        if not titles:
            errors.append(f"slide {n}: no action title (shape named 'Title')")
            continue
        title = titles[0].text_frame.text.strip()
        if len(title) > MAX_TITLE_CHARS:
            errors.append(f"slide {n}: title is {len(title)} characters (max {MAX_TITLE_CHARS}); split the message")
        if len(title.split()) < 6 or title.lower().strip(". ") in TOPIC_WORDS or title.endswith(":"):
            errors.append(f"slide {n}: title reads as a topic, not an action title: '{title}'")
        if not any(ch.isdigit() for ch in title) and has_data(slide):
            warnings.append(f"slide {n}: data slide title has no number; can it quantify the message?")
        if any(title == t for _, t in spine):
            errors.append(f"slide {n}: duplicate title")
        spine.append((n, title))
        if estimate_overflow(titles[0]):
            warnings.append(f"slide {n}: title may run past two lines")

    if len(fonts) > 1:
        warnings.append(f"more than one font family used: {sorted(fonts)}")

    print(f"{path}: {len(prs.slides)} slides, mode {mode}")
    print("Spine (read top to bottom; it must tell the whole story):")
    for n, t in spine:
        print(f"  {n:>2}. {t}")
    for e in errors:
        print("ERROR  ", e)
    for w in warnings:
        print("WARNING", w)
    print(f"{len(errors)} errors, {len(warnings)} warnings")
    return 1 if errors else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--mode")]
    mode = None
    for a in sys.argv[1:]:
        if a.startswith("--mode"):
            mode = a.split("=", 1)[1] if "=" in a else None
    if "--mode" in sys.argv:
        i = sys.argv.index("--mode")
        mode = sys.argv[i + 1] if i + 1 < len(sys.argv) else None
        args = [a for a in args if a != mode]
    if len(args) != 1:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], mode))
