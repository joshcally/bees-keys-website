"""Left or Right? / Which Key Is Higher? worksheets (Bees Keys).

Four US Letter landscape sheets, the keyboards drawn by
tools/beeskeys_keyboard.py (the app's F+ and C+ boards):

  1. Left or Right?        one huge keyboard, the bee above it, two arrows
  2. Left or Right? (x6)   six small boards, the bee centered with two arrows,
                           a short higher/lower prompt under each
  3. Which Key Is Higher?  six C..E boards, bee and frog on white keys
  4. Which Key Is Lower?   same, circle the lower one

The prompt cards that go with sheet 1 are their own deck:
tools/make-left-or-right-cards.py.

Each sheet comes in two copies: the printer-friendly white page with a
black frame, and a full-color "studio" copy (Josh's name for it) on the
app's own meadow background (BeesKeys background.png), for laminating.

    python3 tools/make-higher-lower-sheets.py [out_dir]

Writes one PDF per sheet and copy (<name>.pdf, <name>-studio.pdf) plus
110-dpi PNG previews.
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
ART = os.path.join(HERE, "higher-lower-art")
BEESKEYS = os.path.expanduser("~/Repos/BeesKeys/BeesKeys/assets")
NUNITO = os.path.join(BEESKEYS, "font", "Nunito-VariableFont_wght.ttf")
MEADOW = os.path.join(BEESKEYS, "Assets.xcassets", "background",
                      "background.imageset", "background.png")

W, H = landscape(letter)
MARGIN = 22
BORDER = 5
INK = HexColor("#1E1E1E")
BLUE = HexColor("#3B82D6")
RED = HexColor("#E5483F")
MUTED = HexColor("#6B6B6B")

BEE = ImageReader(os.path.join(ART, "bee.png"))       # faces left
FROG = ImageReader(os.path.join(ART, "frog.png"))
BEE_AR = 846 / 1000
FROG_AR = 897 / 892
MEADOW_AR = 1536 / 1024


def meadow_jpeg():
    """The app's meadow PNG is 2.5 MB; as a JPEG stream it is a tenth of that
    and prints the same (it is a soft painted background)."""
    buf = io.BytesIO()
    Image.open(MEADOW).convert("RGB").save(buf, "JPEG", quality=88)
    buf.seek(0)
    return ImageReader(buf)

# Set per copy by main(): False for the white page, True for the studio copy.
STUDIO = False


def register_fonts():
    tmp = tempfile.mkdtemp()
    for name, wght in (("Nunito", 600), ("Nunito-Black", 900)):
        f = FTFont(NUNITO)
        instancer.instantiateVariableFont(f, {"wght": wght}, inplace=True)
        # Every instance keeps the variable font's names, and reportlab
        # embeds one face per PostScript name, so give each its own.
        for rec in f["name"].names:
            if rec.nameID in (1, 4, 6, 16):
                rec.string = name
        path = os.path.join(tmp, f"{name}.ttf")
        f.save(path)
        pdfmetrics.registerFont(TTFont(name, path))


# ---------------------------------------------------------------- pieces

def frame(c, title, subtitle=None):
    if STUDIO:
        # Full bleed, cover-fit: the meadow is 3:2, the page a little
        # squarer, so the sides crop.
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
        c.drawCentredString(W / 2, H - MARGIN - 66, subtitle)


def pill(c, cx, baseline, text, font, size, pad=7):
    """A white rounded plate behind text that sits on the grass."""
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


def arrow(c, cx, cy, length, height, direction, color):
    """A fat cartoon block arrow centered at (cx, cy); direction -1 left, +1 right."""
    shaft_h = height * 0.46
    head_l = length * 0.46
    half = length / 2
    pts = [(-half, shaft_h / 2), (half - head_l, shaft_h / 2), (half - head_l, height / 2),
           (half, 0), (half - head_l, -height / 2), (half - head_l, -shaft_h / 2),
           (-half, -shaft_h / 2)]
    p = c.beginPath()
    for i, (x, y) in enumerate(pts):
        x = cx + x * direction
        (p.moveTo if i == 0 else p.lineTo)(x, cy + y)
    p.close()
    c.saveState()
    c.setLineJoin(1)
    c.setFillColor(color)
    c.setStrokeColor(INK)
    c.setLineWidth(max(1.5, height * 0.06))
    c.drawPath(p, stroke=1, fill=1)
    c.restoreState()


def bee(c, cx, cy, width):
    h = width * BEE_AR
    c.drawImage(BEE, cx - width / 2, cy - h / 2, width, h, mask="auto")


def frog(c, cx, bottom, width):
    c.drawImage(FROG, cx - width / 2, bottom, width, width * FROG_AR, mask="auto")


def white_key_point(geo, i, x, y_top, frac=0.62):
    """A point on white key i's top surface, `frac` of the way down to its ledge."""
    whites, _ = geo
    tl, tr, lr, ll = whites[i][1]["top"]
    top = ((tl[0] + tr[0]) / 2, tl[1])
    bot = ((ll[0] + lr[0]) / 2, ll[1])
    px = top[0] + (bot[0] - top[0]) * frac
    py = top[1] + (bot[1] - top[1]) * frac
    width = (lr[0] - ll[0]) * (0.6 + 0.4 * frac)
    return x + px, y_top - py, width


