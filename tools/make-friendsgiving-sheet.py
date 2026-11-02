"""Bee's Friendsgiving / Bee's Friends worksheet (Bees Keys).

Kristianna's puzzle: six bug guests, each name spelled with letters and
small piano-key tiles. A tile is the app's 2-black-key group (C D E) or
3-black-key group (F G A B) with the missing letter's key highlighted; the
student reads the key name, fills the letter, and writes the guest's name.

    1. L A D Y B U G       2. B E E T L E       3. C E N T I P E D E
    4. B U M B L E B E E   5. D R A G O N F L Y 6. C R I C K E T

Same house layout as tools/make-higher-lower-sheets.py (US Letter
landscape, Nunito, black frame, footer) with the keyboards from
tools/beeskeys_keyboard.py, a band left open at the bottom for the guests.
Writes a printer-friendly white page and a "studio" copy on Kristianna's
autumn hillside (tools/friendsgiving-art/fall-meadow.png, 3:2).

    python3 tools/make-friendsgiving-sheet.py [out_dir]
"""
import io
import os
import sys
import tempfile

import fitz
from fontTools.ttLib import TTFont as FTFont
from fontTools.varLib import instancer
from PIL import Image
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

sys.path.insert(0, os.path.dirname(__file__))
import beeskeys_keyboard as kb  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BEESKEYS = os.path.expanduser("~/Repos/BeesKeys/BeesKeys/assets")
NUNITO = os.path.join(BEESKEYS, "font", "Nunito-VariableFont_wght.ttf")
MEADOW = os.path.join(HERE, "friendsgiving-art", "fall-meadow.png")

W, H = landscape(letter)
MARGIN = 22
BORDER = 5
INK = HexColor("#1E1E1E")
MUTED = HexColor("#6B6B6B")
HONEY = HexColor("#F2C237")
HONEY_DARK = HexColor("#C9951A")
MEADOW_AR = 1536 / 1024

STUDIO = False

# (file slug, title, subtitle). The second is the holiday-neutral copy for
# teachers who want one.
VARIANTS = [
    ("bees-keys-friendsgiving", "Bee's Friendsgiving",
     ("Use the piano keys to fill in the missing letters and discover who's coming to Friendsgiving!",)),
    ("bees-keys-bees-friends", "Bee's Friends",
     ("Use the piano keys to fill in the missing letters and discover Bee's friends!",)),
]
BUG_BAND = 66        # open space at the bottom for the guests (later)

# Upper-case = printed letter, lower-case = a key tile to decode.
GUESTS = ["LadYbUg", "beeTLe", "ceNTIPede", "bUMbLebee", "dRagONfLY", "cRIcKeT"]

GROUP = {"c": ("C", 3), "d": ("C", 3), "e": ("C", 3),
         "f": ("F", 4), "g": ("F", 4), "a": ("F", 4), "b": ("F", 4)}
INDEX = {"c": 0, "d": 1, "e": 2, "f": 0, "g": 1, "a": 2, "b": 3}

LETTER_W = 26        # slot width for a printed letter
GAP = 5              # between slots
PAD = 12             # card padding
GUTTER = 14          # between the two cards of a row
LETTER_SIZE = 28
MAX_TILE_H = 44

# Two cards per row, paired so each row carries about the same width.
ROWS = [("LadYbUg", "ceNTIPede"), ("beeTLe", "bUMbLebee"), ("dRagONfLY", "cRIcKeT")]


def meadow_jpeg():
    buf = io.BytesIO()
    Image.open(MEADOW).convert("RGB").save(buf, "JPEG", quality=88)
    buf.seek(0)
    return ImageReader(buf)


def register_fonts():
    tmp = tempfile.mkdtemp()
    for name, wght in (("Nunito", 600), ("Nunito-Bold", 800), ("Nunito-Black", 900)):
        f = FTFont(NUNITO)
        instancer.instantiateVariableFont(f, {"wght": wght}, inplace=True)
        for rec in f["name"].names:
            if rec.nameID in (1, 4, 6, 16):
                rec.string = name
        path = os.path.join(tmp, f"{name}.ttf")
        f.save(path)
        pdfmetrics.registerFont(TTFont(name, path))


