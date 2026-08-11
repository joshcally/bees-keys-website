#!/usr/bin/env python3
"""Join the printable's cover pages onto its worksheet pages, keeping the links.

The cover PDF carries live App Store links as PDF link annotations. Most "combine
PDF" tools (Preview's thumbnail drag, `sips`, anything that reprints the pages)
flatten those into dead pixels. Concatenating the page objects the way this does
carries the annotations across untouched.

    pip install pymupdf
    python3 tools/combine-printable.py cover.pdf worksheets.pdf out.pdf

It verifies the link count afterwards and fails loudly if any went missing, so a
silent regression can't ship.

The straight join lands at ~10 MB, which is a long download for a teacher on
school wifi. The pages are all full-bleed artwork stored lossless, so re-encoding
them as high-quality JPEG cuts that to ~3 MB with no difference visible at print
scale — that is the default. Pass --lossless to skip it. Anything already below
300 dpi is left at its own resolution; this never upsamples.
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


def combine(cover_path, worksheets_path, out_path, lossless=False):
    out = pymupdf.open()
    expected = []

    for path in (cover_path, worksheets_path):
        src = pymupdf.open(path)
        offset = len(out)
        # insert_pdf copies the page objects wholesale — annotations, and so the
        # link rectangles, ride along. links=True is the default; it is spelled
        # out here because it is the entire point of the script.
        out.insert_pdf(src, links=True, annots=True)
        expected += [(i + offset, uri) for i, uri in links_in(src)]
        src.close()

    out.set_metadata(
        {
            "title": "Meet the Piano Keys - Bees Keys Printables",
            "author": "Bees Keys",
            "subject": "7 beginner piano worksheets for learning the key names A-G",
            "keywords": "piano, worksheets, printable, note names, beginner, music teacher",
        }
    )
    if not lossless:
        # dpi_target only ever downsamples, so the 72 dpi worksheet scans keep
        # every pixel they have and only the 300 dpi cover art is capped.
        out.rewrite_images(dpi_target=300, quality=92)

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

    print(f"{out_path}: {pages} pages, {len(found)} links intact")
    for page, uri in found:
        print(f"  p{page + 1}  {uri}")
    return 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--lossless"]
    if len(args) != 3:
        sys.exit(__doc__)
    sys.exit(combine(*args, lossless="--lossless" in sys.argv))