def key_center_x(geo, i, x):
    whites, _ = geo
    tl, tr, lr, ll = whites[i][1]["top"]
    return x + (ll[0] + lr[0]) / 2


# ---------------------------------------------------------------- sheets

def sheet_one(c):
    frame(c, "Left or Right?", "Which way should Bee fly?")
    kw = W - 2 * MARGIN - 60
    kh = kw / kb.aspect(11)
    x = (W - kw) / 2
    y_top = MARGIN + 34 + kh
    _, geo = kb.draw_keyboard(c, x, y_top, kw)
    cx = key_center_x(geo, 5, x)
    cy = y_top + 118
    bee(c, cx, cy, 150)
    arrow(c, cx - 215, cy - 8, 190, 120, -1, BLUE)
    arrow(c, cx + 215, cy - 8, 190, 120, +1, RED)
    footer(c)


PROMPTS = [
    "Go higher", "Go lower",
    "Fly to a low sound", "Fly to a high sound",
    "Find a lower key", "Find a higher key",
]


def sheet_six_bees(c):
    frame(c, "Left or Right?", "Circle the arrow that shows which way Bee should fly.")
    cols, rows = 2, 3
    cell_w = (W - 2 * MARGIN - 40) / cols
    top = H - MARGIN - 74
    cell_h = (top - MARGIN - 20) / rows
    kw = cell_w - 110
    kh = kw / kb.aspect(11)
    for n, prompt in enumerate(PROMPTS):
        col, row = n % cols, n // cols
        x = MARGIN + 20 + col * cell_w + (cell_w - kw) / 2
        cell_top = top - row * cell_h
        y_top = cell_top - 50
        _, geo = kb.draw_keyboard(c, x, y_top, kw, outline=1.5)
        bx = key_center_x(geo, 5, x)  # the middle of the 11 whites
        by = y_top + 24
        bee(c, bx, by, 46)
        arrow(c, bx - 56, by - 2, 50, 32, -1, BLUE)
        arrow(c, bx + 56, by - 2, 50, 32, +1, RED)
        if STUDIO:
            pill(c, x + kw / 2, y_top - kh - 16, prompt, "Nunito", 14)
        c.setFillColor(INK)
        c.setFont("Nunito", 14)
        c.drawCentredString(x + kw / 2, y_top - kh - 16, prompt)
    footer(c)


# (bee key, frog key) on the app's C+ board (C..E, 10 whites); far apart
# first, then closer. The middle row of LOWER swaps bee and frog so the
# two pages don't read as mirror images of each other.
HIGHER = [(0, 9), (8, 0), (2, 7), (8, 4), (3, 5), (6, 4)]
LOWER = [(9, 0), (1, 9), (1, 7), (8, 3), (5, 3), (4, 6)]


def sheet_pairs(c, title, subtitle, pairs):
    frame(c, title, subtitle)
    cols, rows = 2, 3
    cell_w = (W - 2 * MARGIN - 40) / cols
    top = H - MARGIN - 78
    cell_h = (top - MARGIN - 6) / rows
    kw = cell_w - 80
    kh = kw / kb.aspect(10)
    for n, (b, f) in enumerate(pairs):
        col, row = n % cols, n // cols
        x = MARGIN + 20 + col * cell_w + (cell_w - kw) / 2
        cell_top = top - row * cell_h
        y_top = cell_top - (cell_h - kh) / 2 + 4
        _, geo = kb.draw_keyboard(c, x, y_top, kw, start="C", white_count=10,
                                  outline=1.5)
        fx, fy, fw = white_key_point(geo, f, x, y_top, 1.0)
        frog(c, fx, fy - 8, fw * 1.05)
        bx, by, bw = white_key_point(geo, b, x, y_top, 1.0)
        bee(c, bx, by + 7, bw * 1.3)
    footer(c)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "output", "higher-lower")
    os.makedirs(out, exist_ok=True)
    register_fonts()
    sheets = [
        ("bees-keys-left-or-right", sheet_one),
        ("bees-keys-left-or-right-six", sheet_six_bees),
        ("bees-keys-which-key-is-higher",
         lambda c: sheet_pairs(c, "Which Key Is Higher?",
                               "Circle the friend on the higher key.", HIGHER)),
        ("bees-keys-which-key-is-lower",
         lambda c: sheet_pairs(c, "Which Key Is Lower?",
                               "Circle the friend on the lower key.", LOWER)),
    ]
    global STUDIO
    for STUDIO in (False, True):
        for name, draw in sheets:
            name += "-studio" if STUDIO else ""
            path = os.path.join(out, f"{name}.pdf")
            c = canvas.Canvas(path, pagesize=(W, H))
            c.setTitle(name)
            draw(c)
            c.save()
            fitz.open(path)[0].get_pixmap(dpi=110).save(os.path.join(out, f"{name}.png"))
            print(path)


if __name__ == "__main__":
    main()
