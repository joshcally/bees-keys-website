#!/usr/bin/env python3
"""Build the two-page cover that leads the Interval Jump Bug Collection printable.

    pip install reportlab pymupdf qrcode
    python3 tools/build-interval-jump-cover.py <cover.pdf>
    python3 tools/build-interval-jump-cover.py --thumb <card.jpg>

Same cover language as the Bees Keys printables — eyebrow, hairline rule, light
title, a fanned preview of the real sheets, and a footer bar — with two
deliberate departures.

**Portrait.** Every Bees Keys printable is US Letter landscape and its cover
matches. The bug sheets are portrait, so this cover is portrait too: a cover in
the other orientation would make the merged PDF rotate halfway through.

**The previews are cut, not whole.** A worksheet cover shows whole pages,
because a worksheet is used whole. These sheets are cut up, so the cover shows
what a teacher ends up holding: a block of stickers off the sheet, one 6-slot
card, and one Collect All Six card, each cropped on the exact line the scissors
follow. The crop rectangles are computed from the same geometry the generators
use (`printables/sheet.py`, `printables/cards.py`), not eyeballed, so they stay
right if a sheet is ever regenerated at a different size.

Page two is the app tie-in, and its claims are pulled from the game rather than
imagined: the lily-pad detour happens once a run for everyone, only Pro puts a
bug on the pad, and the rarer three bugs enter the pool only when an ordinal
4th-9th interval is switched on (`model/Game.swift`, `rollCritter`). Keep it
that way — it is the difference between a printable and an advert.

The output carries live App Store links as real PDF annotations, which is why
`tools/combine-printable.py` must be the thing that merges it.
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
FROG = f"{IJ}/IntervalJump/assets/Assets.xcassets/frog/frog-0.imageset/frog-0.png"
PAD = f"{IJ}/IntervalJump/assets/Assets.xcassets/river/lily-pad.imageset/lily-pad.png"
ART = f"{IJ}/printables/art"
SHEETS = f"{IJ}/printables"

OUT = sys.argv[1] if len(sys.argv) > 1 and not sys.argv[1].startswith("-") \
    else "/tmp/interval-jump-bug-collection-cover.pdf"

APP_STORE = "https://apps.apple.com/us/app/interval-jump-read-music-fast/id6736377103"
SITE_URL = "https://beeskeysapp.com"

W, H = letter  # portrait, unlike every Bees Keys cover
# The resources.html card list is landscape whatever the printable is, so the
# thumbnail is composed on a landscape page of its own.
THUMB_W, THUMB_H = letter[1], letter[0]

# Bees Keys cover furniture (ink, muted, hairline) so the two sit in one family,
# over Interval Jump's own palette: azul and cerulean from `colors/*.colorset`,
# gold and parchment from `view/common/SegmentedPicker.swift`.
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

BUGS = ["fly", "butterfly", "dragonfly", "ladybug", "beetle", "firefly"]


# ---------------------------------------------------------------- assets

def sheet_page(name, index=0, dpi=300):
    """One page of a generated sheet, rendered from the real PDF."""
    doc = pymupdf.open(f"{SHEETS}/{name}")
    pix = doc[index].get_pixmap(dpi=dpi)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    return im


def crops():
    """The three preview pieces, cut on the generators' own grid lines.

    Both numbers below are re-derived rather than hardcoded from a measurement,
    so a change to STICKER or to the card grid moves the crop with it.
    """
    dpi = 300
    inch = lambda x: int(round(x * dpi))

    # sheet.py: a 9x12 grid of 0.81in cells, centred on the page.
    cell = inch(0.81)
    grid_w, grid_h = 9 * cell, 12 * cell
    left, top = (inch(8.5) - grid_w) // 2, (inch(11) - grid_h) // 2
    # Rows 4-8 straddle the block boundary at row 6, so one crop carries all six
    # species — the whole collection, in the sheet's own layout.
    strip = sheet_page("interval-jump-bug-stickers.pdf").crop(
        (left, top + 4 * cell, left + grid_w, top + 8 * cell)
    )

    # cards.py: 2x3 cards on the printable area left by SAFE + TICKZONE.
    avail_w, avail_h = 8.5 - 2 * (0.30 + 0.27), 11 - 2 * (0.30 + 0.27)
    card_w, card_h = inch(avail_w / 2), inch(avail_h / 3)
    cl, ct = (inch(8.5) - 2 * card_w) // 2, (inch(11) - 3 * card_h) // 2
    box = (cl, ct, cl + card_w, ct + card_h)
    six = sheet_page("interval-jump-bug-cards-6-slot.pdf").crop(box)
    ghost = sheet_page("interval-jump-bug-cards-collect-all-six.pdf").crop(box)

    # One loose sticker per species, cut on the same grid, for the peel-and-place
    # detail scattered over the fan.
    loose = [
        sheet_page("interval-jump-bug-stickers.pdf").crop(
            (left + c * cell, top + r * cell, left + (c + 1) * cell, top + (r + 1) * cell)
        )
        for r, c in [(0, 0), (0, 3), (6, 6)]
    ]
    return strip, six, ghost, loose


def qr_image():
    """A QR to the App Store listing, drawn big enough to survive a home printer."""
    q = qrcode.QRCode(box_size=10, border=1, error_correction=qrcode.constants.ERROR_CORRECT_M)
    q.add_data(APP_STORE)
    q.make(fit=True)
    return q.make_image(fill_color="#373936", back_color="white").convert("RGB")


# ---------------------------------------------------------------- drawing

def draw(c, im, x, y, w, h=None):
    """Place a PIL image, keeping alpha."""
    if h is None:
        h = w * im.height / im.width
    c.drawImage(ImageReader(im), x, y, w, h, mask="auto")


def draw_fit(c, im, cx, cy, budget):
    """Centre a bug in a square budget, fitting its *longer* side.

    Scaling by width alone is what a row of these bugs cannot survive: the
    dragonfly is half again wider than it is tall while the beetle is the other
    way round, so one width gives them heights between 24 and 62pt and the tall
    ones climb straight out of their tile. `sheet.py` sizes every sticker with
    `thumbnail((budget, budget))` for the same reason — this is that rule.
    """
    scale = budget / max(im.width, im.height)
    w, h = im.width * scale, im.height * scale
    c.drawImage(ImageReader(im), cx - w / 2, cy - h / 2, w, h, mask="auto")


def paper(c, im, cx, cy, w, angle=0.0, rim=4):
    """A cut piece of the printable, on white stock with a soft drop shadow.

    The sticker sheets and the card fronts are white to the edge, so a preview
    needs its own rim or it dissolves into the page — the same reason
    `.res-shot` on the website carries a border.
    """
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
    draw(c, im, -w / 2, -h / 2, w, h)
    c.restoreState()


def loose_sticker(c, im, cx, cy, w, angle):
    """A single sticker, peeled off the sheet and dropped on the fan."""
    c.saveState()
    c.translate(cx, cy)
    c.rotate(angle)
    c.setFillColor(Color(0, 0, 0, alpha=0.13))
    c.roundRect(-w / 2 + 2, -w / 2 - 3, w, w, 3, fill=1, stroke=0)
    c.setFillColor(white)
    c.roundRect(-w / 2, -w / 2, w, w, 3, fill=1, stroke=0)
    draw(c, im, -w / 2, -w / 2, w, w)
    c.restoreState()


def panel(c, x, y, w, h, fill, stroke):
    """The Bees Keys cover's soft glass card."""
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
    """Greedy wrap against the real font metrics."""
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

