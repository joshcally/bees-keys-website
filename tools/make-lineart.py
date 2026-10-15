#!/usr/bin/env python3
"""Turn the flat-colour card art into colouring-book line art for the
printer-friendly Rhythm Phrase Builders deck.

    python3 tools/make-lineart.py

Reads the creature PNGs the deck uses from tools/sound-garden-art/, the bee
render and the place tiles from tools/rhythm-phrase-art/, writes transparent black-line
PNGs with the same names into tools/rhythm-phrase-art/bw/.

How: the art is flat fills with dark ink outlines. Keep the ink (pixels where
every channel is dark; luminance alone would swallow saturated reds), reduce
thick dark fills such as the ant's body to their outline, and add a line
wherever two neighbouring colours differ a lot after a median blur, except
right beside existing ink so nothing double-lines. Specks are dropped.
"""
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SG = ROOT / "tools" / "sound-garden-art"
PL = ROOT / "tools" / "rhythm-phrase-art"
OUT = PL / "bw"

CREATURES = ["spider-drawn", "grasshopper-drawn", "ant", "ladybug", "caterpillar",
             "firefly-drawn", "butterfly", "cricket-drawn"]
PLACES = ["meadow", "garden", "flowers", "grass", "leaves", "woods", "pond", "trail", "ground"]


def ink_mask(a, dark, blur=3):
    opaque = a[..., 3] > 128
    rgb = a[..., :3].copy()
    rgb[~opaque] = 255
    sm = cv2.medianBlur(rgb, blur) if blur > 1 else rgb
    return opaque, sm, (opaque & (sm.max(axis=2) < dark)).astype(np.uint8)


def ellipse(n):
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (n, n))


