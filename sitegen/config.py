"""Settings shared by every module: the random seed, the brand and the output paths."""

from pathlib import Path

# One fixed seed so that every run produces exactly the same site, byte for byte.
SEED = 20261102

# The fictional brand. The domain uses the reserved .example TLD, so it can never be real.
BRAND_NAME = "Best Company"
DOMAIN = "bestcompany.example.com"
BASE_URL = f"https://{DOMAIN}"

# The repository root is the folder that contains this package.
REPO_ROOT = Path(__file__).resolve().parent.parent

# Where the generated files go.
SITE_DIR = REPO_ROOT / "site"                       # the fake website (HTML, PNG images, sitemap.xml)
CLIENT_AUDIT_CSV = REPO_ROOT / "client_audit.csv"   # the client's incomplete audit, as delivered to us
ANSWER_KEY_DIR = REPO_ROOT / "answer_key"           # hidden answer key for scoring only
GROUND_TRUTH_CSV = ANSWER_KEY_DIR / "ground_truth.csv"
GALLERY_MD = REPO_ROOT / "gallery.md"               # a sample of images you can view on GitHub

# Any detection pipeline built on this site must never open anything under these paths.
# Only a separate scoring step may read the answer key.
FORBIDDEN_FOR_PIPELINE = (ANSWER_KEY_DIR,)

# The three locales. "dir" is the text direction: Arabic reads right to left.
LOCALES = {
    "en-US": {"lang": "en", "dir": "ltr"},
    "ja-JP": {"lang": "ja", "dir": "ltr"},
    "ar-SA": {"lang": "ar", "dir": "rtl"},
}

# Fonts already installed on this machine. Japanese needs a CJK font, and Arabic
# needs a font with Arabic letters (DejaVu Sans has them).
FONT_LATIN = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_LATIN_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
FONT_JAPANESE = "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf"
FONT_ARABIC = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
FONT_ARABIC_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
