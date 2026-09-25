#!/usr/bin/env python3
"""Build the two-page cover that leads the Higher or Lower? printable.

    pip install reportlab pymupdf
    python3 tools/make-higher-lower-sheets.py          # the sheets first
    python3 tools/build-higher-or-lower-cover.py [<cover.pdf>]
    python3 tools/build-higher-or-lower-cover.py --art <fan.png>   # transparent

Landscape, like the sheets. Page one is the house cover grid (eyebrow +
hairline rule, light title, colored kicker, a fan of whole sheets, centered
caption + colored subline, footer bar). Per Josh's standing fan rule it shows
two sheets, one of each version: the studio (meadow) Higher sheet in front,
the white Lower sheet behind it.

Page two is the Bee's Sound Garden cover's page two turned landscape: Bees
Keys on the left, more free printables and the mailing list on the right.
The app has no higher/lower game, so the copy doesn't claim one; it points at
key names as what comes after the ear, which is what the app teaches.

The output carries live links as real PDF annotations, which is why
`tools/combine-printable.py` must merge it.
"""

import io
import sys
from pathlib import Path

import pymupdf
from PIL import Image
from reportlab.graphics import renderPDF
from reportlab.graphics.barcode.qr import QrCodeWidget
from reportlab.graphics.shapes import Drawing
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

SITE = Path(__file__).resolve().parents[1]
SHEETS = SITE / "output" / "higher-lower"

FONT = Path("/Users/josh/Repos/BeesKeys/BeesKeys/assets/font/Nunito-VariableFont_wght.ttf")
ICON = SITE / "images" / "appicon.png"
BEE = SITE / "images" / "bee_icon.png"
# The real game (the CDE learning mode), lifted from the Which Key Is Mine?
# cover's page two.
SHOT = SITE / "tools" / "higher-lower-art" / "bees-keys-game.jpg"

SITE_URL = "https://beeskeysapp.com"
APP_STORE_URL = "https://apps.apple.com/us/app/bees-keys-first-piano-lesson/id1608004053"
PLAY_STORE_URL = "https://play.google.com/store/apps/details?id=com.beeskeysapps.beeskeys"
RESOURCES_URL = "https://beeskeysapp.com/resources.html"
# The site is static, so the "list" is the same mailto the resource pages use.
LIST_MAILTO = ("mailto:beeskeysapp@gmail.com"
               "?subject=Send%20me%20new%20Bees%20Keys%20freebies")

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
    else SITE / "output" / "higher-lower" / "higher-or-lower-cover.pdf"

W, H = letter[1], letter[0]  # landscape, to match the sheets

INK = HexColor("#373936")
MUTED = HexColor("#7D827B")
LINE = HexColor("#E5E7E1")
GREEN = HexColor("#6CB33F")
DEEP_GREEN = HexColor("#2F6B23")
PALE_GREEN = HexColor("#F1F8E8")
CREAM = HexColor("#FFF8DA")
GOLD_LINE = HexColor("#E9CF66")
GOLD = HexColor("#B87A1A")
BUTTON = HexColor("#98B968")

pdfmetrics.registerFont(TTFont("Nunito", str(FONT)))


# ---------------------------------------------------------------- assets

def sheet(name, dpi=150):
    doc = pymupdf.open(str(SHEETS / f"{name}.pdf"))
    pix = doc[0].get_pixmap(dpi=dpi)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return im


def jpeg(im, quality=85):
    """ReportLab stores a PIL image losslessly; a JPEG stream keeps the cover
    small."""
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    return buf


# ---------------------------------------------------------------- drawing

def paper(c, im, cx, cy, w, angle=0.0, rim=4):
    """A whole sheet on white stock with a soft drop shadow."""
    h = w * im.height / im.width
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angle)
    c.setFillColor(Color(0, 0, 0, alpha=0.11))
    c.roundRect(-w / 2 + 4, -h / 2 - 6, w, h, 4, fill=1, stroke=0)
    c.setFillColor(white)
    c.roundRect(-w / 2 - rim, -h / 2 - rim, w + 2 * rim, h + 2 * rim, 4, fill=1, stroke=0)
    c.setStrokeColor(LINE)
    c.setLineWidth(0.6)
    c.roundRect(-w / 2 - rim, -h / 2 - rim, w + 2 * rim, h + 2 * rim, 4, fill=0, stroke=1)
    c.drawImage(ImageReader(jpeg(im)), -w / 2, -h / 2, w, h)
    c.restoreState()


def fan(c, front, back):
    """Shared by the cover page and the transparent art so they never drift."""
    paper(c, back, 300, 318, 390, angle=-3.5)
    paper(c, front, 482, 298, 430, angle=1.8)


