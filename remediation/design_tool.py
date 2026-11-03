"""Redraws an outdated image with the approved persona, keeping everything else the same.

NOTE: this module STANDS IN FOR A DESIGN TOOL. In real life a designer (or a design tool's
API) would open the source file, swap the person and export a new image. Here we redraw
the card with the same renderer the site's images were made with.

It only uses what can be observed about the old image, not the generator's records:
  - layout:     from the image's size (each card style has its own size)
  - locale:     from the folder in the URL, or from the script of the name the AI review read
  - background: from a corner pixel of the old image
  - name form:  whether the AI review saw the Latin name in brackets next to the local script
"""

from io import BytesIO

from PIL import Image

from sitegen.config import LOCALES
from sitegen.personas import JORDAN_VALE, PRIYA_NAIR
from sitegen.render import SIZES, render_persona

# Each persona card style has its own size. Product pictures share the team card's size,
# but they never contain a persona, so they never reach this tool.
STYLE_BY_SIZE = {size: style for style, size in SIZES.items() if style != "product"}


def infer_locale(asset_path, name_form_seen):
    folder = asset_path.split("/")[1]  # "assets/<folder>/file.png"
    if folder in LOCALES:
        return folder
    if any("؀" <= ch <= "ۿ" for ch in name_form_seen):
        return "ar-SA"
    if any("゠" <= ch <= "ヿ" for ch in name_form_seen):
        return "ja-JP"
    return "en-US"


def _pick_name_form(persona, locale, name_form_seen):
    """Same pattern as the old image: plain local name, or local name + Latin in brackets."""
    forms = persona.names[locale]
    bracketed = "(" in name_form_seen or "（" in name_form_seen
    return forms[-1] if bracketed and len(forms) > 1 else forms[0]


def observe(old_bytes, asset_path, name_form_seen):
    """Work out layout, locale, background and name pattern from the old image."""
    image = Image.open(BytesIO(old_bytes)).convert("RGB")
    style = STYLE_BY_SIZE.get(image.size)
    if style is None:
        raise ValueError(f"Unknown card size {image.size} for {asset_path}")
    r, g, b = image.getpixel((3, image.height - 3))  # bottom-left corner is always background
    return {"style": style, "locale": infer_locale(asset_path, name_form_seen),
            "background": f"#{r:02X}{g:02X}{b:02X}", "name_form_seen": name_form_seen}


def redraw(observed, persona, out_path):
    name = _pick_name_form(persona, observed["locale"], observed["name_form_seen"])
    render_persona(out_path, observed["style"], observed["locale"], persona, name, observed["background"])


def replace_persona(old_bytes, asset_path, name_form_seen, new_path, scratch_path):
    """Draw the approved-persona version at new_path.

    As a layout check, first redraw the OLD persona from the same observations into
    scratch_path. If that matches the old file byte for byte, the observations were right,
    so the new image differs from the old one only in the person shown."""
    observed = observe(old_bytes, asset_path, name_form_seen)
    redraw(observed, JORDAN_VALE, scratch_path)
    layout_match = scratch_path.read_bytes() == old_bytes
    scratch_path.unlink()
    redraw(observed, PRIYA_NAIR, new_path)
    return observed, layout_match
