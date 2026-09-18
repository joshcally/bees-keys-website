#!/usr/bin/env python3
"""Build the two-page cover that leads the Bee's Sound Garden printable.

    pip install reportlab pymupdf
    python3 tools/build-sound-garden-cover.py [<cover.pdf>]

Portrait, because the card pages are portrait US Letter and a cover that
disagrees rotates the merged PDF halfway through. The lineage is the Find
Every Key cover (the other card deck): eyebrow + hairline rule, light title,
colored kicker, fanned previews with white rim and drop shadow, centered
caption + colored subline, footer bar.

Page two departs from the house style on purpose. Every other printable's
second page is an ad for the feature the printable mirrors, and there is no
Sound Garden in either app — so this one points at the rest of the free
printables instead of claiming a feature that does not exist.

The output carries live links as real PDF annotations, which is why
`tools/combine-printable.py` must merge it.
"""

import sys
from pathlib import Path

import pymupdf
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

SITE = Path(__file__).resolve().parents[1]
TMP = SITE / "tmp" / "sound-garden" / "cover"

FONT = Path("/Users/josh/Repos/BeesKeys/BeesKeys/assets/font/Nunito-VariableFont_wght.ttf")
ICON = SITE / "images" / "appicon.png"
BEE = SITE / "images" / "bee_icon.png"

ART_DECK = SITE / "output" / "pdf" / "sound-garden-cards-art.pdf"
COLOR_DECK = SITE / "output" / "pdf" / "sound-garden-cards-color.pdf"

SITE_URL = "https://beeskeysapp.com"
RESOURCES_URL = "https://beeskeysapp.com/resources.html"

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else SITE / "output" / "pdf" / "sound-garden-cover.pdf"

W, H = letter  # portrait, to match the card pages

INK = HexColor("#373936")
MUTED = HexColor("#7D827B")
LINE = HexColor("#E5E7E1")
GREEN = HexColor("#6CB33F")
DEEP_GREEN = HexColor("#2F6B23")
PALE_GREEN = HexColor("#F1F8E8")
CREAM = HexColor("#FFF8DA")
GOLD_LINE = HexColor("#E9CF66")
GOLD = HexColor("#B87A1A")

pdfmetrics.registerFont(TTFont("Nunito", str(FONT)))


def render_sources():
    """Render the deck preview pages at 170 dpi. Page 2 of each file is the
    first page of fronts (the layout is backs, fronts, backs, fronts)."""
    TMP.mkdir(parents=True, exist_ok=True)
    for src, stem, pages in ((ART_DECK, "art", [1, 3]), (COLOR_DECK, "color", [1])):
        doc = pymupdf.open(str(src))
        for i in pages:
            doc[i].get_pixmap(dpi=170).save(str(TMP / f"{stem}-{i + 1}.png"))
        doc.close()


def place_sheet(c, path, cx, cy, width, angle=0):
    im = Image.open(path)
    height = width * im.height / im.width
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angle)
    c.setFillColor(Color(0, 0, 0, alpha=0.11))
    c.roundRect(-width / 2 + 5, -height / 2 - 6, width, height, 5, fill=1, stroke=0)
    c.setFillColor(white)
    c.roundRect(-width / 2 - 4, -height / 2 - 4, width + 8, height + 8, 5, fill=1, stroke=0)
    c.drawImage(str(path), -width / 2, -height / 2, width, height, mask="auto")
    c.restoreState()


def footer(c):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(52, 49, W - 52, 49)
    c.drawImage(str(ICON), 52, 12, 30, 30, mask="auto")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 7.5)
    c.drawString(91, 30, "Bees Keys Printables")
    c.setFillColor(GREEN)
    c.drawCentredString(W / 2, 25, "beeskeysapp.com")
    c.setFillColor(MUTED)
    c.drawRightString(W - 52, 25, "Playful first piano lessons")
    c.linkURL(SITE_URL, (W / 2 - 55, 14, W / 2 + 55, 36), relative=0, thickness=0)


def draw_vector_qr(c, value, x, y, size):
    """A true vector QR with a clean white quiet zone."""
    c.setFillColor(white)
    c.rect(x, y, size, size, fill=1, stroke=0)
    inset = 5
    qr = QrCodeWidget(value)
    qr.barWidth = size - inset * 2
    qr.barHeight = size - inset * 2
    qr.x = inset
    qr.y = inset
    drawing = Drawing(size, size)
    drawing.add(qr)
    renderPDF.draw(drawing, c, x, y)