def page_one(c, strip, six, ghost, loose):
    c.setFillColor(white)
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(MUTED)
    c.setFont("Nunito", 10)
    c.drawString(42, H - 34, "Interval Jump Printables")
    c.setStrokeColor(INK)
    c.setLineWidth(0.7)
    c.line(42, H - 44, W - 42, H - 44)

    c.setFillColor(INK)
    c.setFont("Nunito", 26)
    c.drawString(42, H - 98, "Bug Collection Sticker Sheets")
    c.setFillColor(AZUL)
    c.setFont("Nunito", 9.5)
    c.drawString(43, H - 117, "PLAY  •  CATCH  •  COLLECT")

    # The frog is the app's face, so it takes the masthead slot the bee holds on
    # the Bees Keys covers.
    draw(c, Image.open(FROG), W - 108, H - 122, 58)

    # The fan: a block of stickers behind, the two cards a teacher actually cuts
    # out in front of it.
    paper(c, strip, 306, 552, 440, angle=-2.4)
    paper(c, six, 174, 338, 244, angle=-5.0)
    paper(c, ghost, 430, 322, 244, angle=4.0)

    loose_sticker(c, loose[0], 66, 598, 40, 13)
    loose_sticker(c, loose[1], 554, 492, 40, -11)
    loose_sticker(c, loose[2], 300, 188, 44, 7)

    c.setFillColor(INK)
    c.setFont("Nunito", 12)
    c.drawCentredString(W / 2, 128, "756 bug stickers and 16 collection cards to cut out")
    c.setFillColor(CERULEAN)
    c.setFont("Nunito", 8.3)
    c.drawCentredString(W / 2, 108, "Print at 100% scale with margins set to None")

    footer(c)
    c.showPage()


