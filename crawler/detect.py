"""Looks at an image's pixels and decides which persona, if any, it shows.

The client brief says the outdated persona has a TEAL round avatar and the approved one
an ORANGE round avatar. So we look for solid, strongly coloured blobs shaped like a
circle and check their colour:

  teal circle    -> "outdated"      (Jordan Vale: must be replaced)
  orange circle  -> "approved"      (Priya Nair: already correct)
  other circle   -> "other_person"  (someone else, e.g. a look-alike; leave alone)
  no circle      -> "no_person"     (e.g. a product picture)

This does not read any text. It relies only on avatar colour and shape.
"""

import colorsys
from collections import deque
from dataclasses import dataclass
from io import BytesIO

import numpy as np
from PIL import Image

from .settings import APPROVED_PERSONA, OUTDATED_PERSONA

MIN_SATURATION = 0.35   # pale backgrounds and grey text are ignored
MIN_BRIGHTNESS = 0.35   # very dark pixels (header bar, black text) are ignored
MIN_BLOB_PIXELS = 1500  # anything smaller is text or decoration, not an avatar


@dataclass
class Detection:
    status: str
    avatar_hex: str = ""   # colour of the avatar found, e.g. "#0f9d9a"
    hue: float | None = None


def _components(mask):
    """Split a True/False pixel mask into connected blobs (4-neighbour flood fill)."""
    seen = np.zeros_like(mask, dtype=bool)
    h, w = mask.shape
    for y, x in zip(*np.nonzero(mask)):
        if seen[y, x]:
            continue
        blob, queue = [], deque([(y, x)])
        seen[y, x] = True
        while queue:
            cy, cx = queue.popleft()
            blob.append((cy, cx))
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not seen[ny, nx]:
                    seen[ny, nx] = True
                    queue.append((ny, nx))
        yield np.array(blob)


def _looks_like_circle(blob):
    """A filled circle has a square bounding box, fills about 60-85% of it (the initials
    are holes), and leaves the box's corners empty. A rounded rectangle fills its corners."""
    ys, xs = blob[:, 0], blob[:, 1]
    y0, y1, x0, x1 = ys.min(), ys.max(), xs.min(), xs.max()
    w, h = x1 - x0 + 1, y1 - y0 + 1
    if min(w, h) < 40 or abs(w - h) > 0.08 * max(w, h):
        return False
    if not 0.55 <= len(blob) / (w * h) <= 0.85:
        return False
    inside = {(int(y), int(x)) for y, x in blob}
    corners = [(y0 + int(0.12 * h), x0 + int(0.12 * w)), (y0 + int(0.12 * h), x1 - int(0.12 * w)),
               (y1 - int(0.12 * h), x0 + int(0.12 * w)), (y1 - int(0.12 * h), x1 - int(0.12 * w))]
    return not any(c in inside for c in corners)


def _in_range(hue, hue_range):
    lo, hi = hue_range
    return lo <= hue <= hi


def detect(image_bytes):
    """Return a Detection for one image file's bytes."""
    rgb = np.asarray(Image.open(BytesIO(image_bytes)).convert("RGB"), dtype=np.float32) / 255
    top, low = rgb.max(axis=2), rgb.min(axis=2)
    saturation = np.where(top > 0, (top - low) / np.maximum(top, 1e-6), 0)
    mask = (saturation >= MIN_SATURATION) & (top >= MIN_BRIGHTNESS)

    for blob in _components(mask):
        if len(blob) < MIN_BLOB_PIXELS or not _looks_like_circle(blob):
            continue
        r, g, b = np.median(rgb[blob[:, 0], blob[:, 1]], axis=0)
        hue = colorsys.rgb_to_hsv(r, g, b)[0] * 360
        hex_colour = "#{:02x}{:02x}{:02x}".format(*(int(round(v * 255)) for v in (r, g, b)))
        if _in_range(hue, OUTDATED_PERSONA["hue_range"]):
            return Detection("outdated", hex_colour, hue)
        if _in_range(hue, APPROVED_PERSONA["hue_range"]):
            return Detection("approved", hex_colour, hue)
        return Detection("other_person", hex_colour, hue)
    return Detection("no_person")
