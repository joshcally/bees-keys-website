#!/usr/bin/env python3
"""Render and lay out the Left or Right? prompt cards.

Nine landscape poker cards (3.5x2.5 in): clean yellow-bordered prompt
fronts and one cute shared back, drawn from tools/card-left-or-right.html through headless Chrome.
Each card is a prompt to answer on the big Left or Right? board.

    python3 tools/make-left-or-right-cards.py

Output: output/higher-lower/bees-keys-left-or-right-cards.pdf, two landscape
US Letter pages, fronts then backs, the 3x3 grid filling the page. The grid
is centered and every back is the same, so it lines up whichever edge the
printer flips on.
"""
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

import fitz

ROOT = Path(__file__).resolve().parents[1]
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRC = ROOT / "tools" / "card-left-or-right.html"

CARDS = [
    "Go higher", "Go lower", "Find the middle",
    "Find a high sound", "Find a low sound", "Move up",
    "Find a higher key", "Find a lower key", "Move down",
]

W, H = 792, 612            # US Letter landscape, points
CW, CH = 252, 180          # 3.5 x 2.5 inches
MX, MY = (W - 3 * CW) / 2, (H - 3 * CH) / 2


def render(url, png):
    subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--window-size=1512,1080", "--virtual-time-budget=4000",
        f"--screenshot={png}", url,
    ], check=True, capture_output=True)


def cell(r, c):
    return fitz.Rect(MX + c * CW, MY + r * CH, MX + (c + 1) * CW, MY + (r + 1) * CH)


def main():
    tmp = ROOT / "tmp" / "left-or-right"
    out = ROOT / "output" / "higher-lower" / "bees-keys-left-or-right-cards.pdf"
    tmp.mkdir(parents=True, exist_ok=True)
    out.parent.mkdir(parents=True, exist_ok=True)

    base = SRC.resolve().as_uri()
    back = tmp / "back.png"
    render(f"{base}?back=1", back)
    fronts = []
    for i, text in enumerate(CARDS, 1):
        png = tmp / f"card-{i:02d}.png"
        render(f"{base}?{urlencode({'t': text})}", png)
        fronts.append(png)
        print("rendered", i, text, file=sys.stderr)

    doc = fitz.open()
    f = doc.new_page(width=W, height=H)
    for n, png in enumerate(fronts):
        f.insert_image(cell(n // 3, n % 3), filename=str(png))
    # Dashed cut lines on the fronts, one per cut, shared between neighbors.
    grid = fitz.Rect(MX, MY, W - MX, H - MY)
    for i in range(4):
        x, y = MX + i * CW, MY + i * CH
        f.draw_line((x, grid.y0), (x, grid.y1), color=(.6, .6, .6), width=.8, dashes="[5 4] 0")
        f.draw_line((grid.x0, y), (grid.x1, y), color=(.6, .6, .6), width=.8, dashes="[5 4] 0")
    b = doc.new_page(width=W, height=H)
    for n in range(9):
        b.insert_image(cell(n // 3, n % 3), filename=str(back))
    doc.set_metadata({"title": "Left or Right? Prompt Cards - Bees Keys"})
    doc.save(out, deflate=True)
    for i, page in enumerate(doc):
        page.get_pixmap(dpi=110).save(out.with_name(f"{out.stem}-{i + 1}.png"))
    print(out, doc.page_count, "pages")


if __name__ == "__main__":
    main()
