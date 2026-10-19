#!/usr/bin/env python3
"""Frog's Potions: a two-page Halloween color-by-interval worksheet for Interval
Jump, by Kristianna Callahan.

Page 1, Frog's Potions!, is eight potion bottles holding the even harmonic
intervals (2nd, 4th, 6th, 8th), two of each: one with the lower note on a line
and the upper in a space, one the other way round. Page 2, Frog's Potion
Ingredients!, is eight jars of spooky ingredients holding the odd harmonic
intervals: one unison, three 3rds, two 5ths and two 7ths, line-to-line and
space-to-space. Every staff is clef-less (distance, not pitch, like Frog's
First Jumps and Mushroom Hop). The student picks a color for each interval in
the key, then colors each bottle to match. Pure black line art.

The frog is Kristianna's witch frog drawing (tools/frogs-potions-art/), a
line-art bitmap with its background made transparent.

    python3 tools/make-frogs-potions-sheet.py

Output: output/frogs-potions/interval-jump-frogs-potions.pdf and
-ingredients.pdf (US Letter landscape, vector), each with a -preview.png beside it.
"""

import base64
import math
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "frogs-potions"
NAME = "interval-jump-frogs-potions"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT = ROOT / "tools" / "poster" / "fonts" / "Nunito[wght].ttf"
FROG = ROOT / "tools" / "frogs-potions-art" / "witch-frog-cutout.png"
FROG_SIZE = (1219, 1266)   # the cutout's pixel size, for its aspect ratio
BASKET = ROOT / "tools" / "frogs-potions-art" / "basket-cutout.png"
BASKET_SIZE = (811, 821)

INK = "#1c1c1c"

# Page units are 1/100 in: 1100 x 850.
SPACE = 15                 # staff line spacing
STAFF_W = 108
JAR_SCALE = (1.0, 1.0)     # vessel scale, top row and bottom row

# Harmonic intervals as (lower, upper) staff positions, 0 = bottom line … 8 =
# top line (even = line, odd = space). Five across the top row, three below.
PAGES = {
    "": dict(
        title="Frog&#8217;s Potions!",
        subtitle="Choose a color for each interval, and color the potions to match!",
        key=["2nd", "4th", "6th", "8th"],
        scatter=False,
        cauldron=True,
        # 2nd G-A, 6th G-E, 4th E-A, 8th F-F, 2nd A-B / 6th F-D, 8th E-E, 4th A-D
        items=[(2, 3), (2, 7), (0, 3), (1, 8), (3, 4), (1, 6), (0, 7), (3, 6)],
    ),
    "-ingredients": dict(
        title="Frog&#8217;s Potion Ingredients!",
        subtitle="Choose a color for each interval, and color the jars to match!",
        key=["unison", "3rd", "5th", "7th"],
        scatter=True,
        cauldron=False,
        # 3rd E-G, 5th F-C, unison B, 7th E-D, 3rd A-C / 5th G-D, 3rd D-F, 7th F-E
        items=[(0, 2), (1, 5), (4, 4), (0, 6), (3, 5), (2, 6), (6, 8), (1, 7)],
    ),
}

TOP_ROW = ([377, 572, 767, 962], 446)           # x centers, jar bottom y (right of the key)
BOTTOM_ROW = ([447, 622, 797, 972], 752)        # right of the frog


# ----------------------------------------------------------------- notation

def whole_note(x, y):
    """A hollow notehead with no fill, so a staff line stays visible through it
    (Kristianna: that's how a child tells a line note from a space note)."""
    return (f'<ellipse cx="{x}" cy="{y}" rx="9.8" ry="6.6" fill="none" stroke="{INK}" '
            f'stroke-width="2.3" transform="rotate(-18 {x} {y})"/>')