def page_one(c):
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Nunito", 9)
    c.drawString(42, H - 32, "Bees Keys Printables")
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    c.line(42, H - 42, W - 42, H - 42)

    c.setFillColor(INK)
    c.setFont("Nunito", 30)
    c.drawString(42, H - 89, "Bee's Sound Garden")
    c.setFillColor(GREEN)
    c.setFont("Nunito", 9.5)
    c.drawString(43, H - 110, "DRAW  •  PLAY  •  IMAGINE")
    c.drawImage(str(BEE), W - 94, H - 116, 52, 52, preserveAspectRatio=True, mask="auto")

    # The cards themselves are the hero: two pages of the illustrated deck with
    # a page of the color-your-own deck fanned in behind, so the two-for-one
    # reads from the cover without a word of explanation.
    c.setFillColor(PALE_GREEN)
    c.roundRect(48, 180, W - 96, 428, 22, fill=1, stroke=0)
    place_sheet(c, TMP / "color-2.png", 232, 393, 276, -9.0)
    place_sheet(c, TMP / "art-4.png", 380, 393, 276, 9.0)
    place_sheet(c, TMP / "art-2.png", 306, 398, 286, 0.0)

    c.setFillColor(INK)
    c.setFont("Nunito", 12.2)
    c.drawCentredString(W / 2, 139, "Eighteen story cards for piano improvising")
    c.setFillColor(GREEN)
    c.setFont("Nunito", 8.4)
    c.drawCentredString(W / 2, 118, "How to play  •  18 illustrated cards  •  18 color-your-own cards")

    footer(c)
    c.showPage()


def page_two(c):
    c.setFillColor(HexColor("#FBFCF8"))
    c.rect(0, 0, W, H, fill=1, stroke=0)
    c.setFillColor(MUTED)
    c.setFont("Nunito", 22)
    c.drawCentredString(W / 2, H - 62, "There is a whole shelf of these,")
    c.setFillColor(GREEN)
    c.setFont("Nunito", 28)
    c.drawCentredString(W / 2, H - 98, "and they are all free.")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 9)
    c.drawCentredString(W / 2, H - 119,
                        "Print them, copy them, and use them with as many students as you like.")

    x, y, w, h = 48, 116, W - 96, 523
    c.setFillColor(CREAM)
    c.setStrokeColor(GOLD_LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)
    c.drawImage(str(ICON), x + 24, y + h - 74, 48, 48, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 16)
    c.drawString(x + 87, y + h - 45, "FREE PIANO PRINTABLES")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 8.3)
    c.drawString(x + 87, y + h - 63, "No sign-up, no email, nothing to join.")

    # What's on the shelf. Four, not five: a fifth row collides with the
    # closing line below, and the QR goes to the full list anyway.
    shelf = [
        ("Find Every Key", "A timed card game for naming every key on the piano."),
        ("Bee's Color Garden", "Color the flowers by key name, one letter at a time."),
        ("Groups of Black Keys", "Spot the twos and the threes all the way up."),
        ("Help the Bees Find Their Keys", "Match each bee to the key it belongs on."),
    ]
    ty = y + h - 128
    for name, blurb in shelf:
        c.setFillColor(GREEN)
        c.circle(x + 34, ty + 5, 4.5, fill=1, stroke=0)
        c.setFillColor(INK)
        c.setFont("Nunito", 13)
        c.drawString(x + 50, ty, name)
        c.setFillColor(MUTED)
        c.setFont("Nunito", 9)
        c.drawString(x + 50, ty - 16, blurb)
        ty -= 52

    c.setFillColor(INK)
    c.setFont("Nunito", 16)
    c.drawString(x + 26, y + 177, "New ones land every few weeks.")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 9.2)
    lines = [
        "Every printable on the site is US Letter, ready to print, and free to share with",
        "your studio. Scan the code to see what is new.",
    ]
    for i, line in enumerate(lines):
        c.drawString(x + 26, y + 153 - i * 16, line)

    draw_vector_qr(c, RESOURCES_URL, x + 26, y + 35, 82)
    c.setFillColor(GREEN)
    c.setFont("Nunito", 9)
    c.drawString(x + 124, y + 88, "Scan for every free printable")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 7.5)
    c.drawString(x + 124, y + 69, "beeskeysapp.com/resources")
    c.setFillColor(HexColor("#98B968"))
    c.roundRect(x + 124, y + 35, 160, 25, 12.5, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Nunito", 8)
    c.drawCentredString(x + 204, y + 44, "BROWSE THE PRINTABLES")

    c.linkURL(RESOURCES_URL, (x + 20, y + 28, x + w - 20, y + 120), relative=0, thickness=0)
    footer(c)
    c.showPage()


def build():
    render_sources()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("Bee's Sound Garden - Bees Keys Cover")
    c.setAuthor("Bees Keys")
    page_one(c)
    page_two(c)
    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
