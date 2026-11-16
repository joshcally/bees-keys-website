#!/bin/sh
# Rebuild everything for Bee's Friendsgiving: Missing Beats after a change to
# the sheets: sheets, cover, fan art, the three PDFs, the site JPGs, the OG card.
#     sh tools/build-missing-beats.sh
set -e
cd "$(dirname "$0")/.."
O=output/missing-beats
F=resources/files/bees-keys-bees-friendsgiving-missing-beats
C=$O/bees-keys-friendsgiving-missing-beats
N=$O/bees-keys-bees-dinner-missing-beats
SUB="A free printable rhythm worksheet: fill in the missing beats in 4/4 and 3/4"
KW="piano, rhythm worksheet, missing beats, 4/4, 3/4, quarter note, half note, Friendsgiving, free printable"
python3 tools/missing-beats-art/make-lineart.py >/dev/null
python3 tools/make-missing-beats-sheet.py >/dev/null
python3 tools/build-missing-beats-cover.py >/dev/null
python3 tools/build-missing-beats-cover.py --art images/resources/bees-friendsgiving-missing-beats-fan.png >/dev/null
python3 tools/combine-printable.py $O/missing-beats-cover.pdf $C-44-studio.pdf $C-44.pdf $C-34-studio.pdf $C-34.pdf \
  $N-44-studio.pdf $N-44.pdf $N-34-studio.pdf $N-34.pdf $F.pdf --lossless \
  --title "Bee's Friendsgiving: Missing Beats" --subject "$SUB" --keywords "$KW" | head -1
python3 tools/combine-printable.py $O/missing-beats-cover.pdf $C-44-studio.pdf $C-34-studio.pdf $N-44-studio.pdf $N-34-studio.pdf \
  $F-color.pdf --lossless --title "Bee's Friendsgiving: Missing Beats (Color)" --subject "$SUB" --keywords "$KW" | head -1
python3 tools/combine-printable.py $O/missing-beats-cover.pdf $C-44.pdf $C-34.pdf $N-44.pdf $N-34.pdf \
  $F-bw.pdf --lossless --title "Bee's Friendsgiving: Missing Beats (Printer-Friendly)" --subject "$SUB" --keywords "$KW, black and white" | head -1
python3 - <<'PY'
import fitz
from PIL import Image
d = fitz.open("resources/files/bees-keys-bees-friendsgiving-missing-beats.pdf")
for i, name in ((0, "cover"), (2, "studio"), (9, "dinner-printer")):
    pix = d[i].get_pixmap(dpi=384)   # supersampled: the cover's fan is tilted
    Image.frombytes("RGB", (pix.width, pix.height), pix.samples).resize((1056, 816), Image.LANCZOS) \
        .save(f"images/resources/bees-friendsgiving-missing-beats-{name}.jpg", quality=85)
PY
python3 -m http.server 8137 >/dev/null 2>&1 &
SRV=$!
sleep 1
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --headless=new --disable-gpu --hide-scrollbars \
  --window-size=1200,630 --virtual-time-budget=5000 \
  --screenshot=images/resources/bees-friendsgiving-missing-beats-og.png \
  http://localhost:8137/tools/og-card-bees-friendsgiving-missing-beats.html 2>&1 | tail -1
kill $SRV
