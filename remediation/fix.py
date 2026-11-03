"""Backs up and replaces every outdated image, then points the site's pages at the new files.

An image is replaced only when BOTH classifiers agree it shows the outdated persona:
the crawler's pixel detector (manifest.csv) and the AI review (ai_review.json). If only
one of them says so, or the AI review is unsure, the image is left alone and marked
needs_review for a person to decide.
"""

import csv
import hashlib
import json
import shutil

from crawler.settings import MANIFEST_CSV, PUBLIC_BASE, SITE_DIR
from classifier.ai_review import AI_REVIEW_JSON

from .design_tool import replace_persona
from .settings import (BACKUP_DIR, DOCS_SHOWING_ORIGINALS, NEW_SUFFIX, REMEDIATED_MARKER,
                       REMEDIATION_LOG)


def _sha(data):
    return hashlib.sha256(data).hexdigest()


def select_targets():
    """Split images into 'replace' (both classifiers agree) and 'needs_review' (they don't)."""
    with open(MANIFEST_CSV, newline="", encoding="utf-8") as f:
        manifest = list(csv.DictReader(f))
    ai = {i["asset_url"]: i for i in json.loads(AI_REVIEW_JSON.read_text(encoding="utf-8"))["images"]}
    crawler_says = {r["asset_url"]: r["status"] for r in manifest}
    shas = {r["asset_url"]: r["file_sha256"] for r in manifest}
    replace, review = [], []
    for url in sorted(crawler_says):
        detector = crawler_says[url] == "outdated"
        ai_status = ai.get(url, {}).get("status", "pending_review")
        if detector and ai_status == "outdated":
            replace.append(url)
        elif detector or ai_status in ("outdated", "needs_review", "pending_review"):
            review.append({"asset_url": url, "detector": crawler_says[url], "ai_status": ai_status})
    return replace, review, ai, shas


def _update_references(old_path, new_path):
    """Swap the old image path for the new one in every page's src and data-src attributes."""
    pages = []
    for html in sorted(SITE_DIR.glob("*/*.html")):
        text = html.read_text(encoding="utf-8")
        count = text.count(f'"../{old_path}"')
        if count:
            html.write_text(text.replace(f'"../{old_path}"', f'"../{new_path}"'), encoding="utf-8")
            pages.append({"page": html.relative_to(SITE_DIR).as_posix(), "references": count})
    return pages


def _relink_docs(old_paths):
    """gallery.md and gap_report.md show the ORIGINAL images. Replaced files now live in the
    backup folder, so point those documents there instead of at the deleted files."""
    for doc in DOCS_SHOWING_ORIGINALS:
        if not doc.exists():
            continue
        text = doc.read_text(encoding="utf-8")
        for old in old_paths:
            text = text.replace(f'"site/{old}"', f'"backups/originals/{old}"')
        doc.write_text(text, encoding="utf-8")


def remediate():
    if REMEDIATED_MARKER.exists():
        raise SystemExit("site/ is already remediated; run ./run_demo to start from a fresh site.")
    replace, review, ai, shas = select_targets()
    if BACKUP_DIR.exists():
        shutil.rmtree(BACKUP_DIR)  # leftovers from an earlier run of a different site

    entries = []
    for url in replace:
        old_path = url.replace(PUBLIC_BASE + "/", "")            # assets/en-US/team-01.png
        new_path = old_path[:-4] + NEW_SUFFIX + ".png"           # assets/en-US/team-01-v2.png
        old_file, new_file = SITE_DIR / old_path, SITE_DIR / new_path
        old_bytes = old_file.read_bytes()
        if _sha(old_bytes) != shas[url]:
            raise RuntimeError(f"{old_path} changed since it was crawled; refusing to touch it")

        # 1. Back up the original, and check the copy is identical.
        backup = BACKUP_DIR / old_path
        backup.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(old_file, backup)
        assert _sha(backup.read_bytes()) == shas[url], f"backup of {old_path} is not identical"

        # 2. Redraw with the approved persona (design-tool stand-in).
        observed, layout_match = replace_persona(old_bytes, old_path, ai[url].get("name_form_seen", ""),
                                                 new_file, BACKUP_DIR.parent / "_layout_check.png")
        # 3. Point every page at the new file, then remove the old one from the site.
        pages = _update_references(old_path, new_path)
        old_file.unlink()
        entries.append({
            "old_asset_url": url, "new_asset_url": f"{PUBLIC_BASE}/{new_path}",
            "backup_path": backup.relative_to(BACKUP_DIR.parent.parent).as_posix(),
            "old_sha256": shas[url], "new_sha256": _sha(new_file.read_bytes()),
            "observed": observed, "layout_check_passed": layout_match, "pages_updated": pages,
        })

    _relink_docs([e["old_asset_url"].replace(PUBLIC_BASE + "/", "") for e in entries])
    REMEDIATION_LOG.write_text(json.dumps({"replaced": entries, "needs_review": review},
                                          ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    REMEDIATED_MARKER.write_text("Remediated. See backups/remediation_log.json\n", encoding="utf-8")
    return entries, review
