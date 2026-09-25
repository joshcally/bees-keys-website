"""The Bees Keys app's programmatic 3D keyboard, ported to reportlab.

A straight port of BeesKeys/Views/Keyboard/PerspectiveGeometry.swift,
PianoKeyboard.swift (WhitePianoKey, BlackPianoKey) and
Models/PianoKeyboardLayout.swift, so printables draw the same keyboard the
app does. Geometry is computed y-down in a w x h box (like SwiftUI) and
flipped when drawn.

    draw_keyboard(c, x, y_top, width, start="F", white_count=11,
                  highlights={"white": {0}, "black": {7}})

The app's "F+" board (elevenKeys) is F3..B4: 11 white + 8 black = 19 keys.
"""
import math

WHITES = ["C", "D", "E", "F", "G", "A", "B"]
SHARP_AFTER = {"C": "C#", "D": "D#", "F": "F#", "G": "G#", "A": "A#"}
OFFSET_RATIO = {"C#": 0.903, "D#": 1.097, "F#": 0.855, "G#": 1.000, "A#": 1.145}

SEVEN_KEY_ASPECT = 1250.0 / 550.0
TOP_L, TOP_R = (0.165, 0.02), (0.835, 0.02)
BOT_L, BOT_R = (0.0, 0.83), (1.0, 0.83)
KEY_TOP_Y, KEY_BOTTOM_Y = 0.02, 0.98
BLACK_TOP_Y, BLACK_BOTTOM_Y = 0.0, 0.35
BLACK_WIDTH_RATIO = 0.48
WHITE_GAP = 0.015
SHIFT_PEAK, SHIFT_PEAK_AT, SHIFT_WIDTH = 0.018, 0.32, 0.15
CAP_DEPTH, SIDE_REVEAL, SIDE_BASE, SIDE_DROP = 0.33, 0.24, 0.10, 0.08
SIDE_PARALLEL_BLEND = 0.35

HONEY = (0.95, 0.76, 0.22)


def aspect(white_count):
    return SEVEN_KEY_ASPECT * white_count / 7.0


def layout(start="F", white_count=11):
    """[(name, is_white, left_white_index, offset_ratio)] left to right."""
    i0 = WHITES.index(start)
    slots = []
    for i in range(white_count):
        k = WHITES[(i0 + i) % 7]
        slots.append((k, True, i, 0.0))
        if i < white_count - 1 and k in SHARP_AFTER:
            s = SHARP_AFTER[k]
            slots.append((s, False, i, OFFSET_RATIO[s]))
    return slots


def _pt(t, yf, w, h):
    span = BOT_L[1] - TOP_L[1]
    p = (yf - TOP_L[1]) / span
    lx = TOP_L[0] + (BOT_L[0] - TOP_L[0]) * p
    rx = TOP_R[0] + (BOT_R[0] - TOP_R[0]) * p
    return ((lx + (rx - lx) * t) * w, yf * h)


def _ledge_y(n):
    return 0.80 if n <= 7 else 0.83


def white_shape(i, n, w, h):
    """6-point outline plus the ledge corners, y-down."""
    gap = WHITE_GAP / n
    tl_, tr_ = i / n + gap / 2, (i + 1) / n - gap / 2
    tl, tr = _pt(tl_, KEY_TOP_Y, w, h), _pt(tr_, KEY_TOP_Y, w, h)
    ly = _ledge_y(n)
    ll, lr = _pt(tl_, ly, w, h), _pt(tr_, ly, w, h)
    by = KEY_BOTTOM_Y * h
    return {"top": [tl, tr, lr, ll],
            "front": [ll, lr, (lr[0], by), (ll[0], by)],
            "outline": [tl, tr, lr, (lr[0], by), (ll[0], by), ll],
            "ledge": (ll, lr)}


def _shift(t, w):
    d = t - 0.5
    x = (abs(d) - SHIFT_PEAK_AT) / SHIFT_WIDTH
    return (-1 if d < 0 else 1) * SHIFT_PEAK * math.exp(-x * x) * w


