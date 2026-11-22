"""deckkit: python-pptx helpers for analyst decks and launch keynotes.

Part of the deck-craft skill (SKILL.md). Every helper draws native, editable
PowerPoint objects (text boxes, shapes, tables, charts), never pictures of them.
Shapes carry fixed names (Title, Tracker, Source, Illustrative, PageNumber,
Statement, BigNumber, ...) so that check_deck.py can find them.

Two themes:
    consult  white page, dark ink, grey context, one accent. Action titles.
    keynote  black stage, white type, one accent. Few words, huge type.

Usage:
    import sys; sys.path.insert(0, "<skill>/scripts")
    from deckkit import *
    prs = new_deck(mode="consult")            # or mode="keynote"
    set_sections(["Diagnosis", "Options", "Plan"])
    title_slide(prs, "Restoring wholesale margin", "Steering committee, 12 Nov 2026")
    s = content_slide(prs, "Café chains drive most of the margin decline", section="Diagnosis")
    bar_chart(s, ["A", "B"], [3.0, 5.0], highlight=1, unit="Gross margin, %")
    source(s, "Source: client finance data, as provided in brief")
    prs.save("deck.pptx")

Override colours or font AFTER new_deck(): set_theme("consult", accent="C8102E", font="Calibri").
Inline accent: any text helper renders [[words]] in the accent colour.
"""
import json
import os
import re

from lxml import etree
from pptx import Presentation
from pptx.chart.data import CategoryChartData
from pptx.dml.color import RGBColor
from pptx.enum.chart import XL_CHART_TYPE, XL_LABEL_POSITION, XL_LEGEND_POSITION, XL_TICK_LABEL_POSITION, XL_TICK_MARK
from pptx.enum.shapes import MSO_CONNECTOR, MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.oxml.ns import qn
from pptx.util import Emu, Inches, Pt

# ----------------------------------------------------------------- themes

THEMES = {
    "consult": dict(
        mode="consult", font="Arial", ink="1F2933", grey="8A9099", light="D5D9DE", pale="F2F4F7",
        accent="1F5AA6", accent_pale="E6EEF8", negative="B5452F", bg="FFFFFF",
        chart_greys=["A9AFB7", "C9CED4", "7D848D", "E1E4E8"],
    ),
    "keynote": dict(
        mode="keynote", font="Arial", ink="FFFFFF", grey="8E8E93", light="3A3A3C", pale="1C1C1E",
        accent="2F80ED", accent_pale="14243B", negative="FF453A", bg="000000",
        chart_greys=["636366", "48484A", "8E8E93", "3A3A3C"],
    ),
}
T = dict(THEMES["consult"])
WHITE = "FFFFFF"
_TEMPLATE = {"on": False}


def set_theme(name="consult", **overrides):
    """Switch theme and override any key: font, ink, grey, light, pale, accent, accent_pale, negative, bg."""
    T.clear()
    T.update(THEMES[name])
    T.update(overrides)
    T["paint_bg"] = (not _TEMPLATE["on"]) and T["bg"].upper() != "FFFFFF"
    return T


# ----------------------------------------------------------------- grid (16:9, inches)

SLIDE_W, SLIDE_H = 13.333, 7.5
LEFT, RIGHT = 0.5, 0.5
BODY_W = SLIDE_W - LEFT - RIGHT
TRACKER_Y = 0.32
TITLE_Y, TITLE_H = 0.58, 0.9
TITLE_W = BODY_W - 1.7
BODY_TOP, BODY_BOTTOM = 1.7, 6.5
SOURCE_Y = 6.82
GUTTER = 0.3

_SECTIONS = []


def set_sections(names):
    """Declare the deck's sections once; content slides then show a small navigator (page tracker)."""
    _SECTIONS[:] = list(names)


def rgb(hex_value):
    return RGBColor.from_string(hex_value)


def _c(value, default_key):
    """Resolve a colour: explicit hex, a theme key name, or the default theme key."""
    if value is None:
        return T[default_key]
    return T.get(value, value)


# ----------------------------------------------------------------- deck

_LAYOUTS = {}          # role -> layout, set by use_layouts() or new_deck(template=...)

_LAYOUT_NAMES = {
    "blank": ("blank", "leer", "empty"),
    "title_only": ("title only", "nur titel", "title-only", "titel"),
}


def _find_layout(prs, names):
    for layout in prs.slide_layouts:
        if layout.name.lower().strip() in names:
            return layout
    return None


def use_layouts(prs, **roles):
    """Map roles to template layouts by name or index, e.g.
    use_layouts(prs, blank="Leer", title_only="Nur Titel", statement="Statement dark").
    Roles used by the helpers: blank, title_only, statement, divider, cover."""
    for role, ref in roles.items():
        layout = prs.slide_layouts[ref] if isinstance(ref, int) else _find_layout(prs, (ref.lower(),))
        if layout is None:
            raise ValueError(f"layout '{ref}' not in template: {[l.name for l in prs.slide_layouts]}")
        _LAYOUTS[role] = layout


def list_layouts(prs):
    """Print the template's layouts and their placeholders, to choose roles for use_layouts()."""
    for i, layout in enumerate(prs.slide_layouts):
        print(i, repr(layout.name), [(p.placeholder_format.idx, str(p.placeholder_format.type).split(".")[-1])
                                     for p in layout.placeholders])


def theme_from_template(prs):
    """Read the master's theme colours and fonts into the active theme, so every helper draws in the
    brand: dk1->ink, lt1->bg, accent1->accent, minor latin font->font. Returns what it read."""
    found = {}
    try:
        master = prs.slide_masters[0]
        theme_part = [r.target_part for r in master.part.rels.values() if r.reltype.endswith("/theme")][0]
        root = etree.fromstring(theme_part.blob)
        ns = {"a": "http://schemas.openxmlformats.org/drawingml/2006/main"}
        for key in ("dk1", "lt1", "dk2", "lt2", "accent1", "accent2"):
            el = root.find(f".//a:clrScheme/a:{key}", ns)
            if el is not None and len(el):
                c = el[0]
                found[key] = c.get("val") if c.tag.endswith("srgbClr") else c.get("lastClr")
        minor = root.find(".//a:fontScheme/a:minorFont/a:latin", ns)
        major = root.find(".//a:fontScheme/a:majorFont/a:latin", ns)
        if minor is not None:
            found["font"] = minor.get("typeface")
        if major is not None:
            found["font_major"] = major.get("typeface")
    except Exception as exc:  # templates vary; never fail the build on this
        print(f"theme_from_template: could not read theme ({exc}); keeping defaults")
        return found
    if T["mode"] == "consult":
        T.update({k: v for k, v in (("ink", found.get("dk1")), ("accent", found.get("accent1")),
                                    ("font", found.get("font"))) if v})
    else:
        T.update({k: v for k, v in (("accent", found.get("accent1")), ("font", found.get("font"))) if v})
    return found


