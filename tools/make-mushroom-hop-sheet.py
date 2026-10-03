#!/usr/bin/env python3
"""Frog's Mushroom Hop: a color-by-jump worksheet for Interval Jump, by Kristianna Callahan.

A river scene: the Interval Jump stream outlined across the middle, four
smaller mushrooms on the far bank, three and the frog on the near bank. Each
mushroom carries two notes on a clef-less staff (distance, not pitch, like
Frog's First Jumps). The student picks a color for each of the three jumps in
the key, then colors each mushroom to match. Pure black line art, so it
prints on any printer.

The frog is the Interval Jump seated frog (tools/sound-garden-art/frog-seated.svg)
turned into a coloring outline: highlights dropped, fills white, strokes black.

    python3 tools/make-mushroom-hop-sheet.py

Two keys: repeat/step/skip and unison/2nd/3rd.

Output: output/mushroom-hop/interval-jump-frogs-mushroom-hop.pdf and
-intervals.pdf (US Letter landscape, vector), each with a -preview.png beside it.
"""

import math
import re
import subprocess
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "mushroom-hop"
NAME = "interval-jump-frogs-mushroom-hop"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT = ROOT / "tools" / "poster" / "fonts" / "Nunito[wght].ttf"
FROG = ROOT / "tools" / "sound-garden-art" / "frog-seated.svg"

INK = "#1c1c1c"

# (from, to) in staff positions, 0 = bottom line … 8 = top line: the far bank's
# four, then the near bank's three. Up and down, on lines and in spaces, three
# skips, two steps, two repeats. Kristianna set the first (E-F), third (high F
# repeat) and fifth (E-G) by their treble-clef names.
ITEMS = [(0, 1), (5, 3), (8, 8), (3, 5),
         (0, 2), (6, 5), (3, 3)]

# Two labelings of the same three jumps: the game's words, and interval names.
KEYS = {"": ["repeat", "step", "skip"], "-intervals": ["unison", "2nd", "3rd"]}
KEY = KEYS[""]
# Lines under the key's words; empty, since the subtitle already says it.
CAPTION = []

# Page units are 1/100 in: 1100 x 850.
SPACE = 15                 # staff line spacing
STAFF_W = 150


def coloring_frog():
    """The seated frog as a coloring outline, returned as inner SVG markup
    (viewBox 0 0 520 520)."""
    ns = "http://www.w3.org/2000/svg"
    ET.register_namespace("", ns)
    root = ET.parse(FROG).getroot()
    drop = re.compile(r"highlight|shadow|band|glint-.*-small")

    def clean(parent):
        for el in list(parent):
            eid = el.get("id", "")
            tag = el.tag.split("}")[1]
            if tag in ("defs", "title", "desc") or drop.search(eid) \
                    or "display:none" in el.get("style", ""):
                parent.remove(el)
                continue
            if eid.startswith(("pupil", "nostril")):
                el.set("fill", INK)
            elif el.get("fill", "none") != "none":
                el.set("fill", "#fff")
            if el.get("stroke"):
                el.set("stroke", INK)
            el.attrib.pop("opacity", None)
            clean(el)

    clean(root)
    return "".join(ET.tostring(el, encoding="unicode") for el in root)


def note(x, y, up):
    """A quarter note; stem up on the right, down on the left."""
    head = (f'<ellipse cx="{x}" cy="{y}" rx="9.6" ry="6.9" fill="{INK}" '
            f'transform="rotate(-22 {x} {y})"/>')
    sx, sy = (x + 8.4, y - 50) if up else (x - 8.4, y + 50)
    return head + (f'<line x1="{sx}" y1="{y}" x2="{sx}" y2="{sy}" '
                   f'stroke="{INK}" stroke-width="2.6"/>')


def staff(cx, bottom, item):
    x0 = cx - STAFF_W / 2
    out = [f'<line x1="{x0}" y1="{bottom - i * SPACE}" x2="{x0 + STAFF_W}" '
           f'y2="{bottom - i * SPACE}" stroke="{INK}" stroke-width="1.8"/>'
           for i in range(5)]
    for fx, pos in zip((0.30, 0.70), item):
        out.append(note(x0 + STAFF_W * fx, bottom - pos * SPACE / 2, pos < 4))
    return "".join(out)


# Where the spots sit on each cap (dx, dy from the cap's bottom center, radius),
# kept inside the rim and clear of the staff.
SPOTS = [
    [(-84, -19, 10), (30, -130, 11), (-55, -116, 9)],
    [(-32, -130, 11), (84, -19, 10), (56, -115, 9)],
    [(-84, -20, 10), (-4, -134, 11), (60, -112, 9)],
    [(40, -127, 11), (-56, -115, 9), (84, -19, 10)],
    [(-30, -130, 11), (84, -20, 10), (52, -117, 9)],
    [(6, -134, 11), (-60, -112, 9), (-84, -19, 10)],
    [(-36, -128, 11), (84, -20, 10), (50, -118, 9)],
]


