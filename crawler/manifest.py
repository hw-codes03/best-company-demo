"""Merges the crawl and the client audit into one list: manifest.csv.

One row per (page, image) pair, whichever source found it:
  source = "crawler"       only the crawler found it
           "client_audit"  only the audit lists it
           "both"          both found it
Identical files (same SHA-256) share a duplicate_group_id; a file that appears only once
gets a blank group. status is what the detector saw in the image (see detect.py), or
"not_found" if the image could not be downloaded.
"""

import csv
from dataclasses import dataclass
from urllib.parse import urlsplit

from .detect import detect
from .settings import MANIFEST_CSV

COLUMNS = ["asset_id", "source", "page_url", "locale", "asset_url", "file_sha256",
           "duplicate_group_id", "status"]


@dataclass
class ManifestRow:
    asset_id: str
    source: str
    page_url: str
    locale: str
    asset_url: str
    file_sha256: str
    duplicate_group_id: str
    status: str
    load_attributes: str      # how the crawler saw it loaded (kept for the report, not the CSV)
    audit_rows: list          # client audit row numbers for this exact pair
    avatar_hex: str


def _locale(page_url):
    return urlsplit(page_url).path.strip("/").split("/")[0]


def build_manifest(crawler, audit_rows):
    # Every (page, image) pair the crawler saw, with the attribute(s) that loaded it.
    crawled = {}
    for page in crawler.pages.values():
        for img_url, attribute in page.images:
            crawled.setdefault((page.url, img_url), set()).add(attribute)

    audited = {}
    for r in audit_rows:
        audited.setdefault((r.page_url, r.image_url), []).append(r.row)

    detections = {}
    rows = []
    for key in sorted(set(crawled) | set(audited)):
        page_url, img_url = key
        asset = crawler.fetch_asset(img_url)  # already downloaded unless only the audit lists it
        if asset.data is None:
            status, hex_colour = "not_found", ""
        else:
            if asset.sha256 not in detections:
                detections[asset.sha256] = detect(asset.data)
            d = detections[asset.sha256]
            status, hex_colour = d.status, d.avatar_hex
        source = "both" if key in crawled and key in audited else (
            "crawler" if key in crawled else "client_audit")
        rows.append(ManifestRow(
            asset_id=f"AST-{len(rows) + 1:03d}", source=source, page_url=page_url,
            locale=_locale(page_url), asset_url=img_url, file_sha256=asset.sha256 or "",
            duplicate_group_id="", status=status,
            load_attributes="+".join(sorted(crawled.get(key, []))),
            audit_rows=audited.get(key, []), avatar_hex=hex_colour))

    # Group identical files by hash; only hashes used by two or more rows get a group id.
    counts = {}
    for r in rows:
        if r.file_sha256:
            counts[r.file_sha256] = counts.get(r.file_sha256, 0) + 1
    group_ids = {}
    for r in rows:
        if counts.get(r.file_sha256, 0) > 1:
            group_ids.setdefault(r.file_sha256, f"DUP-{len(group_ids) + 1:02d}")
            r.duplicate_group_id = group_ids[r.file_sha256]
    return rows


def write_manifest(rows):
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for r in rows:
            writer.writerow([getattr(r, c) for c in COLUMNS])
