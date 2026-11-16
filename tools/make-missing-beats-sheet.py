"""Bee's Friendsgiving: Missing Beats worksheet (Bees Keys).

Kristianna's sketch: eight dinner plates in the sky, each holding one measure
with some beats missing (a dashed box marks the gap, sized to the beats it
needs). Bee and friends gather round a tree-stump table underneath.

Only quarters, halves, dotted halves, whole notes and quarter rests. Two
meters (4/4 and 3/4), two titles (Friendsgiving and the holiday-neutral
Bee's Dinner), each as a white printer copy and a "studio" copy on the
autumn hillside from tools/make-friendsgiving-sheet.py.

Bugs are the Sound Garden / Rhythm Phrase Builders set; the printer copy
uses their line art from tools/rhythm-phrase-art/bw/.

    python3 tools/make-missing-beats-sheet.py [out_dir]
"""
import io
import math
import os
import re
import sys
import tempfile

import fitz
from fontTools.ttLib import TTFont as FTFont
from fontTools.varLib import instancer
from PIL import Image, ImageOps
from reportlab.lib.colors import HexColor
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfgen import canvas

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
BEESKEYS = os.path.expanduser("~/Repos/BeesKeys/BeesKeys/assets")
NUNITO = os.path.join(BEESKEYS, "font", "Nunito-VariableFont_wght.ttf")
MEADOW = os.path.join(HERE, "friendsgiving-art", "fall-meadow-clear.png")
SG = os.path.join(HERE, "sound-garden-art")
RP = os.path.join(HERE, "rhythm-phrase-art")

W, H = landscape(letter)
MARGIN = 22
BORDER = 5
INK = HexColor("#1E1E1E")
MUTED = HexColor("#6B6B6B")
HONEY = HexColor("#F2C237")
RIM = HexColor("#C98A2B")
BARK = HexColor("#8A5A2E")
BARK_DARK = HexColor("#5C3A1C")
WOOD = HexColor("#EBCB94")
RING = HexColor("#C99A58")
MEADOW_AR = 1536 / 1024

STUDIO = False

# (file slug, title, what the plates are "for" in the subtitle)
TITLES = [
    ("bees-keys-friendsgiving-missing-beats", "Bee's Friendsgiving: Missing Beats"),
    ("bees-keys-bees-dinner-missing-beats", "Bee's Dinner: Missing Beats"),
]
SUBTITLE = "Each plate is missing one or more beats. Draw the missing notes or rests to complete each measure."

# One measure per plate. Q quarter, H half, D dotted half, W whole,
# R quarter rest, a digit = that many beats missing.
METERS = {
    "44": (4, ["HQ1", "Q3", "D1", "2H", "QRQ1", "4", "Q2Q", "3Q"]),
    "34": (3, ["H1", "Q2", "QQ1", "1H", "QR1", "3", "Q1Q", "2Q"]),
}
BEATS = {"Q": 1, "R": 1, "H": 2, "D": 3, "W": 4}

# Bravura restQuarter (Steinberg, SIL OFL), font units, y up; 250 = a staff space.
REST = ("M78 -38C94 -58 108 -77 121 -98C123 -102 127 -110 127 -112C127 -113 127 -115 126 -116C124 -120 120 -121 "
        "115 -121C111 -121 103 -119 99 -118C94 -118 88 -115 83 -115C40 -115 1 -158 1 -211C1 -261 44 -310 117 -366"
        "C125 -372 135 -375 143 -375C150 -375 157 -373 158 -369C159 -366 160 -364 160 -362C160 -353 152 -345 144 "
        "-338C131 -338 120 -311 118 -302C115 -294 114 -285 114 -276C114 -245 129 -210 161 -204C166 -203 171 -203 "
        "177 -203C206 -203 239 -214 255 -220C256 -220 257 -221 258 -221C261 -222 263 -222 265 -222C268 -222 270 "
        "-221 270 -218C270 -206 244 -173 233 -161C195 -115 164 -78 164 -22C164 -18 165 -13 165 -9C169 49 205 97 "
        "231 138C234 143 235 148 235 153C235 163 231 172 231 172C231 172 83 348 66 365C61 370 54 373 48 373C38 "
        "373 28 366 28 352C28 347 29 342 32 336C36 325 93 274 93 202C93 165 78 122 33 75C23 65 19 54 19 46C19 32 "
        "29 22 29 22Z")

