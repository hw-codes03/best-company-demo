"""Prepares AI review rounds: groups images that still need a human-style look into
batches of ten and draws one labelled contact sheet per batch.

Reviews are matched to images by SHA-256 (the file's content), not by URL. So when the
site changes, images that are byte-for-byte unchanged keep their earlier review, and
only new or changed pictures go into a new round.

Layout on disk, one folder per round:
  ai_review/round_N/batches.json      which image (URL + SHA-256) has which ID
  ai_review/round_N/sheets/*.png      exactly what the reviewer looked at
  ai_review/round_N/findings/*.json   the reviewer's judgments, one file per batch
A round with findings is never rewritten.
"""

import json
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from crawler.settings import PUBLIC_BASE, REPO_ROOT

AI_DIR = REPO_ROOT / "ai_review"
BATCH_SIZE = 10
COLUMNS = 2
TILE_W, TILE_H, LABEL_H = 820, 330, 30
LABEL_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def round_dirs():
    return sorted(AI_DIR.glob("round_*"), key=lambda p: int(p.name.split("_")[1]))


def has_findings(round_dir):
    return any((round_dir / "findings").glob("batch_*.json"))


def _draw_sheet(path, items, assets):
    font = ImageFont.truetype(LABEL_FONT, 18)
    rows = -(-len(items) // COLUMNS)
    sheet = Image.new("RGB", (COLUMNS * TILE_W, rows * (TILE_H + LABEL_H)), "#7B8794")
    draw = ImageDraw.Draw(sheet)
    for i, item in enumerate(items):
        x, y = (i % COLUMNS) * TILE_W, (i // COLUMNS) * (TILE_H + LABEL_H)
        picture = Image.open(BytesIO(assets[item["asset_url"]].data)).convert("RGB")
        draw.rectangle([x, y, x + TILE_W, y + LABEL_H], fill="#000000")
        draw.text((x + 8, y + 5), f"{item['image_id']}  {item['asset_url'].replace(PUBLIC_BASE, '')}",
                  font=font, fill="#FFFF00")
        sheet.paste(picture, (x + 10, y + LABEL_H))
    path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(path, optimize=True)


def prepare_round(crawler, pending_urls):
    """Write batches and sheets for images nobody has reviewed yet. Reuses an unreviewed
    round folder if one exists, so rerunning doesn't pile up empty rounds."""
    dirs = round_dirs()
    if dirs and not has_findings(dirs[-1]):
        number = int(dirs[-1].name.split("_")[1])
    else:
        number = (int(dirs[-1].name.split("_")[1]) + 1) if dirs else 1
    round_dir = AI_DIR / f"round_{number}"
    for old in (round_dir / "sheets").glob("*.png"):
        old.unlink()  # safe: this round has no findings yet
    urls = sorted(pending_urls)
    batches = []
    for b, start in enumerate(range(0, len(urls), BATCH_SIZE), start=1):
        items = [{"image_id": f"R{number}-B{b}-{i:02d}", "asset_url": u,
                  "sha256": crawler.assets[u].sha256}
                 for i, u in enumerate(urls[start:start + BATCH_SIZE], start=1)]
        batches.append({"batch": b, "images": items})
        _draw_sheet(round_dir / "sheets" / f"batch_{b:02d}.png", items, crawler.assets)
    round_dir.mkdir(parents=True, exist_ok=True)
    (round_dir / "batches.json").write_text(json.dumps(batches, indent=2) + "\n", encoding="utf-8")
    (round_dir / "findings").mkdir(exist_ok=True)
    return round_dir, batches
