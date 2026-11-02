"""Counts what was generated and prints the exact numbers.

Site counts are read back from the files on disk (HTML, PNG, sitemap), not taken from the
plan, so they show what was actually written.
"""

import csv
import re
from collections import Counter

from . import config


def _site_counts():
    html_files = sorted(config.SITE_DIR.glob("*/*.html"))
    png_files = sorted(config.SITE_DIR.rglob("*.png"))
    sitemap = (config.SITE_DIR / "sitemap.xml").read_text(encoding="utf-8")
    sitemap_urls = re.findall(r"<loc>(.*?)</loc>", sitemap)
    src_tags = data_src_tags = 0
    for f in html_files:
        for tag in re.findall(r"<img [^>]*>", f.read_text(encoding="utf-8")):
            if "data-src=" in tag:
                data_src_tags += 1
            else:
                src_tags += 1
    return html_files, png_files, sitemap_urls, src_tags, data_src_tags


def print_report(plan, audit_rows):
    html_files, png_files, sitemap_urls, src_tags, data_src_tags = _site_counts()
    hidden = [p for p in plan.pages if p.hidden]
    personas = Counter(a.persona_key or "none" for a in plan.images)
    reused = [a for a in plan.images if len(a.refs) > 1]
    outdated = [a for a in plan.images if a.persona_key == "jordan_vale"]
    kinds = Counter(r.kind for r in audit_rows)
    with open(config.CLIENT_AUDIT_CSV, encoding="utf-8") as f:
        audit_csv_rows = sum(1 for _ in csv.DictReader(f))
    caught = {r.image_path for r in audit_rows if r.kind == "true_positive"}

    print(f"Seed: {config.SEED}")
    print(f"Locales: {len(config.LOCALES)} ({', '.join(config.LOCALES)})")
    print(f"HTML pages written: {len(html_files)}")
    for loc in config.LOCALES:
        n = sum(1 for p in plan.pages if p.locale == loc)
        h = [p.slug for p in hidden if p.locale == loc]
        print(f"  {loc}: {n} pages" + (f" (footer-only: {', '.join(h)})" if h else ""))
    print(f"URLs in sitemap.xml: {len(sitemap_urls)} (footer-only pages left out: {len(hidden)})")
    print(f"<img> tags: {src_tags + data_src_tags} (src: {src_tags}, data-src: {data_src_tags})")
    print(f"Distinct PNG files on disk: {len(png_files)}")
    print(f"Files reused on more than one page: {len(reused)} "
          f"({sum(len(a.refs) for a in reused)} tags; "
          f"{sum(len(a.refs) - 1 for a in reused)} extra beyond the first use)")
    print("Image files by person shown:")
    print(f"  Jordan Vale (outdated, must replace): {personas['jordan_vale']}")
    print(f"  Priya Nair (approved, keep):          {personas['priya_nair']}")
    print(f"  Jordan Vail (decoy, keep):            {personas['jordan_vail']}")
    print(f"  No person (product images):           {personas['none']}")
    pages_by_path = {p.path: p for p in plan.pages}
    only_hidden = [a for a in outdated if all(pages_by_path[p].hidden for p, _ in a.refs)]
    only_lazy = [a for a in outdated if all(m == "data-src" for _, m in a.refs)]
    print(f"Outdated files only on footer-only pages: {len(only_hidden)}; "
          f"only lazy-loaded (data-src): {len(only_lazy)}")
    print(f"client_audit.csv rows: {audit_csv_rows} = {kinds['true_positive']} correct + "
          f"{kinds['false_positive']} false positives + {kinds['duplicate']} duplicates")
    print(f"Client audit recall: {len(caught)} of {len(outdated)} outdated files "
          f"({100 * len(caught) / len(outdated):.0f}%); missed: {len(outdated) - len(caught)}")
    print(f"ground_truth.csv rows: {len(plan.images)} (one per image file)")
