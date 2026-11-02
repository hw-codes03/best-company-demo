"""Generate the whole synthetic Best Company test site in one go.

Run:  python3 generate.py

It rebuilds site/, client_audit.csv, answer_key/ground_truth.csv and gallery.md from the
fixed seed in sitegen/config.py, then prints exact counts. Same seed, same files.
"""

from sitegen.answer_key import write_ground_truth
from sitegen.audit import build_audit, write_audit_csv
from sitegen.gallery import write_gallery
from sitegen.plan import build_plan
from sitegen.report import print_report
from sitegen.site import write_site


def main():
    plan = build_plan()             # decide everything in memory first
    write_site(plan)                # images, HTML pages, sitemap.xml
    audit_rows = build_audit(plan)  # the client's incomplete audit
    write_audit_csv(audit_rows)
    write_ground_truth(plan, audit_rows)  # hidden answer key
    write_gallery(plan)
    print_report(plan, audit_rows)


if __name__ == "__main__":
    main()