def keynote_stage(stage="master"):
    """Keynote background in a template deck. master: keep the master's background, logo and footer
    (ink becomes the template's dark text colour); dark: paint a dark stage (T['stage'] or black) on the
    template's layout; accent: paint the brand accent (for one or two STAR moments only)."""
    T["paint_bg"] = stage != "master"
    if stage == "master":
        T.update(bg="FFFFFF", ink=THEMES["consult"]["ink"], grey=THEMES["consult"]["grey"],
                 light=THEMES["consult"]["light"], pale=THEMES["consult"]["pale"],
                 chart_greys=THEMES["consult"]["chart_greys"])
    elif stage == "dark":
        T.update(bg=T.get("stage", "000000"), ink="FFFFFF", grey="8E8E93", light="3A3A3C", pale="1C1C1E",
                 chart_greys=THEMES["keynote"]["chart_greys"])
    elif stage == "accent":
        T.update(bg=T["accent"], ink="FFFFFF", grey="E6E6E6", light="FFFFFF", pale=T["accent"])


def new_deck(template=None, mode="consult", stage=None):
    """A blank 16:9 deck, or one built on a client/corporate template (.pptx/.potx).
    mode: consult | keynote. With a template, theme colours and fonts are read from it, titles go into
    the master's title placeholder, and keynote slides keep the master background unless stage='dark'."""
    set_theme(mode)
    _LAYOUTS.clear()
    _TEMPLATE["on"] = bool(template)
    if template and str(template).lower().endswith(".potx"):
        # python-pptx opens .pptx only: rewrite the content type of a .potx in memory
        import io
        import zipfile
        buf = io.BytesIO()
        with zipfile.ZipFile(template) as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    data = data.replace(b"presentationml.template.main+xml",
                                        b"presentationml.presentation.main+xml")
                zout.writestr(item, data)
        buf.seek(0)
        prs = Presentation(buf)
    else:
        prs = Presentation(template) if template else Presentation()
    if not template:
        prs.slide_width, prs.slide_height = Inches(SLIDE_W), Inches(SLIDE_H)
        T["paint_bg"] = T["bg"].upper() != "FFFFFF"
    else:
        w, h = Emu(prs.slide_width).inches, Emu(prs.slide_height).inches
        if abs(w - SLIDE_W) > 0.05 or abs(h - SLIDE_H) > 0.05:
            print(f"WARNING: template is {w:.2f} x {h:.2f} in; deckkit's grid assumes {SLIDE_W} x {SLIDE_H}. "
                  "Pass explicit x/y/w/h or work in the template's placeholders.")
        theme_from_template(prs)
        if mode == "keynote":
            keynote_stage(stage or "master")
        else:
            T["paint_bg"] = False
        for role, names in _LAYOUT_NAMES.items():
            layout = _find_layout(prs, names)
            if layout is not None:
                _LAYOUTS[role] = layout
    prs.core_properties.keywords = f"deck-craft:{mode}"
    return prs


def apply_design_guide(prs, path):
    """Apply a design-guide.json (from the deck-design-guide skill) to a deck opened with new_deck():
    colours, fonts and layout roles. Explicit brand values win over what the theme said."""
    import json
    with open(path, encoding="utf-8") as f:
        guide = json.load(f)
    colors = {k: v for k, v in (guide.get("colors") or {}).items() if v}
    keep_stage = T["mode"] == "keynote" and T.get("paint_bg") and T["bg"] != "FFFFFF"
    for key in ("ink", "accent", "grey", "light", "pale", "accent_pale", "negative"):
        if key in colors and not (keep_stage and key in ("ink", "grey", "light", "pale")):
            T[key] = colors[key]
    if (guide.get("fonts") or {}).get("body"):
        T["font"] = guide["fonts"]["body"]
    names = {l.name for l in prs.slide_layouts}
    for role, name in (guide.get("layouts") or {}).items():
        if name in names:
            use_layouts(prs, **{role: name})
    stage = (guide.get("keynote") or {}).get("stage")
    if T["mode"] == "keynote" and stage and _TEMPLATE["on"]:
        keynote_stage(stage)
        if stage == "master":
            for key in ("ink", "accent"):
                if key in colors:
                    T[key] = colors[key]
    return guide


def _blank_layout(prs):
    if "blank" in _LAYOUTS:
        return _LAYOUTS["blank"]
    layout = _find_layout(prs, _LAYOUT_NAMES["blank"])
    return layout or prs.slide_layouts[len(prs.slide_layouts) - 1]


def _clear_placeholders(slide, keep=()):
    for ph in list(slide.placeholders):
        if ph.placeholder_format.idx not in keep:
            ph._element.getparent().remove(ph._element)


def _new_slide(prs, role="blank"):
    layout = _LAYOUTS.get(role) or _blank_layout(prs)
    slide = prs.slides.add_slide(layout)
    _clear_placeholders(slide)
    if T.get("paint_bg"):
        fill = slide.background.fill
        fill.solid()
        fill.fore_color.rgb = rgb(T["bg"])
    return slide


def notes(slide, value):
    """Speaker notes. In keynote mode the talk lives here, not on the slide."""
    slide.notes_slide.notes_text_frame.text = value
    return slide


# ----------------------------------------------------------------- primitives

_ACCENT_RE = re.compile(r"\[\[(.+?)\]\]")


def _style(run, size, color=None, bold=False, italic=False):
    run.font.name = T["font"]
    run.font.size = Pt(size)
    run.font.bold = bold
    run.font.italic = italic
    run.font.color.rgb = rgb(_c(color, "ink"))


def _runs(paragraph, line, size, color, bold, italic):
    """Write a line into a paragraph; [[...]] segments get the accent colour."""
    pos = 0
    for m in _ACCENT_RE.finditer(line):
        if m.start() > pos:
            r = paragraph.add_run()
            r.text = line[pos:m.start()]
            _style(r, size, color, bold, italic)
        r = paragraph.add_run()
        r.text = m.group(1)
        _style(r, size, "accent", bold, italic)
        pos = m.end()
    if pos < len(line) or pos == 0:
        r = paragraph.add_run()
        r.text = line[pos:]
        _style(r, size, color, bold, italic)


def _bullet(paragraph, char="•"):
    pPr = paragraph._p.get_or_add_pPr()
    pPr.set("marL", str(Inches(0.2)))
    pPr.set("indent", str(-Inches(0.2)))
    for tag in ("a:buNone", "a:buChar", "a:buAutoNum"):
        for old in pPr.findall(qn(tag)):
            pPr.remove(old)
    bu = etree.SubElement(pPr, qn("a:buChar"))
    bu.set("char", char)


def text(slide, value, x, y, w, h, size=14, color=None, bold=False, italic=False,
         align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, bullets=False, name=None, space_after=4,
         line_spacing=None):
    """A text box. value: string (lines split on \\n) or list of lines. [[x]] renders x in accent."""
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    if name:
        box.name = name
    frame = box.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = frame.margin_right = Inches(0)
    frame.margin_top = frame.margin_bottom = Inches(0.02)
    lines = value if isinstance(value, list) else str(value).split("\n")
    for i, line in enumerate(lines):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.alignment = align
        p.space_after = Pt(space_after)
        if line_spacing:
            p.line_spacing = line_spacing
        if bullets:
            _bullet(p)
        _runs(p, line, size, color, bold, italic)
    return box


