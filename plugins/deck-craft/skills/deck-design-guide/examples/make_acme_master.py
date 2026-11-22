"""Build a small fictional slide master (Acme) to try the design-guide and brand-lock tools on.
Run: python make_acme_master.py [out.pptx]  ->  acme-master.pptx
Theme: Acme orange accent, heading font Inter, body font Liberation Sans, a logo on the master
(bottom right) and a confidentiality footer. Fictional brand; no real company.
"""
import io
import struct
import sys
import zlib

from lxml import etree
from pptx import Presentation
from pptx.opc.constants import RELATIONSHIP_TYPE as RT
from pptx.oxml.ns import qn
from pptx.util import Inches, Pt

A = "{http://schemas.openxmlformats.org/drawingml/2006/main}"
COLORS = {"dk1": "1B1B1F", "lt1": "FFFFFF", "dk2": "2E3440", "lt2": "F4F1EC", "accent1": "E8590C",
          "accent2": "1F6F8B", "accent3": "99A3A4", "accent4": "F2C14E", "accent5": "5B8C5A", "accent6": "B23A48"}


def png(width, height, rgb):
    """A plain one-colour PNG, stdlib only (the fictional logo)."""
    raw = b"".join(b"\x00" + bytes(rgb) * width for _ in range(height))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
    return (b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw)) + chunk(b"IEND", b""))


def main(out="acme-master.pptx"):
    prs = Presentation()
    prs.slide_width, prs.slide_height = Inches(13.333), Inches(7.5)
    master = prs.slide_masters[0]
    theme = [r.target_part for r in master.part.rels.values() if r.reltype.endswith("/theme")][0]
    root = etree.fromstring(theme.blob)
    scheme = root.find(f".//{A}clrScheme")
    scheme.set("name", "Acme")
    for el in scheme:
        key = el.tag.replace(A, "")
        if key in COLORS:
            for child in list(el):
                el.remove(child)
            etree.SubElement(el, f"{A}srgbClr", val=COLORS[key])
    for kind, face in (("major", "Inter"), ("minor", "Liberation Sans")):
        root.find(f".//{A}fontScheme/{A}{kind}Font/{A}latin").set("typeface", face)
    theme._blob = etree.tostring(root, xml_declaration=True, encoding="UTF-8", standalone=True)
    # python-pptx draws only on slides: draw on a scratch slide, then move the shapes to the master
    scratch = prs.slides.add_slide(prs.slide_layouts[6])
    logo = scratch.shapes.add_picture(io.BytesIO(png(120, 40, (0xE8, 0x59, 0x0C))),
                                      Inches(11.6), Inches(6.8), Inches(1.2), Inches(0.4))
    logo.name = "Acme logo"
    blip = logo._element.find(f".//{A}blip")
    image_part = scratch.part.related_part(blip.get(qn("r:embed")))
    blip.set(qn("r:embed"), master.part.relate_to(image_part, RT.IMAGE))
    foot = scratch.shapes.add_textbox(Inches(0.5), Inches(6.9), Inches(5), Inches(0.3))
    foot.name = "Confidentiality"
    foot.text_frame.text = "Acme · confidential"
    foot.text_frame.paragraphs[0].runs[0].font.size = Pt(9)
    tree = master.shapes._spTree
    for shape in (logo, foot):
        tree.append(shape._element)
    slide_ids = prs.slides._sldIdLst
    rid = slide_ids[-1].get(qn("r:id"))
    slide_ids.remove(slide_ids[-1])
    prs.part.drop_rel(rid)
    prs.save(out)
    print("saved", out)


if __name__ == "__main__":
    main(*sys.argv[1:2])
