"""Merges the AI reviewer's per-batch findings into ai_review.json and applies the
confidence rule.

The reviewer (an AI model looking at the contact sheets in ai_review/sheets/) writes one
findings file per batch in ai_review/findings/. Each finding says whether the picture
contains the outdated persona (by name in any locale form, email or teal avatar), whether
it is a look-alike decoy, a confidence from 0 to 1, and short evidence.

The status is set here, in code, not by the reviewer:
  confidence below 0.7         -> "needs_review" (a human must look)
  otherwise, outdated persona  -> "outdated"
  otherwise                    -> "not_outdated"
"""

import json

from crawler.settings import REPO_ROOT

from .ai_batches import BATCHES_JSON, FINDINGS_DIR

AI_REVIEW_JSON = REPO_ROOT / "ai_review.json"
CONFIDENCE_THRESHOLD = 0.7
REQUIRED = ("contains_outdated_persona", "is_decoy", "confidence", "evidence", "signals")


def status_for(finding):
    if finding["confidence"] < CONFIDENCE_THRESHOLD:
        return "needs_review"
    return "outdated" if finding["contains_outdated_persona"] else "not_outdated"


def merge_findings():
    """Join each batch's findings to its image URLs; fail loudly if anything is missing."""
    batches = json.loads(BATCHES_JSON.read_text(encoding="utf-8"))
    images = []
    for batch in batches:
        path = FINDINGS_DIR / f"batch_{batch['batch']:02d}.json"
        if not path.exists():
            raise FileNotFoundError(f"AI review batch {batch['batch']} has no findings yet: {path}")
        data = json.loads(path.read_text(encoding="utf-8"))
        by_id = {f["image_id"]: f for f in data["findings"]}
        for item in batch["images"]:
            f = by_id.get(item["image_id"])
            if f is None or any(k not in f for k in REQUIRED):
                raise ValueError(f"Incomplete finding for {item['image_id']} in {path.name}")
            if not 0 <= f["confidence"] <= 1:
                raise ValueError(f"Confidence out of range for {item['image_id']}")
            images.append({
                "image_id": item["image_id"],
                "batch": batch["batch"],
                "asset_url": item["asset_url"],
                "contains_outdated_persona": f["contains_outdated_persona"],
                "signals": f["signals"],
                "name_form_seen": f.get("name_form_seen", ""),
                "is_decoy": f["is_decoy"],
                "confidence": f["confidence"],
                "status": status_for(f),
                "evidence": f["evidence"],
            })
    return images


def write_ai_review(images):
    counts = {s: sum(1 for i in images if i["status"] == s)
              for s in ("outdated", "not_outdated", "needs_review")}
    doc = {
        "method": "An AI model viewed each image (10 per batch, as labelled contact sheets) "
                  "and judged it on name (any locale form), email and avatar.",
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "batches": len({i["batch"] for i in images}),
        "counts": counts,
        "images": images,
    }
    AI_REVIEW_JSON.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