def mushroom(i, cx, yb, scale=1.0):
    """Mushroom number `i` (its notes and spots) with its cap's bottom center at
    (cx, yb), drawn `scale` times the standard size."""
    cap = (f"M{cx - 108} {yb} C{cx - 114} {yb - 96} {cx - 62} {yb - 152} {cx} {yb - 152} "
           f"C{cx + 62} {yb - 152} {cx + 114} {yb - 96} {cx + 108} {yb} "
           f"Q{cx} {yb + 16} {cx - 108} {yb} Z")
    stem = (f"M{cx - 27} {yb} C{cx - 29} {yb + 40} {cx - 38} {yb + 62} {cx - 42} {yb + 80} "
            f"Q{cx} {yb + 92} {cx + 42} {yb + 80} "
            f"C{cx + 38} {yb + 62} {cx + 29} {yb + 40} {cx + 27} {yb} Z")
    gy = yb + 82
    spots = "".join(f'<circle cx="{cx + dx}" cy="{yb + dy}" r="{r}"/>'
                    for dx, dy, r in SPOTS[i])
    return f"""
  <g transform="translate({cx} {yb}) scale({scale}) translate({-cx} {-yb})">
  <g fill="#fff" stroke="{INK}" stroke-width="3.6" stroke-linecap="round" stroke-linejoin="round">
    <path d="{grass(cx + (-62 if i % 2 else 62), gy)}" fill="none" stroke-width="3"/>
    <path d="{stem}"/>
    <path d="{cap}"/>
    <clipPath id="cap{i}"><path d="{cap}"/></clipPath>
    <g clip-path="url(#cap{i})" stroke-width="3">{spots}</g>
    <path d="{cap}" fill="none"/>
  </g>
  {staff(cx, yb - 34, ITEMS[i])}
  </g>"""


def grass(gx, gy):
    """Path data for a three-blade tuft standing on (gx, gy)."""
    return (f"M{gx - 12} {gy} Q{gx - 13} {gy - 14} {gx - 19} {gy - 22} "
            f"M{gx} {gy - 1} Q{gx + 1} {gy - 20} {gx - 2} {gy - 31} "
            f"M{gx + 12} {gy} Q{gx + 14} {gy - 13} {gx + 21} {gy - 20}")


def key(x, y, w, pitch, r, size):
    """The color key: a rounded box at (x, y), one empty circle and word per row
    for the student to fill with a color of their own, and Kristianna's caption."""
    cap = size * 0.5
    h = pitch * len(KEY) + r + cap * (1.2 * len(CAPTION) + 0.8)
    out = [f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="20" fill="#fff" '
           f'stroke="{INK}" stroke-width="3"/>']
    for i, word in enumerate(KEY):
        cy = y + r / 2 + pitch * (i + 0.5)
        out.append(f'<circle cx="{x + 26 + r}" cy="{cy}" r="{r}" fill="#fff" '
                   f'stroke="{INK}" stroke-width="2.6"/>')
        out.append(f'<text x="{x + 48 + 2 * r}" y="{cy + size * 0.32}" font-size="{size}" '
                   f'font-weight="900">{word}</text>')
    for j, line in enumerate(reversed(CAPTION)):
        out.append(f'<text x="{x + w / 2}" y="{y + h - cap * (0.95 + 1.2 * j)}" font-size="{cap}" '
                   f'font-weight="700" text-anchor="middle" fill="#555">{line}</text>')
    return "".join(out)


def frog(x, y, size):
    return (f'<svg x="{x}" y="{y}" width="{size}" height="{size}" '
            f'viewBox="0 0 520 520">{coloring_frog()}</svg>')


# The river scene: far bank on top, the stream across the middle, near bank
# below. The far bank's four mushrooms are drawn smaller, as if further away.
FAR_SHORE, NEAR_SHORE = 460, 588
FAR_ROW, NEAR_ROW = ([234, 454, 674, 894], 362), ([408, 654, 900], 668)
FAR_SCALE = 0.82


def shoreline(base, phase):
    """A wavy bank edge across the page, the game's two-sine wobble."""
    pts = [(x, base + 7 * math.sin(x / 48 + phase) + 3.5 * math.sin(x / 19.5 + 2 * phase))
           for x in range(20, 1085, 6)]
    return "M" + " L".join(f"{x} {y:.1f}" for x, y in pts)


