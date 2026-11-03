"""Re-crawl and re-classify the fixed site, then write the handoff and reports.

Run:  python3 reaudit.py   (after fix_site.py)

Writes dev_handoff.csv, reaudit_report.md, before_after.md and reaudit/ (the after-state
manifest, baseline and AI review). If new images have no AI review yet, it prepares a new
round of contact sheets in ai_review/ and reports them as pending.
"""

from collections import Counter

from crawler import guard
from remediation.reaudit import run


def main():
    guard.install()
    before, after, a, handoff = run()
    print(f"Pages crawled after fix: {len(after.crawler.pages)}; distinct images: {len(after.sha)}")
    print(f"Outdated images remaining: {len(a['still_outdated'])} (awaiting AI review: {len(a['pending'])})")
    print(f"Decoys wrongly changed: {len(a['decoys_changed'])} of {len(before.decoys)}")
    print(f"Other untouched images changed: {len(a['others_changed'])} of {len(a['others'])}")
    print(f"Old URLs still served: {len(a['old_live'])}; pages still pointing at old files: "
          f"{len(a['old_referenced'])}")
    print("dev_handoff.csv: " + ", ".join(f"{s} {n}" for s, n in sorted(Counter(r['status'] for r in handoff).items())))
    if after.pending_round:
        print(f"AI review needed: see {after.pending_round.name}/sheets/")


if __name__ == "__main__":
    main()