# Plates
PLATE_W, PLATE_H, PLATE_GAP = 176, 132, 7
ROW_TOP = H - MARGIN - 82
RX, RY = 7.6, 5.4          # notehead radii
STEM = 36
SPACE = 2 * RY             # "staff space" for sizing the rest

# Guests round the stump: (art, x of centre, y of bottom, width, flip). Left
# bugs face right as drawn; right-hand ones are flipped to face the table.
# Positions are Kristianna's (Nov 16 2026); she does not want bugs overlapping.
# Widths are mirrored in missing-beats-art/make-lineart.py (line weight).
STUMP_CX, STUMP_BASE, STUMP_W, STUMP_H = W / 2, 50, 176, 74
GUESTS_BACK = [
    ("butterfly", STUMP_CX - 62, 150, 84, False),
    ("bee", STUMP_CX + 58, 146, 96, False),
]
GUESTS_SIDE = [
    ("grasshopper-drawn", STUMP_CX - 254, 26, 112, False),
    ("ladybug", STUMP_CX - 141, 80, 104, False),
    ("caterpillar", STUMP_CX + 206, 27, 108, True),
    ("cricket-drawn", STUMP_CX + 146, 84, 110, True),
]


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


def meadow_jpeg():
    buf = io.BytesIO()
    Image.open(MEADOW).convert("RGB").save(buf, "JPEG", quality=88)
    buf.seek(0)
    return ImageReader(buf)


def pill(c, cx, baseline, text, font, size, pad=7):
    w = pdfmetrics.stringWidth(text, font, size) + 2 * pad + 6
    h = size + 2 * pad - 4
    c.saveState()
    c.setFillColorRGB(1, 1, 1, alpha=0.88)
    c.roundRect(cx - w / 2, baseline - pad + 1 - size * 0.18, w, h, h / 2, stroke=0, fill=1)
    c.restoreState()


def frame(c, title):
    if STUDIO:
        mw = H * MEADOW_AR
        c.drawImage(meadow_jpeg(), (W - mw) / 2, 0, mw, H)
    else:
        c.setStrokeColor(INK)
        c.setLineWidth(BORDER)
        c.roundRect(MARGIN, MARGIN, W - 2 * MARGIN, H - 2 * MARGIN, 10, stroke=1, fill=0)
    c.setFillColor(INK)
    c.setFont("Nunito-Black", 30)
    c.drawCentredString(W / 2, H - MARGIN - 44, title)
    c.setFillColor(INK if STUDIO else MUTED)
    c.setFont("Nunito", 13)
    c.drawCentredString(W / 2, H - MARGIN - 66, SUBTITLE)


def footer(c):
    text = "Bees Keys  ·  beeskeysapp.com"
    if STUDIO:
        pill(c, W / 2, MARGIN + 9, text, "Nunito", 8.5, pad=5)
    c.setFillColor(MUTED)
    c.setFont("Nunito", 8.5)
    c.drawCentredString(W / 2, MARGIN + 9, text)


# ---------- notation ----------

def head(c, x, y, hollow=False):
    c.saveState()
    c.translate(x, y)
    c.rotate(22)
    c.setFillColor(INK)
    c.ellipse(-RX, -RY, RX, RY, stroke=0, fill=1)
    if hollow:
        c.setFillColorRGB(1, 1, 1)
        c.rotate(18)
        c.ellipse(-RX * 0.72, -RY * 0.46, RX * 0.72, RY * 0.46, stroke=0, fill=1)
    c.restoreState()


def stem(c, x, y):
    c.setStrokeColor(INK)
    c.setLineWidth(1.9)
    c.setLineCap(0)
    sx = x + RX - 1.3
    c.line(sx, y + 1.6, sx, y + STEM)


def rest(c, x, y):
    s = SPACE / 250.0
    nums = re.findall(r"[MCZ]|-?\d+", REST)
    c.saveState()
    c.translate(x - 135 * s, y + STEM * 0.42)
    c.scale(s, s)
    p = c.beginPath()
    i = 0
    while i < len(nums):
        t = nums[i]
        if t == "M":
            p.moveTo(float(nums[i + 1]), float(nums[i + 2])); i += 3
        elif t == "C":
            i += 1
            while i < len(nums) and nums[i] not in "MCZ":
                p.curveTo(*[float(v) for v in nums[i:i + 6]]); i += 6
        else:
            p.close(); i += 1
    c.setFillColor(INK)
    c.drawPath(p, stroke=0, fill=1)
    c.restoreState()


