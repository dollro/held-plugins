"""template_profile.py: read a PowerPoint master (.pptx/.potx) and write a design guide from it.

Usage:
    python template_profile.py template.pptx [outdir] [--sampler]

Writes to outdir (default: ./design-guide/):
    design-guide.json  machine-readable tokens: slide size, theme colours, fonts, layout roles,
                       title zone, body top, protected master zones (logo, bands, footers).
                       deckkit.apply_design_guide(prs, "design-guide.json") applies it.
    design-guide.md    human-readable guide with the same facts and TODOs for rules the template
                       cannot tell (tone, imagery, icon style, do/don't). Fill these with the user.
    layout-sampler.pptx (with --sampler) one slide per layout, every placeholder labelled with its
                       index and type, to render and look at before choosing layout roles.

The script only reads the template. It never edits or re-saves the user's file.
"""
import io
import json
import os
import sys
import zipfile

from lxml import etree
from pptx import Presentation
from pptx.util import Emu

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
NS = {"a": A[1:-1]}

ROLE_HINTS = {
    "cover": ("title slide", "titelfolie", "title", "cover", "titel"),
    "title_only": ("title only", "nur titel", "titel only", "title-only"),
    "content": ("title and content", "titel und inhalt", "content", "inhalt"),
    "two_content": ("two content", "zwei inhalte", "comparison", "vergleich"),
    "divider": ("section header", "abschnittsüberschrift", "section", "divider", "kapitel", "trenner"),
    "blank": ("blank", "leer", "empty"),
    "statement": ("statement", "quote", "zitat", "big number", "impact", "key message"),
    "picture": ("picture with caption", "bild mit überschrift", "picture", "bild", "image", "foto"),
    "closing": ("closing", "end", "ende", "abschluss", "thank", "danke", "contact", "kontakt"),
}


def open_any(path):
    if path.lower().endswith(".potx"):
        buf = io.BytesIO()
        with zipfile.ZipFile(path) as zin, zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zout:
            for item in zin.infolist():
                data = zin.read(item.filename)
                if item.filename == "[Content_Types].xml":
                    data = data.replace(b"presentationml.template.main+xml", b"presentationml.presentation.main+xml")
                zout.writestr(item, data)
        buf.seek(0)
        return Presentation(buf)
    return Presentation(path)


def inches(v):
    return round(Emu(v).inches, 2) if v is not None else None


def theme(prs):
    master = prs.slide_masters[0]
    part = [r.target_part for r in master.part.rels.values() if r.reltype.endswith("/theme")][0]
    root = etree.fromstring(part.blob)
    colors = {}
    scheme = root.find(".//a:clrScheme", NS)
    for el in (list(scheme) if scheme is not None else []):
        key = el.tag.replace(A, "")
        c = el[0] if len(el) else None
        if c is not None:
            colors[key] = c.get("val") if c.tag.endswith("srgbClr") else c.get("lastClr")
    fonts = {}
    for kind in ("major", "minor"):
        latin = root.find(f".//a:fontScheme/a:{kind}Font/a:latin", NS)
        if latin is not None:
            fonts["heading" if kind == "major" else "body"] = latin.get("typeface")
    return colors, fonts


def master_title_size(prs):
    master = prs.slide_masters[0]
    el = master._element.find(".//{http://schemas.openxmlformats.org/presentationml/2006/main}titleStyle//" + A + "defRPr")
    if el is not None and el.get("sz"):
        return int(el.get("sz")) / 100
    return None


def placeholders(layout):
    out = []
    for p in layout.placeholders:
        f = p.placeholder_format
        out.append({"idx": f.idx, "type": str(f.type).split(".")[-1].split(" ")[0], "name": p.name,
                    "box_in": [inches(p.left), inches(p.top), inches(p.width), inches(p.height)]})
    return out


def protected(prs):
    """Non-placeholder shapes on the master and layouts: logos, bands, lines, footers. Keep clear."""
    zones = []
    sources = [("master", prs.slide_masters[0])] + [(f"layout:{l.name}", l) for l in prs.slide_layouts]
    for where, obj in sources:
        for sh in obj.shapes:
            if sh.is_placeholder:
                continue
            zones.append({"where": where, "name": sh.name,
                          "kind": "picture" if sh.shape_type == 13 else "text" if sh.has_text_frame and sh.text_frame.text.strip() else "shape",
                          "text": sh.text_frame.text.strip()[:40] if sh.has_text_frame else "",
                          "box_in": [inches(sh.left), inches(sh.top), inches(sh.width), inches(sh.height)]})
    return zones


def guess_roles(prs):
    roles = {}
    names = [(l.name.lower().strip(), l.name) for l in prs.slide_layouts]
    for role, hints in ROLE_HINTS.items():
        for hint in hints:
            hit = next((orig for low, orig in names if low == hint), None) or \
                  next((orig for low, orig in names if hint in low), None)
            if hit:
                roles[role] = hit
                break
    return roles


def sampler(prs, path_out):
    for layout in prs.slide_layouts:
        slide = prs.slides.add_slide(layout)
        for p in slide.placeholders:
            f = p.placeholder_format
            try:
                p.text_frame.text = f"[{f.idx}] {str(f.type).split('.')[-1].split(' ')[0]}  ·  layout: {layout.name}"
            except Exception:
                pass
    prs.save(path_out)