def rect(slide, x, y, w, h, fill=None, line=None, line_w=0.75, shape=MSO_SHAPE.RECTANGLE, name=None):
    item = slide.shapes.add_shape(shape, Inches(x), Inches(y), Inches(w), Inches(h))
    item.shadow.inherit = False
    style = item._element.find(qn("p:style"))
    if style is not None:                      # theme effect styles can carry shadows: neutralise
        eff = style.find(qn("a:effectRef"))
        if eff is not None:
            eff.set("idx", "0")
    if name:
        item.name = name
    if fill:
        item.fill.solid()
        item.fill.fore_color.rgb = rgb(_c(fill, "pale"))
    else:
        item.fill.background()
    if line:
        item.line.color.rgb = rgb(_c(line, "light"))
        item.line.width = Pt(line_w)
    else:
        item.line.fill.background()
    return item


def _shape_text(item, value, size, color=None, bold=False, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE):
    frame = item.text_frame
    frame.word_wrap = True
    frame.vertical_anchor = anchor
    frame.margin_left = frame.margin_right = Inches(0.08)
    frame.margin_top = frame.margin_bottom = Inches(0.03)
    for i, line in enumerate(value.split("\n")):
        p = frame.paragraphs[0] if i == 0 else frame.add_paragraph()
        p.alignment = align
        _runs(p, line, size, color, bold, False)


def line(slide, x1, y1, x2, y2, color=None, weight=0.75, name=None):
    conn = slide.shapes.add_connector(MSO_CONNECTOR.STRAIGHT, Inches(x1), Inches(y1), Inches(x2), Inches(y2))
    conn.line.color.rgb = rgb(_c(color, "light"))
    conn.line.width = Pt(weight)
    style = conn._element.find(qn("p:style"))
    if style is not None:
        conn._element.remove(style)            # drop theme effects (shadow) from rules and leaders
    if name:
        conn.name = name
    return conn


def hline(slide, x, y, w, color=None, weight=0.75):
    return line(slide, x, y, x + w, y, color, weight)


def _page_number(prs, slide):
    text(slide, str(len(prs.slides)), SLIDE_W - RIGHT - 0.5, SOURCE_Y, 0.5, 0.3, size=9,
         color="grey", align=PP_ALIGN.RIGHT, name="PageNumber")


def _navigator(slide, current):
    """Small section list in the tracker row; the current section in accent."""
    if not _SECTIONS:
        return
    box = slide.shapes.add_textbox(Inches(6.2), Inches(TRACKER_Y), Inches(4.9), Inches(0.25))
    box.name = "Navigator"
    frame = box.text_frame
    frame.margin_left = frame.margin_right = Inches(0)
    frame.margin_top = frame.margin_bottom = Inches(0)
    p = frame.paragraphs[0]
    p.alignment = PP_ALIGN.RIGHT
    for i, name in enumerate(_SECTIONS):
        if i:
            r = p.add_run()
            r.text = "   "
            _style(r, 9, "grey")
        r = p.add_run()
        r.text = name.upper()
        on = name == current
        _style(r, 9, "accent" if on else "light" if T["mode"] == "consult" else "grey", bold=on)


# ----------------------------------------------------------------- consult: slides

def title_slide(prs, title, subtitle="", note=""):
    """Cover. Put 'Illustrative example · Fictional company and sample data' in note when it applies.
    With a template and use_layouts(prs, cover=...), the master's title/subtitle placeholders are used."""
    if "cover" in _LAYOUTS:
        slide = prs.slides.add_slide(_LAYOUTS["cover"])
        phs = {p.placeholder_format.type: p for p in slide.placeholders}
        from pptx.enum.shapes import PP_PLACEHOLDER as PH
        t = phs.get(PH.CENTER_TITLE) or phs.get(PH.TITLE)
        st = phs.get(PH.SUBTITLE)
        keep = []
        if t is not None:
            t.text_frame.text, t.name = title, "CoverTitle"
            keep.append(t.placeholder_format.idx)
        if st is not None and subtitle:
            st.text_frame.text, st.name = subtitle, "CoverSubtitle"
            keep.append(st.placeholder_format.idx)
        _clear_placeholders(slide, keep=keep)
        if t is None:
            text(slide, title, 1.0, 2.4, 10.5, 1.6, size=34, bold=True, anchor=MSO_ANCHOR.BOTTOM, name="CoverTitle")
        if subtitle and st is None:
            text(slide, subtitle, 1.0, 4.15, 10.5, 0.5, size=16, color="grey", name="CoverSubtitle")
        if note:
            text(slide, note, 1.0, 6.6, 10.5, 0.35, size=10, color="grey", italic=True, name="CoverNote")
        return slide
    slide = _new_slide(prs, "cover")
    if T["mode"] == "keynote":
        text(slide, title, 1.0, 2.3, SLIDE_W - 2.0, 1.9, size=60, bold=True, align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.BOTTOM, name="CoverTitle", line_spacing=0.95)
        if subtitle:
            text(slide, subtitle, 1.0, 4.35, SLIDE_W - 2.0, 0.6, size=24, color="grey",
                 align=PP_ALIGN.CENTER, name="CoverSubtitle")
        if note:
            text(slide, note, 1.0, 6.75, SLIDE_W - 2.0, 0.35, size=11, color="grey",
                 align=PP_ALIGN.CENTER, name="CoverNote")
        return slide
    rect(slide, 0, 0, 0.18, SLIDE_H, fill="accent")
    text(slide, title, 1.0, 2.4, 10.5, 1.6, size=34, bold=True, anchor=MSO_ANCHOR.BOTTOM, name="CoverTitle")
    if subtitle:
        text(slide, subtitle, 1.0, 4.15, 10.5, 0.5, size=16, color="grey", name="CoverSubtitle")
    if note:
        text(slide, note, 1.0, 6.6, 10.5, 0.35, size=10, color="grey", italic=True, name="CoverNote")
    return slide


def content_slide(prs, title, tracker="", section=None):
    """Content slide: tracker label, action title, rule, page number, optional section navigator.
    section: current section name (also used as tracker label if tracker is empty)."""
    title_only = _LAYOUTS.get("title_only") if _TEMPLATE["on"] else None
    if title_only is not None:
        # Template deck: the action title goes into the master's own title placeholder, so the
        # template's title font, size and position apply. Body helpers start at BODY_TOP: check the
        # rendered slide; if the template's title sits lower, pass y= to the exhibit helpers.
        slide = prs.slides.add_slide(title_only)
        title_ph = slide.shapes.title
        _clear_placeholders(slide, keep=(title_ph.placeholder_format.idx,) if title_ph is not None else ())
        if title_ph is not None:
            title_ph.text_frame.text = title
            title_ph.name = "Title"
            # Template font, colour and position stay. Only the size is set, so that an action title
            # fits two lines in the master's box (cap 28 pt, floor 18 pt).
            width_in = Emu(title_ph.width).inches
            size = int(min(28, max(18, width_in * 72 * 2 / (0.52 * max(len(title), 1)))))
            for p in title_ph.text_frame.paragraphs:
                for r in p.runs:
                    r.font.size = Pt(size)
            slide._dk_body_top = max(BODY_TOP, Emu(title_ph.top + title_ph.height).inches + 0.2)
            room_for_tracker = Emu(title_ph.top).inches >= TRACKER_Y + 0.3
        else:
            text(slide, title, LEFT, TITLE_Y, TITLE_W, TITLE_H, size=20, bold=True, name="Title", space_after=0)
            room_for_tracker = True
    else:
        slide = _new_slide(prs)
        text(slide, title, LEFT, TITLE_Y, TITLE_W, TITLE_H, size=20, bold=True, name="Title", space_after=0)
        hline(slide, LEFT, BODY_TOP - 0.15, BODY_W)
        room_for_tracker = True
    if not room_for_tracker:
        _page_number(prs, slide)
        return slide          # the template owns the top zone: no tracker or navigator on top of it
    label = tracker or section or ""
    if label:
        text(slide, label.upper(), LEFT, TRACKER_Y, 5.5, 0.25, size=9, color="accent", bold=True, name="Tracker")
    _navigator(slide, section or tracker)
    _page_number(prs, slide)
    return slide