def staff(cx, cy, item):
    """A clef-less five-line staff centered on (cx, cy) with one harmonic
    interval of whole notes in it. Seconds are drawn the standard way, upper
    note nudged right; a unison is two heads side by side."""
    x0, bottom = cx - STAFF_W / 2, cy + 2 * SPACE
    out = [f'<line x1="{x0}" y1="{bottom - i * SPACE}" x2="{x0 + STAFF_W}" '
           f'y2="{bottom - i * SPACE}" stroke="{INK}" stroke-width="1.7"/>'
           for i in range(5)]
    lo, hi = item
    nudge = {0: 10.2, 1: 9.4}.get(hi - lo, 0)
    out.append(whole_note(cx - nudge, bottom - lo * SPACE / 2))
    out.append(whole_note(cx + nudge, bottom - hi * SPACE / 2))
    return "".join(out)


# ----------------------------------------------------------------- doodles
# Each doodle is inner markup around a point, in the jar's local coordinates;
# stroke/fill come from the enclosing group.

def bubble(x, y, r):
    return f'<circle cx="{x}" cy="{y}" r="{r}"/>'


def star(x, y, r, points=5):
    pts = []
    for i in range(points * 2):
        a = -math.pi / 2 + i * math.pi / points
        rr = r if i % 2 == 0 else r * 0.45
        pts.append(f"{x + rr * math.cos(a):.1f} {y + rr * math.sin(a):.1f}")
    return f'<polygon points="{" ".join(pts)}"/>'


def sparkle(x, y, r):
    return (f'<path d="M{x} {y - r} Q{x} {y} {x + r} {y} Q{x} {y} {x} {y + r} '
            f'Q{x} {y} {x - r} {y} Q{x} {y} {x} {y - r} Z"/>')


def worm(x, y, s, flip=1):
    """A wiggly worm with its head at the right end."""
    return (f'<path d="M{x - s} {y} q{s * 0.35} {-s * 0.6 * flip} {s * 0.7} 0 '
            f't{s * 0.7} 0 t{s * 0.6} 0" fill="none" stroke-width="7" stroke-linecap="round"/>'
            f'<path d="M{x - s} {y} q{s * 0.35} {-s * 0.6 * flip} {s * 0.7} 0 '
            f't{s * 0.7} 0 t{s * 0.6} 0" fill="none" stroke="#fff" stroke-width="3" stroke-linecap="round"/>'
            f'<circle cx="{x + s * 0.92}" cy="{y - 2.2}" r="1.6" fill="{INK}" stroke="none"/>')


def toadstool(x, y, s, lean=0):
    """A little mushroom standing on (x, y): stem first, then the cap over it."""
    return (f'<path d="M{x - s * 0.22} {y} L{x - s * 0.18 + lean} {y - s * 0.7} L{x + s * 0.18 + lean} {y - s * 0.7} L{x + s * 0.22} {y} Z"/>'
            f'<path d="M{x - s * 0.6 + lean} {y - s * 0.66} C{x - s * 0.62 + lean} {y - s * 1.2} {x + s * 0.62 + lean} {y - s * 1.2} '
            f'{x + s * 0.6 + lean} {y - s * 0.66} Q{x + lean} {y - s * 0.56} {x - s * 0.6 + lean} {y - s * 0.66} Z"/>'
            f'<circle cx="{x - s * 0.22 + lean}" cy="{y - s * 0.9}" r="{s * 0.08}"/>'
            f'<circle cx="{x + s * 0.2 + lean}" cy="{y - s * 0.84}" r="{s * 0.06}"/>')


