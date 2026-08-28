#!/usr/bin/env python3
"""Render the QR code that goes on business cards and the conference poster.

It encodes exactly one thing, https://beeskeysapp.com/go, and that never
changes. What the QR *lands on* is go.html, which can change freely.

    pip install qrcode pillow
    python3 tools/make-go-qr.py

Writes tools/qr/beeskeysapp-go.svg (print this one when you can; it scales
to any size) and tools/qr/beeskeysapp-go.png (2400 px, for tools that only
take a bitmap).

Error correction is H, the highest: a third of the code can be smudged,
scuffed, or printed badly and it still scans. The URL is short enough that
the code stays small (33x33 modules) even so. Print it at least 2 cm across
on a card and 5 cm or more on the poster, with the white quiet zone kept.
"""

from pathlib import Path

import qrcode
import qrcode.image.svg

URL = "https://beeskeysapp.com/go"
OUT = Path(__file__).resolve().parent / "qr"
STEM = "beeskeysapp-go"


def build():
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=1,
        border=4,  # the quiet zone the spec asks for
    )
    qr.add_data(URL)
    qr.make(fit=True)
    return qr


def main():
    OUT.mkdir(parents=True, exist_ok=True)

    svg = build()
    svg_path = OUT / f"{STEM}.svg"
    # SvgPathImage draws one <path> instead of one <rect> per module, which
    # keeps design tools from choking on ~500 tiny objects.
    svg.make_image(image_factory=qrcode.image.svg.SvgPathImage).save(str(svg_path))

    png = build()
    png.box_size = 2400 // (png.modules_count + 2 * png.border)
    png_path = OUT / f"{STEM}.png"
    png.make_image(fill_color="black", back_color="white").save(str(png_path))

    print(f"{URL}")
    print(f"  version {svg.version}, {svg.modules_count}x{svg.modules_count} modules, EC level H")
    print(f"  {svg_path.relative_to(Path.cwd())}")
    print(f"  {png_path.relative_to(Path.cwd())}")


if __name__ == "__main__":
    main()
