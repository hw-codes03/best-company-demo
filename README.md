# best-company-demo

A synthetic test website for **Best Company** (`bestcompany.example.com`), a fictional brand.
It's used to test finding and replacing an outdated persona in images. Everything is made
up: the brand, the people, and every email (all `@example.com`).

## The scenario

The site's images still show an **outdated persona**, Jordan Vale (`jordan.vale@example.com`,
teal avatar "JV"). They must be replaced by the **approved persona**, Priya Nair
(`priya.nair@example.com`, orange avatar "PN"). The client's own audit is incomplete.

## Generate

Needs Python 3.11+ and Pillow with Raqm (for Arabic shaping), plus the DejaVu and IPA Gothic fonts.

```bash
python3 generate.py
```

The seed is fixed (`SEED` in `sitegen/config.py`), so every run writes byte-identical files.

## What you get

| Path | What it is |
|---|---|
| `site/` | The fake website: 3 locales (en-US, ja-JP, ar-SA right-to-left), 17 HTML pages, 40 PNG images, `sitemap.xml` |
| `client_audit.csv` | The client's audit: finds 15 of 20 outdated images (75%), plus 3 false positives and 2 duplicate rows |
| `answer_key/ground_truth.csv` | **Hidden answer key.** The true status of all 40 images. A detection pipeline must never read it |
| `gallery.md` | A 12-image sample you can view on GitHub |

## Traps seeded in the site

- **Footer-only pages**: `en-US/legacy-team.html` and `ar-SA/press-archive.html` are linked only from the footer and missing from `sitemap.xml`.
- **Lazy loading**: 8 `<img>` tags keep the real URL in `data-src`, not `src`.
- **Reused files**: 3 image files appear on several pages (one is shared across en-US and ar-SA).
- **Decoys**: 5 images show Jordan Vail, a different person with the same "JV" initials, a purple avatar and `jordan.vail@example.com`. They must not be replaced.
- **Locale name forms**: Japanese and Arabic images write the name in katakana or Arabic script, sometimes with the Latin name in brackets.

## Code layout (`sitegen/`)

| Module | Job |
|---|---|
| `config.py` | Seed, brand, paths, locales, fonts |
| `personas.py` | The three people and their name forms per locale |
| `strings.py` | All translated text |
| `render.py` | Draws the PNG images (mirrored for right-to-left) |
| `plan.py` | Decides pages, images and traps in memory |
| `site.py` | Writes HTML pages and `sitemap.xml` |
| `audit.py` | Writes `client_audit.csv` |
| `answer_key.py` | Writes `answer_key/ground_truth.csv` |
| `gallery.py` | Writes `gallery.md` |
| `report.py` | Prints exact counts |
