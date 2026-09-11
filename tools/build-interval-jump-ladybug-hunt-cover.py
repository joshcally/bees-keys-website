#!/usr/bin/env python3
"""Build the two-page cover that leads the Ladybug Hunt printable.

    pip install reportlab pymupdf qrcode
    python3 tools/build-interval-jump-ladybug-hunt-cover.py <cover.pdf>
    python3 tools/build-interval-jump-ladybug-hunt-cover.py --art <fan.png>   # transparent

The Key Jumps cover (`build-interval-jump-key-jumps-cover.py`) with a photo
and one sheet instead of a fan: Ladybug Hunt is a single page (cut-out frogs
and ladybugs, a dice key, and how to play), so the cover shows that page
whole on the right and Josh's photo of the cut-outs on his piano on the
left, both on the same white rim the sheets get.
Page two is unchanged. The output carries live store links as real PDF
annotations, which is why `tools/combine-printable.py` must merge it.
"""

import io
import os
import sys

import pymupdf
import qrcode
from PIL import Image
from reportlab.lib.colors import Color, HexColor, white
from reportlab.lib.pagesizes import letter
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

IJ = "/Users/josh/Repos/IntervalJump"
SITE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

FONT = f"{IJ}/IntervalJump/assets/font/Nunito-VariableFont_wght.ttf"
ICON = f"{SITE}/images/intervaljump-icon.png"
FROG = f"{IJ}/printables/art/frog-happy.png"
LADYBUG = f"{IJ}/printables/art/ladybug.png"
PHOTO = f"{IJ}/printables/art/ladybug-hunt-piano.jpg"
SHOT = f"{IJ}/printables/art/game-screenshot.png"
SHEETS = f"{IJ}/printables"

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
    else "/tmp/interval-jump-ladybug-hunt-cover.pdf"

APP_STORE = "https://apps.apple.com/us/app/interval-jump-read-music-fast/id6736377103"
PLAY_STORE = "https://play.google.com/store/apps/details?id=com.joshuacallahan.intervaljump"
SITE_URL = "https://beeskeysapp.com"

W, H = letter[1], letter[0]  # landscape, like every Bees Keys cover

INK = HexColor("#373936")
MUTED = HexColor("#7D827B")
LINE = HexColor("#E5E7E1")
AZUL = HexColor("#15B8F1")
CERULEAN = HexColor("#118EB9")
GOLD = HexColor("#EEAC2D")
GOLD_DEEP = HexColor("#F29900")
CREAM = HexColor("#FAF2D6")
WOOD = HexColor("#8C5E2E")

pdfmetrics.registerFont(TTFont("Nunito", FONT))


# ---------------------------------------------------------------- assets

def sheet_page(name, dpi=150):
    """One worksheet, rendered whole from the real PDF."""
    doc = pymupdf.open(f"{SHEETS}/{name}")
    pix = doc[0].get_pixmap(dpi=dpi)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return im


