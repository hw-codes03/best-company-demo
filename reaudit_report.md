# Re-audit report: after replacing the outdated persona

Synthetic data only. Best Company, its people and every `example.com` address are fictional.

After the fix, the site was served locally again, crawled by following every link, and re-checked by the pixel detector and the AI review. AI findings are matched by file fingerprint (SHA-256), so unchanged images kept their first review and only the new images were reviewed again.

## Results

- **Outdated images remaining:** **0** (target 0) ✅
- **Decoys wrongly changed:** **0** (target 0) ✅ (checked 5 decoys: same URL, same bytes, same pages)
- **Other untouched images changed:** **0** (target 0) ✅ (checked 15 approved-persona and product images)
- **Old files still served:** **0** (target 0) ✅ (every replaced image's old URL now returns 404)
- **Pages still pointing at an old file:** **0** (target 0) ✅

## Before and after

| Measure | Before | After |
|---|---|---|
| Pages crawled | 17 | 17 |
| Image uses (page + image) | 44 | 44 |
| Distinct image files | 40 | 40 |
| Outdated persona, per pixel detector | 20 | 0 |
| Outdated persona, per AI review | 20 | 0 |
| Approved persona, per pixel detector | 6 | 26 |
| Decoys, per AI review | 5 | 5 |
| No person (product images) | 9 | 9 |
| AI review: needs_review | 0 | 0 |
| Baseline flagged (filenames and alt text only) | 31 | 31 |

**What changed:** 20 image files were backed up to `backups/originals/` and redrawn with the approved persona. 24 `src`/`data-src` references were updated across 16 pages, and the old files were removed from the site. 0 image(s) were left for human review because the classifiers disagreed.

**Why the baseline doesn't move:** filenames and alt text still say *a person is pictured*. It can't tell the old persona from the new one, so it can't confirm the fix. That takes looking at the pixels.

## Developer handoff (`dev_handoff.csv`)

24 rows, one per page that showed an outdated image: 24 `replaced_verified`. `replaced_verified` means the page now loads the new file, no longer loads the old one, and both the pixel detector and the AI review see the approved persona in it.
