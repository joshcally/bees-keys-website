#!/usr/bin/env python3
"""Draw a gold edge along the cutout's alpha boundary.

The background removal leaves a ragged edge where the piano meets transparency.
A stroke straddling that boundary covers the ragged pixels on both sides — the
same trick the Pro ad uses, where a gold contour traces the tablet and desk.

The band is built morphologically: dilate the alpha mask, erode it, and take the
difference. That gives a ring centred on the edge, so half the stroke sits over
the ragged fringe and half over clean background.

Only *interior* edges are traced. Where the piano runs off the side or bottom of
the frame the boundary is just the image border, not a cutout edge, and drawing
there would box the photo in.
"""

import sys

from PIL import Image, ImageChops, ImageFilter

# Gold ramp, top to bottom — same family as the ad's contour.
GOLD_TOP = (240, 180, 41)   # --comb-mid  #f0b429
GOLD_MID = (200, 144, 26)   # between comb-mid and comb-deep
GOLD_LOW = (160, 106, 18)   # deeper than --comb-deep, so the edge reads as
                            # struck metal against the section's navy rather
                            # than a bright highlight


def ramp(h):
    """A vertical gold gradient, h px tall, as a 1px-wide image."""
    strip = Image.new("RGB", (1, h))
    px = strip.load()
    for y in range(h):
        t = y / max(h - 1, 1)
        if t < 0.5:
            u = t / 0.5
            c = tuple(round(a + (b - a) * u) for a, b in zip(GOLD_TOP, GOLD_MID))
        else:
            u = (t - 0.5) / 0.5
            c = tuple(round(a + (b - a) * u) for a, b in zip(GOLD_MID, GOLD_LOW))
        px[0, y] = c
    return strip


def trace(src, dst, radius=5, border=8, out_width=900, feather=2.8, smooth=16.0):
    im = Image.open(src).convert("RGBA")
    w, h = im.size
    alpha = im.getchannel("A")

    # Binary silhouette of the subject. Blurring before the threshold rounds off
    # both the stair-stepping and the sharp notches the background removal
    # leaves where two objects meet — at the iPad's top-left corner it otherwise
    # traced a hard right-angle jog. The blur radius sets the corner radius, so
    # it needs to exceed the notch: too small and the kink survives, too large
    # and the outline bulges away from the subject.
    solid = alpha.point(lambda v: 255 if v > 128 else 0)
    solid = solid.filter(ImageFilter.GaussianBlur(smooth))
    solid = solid.point(lambda v: 255 if v > 128 else 0)

    k = 2 * radius + 1
    grown = solid.filter(ImageFilter.MaxFilter(k))
    shrunk = solid.filter(ImageFilter.MinFilter(k))
    band = ImageChops.subtract(grown, shrunk)

    # Kill the band along the frame edges — those aren't cutout boundaries.
    interior = Image.new("L", (w, h), 0)
    interior.paste(255, (border, border, w - border, h - border))
    band = ImageChops.multiply(band, interior)

    # Soften so the stroke doesn't read as aliased pixel stairs.
    band = band.filter(ImageFilter.GaussianBlur(feather))

    gold = ramp(h).resize((w, h))
    out = im.copy()
    out.paste(gold, (0, 0), band)                       # colour where the band is
    merged = ImageChops.lighter(im.getchannel("A"), band)  # and make it opaque
    out.putalpha(merged)

    if out_width and out_width != w:
        out = out.resize((out_width, round(h * out_width / w)), Image.LANCZOS)

    clean = Image.new("RGBA", out.size)
    clean.putdata(list(out.getdata()))                  # drop metadata
    clean.save(dst, "WEBP", quality=88, method=6)
    print(f"{dst}: {clean.size[0]}x{clean.size[1]}, radius {radius}px @ {w}px wide")
    return clean


if __name__ == "__main__":
    trace(sys.argv[1], sys.argv[2],
          radius=int(sys.argv[3]) if len(sys.argv) > 3 else 5)
