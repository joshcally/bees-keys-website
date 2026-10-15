#!/usr/bin/env python3
"""Render and lay out the Rhythm Phrase Builders cards.

Four categories of nine poker-size cards (Creature / Action / Path / Place).
One card from each pile makes a sentence and a two-bar rhythm. Same
2.5x3.5 in cards and duplex page geometry as Find Every Key and Sound Garden.

    python3 tools/make-rhythm-phrase-cards.py [--only creature] [--bw]

--bw builds the printer-friendly deck instead: fronts only, white cards with
line-art creatures and places from tools/rhythm-phrase-art/bw/ (made by
tools/make-lineart.py), to output/pdf/rhythm-phrase-builders-bw.pdf.

Output: backs page then fronts page per category (columns mirrored on the
backs so a long-edge flip aligns).
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
SRC = ROOT / "tools" / "card-rhythm-phrase.html"

# category -> (accent, [(word, syllables, rhythm, art-or-doodle)])
# Rhythm codes: Q quarter, E eighth (beamed in pairs), H half, R quarter rest,
# _ a tie between the notes either side (EE_EE: the long sound on beat two's
# upbeat, for second-syllable words like a-CROSS the).
# Two beats per card. Creatures use the final Sound Garden art (the Sep 18
# *-drawn files), places use Kristianna's tiles in tools/rhythm-phrase-art/.
DECKS = {
    "creature": ("pink", [
        ("Spiders",      "Spi-ders",         "QQ",   "art=spider-drawn.png&g=0,100,255,255;222,0,255,255;445,100,255,255"),
        ("Bumblebees",   "Bum-ble-bees",     "EEQ",  "art=bee&g=30,130,230,230;250,0,250,250,1;470,140,210,210"),
        ("Grasshoppers", "Grass-hop-pers",   "QEE",  "art=grasshopper-drawn.png&g=10,30,350,310;400,130,260,230"),
        ("Ants",         "Ants",             "QR",   "art=ant.png&g=0,100,255,255;222,0,255,255;445,100,255,255"),
        ("Ladybugs",     "La-dy-bugs",       "EEQ",  "art=ladybug.png&g=50,50,320,290;410,150,220,200,1"),
        ("Caterpillars", "Ca-ter-pil-lars",  "EEEE", "art=caterpillar.png&g=20,40,330,300;350,40,330,300"),
        ("Fireflies",    "Fi-re-flies",      "EEQ",  "art=firefly-drawn.png&g=0,20,195,195;255,160,195,195;505,0,195,195"),
        ("Butterflies",  "But-ter-flies",    "EEQ",  "art=butterfly.png&g=60,20,330,300;430,160,210,190,1"),
        ("Crickets",     "Crick-ets",        "QQ",   "art=cricket-drawn.png&g=30,60,300,280;380,60,300,280,1"),
    ]),
    "action": ("orange", [
        ("flutter", "flut-ter", "EER", "doodle=loop"),
        ("crawl",   "crawl",    "H",  "doodle=humps"),
        ("hover",   "ho-ver",   "QQ", "doodle=hover"),
        ("jump",    "jump",     "QR", "doodle=arc"),
        ("march",   "march",    "H",  "doodle=chevrons"),
        ("scurry",  "scur-ry",  "EER", "doodle=zigzag"),
        ("glitter", "glit-ter", "QQ", "doodle=burst"),
        ("wiggle",  "wig-gle",  "QQ", "doodle=wave"),
        ("dance",   "dance",    "H",  "doodle=spiral"),
    ]),
    "path": ("yellow", [
        ("over the",   "o-ver the",   "EEQ", ""),
        ("under the",  "un-der the",  "EEQ", ""),
        ("through the","through the", "QQ",  ""),
        ("across the", "a-cross the", "EE_EE", ""),
        ("around the", "a-round the", "EE_EE", ""),
        ("near the",   "near the",    "QQ",  ""),
        ("beside the", "be-side the", "EE_EE", ""),
        ("on the",     "on the",      "QQ",  ""),
        ("in the",     "in the",      "QQ",  ""),
    ]),
    "place": ("green", [
        ("meadow",  "mea-dow",  "QQ", "art=../rhythm-phrase-art/meadow.png"),
        ("garden",  "gar-den",  "QQ", "art=../rhythm-phrase-art/garden.png"),
        ("flowers", "flow-ers", "QQ", "art=../rhythm-phrase-art/flowers.png"),
        ("grass",   "grass",    "H",  "art=../rhythm-phrase-art/grass.png"),
        ("leaves",  "leaves",   "H",  "art=../rhythm-phrase-art/leaves.png"),
        ("woods",   "woods",    "H",  "art=../rhythm-phrase-art/woods.png"),
        ("pond",    "pond",     "H",  "art=../rhythm-phrase-art/pond.png"),
        ("trail",   "trail",    "H",  "art=../rhythm-phrase-art/trail.png"),
        ("ground",  "ground",   "H",  "art=../rhythm-phrase-art/ground.png"),
    ]),
}

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
    ap.add_argument("--only", choices=list(DECKS), action="append")
    ap.add_argument("--no-backs", action="store_true")
    ap.add_argument("--syllables", action="store_true")
    ap.add_argument("--bw", action="store_true", help="printer-friendly deck, fronts only")
    ap.add_argument("--outdir", type=Path, default=ROOT / "output" / "pdf")
    ap.add_argument("--tmp", type=Path, default=ROOT / "tmp" / "rhythm-phrase")
    a = ap.parse_args()
    if a.bw:
        a.no_backs = True
    a.tmp.mkdir(parents=True, exist_ok=True)
    a.outdir.mkdir(parents=True, exist_ok=True)

    base = SRC.resolve().as_uri()
    art_src = ART.resolve().as_uri() + "/"
    doc = fitz.open()
    for cat, (color, cards) in DECKS.items():
        if a.only and cat not in a.only:
            continue
        assert len(cards) == 9, cat
        back = a.tmp / f"{cat}-back.png"
        if not a.no_backs:
            render(f"{base}?back=1&cat={cat}&c={color}", back)
        fronts = []
        for i, (word, syl, rhythm, art) in enumerate(cards, 1):
            params = {"w": word, "s": syl if a.syllables else "", "r": rhythm, "cat": cat, "c": color, "src": art_src}
            if a.bw:
                params["bw"] = "1"
            png = a.tmp / f"{'bw-' if a.bw else ''}{cat}-{i:02d}.png"
            render(f"{base}?{urlencode(params)}&{art}", png)
            fronts.append(png)
            print("rendered", cat, i, word, file=sys.stderr)
        if not a.no_backs:
            b = doc.new_page(width=W, height=H)
            for r in range(3):
                for c in range(3):
                    b.insert_image(cell(r, c), filename=str(back))
        # Fronts are mirrored to line up with a duplex backs page; with no
        # backs they read left to right.
        f = doc.new_page(width=W, height=H)
        for r in range(3):
            for c in range(3):
                k = r * 3 + c if a.no_backs else r * 3 + (2 - c)
                f.insert_image(cell(r, c), filename=str(fronts[k]))
    doc.set_metadata({"title": "Rhythm Phrase Builders" + (" (printer-friendly)" if a.bw else "") + " - Bees Keys"})
    out = a.outdir / ("rhythm-phrase-builders-bw.pdf" if a.bw else "rhythm-phrase-builders.pdf")
    doc.save(out, deflate=True)
    print(out, doc.page_count, "pages")


if __name__ == "__main__":
    main()