def creature_lineart(src, dst, dark=90, bold=3, fat=21, fat_area=15000, hole_area=3000,
                     extra_T=None, glint_grow=5, blur=3):
    """Colouring-book outline for a creature (Kristianna's notes, Oct 15):
    keep the drawn ink as ink (pupils, smiles, stripes stay solid), turn only
    big solid-dark bodies into outlines (their holes, the eye whites, outline
    themselves and thin holes like a smile fill in), trace the outer
    silhouette so wings and gaps close, make it all bold. No colour-edge
    tracing: that is what produced speckled legs and double lines."""
    a = np.array(Image.open(src).convert("RGBA"))
    opaque, sm, ink = ink_mask(a, dark, blur)
    # fat dark regions: what survives a wide opening, if there is a lot of it
    fatpart = cv2.morphologyEx(ink, cv2.MORPH_OPEN, ellipse(fat))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fatpart, connectivity=8)
    fills = np.zeros_like(fatpart)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= fat_area:
            fills[lab == i] = 1
    # thin holes inside a fill (a smile on a dark face) become ink
    holes = np.zeros_like(fills)
    if fills.any():
        inv = (1 - fills).astype(np.uint8)
        m, hl, hs, _ = cv2.connectedComponentsWithStats(inv, connectivity=4)
        border = set(np.unique(np.concatenate([hl[0], hl[-1], hl[:, 0], hl[:, -1]])))
        for i in range(1, m):
            if i not in border and hs[i, cv2.CC_STAT_AREA] < hole_area:
                holes[hl == i] = 1
    # a smile or an eye ring drawn on a dark face: thin features inside a
    # fill that are darker than the fill itself
    relief = np.zeros_like(fills)
    if fills.any():
        mx = sm.max(axis=2).astype(int)
        differ = np.zeros_like(fills)
        fn, fl = cv2.connectedComponents(fills, connectivity=8)
        for i in range(1, fn):           # each solid region against its own darkness
            region = fl == i
            base = np.median(mx[region])
            differ[region & (mx < base - 16)] = 1      # darker only: highlights near the edge read as lashes
        relief = differ - cv2.morphologyEx(differ, cv2.MORPH_OPEN, ellipse(27))   # drop broad highlights, keep strokes
        relief = cv2.morphologyEx(relief, cv2.MORPH_OPEN, ellipse(5))
        m, rl, rs, _ = cv2.connectedComponentsWithStats(relief, connectivity=8)
        for i in range(1, m):
            if rs[i, cv2.CC_STAT_AREA] < 250:
                relief[rl == i] = 0
    outline = fills - cv2.erode(fills, ellipse(2 * bold + 3))
    strokes = ink & (1 - fills)
    sil = opaque.astype(np.uint8) - cv2.erode(opaque.astype(np.uint8), ellipse(2 * bold + 3))
    line = ((strokes | outline | holes | relief | sil) > 0).astype(np.uint8)
    if extra_T is not None:
        # a few drawings have unlined parts (the bee's wings over its body)
        sm_i = sm.astype(int)
        h, w = opaque.shape
        edge = np.zeros_like(opaque)
        for dy, dx in ((0, 1), (1, 0)):
            A = sm_i[dy:, dx:]
            B = sm_i[:h - dy, :w - dx]
            diff = np.abs(A - B).max(axis=2) > extra_T
            e = np.zeros_like(opaque)
            e[dy:, dx:] |= diff
            edge |= e
        edge &= opaque
        line |= cv2.dilate(edge.astype(np.uint8), ellipse(2 * bold + 1))
    line = cv2.dilate(line, ellipse(2 * bold - 1))
    # the white glint in each pupil: a small hole inside a small solid ink
    # shape; grow it so it survives the bold pass and reads at card size
    pupils = np.zeros_like(fatpart)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] < fat_area:
            pupils[lab == i] = 1
    if pupils.any():
        near_pupil = cv2.dilate(pupils, ellipse(5))
        light = (sm.min(axis=2) > 150).astype(np.uint8) & near_pupil
        m, gl, gs, _ = cv2.connectedComponentsWithStats(light, connectivity=8)
        glint = np.zeros_like(pupils)
        for i in range(1, m):
            w_, h_, area = gs[i, cv2.CC_STAT_WIDTH], gs[i, cv2.CC_STAT_HEIGHT], gs[i, cv2.CC_STAT_AREA]
            # a glint is small and compact; the white of the eye is a big crescent
            if area < 1500 and w_ < 48 and h_ < 48 and area > 0.5 * w_ * h_:
                glint[gl == i] = 1
        glint = cv2.dilate(glint, ellipse(2 * glint_grow + 1)) & cv2.dilate(pupils, ellipse(3))
        line[glint > 0] = 0
    n, lab, stats, _ = cv2.connectedComponentsWithStats(line, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= 60
    out = np.zeros(a.shape, dtype=np.uint8)
    out[..., 3] = np.where(keep[lab], 255, 0)
    Image.fromarray(out).save(dst)


def lineart(src, dst, dark=90, T=80, thick=1, blur=7, min_area=40):
    """Scene tiles: ink plus colour edges (the tiles have many unlined fills)."""
    a = np.array(Image.open(src).convert("RGBA"))
    opaque = a[..., 3] > 128
    rgb = a[..., :3].copy()
    rgb[~opaque] = 255
    sm = cv2.medianBlur(rgb, blur).astype(int)
    ink = (opaque & (sm.max(axis=2) < dark)).astype(np.uint8)
    fatpart = cv2.morphologyEx(ink, cv2.MORPH_OPEN, ellipse(11))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(fatpart, connectivity=8)
    blob = np.zeros_like(opaque)
    for i in range(1, n):
        if stats[i, cv2.CC_STAT_AREA] >= 2500:     # a real fill, not a line crossing
            blob |= lab == i
    stroke = ink.astype(bool) & ~blob
    h, w = opaque.shape
    edge = np.zeros_like(opaque)
    for dy, dx in ((0, 1), (1, 0), (1, 1), (1, -1)):
        A = sm[max(dy, 0):h - max(-dy, 0), max(dx, 0):w - max(-dx, 0)]
        B = sm[max(-dy, 0):h - max(dy, 0), max(-dx, 0):w - max(dx, 0)]
        diff = np.abs(A - B).max(axis=2) > T
        s = np.zeros_like(opaque)
        s[max(dy, 0):h - max(-dy, 0), max(dx, 0):w - max(-dx, 0)] |= diff
        edge |= s
    near = cv2.dilate(stroke.astype(np.uint8), ellipse(7)).astype(bool)
    inner = cv2.erode(blob.astype(np.uint8), ellipse(5)).astype(bool)
    edge &= ~near
    edge &= ~inner
    line = (stroke | edge).astype(np.uint8)
    if thick:
        line = cv2.dilate(line, ellipse(2 * thick + 1))
    n, lab, stats, _ = cv2.connectedComponentsWithStats(line, connectivity=8)
    keep = np.zeros(n, bool)
    keep[1:] = stats[1:, cv2.CC_STAT_AREA] >= min_area
    out = np.zeros(a.shape, dtype=np.uint8)
    out[..., 3] = np.where(keep[lab], 255, 0)
    Image.fromarray(out).save(dst)


def main():
    OUT.mkdir(exist_ok=True)
    for f in CREATURES:
        if f == "butterfly":
            # tiny face with hairline eye rings: no blur, thinner lines
            creature_lineart(SG / f"{f}.png", OUT / f"{f}.png", bold=2, blur=1, glint_grow=3)
        else:
            creature_lineart(SG / f"{f}.png", OUT / f"{f}.png", dark=60 if f == "spider-drawn" else 90)
    # the app bee, rendered from its three stacked SVGs into rhythm-phrase-art/bee.png;
    # its wings have no drawn outline, so colour edges are allowed for it
    creature_lineart(PL / "bee.png", OUT / "bee.png", extra_T=110)
    for f in PLACES:
        # the tiles are smaller and already outlined: thinner, slightly stricter
        lineart(PL / f"{f}.png", OUT / f"{f}.png", thick=1, blur=5, T=60, min_area=25)
    print("wrote", len(CREATURES) + len(PLACES), "files to", OUT)


if __name__ == "__main__":
    main()
