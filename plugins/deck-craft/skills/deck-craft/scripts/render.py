"""render.py: render a .pptx to PNGs and one contact sheet, so the slides can be looked at.

Usage: python render.py deck.pptx [outdir] [--dpi 80]
Needs LibreOffice (soffice) and pdftoppm (poppler). Pillow is optional, for the contact sheet.
LibreOffice substitutes fonts it does not have, so judge layout and overflow, not exact typography.
"""
import glob
import os
import shutil
import subprocess
import sys


def main(deck, outdir=None, dpi=80):
    outdir = outdir or os.path.splitext(deck)[0] + "_render"
    os.makedirs(outdir, exist_ok=True)
    soffice = shutil.which("soffice") or shutil.which("libreoffice")
    if not soffice:
        print("LibreOffice not found; open the deck in PowerPoint and look at every slide instead.")
        return 2
    subprocess.run([soffice, "--headless", "--convert-to", "pdf", "--outdir", outdir, deck],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    pdf = os.path.join(outdir, os.path.splitext(os.path.basename(deck))[0] + ".pdf")
    subprocess.run(["pdftoppm", "-png", "-r", str(dpi), pdf, os.path.join(outdir, "slide")], check=True)
    pngs = sorted(glob.glob(os.path.join(outdir, "slide*.png")))
    print(f"{len(pngs)} slides rendered to {outdir}")
    try:
        from PIL import Image
        thumbs = [Image.open(p) for p in pngs]
        if thumbs:
            w, h = thumbs[0].size
            scale = 360 / w
            tw, th = int(w * scale), int(h * scale)
            cols = 3
            rows = -(-len(thumbs) // cols)
            sheet = Image.new("RGB", (cols * (tw + 12) + 12, rows * (th + 12) + 12), "#888888")
            for i, im in enumerate(thumbs):
                sheet.paste(im.resize((tw, th)), (12 + (i % cols) * (tw + 12), 12 + (i // cols) * (th + 12)))
            path = os.path.join(outdir, "contact_sheet.png")
            sheet.save(path)
            print(f"contact sheet: {path}")
    except ImportError:
        pass
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    dpi = 80
    if "--dpi" in sys.argv:
        dpi = int(sys.argv[sys.argv.index("--dpi") + 1])
        args = [a for a in args if a != str(dpi)]
    if not args:
        print(__doc__)
        sys.exit(2)
    sys.exit(main(args[0], args[1] if len(args) > 1 else None, dpi))
