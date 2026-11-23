"""export_brand_lock.py: turn a design-guide.json into brand-lock.md, the brand handoff for
motion work (motion-craft:motion-director) and any HTML rendering.

Usage: python export_brand_lock.py design-guide.json [brand-lock.md] [--template master.pptx]
                                   [--fonts-dir DIR ...] [--logo FILE ...]

brand-lock.md lists colours with their roles (accent = hero), heading and body fonts with the
font files found for them (HTML rendering needs files; missing ones are flagged), logo files,
protected zones and the never-do list. A YAML-style frontmatter repeats the tokens for tools.
Logo files: --logo, else `assets.logos` in the JSON, else pictures extracted from the master
(--template, or the guide's `source` next to the JSON) into <out folder>/logos/.
Never-do: the template-first rules, the guide's `rules`, and the "Do / don't" section of a
design-guide.md next to the JSON. Fonts are searched in --fonts-dir, the JSON's folder and
its fonts/ subfolder, ~/.fonts, ~/.local/share/fonts, /usr/share/fonts, /Library/Fonts.
"""
import json
import os
import re
import sys

ROLE_TEXT = [
    ("accent", "hero", "the one thing per frame: the key word, number, CTA, end-card mark; rationed"),
    ("ink", "text", "titles and body on light grounds"),
    ("bg", "background", "default ground"),
    ("dark2", "dark ground", "dark stage or text on light2"),
    ("light2", "light ground", "panels, alternative ground"),
    ("grey", "context", "secondary text, context data"),
    ("negative", "negative", "only where a sign matters"),
    ("accent2", "secondary", "second data series, supporting shapes; never competes with the hero"),
    ("accent3", "support 3", "charts and diagrams only"),
    ("accent4", "support 4", "charts and diagrams only"),
    ("accent5", "support 5", "charts and diagrams only"),
    ("accent6", "support 6", "charts and diagrams only"),
]
NEVER = [
    "no fonts other than the heading and body fonts listed here",
    "no colours outside this palette; no off-palette gradients",
    "the hero colour marks one thing per frame, never a whole background unless the guide allows an accent stage",
    "never stretch, recolour, rotate or crop the logo; keep its clear space",
    "never cover or move protected zones (logo, bands, footer, legal lines)",
]
FONT_DIRS = ["~/.fonts", "~/.local/share/fonts", "/usr/share/fonts", "/usr/local/share/fonts", "/Library/Fonts",
             "~/Library/Fonts", "C:/Windows/Fonts"]


def font_files(family, dirs):
    """Font files whose name matches the family (spaces and case ignored)."""
    key = re.sub(r"[^a-z0-9]", "", (family or "").lower())
    if not key:
        return []
    hits = []
    for d in dirs:
        d = os.path.expanduser(d)
        if not os.path.isdir(d):
            continue
        for root, _, files in os.walk(d):
            for f in files:
                if f.lower().endswith((".ttf", ".otf", ".woff", ".woff2")):
                    stem = os.path.splitext(f)[0].lower()
                    family_part = re.sub(r"[^a-z0-9]", "", re.split(r"[-_]", stem)[0])
                    if family_part == key or re.sub(r"[^a-z0-9]", "", stem) == key:
                        hits.append(os.path.join(root, f))
    return sorted(set(hits))


def show(path, out_dir):
    """Path relative to the brand-lock folder when it lives there, else absolute."""
    path = os.path.abspath(path)
    return os.path.relpath(path, out_dir) if path.startswith(out_dir + os.sep) else path


def extract_logos(template, out_dir):
    """Save picture shapes of the master and its layouts; return their paths."""
    try:
        from pptx import Presentation
    except ImportError:
        return []
    prs = Presentation(template)
    sources = [prs.slide_masters[0]] + list(prs.slide_layouts)
    paths, seen = [], set()
    for obj in sources:
        for sh in obj.shapes:
            if sh.shape_type == 13 and not sh.is_placeholder:
                blob = sh.image.blob
                if blob in seen:
                    continue
                seen.add(blob)
                os.makedirs(out_dir, exist_ok=True)
                name = re.sub(r"[^a-z0-9]+", "-", sh.name.lower()).strip("-") or "logo"
                path = os.path.join(out_dir, f"{name}.{sh.image.ext}")
                with open(path, "wb") as f:
                    f.write(blob)
                paths.append(path)
    return paths