def measure(c, x0, x1, y, code, beats):
    """Draw one measure between x0 and x1, noteheads on the line y."""
    slot = (x1 - x0) / beats
    b = 0
    for ch in code:
        cx = x0 + slot * (b + 0.5)
        if ch.isdigit():
            n = int(ch)
            c.saveState()
            c.setStrokeColor(MUTED)
            c.setLineWidth(1.3)
            c.setDash(4, 3)
            c.roundRect(x0 + slot * b + 2.5, y - RY - 7, slot * n - 5, STEM + RY + 14, 6, stroke=1, fill=0)
            c.restoreState()
            b += n
            continue
        if ch == "R":
            rest(c, cx, y)
        elif ch == "W":
            head(c, cx, y, hollow=True)
        else:
            stem(c, cx, y)
            head(c, cx, y, hollow=ch in "HD")
            if ch == "D":
                c.setFillColor(INK)
                c.circle(cx + RX + 5, y + 0.5, 1.9, stroke=0, fill=1)
        b += BEATS[ch]


def plate(c, x, y, code, beats):
    """A dinner plate (bottom-left x, y) holding one measure."""
    cx, cy = x + PLATE_W / 2, y + PLATE_H / 2
    c.saveState()
    if STUDIO:
        c.setFillColor(HexColor("#FFFDF6"))
        c.setStrokeColor(RIM)
    else:
        c.setFillColorRGB(1, 1, 1)
        c.setStrokeColor(INK)
    c.setLineWidth(2.2)
    c.ellipse(x, y, x + PLATE_W, y + PLATE_H, stroke=1, fill=1)
    c.setLineWidth(0.9)
    c.setStrokeColor(HONEY if STUDIO else MUTED)
    c.ellipse(x + 7, y + 7, x + PLATE_W - 7, y + PLATE_H - 7, stroke=1, fill=0)
    c.restoreState()

    ny = cy - STEM / 2 + 1                    # notehead line
    left = x + 17
    c.setFillColor(INK)
    c.setFont("Nunito-Black", 21)
    c.drawCentredString(left + 6, ny + STEM / 2 + 1.5, str(beats))
    c.drawCentredString(left + 6, ny + STEM / 2 - 16, "4")
    bar_x = x + PLATE_W - 18
    measure(c, left + 17, bar_x - 8, ny, code, beats)
    c.setStrokeColor(INK)
    c.setLineWidth(1.8)
    c.line(bar_x, ny - RY - 3, bar_x, ny + STEM + 3)


# ---------- the table and the guests ----------

def art(name):
    if not STUDIO:
        p = os.path.join(HERE, "missing-beats-art", name + "-bw.png")   # redrawn for this sheet
        if os.path.exists(p):
            return p
        p = os.path.join(RP, "bw", name + ".png")
        if os.path.exists(p):
            return p
    for d in (RP, SG):
        p = os.path.join(d, name + ".png")
        if os.path.exists(p):
            return p
    raise FileNotFoundError(name)


def guest(c, name, cx, y, w, flip):
    im = Image.open(art(name)).convert("RGBA")
    im = im.crop(im.getbbox())
    if flip:
        im = ImageOps.mirror(im)
    px = int(w * 300 / 72)
    im = im.resize((px, round(px * im.height / im.width)), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "PNG")
    buf.seek(0)
    h = w * im.height / im.width
    c.drawImage(ImageReader(buf), cx - w / 2, y, w, h, mask="auto")