def fly(x, y, s, rot=0):
    """A tiny fly: oval body, round head, two wings swept back, a dotted trail."""
    return (f'<g transform="rotate({rot} {x} {y})">'
            # Two teardrop wings, points meeting on the body's back, rounded ends out.
            f'<path d="M{x} {y - s * 0.3} Q{x - s * 0.3} {y - s * 1.25} {x - s * 0.95} {y - s * 1.0} '
            f'Q{x - s * 1.05} {y - s * 0.55} {x} {y - s * 0.3} Z"/>'
            f'<path d="M{x} {y - s * 0.3} Q{x + s * 0.4} {y - s * 1.25} {x + s * 1.0} {y - s * 0.95} '
            f'Q{x + s * 1.05} {y - s * 0.5} {x} {y - s * 0.3} Z"/>'
            f'<ellipse cx="{x}" cy="{y}" rx="{s * 0.55}" ry="{s * 0.36}"/>'
            f'<circle cx="{x + s * 0.6}" cy="{y - s * 0.1}" r="{s * 0.22}"/>'
            f'<circle cx="{x + s * 0.66}" cy="{y - s * 0.16}" r="{s * 0.07}" fill="{INK}"/>'
            f'<path d="M{x - s * 0.8} {y + s * 0.3} q-4 4 -8 0 t-8 0" fill="none" stroke-width="1.6" stroke-dasharray="3 3"/></g>')


def leaf(x, y, s, rot=0):
    """A simple leaf with a midrib and a short stem."""
    return (f'<g transform="rotate({rot} {x} {y})">'
            f'<path d="M{x - s} {y} C{x - s * 0.7} {y - s * 0.75} {x + s * 0.3} {y - s * 0.8} {x + s} {y - s * 0.1} '
            f'C{x + s * 0.3} {y + s * 0.75} {x - s * 0.7} {y + s * 0.7} {x - s} {y} Z"/>'
            f'<path d="M{x - s} {y} L{x + s * 0.9} {y - s * 0.08} M{x - s} {y} L{x - s * 1.35} {y + s * 0.1}" fill="none" stroke-width="1.8"/></g>')


def spider(x, y, r):
    legs = "".join(
        f'<path d="M{x + sx * r * 0.6} {y - 2} q{sx * r * 0.9} {dy - 6} {sx * r * 1.7} {dy}" fill="none"/>'
        for sx in (-1, 1) for dy in (-10, -3, 4, 11))
    return (f'<g stroke-width="2">{legs}</g>'
            f'<circle cx="{x}" cy="{y}" r="{r}"/>'
            f'<circle cx="{x}" cy="{y - r * 1.25}" r="{r * 0.55}"/>')


def liquid(y, half, amp=4, waves=3):
    """A wavy fill line across a body `2*half` wide at height y (clipped later)."""
    w = 2 * half / waves
    d = f"M{-half - 10} {y}"
    for i in range(waves + 1):
        x = -half - 10 + i * w
        d += f" q{w / 4} {-amp} {w / 2} 0 t{w / 2} 0"
    return f'<path d="{d}" fill="none"/>'


# ----------------------------------------------------------------- vessels
# Each vessel returns (body path, top markup, inside doodles, staff center y).
# Local coordinates: origin at the bottom center, y up is negative.

def rounded_box(hw, top, bottom=0, r=14):
    return (f"M{-hw + r} {bottom} H{hw - r} Q{hw} {bottom} {hw} {bottom - r} "
            f"V{top + r} Q{hw} {top} {hw - r} {top} H{-hw + r} Q{-hw} {top} {-hw} {top + r} "
            f"V{bottom - r} Q{-hw} {bottom} {-hw + r} {bottom} Z")


def cork(y, hw=15, h=22):
    return (f'<path d="M{-hw} {y} L{-hw - 3} {y - h} Q0 {y - h - 5} {hw + 3} {y - h} L{hw} {y} Z"/>'
            f'<path d="M{-hw * 0.6} {y - h * 0.6} l4 0 M{hw * 0.2} {y - h * 0.35} l5 0" fill="none" stroke-width="1.6"/>')


def tag(x, y, rot, inner):
    """A little parcel tag hanging from a neck, with a doodle on it."""
    return (f'<g transform="translate({x} {y}) rotate({rot})">'
            f'<path d="M-14 -16 h28 l6 7 v30 h-40 v-30 Z"/>'
            f'<circle cx="0" cy="-11" r="2.4"/>{inner}</g>')


