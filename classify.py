"""Run both classifiers over the crawled site.

Run:  python3 classify.py

1. Crawls the locally served site (same crawler as crawl_site.py).
2. Baseline: writes baseline_predictions.csv from filenames and alt text only.
3. AI review: writes the batch contact sheets to ai_review/sheets/, then, once a
   findings file exists for every batch in ai_review/findings/, merges them into
   ai_review.json and applies the 0.7 confidence rule.

The answer key stays locked for the whole run.
"""

from collections import Counter

from classifier.ai_batches import prepare
from classifier.ai_review import merge_findings, write_ai_review
from classifier.baseline import run_baseline, write_baseline
from crawler import guard
from crawler.crawl import Crawler
from crawler.server import serve_site


def main():
    guard.install()
    with serve_site() as local_base:
        crawler = Crawler(local_base).crawl()

    baseline = run_baseline(crawler)
    write_baseline(baseline)
    rules = Counter(p.rule for p in baseline)
    print(f"Baseline: {sum(p.flagged for p in baseline)} of {len(baseline)} images flagged "
          f"({', '.join(f'{k} {v}' for k, v in sorted(rules.items()))})")

    batches = prepare(crawler)
    print(f"AI review: {len(batches)} batches of up to 10 images; sheets in ai_review/sheets/")
    try:
        doc = write_ai_review(merge_findings())
    except FileNotFoundError as err:
        print(f"AI review not merged yet: {err}")
        return
    c = doc["counts"]
    print(f"AI review merged: {len(doc['images'])} images: outdated {c['outdated']}, "
          f"not_outdated {c['not_outdated']}, needs_review {c['needs_review']} "
          f"(threshold {doc['confidence_threshold']}); decoys flagged: "
          f"{sum(i['is_decoy'] for i in doc['images'])}")


if __name__ == "__main__":
    main()