def page_two(c, qr):
    c.setFillColor(HexColor("#FBFCF8"))
    c.rect(0, 0, W, H, fill=1, stroke=0)

    c.setFillColor(INK)
    c.setFont("Nunito", 24)
    c.drawString(44, H - 60, "Where the bugs come from")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 9.5)
    c.drawString(45, H - 80, "A frog, a river, and one lily pad every run.")
    draw(c, Image.open(ICON), W - 96, H - 96, 48, 48)

    # ---- how a bug is caught
    panel(c, 44, 480, 524, 210, Color(1, 0.985, 0.89, alpha=0.66), GOLD)
    c.setFillColor(INK)
    c.setFont("Nunito", 14)
    c.drawString(66, 658, "How a bug gets caught")

    steps = [
        ("PLAY", AZUL,
         "Find your frog, look at the next log, and choose the interval for the frog "
         "to jump successfully to the next log."),
        ("CATCH", GOLD_DEEP,
         "Once a run, a lily pad drifts into the gap with a bug waiting on it. "
         "Hop out and back to the next log before the pad sinks — and don't splash, "
         "or the bug is gone."),
        ("COLLECT", CERULEAN,
         "The bug you caught escorts the frog to the island. Peel its sticker and "
         "put it on a card."),
    ]
    y = 628
    for label, color, text in steps:
        pill(c, 66, y - 5.6, 62, 17, color, label, size=7.6)
        para(c, text, 140, y, 406, 9, 12.5)
        y -= 52

    # ---- the six
    panel(c, 44, 300, 524, 160, Color(0.94, 0.98, 0.88, alpha=0.75), HexColor("#B7D37F"))
    c.setFillColor(INK)
    c.setFont("Nunito", 14)
    c.drawString(66, 434, "The six river bugs")
    c.setFillColor(MUTED)
    c.setFont("Nunito", 8.4)
    c.drawString(66, 420, "The rarer bugs are the reward for the harder practice.")

    for i, name in enumerate(BUGS):
        x = 74 + i * 84
        c.setFillColor(CREAM)
        c.roundRect(x, 336, 68, 62, 12, fill=1, stroke=0)
        draw_fit(c, Image.open(f"{ART}/{name}.png"), x + 34, 367, 46)
        c.setFillColor(WOOD)
        c.setFont("Nunito", 7)
        c.drawCentredString(x + 34, 325, name.capitalize())

    # Which three you can catch depends on the practice, so the split is drawn
    # rather than described: a rule under each group with its own condition.
    for x0, x1, note in [(74, 310, "From the very first run"),
                         (326, 562, "With any 4th-9th interval on")]:
        c.setStrokeColor(GOLD)
        c.setLineWidth(0.8)
        c.line(x0, 316, x1, 316)
        c.setFillColor(WOOD)
        c.setFont("Nunito", 7.4)
        c.drawCentredString((x0 + x1) / 2, 306, note)

    # ---- Pro
    panel(c, 44, 96, 524, 184, Color(1, 1, 1, alpha=0.85), LINE)
    c.setFillColor(INK)
    c.setFont("Nunito", 15)
    c.drawString(66, 250, "INTERVAL JUMP")
    c.setFillColor(GOLD_DEEP)
    c.setFont("Nunito", 15)
    c.drawString(66, 229, "PRO")

    para(c,
         "Catching bugs is a Pro feature. Free players still get the lily-pad detour on "
         "every run — it is good interval practice either way — there is just no bug "
         "waiting on the pad.",
         66, 205, 296, 9, 12.5)

    para(c,
         "Pro also unlocks the 4th-9th intervals, custom practice sessions, and all the "
         "timers and controls. One-time unlock, no subscription.",
         66, 155, 296, 9, 12.5, color=INK)

    qw = 88
    c.setFillColor(white)
    c.roundRect(452, 118, qw + 14, qw + 14, 8, fill=1, stroke=0)
    draw(c, qr, 459, 125, qw, qw)
    c.setFillColor(AZUL)
    c.setFont("Nunito", 8.2)
    c.drawCentredString(459 + qw / 2, 106, "Scan for iOS")
    c.linkURL(APP_STORE, (452, 118, 452 + qw + 14, 118 + qw + 14), relative=0, thickness=0)

    pill(c, 386, 236, 170, 26, GOLD_DEEP, "Interval Jump on the App Store", size=8)
    c.linkURL(APP_STORE, (386, 236, 556, 262), relative=0, thickness=0)

    footer(c)
    c.showPage()