def P_round_flask():
    body = ("M-14 -150 L-14 -128 C-55 -118 -70 -92 -70 -62 C-70 -22 -40 0 0 0 "
            "C40 0 70 -22 70 -62 C70 -92 55 -118 14 -128 L14 -150 Z")
    top = cork(-150, 17)
    inside = liquid(-118, 70) + bubble(-46, -26, 5) + bubble(40, -22, 4) + bubble(-30, -126, 3) + bubble(50, -110, 3.5)
    return body, top, inside, -72


def P_erlenmeyer():
    body = ("M-20 -196 L-20 -168 L-86 -18 Q-90 0 -70 0 L70 0 Q90 0 86 -18 L20 -168 L20 -196 Z")
    top = cork(-196, 22)
    inside = liquid(-122, 60, 4, 2) + bubble(-54, -26, 5) + bubble(58, -22, 3.5) + bubble(-14, -146, 3) + bubble(20, -156, 2.4)
    return body, top, inside, -56


def P_apple():
    body = ("M-22 -168 L-22 -124 C-56 -116 -74 -96 -74 -64 C-74 -24 -42 0 0 0 "
            "C42 0 74 -24 74 -64 C74 -96 56 -116 22 -124 L22 -168 Z")
    top = cork(-168, 25) + '<path d="M-28 -168 h56" fill="none"/>'
    inside = liquid(-118, 70, 5, 2) + bubble(-48, -22, 4) + bubble(46, -26, 5) + bubble(-58, -62, 2.6) + bubble(-20, -130, 2.6)
    return body, top, inside, -66


def P_teardrop():
    body = ("M-18 -172 L-18 -150 C-18 -122 -78 -108 -78 -52 C-78 -8 -42 0 0 0 "
            "C42 0 78 -8 78 -52 C78 -108 18 -122 18 -150 L18 -172 Z")
    top = cork(-172, 19) + tag(46, -150, 18, star(0, 6, 9))
    inside = liquid(-120, 70, 4, 2) + bubble(-54, -22, 4.5) + bubble(44, -18, 3.6) + bubble(-32, -130, 2.6) + bubble(30, -136, 3)
    return body, top, inside, -72


def P_tall():
    body = ("M-17 -230 L-17 -170 C-17 -150 -60 -150 -60 -124 L-60 -14 Q-60 0 -46 0 L46 0 "
            "Q60 0 60 -14 L60 -124 C60 -150 17 -150 17 -170 L17 -230 Z")
    top = cork(-230, 18)
    inside = liquid(-140, 60, 4, 2) + bubble(-38, -28, 4.6) + bubble(36, -38, 3.4) + bubble(-34, -128, 2.6) + bubble(8, -196, 2.4) + bubble(-4, -180, 1.8)
    return body, top, inside, -82


def P_gourd():
    body = ("M-16 -172 L-16 -140 C-20 -120 -84 -104 -84 -50 C-84 -10 -46 0 0 0 "
            "C46 0 84 -10 84 -50 C84 -104 20 -120 16 -140 L16 -172 Z")
    top = cork(-172, 18)
    inside = liquid(-114, 76, 5, 3) + bubble(-62, -18, 5) + bubble(56, -16, 4) + bubble(-54, -104, 3) + bubble(30, -128, 2.6)
    return body, top, inside, -62


def P_crystal():
    body = ("M-18 -176 L-18 -158 L-72 -116 L-72 -36 L-40 0 L40 0 L72 -36 L72 -116 L18 -158 L18 -176 Z")
    top = cork(-176, 20)
    inside = (liquid(-128, 70, 4, 2) + bubble(-50, -24, 4) + bubble(48, -28, 3.4) + bubble(-30, -140, 2.4) + bubble(36, -134, 2.8)
              + '<path d="M-72 -36 L-40 -36 L-40 0 M72 -36 L40 -36 L40 0" fill="none" stroke-width="1.6"/>')
    return body, top, inside, -72


