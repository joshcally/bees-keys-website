"""Compose the Find Every Key print-and-cut card sheet.

Six US Letter pages, nine poker-size cards (2.5x3.5in) per page, in
front/back pairs for double-sided printing: covers then naturals (C-B),
covers then sharps, covers then flats, with letterless wilds filling
spare slots. Each letter page's columns are mirrored so every back lands
behind its front on a long-edge flip.

Render the inputs first with headless Chrome (see the header comments in
tools/card-cover-find-every-key.html and tools/card-letter-find-every.html),
then:

    python3 tools/make-cards-pdf.py <cover.png> <letters-dir> <out.pdf>

where <letters-dir> holds letter-<X>.png for X in C..B, Cs Ds Fs Gs As,
Db Eb Gb Ab Bb, and wild.
"""
import sys
import fitz

cover, letters_dir, out = sys.argv[1:4]

W, H = 612, 792            # US Letter, points
CW, CH = 180, 252          # 2.5 x 3.5 inches
MX, MY = (W - 3*CW) / 2, (H - 3*CH) / 2

doc = fitz.open()

def cell(r, c):
    return fitz.Rect(MX + c*CW, MY + r*CH, MX + (c+1)*CW, MY + (r+1)*CH)

PAGES = [
    [["C", "D", "E"], ["F", "G", "A"], ["B", "wild", "wild"]],
    [["Cs", "Ds", "Fs"], ["Gs", "As", "wild"], ["wild", "wild", "wild"]],
    [["Db", "Eb", "Gb"], ["Ab", "Bb", "wild"], ["wild", "wild", "wild"]],
]

for letters in PAGES:
    front = doc.new_page(width=W, height=H)
    for r in range(3):
        for c in range(3):
            front.insert_image(cell(r, c), filename=cover)
    back = doc.new_page(width=W, height=H)
    for r in range(3):
        for c in range(3):
            name = letters[r][2 - c]
            back.insert_image(cell(r, c), filename=f"{letters_dir}/letter-{name}.png")

doc.set_metadata({"title": "Find Every Key - Bees Keys Cards"})
doc.save(out, deflate=True)
print(out, doc.page_count, "pages")
