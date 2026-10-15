#!/usr/bin/env python3
"""Build the two-page cover that leads the Rhythm Phrase Builders printable.

    pip install reportlab pymupdf
    python3 tools/build-rhythm-phrase-cover.py [<cover.pdf>] [--bw]

--bw builds the cover for the printer-friendly download: the same two pages,
with the line-art cards in the hand and a kicker that says what it is.

Portrait, because the card pages are portrait US Letter. Lineage is the
Sound Garden cover (the other card deck): eyebrow + hairline rule, light
title, colored kicker, fanned previews with white rim and drop shadow,
centered caption + colored subline, footer bar.

Page one is the same four cards the ideas sheet uses, "Butterflies flutter
over the meadow", laid out as a hand of cards so the sentence reads left to
right and the four colors show. Page two is the Sound Garden layout: Bees Keys on top,
the rest of the free printables and the mailing list underneath. The app has
no rhythm content, so the copy pitches key names as the other half of a
first lesson rather than claiming a rhythm game.

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
TMP = SITE / "tmp" / "rhythm-phrase" / "cover"

FONT = Path("/Users/josh/Repos/BeesKeys/BeesKeys/assets/font/Nunito-VariableFont_wght.ttf")
ICON = SITE / "images" / "appicon.png"
BEE = SITE / "images" / "bee_icon.png"

BW = "--bw" in sys.argv
args = [a for a in sys.argv[1:] if a != "--bw"]

DECK = SITE / "output" / "pdf" / "rhythm-phrase-builders.pdf"
# The example sentence, as rendered by tools/make-rhythm-phrase-cards.py.
CARDS = [SITE / "tmp" / "rhythm-phrase" / (("bw-" if BW else "") + f) for f in
         ("creature-08.png", "action-01.png", "path-01.png", "place-01.png")]

SITE_URL = "https://beeskeysapp.com"
APP_STORE_URL = "https://apps.apple.com/us/app/bees-keys-first-piano-lesson/id1608004053"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.beeskeysapps.beeskeys"
RESOURCES_URL = "https://beeskeysapp.com/resources.html"
LIST_MAILTO = ("mailto:beeskeysapp@gmail.com"
               "?subject=Send%20me%20new%20Bees%20Keys%20freebies")

OUT = Path(args[0]) if args else SITE / "output" / "pdf" / ("rhythm-phrase-cover-bw.pdf" if BW else "rhythm-phrase-cover.pdf")

W, H = letter

INK = HexColor("#373936")
MUTED = HexColor("#7D827B")
LINE = HexColor("#E5E7E1")
GREEN = HexColor("#6CB33F")
DEEP_GREEN = HexColor("#2F6B23")
PALE_GREEN = HexColor("#F1F8E8")
PINK = HexColor("#D63B78")
PALE = HexColor("#FFF9EC")       # neutral warm panel, so all four card colors sit on it
CREAM = HexColor("#FFF8DA")
GOLD_LINE = HexColor("#E9CF66")
GOLD = HexColor("#B87A1A")

pdfmetrics.registerFont(TTFont("Nunito", str(FONT)))

if BW:
    # printer-friendly cover: every colour becomes a grey, panels go white
    # with a grey rule, and the raster bits are converted to greyscale
    GREEN = HexColor("#555555")
    DEEP_GREEN = HexColor("#444444")
    PALE_GREEN = white
    PINK = HexColor("#444444")
    PALE = white
    CREAM = white
    GOLD_LINE = HexColor("#BDBDBD")
    GOLD = HexColor("#555555")
BUTTON = HexColor("#777777") if BW else HexColor("#98B968")
PANEL_LINE = HexColor("#BDBDBD") if BW else HexColor("#CBE3B4")


def img(path):
    """The image to draw: the file itself, or a greyscale copy for --bw."""
    if not BW:
        return path
    TMP.mkdir(parents=True, exist_ok=True)
    out = TMP / ("grey-" + Path(path).name.rsplit(".", 1)[0] + ".png")
    if not out.exists():
        Image.open(path).convert("LA").save(out)
    return out


def render_sources():
    """The deck is backs/fronts per category, so the fronts pages are 2, 4,
    6, 8 (indices 1, 3, 5, 7): Creature, Action, Path, Place."""
    TMP.mkdir(parents=True, exist_ok=True)
    doc = pymupdf.open(str(DECK))
    for i in (1, 3, 5, 7):
        doc[i].get_pixmap(dpi=170).save(str(TMP / f"fronts-{i + 1}.png"))
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
    c.drawImage(str(img(path)), -width / 2, -height / 2, width, height, mask="auto")
    c.restoreState()


def footer(c):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(52, 49, W - 52, 49)
    c.drawImage(str(img(ICON)), 52, 12, 30, 30, mask="auto")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 7.5)
    c.drawString(91, 30, "Bees Keys Printables")
    c.setFillColor(GREEN)
    c.drawCentredString(W / 2, 25, "beeskeysapp.com")
    c.setFillColor(MUTED)
    c.drawRightString(W - 52, 25, "Practice Through Play")
    c.linkURL(SITE_URL, (W / 2 - 55, 14, W / 2 + 55, 36), relative=0, thickness=0)


def draw_vector_qr(c, value, x, y, size):
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
    c.drawString(42, H - 89, "Rhythm Phrase Builders")
    c.setFillColor(PINK)
    c.setFont("Nunito", 9.5)
    c.drawString(43, H - 110, "PRINTER-FRIENDLY  •  COLOR YOUR OWN" if BW else "BUILD  •  CHANT  •  CLAP  •  PLAY")
    c.drawImage(str(img(BEE)), W - 94, H - 116, 52, 52, preserveAspectRatio=True, mask="auto")

    # The example sentence as a row of four cards, no overlap so every word
    # reads, with a gentle tilt and arc so it sits like a hand rather than a
    # grid. Kristianna asked for these exact four cards (Oct 14).
    c.setFillColor(PALE)
    c.setStrokeColor(PANEL_LINE)
    c.setLineWidth(1)
    c.roundRect(48, 213, W - 96, 397, 22, fill=1, stroke=1 if BW else 0)
    grey = HexColor("#555555")
    hand = [(CARDS[0], 112, 402, -4.0, "CREATURE", grey if BW else HexColor("#D63B78")),
            (CARDS[1], 241, 412, -1.5, "ACTION", grey if BW else HexColor("#E0701A")),
            (CARDS[2], 370, 412, 1.5, "PATH", grey if BW else HexColor("#D2960A")),
            (CARDS[3], 499, 402, 4.0, "PLACE", grey if BW else HexColor("#4F9A2A"))]
    for path, cx, cy, angle, label, color in hand:
        place_sheet(c, path, cx, cy, 122, angle)
        if BW:
            continue          # the printer-friendly cards carry their own label
        c.setFillColor(color)
        c.setFont("Nunito", 7.6)
        c.drawCentredString(cx, 514 if label in ("ACTION", "PATH") else 506, label)

    c.setFillColor(INK)
    c.setFont("Nunito", 12.2)
    c.drawCentredString(W / 2, 139, "Build a phrase, read the sentence, and clap the rhythm with 36 mix-and-match cards")
    c.setFillColor(PINK)
    c.setFont("Nunito", 8.4)
    c.drawCentredString(W / 2, 118, "Includes an ideas sheet, 4 decks of 9 cards, a phrase mat, and a write-the-rhythm page")

    footer(c)
    c.showPage()


def thumb(c, path, cx, cy, width, caption):
    im = Image.open(path)
    height = width * im.height / im.width
    c.setFillColor(Color(0, 0, 0, alpha=0.10))
    c.roundRect(cx - width / 2 + 3, cy - height / 2 - 5, width, height, 4, fill=1, stroke=0)
    c.setFillColor(white)
    c.roundRect(cx - width / 2 - 3, cy - height / 2 - 3, width + 6, height + 6, 4, fill=1, stroke=0)
    c.drawImage(str(img(path)), cx - width / 2, cy - height / 2, width, height, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 8.6)
    c.drawCentredString(cx, cy - height / 2 - 20, caption)


def page_two(c):
    c.setFillColor(white if BW else HexColor("#FBFCF8"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ---------- top half: Bees Keys ----------
    x, y, w, h = 48, 470, W - 96, 290
    c.setFillColor(CREAM)
    c.setStrokeColor(GOLD_LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)

    c.drawImage(str(img(ICON)), x + 26, y + h - 80, 54, 54, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 19)
    c.drawString(x + 96, y + h - 50, "BEES KEYS")
    c.setFillColor(GOLD)
    c.setFont("Nunito", 9.5)
    c.drawString(x + 96, y + h - 69, "Learn the piano key names through play")

    c.setFillColor(MUTED)
    c.setFont("Nunito", 9.6)
    lines = [
        "These cards are about rhythm: say it, clap it, play it. Naming the keys is the other half of",
        "a first lesson, and that is the whole job of Bees Keys: a bee flies across the screen carrying",
        "a note name, and your student taps the matching key before it escapes. Free, with no ads,",
        "and Bees Keys Pro is a one-time unlock that adds play on your own piano, by mic or MIDI.",
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
    c.setFillColor(BUTTON)
    c.roundRect(x + 128, y + 26, 150, 25, 12.5, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Nunito", 8)
    c.drawCentredString(x + 203, y + 35, "GET BEES KEYS")
    c.linkURL(APP_STORE_URL, (x + 20, y + 18, x + 290, y + 98), relative=0, thickness=0)
    c.linkURL(PLAY_STORE_URL, (x + 300, y + 54, x + w - 20, y + 72), relative=0, thickness=0)

    # ---------- bottom half: the shelf, and the list ----------
    x, y, w, h = 48, 116, W - 96, 338
    c.setFillColor(PALE_GREEN)
    c.setStrokeColor(PANEL_LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)

    c.drawImage(str(img(BEE)), x + 26, y + h - 70, 44, 44, preserveAspectRatio=True, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 17)
    c.drawString(x + 84, y + h - 44, "MORE FREE PRINTABLES")
    c.setFillColor(DEEP_GREEN)
    c.setFont("Nunito", 9)
    c.drawString(x + 84, y + h - 62, "More on the site, with new ones every few weeks")

    shelf = [
        # landscape -card shots for the portrait printables, so the shelf lines up
        (SITE / "images/resources/sound-garden-adventure-cards-card.jpg", "Bee's Sound Garden"),
        (SITE / "images/resources/find-every-key-card.jpg", "Find Every Key"),
        (SITE / "images/resources/left-or-right-cover.jpg", "Left or Right?"),
    ]
    tw = 132
    gap = (w - 52 - 3 * tw) / 2
    for i, (path, caption) in enumerate(shelf):
        thumb(c, path, x + 26 + tw / 2 + i * (tw + gap), y + 205, tw, caption)

    draw_vector_qr(c, LIST_MAILTO, x + 26, y + 22, 80)
    c.setFillColor(INK)
    c.setFont("Nunito", 12.5)
    c.drawString(x + 124, y + 82, "Want them first? Join the list.")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 8.4)
    c.drawString(x + 124, y + 63, "Scan and it opens a ready-made email. Send it and you are on the list.")
    c.drawString(x + 124, y + 50, "Your address is only ever used to send you the free resources.")
    c.setFillColor(BUTTON)
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
    c.setTitle("Rhythm Phrase Builders" + (" (printer-friendly)" if BW else "") + " - Bees Keys Cover")
    c.setAuthor("Bees Keys")
    page_one(c)
    page_two(c)
    c.save()
    print(OUT)


if __name__ == "__main__":
    build()
