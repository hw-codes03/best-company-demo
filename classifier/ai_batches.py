"""Prepares the AI review: splits the crawled images into batches and draws one contact
sheet per batch, so the reviewer looks at ten real pictures at a time.

Each tile is labelled with a short image ID (e.g. "B2-07") and its URL path, so the
reviewer's findings can be tied back to the right file. The sheets are kept in
ai_review/sheets/ as a record of exactly what the reviewer saw.
"""

import json
from io import BytesIO

from PIL import Image, ImageDraw, ImageFont

from crawler.settings import PUBLIC_BASE, REPO_ROOT

AI_DIR = REPO_ROOT / "ai_review"
SHEETS_DIR = AI_DIR / "sheets"
FINDINGS_DIR = AI_DIR / "findings"
BATCHES_JSON = AI_DIR / "batches.json"
BATCH_SIZE = 10
COLUMNS = 2
TILE_W, TILE_H, LABEL_H = 820, 330, 30
LABEL_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


def plan_batches(crawler):
    """Split distinct image URLs, in sorted order, into batches of ten with stable IDs."""
    urls = sorted(crawler.assets)
    batches = []
    for b, start in enumerate(range(0, len(urls), BATCH_SIZE), start=1):
        items = [{"image_id": f"B{b}-{i:02d}", "asset_url": u}
                 for i, u in enumerate(urls[start:start + BATCH_SIZE], start=1)]
        batches.append({"batch": b, "images": items})
    return batches


def draw_sheets(crawler, batches):
    """Draw one labelled contact sheet per batch, each picture at full size."""
    SHEETS_DIR.mkdir(parents=True, exist_ok=True)
    font = ImageFont.truetype(LABEL_FONT, 18)
    for batch in batches:
        rows = -(-len(batch["images"]) // COLUMNS)
        sheet = Image.new("RGB", (COLUMNS * TILE_W, rows * (TILE_H + LABEL_H)), "#7B8794")
        draw = ImageDraw.Draw(sheet)
        for i, item in enumerate(batch["images"]):
            x, y = (i % COLUMNS) * TILE_W, (i // COLUMNS) * (TILE_H + LABEL_H)
            picture = Image.open(BytesIO(crawler.assets[item["asset_url"]].data)).convert("RGB")
            draw.rectangle([x, y, x + TILE_W, y + LABEL_H], fill="#000000")
            draw.text((x + 8, y + 5), f"{item['image_id']}  {item['asset_url'].replace(PUBLIC_BASE, '')}",
                      font=font, fill="#FFFF00")
            sheet.paste(picture, (x + 10, y + LABEL_H))
        sheet.save(SHEETS_DIR / f"batch_{batch['batch']:02d}.png", optimize=True)


def prepare(crawler):
    batches = plan_batches(crawler)
    AI_DIR.mkdir(exist_ok=True)
    BATCHES_JSON.write_text(json.dumps(batches, indent=2) + "\n", encoding="utf-8")
    draw_sheets(crawler, batches)
    return batches