def body_top(slide):
    """Where the body may start on this slide: BODY_TOP, or lower if a template title sits lower.
    Pass it as y= to exhibit helpers in template decks: bar_chart(s, ..., y=body_top(s) + 0.4)."""
    return getattr(slide, "_dk_body_top", BODY_TOP)


def divider_slide(prs, section, takeaway, number=None):
    """Section divider: section name plus the section's one-line takeaway (its own action title).
    Template deck with a divider layout: the master's placeholders carry it, nothing is drawn on top."""
    if _TEMPLATE["on"] and "divider" in _LAYOUTS:
        slide = prs.slides.add_slide(_LAYOUTS["divider"])
        title_ph = slide.shapes.title
        others = [p for p in slide.placeholders if title_ph is None or p.placeholder_format.idx != title_ph.placeholder_format.idx]
        body_ph = next((p for p in others if "BODY" in str(p.placeholder_format.type)), None)
        keep = []
        if title_ph is not None:
            title_ph.text_frame.text, title_ph.name = takeaway, "DividerTitle"
            keep.append(title_ph.placeholder_format.idx)
        else:
            text(slide, takeaway, LEFT, 2.6, BODY_W, 1.6, size=28, bold=True, name="DividerTitle")
        label = f"{number:02d}  {section}" if isinstance(number, int) else section
        if body_ph is not None:
            body_ph.text_frame.text, body_ph.name = label, "DividerSection"
            keep.append(body_ph.placeholder_format.idx)
        _clear_placeholders(slide, keep=keep)
        _page_number(prs, slide)
        return slide
    slide = _new_slide(prs, "divider")
    rect(slide, 0, 0, 4.3, SLIDE_H, fill="accent")
    if number is not None:
        text(slide, f"{number:02d}" if isinstance(number, int) else str(number), 0.7, 2.2, 3.0, 1.4,
             size=72, bold=True, color=WHITE, name="DividerNumber")
    text(slide, section, 0.7, 3.7, 3.3, 1.2, size=24, bold=True, color=WHITE, name="DividerSection")
    text(slide, takeaway, 5.0, 2.6, 7.6, 2.2, size=26, bold=True, anchor=MSO_ANCHOR.MIDDLE, name="DividerTitle")
    if _SECTIONS:
        y = 5.4
        for name in _SECTIONS:
            on = name == section
            text(slide, ("▸ " if on else "   ") + name, 5.0, y, 7.6, 0.3, size=12,
                 color="accent" if on else "grey", bold=on, name="DividerAgenda")
            y += 0.32
    _page_number(prs, slide)
    return slide


def ghost_slide(prs, title, exhibit, data_needed="", confidence="likely", section=None):
    """Ghost-deck page: final action title, the intended exhibit in words, data needed, confidence
    (solid | likely | speculative). Deliberately unstyled so reviewers critique logic, not polish."""
    slide = content_slide(prs, title, section=section)
    rect(slide, LEFT, BODY_TOP, BODY_W, BODY_BOTTOM - BODY_TOP, line="grey", line_w=1.0, name="Ghost")
    text(slide, "EXHIBIT", LEFT + 0.4, BODY_TOP + 0.4, 3, 0.3, size=10, bold=True, color="grey")
    text(slide, exhibit, LEFT + 0.4, BODY_TOP + 0.75, BODY_W - 0.8, 1.6, size=16)
    if data_needed:
        text(slide, "DATA NEEDED", LEFT + 0.4, BODY_TOP + 2.6, 3, 0.3, size=10, bold=True, color="grey")
        text(slide, data_needed, LEFT + 0.4, BODY_TOP + 2.95, BODY_W - 0.8, 1.2, size=14)
    text(slide, f"Confidence: {confidence}", LEFT + 0.4, BODY_BOTTOM - 0.6, 5, 0.3, size=12,
         color="negative" if confidence == "speculative" else "grey", bold=True, name="Confidence")
    return slide


def illustrative(slide, label="Illustrative"):
    """Small label, top right, on any slide whose numbers are sample or invented data."""
    box = rect(slide, SLIDE_W - RIGHT - 1.5, TRACKER_Y - 0.02, 1.5, 0.3, line="grey",
               shape=MSO_SHAPE.ROUNDED_RECTANGLE, name="Illustrative")
    _shape_text(box, label, 9, "grey")
    return box


def source(slide, value, footnote=""):
    """Source line bottom left; optional footnote above it."""
    if footnote:
        text(slide, footnote, LEFT, SOURCE_Y - 0.28, BODY_W - 1, 0.26, size=9, color="grey", name="Footnote")
    return text(slide, value, LEFT, SOURCE_Y, BODY_W - 1, 0.3, size=9, color="grey", name="Source")


def unit_line(slide, value, x=LEFT, y=BODY_TOP, w=BODY_W):
    """Chart header: measure, scope, period, unit. 'Gross margin by channel, FY2025, %'."""
    return text(slide, value, x, y, w, 0.3, size=12, bold=True, name="Unit")


# ----------------------------------------------------------------- consult: text exhibits

def exec_summary(slide, rows, ask=None, top=BODY_TOP + 0.05, heading_w=2.6):
    """rows: (heading, sentence) pairs, 3-5 of them. ask: optional decision request in an accent band."""
    bottom = BODY_BOTTOM - (0.85 if ask else 0)
    height = (bottom - top) / max(len(rows), 1)
    for i, (heading, sentence) in enumerate(rows):
        y = top + i * height
        text(slide, heading, LEFT, y + 0.12, heading_w, height - 0.2, size=14, bold=True, color="accent")
        text(slide, sentence, LEFT + heading_w + 0.3, y + 0.12, BODY_W - heading_w - 0.3, height - 0.2, size=14)
        if i < len(rows) - 1:
            hline(slide, LEFT, y + height, BODY_W)
    if ask:
        band = rect(slide, LEFT, bottom + 0.15, BODY_W, 0.65, fill="accent", name="Ask")
        _shape_text(band, ask, 14, WHITE, bold=True, align=PP_ALIGN.LEFT)
        band.text_frame.margin_left = Inches(0.25)


def callout(slide, heading, bullets, x=None, y=BODY_TOP, w=3.7, h=None):
    """Takeaway panel, normally on the right third beside a chart (chart w=8.3)."""
    x = SLIDE_W - RIGHT - w if x is None else x
    h = (BODY_BOTTOM - y) if h is None else h
    rect(slide, x, y, w, h, fill="pale", name="Callout")
    text(slide, heading, x + 0.25, y + 0.2, w - 0.5, 0.4, size=13, bold=True, color="accent")
    text(slide, bullets, x + 0.25, y + 0.7, w - 0.5, h - 0.9, size=12, bullets=True, space_after=8)