def stump(c, cx, base, w, h):
    """A tree-stump table: flared bark body, ringed top, a plate per guest."""
    top_ry = w * 0.15
    top_y = base + h                           # centre of the top face
    hw = w / 2
    c.saveState()
    c.setLineJoin(1)
    c.setStrokeColor(BARK_DARK if STUDIO else INK)
    c.setLineWidth(1.8 if STUDIO else 1.3)
    c.setFillColor(BARK if STUDIO else HexColor("#FFFFFF"))
    p = c.beginPath()
    p.moveTo(cx - hw, top_y)
    p.curveTo(cx - hw, base + h * 0.35, cx - hw - 4, base + 10, cx - hw - 22, base + 1)   # left root
    p.curveTo(cx - hw - 6, base - 5, cx - hw * 0.62, base - 2, cx - hw * 0.5, base + 5)
    p.curveTo(cx - hw * 0.3, base - 7, cx + hw * 0.25, base - 7, cx + hw * 0.5, base + 5)
    p.curveTo(cx + hw * 0.62, base - 2, cx + hw + 6, base - 5, cx + hw + 22, base + 1)    # right root
    p.curveTo(cx + hw + 4, base + 10, cx + hw, base + h * 0.35, cx + hw, top_y)
    p.close()
    c.drawPath(p, stroke=1, fill=1)
    # bark grooves
    c.setLineWidth(1.2 if STUDIO else 0.8)
    c.setLineCap(1)
    for fx, a, b in ((-0.7, 0.2, 0.62), (-0.42, 0.34, 0.74), (-0.12, 0.12, 0.5),
                     (0.2, 0.3, 0.72), (0.5, 0.16, 0.56), (0.76, 0.36, 0.7)):
        gx = cx + hw * fx
        drop = top_ry * math.sqrt(max(0, 1 - fx * fx))
        y0, y1 = top_y - drop - h * a, top_y - drop - h * b
        c.bezier(gx, y0, gx - 2.5, y0 - (y0 - y1) / 3, gx + 2.5, y1 + (y0 - y1) / 3, gx, y1)
    # top face
    c.setLineWidth(1.8 if STUDIO else 1.3)
    c.setFillColor(WOOD if STUDIO else HexColor("#FFFFFF"))
    c.ellipse(cx - hw, top_y - top_ry, cx + hw, top_y + top_ry, stroke=1, fill=1)
    c.setStrokeColor(RING if STUDIO else INK)
    c.setLineWidth(0.8 if STUDIO else 0.6)
    for k in (0.8, 0.56, 0.3):
        c.ellipse(cx - hw * k, top_y - top_ry * k, cx + hw * k, top_y + top_ry * k, stroke=1, fill=0)
    # little plates, one per guest
    c.setStrokeColor(RIM if STUDIO else INK)
    for fx, fy in ((-0.66, -0.08), (-0.36, 0.5), (-0.3, -0.56), (0.3, -0.56), (0.36, 0.5), (0.66, -0.08)):
        px, py = cx + hw * fx, top_y + top_ry * fy
        c.setFillColorRGB(1, 1, 1)
        c.setLineWidth(0.9)
        c.ellipse(px - 13, py - 4.4, px + 13, py + 4.4, stroke=1, fill=1)
        c.setLineWidth(0.5)
        c.ellipse(px - 8, py - 2.6, px + 8, py + 2.6, stroke=1, fill=0)
    c.restoreState()


def scene(c):
    for g in GUESTS_BACK:
        guest(c, *g)
    stump(c, STUMP_CX, STUMP_BASE, STUMP_W, STUMP_H)
    for g in sorted(GUESTS_SIDE, key=lambda g: -g[2]):     # lower on the page = nearer
        guest(c, *g)


def sheet(c, title, beats, codes):
    frame(c, title)
    total = 4 * PLATE_W + 3 * PLATE_GAP
    x0 = (W - total) / 2
    for i, code in enumerate(codes):
        assert sum(int(ch) if ch.isdigit() else BEATS[ch] for ch in code) == beats, code
        r, k = divmod(i, 4)
        plate(c, x0 + k * (PLATE_W + PLATE_GAP), ROW_TOP - PLATE_H - r * (PLATE_H + PLATE_GAP), code, beats)
    scene(c)
    footer(c)


def main():
    out = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "output", "missing-beats")
    os.makedirs(out, exist_ok=True)
    register_fonts()
    global STUDIO
    for slug, title in TITLES:
        for meter, (beats, codes) in METERS.items():
            for STUDIO in (False, True):
                name = f"{slug}-{meter}" + ("-studio" if STUDIO else "")
                path = os.path.join(out, f"{name}.pdf")
                c = canvas.Canvas(path, pagesize=(W, H))
                c.setTitle(title)
                sheet(c, title, beats, codes)
                c.save()
                fitz.open(path)[0].get_pixmap(dpi=110).save(os.path.join(out, f"{name}.png"))
                print(path)


if __name__ == "__main__":
    main()