def cattails(x, y):
    """Three cattails standing on (x, y): straight stalks, each head sitting on
    its own stalk at the stalk's angle, with the stalk's tip poking out above."""
    out = []
    for dx, h, lean in ((-24, 118, -14), (0, 150, 2), (26, 100, 16)):
        bx, tx, ty = x + dx * 0.4, x + dx + lean, y - h
        ang = math.degrees(math.atan2(tx - bx, h))
        out.append(f'<line x1="{bx}" y1="{y}" x2="{tx}" y2="{ty}"/>')
        # Head centered on the stalk, 28 units below its tip.
        hx, hy = tx - 28 * math.sin(math.radians(ang)), ty + 28 * math.cos(math.radians(ang))
        out.append(f'<rect x="{hx - 6.5}" y="{hy - 20}" width="13" height="40" rx="6.5" '
                   f'transform="rotate({ang:.1f} {hx} {hy})"/>')
    out.append(f'<path d="M{x - 8} {y} Q{x - 40} {y - 40} {x - 52} {y - 74} Q{x - 26} {y - 44} {x - 2} {y} '
               f'M{x + 8} {y} Q{x + 44} {y - 34} {x + 60} {y - 62} Q{x + 30} {y - 40} {x + 2} {y}"/>')
    return (f'<g fill="#fff" stroke="{INK}" stroke-width="3" stroke-linecap="round" '
            f'stroke-linejoin="round">{"".join(out)}</g>')


def river_body():
    ripples = "".join(f'<path d="M{x} {y} q11 -7 22 0 t22 0"/>' for x, y in
                      [(96, 498), (176, 548), (508, 552), (606, 482), (776, 500),
                       (1004, 520), (330, 484)])
    far = "".join(mushroom(c, cx, FAR_ROW[1], scale=FAR_SCALE)
                  for c, cx in enumerate(FAR_ROW[0]))
    near = "".join(mushroom(4 + c, cx, NEAR_ROW[1])
                   for c, cx in enumerate(NEAR_ROW[0]))
    return f"""
  <text x="420" y="116" font-size="60" font-weight="900" text-anchor="middle">{TITLE}</text>
  <text x="420" y="158" font-size="20.5" font-weight="700" text-anchor="middle">{SUBTITLE}</text>
  {key(826, 56, 214, 42, 14, 26)}

  <clipPath id="frame"><rect x="33.5" y="33.5" width="1033" height="783" rx="22.5"/></clipPath>
  <g clip-path="url(#frame)" fill="none" stroke="{INK}" stroke-width="3.4" stroke-linecap="round" stroke-linejoin="round">
    <path d="{shoreline(FAR_SHORE, 0.6)}"/>
    <path d="{shoreline(NEAR_SHORE, 2.1)}"/>
    <g stroke-width="2.6">{ripples}</g>
  </g>
  <g fill="#fff" stroke="{INK}" stroke-width="3" stroke-linejoin="round">
    <path d="M236 500 h66 a9 15 0 0 1 0 30 h-66 a9 15 0 0 1 0 -30 Z"/>
    <ellipse cx="302" cy="515" rx="9" ry="15"/>
    <path d="M250 509 h30 M262 521 h26" fill="none" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M556 520 L530 513 A28 11 0 1 0 546 510 Z"/>
  </g>
  {cattails(90, 446)}
  {far}
  {near}
  <path d="{grass(276, 752)} {grass(1022, 742)}" fill="none" stroke="{INK}" stroke-width="3" stroke-linecap="round"/>
  {frog(64, 574, 190)}"""


TITLE = "Frog&#8217;s Mushroom Hop"
SUBTITLE = "Choose a color for each interval, and color the mushrooms to match!"


def page():
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
  {river_body()}
  <text x="550" y="801" font-size="12.5" font-weight="700" text-anchor="middle" fill="#777">Interval Jump  ·  beeskeysapp.com</text>
</svg>
</body></html>"""


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    common = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
              "--virtual-time-budget=3000"]
    for labels, words in KEYS.items():
        KEY = words
        name = NAME + labels
        html = OUT / f"{name}.html"
        html.write_text(page(), encoding="utf-8")
        subprocess.run(common + ["--no-pdf-header-footer",
                                 f"--print-to-pdf={OUT / (name + '.pdf')}", html.as_uri()],
                       check=True, capture_output=True)
        subprocess.run(common + ["--window-size=1056,816", "--force-device-scale-factor=2",
                                 f"--screenshot={OUT / (name + '-preview.png')}", html.as_uri()],
                       check=True, capture_output=True)
        html.unlink()
        print(OUT / f"{name}.pdf")