def frame(c, title, subtitle=None):
    if STUDIO:
        # cover-fit: the hillside is 3:2, the page a little squarer, so the sides crop
        mw = H * MEADOW_AR
        c.drawImage(meadow_jpeg(), (W - mw) / 2, 0, mw, H)
    else:
        c.setStrokeColor(INK)
        c.setLineWidth(BORDER)
        c.roundRect(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN, 10, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont("Nunito-Black", 30)
    c.drawCentredString(W / 2, H - MARGIN - 44, title)
    if subtitle:
        c.setFillColor(INK if STUDIO else MUTED)
        c.setFont("Nunito", 14)
        for i, line in enumerate(subtitle):
            c.drawCentredString(W / 2, H - MARGIN - 66 - 18 * i, line)


def pill(c, cx, baseline, text, font, size, pad=7):
    w = pdfmetrics.stringWidth(text, font, size) + 2 * pad + 6
    h = size + 2 * pad - 4
    c.saveState()
    c.setFillColorRGB(1, 1, 1, alpha=0.88)
    c.roundRect(cx - w / 2, baseline - pad + 1 - size * 0.18, w, h, h / 2, stroke=0, fill=1)
    c.restoreState()


def footer(c):
    text = "Bees Keys  ·  beeskeysapp.com"
    if STUDIO:
        pill(c, W / 2, MARGIN + 9, text, "Nunito", 8.5, pad=5)
    c.setFillColor(MUTED)
    c.setFont("Nunito", 8.5)
    c.drawCentredString(W / 2, MARGIN + 9, text)


def tile_width(ch, th):
    start, n = GROUP[ch]
    return th * kb.aspect(n)


def slot_width(ch, th):
    return tile_width(ch, th) if ch.islower() else LETTER_W


def word_width(word, th):
    return sum(slot_width(ch, th) + GAP for ch in word) - GAP


def card_width(word, th):
    return word_width(word, th) + 2 * PAD


def fit_tile_height():
    """The biggest tile height at which every row's two cards fit the page."""
    avail = W - 2 * MARGIN - 2 * 14 - GUTTER
    th = MAX_TILE_H
    while th > 20 and any(card_width(a, th) + card_width(b, th) > avail for a, b in ROWS):
        th -= 0.5
    return th


def tile(c, x, y_top, ch, th):
    """A small keyboard group with the key for `ch` highlighted and dotted."""
    start, n = GROUP[ch]
    w = tile_width(ch, th)
    _, geo = kb.draw_keyboard(c, x, y_top, w, start=start, white_count=n,
                              highlights={"white": {INDEX[ch]}}, outline=1.2)
    whites, _ = geo
    tl, tr, lr, ll = whites[INDEX[ch]][1]["top"]
    frac = 0.74
    px = (tl[0] + tr[0]) / 2 + ((ll[0] + lr[0]) / 2 - (tl[0] + tr[0]) / 2) * frac
    py = tl[1] + (ll[1] - tl[1]) * frac
    c.setFillColor(INK)
    c.circle(x + px, y_top - py, max(2.0, th * 0.055), stroke=0, fill=1)
    return w


def card(c, x, y, word, th, extra=0.0):
    """A rounded card at (x, y) bottom-left: tiles above, letters and blanks below.

    `extra` widens the card by spreading that much more space between its slots,
    so a short row can keep the same gutter as the widest one."""
    cw = card_width(word, th) + extra
    gap = GAP + extra / (len(word) - 1)
    ch_ = PAD + th + 10 + LETTER_SIZE + PAD
    c.saveState()
    if STUDIO:
        c.setFillColorRGB(1, 1, 1, alpha=0.9)
        c.setStrokeColor(HONEY)
        c.setLineWidth(2.2)
    else:
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColor(INK)
        c.setLineWidth(1.5)
    c.roundRect(x, y, cw, ch_, 14, stroke=1, fill=1)
    c.restoreState()
    baseline = y + PAD + 4
    tile_top = y + ch_ - PAD
    sx = x + PAD
    for ch in word:
        sw = slot_width(ch, th)
        if ch.islower():
            tile(c, sx, tile_top, ch, th)
            c.setStrokeColor(INK)
            c.setLineWidth(1.6)
            c.line(sx + 2, baseline - 2, sx + sw - 2, baseline - 2)
        else:
            c.setFillColor(INK)
            c.setFont("Nunito-Black", LETTER_SIZE)
            c.drawCentredString(sx + sw / 2, baseline, ch)
        sx += sw + gap
    return cw, ch_


def sheet(c, title, subtitle):
    frame(c, title, subtitle)
    th = fit_tile_height()
    top = H - MARGIN - 92
    bottom = MARGIN + BUG_BAND
    row_h = (top - bottom) / len(ROWS)
    left, right = MARGIN + 14, W - MARGIN - 14
    # every row keeps the gutter of the widest row; shorter rows spread the
    # slack across both cards' slots so the two cards still hug the edges
    gutter = min(right - left - card_width(a, th) - card_width(b, th) for a, b in ROWS)
    for i, (a, b) in enumerate(ROWS):
        cy = top - row_h * (i + 0.5)
        ch_ = PAD + th + 10 + LETTER_SIZE + PAD
        y = cy - ch_ / 2
        slack = right - left - card_width(a, th) - card_width(b, th) - gutter
        card(c, left, y, a, th, slack / 2)
        card(c, right - card_width(b, th) - slack / 2, y, b, th, slack / 2)
    footer(c)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "output", "friendsgiving")
    os.makedirs(out, exist_ok=True)
    register_fonts()
    global STUDIO
    for slug, title, subtitle in VARIANTS:
        for STUDIO in (False, True):
            name = slug + ("-studio" if STUDIO else "")
            path = os.path.join(out, f"{name}.pdf")
            c = canvas.Canvas(path, pagesize=(W, H))
            c.setTitle(title)
            sheet(c, title, subtitle)
            c.save()
            fitz.open(path)[0].get_pixmap(dpi=110).save(os.path.join(out, f"{name}.png"))
            print(path)


if __name__ == "__main__":
    main()