def P_jug():
    body = ("M-20 -196 L-20 -160 C-20 -146 -64 -148 -64 -126 L-64 -14 Q-64 0 -50 0 L50 0 "
            "Q64 0 64 -14 L64 -126 C64 -148 20 -146 20 -160 L20 -196 Z")
    top = (cork(-196, 22) + '<path d="M-26 -196 h52" fill="none"/>'
           + '<path d="M62 -124 C96 -126 100 -70 64 -64" fill="none"/>'
           + '<path d="M64 -116 C84 -116 86 -78 64 -74" fill="none"/>')
    inside = liquid(-136, 64, 4, 2) + bubble(-40, -26, 5) + bubble(40, -32, 3.6) + bubble(-26, -152, 2.4) + bubble(14, -146, 3)
    return body, top, inside, -78


def J_mason_eyeballs():
    body = rounded_box(70, -180)
    top = (f'<path d="{rounded_box(76, -202, -180, 6)}"/>'
           '<path d="M-56 -202 C-56 -222 -22 -230 0 -230 C22 -230 56 -222 56 -202" fill="none"/>'
           '<path d="M-6 -230 a6 6 0 1 1 12 0 Z"/>')
    inside = ""
    return body, top, inside, -90


def J_flies():
    body = rounded_box(64, -184, 0, 16)
    top = (f'<path d="{rounded_box(70, -206, -184, 6)}"/>'
           '<path d="M-30 -195 h8 M-10 -195 h8 M10 -195 h8 M30 -195 h8" fill="none" stroke-width="2"/>')
    inside = ""
    return body, top, inside, -92


def J_cloth_leaves():
    body = ("M-70 -140 C-70 -168 -40 -176 0 -176 C40 -176 70 -168 70 -140 L70 -16 Q70 0 54 0 L-54 0 Q-70 0 -70 -16 Z")
    top = ('<path d="M-76 -178 Q-72 -192 -62 -186 Q-54 -200 -44 -190 Q-34 -204 -24 -192 Q-14 -206 -4 -192 '
           'Q6 -206 16 -192 Q26 -204 36 -190 Q46 -200 56 -186 Q66 -192 72 -178 Q74 -168 66 -164 '
           'Q0 -150 -66 -164 Q-78 -168 -76 -178 Z"/>'
           '<path d="M-66 -164 Q0 -150 66 -164" fill="none" stroke-width="1.6"/>'
           '<path d="M62 -160 l16 10 M78 -170 l-16 10 M62 -160 l14 -2" fill="none"/>')
    inside = ""
    return body, top, inside, -84


def J_cork_worms():
    body = ("M-30 -176 L-30 -160 C-64 -156 -70 -132 -70 -110 L-70 -16 Q-70 0 -54 0 L54 0 "
            "Q70 0 70 -16 L70 -110 C70 -132 64 -156 30 -160 L30 -176 Z")
    top = cork(-176, 30, 24) + '<path d="M-30 -176 h60" fill="none"/>'
    inside = ""
    return body, top, inside, -84


def J_bottle_mushrooms():
    body = ("M-16 -236 L-16 -176 C-16 -156 -60 -156 -60 -130 L-60 -14 Q-60 0 -46 0 L46 0 "
            "Q60 0 60 -14 L60 -130 C60 -156 16 -156 16 -176 L16 -236 Z")
    top = cork(-236, 17)
    inside = ""
    return body, top, inside, -84


def J_round_spiders():
    body = ("M-50 -172 C-80 -168 -80 -140 -80 -120 L-80 -40 C-80 -8 -50 0 0 0 C50 0 80 -8 80 -40 "
            "L80 -120 C80 -140 80 -168 50 -172 Z")
    top = (f'<path d="{rounded_box(56, -192, -172, 6)}"/>'
           '<path d="M-50 -186 h100 M-50 -179 h100" fill="none" stroke-width="1.6"/>')
    inside = ""
    return body, top, inside, -86


def J_hex_flowers():
    body = ("M-24 -180 L-24 -168 L-62 -150 L-62 -30 L-40 0 L40 0 L62 -30 L62 -150 L24 -168 L24 -180 Z")
    top = (f'<path d="{rounded_box(30, -196, -180, 5)}"/>'
           '<path d="M-24 -190 h48" fill="none" stroke-width="1.6"/>')
    inside = ""
    return body, top, inside, -86


