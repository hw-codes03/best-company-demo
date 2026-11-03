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

## Crawl and compare with the client audit

```bash
python3 crawl_site.py
```

This serves `site/` on a local web server (127.0.0.1) and crawls it by following links,
starting from `sitemap.xml` and the home page. It reads image URLs from `src`, `data-src` and
`srcset`, downloads every image and hashes it with SHA-256. Each image is then checked for
the outdated persona's teal round avatar. It writes:

| Path | What it is |
|---|---|
| `manifest.csv` | Every (page, image) pair from the crawl and the audit: `asset_id, source, page_url, locale, asset_url, file_sha256, duplicate_group_id, status` |
| `gap_report.md` | What the audit missed, its false positives, its duplicate rows, and the pages missing from the sitemap |

`status` is what the detector saw: `outdated` (teal avatar), `approved` (orange avatar),
`other_person` (an avatar in another colour), `no_person` or `not_found`. Identical files
share a `duplicate_group_id`. A file that appears only once has none.

The crawler never reads `answer_key/`. A Python audit hook (`crawler/guard.py`) stops the
program if anything tries to open it, and the local server exposes only `site/`.

## Classify and evaluate

```bash
python3 classify.py
```

```bash
python3 evaluate.py
```

`classify.py` runs two classifiers over the crawled images (answer key locked):

- **Baseline** (`baseline_predictions.csv`): rules that use only filenames and alt text, never pixels.
- **AI review** (`ai_review.json`): an AI model looks at every picture in batches of 10, as labelled
  contact sheets in `ai_review/sheets/`. Its judgments for each batch are in `ai_review/findings/`.
  Each image records whether it contains the outdated persona (name in any locale form, email or
  avatar), whether it is a decoy, a confidence from 0 to 1 and short evidence. Code then sets
  `needs_review` for anything below 0.7.

`evaluate.py` is the only code that reads `answer_key/ground_truth.csv`. It scores the client
audit, the crawler, the baseline and the AI review (precision and recall per image file) and
writes `metrics.md` with a plain-English account of where each one failed.

## Code layout (`classifier/`)

| Module | Job |
|---|---|
| `baseline.py` | Filename and alt-text rules |
| `ai_batches.py` | Splits images into batches and draws the labelled contact sheets |
| `ai_review.py` | Merges per-batch findings into `ai_review.json`; applies the 0.7 rule |

## Code layout (`crawler/`)

| Module | Job |
|---|---|
| `settings.py` | Paths, public URL, and the persona facts from the client brief |
| `guard.py` | Blocks any file open under `answer_key/` |
| `server.py` | Serves `site/` on a free local port |
| `crawl.py` | Follows links; collects `src`, `data-src`, `srcset`; downloads and hashes images |
| `detect.py` | Finds round avatars in the pixels and classifies them by colour |
| `audit_reader.py` | Reads `client_audit.csv` |
| `manifest.py` | Merges crawl and audit into `manifest.csv`; groups identical files by hash |
| `gap_report.py` | Writes `gap_report.md` |

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
