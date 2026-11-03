# best-company-demo

A synthetic test of finding and replacing an outdated persona in website images. Best Company
(`bestcompany.example.com`), its people and every `example.com` email are fictional.

**The task:** Jordan Vale (teal "JV" avatar) must become Priya Nair (orange "PN") everywhere,
without touching look-alike decoys (Jordan Vail, purple "JV").

## Run everything

```bash
./run_demo
```

Needs Python 3.11+, Pillow with Raqm, numpy, and the DejaVu and IPA Gothic fonts. The seed is fixed, so every run gives the same output.

## Steps and results

| Step | Output |
|---|---|
| Generate the site: 3 locales, 17 pages, 40 images | `site/`, `gallery.md` |
| Crawl by following links, compare with the client audit | `manifest.csv`, `gap_report.md` |
| Classify: filename/alt-text baseline, batched AI review | `baseline_predictions.csv`, `ai_review.json` |
| Score against the hidden answer key | `metrics.md` |
| Back up and replace outdated images | `backups/`, `dev_handoff.csv` |
| Re-audit the fixed site | `reaudit_report.md`, `before_after.md` |

Only `evaluate.py` reads `answer_key/`. Every other step runs with a lock that blocks it.
The AI review's saved judgments live in `ai_review/round_N/` and are matched to images by SHA-256.