def annotate(slide, value, x, y, target, w=2.4, h=0.6, size=12):
    """Data callout: short claim at (x, y) with a thin accent leader line to target=(tx, ty) and a dot.
    Place the text in white space; at most two per exhibit. Chart internals have no fixed coordinates:
    for a target inside a chart, estimate, render, and correct the target before shipping."""
    tx, ty = target
    box = text(slide, value, x, y, w, h, size=size, bold=True, color="accent", name="Annotation")
    sx = x if tx < x else (x + w if tx > x + w else tx)
    sy = y + h / 2 if (tx < x or tx > x + w) else (y if ty < y else y + h)
    line(slide, sx, sy, tx, ty, color="accent", weight=1.0, name="Leader")
    dot = rect(slide, tx - 0.06, ty - 0.06, 0.12, 0.12, fill="accent", shape=MSO_SHAPE.OVAL, name="Marker")
    return box, dot


def columns(slide, items, highlight=None, band=None, x=LEFT, y=BODY_TOP, w=BODY_W, h=None, size=13):
    """MECE parallel columns. items: (heading, body) with body a string or list of bullets.
    band: optional spanning summary above the columns. highlight: index of the column in accent."""
    h = (BODY_BOTTOM - y) if h is None else h
    if band:
        b = rect(slide, x, y, w, 0.6, fill="accent_pale", name="Band")
        _shape_text(b, band, 14, "ink", bold=True)
        y, h = y + 0.8, h - 0.8
    n = len(items)
    cw = (w - GUTTER * (n - 1)) / n
    for i, (heading, body) in enumerate(items):
        cx = x + i * (cw + GUTTER)
        on = i == highlight
        head = rect(slide, cx, y, cw, 0.55, fill="accent" if on else "pale", name="ColumnHead")
        _shape_text(head, heading, 14, WHITE if on else "ink", bold=True)
        text(slide, body if isinstance(body, list) else [body], cx + 0.1, y + 0.75, cw - 0.2, h - 0.85,
             size=size, bullets=isinstance(body, list), space_after=6)
        hline(slide, cx, y + h, cw, color="accent" if on else "light", weight=1.5 if on else 0.75)


def matrix_2x2(slide, x_axis, y_axis, quadrants, highlight=None, x=LEFT + 0.6, y=BODY_TOP + 0.1, w=7.6, h=4.4):
    """2x2 framework. x_axis/y_axis: (low_label, high_label, axis_name).
    quadrants: four (heading, line) in order top-left, top-right, bottom-left, bottom-right.
    highlight: index of the quadrant the title talks about. Use w=7.6 and a callout on the right."""
    qw, qh = w / 2, h / 2
    cells = [(x, y), (x + qw, y), (x, y + qh), (x + qw, y + qh)]
    for i, ((cx, cy), (heading, body)) in enumerate(zip(cells, quadrants)):
        on = i == highlight
        r = rect(slide, cx + 0.04, cy + 0.04, qw - 0.08, qh - 0.08, fill="accent" if on else "pale", name="Quadrant")
        r.text_frame.word_wrap = True
        text(slide, heading, cx + 0.25, cy + 0.2, qw - 0.5, 0.4, size=14, bold=True, color=WHITE if on else "ink")
        text(slide, body, cx + 0.25, cy + 0.65, qw - 0.5, qh - 0.8, size=12, color=WHITE if on else "ink")
    line(slide, x, y + h + 0.1, x + w, y + h + 0.1, color="grey", weight=1.0)
    line(slide, x - 0.1, y, x - 0.1, y + h, color="grey", weight=1.0)
    text(slide, x_axis[0], x, y + h + 0.15, 2, 0.3, size=10, color="grey", name="AxisLabel")
    text(slide, x_axis[1], x + w - 2, y + h + 0.15, 2, 0.3, size=10, color="grey", align=PP_ALIGN.RIGHT, name="AxisLabel")
    text(slide, x_axis[2], x, y + h + 0.42, w, 0.3, size=12, bold=True, align=PP_ALIGN.CENTER, name="AxisLabel")
    text(slide, y_axis[1], x - 0.6, y, 0.45, 0.3, size=10, color="grey", align=PP_ALIGN.RIGHT, name="AxisLabel")
    text(slide, y_axis[0], x - 0.6, y + h - 0.3, 0.45, 0.3, size=10, color="grey", align=PP_ALIGN.RIGHT, name="AxisLabel")
    lab = text(slide, y_axis[2], x - 0.95 - h / 2 + 0.15, y + h / 2 - 0.15, h, 0.3, size=12, bold=True,
               align=PP_ALIGN.CENTER, name="AxisLabel")
    lab.rotation = 270


def process_flow(slide, steps, highlight=None, x=LEFT, y=BODY_TOP + 0.1, w=BODY_W, h=0.8, body_h=3.2):
    """Linear process / value chain. steps: (verb-led heading, one line of substance).
    highlight: index of the stage that is broken or matters."""
    n = len(steps)
    sw = (w + 0.15 * (n - 1)) / n
    for i, (heading, body) in enumerate(steps):
        sx = x + i * (sw - 0.15)
        on = i == highlight
        shape = MSO_SHAPE.PENTAGON if i == 0 else MSO_SHAPE.CHEVRON
        c = rect(slide, sx, y, sw, h, fill="accent" if on else "pale", shape=shape, name="Step")
        _shape_text(c, heading, 13, WHITE if on else "ink", bold=True)
        text(slide, body if isinstance(body, list) else [body], sx + 0.25, y + h + 0.25, sw - 0.6, body_h,
             size=12, bullets=isinstance(body, list), space_after=6)


def kpi_row(slide, items, x=LEFT, y=BODY_TOP + 0.2, w=BODY_W, highlight=None, size=40):
    """Row of headline numbers. items: (value, label). Works in both themes."""
    n = len(items)
    cw = (w - GUTTER * (n - 1)) / n
    for i, (value, label) in enumerate(items):
        cx = x + i * (cw + GUTTER)
        text(slide, value, cx, y, cw, 0.9, size=size, bold=True,
             color="accent" if i == highlight else "ink", name="KPI")
        text(slide, label, cx, y + 0.95, cw, 0.8, size=12, color="grey")


# ----------------------------------------------------------------- charts

def _clean_chart(chart, legend=False):
    chart.has_title = False
    chart.font.name = T["font"]
    chart.font.size = Pt(11)
    chart.font.color.rgb = rgb(T["ink"])
    chart.has_legend = legend
    if legend:
        chart.legend.position = XL_LEGEND_POSITION.TOP
        chart.legend.include_in_layout = False
        chart.legend.font.size = Pt(10)
        chart.legend.font.color.rgb = rgb(T["ink"])


def _axes(chart, show_value_axis=False):
    va = chart.value_axis
    va.has_major_gridlines = False
    va.has_minor_gridlines = False
    va.visible = show_value_axis
    va.tick_labels.font.size = Pt(10)
    va.major_tick_mark = XL_TICK_MARK.NONE
    ca = chart.category_axis
    ca.has_major_gridlines = False
    ca.format.line.color.rgb = rgb(T["light"])
    ca.tick_labels.font.size = Pt(11)
    ca.tick_labels.font.color.rgb = rgb(T["ink"])
    ca.major_tick_mark = XL_TICK_MARK.NONE
    ca.tick_label_position = XL_TICK_LABEL_POSITION.LOW   # labels stay clear of negative bars


