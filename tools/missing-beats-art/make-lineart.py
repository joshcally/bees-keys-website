"""Coloring-book line art of the six guests for the Missing Beats printer page.

Kristianna's brief (Nov 16 2026): no heavy black spots, outline the
creatures, "pretend someone else is coloring them in". So only the pupils
are filled: antenna tips, stripes, feet and ladybug spots are open shapes.

Each bug is traced from its color art (the art's own dark lines), every
solid dark area is hollowed to a thin line, eye whites / spots / wings get a
ring, and the outer outline is redrawn at one printed weight for all six.

    python3 tools/missing-beats-art/make-lineart.py
"""
import os

import cv2
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
RP = os.path.join(HERE, "..", "rhythm-phrase-art")
SG = os.path.join(HERE, "..", "sound-garden-art")
OUTLINE = 1.3                      # printed weight of the outer outline, points
DETAIL = 0.75                      # printed weight of hollowed shapes and rings
# art dir and printed width of each bug (GUESTS_* in make-missing-beats-sheet.py)
BEE_LEGS = (152, 592, 512, 770)    # x0, y0, x1, y1 in the padded bee art
# each leg in the color bee, body end first then foot (unpadded art px)
BEE_LEG_LINES = [((286, 610), (240, 630)), ((304, 640), (274, 662)), ((356, 680), (333, 712)),
                 ((381, 676), (360, 724)), ((421, 705), (426, 744)), ((445, 692), (454, 750))]
GRASSHOPPER_FLECK = (1024, 274, 1064, 320)   # x0, y0, x1, y1 (unpadded art px)
WING_SMOOTH = 111                  # px: wing-edge wiggles narrower than this are ironed out
BUGS = {"bee": (RP, 96), "butterfly": (SG, 84), "ladybug": (SG, 86),
        "grasshopper-drawn": (SG, 112), "cricket-drawn": (SG, 110), "caterpillar": (SG, 108)}


def ell(n):
    n = max(1, int(round(n)))
    return cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (n, n))


