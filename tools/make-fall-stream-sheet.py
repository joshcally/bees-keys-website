#!/usr/bin/env python3
"""Frog's Autumn Journey (first called Frog's Fall Adventure, then Frog's Autumn Hop): a cross-the-stream interval worksheet for Interval
Jump, by Kristianna Callahan.

Eleven stepping stones wind down an autumn stream in an S. Stone 1
carry a note; the arrows between stones say repeat / step up / skip down and
so on, and the student draws the missing notes. Staves are clef-less (distance,
not pitch), like every other frog sheet. The scene is Kristianna's ChatGPT
painting (tools/fall-stream-art/autumn-river.png, 3:2, cover-fit cropped to
the page); the frog is the Interval Jump app frog.

    python3 tools/make-fall-stream-sheet.py                   # full color, repeat/step/skip
    python3 tools/make-fall-stream-sheet.py --bw              # printer-friendly line art
    python3 tools/make-fall-stream-sheet.py --intervals       # 2nd/3rd/4th/5th labeling
    python3 tools/make-fall-stream-sheet.py --intervals --bw

Output: output/fall-stream/interval-jump-frogs-fall-stream.pdf (US Letter
landscape) plus a -preview.png beside it.
"""

import base64
import io
import subprocess
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "output" / "fall-stream"
NAME = "interval-jump-frogs-fall-stream"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
FONT = ROOT / "tools" / "poster" / "fonts" / "Nunito[wght].ttf"
SCENE = ROOT / "tools" / "fall-stream-art" / "autumn-river-clean.png"   # her painting, the leaf under stone 10 painted out
FROG = Path.home() / "Repos" / "IntervalJump" / "printables" / "art" / "frog-happy.png"
STONE_PNG = ROOT / "tools" / "fall-stream-art" / "stone-cutout.png"   # her ChatGPT stone, halo removed
SIGN_PNG = ROOT / "tools" / "fall-stream-art" / "mushroom-sign-cutout.png"   # her blank sign with mushrooms, 1163x991
MUSHROOMS = {c: ROOT / "tools" / "fall-stream-art" / f"mushroom-{c}.png" for c in ("red", "orange", "yellow")}   # her wide-cap trio
MUSHROOM_SIZE = {"red": (680, 628), "orange": (653, 634), "yellow": (687, 623)}

import sys
BW = "--bw" in sys.argv       # printer-friendly twin: white page, line-art stream, outlined art
INTERVALS = "--intervals" in sys.argv   # second labeling: 2nd/3rd/4th/5th up and down instead of repeat/step/skip

INK = "#000" if BW else "#2a2118"            # ink for text and staff lines
STONE = "#efe3c8"          # stone fill
STONE_EDGE = "#6b5a3c"     # stone outline
BADGE = "#7a4a1e"          # number badge
LABEL_BG = "#fff" if BW else "#fdf3d6"       # cream pills, like the reference
LABEL_INK = "#000" if BW else "#6b3f1d"
ARROW = "#000" if BW else "#6b3f1d"
ARROW_HALO = "#fff" if BW else "#fdf3d6"
PANEL = "#fff" if BW else "#fdf0d0"

TITLE = "Frog&#8217;s Autumn Journey"
SUBTITLE = "Help Frog cross the stream! Follow each arrow and draw the missing notes."

# Page units are 1/100 in: 1100 x 850.
SPACE = 10                 # staff line spacing
STAFF_W = 96
STONE_W = 150              # her stone drawing, 1082x799, scaled to this width
STONE_H = round(STONE_W * 799 / 1082)

# Stone centers (x, y of the stone's middle) in path order, 4 - 3 - 3 along the
# three reaches of the stream. Then the arrow labels between them.
# (x, y) of each stone's BOTTOM edge, in path order, 4 - 3 - 3 along the three
# reaches of the stream. Every bottom sits inside the water, about 8 units
# above the near bank (Kristianna: "make sure the bottom of the stone is in
# the river"); the tall stone then rises over the far bank, as in her reference.
# Stone 7 sits IN the left bend, between the middle and bottom rows (where
# the stream turns); stone 6 is midway between 5 and 7, and the bottom row
# starts right of stone 7.
STONE_FEET = [(255, 452), (518, 439), (780, 440), (975, 520),
              (800, 592), (515, 606), (268, 630), (104, 722),
              (325, 760), (565, 762), (835, 768)]
