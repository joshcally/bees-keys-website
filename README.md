# beeskeysapp.com

The Bees Keys landing page. Static HTML/CSS, no build step, deployed by GitHub Pages
straight from the default branch — the same setup as `krissy-website`.

## Files

```
index.html        the whole page
styles.css        all styles
privacy.html      privacy policy (linked from the App Store listing)
terms.html        terms of use
resources.html    index of the free printables
resources/        one page per printable, plus resources/files/*.pdf
CNAME             custom domain, beeskeysapp.com
robots.txt        allows everything, points at the sitemap
sitemap.xml       hand-maintained; add a line when a page is added
images/           art copied from the app asset catalogs
tools/og-card.html           source for the link-preview image
tools/og-card-<slug>.html    same, one per printable page
tools/ig-card-<slug>.html    source for the Instagram post, rendered the same way
tools/combine-printable.py   joins a printable's cover onto its worksheets
tools/trace-cutout-edge.py   draws a gold edge along a cutout's alpha boundary
```

`images/pro-piano.webp` is the studio photo in the Pro section — an iPad running
Live on a real piano, which is the section's whole claim. It is a WebP because
the same image as PNG is 870 KB against 78 KB, and it is a cutout on
transparency so the section's gradient shows through. Its ragged removal edge is
covered by a gold trace from `tools/trace-cutout-edge.py`.

## The link-preview image

`images/og-card.png` is what shows up when the site is shared in iMessage,
Discord, Facebook, or Slack. It is rendered from `tools/og-card.html`, not drawn
by hand:

```sh
python3 -m http.server 8000
"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" \
  --headless=new --disable-gpu --hide-scrollbars --window-size=1200,630 \
  --virtual-time-budget=5000 --screenshot=images/og-card.png \
  http://localhost:8000/tools/og-card.html
```

It has to stay **1200x630**. The cards are `summary_large_image`, which
centre-crops anything squarer, and `og:image` has to be an absolute
`https://beeskeysapp.com/...` URL or the scrapers won't fetch it. If you change
the hero, re-render this so the two don't drift apart.

## Free resources

`resources.html` lists the printables; each one gets its own page under
`resources/`, with the PDF beside it in `resources/files/`. The per-resource page
exists so a teacher arriving from a search lands on something that can explain
the printable and point at the app — a bare PDF is a dead end.

Downloads are **ungated**: no email, no form, no third-party script. That is what
`privacy.html` promises, so keep it that way unless the policy changes with it.

### Adding a printable

1. Drop the PDF in `resources/files/`, named for its URL slug.
2. Render previews from it (cover plus a page or two) into `images/resources/`,
   at 1056x816 — 96 dpi of a landscape US Letter page, which is what the pages
   size their `<img>` at.
3. Copy `resources/groups-of-black-keys.html` as the starting point, and add a
   `.res-card` to the list in `resources.html`. **New printables go at the top**
   — most visitors arrive from a link to the latest one shared in a teacher
   group, so the newest leads.
4. Render a link-preview card from a copy of an existing `tools/og-card-<slug>.html`.

Leave `index.html` alone. The `#freebies` column there shows **one** printable
as a door to `resources.html` — it is not a second copy of the list, and it
doesn't grow as printables are added.

### Combining a cover with worksheets

The cover PDF carries live App Store links as annotations. Dragging pages
together in Preview flattens them into dead pixels. Use the script instead — it
verifies the links survived and fails if they didn't:

```sh
pip install pymupdf
python3 tools/combine-printable.py cover.pdf worksheets.pdf \
  resources/files/bees-keys-groups-of-black-keys.pdf \
  --title "Groups of Black Keys"
```

It re-encodes the page artwork as JPEG rather than storing it lossless, which is
worth roughly a third of the file. `--lossless` skips that.

`--title` is required — it sets the PDF's own metadata title, which is what a
reader's tab and print dialog show. `--subject` and `--keywords` are optional.

The worksheet masters in `~/Downloads` are 300 dpi (3300x2550 px per landscape
11x8.5in page). The **published copies are built at 200 dpi** with `--dpi 200`,
which took the 16-page set from ~12 MB to ~7 MB with no difference visible at
print scale — both measure a 2px edge transition, against 6px for the old
72 dpi set. Most of the traffic arrives from Facebook groups on phones, so the
download size matters more than the last 100 dpi.

Rebuild from the masters, never from the published copy:

```sh
python3 tools/combine-printable.py cover.pdf worksheets-300dpi.pdf \
  resources/files/bees-keys-groups-of-black-keys.pdf \
  --title "Groups of Black Keys" --dpi 200
```

Drop `--dpi` for the full 300 dpi build. Note that `rewrite_images(dpi_target=...)`
looks like it should resize and does not — it will not re-downsample images it
has already re-encoded, and reports success either way.

> Procreate bakes resolution in at canvas creation and cannot add it later, so
> a redraw has to start from a canvas set to 300 dpi.

## Design language

The palette follows the **App Store creatives**, not the in-app screens: sky blue
fading to a golden sunrise over a green meadow, near-black headlines with a
forest-green accent word, and gold honeycomb hexagons. Circles are avoided —
hexagons are the brand shape (`--hex` holds the app's `Hexagon` path as a clip
path). Amatic SC is retired; everything is Nunito, with headings separated by
weight rather than typeface.

## Local preview

```sh
python3 -m http.server 8000
# then open http://localhost:8000
```

## Deploying

Push to the default branch. In **Settings → Pages**, set the source to that branch
(root). The `CNAME` file keeps the custom domain bound across deploys — don't delete
it.

DNS for `beeskeysapp.com` needs the four GitHub Pages A records:

```
185.199.108.153
185.199.109.153
185.199.110.153
185.199.111.153
```

...plus a `CNAME` record for `www` → `<user>.github.io`. Enable **Enforce HTTPS**
once the certificate finishes provisioning.

## Images

`images/` is copied by hand from `BeesKeys/BeesKeys/assets/Assets.xcassets`. The bee
is three separate layers (`bee-body.svg`, `back-wing.svg`, `front-wing.svg`) so the
wings can flap independently in CSS, the same way they animate in the app. If the
app's art changes, re-copy them.

## Copy that must stay true

Numbers on the page come from `BeesKeys/business-analysis.md` and should be updated
when it is:

- **25,000+ downloads** — all-time, as of May 2026
- **4.6 from 500+ ratings** — US App Store (matches the App Store creatives)
- **16 languages** — matches the shipped `.lproj` localizations

The page does **not** advertise "no in-app purchases" (Bees Keys Pro is a paid
unlock) and does **not** quote user reviews — it links to the App Store listing
instead, so the social proof stays real without anyone maintaining testimonials.

`privacy.html` and `terms.html` are the **same text the app ships** in
`BeesKeys/Views/Live/HelpOverlay.swift` (`Self.privacyPolicy` / `Self.terms`).
If you change one, change the other, or the app and the site will disagree.
