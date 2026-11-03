"""Paths used by the remediation and re-audit steps."""

from crawler.settings import REPO_ROOT, SITE_DIR

BACKUP_DIR = REPO_ROOT / "backups" / "originals"        # untouched copies of every replaced image
REMEDIATION_LOG = REPO_ROOT / "backups" / "remediation_log.json"
REMEDIATED_MARKER = SITE_DIR / ".remediated"            # tells crawl/classify the site has changed
NEW_SUFFIX = "-v2"                                      # team-01.png -> team-01-v2.png

REAUDIT_DIR = REPO_ROOT / "reaudit"
DEV_HANDOFF_CSV = REPO_ROOT / "dev_handoff.csv"
REAUDIT_REPORT_MD = REPO_ROOT / "reaudit_report.md"
BEFORE_AFTER_MD = REPO_ROOT / "before_after.md"
DOCS_SHOWING_ORIGINALS = [REPO_ROOT / "gallery.md", REPO_ROOT / "gap_report.md"]