def black_shifts(slots, n, w):
    blacks = [(j, s) for j, s in enumerate(slots) if not s[1]]
    groups, g, prev = [], [], None
    for j, s in blacks:
        if g and s[2] != prev + 1:
            groups.append(g)
            g = []
        g.append((j, s))
        prev = s[2]
    if g:
        groups.append(g)
    out = {}
    for grp in groups:
        sh = [[j, _shift((s[2] + s[3]) / n, w)] for j, s in grp]
        if len(sh) == 3:
            sh[1][1] = (sh[0][1] + sh[2][1]) / 2
        for j, v in sh:
            out[j] = v
    return out


def black_shape(left_idx, offset, dx, n, w, h):
    slot = 1.0 / n
    half = slot * BLACK_WIDTH_RATIO / 2
    c = (left_idx + offset) * slot
    tl = _pt(c - half, BLACK_TOP_Y, w, h)
    tr = _pt(c + half, BLACK_TOP_Y, w, h)
    br = _pt(c + half, BLACK_BOTTOM_Y, w, h)
    bl = _pt(c - half, BLACK_BOTTOM_Y, w, h)
    tl, tr, br, bl = [(p[0] + dx, p[1]) for p in (tl, tr, br, bl)]
    kw = math.hypot(tr[0] - tl[0], tr[1] - tl[1])
    sh = bl[1] - tl[1]
    ty = sh * CAP_DEPTH
    lean = (tl[0] + tr[0]) / 2 - (bl[0] + br[0]) / 2
    right = lean >= 0
    brn, bln = (br[0], br[1] + ty), (bl[0], bl[1] + ty)
    sw = kw * SIDE_BASE + abs(lean) * SIDE_REVEAL
    sd = sh * SIDE_DROP
    s = (tr[0] + sw, tr[1] + sd) if right else (tl[0] - sw, tl[1] + sd)
    inner_f, outer_f, back = (br, brn, tr) if right else (bl, bln, tl)
    back_par = (inner_f[0] + s[0] - outer_f[0], inner_f[1] + s[1] - outer_f[1])
    back_in = (back[0] + (back_par[0] - back[0]) * SIDE_PARALLEL_BLEND,
               back[1] + (back_par[1] - back[1]) * SIDE_PARALLEL_BLEND)
    sil = [tl, tr, s, brn, bln, bl] if right else [tl, tr, br, brn, bln, s]
    side = [back_in, s, brn, br] if right else [s, back_in, bl, bln]
    edges = [(bl, br), (back_in, inner_f), (inner_f, outer_f)]
    return {"sil": sil, "radius": kw * 0.16, "front": [bl, br, brn, bln],
            "side": side, "edges": edges, "center": ((tl[0] + br[0]) / 2, (tl[1] + bl[1]) / 2)}


def keyboard_geometry(width, start="F", white_count=11):
    h = width / aspect(white_count)
    slots = layout(start, white_count)
    n = white_count
    shifts = black_shifts(slots, n, width)
    whites, blacks = [], []
    for j, (name, is_white, li, off) in enumerate(slots):
        if is_white:
            whites.append((name, white_shape(li, n, width, h)))
        else:
            blacks.append((name, black_shape(li, off, shifts[j], n, width, h)))
    return h, whites, blacks


# ---------------------------------------------------------------- drawing

def _path(c, pts, X, Y, close=True):
    p = c.beginPath()
    p.moveTo(X(pts[0][0]), Y(pts[0][1]))
    for q in pts[1:]:
        p.lineTo(X(q[0]), Y(q[1]))
    if close:
        p.close()
    return p


def _rounded(c, pts, r, X, Y):
    p = c.beginPath()
    n = len(pts)
    for i in range(n):
        prev, cur, nxt = pts[i - 1], pts[i], pts[(i + 1) % n]
        dp = (prev[0] - cur[0], prev[1] - cur[1])
        dn = (nxt[0] - cur[0], nxt[1] - cur[1])
        lp, ln = max(math.hypot(*dp), 1e-4), max(math.hypot(*dn), 1e-4)
        rp, rn = min(r, lp / 2), min(r, ln / 2)
        p1 = (cur[0] + dp[0] / lp * rp, cur[1] + dp[1] / lp * rp)
        p2 = (cur[0] + dn[0] / ln * rn, cur[1] + dn[1] / ln * rn)
        if i == 0:
            p.moveTo(X(p1[0]), Y(p1[1]))
        else:
            p.lineTo(X(p1[0]), Y(p1[1]))
        # quadratic -> cubic
        c1 = (p1[0] + 2 / 3 * (cur[0] - p1[0]), p1[1] + 2 / 3 * (cur[1] - p1[1]))
        c2 = (p2[0] + 2 / 3 * (cur[0] - p2[0]), p2[1] + 2 / 3 * (cur[1] - p2[1]))
        p.curveTo(X(c1[0]), Y(c1[1]), X(c2[0]), Y(c2[1]), X(p2[0]), Y(p2[1]))
    p.close()
    return p