def _labels(plot, number_format, size=11, position=None):
    plot.has_data_labels = True
    labels = plot.data_labels
    labels.number_format = number_format
    labels.number_format_is_linked = False
    labels.font.size = Pt(size)
    labels.font.color.rgb = rgb(T["ink"])
    if position is not None:
        labels.position = position


def _chart_box(slide, unit, x, y, w, h):
    h = (BODY_BOTTOM - y) if h is None else h
    if unit:
        unit_line(slide, unit, x, y - 0.4, w)
    return h


def bar_chart(slide, categories, values, highlight=None, horizontal=True, number_format='0.0',
              x=LEFT, y=BODY_TOP + 0.4, w=BODY_W, h=None, unit=None, series_name="Value"):
    """Single-series ranking or comparison; bars grey, highlight (index or list) in accent.
    Horizontal bars read top to bottom in the order given: sort before passing."""
    h = _chart_box(slide, unit, x, y, w, h)
    data = CategoryChartData()
    data.categories = categories
    data.add_series(series_name, values)
    kind = XL_CHART_TYPE.BAR_CLUSTERED if horizontal else XL_CHART_TYPE.COLUMN_CLUSTERED
    chart = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), data).chart
    _clean_chart(chart)
    _axes(chart)
    if horizontal:
        chart.category_axis.reverse_order = True
    plot = chart.plots[0]
    plot.gap_width = 60
    _labels(plot, number_format, position=XL_LABEL_POSITION.OUTSIDE_END)
    marks = set(highlight if isinstance(highlight, (list, tuple, set)) else [highlight])
    for i, point in enumerate(plot.series[0].points):
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(T["accent"] if i in marks else T["chart_greys"][1 if T["mode"] == "consult" else 0])
    return chart


def column_chart(slide, categories, series, number_format='0', stacked=False, percent=False,
                 highlight_series=None, x=LEFT, y=BODY_TOP + 0.4, w=BODY_W, h=None, unit=None):
    """series: list of (name, values). Greys for context, accent for highlight_series (index).
    stacked=True for mix; percent=True for 100% stacked composition."""
    h = _chart_box(slide, unit, x, y, w, h)
    data = CategoryChartData()
    data.categories = categories
    for name, values in series:
        data.add_series(name, values)
    kind = (XL_CHART_TYPE.COLUMN_STACKED_100 if percent else XL_CHART_TYPE.COLUMN_STACKED if stacked
            else XL_CHART_TYPE.COLUMN_CLUSTERED)
    chart = slide.shapes.add_chart(kind, Inches(x), Inches(y), Inches(w), Inches(h), data).chart
    _clean_chart(chart, legend=len(series) > 1)
    _axes(chart)
    plot = chart.plots[0]
    plot.gap_width = 60
    if stacked or percent:
        plot.overlap = 100
    _labels(plot, number_format,
            position=XL_LABEL_POSITION.CENTER if (stacked or percent) else XL_LABEL_POSITION.OUTSIDE_END)
    greys = T["chart_greys"]
    for i, s in enumerate(plot.series):
        s.format.fill.solid()
        s.format.fill.fore_color.rgb = rgb(T["accent"] if i == highlight_series else greys[i % len(greys)])
    return chart


def line_chart(slide, categories, series, number_format='0', highlight_series=0,
               x=LEFT, y=BODY_TOP + 0.4, w=BODY_W, h=None, unit=None, labels=True):
    """Trend. At most 3 lines; the one the title talks about in accent, others grey."""
    h = _chart_box(slide, unit, x, y, w, h)
    data = CategoryChartData()
    data.categories = categories
    for name, values in series:
        data.add_series(name, values)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.LINE_MARKERS, Inches(x), Inches(y), Inches(w), Inches(h), data).chart
    _clean_chart(chart, legend=len(series) > 1)
    _axes(chart)
    plot = chart.plots[0]
    if labels:
        _labels(plot, number_format, position=XL_LABEL_POSITION.ABOVE)
    for i, s in enumerate(plot.series):
        colour = T["accent"] if i == highlight_series else T["chart_greys"][0]
        s.format.line.color.rgb = rgb(colour)
        s.format.line.width = Pt(2.25)
        s.smooth = False
        s.marker.format.fill.solid()
        s.marker.format.fill.fore_color.rgb = rgb(colour)
        s.marker.format.line.color.rgb = rgb(colour)
    return chart


def waterfall(slide, steps, number_format='+0.0;-0.0;0.0', total_format='0.0',
              x=LEFT, y=BODY_TOP + 0.4, w=BODY_W, h=None, unit=None):
    """Bridge as a stacked column with an invisible base (editable everywhere).
    steps: (label, value, kind) with kind 'total' or 'delta'. First and last are normally totals.
    Keep to 7 steps; group small drivers into 'Other'. Works for bridges that stay above zero."""
    h = _chart_box(slide, unit, x, y, w, h)
    base, bar, kinds, running = [], [], [], 0.0
    for label, value, kind in steps:
        if kind == "total":
            base.append(0)
            bar.append(value)
            running = value
        else:
            base.append(running + min(value, 0))
            bar.append(abs(value))
            running += value
        kinds.append((kind, value))
    data = CategoryChartData()
    data.categories = [s[0] for s in steps]
    data.add_series("base", base)
    data.add_series("value", bar)
    chart = slide.shapes.add_chart(XL_CHART_TYPE.COLUMN_STACKED, Inches(x), Inches(y), Inches(w), Inches(h), data).chart
    _clean_chart(chart)
    _axes(chart)
    plot = chart.plots[0]
    plot.gap_width = 50
    plot.overlap = 100
    base_series, value_series = plot.series
    base_series.format.fill.background()
    base_series.format.line.fill.background()
    scale = max(abs(v) for v in bar) or 1
    for i, point in enumerate(value_series.points):
        kind, value = kinds[i]
        colour = T["accent"] if kind == "total" else (T["negative"] if value < 0 else T["chart_greys"][0])
        point.format.fill.solid()
        point.format.fill.fore_color.rgb = rgb(colour)
        if kind != "total" and abs(value) < 0.08 * scale and base[i] > 0.05 * scale:
            # thin bar: label sits just under it, on the invisible base, in ink
            lab = base_series.points[i].data_label
            lab.has_text_frame = True
            lab.position = XL_LABEL_POSITION.INSIDE_END
            lab.text_frame.text = _fmt(value, number_format)
            _style(lab.text_frame.paragraphs[0].runs[0], 11, T["ink"])
            continue
        label = point.data_label
        label.has_text_frame = True
        label.position = XL_LABEL_POSITION.INSIDE_END if kind == "total" else XL_LABEL_POSITION.CENTER
        label.text_frame.text = _fmt(value, total_format if kind == "total" else number_format)
        run = label.text_frame.paragraphs[0].runs[0]
        _style(run, 11, WHITE if (kind == "total" or value < 0) else T["ink"], bold=kind == "total")
    return chart


def _fmt(value, fmt):
    head = fmt.split(";")[0]
    sign = "+" if head.startswith("+") and value > 0 else ""
    decimals = len(head.split(".")[1]) if "." in head else 0
    return f"{sign}{value:,.{decimals}f}"