STONES = [(x, y - STONE_H / 2) for x, y in STONE_FEET]   # stone centers
# Ten moves, two of each; from G they run G A C C B G E E F A G and end back on G.
MOVES = ["Step Up", "Skip Up", "Repeat", "Step Down", "Skip Down", "Skip Down",
         "Repeat", "Step Up", "Skip Up", "Step Down"]
START_POS = 2              # 0 = bottom line … 8 = top line
DELTA = {"Repeat": 0, "Step Up": 1, "Step Down": -1, "Skip Up": 2, "Skip Down": -2}
if INTERVALS:
    # From G: G C E A B F D A G A F, ending on F (first space). Three 2nds,
    # three 3rds, two 4ths, two 5ths; never leaves the staff.
    MOVES = ["4th Up", "3rd Up", "5th Down", "2nd Up", "5th Up", "3rd Down",
             "4th Down", "2nd Down", "2nd Up", "3rd Down"]
    DELTA = {"2nd Up": 1, "2nd Down": -1, "3rd Up": 2, "3rd Down": -2,
             "4th Up": 3, "4th Down": -3, "5th Up": 4, "5th Down": -4}


def positions():
    pos = [START_POS]
    for m in MOVES:
        pos.append(pos[-1] + DELTA[m])
    return pos


# ----------------------------------------------------------------- pictures

