"""Crawl the local copy of the Best Company site and compare it with the client audit.

Run:  python3 crawl_site.py

Writes manifest.csv and gap_report.md, then prints exact counts. The answer key is
locked away for the whole run: any attempt to open it stops the program.
"""

from collections import Counter

from crawler import guard
from crawler.audit_reader import read_client_audit
from crawler.crawl import Crawler
from crawler.gap_report import write_gap_report
from crawler.manifest import build_manifest, write_manifest
from crawler.server import serve_site


def main():
    guard.install()                       # from here on, answer_key/ cannot be opened
    audit_rows = read_client_audit()
    with serve_site() as local_base:      # site/ on a local port, only while crawling
        crawler = Crawler(local_base).crawl()
        manifest = build_manifest(crawler, audit_rows)
    write_manifest(manifest)
    gaps = write_gap_report(crawler, audit_rows, manifest)

    pages = crawler.pages.values()
    sources = Counter(r.source for r in manifest)
    statuses = Counter(r.status for r in manifest)
    attrs = Counter(a for p in pages for _, a in p.images)
    groups = Counter(r.duplicate_group_id for r in manifest if r.duplicate_group_id)
    print(f"Pages crawled: {len(crawler.pages)} (in sitemap: {sum(p.in_sitemap for p in pages)}, "
          f"found only by following links: {len(gaps['hidden_pages'])})")
    print(f"Image uses found: {sum(attrs.values())} (src: {attrs['src']}, data-src: {attrs['data-src']})")
    print(f"Distinct image URLs: {len(crawler.assets)}; distinct contents by SHA-256: "
          f"{len({a.sha256 for a in crawler.assets.values()})}")
    print(f"manifest.csv rows: {len(manifest)} (both: {sources['both']}, crawler only: "
          f"{sources['crawler']}, client_audit only: {sources['client_audit']})")
    print("Detector status per row: " + ", ".join(f"{k} {v}" for k, v in sorted(statuses.items())))
    print(f"Duplicate groups (same hash, 2+ rows): {len(groups)} covering {sum(groups.values())} rows")
    print(f"Client audit rows read: {len(audit_rows)}")
    print(f"Outdated images the audit missed: {len(gaps['missed'])}")
    print(f"Audit false positives: {len(gaps['false_positives'])}")
    print(f"Audit duplicate rows: {len(gaps['exact_duplicates']) + len(gaps['same_file_rows'])} "
          f"({len(gaps['exact_duplicates'])} exact, {len(gaps['same_file_rows'])} same file from another page)")
    print(f"Identical pictures at different URLs: {len(gaps['same_content_groups'])} group(s)")
    print(f"Pages missing from sitemap: {len(gaps['hidden_pages'])}")


if __name__ == "__main__":
    main()
