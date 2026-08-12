#!/usr/bin/env python3
"""Join the printable's cover pages onto its worksheet pages, keeping the links.

The cover PDF carries live App Store links as PDF link annotations. Most "combine
PDF" tools (Preview's thumbnail drag, `sips`, anything that reprints the pages)
flatten those into dead pixels. Concatenating the page objects the way this does
carries the annotations across untouched.

    pip install pymupdf
    python3 tools/combine-printable.py cover.pdf worksheets.pdf out.pdf
    python3 tools/combine-printable.py cover.pdf worksheets.pdf out.pdf --dpi 200

It verifies the links afterwards and fails loudly if any went missing, so a
silent regression can't ship.

Every page is full-bleed artwork, so the file is essentially 16 photographs and
its size is decided by resolution. Two levers, in order of effect:

  --dpi N     re-render the worksheet pages at N dpi. This is the real lever.
              The source art is 300 dpi (3300x2550 per page); 200 dpi lands near
              7 MB against 12, and stays well above what a home printer resolves.
              The cover pages are never re-rendered — they carry the links, and
              rasterising them would flatten those into dead pixels.
  --quality Q JPEG quality, default 92. Worth far less than --dpi; dropping to
              85 saves about a tenth and starts to show on the flat colour.

Note that `rewrite_images(dpi_target=...)` looks like it should do the resizing
and does not: it will not re-downsample images it has already re-encoded, and
reports success either way. The pages have to be re-rendered and re-inserted as
JPEG streams, which is what --dpi does.

Pass --lossless to skip all re-encoding and keep the source bytes.
"""

import sys

import pymupdf


def links_in(doc):
    """Every URI link in the document, as (page index, url)."""
    return [
        (i, l["uri"])
        for i, page in enumerate(doc)
        for l in page.get_links()
        if l.get("uri")
    ]


def combine(cover_path, worksheets_path, out_path, lossless=False, dpi=None, quality=92):
    out = pymupdf.open()
    expected = []

    # The cover always goes in as real page objects so its link annotations
    # survive. It leads the document: two preview pages, then the worksheets.
    cover = pymupdf.open(cover_path)
    out.insert_pdf(cover, links=True, annots=True)
    expected += links_in(cover)
    offset = len(cover)
    cover.close()

    sheets = pymupdf.open(worksheets_path)
    if dpi:
        # Re-render each worksheet at the target resolution. Safe here only
        # because the worksheets carry no links or text to lose — they are
        # single full-page bitmaps already.
        for page in sheets:
            pix = page.get_pixmap(dpi=dpi)
            new = out.new_page(width=page.rect.width, height=page.rect.height)
            new.insert_image(
                new.rect,
                stream=pix.tobytes("jpeg", jpg_quality=quality),
                keep_proportion=False,
            )
    else:
        out.insert_pdf(sheets, links=True, annots=True)
        expected += [(i + offset, uri) for i, uri in links_in(sheets)]
    sheets.close()

    out.set_metadata(
        {
            "title": "Meet the Piano Keys - Bees Keys Printables",
            "author": "Bees Keys",
            "subject": "7 beginner piano worksheets for learning the key names A-G",
            "keywords": "piano, worksheets, printable, note names, beginner, music teacher",
        }
    )
    if not lossless:
        # Squashes the cover's lossless artwork. Worksheets rendered by --dpi are
        # already JPEG at the requested quality; this leaves their size alone.
        out.rewrite_images(quality=quality)

    # garbage=4 dedupes the objects the two files share; deflate re-compresses
    # the streams.
    out.save(out_path, garbage=4, deflate=True)
    out.close()

    check = pymupdf.open(out_path)
    found = links_in(check)
    pages = len(check)
    check.close()

    if found != expected:
        print("LINKS DID NOT SURVIVE THE MERGE", file=sys.stderr)
        print(f"  expected: {expected}", file=sys.stderr)
        print(f"  found:    {found}", file=sys.stderr)
        return 1

    detail = f" at {dpi} dpi" if dpi else ""
    print(f"{out_path}: {pages} pages{detail}, {len(found)} links intact")
    for page, uri in found:
        print(f"  p{page + 1}  {uri}")
    return 0


def main(argv):
    opts = {"lossless": False, "dpi": None, "quality": 92}
    args = []
    i = 0
    while i < len(argv):
        a = argv[i]
        if a == "--lossless":
            opts["lossless"] = True
        elif a in ("--dpi", "--quality"):
            if i + 1 >= len(argv):
                sys.exit(f"{a} needs a value")
            opts[a[2:]] = int(argv[i + 1])
            i += 1
        else:
            args.append(a)
        i += 1

    if len(args) != 3:
        sys.exit(__doc__)
    return combine(*args, **opts)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
