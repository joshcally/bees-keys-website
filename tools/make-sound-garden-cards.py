#!/usr/bin/env python3
"""Render and lay out the Bee's Sound Garden adventure cards.

Eighteen poker-size story prompts for piano improv, same 2.5x3.5 in cards
and duplex page geometry as Find Every Key so the two decks stack together.
Fronts carry a number, a title, one short subtitle giving the shape of the
sound (HIGH/LOW are the only direction words), and art.

    python3 tools/make-sound-garden-cards.py [--deck art|color|both]

Two decks from one source: "art" composes a simple scene per card from the
app art in tools/sound-garden-art/ (plus flat SVG creatures drawn in the
HTML); "color" leaves a blank white square for the student to draw in.
Cards are not numbered; the number only picks the scene.

Output pages: backs, fronts 1-9, backs, fronts 10-18. The backs page precedes
its fronts page and columns are mirrored so a long-edge flip aligns.
"""
import argparse
import subprocess
import sys
from pathlib import Path
from urllib.parse import urlencode

import fitz

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "tools" / "sound-garden-art"
CHROME = "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
SRC = ROOT / "tools" / "card-sound-garden.html"

# (title, accent, subtitle). One short line of shape, HIGH/LOW are the only
# direction words, and the rest is left to the player.
CARDS = [
    ("Bee Takes Flight",       "yellow",   "Start LOW. Fly HIGHER."),
    ("A Seed Grows",           "green",    "Grow from LOW to HIGH."),
    ("Spider Climbs Her Web",  "purple",   "Climb HIGHER, one step at a time."),
    ("Ants in a Line",         "pink",     "March from LOW to HIGH."),
    ("Dandelion Puffs Away",   "blue",     "Float HIGHER, softly."),
    ("Grasshopper Jumps!",     "blue",     "Jump from LOW to HIGH."),
    ("Bee Flies Home",         "yellow",   "Start HIGH. Fly LOW to the hive."),
    ("A Leaf Falls",           "green",    "Drift from HIGH to LOW."),
    ("Snail Climbs the Tree",  "green",    "Climb HIGHER, then slide LOW."),
    ("Ladybug Scurries",       "pink",     "Scurry on the HIGH keys."),
    ("Worm Wiggles",           "pink",     "Wiggle LOW. Peek HIGH once."),
    ("Sleepy Frog",            "green",    "Play LOW and slow. Then yawn."),
    ("Beetle Underground",     "purple",   "Rumble on the LOWEST keys."),
    ("Fireflies at Night",     "yellow",   "Play tiny HIGH sparkles. Add a few LOW."),
    ("Caterpillar Meets Frog", "green",    "Take turns: HIGH voice, LOW voice."),
    ("Cricket at Night",       "purple",   "Play HIGH. Answer LOW."),
    ("Raindrops",              "blue",     "Start HIGH. Fall LOWER."),
    ("Butterfly Flutters",     "pink",     "Flutter HIGH, dip LOW, go HIGH again."),
]
assert len(CARDS) == 18

W, H = 612, 792            # US Letter, points
CW, CH = 180, 252          # 2.5 x 3.5 inches
MX, MY = (W - 3 * CW) / 2, (H - 3 * CH) / 2


def render(url, png):
    subprocess.run([
        CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
        "--window-size=1080,1512", "--virtual-time-budget=4000",
        f"--screenshot={png}", url,
    ], check=True, capture_output=True)


def cell(r, c):
    return fitz.Rect(MX + c * CW, MY + r * CH, MX + (c + 1) * CW, MY + (r + 1) * CH)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", choices=["art", "color", "both"], default="both")
    ap.add_argument("--outdir", type=Path, default=ROOT / "output" / "pdf")
    ap.add_argument("--tmp", type=Path, default=ROOT / "tmp" / "sound-garden")
    a = ap.parse_args()
    a.tmp.mkdir(parents=True, exist_ok=True)
    a.outdir.mkdir(parents=True, exist_ok=True)

    base = SRC.resolve().as_uri()
    art_src = ART.resolve().as_uri() + "/"
    back = a.tmp / "back.png"
    render(f"{base}?back=1&c=yellow", back)
    for deck in (["art", "color"] if a.deck == "both" else [a.deck]):
        fronts = []
        for i, (title, color, sub) in enumerate(CARDS, 1):
            params = {"n": i, "t": title, "c": color, "s": sub, "deck": deck, "src": art_src}
            png = a.tmp / f"{deck}-{i:02d}.png"
            render(f"{base}?{urlencode(params)}", png)
            fronts.append(png)
            print("rendered", deck, i, title, file=sys.stderr)
        compose(fronts, back, a.outdir / f"sound-garden-cards-{deck}.pdf", deck)


def compose(fronts, back, out, deck):

    doc = fitz.open()
    for page_fronts in (fronts[:9], fronts[9:]):
        b = doc.new_page(width=W, height=H)
        for r in range(3):
            for c in range(3):
                b.insert_image(cell(r, c), filename=str(back))
        f = doc.new_page(width=W, height=H)
        for r in range(3):
            for c in range(3):
                f.insert_image(cell(r, c), filename=str(page_fronts[r * 3 + (2 - c)]))
    label = "Color Your Own" if deck == "color" else "Adventure Cards"
    doc.set_metadata({"title": f"Bee's Sound Garden {label} - Bees Keys"})
    doc.save(out, deflate=True)
    print(out, doc.page_count, "pages")


if __name__ == "__main__":
    main()