def dont_lines(md_path):
    if not os.path.exists(md_path):
        return []
    text = open(md_path, encoding="utf-8").read()
    m = re.search(r"^## Do / don't\s*\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not m:
        return []
    lines = []
    for line in m.group(1).splitlines():
        line = line.strip().lstrip("-* ").strip()
        if re.match(r"(?i)^(don'?t|never|no )", line) and "<" not in line:
            lines.append(re.sub(r"(?i)^don'?t:?\s*", "", line))
    return lines


def main(argv):
    def opt(name):
        vals, i = [], 0
        while i < len(argv):
            if argv[i] == name and i + 1 < len(argv):
                vals.append(argv[i + 1])
                i += 2
            else:
                i += 1
        return vals

    flags = {"--template", "--fonts-dir", "--logo"}
    args, skip = [], False
    for a in argv:
        if skip:
            skip = False
            continue
        if a in flags:
            skip = True
            continue
        args.append(a)
    if not args:
        print(__doc__)
        return 2
    guide_path = args[0]
    out = args[1] if len(args) > 1 else os.path.join(os.path.dirname(os.path.abspath(guide_path)), "brand-lock.md")
    out_dir = os.path.dirname(os.path.abspath(out))
    guide = json.load(open(guide_path, encoding="utf-8"))
    base = os.path.dirname(os.path.abspath(guide_path))

    colors = guide.get("colors", {})
    rows = [(key, role, use, colors[key]) for key, role, use in ROLE_TEXT if colors.get(key)]

    fonts = guide.get("fonts", {})
    dirs = opt("--fonts-dir") + [base, os.path.join(base, "fonts")] + FONT_DIRS
    font_rows = []
    for kind in ("heading", "body"):
        family = fonts.get(kind)
        files = font_files(family, dirs)
        font_rows.append((kind, family or "open: not in the guide", files))

    logos = opt("--logo") or (guide.get("assets") or {}).get("logos") or []
    template = (opt("--template") or [None])[0]
    if not template and guide.get("source") and os.path.exists(os.path.join(base, guide["source"])):
        template = os.path.join(base, guide["source"])
    if not logos and template and os.path.exists(template):
        logos = extract_logos(template, os.path.join(out_dir, "logos"))
    logos = [show(p, out_dir) if os.path.isabs(p) else p for p in logos]

    zones = guide.get("protected_zones", [])
    never = NEVER + [r for r in guide.get("rules", []) if isinstance(r, str)] + dont_lines(os.path.join(base, "design-guide.md"))
    safe = (guide.get("zones") or {}).get("safe_margin_in", 0.5)
    slide = guide.get("slide", {})

    missing_fonts = [f for k, f, files in font_rows if not files]
    lines = ["---",
             f"brand: {guide.get('name', '')}",
             "colors: {" + ", ".join(f"{role.replace(' ', '_')}: \"#{hex_}\"" for _, role, _, hex_ in rows) + "}",
             f"fonts: {{heading: \"{font_rows[0][1]}\", body: \"{font_rows[1][1]}\"}}",
             "font_files: {" + ", ".join(f"{k}: [{', '.join(json.dumps(show(p, out_dir)) for p in files)}]" for k, _, files in font_rows) + "}",
             f"logos: [{', '.join(json.dumps(p) for p in logos)}]",
             f"safe_margin: {round(safe / slide['width_in'] * 100, 1) if slide.get('width_in') else 4}%   # of frame width",
             "---", "",
             f"# Brand lock · {guide.get('name', '')}", "",
             f"Exported from {os.path.basename(guide_path)} (source: {guide.get('source', 'unknown')}). Motion and HTML work use only what is listed here.", "",
             "## Colours", "",
             "| Role | Hex | Use |", "|---|---|---|"]
    lines += [f"| {role} (`{key}`) | #{hex_} | {use} |" for key, role, use, hex_ in rows]
    lines += ["", "## Fonts", "", "| Use | Family | Files |", "|---|---|---|"]
    for kind, family, files in font_rows:
        listed = "<br>".join(show(p, out_dir) for p in files) if files else "**missing**: add the font files (licensed) before rendering HTML or video"
        lines.append(f"| {kind} | {family} | {listed} |")
    lines += ["", "## Logo", ""]
    lines += [f"- `{p}`" for p in logos] or ["- open: no logo file found; pass --logo or add assets.logos to the guide"]
    lines += ["- Clear space: at least the logo's own height on every side. Lands once, with weight, usually on the end card."]
    lines += ["", "## Safe zones", "",
              f"- Margin: {safe} in on a {slide.get('width_in', '?')} × {slide.get('height_in', '?')} in slide; keep the same proportion in video frames."]
    for z in zones:
        box = z.get("box_in") or ["?"] * 4
        lines.append(f"- Protected ({z.get('where')}): {z.get('name')} ({z.get('kind')}) at x {box[0]}, y {box[1]}, {box[2]} × {box[3]} in")
    lines += ["", "## Never", ""] + [f"- {n}" for n in never]
    if missing_fonts:
        lines += ["", "## Open", "", f"- Font files missing for: {', '.join(missing_fonts)}"]
    open(out, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"brand lock: {out} ({len(rows)} colours, fonts {font_rows[0][1]} / {font_rows[1][1]}, {len(logos)} logo files)")
    for f in missing_fonts:
        print(f"MISSING font files: {f}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
