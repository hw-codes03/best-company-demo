"""Paths and the facts from the client brief that the crawler is allowed to use."""

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

SITE_DIR = REPO_ROOT / "site"                     # served over HTTP; never read directly
CLIENT_AUDIT_CSV = REPO_ROOT / "client_audit.csv"
MANIFEST_CSV = REPO_ROOT / "manifest.csv"
GAP_REPORT_MD = REPO_ROOT / "gap_report.md"

# The hidden answer key. The guard module blocks every attempt to open anything in here.
ANSWER_KEY_DIR = REPO_ROOT / "answer_key"

# The public address the site lives at. The crawler fetches from a local server but
# records public URLs, so they line up with the URLs in the client audit.
PUBLIC_BASE = "https://bestcompany.example.com"

# Where crawling starts, besides every URL listed in sitemap.xml.
START_PATHS = ["/en-US/index.html"]

# From the client brief: how to tell the personas apart. Avatar colours are given as hue
# ranges in degrees (0-360) so small rendering differences still match.
OUTDATED_PERSONA = {"name": "Jordan Vale", "email": "jordan.vale@example.com",
                    "avatar": "teal", "hue_range": (165, 195)}
APPROVED_PERSONA = {"name": "Priya Nair", "email": "priya.nair@example.com",
                    "avatar": "orange", "hue_range": (15, 45)}
