#!/usr/bin/env python3
"""Build the two-page cover that leads the Bee's Sound Garden printable.

    pip install reportlab pymupdf
    python3 tools/build-sound-garden-cover.py [<cover.pdf>]

Portrait, because the card pages are portrait US Letter and a cover that
disagrees rotates the merged PDF halfway through. The lineage is the Find
Every Key cover (the other card deck): eyebrow + hairline rule, light title,
colored kicker, fanned previews with white rim and drop shadow, centered
caption + colored subline, footer bar.

Page two is two halves: Bees Keys on top, the rest of the free printables and
the mailing list underneath. It does not claim the app has a HIGH/LOW game,
because it does not; it points at key names as the thing that comes after the
ear, which is what the app actually teaches.

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
APP_STORE_URL = "https://apps.apple.com/us/app/bees-keys-first-piano-lesson/id1608004053"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.beeskeysapps.beeskeys"
RESOURCES_URL = "https://beeskeysapp.com/resources.html"
# The site is static, so the "list" is the same mailto the resource pages use.
LIST_MAILTO = ("mailto:beeskeysapp@gmail.com"
               "?subject=Send%20me%20new%20Bees%20Keys%20freebies")

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
    """Render the deck preview pages at 170 dpi. The layout of each deck file
    is backs, fronts 1-9, backs, fronts 10-18, so page 2 is the first page of
    fronts and page 4 is the second."""
    TMP.mkdir(parents=True, exist_ok=True)
    for src, stem, pages in ((ART_DECK, "art", [1]), (COLOR_DECK, "color", [3])):
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

    # The cards themselves are the hero: a two-sheet fan, the illustrated deck
    # in front and the color-your-own deck behind it. The front sheet is cards
    # 1-9 and the back sheet is cards 10-18, so the two sheets show eighteen
    # different prompts rather than the same nine twice. The back sheet sits
    # far enough right that more than half of it shows, because the
    # two-for-one is the thing the cover has to say.
    c.setFillColor(PALE_GREEN)
    c.roundRect(48, 180, W - 96, 428, 22, fill=1, stroke=0)
    place_sheet(c, TMP / "color-4.png", 392, 393, 292, 6.0)
    place_sheet(c, TMP / "art-2.png", 228, 396, 292, -5.0)

    c.setFillColor(INK)
    c.setFont("Nunito", 12.2)
    c.drawCentredString(W / 2, 139, "Eighteen story cards for piano improvising")
    c.setFillColor(GREEN)
    c.setFont("Nunito", 8.4)
    c.drawCentredString(W / 2, 118, "How to play  •  18 illustrated cards  •  18 color-your-own cards")

    footer(c)
    c.showPage()


def thumb(c, path, cx, cy, width, caption):
    """A printable's cover shot with a white rim and a soft shadow, captioned."""
    im = Image.open(path)
    height = width * im.height / im.width
    c.setFillColor(Color(0, 0, 0, alpha=0.10))
    c.roundRect(cx - width / 2 + 3, cy - height / 2 - 5, width, height, 4, fill=1, stroke=0)
    c.setFillColor(white)
    c.roundRect(cx - width / 2 - 3, cy - height / 2 - 3, width + 6, height + 6, 4, fill=1, stroke=0)
    c.drawImage(str(path), cx - width / 2, cy - height / 2, width, height, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 8.6)
    c.drawCentredString(cx, cy - height / 2 - 20, caption)


