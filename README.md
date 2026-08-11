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
images/           art copied from the app asset catalogs
tools/og-card.html           source for the link-preview image
tools/og-card-resource.html  same, for the printable's page
tools/combine-printable.py   joins a printable's cover onto its worksheets
```

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
2. Render previews from it (cover plus a page or two) into `images/resources/`.
3. Copy `resources/meet-the-piano-keys.html` as the starting point, and add a
   `.res-card` to the list in `resources.html`.
4. Render a link-preview card from a copy of `tools/og-card-resource.html`.

### Combining a cover with worksheets

The cover PDF carries live App Store links as annotations. Dragging pages
together in Preview flattens them into dead pixels. Use the script instead — it
verifies the links survived and fails if they didn't:

```sh
pip install pymupdf
python3 tools/combine-printable.py cover.pdf worksheets.pdf \
  resources/files/bees-keys-meet-the-piano-keys.pdf
```

It re-encodes the page artwork as high-quality JPEG, which takes the current set
from ~10 MB to ~3 MB with no difference visible at print scale. `--lossless`
skips that.

> **Known issue:** the worksheet pages in the current set are 72 dpi — screen
> resolution, not print resolution — so they print noticeably soft. The cover is
> a proper 300 dpi. Re-export the worksheets at 300 dpi and re-run the script.

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