def flat_fan(front, back):
    """The fan pre-flattened to one upright bitmap on the page's white, so no
    viewer has to rasterize the tilted sheets itself (they come out jagged).
    Rendered at 600 dpi and Lanczos-downsampled to 300."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    fan(c, front, back)
    c.showPage()
    c.save()
    doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
    pix = doc[0].get_pixmap(dpi=600)
    doc.close()
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return im.resize((pix.width // 2, pix.height // 2), Image.LANCZOS)


def wrap(text, width, size):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if pdfmetrics.stringWidth(trial, "Nunito", size) <= width:
            cur = trial
        else:
            lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(c, text, x, y, width, size, leading, color=MUTED):
    c.setFillColor(color)
    c.setFont("Nunito", size)
    lines = wrap(text, width, size)
    for i, line in enumerate(lines):
        c.drawString(x, y - i * leading, line)
    return y - len(lines) * leading


def button(c, x, y, w, text):
    c.setFillColor(BUTTON)
    c.roundRect(x, y, w, 25, 12.5, fill=1, stroke=0)
    c.setFillColor(white)
    c.setFont("Nunito", 8)
    c.drawCentredString(x + w / 2, y + 9, text)


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


# ---------------------------------------------------------------- pages

def page_one(c, front, back):
    c.drawImage(ImageReader(jpeg(flat_fan(front, back), quality=80)), 0, 0, W, H)

    c.setFillColor(MUTED)
    c.setFont("Nunito", 10)
    c.drawString(42, H - 34, "Bees Keys Printables")
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    c.line(42, H - 44, W - 42, H - 44)

    c.setFillColor(INK)
    c.setFont("Nunito", 28)
    c.drawString(42, H - 92, "Higher or Lower?")
    c.setFillColor(GREEN)
    c.setFont("Nunito", 9.5)
    c.drawString(43, H - 111, "LISTEN  •  CIRCLE  •  SORT")
    c.drawImage(str(BEE), W - 104, H - 118, 58, 58, preserveAspectRatio=True, mask="auto")

    c.setFillColor(INK)
    c.setFont("Nunito", 12)
    c.drawCentredString(W / 2, 100, "2 keyboard worksheets for finding the higher and the lower key")
    c.setFillColor(GREEN)
    c.setFont("Nunito", 8.3)
    c.drawCentredString(W / 2, 82, "Circle the bee or the frog. White and meadow studio copies included.")

    footer(c)
    c.showPage()


def thumb(c, path, cx, top, width, caption):
    """A printable's cover shot with a white rim and a soft shadow, captioned."""
    im = Image.open(path)
    height = width * im.height / im.width
    y = top - height
    c.setFillColor(Color(0, 0, 0, alpha=0.10))
    c.roundRect(cx - width / 2 + 3, y - 5, width, height, 4, fill=1, stroke=0)
    c.setFillColor(white)
    c.roundRect(cx - width / 2 - 3, y - 3, width + 6, height + 6, 4, fill=1, stroke=0)
    c.drawImage(str(path), cx - width / 2, y, width, height, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 8.2)
    c.drawCentredString(cx, y - 18, caption)