def qr_image(url):
    q = qrcode.QRCode(box_size=10, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(url)
    q.make(fit=True)
    return q.make_image(fill_color="#373936", back_color="white").convert("RGB")


# ---------------------------------------------------------------- drawing

def draw(c, im, x, y, w, h=None):
    if h is None:
        h = w * im.height / im.width
    c.drawImage(ImageReader(im), x, y, w, h, mask="auto")


def jpeg(im, quality=85):
    """Re-wrap an opaque render as a JPEG stream. ReportLab stores a PIL image
    losslessly, which put the three sheet renders and the screenshot at 5 MB+;
    routing them through JPEG bytes keeps the cover under a megabyte."""
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    buf.seek(0)
    return buf


def paper(c, im, cx, cy, w, angle=0.0, rim=4):
    """A whole sheet on white stock with a soft drop shadow - the same rim the
    bug-collection cover and `.res-shot` on the website give their previews."""
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


def panel(c, x, y, w, h, fill, stroke):
    c.setFillColor(Color(1, 1, 1, alpha=0.58))
    c.setStrokeColor(stroke)
    c.setLineWidth(1)
    c.roundRect(x, y, w, h, 15, fill=1, stroke=1)
    c.setFillColor(fill)
    c.roundRect(x + 1, y + 1, w - 2, h - 2, 14, fill=1, stroke=0)


def pill(c, x, y, w, h, fill, text, size=8.6, fg=white):
    c.setFillColor(fill)
    c.roundRect(x, y, w, h, h / 2, fill=1, stroke=0)
    c.setFillColor(fg)
    c.setFont("Nunito", size)
    c.drawCentredString(x + w / 2, y + h / 2 - size * 0.34, text)


def wrap(c, text, width, size):
    words, lines, cur = text.split(), [], ""
    for word in words:
        trial = f"{cur} {word}".strip()
        if pdfmetrics.stringWidth(trial, "Nunito", size) <= width:
            cur = trial
        else:
            if cur:
                lines.append(cur)
            cur = word
    if cur:
        lines.append(cur)
    return lines


def para(c, text, x, y, width, size, leading, color=MUTED):
    c.setFillColor(color)
    c.setFont("Nunito", size)
    for i, line in enumerate(wrap(c, text, width, size)):
        c.drawString(x, y - i * leading, line)
    return y - (len(wrap(c, text, width, size)) - 1) * leading


def footer(c):
    c.setStrokeColor(LINE)
    c.setLineWidth(0.7)
    c.line(52, 49, W - 52, 49)
    draw(c, Image.open(ICON), 52, 12, 30, 30)
    c.setFillColor(MUTED)
    c.setFont("Nunito", 7.5)
    c.drawString(91, 30, "Interval Jump Printables")
    c.setFillColor(AZUL)
    c.drawCentredString(W / 2, 25, "beeskeysapp.com")
    c.setFillColor(MUTED)
    c.drawRightString(W - 52, 25, "Made for playful music lessons")
    c.linkURL(SITE_URL, (W / 2 - 55, 14, W / 2 + 55, 36), relative=0, thickness=0)


# ---------------------------------------------------------------- pages

def piano_photo():
    """Josh's photo of the cut-outs on his piano (IMG_6511, Sep 11 2026),
    cropped to 3:2 from the bottom so the dice and the tokens fill it."""
    im = Image.open(PHOTO).convert("RGB")
    h = int(im.width * 2 / 3)
    return im.crop((0, im.height - h, im.width, im.height))


def fan(c, sheet, spare=None):
    """The sheet on the right and the piano photo on the left, both on the
    white rim, leaning gently toward each other; a ladybug crawls onto the
    sheet's corner. The photo shows the game being played, so the sheet no
    longer has to carry that on its own. Shared by the cover page and the
    transparent art so they never drift. (`spare` keeps the two-sheet call
    shape of the sibling builders.)"""
    paper(c, piano_photo(), 214, 292, 304, angle=-3.2)
    paper(c, sheet, 540, 302, 384, angle=1.6)
    bug = Image.open(LADYBUG).convert("RGBA").rotate(-32, expand=True, resample=Image.BICUBIC)
    draw(c, bug, 706, 432, 34)


def flat_fan(circle, write_in_ink=None):
    """The fan pre-flattened to one axis-aligned bitmap on the page's white.

    Drawing the sheets rotated in the PDF left every viewer to rasterize the
    tilted staff lines itself, and they come out jagged and moire-ridden at
    most zooms (Josh flagged it). Rasterizing the fan here at 600 dpi and
    Lanczos-downsampling to 300 bakes the anti-aliasing in; the viewer then
    only ever scales an upright image, which every renderer does cleanly."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)
    fan(c, circle, write_in_ink)
    c.showPage()
    c.save()

    doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
    pix = doc[0].get_pixmap(dpi=600)
    doc.close()
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    return im.resize((pix.width // 2, pix.height // 2), Image.LANCZOS)


def page_one(c, circle, write_in_ink=None):
    # The flattened fan carries the page's white ground, so it goes down first
    # and everything else draws over it.
    c.drawImage(ImageReader(jpeg(flat_fan(circle, write_in_ink), quality=80)),
                0, 0, W, H)

    c.setFillColor(MUTED)
    c.setFont("Nunito", 10)
    c.drawString(42, H - 34, "Interval Jump Printables")
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    c.line(42, H - 44, W - 42, H - 44)

    c.setFillColor(INK)
    c.setFont("Nunito", 28)
    c.drawString(42, H - 92, "Ladybug Hunt")
    c.setFillColor(AZUL)
    c.setFont("Nunito", 9.5)
    c.drawString(43, H - 111, "ROLL  •  JUMP  •  CATCH")

    # The frog takes the masthead slot the bee holds on the Bees Keys covers.
    draw(c, Image.open(FROG), W - 116, H - 116, 62)

    c.setFillColor(INK)
    c.setFont("Nunito", 12)
    c.drawCentredString(W / 2, 100, "A cut-out piano game for repeat, step, and skip")
    c.setFillColor(CERULEAN)
    c.setFont("Nunito", 8.3)
    c.drawCentredString(W / 2, 82, "Frog, eight ladybugs, a dice key, and two panels of ways to play. Print at 100% on card stock.")

    footer(c)
    c.showPage()


def page_two(c, qr_ios, qr_play):
    c.setFillColor(HexColor("#FBFCF8"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(INK)
    c.setFont("Nunito", 24)
    c.drawString(44, H - 60, "Keep learning with Interval Jump")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 9.5)
    c.drawString(45, H - 80, "Interval practice that feels like a game.")

    # ---- the game (the whole panel is one big link to the /go landing page)
    panel(c, 44, 78, 490, 440, Color(1, 0.985, 0.89, alpha=0.66), GOLD)
    c.linkURL(f"{SITE_URL}/go", (44, 78, 534, 518), relative=0, thickness=0)
    c.setFillColor(INK)
    c.setFont("Nunito", 13)
    c.drawString(66, 488, "Choose the jump. Cross the river.")
    # Not "the game's buttons": the screenshot below happens to show the ordinal
    # notation (1st-5th), the other of the two labelings the game offers.
    para(c,
         "Interval Jump plays the same three jumps on the staff: repeat, step, "
         "and skip, log to log across the river.",
         66, 468, 440, 8.8, 12)

    # The real gameplay screenshot, on the same white stock as a sheet preview.
    shot = Image.open(SHOT).convert("RGB")
    shot.thumbnail((1400, 1400))
    sw = 400
    sh = sw * shot.height / shot.width
    paper(c, shot, 66 + sw / 2, 140 + sh / 2, sw, angle=0, rim=4)

    pill(c, 66 + sw / 2 - 122, 100, 244, 24, HexColor("#9CBF60"),
         "Free on the App Store and Google Play", size=8.4)

    # ---- Pro + QRs
    panel(c, 558, 78, 190, 440, Color(0.94, 0.98, 0.88, alpha=0.75), HexColor("#B7D37F"))
    c.setFillColor(INK)
    c.setFont("Nunito", 14)
    c.drawString(580, 486, "INTERVAL JUMP")
    c.setFillColor(GOLD_DEEP)
    c.setFont("Nunito", 14)
    c.drawString(580, 468, "PRO")

    para(c,
         "Repeat, step, and skip are free forever. Pro adds leaps, the "
         "4th-9th intervals, custom practice sessions, and all the timers. "
         "One-time unlock, no subscription.",
         580, 448, 148, 8.2, 11.4)

    qw = 74
    for qr, label, url, top in [(qr_ios, "Scan for the App Store", APP_STORE, 350),
                                (qr_play, "Scan for Google Play", PLAY_STORE, 218)]:
        x = 558 + (190 - qw - 12) / 2
        c.setFillColor(white)
        c.roundRect(x, top - qw - 12, qw + 12, qw + 12, 8, fill=1, stroke=0)
        draw(c, qr, x + 6, top - qw - 6, qw, qw)
        c.setFillColor(CERULEAN)
        c.setFont("Nunito", 7.8)
        c.drawCentredString(558 + 95, top - qw - 26, label)
        c.linkURL(url, (x, top - qw - 12, x + qw + 12, top), relative=0, thickness=0)

    footer(c)
    c.showPage()


def write_art(path, circle, write_in_ink=None, dpi=150):
    """The fan alone on a transparent ground, for the OG and social cards.

    Rendered at 4x and downsampled: a straight render leaves the rotated
    sheets' edges stair-stepped (the same jaggies the site's cover JPG had
    until it was supersampled the same way)."""
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(W, H))
    fan(c, circle, write_in_ink)
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
    circle = sheet_page("interval-jump-ladybug-hunt.pdf")
    write_in_ink = None

    if "--art" in sys.argv:
        write_art(sys.argv[sys.argv.index("--art") + 1], circle, write_in_ink)
        return

    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("Ladybug Hunt - Interval Jump")
    c.setAuthor("Bees Keys")
    page_one(c, circle, write_in_ink)
    page_two(c, qr_image(APP_STORE), qr_image(PLAY_STORE))
    c.save()

    doc = pymupdf.open(OUT)
    links = [(i + 1, l["uri"]) for i, p in enumerate(doc) for l in p.get_links() if l.get("uri")]
    sizes = [(round(p.rect.width), round(p.rect.height)) for p in doc]
    doc.close()
    print(f"{OUT}: {len(sizes)} pages {sizes}, {os.path.getsize(OUT) // 1024} KB")
    for page, uri in links:
        print(f"  p{page}  {uri}")
    if sizes != [(792, 612)] * 2:
        sys.exit("cover must be landscape US Letter to match the sheets")


if __name__ == "__main__":
    main()