def scene_data_uri():
    """The painting cover-fit cropped to the page's 11:8.5 and re-encoded as a
    JPEG so the PDF stays a sensible size."""
    im = Image.open(SCENE).convert("RGB")
    w, h = im.size
    cw = round(h * 1100 / 850)
    x0 = (w - cw) // 2
    im = im.crop((x0, 0, x0 + cw, h)).resize((2200, 1700), Image.LANCZOS)
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=90)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def line_art(path):
    """A colored cartoon cutout turned into black outlines on white. The dark
    outline strokes go black, everything else inside the cutout goes white
    (so a mushroom's spots vanish and the cap is open for coloring). The ink
    is a soft ramp over the luminance rather than a hard cutoff, and the
    whole thing is done at 2x then downsampled, so the edges stay smooth in
    print (Kristianna: the outlines looked jagged)."""
    import numpy as np
    from PIL import ImageFilter
    im = Image.open(path).convert("RGBA")
    im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
    a = np.asarray(im).astype(float)
    alpha = a[..., 3] / 255
    lum = a[..., :3].mean(axis=2)
    ink = np.clip((92 - lum) / 28, 0, 1)              # 1 at lum<=64 (outline), 0 at lum>=92 (shaded color stays white)
    ink = np.asarray(Image.fromarray((ink * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.0))) / 255
    out = np.zeros(a.shape, dtype=np.uint8)
    out[..., :3] = (255 * (1 - ink))[..., None].astype(np.uint8)
    out[..., 3] = (alpha * 255).astype(np.uint8)
    res = Image.fromarray(out)
    return res.resize((im.width // 2, im.height // 2), Image.LANCZOS)


def image_uri(path):
    if not BW:
        return "data:image/png;base64," + base64.b64encode(path.read_bytes()).decode()
    buf = io.BytesIO()
    line_art(path).save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def picture(path, x, y, w):
    im = Image.open(path)
    h = w * im.size[1] / im.size[0]
    return (f'<image x="{x}" y="{y - h}" width="{w}" height="{h}" href="{image_uri(path)}"/>')


ROCK_BOX = (930, 668, 170, 90)        # page box (x, y, w, h) that holds the right-bank river rock


def rock_cutout_uri():
    """The painted rock under the Finish sign, cut out of the painting (its
    tan fill plus dark outline) so it can be drawn OVER the sign post and the
    post looks like it stands behind the rock (Kristianna: "crop the sign so
    it matches the rock")."""
    import numpy as np
    from PIL import ImageFilter, ImageDraw
    im = Image.open(SCENE).convert("RGB")
    w, h = im.size
    cw = round(h * 1100 / 850)
    x0 = (w - cw) // 2
    bx, by, bw, bh = ROCK_BOX
    X0, Y0 = x0 + round(bx * cw / 1100), round(by * h / 850)
    X1, Y1 = x0 + round((bx + bw) * cw / 1100), round((by + bh) * h / 850)
    crop = im.crop((X0, Y0, X1, Y1))
    a = np.asarray(crop).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    tan = (r > 150) & (b > 100) & (r > b + 40) & (g > b + 15) & (abs(r - g) < 60)   # the rock's tan (grass has b < 80)
    m = Image.fromarray((tan * 255).astype(np.uint8))
    m = m.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(5))
    # keep only the tan blob under the box's middle, then grow it to take in
    # the rock's dark outline (about 6 px thick at this scale)
    seed = (round(m.width * 0.5), round(m.height * 0.55))
    flood = m.copy(); ImageDraw.floodfill(flood, seed, 128)
    blob = Image.fromarray(((np.asarray(flood) == 128) * 255).astype(np.uint8))
    mask = np.asarray(blob.filter(ImageFilter.MaxFilter(15))) > 0
    out = crop.convert("RGBA")
    out.putalpha(Image.fromarray((mask * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.8)))
    buf = io.BytesIO(); out.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def rock_cutout():
    bx, by, bw, bh = ROCK_BOX
    return f'<image x="{bx}" y="{by}" width="{bw}" height="{bh}" href="{rock_cutout_uri()}"/>'


def stream_outline_uri():
    """The stream's two shorelines as black line art, traced from the blue
    water in the painting (same cover-fit crop as the scene), on transparency.
    The water mask is Gaussian-smoothed (not box-closed) so the shoreline is
    a smooth curve, and the ring is built from soft masks so its edges are
    anti-aliased."""
    import numpy as np
    from PIL import ImageFilter
    im = Image.open(SCENE).convert("RGB")
    w, h = im.size
    cw = round(h * 1100 / 850)
    x0 = (w - cw) // 2
    im = im.crop((x0, 0, x0 + cw, h))
    a = np.asarray(im).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    water = (b > 140) & (b > r + 30) & (b > g + 5)
    water[: int(h * 300 / 850), :] = False            # the sky is blue too
    S = 2
    m = Image.fromarray((water * 255).astype(np.uint8)).resize((cw * S, h * S), Image.LANCZOS)
    # smooth the mask: blur wide enough to swallow the highlight streaks and
    # the painting's wobble, then re-threshold to a clean shape
    m = m.filter(ImageFilter.GaussianBlur(7)).point(lambda v: 255 if v > 118 else 0)
    m = m.filter(ImageFilter.GaussianBlur(5)).point(lambda v: 255 if v > 127 else 0)
    pad = 32
    arr = np.pad(np.asarray(m) > 0, pad, mode="edge")
    outer = Image.fromarray((arr * 255).astype(np.uint8))
    inner = outer.filter(ImageFilter.MinFilter(19))
    # soft edges on both before subtracting, so the ring is anti-aliased
    outer_s = np.asarray(outer.filter(ImageFilter.GaussianBlur(1.6))).astype(float)
    inner_s = np.asarray(inner.filter(ImageFilter.GaussianBlur(1.6))).astype(float)
    ring = np.clip(outer_s - inner_s, 0, 255)[pad:-pad, pad:-pad]
    out = np.zeros(ring.shape + (4,), dtype=np.uint8)
    out[..., 3] = ring.astype(np.uint8)
    res = Image.fromarray(out)
    buf = io.BytesIO()
    res.save(buf, "PNG", optimize=True)
    return "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


# ----------------------------------------------------------------- notation

def note(x, y, up):
    head = (f'<ellipse cx="{x}" cy="{y}" rx="6.6" ry="4.7" fill="{INK}" '
            f'transform="rotate(-22 {x} {y})"/>')
    sx, sy = (x + 5.8, y - 32) if up else (x - 5.8, y + 32)
    return head + (f'<line x1="{sx}" y1="{y}" x2="{sx}" y2="{sy}" '
                   f'stroke="{INK}" stroke-width="2.1"/>')


def staff(cx, cy, pos=None):
    """A clef-less five-line staff centered on (cx, cy), with one quarter note
    at staff position `pos` if given."""
    x0, bottom = cx - STAFF_W / 2, cy + 2 * SPACE
    out = [f'<line x1="{x0}" y1="{bottom - i * SPACE}" x2="{x0 + STAFF_W}" '
           f'y2="{bottom - i * SPACE}" stroke="{INK}" stroke-width="1.4"/>'
           for i in range(5)]
    if pos is not None:
        out.append(note(cx, bottom - pos * SPACE / 2, pos < 4))
    return "".join(out)


# ----------------------------------------------------------------- stones

def stone(i, cx, cy, pos):
    """Stepping stone `i` centered at (cx, cy): Kristianna's stone drawing
    (tools/fall-stream-art/stone.png, cut out of its halo) with a clef-less
    staff in its wide lower half. No number: the arrows give the order."""
    w, h = STONE_W, STONE_H
    return f"""
  <g>
    {"" if BW else f'<ellipse cx="{cx + 2}" cy="{cy + h / 2 - 4}" rx="{w / 2 - 2}" ry="12" fill="rgba(0,0,0,0.22)"/>'}
    {picture(STONE_PNG, cx - w / 2, cy + h / 2, w)}
    {staff(cx, cy + 10, pos)}
  </g>"""


def label(x, y, text):
    """A cream speech-bubble pill with the move's name in brown, centered at
    (x, y); two-word moves stack on two lines like the reference."""
    words = text.split()
    size = 22
    if len(words) == 2:
        w, h = 98, 64
        body = (f'<text x="{x}" y="{y - 4}" font-size="{size}" font-weight="900" text-anchor="middle" fill="{LABEL_INK}">{words[0]}</text>'
                f'<text x="{x}" y="{y + 20}" font-size="{size}" font-weight="900" text-anchor="middle" fill="{LABEL_INK}">{words[1]}</text>')
    else:
        w, h = 28 + len(text) * 13.6, 40
        body = f'<text x="{x}" y="{y + 8}" font-size="{size}" font-weight="900" text-anchor="middle" fill="{LABEL_INK}">{text}</text>'
    return (f'<rect x="{x - w / 2}" y="{y - h / 2}" width="{w}" height="{h}" rx="{h / 2}" '
            f'fill="{LABEL_BG}" stroke="{LABEL_INK}" stroke-width="2.4"/>' + body)


def arrow(path_d):
    """A chunky brown arrow with a cream outline, drawn as a halo stroke under
    the brown one (each with its own head so the head is outlined too)."""
    return (f'<path d="{path_d}" fill="none" stroke="{ARROW_HALO}" stroke-width="11" '
            f'stroke-linecap="round" marker-end="url(#headhalo)"/>'
            f'<path d="{path_d}" fill="none" stroke="{ARROW}" stroke-width="5.5" '
            f'stroke-linecap="round" marker-end="url(#head)"/>')


# How each hop is drawn, by index of the hop (stone i to stone i+1):
#   "reach"   straight arrow through the water, label above the middle
#   "right"   loop out to the right and back into the next stone's side (4 to 5)
#   "over"    short arc over the first stone's shoulder (3 to 4)
#   "diag"    diagonal down-left, label on the arrow (7 to 8)
#   "bend"    short hop down-right into the bottom row (8 to 9)
ROUTES = ["reach", "reach", "diagr", "right", "reach", "reach", "diag", "bend", "reach", "reach"]


def links():
    """Arrows between consecutive stones and the move labels that sit on them.
    Returns (arrows, labels) so the arrows can go under the stones and the
    labels on top."""
    arrows, labels = [], []
    hw = STONE_W / 2
    for i, m in enumerate(MOVES):
        (x1, y1), (x2, y2) = STONES[i], STONES[i + 1]
        kind = ROUTES[i]
        d = 1 if x2 > x1 else -1
        if kind == "reach":
            ya = (y1 + y2) / 2 + 16
            arrows.append(arrow(f"M{x1 + d * (hw - 6)} {ya} Q{(x1 + x2) / 2} {ya + 10} {x2 - d * (hw + 14)} {ya}"))
            labels.append(label((x1 + x2) / 2, ya - 40, m))
        elif kind == "over":
            sx, sy = x1 + hw - 22, y1 - 6
            ex, ey = x2 - hw - 10, y2 - STONE_H / 2 + 14
            arrows.append(arrow(f"M{sx} {sy} Q{(sx + ex) / 2 + 12} {(sy + ey) / 2 - 16} {ex} {ey}"))
            labels.append(label(ex + 18, sy - 30, m))
        elif kind == "diagr":                          # diagonal down-right (3 to 4)
            sx, sy = x1 + hw - 30, y1 + 36
            ex, ey = x2 - hw + 34, y2 - 48
            arrows.append(arrow(f"M{sx} {sy} Q{(sx + ex) / 2 + 24} {(sy + ey) / 2 - 24} {ex} {ey}"))
            labels.append(label((sx + ex) / 2 + 40, (sy + ey) / 2 - 46, m))
        elif kind == "right":
            arrows.append(arrow(f"M{x1 - 26} {y1 + 52} Q{x1 - 40} {y2 + 24} {x2 + hw + 6} {y2 + 10}"))
            labels.append(label(x1 - 40, y2 + 30, m))
        elif kind == "diag":                           # down-left into the bend (8 to 9)
            sx, sy = x1 - hw + 20, y1 + 10
            ex, ey = x2 + 16, y2 - STONE_H / 2 - 14
            arrows.append(arrow(f"M{sx} {sy} Q{sx - 40} {(sy + ey) / 2 - 10} {ex} {ey}"))
            labels.append(label(sx - 60, sy - 36, m))
        elif kind == "bend":
            sx, sy = x1 + hw - 6, y1 + 4
            ex, ey = x2 - hw - 10, y2 - 8
            arrows.append(arrow(f"M{sx} {sy} Q{(sx + ex) / 2 + 10} {(sy + ey) / 2 + 16} {ex} {ey}"))
            # label UNDER this arrow, so it can't be read as belonging to the hop above (Kristianna, Nov 9)
            labels.append(label((sx + ex) / 2 - 14, (sy + ey) / 2 + 56, m))
    return "".join(arrows), "".join(labels)


# ----------------------------------------------------------------- props

def sign(x, y, text, w=118, lean=-4, size=24):
    """A wooden sign on a post, the post's foot at (x, y)."""
    return f"""
  <g transform="translate({x} {y}) rotate({lean})" stroke-linejoin="round">
    <rect x="-6" y="-56" width="12" height="56" fill="{'#fff' if BW else '#8a5a2b'}" stroke="{'#000' if BW else STONE_EDGE}" stroke-width="2.5"/>
    <rect x="{-w / 2}" y="-96" width="{w}" height="46" rx="8" fill="{'#fff' if BW else '#f3dfae'}" stroke="{'#000' if BW else STONE_EDGE}" stroke-width="3"/>
    <text x="0" y="-64" font-size="{size}" font-weight="900" text-anchor="middle" fill="{'#000' if BW else BADGE}">{text}</text>
  </g>"""


# The finish: three mushrooms, each with a clef-less staff and one note on its
# cap. One carries Frog's last note (the answer to the path); the other two are
# a step above and below it. (color, foot x, foot y, width, staff position offset
# from the answer). Two stand where the sign was, one on the far side of the water.
# The three choices sit in a row inside one cream sign panel in the bottom-right
# corner (Kristianna's Nov 8 mock-up), under the question.
CHOICE_BOX = (664, 632, 404, 204)      # x, apex y, w, h (an arched banner, flat bottom)
# (color, foot x, foot y, width, offset from the answer). The answer is the
# yellow mushroom on the repeat/step/skip sheet and the orange one on the
# intervals sheet, so the two sheets don't share an answer.
if INTERVALS:
    MUSHROOMS_AT = [("red", 744, 828, 118, -1), ("orange", 866, 828, 118, 0), ("yellow", 988, 828, 118, +1)]
else:
    MUSHROOMS_AT = [("red", 744, 828, 118, +1), ("orange", 866, 828, 118, -1), ("yellow", 988, 828, 118, 0)]


def mushroom(color, x, y, w, pos, k=1.0):
    """One of Kristianna's mushrooms standing on (x, y), `w` wide, with a
    `k`-scale clef-less staff and one quarter note on a cream panel across
    the middle of its cap (the panel reads as one more spot)."""
    iw, ih = MUSHROOM_SIZE[color]
    h = w * ih / iw
    cx, cy = x, y - h * 0.62
    # a short staff, full height (same line spacing as the stones, Kristianna:
    # "the sides of the notes can be trimmed off, but not the top/bottom"),
    # just wide enough for the note, on a snug cream panel
    sw, sh = 46 * k, 4 * SPACE * k
    panel = (f'<rect x="{cx - sw / 2 - 5}" y="{cy - sh / 2 - 5}" width="{sw + 10}" height="{sh + 10}" '
             f'rx="7" fill="{PANEL}"/>')
    full = STAFF_W * k
    staff_svg = (f'<g transform="translate({cx} {cy}) scale({k}) translate({-cx} {-cy})">{staff(cx, cy, pos)}</g>'
                 .replace(f'x1="{cx - STAFF_W / 2}"', f'x1="{cx - sw / 2 / k}"')
                 .replace(f'x2="{cx + STAFF_W / 2}"', f'x2="{cx + sw / 2 / k}"'))
    return picture(MUSHROOMS[color], x - w / 2, y, w) + panel + staff_svg


def mushroom_patch(answer):
    bx, by, bw, bh = CHOICE_BOX
    x0, x1, yb, r = bx, bx + bw, by + bh, 26
    ys = by + 72                                   # shoulder height; the dome rises to `by` at the middle
    cy = (by - 0.25 * ys) / 0.75                   # cubic control height that puts the apex at `by`
    shape = (f"M{x0} {yb - r} L{x0} {ys} C{x0 + 40} {cy} {x1 - 40} {cy} {x1} {ys} L{x1} {yb - r} "
             f"A{r} {r} 0 0 1 {x1 - r} {yb} L{x0 + r} {yb} A{r} {r} 0 0 1 {x0} {yb - r} Z")
    box = (f'<path d="{shape}" fill="{LABEL_BG}" stroke="{LABEL_INK}" stroke-width="3" stroke-linejoin="round"/>'
           f'<text x="{bx + bw / 2}" y="{by + 40}" font-size="19" font-weight="900" text-anchor="middle" fill="{LABEL_INK}">Which mushroom has</text>'
           f'<text x="{bx + bw / 2}" y="{by + 64}" font-size="19" font-weight="900" text-anchor="middle" fill="{LABEL_INK}">Frog&#8217;s last note?</text>')
    return box + "".join(mushroom(c, x, y, w, answer + d) for c, x, y, w, d in MUSHROOMS_AT)


# ----------------------------------------------------------------- the page

def page():
    pos = positions()
    arrows, labels = links()
    stones = "".join(stone(i + 1, cx, cy, pos[i] if i == 0 else None)
                     for i, (cx, cy) in enumerate(STONES))
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
  <defs>
    <marker id="headhalo" markerWidth="28" markerHeight="28" refX="12" refY="14" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M-1 1 L23 14 L-1 27 Z" fill="{ARROW_HALO}" stroke="{ARROW_HALO}" stroke-width="4" stroke-linejoin="round"/>
    </marker>
    <marker id="head" markerWidth="28" markerHeight="28" refX="12" refY="14" orient="auto" markerUnits="userSpaceOnUse">
      <path d="M2 5 L19 14 L2 23 Z" fill="{ARROW}"/>
    </marker>
  </defs>
  {f'<clipPath id="frame"><rect x="32" y="32" width="1036" height="786" rx="24"/></clipPath><image x="0" y="0" width="1100" height="850" href="{stream_outline_uri()}" preserveAspectRatio="none" clip-path="url(#frame)"/><rect x="32" y="32" width="1036" height="786" rx="24" fill="none" stroke="#000" stroke-width="3"/>' if BW else f'<image x="0" y="0" width="1100" height="850" href="{scene_data_uri()}" preserveAspectRatio="none"/>'}
  <text x="550" y="98" font-size="58" font-weight="900" text-anchor="middle">{TITLE}</text>
  <text x="550" y="140" font-size="20" font-weight="700" text-anchor="middle">{SUBTITLE}</text>
  {picture(FROG, 44, 356, 110)}
  {sign(222, 352, "Start")}
  {sign(1000, 724, "Finish", w=108, lean=3, size=22)}
  {"" if BW else rock_cutout()}
  {arrows}
  {stones}
  {labels}
  <text x="550" y="{806 if BW else 832}" font-size="12.5" font-weight="700" text-anchor="middle" fill="{INK}" opacity="0.75">Interval Jump  ·  beeskeysapp.com</text>
</svg>
</body></html>"""


if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    common = [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
              "--virtual-time-budget=3000"]
    NAME = NAME + ("-intervals" if INTERVALS else "") + ("-bw" if BW else "")
    html = OUT / f"{NAME}.html"
    html.write_text(page(), encoding="utf-8")
    subprocess.run(common + ["--no-pdf-header-footer",
                             f"--print-to-pdf={OUT / (NAME + '.pdf')}", html.as_uri()],
                   check=True, capture_output=True)
    subprocess.run(common + ["--window-size=1056,816", "--force-device-scale-factor=2",
                             f"--screenshot={OUT / (NAME + '-preview.png')}", html.as_uri()],
                   check=True, capture_output=True)
    html.unlink()
    print(OUT / f"{NAME}.pdf")
