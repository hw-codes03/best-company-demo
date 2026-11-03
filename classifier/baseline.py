"""Baseline classifier: guesses from filenames and alt text only, never opening the image.

The rules, in plain English:
  1. If the filename or alt text mentions the outdated persona by name (e.g. "jordan",
     "vale"), flag it. This is the strongest hint a filename could give.
  2. If the alt text describes a person (e.g. "Team member" in any of the site's
     languages), flag it, because it might be the outdated persona.
  3. If the filename starts with a person-style prefix (team, hero, quote, sig), flag it.
  4. Otherwise (e.g. "product-..." with product alt text) leave it unflagged.

So the baseline can tell "person picture" from "product picture", but it cannot tell
WHICH person, so it expects to over-flag the approved persona and the decoys.
"""

import csv
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from crawler.settings import REPO_ROOT

BASELINE_CSV = REPO_ROOT / "baseline_predictions.csv"

NAME_HINTS = re.compile(r"jordan|vale|ジョーダン|ヴェール|جوردان|فيل", re.IGNORECASE)
PERSON_ALT_TEXT = {"team member", "チームメンバー", "عضو في الفريق"}
PERSON_FILE_PREFIXES = ("team-", "hero-", "quote-", "sig-")


@dataclass
class BaselinePrediction:
    asset_url: str
    flagged: bool
    rule: str
    evidence: str


def classify(asset_url, alt_texts):
    """Apply the rules to one image URL and every alt text it was shown with."""
    filename = urlsplit(asset_url).path.rsplit("/", 1)[-1]
    alts = sorted({a.strip() for a in alt_texts if a})
    alt_desc = " | ".join(alts) or "(no alt text)"
    if NAME_HINTS.search(filename) or any(NAME_HINTS.search(a) for a in alts):
        return BaselinePrediction(asset_url, True, "name_in_filename_or_alt", f"{filename}; alt: {alt_desc}")
    if any(a.lower() in PERSON_ALT_TEXT for a in alts):
        return BaselinePrediction(asset_url, True, "person_alt_text", f"alt: {alt_desc}")
    if filename.startswith(PERSON_FILE_PREFIXES):
        return BaselinePrediction(asset_url, True, "person_filename_prefix", filename)
    return BaselinePrediction(asset_url, False, "no_person_hint", f"{filename}; alt: {alt_desc}")


def run_baseline(crawler):
    """Classify every distinct image URL the crawler found."""
    alts = {}
    for page in crawler.pages.values():
        for url, alt in page.alts.items():
            alts.setdefault(url, []).append(alt)
    return [classify(url, alts.get(url, [])) for url in sorted(crawler.assets)]


def write_baseline(predictions, path=BASELINE_CSV):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["asset_url", "flagged", "rule", "evidence"])
        for p in predictions:
            writer.writerow([p.asset_url, "yes" if p.flagged else "no", p.rule, p.evidence])