def J_stars():
    body = rounded_box(66, -172, 0, 20)
    top = (f'<path d="{rounded_box(72, -192, -172, 6)}"/>'
           '<path d="M-16 -192 Q-16 -212 0 -212 Q16 -212 16 -192" fill="none"/>')
    inside = ""
    return body, top, inside, -84


VESSELS = {
    "": [P_gourd, P_erlenmeyer, P_jug, P_apple, P_teardrop, P_round_flask, P_tall, P_crystal],
    "-ingredients": [J_mason_eyeballs, J_flies, J_cloth_leaves, J_bottle_mushrooms,
                     J_cork_worms, J_round_spiders, J_hex_flowers, J_stars],
}


def vessel(i, cx, yb, maker, item, scale):
    body, top, inside, cy = maker()
    return f"""
  <g transform="translate({cx} {yb}) scale({scale})" fill="#fff" stroke="{INK}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round">
    <clipPath id="body{i}"><path d="{body}"/></clipPath>
    <path d="{body}"/>
    <g clip-path="url(#body{i})" stroke-width="2.6">{inside}</g>
    <path d="{body}" fill="none"/>
    {top}
    {staff(0, cy, item)}
  </g>"""


# ----------------------------------------------------------------- the frog

def picture(path, size, x, y, w):
    """One of Kristianna's line drawings (tools/frogs-potions-art/, with the
    outside background made transparent in its -cutout.png), `w` wide with its
    bottom-left corner at (x, y)."""
    data = base64.b64encode(path.read_bytes()).decode()
    h = w * size[1] / size[0]
    return (f'<image x="{x}" y="{y - h}" width="{w}" height="{h}" '
            f'href="data:image/png;base64,{data}"/>')


def wizard_frog(x, y, w):
    return picture(FROG, FROG_SIZE, x, y, w)


def basket(x, y, w):
    """Kristianna's foraging basket: a mushroom, a leaf, a worm, and a fly above."""
    return picture(BASKET, BASKET_SIZE, x, y, w)



def scatter():
    """A few ingredients floating in the band between the two rows of jars
    (the jars themselves stay empty so the intervals get the attention)."""
    # Six of them, bobbing up and down across the band in a loose zigzag.
    items = (worm(120, 472, 22)
             + f'<g transform="rotate(-14 270 512)">{toadstool(270, 530, 32, 2)}</g>'
             + leaf(420, 476, 16, -20) + fly(570, 522, 12, -10) + spider(720, 470, 9)
             + f'<g transform="rotate(18 880 498)">{toadstool(880, 514, 28, -2)}</g>')
    return (f'<g fill="#fff" stroke="{INK}" stroke-width="2.6" stroke-linecap="round" '
            f'stroke-linejoin="round">{items}</g>')


def cauldron(x, y, scale=1.0):
    """A bubbling cauldron standing on (x, y) with a spoon leaning in."""
    return f"""
  <g transform="translate({x} {y}) scale({scale})" fill="#fff" stroke="{INK}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round">
    <path d="M-30 -2 L-40 10 M30 -2 L40 10 M0 0 L0 12" stroke-width="5"/>
    <path d="M-54 -58 C-62 -30 -48 0 0 0 C48 0 62 -30 54 -58 Z"/>
    <path d="M-60 -62 h120 a6 6 0 0 1 0 12 h-120 a6 6 0 0 1 0 -12 Z"/>
    <path d="M-46 -62 q10 -8 20 0 t20 0 t20 0 t20 0 t12 0" fill="none" stroke-width="2.6"/>
    <path d="M22 -62 C32 -80 46 -98 56 -114" stroke-width="9" stroke="{INK}"/>
    <path d="M22 -62 C32 -80 46 -98 56 -114" stroke-width="4" stroke="#fff"/>
    <g stroke-width="2.6">{bubble(-10, -86, 5)}{bubble(8, -104, 3.5)}{bubble(-24, -110, 2.6)}{bubble(14, -84, 3)}</g>
  </g>"""


