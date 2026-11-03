"""Run both classifiers over the crawled site.

Run:  python3 classify.py

1. Crawls the locally served site (same crawler as crawl_site.py).
2. Baseline: writes baseline_predictions.csv from filenames and alt text only.
3. AI review: matches each image (by SHA-256) to saved findings in ai_review/round_N/
   and writes ai_review.json with the 0.7 confidence rule. Images nobody has reviewed
   get "pending_review", and contact sheets for them are drawn in a new round.

It scores the ORIGINAL site, so it refuses to run once the site has been remediated
(use ./run_demo to start again from a fresh site).

The answer key stays locked for the whole run.
"""

from collections import Counter

from classifier.ai_review import review, write_ai_review
from classifier.baseline import run_baseline, write_baseline
from crawler import guard
from crawler.crawl import Crawler
from crawler.server import serve_site
from crawler.settings import SITE_DIR


def main():
    guard.install()
    if (SITE_DIR / ".remediated").exists():
        raise SystemExit("site/ has already been remediated; run ./run_demo to start from a fresh site.")
    with serve_site() as local_base:
        crawler = Crawler(local_base).crawl()

    baseline = run_baseline(crawler)
    write_baseline(baseline)
    rules = Counter(p.rule for p in baseline)
    print(f"Baseline: {sum(p.flagged for p in baseline)} of {len(baseline)} images flagged "
          f"({', '.join(f'{k} {v}' for k, v in sorted(rules.items()))})")

    images, pending_round = review(crawler)
    doc = write_ai_review(images)
    c = doc["counts"]
    print(f"AI review: {len(images)} images: outdated {c['outdated']}, not_outdated {c['not_outdated']}, "
          f"needs_review {c['needs_review']}, pending_review {c['pending_review']} "
          f"(threshold {doc['confidence_threshold']}); decoys flagged: "
          f"{sum(bool(i['is_decoy']) for i in images)}")
    if pending_round:
        print(f"Waiting for AI review: contact sheets are in {pending_round.relative_to(SITE_DIR.parent)}/sheets/")


if __name__ == "__main__":
    main()