# ----------------------------------------------------------------- tables

def _cell_border(cell, side="B", color=None, width=0.75):
    tcPr = cell._tc.get_or_add_tcPr()
    tag = {"L": "a:lnL", "R": "a:lnR", "T": "a:lnT", "B": "a:lnB"}[side]
    for old in tcPr.findall(qn(tag)):
        tcPr.remove(old)
    ln = etree.SubElement(tcPr, qn(tag))
    ln.set("w", str(int(Pt(width))))
    if width == 0:
        etree.SubElement(ln, qn("a:noFill"))
        return
    fill = etree.SubElement(ln, qn("a:solidFill"))
    clr = etree.SubElement(fill, qn("a:srgbClr"))
    clr.set("val", _c(color, "light"))


def table(slide, header, rows, col_widths=None, highlight_row=None, size=12,
          x=LEFT, y=BODY_TOP, w=BODY_W, row_h=0.5, name=None):
    """Native table. highlight_row: index into rows to shade (e.g. the recommended option)."""
    n_rows, n_cols = len(rows) + 1, len(header)
    shape = slide.shapes.add_table(n_rows, n_cols, Inches(x), Inches(y), Inches(w), Inches(row_h * n_rows))
    shape.name = name or "Table"
    tbl = shape.table
    tbl.first_row = True
    tbl.horz_banding = False
    widths = col_widths or [w / n_cols] * n_cols
    for i, cw in enumerate(widths):
        tbl.columns[i].width = Inches(cw)
    for r in range(n_rows):
        tbl.rows[r].height = Inches(row_h)
        for c in range(n_cols):
            cell = tbl.cell(r, c)
            value = header[c] if r == 0 else rows[r - 1][c]
            cell.fill.solid()
            hl = highlight_row is not None and r - 1 == highlight_row
            cell.fill.fore_color.rgb = rgb(T["pale"] if r == 0 else (T["accent_pale"] if hl else T["bg"]))
            cell.margin_left = cell.margin_right = Inches(0.1)
            cell.margin_top = cell.margin_bottom = Inches(0.05)
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE
            frame = cell.text_frame
            frame.word_wrap = True
            frame.text = ""
            _runs(frame.paragraphs[0], str(value), size, None, r == 0 or c == 0, False)
            for side in ("L", "R", "T"):
                _cell_border(cell, side, width=0)
            _cell_border(cell, "B", color="grey" if r == 0 else "light")
    return tbl


def next_steps(slide, rows, **kw):
    """rows: (action, owner, date). Ends a consult deck: decisions, owners, dates."""
    return table(slide, ["Action", "Owner", "By"], rows, col_widths=[8.0, 2.6, 1.733], name="NextSteps", **kw)


# ----------------------------------------------------------------- keynote slides

def _fit_size(value, width_in, max_size, min_size=28, glyph=0.56):
    longest = max((len(_ACCENT_RE.sub(r"\1", s)) for s in str(value).split("\n")), default=1)
    if longest > 22 and max_size >= 80:      # long statement: size for two lines, not one thin line
        longest = int(longest / 2 * 1.35)
    size = int(width_in * 72 / (glyph * max(longest, 1)))
    return max(min_size, min(max_size, size))


def statement(prs, value, sub=None, size=None, align=PP_ALIGN.CENTER):
    """One idea, a few words, huge type. [[word]] in accent. Use for the headline, the villain,
    the turn, section openers. Aim for 1-8 words."""
    slide = _new_slide(prs, "statement")
    size = size or _fit_size(value, SLIDE_W - 2.0, 96, glyph=0.62)
    text(slide, value, 1.0, 1.2, SLIDE_W - 2.0, 4.0 if sub else 5.1, size=size, bold=True, align=align,
         anchor=MSO_ANCHOR.BOTTOM if sub else MSO_ANCHOR.MIDDLE, name="Statement", line_spacing=0.95)
    if sub:
        text(slide, sub, 1.5, 5.4, SLIDE_W - 3.0, 1.0, size=24, color="grey", align=align, name="Sub")
    return slide


def big_number(prs, number, label, fine_print=None, context=None):
    """One number per slide, made meaningful by one line. fine_print: test conditions or source
    (every performance claim needs it). context: optional comparison anchor ('vs 41% industry')."""
    slide = _new_slide(prs, "statement")
    size = _fit_size(number, SLIDE_W - 2.0, 200, min_size=72, glyph=0.7)
    text(slide, number, 1.0, 1.0, SLIDE_W - 2.0, 3.4, size=size, bold=True, color="accent",
         align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM, name="BigNumber", line_spacing=0.9)
    text(slide, label, 1.5, 4.6, SLIDE_W - 3.0, 0.8, size=28, align=PP_ALIGN.CENTER, name="Label")
    if context:
        text(slide, context, 1.5, 5.4, SLIDE_W - 3.0, 0.5, size=20, color="grey", align=PP_ALIGN.CENTER, name="Context")
    if fine_print:
        fine(slide, fine_print)
    return slide


def fine(slide, value):
    """Fine print, bottom centre: test conditions, sources, footnotes for claims."""
    return text(slide, value, 1.0, 6.85, SLIDE_W - 2.0, 0.4, size=10, color="grey",
                align=PP_ALIGN.CENTER, name="Source")


def three(prs, headline, items, highlight=None):
    """Rule of three: headline plus three (word, one line) pillars."""
    slide = _new_slide(prs, "statement")
    text(slide, headline, 1.0, 0.9, SLIDE_W - 2.0, 1.0, size=40, bold=True, align=PP_ALIGN.CENTER, name="Statement")
    cw = (SLIDE_W - 2.0 - 2 * 0.5) / 3
    for i, (word, body) in enumerate(items[:3]):
        cx = 1.0 + i * (cw + 0.5)
        text(slide, word, cx, 2.9, cw, 1.2, size=_fit_size(word, cw, 54, glyph=0.7), bold=True,
             color="accent" if (highlight is None or i == highlight) else "ink", align=PP_ALIGN.CENTER,
             anchor=MSO_ANCHOR.BOTTOM, name="Pillar")
        text(slide, body, cx + 0.2, 4.3, cw - 0.4, 1.6, size=20, color="grey", align=PP_ALIGN.CENTER)
    return slide


def reveal(prs, headline, items, size=40):
    """Progressive reveal without animation: one slide per item; earlier items dim to grey,
    the newest in accent. Use for '3 things' builds, feature lists, the turn. Returns the slides."""
    slides = []
    for k in range(1, len(items) + 1):
        slide = _new_slide(prs, "statement")
        if headline:
            text(slide, headline, 1.0, 0.8, SLIDE_W - 2.0, 0.8, size=28, color="grey", align=PP_ALIGN.CENTER, name="Sub")
        n = len(items)
        top = 1.9 + max(0, (4 - n)) * 0.45
        for i in range(k):
            text(slide, items[i], 1.0, top + i * (size / 72 * 1.35), SLIDE_W - 2.0, size / 72 * 1.3,
                 size=size, bold=True, color="accent" if i == k - 1 else "grey", align=PP_ALIGN.CENTER,
                 name="Statement" if i == k - 1 else "Revealed")
        slides.append(slide)
    return slides