def main(path, outdir="design-guide", make_sampler=False):
    os.makedirs(outdir, exist_ok=True)
    prs = open_any(path)
    colors, fonts = theme(prs)
    roles = guess_roles(prs)
    layouts = [{"index": i, "name": l.name, "placeholders": placeholders(l)} for i, l in enumerate(prs.slide_layouts)]
    title_box, body_top = None, None
    if "title_only" in roles:
        lay = next(l for l in prs.slide_layouts if l.name == roles["title_only"])
        t = next((p for p in lay.placeholders if "TITLE" in str(p.placeholder_format.type)), None)
        if t is not None:
            title_box = [inches(t.left), inches(t.top), inches(t.width), inches(t.height)]
            body_top = round(title_box[1] + title_box[3] + 0.2, 2)
    w, h = inches(prs.slide_width), inches(prs.slide_height)
    guide = {
        "name": os.path.splitext(os.path.basename(path))[0],
        "source": os.path.basename(path),
        "slide": {"width_in": w, "height_in": h, "aspect": "16:9" if abs(w / h - 16 / 9) < 0.02 else f"{w}x{h}"},
        "colors": {
            "ink": colors.get("dk1"), "bg": colors.get("lt1"), "dark2": colors.get("dk2"), "light2": colors.get("lt2"),
            "accent": colors.get("accent1"), "accent2": colors.get("accent2"), "accent3": colors.get("accent3"),
            "accent4": colors.get("accent4"), "accent5": colors.get("accent5"), "accent6": colors.get("accent6"),
            "grey": None, "negative": None,
        },
        "fonts": {"heading": fonts.get("heading"), "body": fonts.get("body")},
        "type_scale_pt": {"master_title": master_title_size(prs), "action_title": 20, "body": 14, "label": 9,
                          "keynote_statement": "40-96", "keynote_number": "120-200"},
        "layouts": roles,
        "zones": {"title_box_in": title_box, "body_top_in": body_top, "safe_margin_in": 0.5},
        "protected_zones": protected(prs),
        "keynote": {"stage": "master", "accent_stage_max_slides": 2,
                    "allowed_enhancements": ["larger type within the template fonts", "full-bleed image on picture layouts",
                                             "one accent word per statement", "dark or accent stage on a master layout for STAR moments"]},
        "rules": [],
        "all_layouts": layouts,
    }
    with open(os.path.join(outdir, "design-guide.json"), "w", encoding="utf-8") as f:
        json.dump(guide, f, indent=2, ensure_ascii=False)

    md = [f"# Design guide: {guide['name']}", "",
          f"Derived from `{guide['source']}` by template_profile.py. Facts below come from the master; "
          "sections marked TODO need the brand owner or the user.", "",
          "## Canvas", f"- Slide size: {w} x {h} in ({guide['slide']['aspect']})",
          f"- Title zone (Title Only layout): {title_box} in; body starts at {body_top} in",
          f"- Master title size: {guide['type_scale_pt']['master_title']} pt", "",
          "## Colours (theme)"]
    md += [f"- {k}: #{v}" for k, v in guide["colors"].items() if v]
    md += ["- Roles: ink for text, bg for pages, accent for the one thing per slide; grey and pale context tones: TODO "
           "(derive from dk2/lt2 or the brand guide)", "",
           "## Fonts", f"- Headings: {fonts.get('heading')}", f"- Body: {fonts.get('body')}",
           "- Never substitute another font. If the font is missing on a machine, say so; do not swap it.", "",
           "## Layout roles (guessed from names; confirm with the layout sampler)"]
    md += [f"- {role}: {name}" for role, name in roles.items()]
    md += ["", "## Protected zones (master and layout artwork: keep clear, never cover or move)"]
    md += [f"- {z['where']}: {z['name']} ({z['kind']}{': ' + z['text'] if z['text'] else ''}) at {z['box_in']}"
           for z in guide["protected_zones"]] or ["- none found"]
    md += ["", "## Keynote within this template",
           "- Default stage: master (keep background, logo, footer).",
           "- Allowed enhancements: " + "; ".join(guide["keynote"]["allowed_enhancements"]),
           "", "## TODO: rules the template cannot tell",
           "- Tone of voice and title style (sentence case? numbers as digits?)",
           "- Imagery: photo style, people or product, allowed sources",
           "- Icons: family, stroke weight, colour",
           "- Chart palette order beyond accent1",
           "- Logo and legal: confidentiality line, disclaimer, footer text",
           "- Do / don't examples from the brand book", ""]
    logo = next((z for z in guide["protected_zones"] if z["kind"] in ("picture", "text")), None)
    md += ["## Add-in short form (paste into Claude for PowerPoint, Settings, Instructions)", "```",
           "Template-first: use our master layouts and placeholders; never add fonts or colours.",
           f"Accent = #{guide['colors']['accent']}, only for the one thing per slide. Fonts: {fonts.get('heading')} / {fonts.get('body')}.",
           f"Consult content slides on layout '{roles.get('title_only', 'Title Only')}', full-sentence action titles in the title placeholder, body 12-16 pt.",
           f"Keep clear of master artwork{(' (e.g. ' + logo['name'] + ' at ' + str(logo['box_in']) + ' in)') if logo else ''}. Every data slide has a source line.",
           f"Keynote slides on '{roles.get('statement', roles.get('blank', 'Blank'))}', template fonts, statements 40-96 pt, one number per slide, talk in the notes.",
           "```", ""]
    md += ["## All layouts"]
    for l in layouts:
        md.append(f"- [{l['index']}] {l['name']}: " + ", ".join(f"{p['idx']}:{p['type']}" for p in l["placeholders"]))
    with open(os.path.join(outdir, "design-guide.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(md) + "\n")

    if make_sampler:
        sampler(open_any(path), os.path.join(outdir, "layout-sampler.pptx"))
    print(f"design guide written to {outdir}/ (layouts: {len(layouts)}, roles: {roles})")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], args[1] if len(args) > 1 else "design-guide", "--sampler" in sys.argv))
