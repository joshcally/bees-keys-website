#!/usr/bin/env python3
"""Insert (or update) the Google Analytics 4 tag on every published page.

Usage:
    python3 tools/add-analytics.py G-XXXXXXXXXX

Inserts the standard gtag.js snippet right after the viewport meta tag in
every *.html at the repo root and in resources/. Safe to re-run: a page
that already has the tag gets its measurement ID updated instead of a
second copy. Pages under tools/, output/ and tmp/ are not published and
are left alone.

GA4's Enhanced Measurement ("File downloads", on by default) turns clicks
on the .pdf links into file_download events, so nothing else is needed
to see which printables get downloaded most.
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
MARKER_START = "<!-- Google tag (gtag.js) -->"
MARKER_END = "<!-- /Google tag -->"

SNIPPET = """  {start}
  <script async src="https://www.googletagmanager.com/gtag/js?id={id}"></script>
  <script>
    window.dataLayer = window.dataLayer || [];
    function gtag(){{dataLayer.push(arguments);}}
    gtag('js', new Date());
    gtag('config', '{id}');
  </script>
  {end}
"""

VIEWPORT = re.compile(r'^[ \t]*<meta name="viewport"[^>]*>\s*\n', re.M)
EXISTING = re.compile(
    r"^[ \t]*" + re.escape(MARKER_START) + r".*?" + re.escape(MARKER_END) + r"\n",
    re.S | re.M,
)


def main() -> int:
    if len(sys.argv) != 2 or not re.fullmatch(r"G-[A-Z0-9]{6,12}", sys.argv[1]):
        print(__doc__)
        return 2
    gid = sys.argv[1]
    snippet = SNIPPET.format(start=MARKER_START, end=MARKER_END, id=gid)

    pages = sorted(ROOT.glob("*.html")) + sorted((ROOT / "resources").glob("*.html"))
    added = updated = 0
    for page in pages:
        html = page.read_text(encoding="utf-8")
        if EXISTING.search(html):
            new = EXISTING.sub(snippet, html, count=1)
            updated += new != html
        else:
            m = VIEWPORT.search(html)
            if not m:
                print(f"skip (no viewport meta): {page.relative_to(ROOT)}")
                continue
            new = html[: m.end()] + snippet + html[m.end():]
            added += 1
        if new != html:
            page.write_text(new, encoding="utf-8")
    print(f"{gid}: tag added to {added} pages, updated on {updated}, {len(pages)} pages scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main())
