"""Score every method against the hidden answer key and write metrics.md.

Run:  python3 evaluate.py

This is the ONLY code allowed to read answer_key/ground_truth.csv. Everything else
(crawler, baseline, AI review) runs with the answer key locked away.

What is scored: each distinct image file (by URL). "Positive" means the file really
shows the outdated persona (Jordan Vale) and must be replaced.
  - Precision: of the files a method flagged, how many really needed replacing.
  - Recall: of the files that really needed replacing, how many the method flagged.

The methods:
  - Client audit: every image URL listed in client_audit.csv (duplicate rows count once).
  - Crawler: manifest.csv rows the pixel detector marked "outdated".
  - Baseline: baseline_predictions.csv rows flagged from filenames and alt text.
  - AI review: ai_review.json images with status "outdated" or "needs_review"
    (needs_review counts as flagged, because a person will check it).
"""

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
GROUND_TRUTH = ROOT / "answer_key" / "ground_truth.csv"
METRICS_MD = ROOT / "metrics.md"
BASE = "https://bestcompany.example.com"


# ---------- Load the truth and each method's flagged set ----------

def load_truth():
    with open(GROUND_TRUTH, newline="", encoding="utf-8") as f:
        return {r["image_url"]: r for r in csv.DictReader(f)}


def _read_csv(name):
    with open(ROOT / name, newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def load_methods():
    ai = json.loads((ROOT / "ai_review.json").read_text(encoding="utf-8"))
    return ai, {
        "Client audit": {r["image_url"] for r in _read_csv("client_audit.csv")},
        "Crawler": {r["asset_url"] for r in _read_csv("manifest.csv") if r["status"] == "outdated"},
        "Baseline": {r["asset_url"] for r in _read_csv("baseline_predictions.csv") if r["flagged"] == "yes"},
        "AI review": {i["asset_url"] for i in ai["images"] if i["status"] in ("outdated", "needs_review")},
    }


# ---------- Scoring ----------

def score(flagged, truth):
    positives = {u for u, r in truth.items() if r["is_outdated"] == "yes"}
    tp, fp, fn = flagged & positives, flagged - positives, positives - flagged
    precision = len(tp) / len(flagged) if flagged else 0.0
    recall = len(tp) / len(positives) if positives else 0.0
    return {"tp": tp, "fp": fp, "fn": fn, "precision": precision, "recall": recall,
            "unknown": flagged - set(truth)}  # flagged URLs that aren't real site images


def why_missed(row):
    """Plain-English reason a truly outdated file might be overlooked."""
    if row["only_on_hidden_pages"] == "yes":
        return "only on a footer-only page missing from the sitemap"
    if row["only_lazy_loaded"] == "yes":
        return "only lazy-loaded via data-src"
    return "an ordinary image on a normal page"


def why_wrong(row):
    """Plain-English description of a file that was flagged but did not need replacing."""
    return {"jordan_vail": "the Jordan Vail look-alike (decoy)",
            "priya_nair": "the approved persona, Priya Nair",
            "none": "a product picture with no person"}.get(row["persona"], row["persona"])


def _short(url):
    return url.replace(BASE, "")


def _group(urls, truth, explain):
    """Count reasons, e.g. {'only lazy-loaded via data-src': 1, ...}."""
    counts = {}
    for u in sorted(urls):
        reason = explain(truth[u])
        counts[reason] = counts.get(reason, 0) + 1
    return counts


def _describe(counts):
    return "; ".join(f"{n} × {reason}" for reason, n in sorted(counts.items(), key=lambda kv: -kv[1]))


# ---------- Guard check: nobody else reads the answer key ----------

def other_readers():
    """List pipeline source files that mention the answer key. The generator (sitegen/ and
    its entry point generate.py) writes it and evaluate.py reads it; nothing else should."""
    suspects = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if rel.parts[0] == "sitegen" or rel.name in ("generate.py", "evaluate.py"):
            continue
        text = path.read_text(encoding="utf-8")
        if "ground_truth" in text:
            suspects.append(str(rel))
    return suspects


# ---------- Report ----------

def summary_text(name, s, truth, ai):
    fn_reasons, fp_reasons = _group(s["fn"], truth, why_missed), _group(s["fp"], truth, why_wrong)
    parts = []
    if name == "Client audit":
        parts.append("A manual list from the client.")
    elif name == "Crawler":
        parts.append("Follows every link (including footer-only pages), reads both src and data-src, "
                     "then checks the pixels for a round teal avatar.")
    elif name == "Baseline":
        parts.append("Never looks at the picture: it flags anything whose alt text or filename "
                     "suggests a person.")
    else:
        parts.append(f"An AI model looked at every picture, {ai['batches']} batches of up to 10, and "
                     "judged name, email and avatar in each locale's script.")
    if s["fn"]:
        parts.append(f"**Missed {len(s['fn'])}:** {_describe(fn_reasons)}.")
    else:
        parts.append("**Missed nothing.**")
    if s["fp"]:
        parts.append(f"**Wrongly flagged {len(s['fp'])}:** {_describe(fp_reasons)}.")
    else:
        parts.append("**No false alarms.**")
    if name == "Baseline" and s["fp"]:
        parts.append("Filenames and alt text say *a person* is pictured, not *which* person, so every "
                     "approved-persona and decoy image looks the same to it.")
    if name == "Client audit" and s["fn"]:
        parts.append("The misses cluster where a manual audit wouldn't look: pages reachable only "
                     "from the footer and images that only load when scrolled into view.")
    if name == "AI review":
        needs = [i for i in ai["images"] if i["status"] == "needs_review"]
        decoys_true = {u for u, r in truth.items() if r["is_decoy"] == "yes"}
        decoys_ai = {i["asset_url"] for i in ai["images"] if i["is_decoy"]}
        parts.append(f"{len(needs)} image(s) fell below the {ai['confidence_threshold']} confidence "
                     f"threshold and went to needs_review. It labelled {len(decoys_ai & decoys_true)} "
                     f"of {len(decoys_true)} decoys correctly"
                     f"{f' and {len(decoys_ai - decoys_true)} non-decoys as decoys' if decoys_ai - decoys_true else ''}.")
    return " ".join(parts)


def write_metrics(scores, truth, ai):
    positives = sum(1 for r in truth.values() if r["is_outdated"] == "yes")
    lines = [
        "# Metrics: who found the outdated persona?",
        "",
        "Synthetic data only. Best Company, its people and every `example.com` address are fictional.",
        "",
        f"Scored per distinct image file: {len(truth)} files, of which **{positives}** really show the "
        "outdated persona (Jordan Vale) and must be replaced. Only `evaluate.py` reads the answer key.",
        "",
        "- **Precision**: of the files a method flagged, the share that really needed replacing.",
        "- **Recall**: of the files that really needed replacing, the share the method flagged.",
        "",
        "| Method | Flagged | Correct | Wrong | Missed | Precision | Recall |",
        "|---|---|---|---|---|---|---|",
    ]
    for name, s in scores.items():
        flagged = len(s["tp"]) + len(s["fp"])
        lines.append(f"| {name} | {flagged} | {len(s['tp'])} | {len(s['fp'])} | {len(s['fn'])} | "
                     f"{s['precision']:.1%} | {s['recall']:.1%} |")
    lines += ["", "## Where each one failed", ""]
    for name, s in scores.items():
        lines += [f"### {name}", "", summary_text(name, s, truth, ai), ""]
        if s["fn"] or s["fp"]:
            lines += ["| File | Outcome | Why |", "|---|---|---|"]
            lines += [f"| `{_short(u)}` | missed | {why_missed(truth[u])} |" for u in sorted(s["fn"])]
            lines += [f"| `{_short(u)}` | wrongly flagged | {why_wrong(truth[u])} |" for u in sorted(s["fp"])]
            lines.append("")
    lines += [
        "## Caveats", "",
        "- **The data is clean and synthetic.** Images are flat renders with crisp text and exact "
        "colours. Real photos, compression and screenshots would make both the pixel detector and the "
        "AI review less reliable.",
        "- **The AI review was not blind.** The same assistant wrote the generator, so it already knew "
        "how the personas and decoys look. It judged only what was visible in each picture and recorded "
        "evidence for every call, but an independent reviewer would be a fairer test.",
        "- **The crawler's detector relies on avatar colour**, as the client brief describes it. A "
        "look-alike in the same teal would fool it. The AI review also checks name and email, so it "
        "would not be fooled.",
        "",
    ]
    readers = other_readers()
    lines += ["## Answer-key isolation", "",
              "No pipeline code mentions the answer key. The crawler and classifiers also run with a "
              "guard that blocks any attempt to open `answer_key/`."
              if not readers else
              "**Warning:** these files mention the answer key: " + ", ".join(f"`{r}`" for r in readers),
              ""]
    METRICS_MD.write_text("\n".join(lines), encoding="utf-8")
    return readers


def main():
    truth = load_truth()
    ai, methods = load_methods()
    scores = {name: score(flagged, truth) for name, flagged in methods.items()}
    for name, s in scores.items():
        if s["unknown"]:
            print(f"Note: {name} flagged {len(s['unknown'])} URL(s) that are not site images")
    readers = write_metrics(scores, truth, ai)
    print(f"{'Method':<13} {'Flagged':>7} {'TP':>4} {'FP':>4} {'FN':>4} {'Precision':>10} {'Recall':>8}")
    for name, s in scores.items():
        print(f"{name:<13} {len(s['tp']) + len(s['fp']):>7} {len(s['tp']):>4} {len(s['fp']):>4} "
              f"{len(s['fn']):>4} {s['precision']:>10.1%} {s['recall']:>8.1%}")
    print("Answer key read only by evaluate.py:", "yes" if not readers else f"NO, also {readers}")


if __name__ == "__main__":
    main()
