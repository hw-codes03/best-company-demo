"""Turns the AI reviewer's saved findings into a per-image verdict file (ai_review.json).

The reviewer (an AI model looking at the contact sheets) records, for each image: whether
it contains the outdated persona (name in any locale form, email or teal avatar), whether
it is a look-alike decoy, a confidence from 0 to 1, and short evidence.

The status is set here, in code, not by the reviewer:
  no review yet for this exact file  -> "pending_review"
  confidence below 0.7               -> "needs_review" (a human must look)
  otherwise, outdated persona        -> "outdated"
  otherwise                          -> "not_outdated"
"""

import json

from crawler.settings import REPO_ROOT

from .ai_batches import prepare_round, round_dirs

AI_REVIEW_JSON = REPO_ROOT / "ai_review.json"
CONFIDENCE_THRESHOLD = 0.7
REQUIRED = ("contains_outdated_persona", "is_decoy", "confidence", "evidence", "signals")


def status_for(finding):
    if finding["confidence"] < CONFIDENCE_THRESHOLD:
        return "needs_review"
    return "outdated" if finding["contains_outdated_persona"] else "not_outdated"


def load_findings():
    """Every saved finding from every round, keyed by the reviewed file's SHA-256.
    Byte-identical files at different URLs share a key, so each key holds a list."""
    known = {}
    for round_dir in round_dirs():
        batches = json.loads((round_dir / "batches.json").read_text(encoding="utf-8"))
        for batch in batches:
            path = round_dir / "findings" / f"batch_{batch['batch']:02d}.json"
            if not path.exists():
                continue  # this batch is still waiting for review
            by_id = {f["image_id"]: f for f in json.loads(path.read_text(encoding="utf-8"))["findings"]}
            for item in batch["images"]:
                f = by_id.get(item["image_id"])
                if f is None or any(k not in f for k in REQUIRED):
                    raise ValueError(f"Incomplete finding for {item['image_id']} in {path}")
                if not 0 <= f["confidence"] <= 1:
                    raise ValueError(f"Confidence out of range for {item['image_id']}")
                known.setdefault(item["sha256"], []).append(
                    dict(f, round=round_dir.name, batch=batch["batch"], reviewed_url=item["asset_url"]))
    return known


def review(crawler):
    """Return one verdict per crawled image. Images with no saved finding get
    "pending_review", and a new round of sheets is prepared for them."""
    known = load_findings()
    pending = [u for u, a in crawler.assets.items() if a.sha256 and a.sha256 not in known]
    round_dir = prepare_round(crawler, pending)[0] if pending else None
    images = []
    for url in sorted(crawler.assets):
        candidates = known.get(crawler.assets[url].sha256, [])
        # Prefer the finding made for this exact URL; otherwise reuse one for identical content.
        f = next((c for c in candidates if c["reviewed_url"] == url), candidates[0] if candidates else None)
        if f is None:
            images.append({"asset_url": url, "status": "pending_review", "confidence": None,
                           "is_decoy": None, "contains_outdated_persona": None,
                           "evidence": f"Waiting for review in {round_dir.name}"})
            continue
        images.append({
            "image_id": f["image_id"], "review_round": f["round"], "batch": f["batch"],
            "asset_url": url, "contains_outdated_persona": f["contains_outdated_persona"],
            "signals": f["signals"], "name_form_seen": f.get("name_form_seen", ""),
            "is_decoy": f["is_decoy"], "confidence": f["confidence"],
            "status": status_for(f), "evidence": f["evidence"],
        })
    return images, round_dir


def write_ai_review(images, path=AI_REVIEW_JSON):
    counts = {s: sum(1 for i in images if i["status"] == s)
              for s in ("outdated", "not_outdated", "needs_review", "pending_review")}
    doc = {
        "method": "An AI model viewed each image (10 per batch, as labelled contact sheets) "
                  "and judged it on name (any locale form), email and avatar. Findings are "
                  "matched to files by SHA-256.",
        "confidence_threshold": CONFIDENCE_THRESHOLD,
        "batches": len({(i.get("review_round"), i.get("batch")) for i in images if i.get("batch")}),
        "counts": counts,
        "images": images,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return doc