def page_thumb(c, strip, six, ghost, loose):
    """The landscape thumbnail for the resources.html card list.

    Cropping the portrait cover to landscape was the obvious shortcut and the
    wrong one: it cut the sheet on all four edges, slicing bugs mid-body, which
    reads as damage rather than as a frame. Every other card in that list shows
    a whole cover page, so this composes the same three pieces afresh at the
    list's own aspect, with nothing running off an edge.
    """
    c.setFillColor(white)
    c.rect(0, 0, THUMB_W, THUMB_H, fill=1, stroke=0)

    paper(c, strip, 396, 428, 560, angle=-2.0)
    paper(c, six, 243, 196, 266, angle=-5.0)
    paper(c, ghost, 551, 184, 266, angle=4.0)

    loose_sticker(c, loose[0], 86, 462, 42, 12)
    loose_sticker(c, loose[1], 716, 340, 42, -12)
    loose_sticker(c, loose[2], 397, 92, 44, 6)

    c.showPage()


def write_thumb(path, strip, six, ghost, loose):
    """Render the thumbnail page to the JPG the card list loads.

    96 dpi over a landscape Letter page is 1056x816 — the exact size the other
    five cards carry, so the row heights stay level.
    """
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=(THUMB_W, THUMB_H))
    page_thumb(c, strip, six, ghost, loose)
    c.save()

    doc = pymupdf.open(stream=buf.getvalue(), filetype="pdf")
    pix = doc[0].get_pixmap(dpi=96)
    im = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    doc.close()
    im.save(path, quality=85)
    print(f"{path}: {im.width}x{im.height}")


def main():
    strip, six, ghost, loose = crops()
    if "--thumb" in sys.argv:
        write_thumb(sys.argv[sys.argv.index("--thumb") + 1], strip, six, ghost, loose)
        return
    qr = qr_image()
    c = canvas.Canvas(OUT, pagesize=(W, H))
    c.setTitle("Bug Collection Sticker Sheets - Interval Jump")
    c.setAuthor("Bees Keys")
    page_one(c, strip, six, ghost, loose)
    page_two(c, qr)
    c.save()

    doc = pymupdf.open(OUT)
    links = [(i + 1, l["uri"]) for i, p in enumerate(doc) for l in p.get_links() if l.get("uri")]
    sizes = [(round(p.rect.width), round(p.rect.height)) for p in doc]
    doc.close()
    print(f"{OUT}: {len(sizes)} pages {sizes}, {os.path.getsize(OUT) // 1024} KB")
    for page, uri in links:
        print(f"  p{page}  {uri}")
    if sizes != [(612, 792)] * 2:
        sys.exit("cover must be portrait US Letter to match the sheets")


if __name__ == "__main__":
    main()