def versus(prs, headline, left, right, fine_print=None):
    """Old way vs new way, or us vs the familiar benchmark. left/right: (label, value, line).
    The right side is the hero (accent)."""
    slide = _new_slide(prs, "statement")
    text(slide, headline, 1.0, 0.8, SLIDE_W - 2.0, 1.0, size=36, bold=True, align=PP_ALIGN.CENTER, name="Statement")
    for i, (label, value, body) in enumerate([left, right]):
        cx = 1.0 + i * 5.9
        hero = i == 1
        text(slide, label, cx, 2.3, 5.4, 0.6, size=22, color="grey", align=PP_ALIGN.CENTER)
        text(slide, value, cx, 2.95, 5.4, 1.7, size=_fit_size(value, 5.0, 110, glyph=0.72), bold=True,
             color="accent" if hero else "grey", align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.MIDDLE,
             name="BigNumber" if hero else "Compare")
        text(slide, body, cx + 0.3, 4.8, 4.8, 1.2, size=18, color="ink" if hero else "grey", align=PP_ALIGN.CENTER)
    line(slide, SLIDE_W / 2, 2.4, SLIDE_W / 2, 5.8, color="light", weight=1.0)
    if fine_print:
        fine(slide, fine_print)
    return slide


def image_slide(prs, image=None, caption=None, placeholder="Product shot", full_bleed=True):
    """Hero visual. image: path to a file the user supplied or owns. Without one, a labelled
    placeholder is drawn (named ImagePlaceholder) so nobody mistakes it for a finished slide."""
    slide = _new_slide(prs, "statement")
    if image:
        if full_bleed:
            slide.shapes.add_picture(image, 0, 0, Inches(SLIDE_W), Inches(SLIDE_H)).name = "Hero"
        else:
            slide.shapes.add_picture(image, Inches(1.5), Inches(0.8), height=Inches(5.0)).name = "Hero"
    else:
        r = rect(slide, 1.5, 0.7, SLIDE_W - 3.0, 5.0, fill="pale", line="grey", name="ImagePlaceholder")
        _shape_text(r, f"IMAGE PLACEHOLDER\n{placeholder}", 20, "grey")
    if caption:
        text(slide, caption, 1.0, 6.0, SLIDE_W - 2.0, 0.8, size=28, bold=True, align=PP_ALIGN.CENTER, name="Caption")
    return slide


def video_slide(prs, clip, poster, beat=None, caption=None, layout=None, full_bleed=True):
    """Clip slide for a beat, e.g. a motion-craft render (renders/beats/B02.mp4). poster: the
    still PowerPoint shows before play and renderers show instead of the video; required. The clip
    is embedded, plays on click (no autoplay) and is named Clip; its alt text records the beat.
    layout: a role from use_layouts() (default: the statement / blank layout). Without full_bleed
    the clip sits at 16:9 in the upper area with an optional caption beneath."""
    if not poster:
        raise ValueError("video_slide needs a poster frame (renders/beats/<beat>.jpg)")
    for path in (clip, poster):
        if not os.path.exists(path):
            raise FileNotFoundError(path)
    slide = _new_slide(prs, layout or "statement")
    if full_bleed:
        x, y, w, h = 0, 0, SLIDE_W, SLIDE_H
    else:
        w = SLIDE_W - 3.0
        h = w * 9 / 16
        x, y = 1.5, 0.5
    movie = slide.shapes.add_movie(clip, Inches(x), Inches(y), Inches(w), Inches(h),
                                   poster_frame_image=poster, mime_type="video/mp4")
    movie.name = "Clip"
    movie._element.nvPicPr.cNvPr.set("descr", f"beat {beat or '–'} · {os.path.basename(clip)}")
    if caption and not full_bleed:
        text(slide, caption, 1.0, y + h + 0.2, SLIDE_W - 2.0, 0.7, size=24, bold=True, align=PP_ALIGN.CENTER,
             name="Caption")
    return slide


def video_slide_from_clips(prs, clips_json, beat, cut=None, **kw):
    """video_slide() for one beat of a motion-craft clips.json ([{beat, cut, file, poster, ...}]).
    Paths in clips.json are resolved against the folder of clips.json, then its parent, then the
    working folder. cut: pick the clip from this cut when several cuts have the beat."""
    with open(clips_json, encoding="utf-8") as f:
        clips = json.load(f)
    hits = [c for c in clips if c.get("beat") == beat and (cut is None or c.get("cut") == cut)]
    if not hits:
        raise KeyError(f"no clip for {beat} in {clips_json}" + (f" (cut {cut})" if cut else ""))
    base = os.path.dirname(os.path.abspath(clips_json))

    def resolve(path):
        for root in (base, os.path.dirname(base), os.getcwd()):
            candidate = os.path.join(root, path)
            if os.path.exists(candidate):
                return candidate
        return path

    clip = hits[0]
    return video_slide(prs, resolve(clip["file"]), resolve(clip["poster"]), beat=beat, **kw)


def quote(prs, value, attribution):
    """Customer or expert voice. Only real, attributable quotes; never invent one."""
    slide = _new_slide(prs, "statement")
    text(slide, f"“{value}”", 1.5, 1.4, SLIDE_W - 3.0, 3.6, size=_fit_size(value, (SLIDE_W - 3.0) * 2.2, 44, min_size=28),
         bold=True, align=PP_ALIGN.CENTER, anchor=MSO_ANCHOR.BOTTOM, name="Statement")
    text(slide, attribution, 1.5, 5.3, SLIDE_W - 3.0, 0.6, size=20, color="grey", align=PP_ALIGN.CENTER, name="Sub")
    return slide


def closing(prs, headline, details=(), cta=None):
    """Close on what happens next: availability, price, how to start. Never 'Questions?'."""
    slide = _new_slide(prs, "statement")
    text(slide, headline, 1.0, 1.4, SLIDE_W - 2.0, 1.6, size=54, bold=True, align=PP_ALIGN.CENTER,
         anchor=MSO_ANCHOR.BOTTOM, name="Statement")
    if details:
        text(slide, list(details), 2.0, 3.4, SLIDE_W - 4.0, 1.8, size=24, color="grey", align=PP_ALIGN.CENTER)
    if cta:
        b = rect(slide, SLIDE_W / 2 - 2.6, 5.4, 5.2, 0.8, fill="accent", shape=MSO_SHAPE.ROUNDED_RECTANGLE, name="CTA")
        _shape_text(b, cta, 22, WHITE, bold=True)
    return slide


def keynote_chart_slide(prs, headline, sub=None):
    """Keynote slide that carries one simple chart: short headline, room below for one exhibit.
    Draw the chart with bar_chart/line_chart(slide, ..., x=1.5, y=2.2, w=10.3, h=4.3)."""
    slide = _new_slide(prs, "statement")
    text(slide, headline, 1.0, 0.6, SLIDE_W - 2.0, 0.9, size=36, bold=True, align=PP_ALIGN.CENTER, name="Statement")
    if sub:
        text(slide, sub, 1.0, 1.45, SLIDE_W - 2.0, 0.5, size=20, color="grey", align=PP_ALIGN.CENTER, name="Sub")
    return slide


__all__ = [n for n in dir() if not n.startswith("_") and n not in (
    "json", "os", "re", "etree", "Presentation", "CategoryChartData", "RGBColor", "qn", "Emu")]
