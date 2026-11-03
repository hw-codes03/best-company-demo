"""Re-audits the fixed site: crawls and classifies it again, then writes dev_handoff.csv,
reaudit_report.md and before_after.md.

Checks, in plain English:
  - Outdated images remaining: any image on the fixed site that the pixel detector or the
    AI review still calls outdated (or that the AI review is unsure about). Target: zero.
  - Old files still live: every replaced image's old URL should now return "not found".
  - Decoys wrongly changed: every image the first AI review called a decoy must still be at
    the same URL, with the same bytes, on the same pages. Target: zero.
  - Other images changed: the same check for every image that was not a replacement target.
"""

import csv
import json
from collections import Counter

from classifier.ai_review import AI_REVIEW_JSON, review, write_ai_review
from classifier.baseline import BASELINE_CSV, run_baseline, write_baseline
from crawler.crawl import Crawler
from crawler.manifest import build_manifest, write_manifest
from crawler.server import serve_site
from crawler.settings import MANIFEST_CSV, PUBLIC_BASE

from .settings import (BEFORE_AFTER_MD, DEV_HANDOFF_CSV, REAUDIT_DIR, REAUDIT_REPORT_MD,
                       REMEDIATION_LOG)


def _short(url):
    return url.replace(PUBLIC_BASE, "")


