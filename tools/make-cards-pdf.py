"""Compose the Find Every Key print-and-cut card sheet.

Two US Letter pages, nine poker-size cards (2.5x3.5in) per page:
page 1 is nine copies of the cover, page 2 the FIND EVERY letter cards
(C-B plus two letterless wilds). Page 2's columns are mirrored so each
back lands behind its front when printed double-sided with a long-edge
flip.

Render the inputs first with headless Chrome (see the header comments in
tools/card-cover-find-every-key.html and tools/card-letter-find-every.html),
then:

    python3 tools/make-cards-pdf.py <cover.png> <letters-dir> <out.pdf>

where <letters-dir> holds letter-C.png ... letter-B.png and letter-wild.png.
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

p1 = doc.new_page(width=W, height=H)
for r in range(3):
    for c in range(3):
        p1.insert_image(cell(r, c), filename=cover)

letters = [["C", "D", "E"], ["F", "G", "A"], ["B", "wild", "wild"]]
p2 = doc.new_page(width=W, height=H)
for r in range(3):
    for c in range(3):
        name = letters[r][2 - c]
        p2.insert_image(cell(r, c), filename=f"{letters_dir}/letter-{name}.png")

doc.set_metadata({"title": "Find Every Key - Bees Keys Cards"})
doc.save(out, deflate=True)
print(out, doc.page_count, "pages")