def draw_keyboard(c, x, y_top, width, start="F", white_count=11,
                  highlights=None, highlight_color=HONEY, outline=None):
    """Draw at (x, y_top) in reportlab points; returns (height, geometry).

    highlights: {"white": set of white indices, "black": set of black indices}
    (both 0-based, left to right). Highlighted white keys take a honey wash;
    highlighted black keys get a honey top surface.
    """
    highlights = highlights or {}
    hw, hb = highlights.get("white", set()), highlights.get("black", set())
    h, whites, blacks = keyboard_geometry(width, start, white_count)
    X = lambda v: x + v
    Y = lambda v: y_top - v
    ow = outline if outline is not None else min(3.2, max(1.2, h * 0.014))
    c.saveState()
    c.setLineJoin(1)
    c.setLineCap(1)
    for i, (_, s) in enumerate(whites):
        lit = i in hw
        face = (0.99, 0.88, 0.55) if lit else (0.95, 0.93, 0.93)
        top = (1.0, 0.93, 0.66) if lit else (1, 1, 1)
        c.setFillColorRGB(*face)
        c.drawPath(_path(c, s["front"], X, Y), stroke=0, fill=1)
        c.setFillColorRGB(*top)
        c.drawPath(_path(c, s["top"], X, Y), stroke=0, fill=1)
        c.setStrokeColorRGB(0.72, 0.72, 0.72) if not lit else c.setStrokeColorRGB(0.85, 0.66, 0.2)
        c.setLineWidth(max(0.6, ow * 0.4))
        c.drawPath(_path(c, list(s["ledge"]), X, Y, close=False), stroke=1, fill=0)
        c.setStrokeColorRGB(0, 0, 0)
        c.setLineWidth(ow)
        c.drawPath(_path(c, s["outline"], X, Y), stroke=1, fill=0)
    for i, (_, s) in enumerate(blacks):
        lit = i in hb
        sil = _rounded(c, s["sil"], s["radius"], X, Y)
        c.saveState()
        c.clipPath(_rounded(c, s["sil"], s["radius"], X, Y), stroke=0, fill=0)
        c.setFillColorRGB(*((0.93, 0.70, 0.16) if lit else (0.08, 0.08, 0.08)))
        c.drawPath(_path(c, s["sil"] + [], X, Y), stroke=0, fill=1)
        c.rect(X(min(p[0] for p in s["sil"])) - 2, Y(max(p[1] for p in s["sil"])) - 2,
               max(p[0] for p in s["sil"]) - min(p[0] for p in s["sil"]) + 4,
               max(p[1] for p in s["sil"]) - min(p[1] for p in s["sil"]) + 4, stroke=0, fill=1)
        c.setFillColorRGB(*((1.0, 0.86, 0.45) if lit else (0.34, 0.34, 0.34)))
        c.drawPath(_path(c, s["front"], X, Y), stroke=0, fill=1)
        c.setFillColorRGB(*((0.80, 0.58, 0.10) if lit else (0.24, 0.24, 0.24)))
        c.drawPath(_path(c, s["side"], X, Y), stroke=0, fill=1)
        c.setStrokeColorRGB(0.03, 0.03, 0.03)
        c.setLineWidth(max(0.5, ow * 0.35))
        for a, b in s["edges"]:
            c.line(X(a[0]), Y(a[1]), X(b[0]), Y(b[1]))
        c.restoreState()
        c.setStrokeColorRGB(0.03, 0.03, 0.03)
        c.setLineWidth(ow * 0.85)
        c.drawPath(sil, stroke=1, fill=0)
    c.restoreState()
    return h, (whites, blacks)
