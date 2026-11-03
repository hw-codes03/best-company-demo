# Gap report: client audit vs. full crawl

Synthetic data only. Best Company, its people and every `example.com` address are fictional.

The crawler served `site/` locally, followed every link and downloaded every image. It then compared what it found with the 20 rows of `client_audit.csv`.

| Measure | Count |
|---|---|
| Pages found by following links | 17 |
| Pages listed in `sitemap.xml` | 15 |
| Image uses found (page + image pairs) | 44 |
| Distinct image URLs | 40 |
| Distinct image contents (by SHA-256) | 39 |
| Image URLs showing the outdated persona | 20 |
| ...of which the client audit listed | 15 (75%) |
| **Outdated images the audit missed** | **5** |
| **Audit false positives** | **3** |
| **Audit duplicate rows** | **2** (1 exact, 1 same file from another page) |
| **Pages missing from the sitemap** | **2** |

## 1. Outdated images the client audit missed

**How this was found:** the detector checked every downloaded image for a round teal avatar (the outdated persona in the client brief). Any such image whose URL appears in no audit row is listed here. The reason column says what made each one easy to overlook.

| Preview | Image | Used on | Why it was easy to miss |
|---|---|---|---|
| <img src="backups/originals/assets/ar-SA/hero-15.png" width="240" alt="/assets/ar-SA/hero-15.png"> | `/assets/ar-SA/hero-15.png` | `/ar-SA/press-archive.html` (src) | only on a footer-only page that is missing from `sitemap.xml` |
| <img src="backups/originals/assets/ar-SA/quote-08.png" width="240" alt="/assets/ar-SA/quote-08.png"> | `/assets/ar-SA/quote-08.png` | `/ar-SA/team.html` (src) | a normal `<img src>` on a page in the sitemap; the audit simply missed it |
| <img src="backups/originals/assets/ar-SA/sig-14.png" width="240" alt="/assets/ar-SA/sig-14.png"> | `/assets/ar-SA/sig-14.png` | `/ar-SA/press-archive.html` (src) | only on a footer-only page that is missing from `sitemap.xml` |
| <img src="backups/originals/assets/ar-SA/team-16.png" width="240" alt="/assets/ar-SA/team-16.png"> | `/assets/ar-SA/team-16.png` | `/ar-SA/press-archive.html` (src) | only on a footer-only page that is missing from `sitemap.xml` |
| <img src="backups/originals/assets/en-US/quote-09.png" width="240" alt="/assets/en-US/quote-09.png"> | `/assets/en-US/quote-09.png` | `/en-US/news.html` (data-src) | only lazy-loaded: its real URL is in `data-src`, not `src` |

**Also worth knowing:** these files are in the audit, but they appear on more pages than it lists. Replacing the file fixes every page, so no extra work is needed. Just check those pages afterwards.

- `/assets/shared/sig-01.png` also appears on `/ar-SA/contact.html`
- `/assets/en-US/team-01.png` also appears on `/en-US/legacy-team.html`
- `/assets/ja-JP/hero-01.png` also appears on `/ja-JP/news.html`

## 2. Client audit false positives

**How this was found:** each audited image was downloaded and checked for the outdated persona's teal round avatar. These rows point at images that don't have one. The colour found is shown so you can see why. A round avatar with the same "JV" initials but a different colour is a different person, so replacing it would be a mistake.

| Preview | Audit row | Page | Image | What the image actually shows |
|---|---|---|---|---|
| <img src="site/assets/ar-SA/quote-13.png" width="240" alt="/assets/ar-SA/quote-13.png"> | 8 | `/ar-SA/contact.html` | `/assets/ar-SA/quote-13.png` | orange avatar: the approved persona (`#f28c28`) |
| <img src="site/assets/ar-SA/sig-12.png" width="240" alt="/assets/ar-SA/sig-12.png"> | 9 | `/ar-SA/contact.html` | `/assets/ar-SA/sig-12.png` | a round avatar in a different colour: someone else (`#6b5ba8`) |
| <img src="site/assets/en-US/quote-11.png" width="240" alt="/assets/en-US/quote-11.png"> | 18 | `/en-US/contact.html` | `/assets/en-US/quote-11.png` | a round avatar in a different colour: someone else (`#6b5ba8`) |

## 3. Duplicate rows in the client audit

**How this was found:** audit rows were grouped by page URL plus image URL (exact duplicates), then by image URL alone (the same file listed again from another page). Images were also grouped by SHA-256, which catches different URLs serving the very same picture.

**Exact duplicates** (same page, same image):

- Rows 3, 12: `/assets/ja-JP/hero-01.png` on `/ja-JP/index.html`

**Same file listed again from another page.** One replacement fixes all of them, so count it as one fix:

- Rows 4, 5: `/assets/en-US/team-01.png` (listed from `/en-US/about.html`, `/en-US/team.html`)

**Same picture at different URLs** (identical SHA-256). Not a duplicate row: each URL is a separate file to replace, but they can share one new image:

- `DUP-02`: `/assets/ar-SA/quote-01.png`, `/assets/ar-SA/quote-03.png` (audit rows 6, 14)

## 4. Pages missing from the sitemap

**How this was found:** the crawler started from every URL in `sitemap.xml` plus the home page, then followed every link on every page. Any page it reached that isn't in the sitemap is listed here, along with where its links sit in the HTML.

| Page | Linked from | Where the link is | Outdated images on it |
|---|---|---|---|
| `/ar-SA/press-archive.html` | 5 other pages: `/ar-SA/about.html`, `/ar-SA/contact.html`, `/ar-SA/index.html`, `/ar-SA/news.html`, `/ar-SA/team.html` | footer only | `/assets/ar-SA/sig-14.png`, `/assets/ar-SA/hero-15.png`, `/assets/ar-SA/team-16.png` |
| `/en-US/legacy-team.html` | 5 other pages: `/en-US/about.html`, `/en-US/contact.html`, `/en-US/index.html`, `/en-US/news.html`, `/en-US/team.html` | footer only | `/assets/en-US/team-01.png` |