def page_two(c):
    """Two halves: the Bees Keys app on top, the rest of the free printables
    and the mailing list underneath.

    The app has no HIGH/LOW content, so this does not claim it does. It picks
    up where the deck leaves off instead: these cards are about hearing high
    from low, and naming the keys is the next thing, which is the app's whole
    job. The deck is Bees Keys themed either way.
    """
    c.setFillColor(HexColor("#FBFCF8"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ---------- top half: Bees Keys ----------
    x, y, w, h = 48, 470, W - 96, 290
    c.setFillColor(CREAM)
    c.setStrokeColor(GOLD_LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)

    c.drawImage(str(ICON), x + 26, y + h - 80, 54, 54, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 19)
    c.drawString(x + 96, y + h - 50, "BEES KEYS")
    c.setFillColor(GOLD)
    c.setFont("Nunito", 9.5)
    c.drawString(x + 96, y + h - 69, "Learn the piano key names through play")

    c.setFillColor(MUTED)
    c.setFont("Nunito", 9.8)
    c.setFont("Nunito", 9.6)
    lines = [
        "These cards are about HIGH and LOW, the first thing a beginner's ear can hear. Naming the",
        "keys is what comes next, and that is the whole job of Bees Keys: a bee flies across the screen",
        "carrying a note name, and your student taps the matching key before it escapes. Free, with no",
        "ads, and Bees Keys Pro is a one-time unlock that adds play on your own piano, by mic or MIDI.",
    ]
    for i, line in enumerate(lines):
        c.drawString(x + 26, y + 180 - i * 17, line)

    draw_vector_qr(c, APP_STORE_URL, x + 26, y + 24, 84)
    c.setFillColor(GREEN)
    c.setFont("Nunito", 10)
    c.drawString(x + 128, y + 80, "Scan to get Bees Keys")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 7.5)
    c.drawString(x + 128, y + 62, "On the App Store and Google Play · beeskeysapp.com")
    c.setFillColor(HexColor("#98B968"))
    c.roundRect(x + 128, y + 26, 150, 25, 12.5, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Nunito", 8)
    c.drawCentredString(x + 203, y + 35, "GET BEES KEYS")
    c.linkURL(APP_STORE_URL, (x + 20, y + 18, x + 290, y + 98), relative=0, thickness=0)
    c.linkURL(PLAY_STORE_URL, (x + 300, y + 54, x + w - 20, y + 72), relative=0, thickness=0)

    # ---------- bottom half: the shelf, and the list ----------
    x, y, w, h = 48, 116, W - 96, 338
    c.setFillColor(PALE_GREEN)
    c.setStrokeColor(HexColor("#CBE3B4"))
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)

    c.drawImage(str(BEE), x + 26, y + h - 70, 44, 44, preserveAspectRatio=True, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 17)
    c.drawString(x + 84, y + h - 44, "MORE FREE PRINTABLES")
    c.setFillColor(DEEP_GREEN)
    c.setFont("Nunito", 9)
    c.drawString(x + 84, y + h - 62, "Nine more on the site, with new ones every few weeks")

    shelf = [
        (SITE / "images/resources/bees-color-garden-cover.jpg", "Bee's Color Garden"),
        (SITE / "images/resources/help-the-bees-find-their-keys-cover.jpg", "Help the Bees"),
        (SITE / "images/resources/groups-of-black-keys-cover.jpg", "Groups of Black Keys"),
    ]
    tw = 132
    gap = (w - 52 - 3 * tw) / 2
    for i, (path, caption) in enumerate(shelf):
        thumb(c, path, x + 26 + tw / 2 + i * (tw + gap), y + 205, tw, caption)

    # No signup form on the site (it is static), so the list is the same
    # mailto the resource pages use, as a QR a phone camera can open.
    draw_vector_qr(c, LIST_MAILTO, x + 26, y + 22, 80)
    c.setFillColor(INK)
    c.setFont("Nunito", 12.5)
    c.drawString(x + 124, y + 82, "Want them first? Join the list.")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 8.4)
    c.drawString(x + 124, y + 63, "Scan and it opens a ready-made email. Send it and you are on the list.")
    c.drawString(x + 124, y + 50, "Your address is only ever used to send you the free resources.")
    c.setFillColor(HexColor("#98B968"))
    c.roundRect(x + 124, y + 18, 168, 25, 12.5, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Nunito", 8)
    c.drawCentredString(x + 208, y + 27, "SEND ME NEW FREEBIES")
    c.linkURL(LIST_MAILTO, (x + 20, y + 14, x + 300, y + 98), relative=0, thickness=0)
    c.linkURL(RESOURCES_URL, (x + 80, y + h - 70, x + w - 20, y + h - 54), relative=0, thickness=0)

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