# ----------------------------------------------------------------- the key

KEY_H = 24 * 1.1 + 14 + 40 * 4 + 8     # the key box's height, so it can sit on the jars' baseline


def key(x, y, w, words, pitch=40, r=13, size=24):
    """The color key: a rounded box with a heading, then one empty circle and
    interval name per row for the student to fill with a color of their own."""
    head = size * 1.1
    h = head + 14 + pitch * len(words) + 8
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="#fff" '
           f'stroke="{INK}" stroke-width="3"/>',
           f'<text x="{x + w / 2}" y="{y + head + 2}" font-size="{head * 0.92}" font-weight="900" '
           f'text-anchor="middle">Pick your color:</text>']
    for i, word in enumerate(words):
        cy = y + head + 20 + pitch * (i + 0.5)
        out.append(f'<circle cx="{x + 30 + r}" cy="{cy}" r="{r}" fill="#fff" '
                   f'stroke="{INK}" stroke-width="2.6"/>')
        out.append(f'<text x="{x + 52 + 2 * r}" y="{cy + size * 0.32}" font-size="{size}" '
                   f'font-weight="900">{word}</text>')
    return "".join(out)


# ----------------------------------------------------------------- the page

def page(spec, makers):
    items = spec["items"]
    jars = "".join(vessel(i, cx, TOP_ROW[1], makers[i], items[i], JAR_SCALE[0])
                   for i, cx in enumerate(TOP_ROW[0]))
    jars += "".join(vessel(4 + i, cx, BOTTOM_ROW[1], makers[4 + i], items[4 + i], JAR_SCALE[1])
                    for i, cx in enumerate(BOTTOM_ROW[0]))
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  @font-face {{ font-family: 'Nunito'; src: url('{FONT.as_uri()}'); font-weight: 200 1000; }}
  @page {{ size: 11in 8.5in; margin: 0; }}
  * {{ margin: 0; padding: 0; }}
  html, body {{ width: 11in; height: 8.5in; background: #fff; overflow: hidden; }}
  svg {{ display: block; width: 11in; height: 8.5in; }}
  text {{ font-family: 'Nunito', sans-serif; fill: {INK}; }}
</style></head><body>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1100 850">
  <rect x="32" y="32" width="1036" height="786" rx="24" fill="none" stroke="{INK}" stroke-width="3"/>
  <text x="550" y="104" font-size="58" font-weight="900" text-anchor="middle">{spec["title"]}</text>
  <text x="550" y="142" font-size="20" font-weight="700" text-anchor="middle">{spec["subtitle"]}</text>
  {jars}
  {key(44, TOP_ROW[1] - KEY_H, 212, spec["key"])}
  {wizard_frog(34, 764, 212)}
  {cauldron(300, 752, 0.8) if spec["cauldron"] else basket(246, 756, 109)}
  {scatter() if spec["scatter"] else ""}
  <text x="550" y="801" font-size="12.5" font-weight="700" text-anchor="middle" fill="#777">Interval Jump  ·  beeskeysapp.com</text>
</svg>
</body></html>"""


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    common = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
              "--virtual-time-budget=3000"]
    for suffix, spec in PAGES.items():
        name = NAME + suffix
        html = OUT / f"{name}.html"
        html.write_text(page(spec, VESSELS[suffix]), encoding="utf-8")
        subprocess.run(common + ["--no-pdf-header-footer",
                                 f"--print-to-pdf={OUT / (name + '.pdf')}", html.as_uri()],
                       check=True, capture_output=True)
        subprocess.run(common + ["--window-size=1056,816", "--force-device-scale-factor=2",
                                 f"--screenshot={OUT / (name + '-preview.png')}", html.as_uri()],
                       check=True, capture_output=True)
        html.unlink()
        print(OUT / f"{name}.pdf")