def page_two(c):
    c.setFillColor(HexColor("#FBFCF8"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    # ---------- left: Bees Keys ----------
    x, y, w, h = 48, 84, 338, 478
    c.setFillColor(CREAM)
    c.setStrokeColor(GOLD_LINE)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)

    c.drawImage(str(ICON), x + 24, y + h - 80, 54, 54, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 19)
    c.drawString(x + 92, y + h - 50, "BEES KEYS")
    c.setFillColor(GOLD)
    c.setFont("Nunito", 9.3)
    c.drawString(x + 92, y + h - 68, "Learn the piano key names through play")

    para(c,
         "These worksheets are about HIGHER and LOWER, the first thing a "
         "beginner's ear can hear. Naming the keys is what comes next, and "
         "that is the whole job of Bees Keys: a bee flies across the screen "
         "carrying a note name, and your student taps the matching key "
         "before it escapes. Free, with no ads. Bees Keys Pro is a one-time "
         "unlock that adds play on your own piano, by mic or MIDI.",
         x + 24, y + h - 104, w - 48, 8.8, 13.2)

    # The game itself, on the same white stock as a sheet preview.
    shot = Image.open(SHOT).convert("RGB")
    sw = 188
    paper(c, shot, x + w / 2, y + 206, sw, rim=3)

    draw_vector_qr(c, APP_STORE_URL, x + 24, y + 26, 90)
    c.setFillColor(GREEN)
    c.setFont("Nunito", 10)
    c.drawString(x + 130, y + 90, "Scan to get Bees Keys")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 7.5)
    c.drawString(x + 130, y + 74, "On the App Store and Google Play")
    button(c, x + 130, y + 30, 150, "GET BEES KEYS")
    c.linkURL(APP_STORE_URL, (x + 18, y + 20, x + 290, y + 122), relative=0, thickness=0)
    c.linkURL(PLAY_STORE_URL, (x + 128, y + 68, x + 270, y + 82), relative=0, thickness=0)

    # ---------- right: the shelf, and the list ----------
    x, y, w, h = 406, 84, 338, 478
    c.setFillColor(PALE_GREEN)
    c.setStrokeColor(HexColor("#CBE3B4"))
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 18, fill=1, stroke=1)

    c.drawImage(str(BEE), x + 22, y + h - 72, 46, 46, preserveAspectRatio=True, mask="auto")
    c.setFillColor(INK)
    c.setFont("Nunito", 16)
    c.drawString(x + 80, y + h - 46, "MORE FREE PRINTABLES")
    c.setFillColor(DEEP_GREEN)
    c.setFont("Nunito", 8.6)
    c.drawString(x + 80, y + h - 63, "Eleven more on the site, and new ones every few weeks")
    c.linkURL(RESOURCES_URL, (x + 76, y + h - 70, x + w - 16, y + h - 34), relative=0, thickness=0)

    shelf = [
        (SITE / "images/resources/which-key-is-mine-cover.jpg", "Which Key Is Mine?"),
        (SITE / "images/resources/sound-garden-adventure-cards-card.jpg", "Sound Garden Cards"),
        (SITE / "images/resources/meet-the-piano-keys-cover.jpg", "Meet the Piano Keys"),
    ]
    tw = 86
    gap = (w - 44 - 3 * tw) / 2  # thumbs centered between the header and the list
    for i, (path, caption) in enumerate(shelf):
        thumb(c, path, x + 22 + tw / 2 + i * (tw + gap), y + 336, tw, caption)

    draw_vector_qr(c, LIST_MAILTO, x + 22, y + 26, 90)
    c.setFillColor(INK)
    c.setFont("Nunito", 12)
    c.drawString(x + 128, y + 146, "Want them first?")
    c.drawString(x + 128, y + 130, "Join the list.")
    para(c,
         "Scan and it opens a ready-made email. Send it and you are on the "
         "list. Your address is only ever used to send you the free resources.",
         x + 128, y + 110, w - 150, 8, 11.5)
    button(c, x + 128, y + 30, 168, "SEND ME NEW FREEBIES")
    c.linkURL(LIST_MAILTO, (x + 16, y + 20, x + w - 16, y + 160), relative=0, thickness=0)

    footer(c)
    c.showPage()


def write_art(path, front, back, dpi=150):
    """The fan alone on a transparent ground, for the OG and social cards.
    Supersampled 4x so the rotated sheet edges don't stair-step."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    fan(c, front, back)
    c.showPage()
    c.save()
    doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
    pix = doc[0].get_pixmap(dpi=dpi * 4, alpha=True)
    doc.close()
    im = Image.frombytes("RGBA", (pix.width, pix.height), pix.samples)
    im = im.resize((pix.width // 4, pix.height // 4), Image.LANCZOS)
    im.save(path)
    print(f"{path}: {im.width}x{im.height} RGBA")


def main():
    front = sheet("bees-keys-which-key-is-higher-studio")
    back = sheet("bees-keys-which-key-is-lower")

    if "--art" in sys.argv:
        write_art(sys.argv[sys.argv.index("--art") + 1], front, back)
        return

    OUT.parent.mkdir(parents=True, exist_ok=True)
    c = canvas.Canvas(str(OUT), pagesize=(W, H), pageCompression=1)
    c.setTitle("Higher or Lower? - Bees Keys Cover")
    c.setAuthor("Bees Keys")
    page_one(c, front, back)
    page_two(c)
    c.save()

    doc = pymupdf.open(str(OUT))
    sizes = [(round(p.rect.width), round(p.rect.height)) for p in doc]
    links = [(i + 1, l["uri"]) for i, p in enumerate(doc) for l in p.get_links() if l.get("uri")]
    doc.close()
    print(f"{OUT}: {len(sizes)} pages {sizes}, {OUT.stat().st_size // 1024} KB")
    for page, uri in links:
        print(f"  p{page}  {uri}")
    if sizes != [(792, 612)] * 2:
        sys.exit("cover must be landscape US Letter to match the sheets")


if __name__ == "__main__":
    main()