def _read_csv(path):
    with open(path, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


class Before:
    """What the pipeline knew about the original site (its own outputs, not the answer key)."""

    def __init__(self):
        self.manifest = _read_csv(MANIFEST_CSV)
        self.ai = json.loads(AI_REVIEW_JSON.read_text(encoding="utf-8"))["images"]
        self.baseline = _read_csv(BASELINE_CSV)
        self.log = json.loads(REMEDIATION_LOG.read_text(encoding="utf-8"))
        self.crawled = [r for r in self.manifest if r["source"] != "client_audit"]
        self.sha = {r["asset_url"]: r["file_sha256"] for r in self.crawled}
        self.pages_of = {}
        for r in self.crawled:
            self.pages_of.setdefault(r["asset_url"], set()).add(r["page_url"])
        self.replaced = {e["old_asset_url"]: e for e in self.log["replaced"]}
        self.decoys = sorted(i["asset_url"] for i in self.ai if i["is_decoy"])


class After:
    """A fresh crawl and classification of the fixed site."""

    def __init__(self, crawler):
        self.crawler = crawler
        self.manifest = build_manifest(crawler, [])
        self.baseline = run_baseline(crawler)
        self.ai, self.pending_round = review(crawler)
        self.sha = {u: a.sha256 for u, a in crawler.assets.items()}
        self.pages_of = {}
        for r in self.manifest:
            self.pages_of.setdefault(r.asset_url, set()).add(r.page_url)
        self.detector = {r.asset_url: r.status for r in self.manifest}
        self.ai_by_url = {i["asset_url"]: i for i in self.ai}

    def write(self):
        write_manifest(self.manifest, REAUDIT_DIR / "manifest_after.csv")
        write_baseline(self.baseline, REAUDIT_DIR / "baseline_after.csv")
        write_ai_review(self.ai, REAUDIT_DIR / "ai_review_after.json")


def _old_url_status(crawler, url):
    return crawler._fetch(url)[0]


def analyse(before, after):
    still_outdated = sorted(u for u in after.sha if after.detector.get(u) == "outdated"
                            or after.ai_by_url[u]["status"] in ("outdated", "needs_review"))
    pending = sorted(u for u in after.sha if after.ai_by_url[u]["status"] == "pending_review")
    old_live = sorted(u for u in before.replaced if _old_url_status(after.crawler, u) != 404)
    old_referenced = sorted(u for u in before.replaced if u in after.pages_of)

    def changed(url):
        return (url not in after.sha or after.sha[url] != before.sha[url]
                or after.pages_of.get(url, set()) != before.pages_of[url])

    decoys_changed = [u for u in before.decoys if changed(u)]
    others = [u for u in before.sha if u not in before.replaced and u not in before.decoys]
    others_changed = [u for u in others if changed(u)]
    return {"still_outdated": still_outdated, "pending": pending, "old_live": old_live,
            "old_referenced": old_referenced, "decoys_changed": decoys_changed,
            "others": others, "others_changed": others_changed}


def handoff_rows(before, after):
    """One row per page that showed an outdated image, saying what was done there."""
    rows = []
    review_urls = {r["asset_url"] for r in before.log["needs_review"]}
    for r in before.crawled:
        url = r["asset_url"]
        if url not in before.replaced and url not in review_urls:
            continue
        entry = before.replaced.get(url)
        new_url = entry["new_asset_url"] if entry else ""
        if not entry:
            status = "needs_review"
        else:
            on_page = r["page_url"] in after.pages_of.get(new_url, set())
            old_gone = r["page_url"] not in after.pages_of.get(url, set())
            ai_status = after.ai_by_url.get(new_url, {}).get("status")
            clean = after.detector.get(new_url) == "approved" and ai_status == "not_outdated"
            if ai_status == "pending_review":
                status = "replaced_pending_ai_review"
            elif on_page and old_gone and clean:
                status = "replaced_verified"
            else:
                status = "replaced_not_verified"
        rows.append({"asset_id": r["asset_id"], "page_url": r["page_url"], "locale": r["locale"],
                     "old_asset_url": url, "new_asset_url": new_url, "status": status})
    return rows


def write_handoff(rows):
    cols = ["asset_id", "page_url", "locale", "old_asset_url", "new_asset_url", "status"]
    with open(DEV_HANDOFF_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=cols)
        writer.writeheader()
        writer.writerows(rows)


def _count(items, key, value):
    return sum(1 for i in items if key(i) == value)


def write_report(before, after, a, handoff):
    b_det = Counter(r["status"] for r in {r["asset_url"]: r for r in before.crawled}.values())
    a_det = Counter(after.detector.values())
    b_ai, a_ai = Counter(i["status"] for i in before.ai), Counter(i["status"] for i in after.ai)
    refs = sum(p["references"] for e in before.log["replaced"] for p in e["pages_updated"])
    status_counts = Counter(r["status"] for r in handoff)

    def target(n, pending=0):
        if pending:
            return f"**{n}** (target 0), with {pending} image(s) still awaiting AI review"
        return f"**{n}** (target 0) ✅" if n == 0 else f"**{n}** (target 0) ❌"

    lines = [
        "# Re-audit report: after replacing the outdated persona",
        "",
        "Synthetic data only. Best Company, its people and every `example.com` address are fictional.",
        "",
        "After the fix, the site was served locally again, crawled by following every link, and "
        "re-checked by the pixel detector and the AI review. AI findings are matched by file "
        "fingerprint (SHA-256), so unchanged images kept their first review and only the new "
        "images were reviewed again.",
        "",
        "## Results",
        "",
        f"- **Outdated images remaining:** {target(len(a['still_outdated']), len(a['pending']))}",
        f"- **Decoys wrongly changed:** {target(len(a['decoys_changed']))} "
        f"(checked {len(before.decoys)} decoys: same URL, same bytes, same pages)",
        f"- **Other untouched images changed:** {target(len(a['others_changed']))} "
        f"(checked {len(a['others'])} approved-persona and product images)",
        f"- **Old files still served:** {target(len(a['old_live']))} "
        f"(every replaced image's old URL now returns 404)",
        f"- **Pages still pointing at an old file:** {target(len(a['old_referenced']))}",
        "",
    ]
    for title, urls in (("Still outdated", a["still_outdated"]), ("Decoys changed", a["decoys_changed"]),
                        ("Other images changed", a["others_changed"]), ("Awaiting AI review", a["pending"])):
        if urls:
            lines += [f"**{title}:** " + ", ".join(f"`{_short(u)}`" for u in urls), ""]
    lines += [
        "## Before and after",
        "",
        "| Measure | Before | After |",
        "|---|---|---|",
        f"| Pages crawled | {len({r['page_url'] for r in before.crawled})} | {len(after.crawler.pages)} |",
        f"| Image uses (page + image) | {len(before.crawled)} | {len(after.manifest)} |",
        f"| Distinct image files | {len(before.sha)} | {len(after.sha)} |",
        f"| Outdated persona, per pixel detector | {b_det['outdated']} | {a_det['outdated']} |",
        f"| Outdated persona, per AI review | {b_ai['outdated']} | {a_ai['outdated']} |",
        f"| Approved persona, per pixel detector | {b_det['approved']} | {a_det['approved']} |",
        f"| Decoys, per AI review | {sum(bool(i['is_decoy']) for i in before.ai)} | "
        f"{sum(bool(i['is_decoy']) for i in after.ai)} |",
        f"| No person (product images) | {b_det['no_person']} | {a_det['no_person']} |",
        f"| AI review: needs_review | {b_ai['needs_review']} | {a_ai['needs_review']} |",
        f"| Baseline flagged (filenames and alt text only) | "
        f"{_count(before.baseline, lambda r: r['flagged'], 'yes')} | {sum(p.flagged for p in after.baseline)} |",
        "",
        f"**What changed:** {len(before.replaced)} image files were backed up to `backups/originals/` "
        f"and redrawn with the approved persona. {refs} `src`/`data-src` references were updated "
        f"across {len({p['page'] for e in before.log['replaced'] for p in e['pages_updated']})} pages, "
        f"and the old files were removed from the site. "
        f"{len(before.log['needs_review'])} image(s) were left for human review because the "
        "classifiers disagreed.",
        "",
        "**Why the baseline doesn't move:** filenames and alt text still say *a person is pictured*. "
        "It can't tell the old persona from the new one, so it can't confirm the fix. That takes "
        "looking at the pixels.",
        "",
        "## Developer handoff (`dev_handoff.csv`)",
        "",
        f"{len(handoff)} rows, one per page that showed an outdated image: "
        + ", ".join(f"{n} `{s}`" for s, n in sorted(status_counts.items())) + ". "
        "`replaced_verified` means the page now loads the new file, no longer loads the old one, "
        "and both the pixel detector and the AI review see the approved persona in it.",
        "",
    ]
    REAUDIT_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def write_before_after(before):
    """Three replaced images side by side, one per locale, linked by relative paths."""
    picks = {}
    for e in before.log["replaced"]:
        locale = e["observed"]["locale"]
        if locale not in picks and "/shared/" not in e["old_asset_url"]:
            picks[locale] = e
    lines = ["# Before and after", "",
             "Three of the replaced images, one per locale. Left: the original, kept in "
             "`backups/originals/`. Right: the replacement now on the site. Only the person "
             "changes; the layout, background and name pattern stay the same.", "",
             "Synthetic data only. Every name and `example.com` address is fictional.", "",
             "| Locale | Before (outdated persona) | After (approved persona) |", "|---|---|---|"]
    for locale in ("en-US", "ja-JP", "ar-SA"):
        e = picks.get(locale)
        if not e:
            continue
        old = e["backup_path"]
        new = "site" + _short(e["new_asset_url"])
        lines.append(f'| {locale} | <img src="{old}" width="360" alt="before"><br>`{old}` '
                     f'| <img src="{new}" width="360" alt="after"><br>`{new}` |')
    BEFORE_AFTER_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")


def run():
    before = Before()
    with serve_site() as local_base:
        crawler = Crawler(local_base).crawl()
        after = After(crawler)
        a = analyse(before, after)  # needs the server for the old-URL check
    after.write()
    handoff = handoff_rows(before, after)
    write_handoff(handoff)
    write_report(before, after, a, handoff)
    write_before_after(before)
    return before, after, a, handoff