def trace(name, folder, width_pt):
    im = cv2.imread(os.path.join(folder, name + ".png"), cv2.IMREAD_UNCHANGED)
    im = cv2.copyMakeBorder(im, 12, 12, 12, 12, cv2.BORDER_CONSTANT, value=(0, 0, 0, 0))
    sil = (im[..., 3] > (60 if name == "bee" else 128)).astype(np.uint8)
    sil = cv2.morphologyEx(sil, cv2.MORPH_OPEN, ell(5))
    V = im[..., :3].max(axis=2).astype(np.int16)
    V[sil == 0] = 255
    V = V.astype(np.uint8)
    xs = np.where(sil.any(axis=0))[0]
    scale = (xs.max() - xs.min() + 1) / width_pt               # source px per printed point
    w, d = OUTLINE * scale, DETAIL * scale
    total = sil.sum()

    if name == "ladybug":      # black lines on a near-black head and legs: only true black is ink
        ink = ((V < 18) & (sil > 0)).astype(np.uint8)
    else:
        hat = cv2.morphologyEx(V, cv2.MORPH_CLOSE, ell(35)).astype(np.int16) - V
        ink = (((hat > 55) | (V < 85)) & (sil > 0)).astype(np.uint8)

    white = ((im[..., :3].min(axis=2) > 205) & (sil > 0)).astype(np.uint8)

    if name == "bee":          # its stubby legs are redrawn one by one at the end
        x0, y0, x1, y1 = BEE_LEGS
        body = cv2.morphologyEx(sil, cv2.MORPH_OPEN, ell(45))
        thin = ink & (1 - cv2.morphologyEx(ink, cv2.MORPH_OPEN, ell(41)))
        legs = np.zeros_like(ink)
        legs[y0:y1, x0:x1] = cv2.morphologyEx(thin, cv2.MORPH_OPEN, ell(11))[y0:y1, x0:x1]
        stubs = cv2.dilate(legs, ell(5)) & body               # leg tops drawn over the body
        legs = cv2.dilate(legs, ell(9)) & (1 - body)
        ink[legs > 0] = 0
        sil[legs > 0] = 0

    # nothing stays filled except the pupils: anything else thicker than a
    # line becomes an open shape to color
    core = cv2.erode(ink, ell(2 * d + 1))
    core = cv2.morphologyEx(core, cv2.MORPH_OPEN, ell(5))      # no hairline slits in fat lines
    n, lab = cv2.connectedComponents(core)
    for i in range(1, n):
        comp = (lab == i).astype(np.uint8)
        blob = cv2.dilate(comp, ell(2 * d + 3)) & ink
        around = cv2.dilate(blob, ell(13)) & (1 - blob)
        if white[around > 0].mean() > 0.35:                    # sits in an eye white: a pupil
            continue
        ink[comp > 0] = 0

    if name == "grasshopper-drawn":   # a stray dark fleck beside its right eye in the color art
        x0, y0, x1, y1 = GRASSHOPPER_FLECK
        ink[y0 + 12:y1 + 12, x0 + 12:x1 + 12] = 0     # the eye ring and outline are redrawn below

    def rings(mask, lo, hi):
        n, lab, st, _ = cv2.connectedComponentsWithStats(mask.astype(np.uint8))
        for i in range(1, n):
            if lo * total < st[i, cv2.CC_STAT_AREA] < hi * total:
                comp = (lab == i).astype(np.uint8)
                k = float(np.clip(np.sqrt(st[i, cv2.CC_STAT_AREA]) / 14, 3, d))
                ink[(cv2.dilate(comp, ell(k)) > 0) & (cv2.erode(comp, ell(k)) == 0)] = 1

    # eye whites (and the bee's wings), whatever they sit on
    rings(cv2.morphologyEx(white, cv2.MORPH_OPEN, ell(5)), 0.0015, 0.04)
    if name == "bee":          # wings: see-through, so their edge over the body is ragged; smooth it
        n, lab, st, _ = cv2.connectedComponentsWithStats(cv2.morphologyEx(white, cv2.MORPH_OPEN, ell(5)))
        for i in range(1, n):
            if st[i, cv2.CC_STAT_AREA] > 0.04 * total:
                wing = cv2.morphologyEx((lab == i).astype(np.uint8), cv2.MORPH_OPEN, ell(WING_SMOOTH))
                ink[(cv2.dilate(wing, ell(d)) > 0) & (cv2.erode(wing, ell(d)) == 0)] = 1
    if name == "ladybug":      # spots
        rings(cv2.morphologyEx(((V < 60) & (sil > 0)).astype(np.uint8), cv2.MORPH_OPEN, ell(31)), 0.003, 0.04)
    ink &= sil
    n, lab, st, _ = cv2.connectedComponentsWithStats(ink, connectivity=8)
    for i in range(1, n):      # no specks or broken dashes
        if st[i, cv2.CC_STAT_AREA] < (80 if name == "butterfly" else 200):   # its smile is tiny
            ink[lab == i] = 0

    # the outer outline, one weight for every bug
    depth = cv2.distanceTransform(sil, cv2.DIST_L2, 5)
    old = 40
    for k in range(1, 40):
        ring = (depth > k - 1) & (depth <= k)
        if ink[ring].mean() < 0.5:
            old = k + 3
            break
    rim = sil & (depth <= w)
    if old <= w:
        new = rim | ink
    else:
        inner = ink & (depth > old)
        gap = ink & (depth > w) & (depth <= old)
        new = rim | inner | (gap & cv2.dilate(inner, ell(2 * (old - w) + 5)))
    if name == "bee":          # six separate legs, each its own open shape, tucked behind the body
        new[(stubs > 0) & (depth > w + 1)] = 0
        for (ax, ay), (bx, by) in BEE_LEG_LINES:
            cap = np.zeros_like(sil)
            cv2.line(cap, (ax + 12, ay + 12), (bx + 12, by + 12), 1, 28, cv2.LINE_8)
            cv2.circle(cap, (bx + 12, by + 12), 14, 1, -1)
            vis = cap & (1 - body)
            new[vis > 0] = 0
            new[(vis > 0) & (cv2.erode(cap, ell(2 * d + 1)) == 0)] = 1
            sil |= vis
    g = cv2.GaussianBlur(np.where(new > 0, 0, 255).astype(np.uint8), (0, 0), 0.8)
    a = cv2.GaussianBlur(sil * 255, (0, 0), 0.8)
    return np.dstack([g, g, g, a])[12:-12, 12:-12]


for name, (folder, width) in BUGS.items():
    cv2.imwrite(os.path.join(HERE, name + "-bw.png"), trace(name, folder, width))
    print(name)
