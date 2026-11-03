"""Replace every outdated image with the approved persona.

Run:  python3 fix_site.py   (after crawl_site.py and classify.py)

Backs up each original to backups/originals/, redraws it with the approved persona,
updates every page that used it, removes the old file, and logs it all in
backups/remediation_log.json.
"""

from crawler import guard
from remediation.fix import remediate


def main():
    guard.install()
    entries, review = remediate()
    refs = sum(p["references"] for e in entries for p in e["pages_updated"])
    print(f"Images backed up and replaced: {len(entries)}")
    print(f"Page references updated: {refs} across "
          f"{len({p['page'] for e in entries for p in e['pages_updated']})} pages")
    print(f"Layout check passed (old persona redrawn identically from observations): "
          f"{sum(e['layout_check_passed'] for e in entries)} of {len(entries)}")
    print(f"Left for human review (classifiers disagreed or unsure): {len(review)}")


if __name__ == "__main__":
    main()
