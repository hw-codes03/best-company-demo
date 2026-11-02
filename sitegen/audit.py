"""Builds client_audit.csv: the client's own, incomplete list of outdated images.

It imitates a realistic manual audit:
  - it finds 15 of the 20 truly outdated images (75%), mostly missing the hard ones
    (hidden pages and lazy-loaded images);
  - it wrongly lists 3 images that are fine (two Jordan Vail decoys, one Priya Nair);
  - it repeats 2 rows (one exact copy, one listing a reused file again from another page).
"""

import csv
import random
from dataclasses import dataclass

from . import config
from .plan import hard_to_find

CAUGHT_COUNT = 15
COLUMNS = ["row", "page_url", "image_url", "persona_reported", "auditor_note"]


@dataclass
class AuditRow:
    page_path: str
    image_path: str
    note: str
    kind: str  # "true_positive", "false_positive" or "duplicate" (kept out of the CSV)


def _url(path):
    return f"{config.BASE_URL}/{path}"


def _visible_page(asset, pages_by_path):
    """The page an auditor would most likely have found this image on."""
    visible = [p for p, _ in asset.refs if not pages_by_path[p].hidden]
    return (visible or [asset.refs[0][0]])[0]


def build_audit(plan):
    """Return the audit rows in final CSV order."""
    # A separate, seeded generator, so audit choices never shift the site layout.
    rng = random.Random(f"{config.SEED}-audit")
    pages_by_path = {p.path: p for p in plan.pages}
    outdated = [a for a in plan.images if a.persona_key == "jordan_vale"]

    # Miss four of the hard-to-find images, then one more easy one at random.
    hard = [a for a in outdated if hard_to_find(a, pages_by_path)]
    missed = rng.sample(hard, min(4, len(hard)))
    easy = [a for a in outdated if a not in missed]
    missed += rng.sample(easy, len(outdated) - CAUGHT_COUNT - len(missed))
    caught = [a for a in outdated if a not in missed]

    rows = [AuditRow(_visible_page(a, pages_by_path), a.path, "Old persona visible", "true_positive")
            for a in caught]

    # Three false positives: images that look similar but must NOT be replaced.
    decoys = rng.sample([a for a in plan.images if a.persona_key == "jordan_vail"], 2)
    approved = rng.choice([a for a in plan.images if a.persona_key == "priya_nair"])
    for a in decoys:
        rows.append(AuditRow(_visible_page(a, pages_by_path), a.path, "JV avatar, looks outdated",
                             "false_positive"))
    rows.append(AuditRow(_visible_page(approved, pages_by_path), approved.path,
                         "Unsure, please double-check", "false_positive"))

    # Two duplicates: an exact copy of one row, and a reused file listed again from another page.
    exact = rng.choice([r for r in rows if r.kind == "true_positive"])
    rows.append(AuditRow(exact.page_path, exact.image_path, exact.note, "duplicate"))
    reused = [a for a in caught if len(a.refs) > 1]
    first = next(r for r in rows if r.image_path == reused[0].path)
    other_page = next(p for p, _ in reused[0].refs if p != first.page_path)
    rows.append(AuditRow(other_page, reused[0].path, "Old persona visible", "duplicate"))

    rng.shuffle(rows)
    return rows


def write_audit_csv(rows):
    with open(config.CLIENT_AUDIT_CSV, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(COLUMNS)
        for i, r in enumerate(rows, start=1):
            writer.writerow([i, _url(r.page_path), _url(r.image_path), "Jordan Vale", r.note])
