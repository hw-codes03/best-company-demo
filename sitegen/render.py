"""Draws the PNG images: persona cards with name, email and avatar, and plain product pictures.

Arabic images are mirrored: the avatar sits on the right and text is right-aligned
and shaped right to left. Email addresses are always drawn left to right.
"""

from PIL import Image, ImageDraw, ImageFont

from . import config
from .strings import TEXT

# Image sizes for each style, in pixels (width, height).
SIZES = {
    "team_card": (640, 300),
    "banner": (800, 260),
    "testimonial": (640, 320),
    "signature": (600, 200),
    "product": (640, 300),
}

# A few soft background colours; the plan picks one per image.
BACKGROUNDS = ["#F5F7FA", "#FFF8EE", "#EEF6F3", "#F3F0FA", "#FDF1F1"]


def _font(locale, size, bold=False):
    """Pick a font that can draw the locale's script."""
    if locale == "ja-JP":
        path = config.FONT_JAPANESE  # this Japanese font has no bold variant
    elif locale == "ar-SA":
        path = config.FONT_ARABIC_BOLD if bold else config.FONT_ARABIC
    else:
        path = config.FONT_LATIN_BOLD if bold else config.FONT_LATIN
    # The Raqm engine handles right-to-left text and joins Arabic letters correctly.
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


def _fit(locale, value, size, max_width, bold=False):
    """Return the largest font (up to `size`) at which `value` fits inside `max_width` pixels."""
    while size > 10:
        font = _font(locale, size, bold)
        if font.getlength(value) <= max_width:
            return font
        size -= 1
    return _font(locale, size, bold)


def _latin_font(size, bold=False):
    path = config.FONT_LATIN_BOLD if bold else config.FONT_LATIN
    return ImageFont.truetype(path, size, layout_engine=ImageFont.Layout.RAQM)


class _Canvas:
    """A blank image plus helpers that place text on the correct side for the locale."""

    def __init__(self, style, locale, background):
        self.width, self.height = SIZES[style]
        self.locale = locale
        self.rtl = config.LOCALES[locale]["dir"] == "rtl"
        self.image = Image.new("RGB", (self.width, self.height), background)
        self.draw = ImageDraw.Draw(self.image)

    def x(self, from_start):
        """Turn 'distance from the start edge' into an x position (start is right for RTL)."""
        return self.width - from_start if self.rtl else from_start

    def text(self, from_start, y, value, font, fill="#1F2933", force_ltr=False):
        """Draw text aligned to the start edge. Set force_ltr for emails and URLs."""
        anchor = "ra" if self.rtl else "la"
        if force_ltr:
            direction = "ltr"
        else:
            direction = "rtl" if self.rtl else "ltr"
        self.draw.text((self.x(from_start), y), value, font=font, fill=fill,
                       anchor=anchor, direction=direction,
                       language=config.LOCALES[self.locale]["lang"])

    def brand_bar(self):
        """A thin header strip with the brand name and domain, like a site screenshot."""
        self.draw.rectangle([0, 0, self.width, 28], fill="#1F2933")
        self.text(14, 6, f"{config.BRAND_NAME} · {config.DOMAIN}",
                  _latin_font(13), fill="#FFFFFF", force_ltr=True)

    def avatar(self, from_start, cy, radius, persona):
        """A filled circle in the persona's colour with white initials in the middle."""
        cx = self.x(from_start)
        self.draw.ellipse([cx - radius, cy - radius, cx + radius, cy + radius],
                          fill=persona.avatar_color)
        self.draw.text((cx, cy), persona.initials, font=_latin_font(int(radius * 0.8), bold=True),
                       fill="#FFFFFF", anchor="mm")

    def save(self, path):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.image.save(path, format="PNG", optimize=True)


def render_persona(path, style, locale, persona, name_shown, background):
    """Draw one persona image in the given style and save it as a PNG."""
    t = TEXT[locale]
    c = _Canvas(style, locale, background)
    c.brand_bar()
    email_font = _latin_font(20)

    if style == "team_card":
        c.avatar(110, 165, 70, persona)
        c.text(210, 95, name_shown, _fit(locale, name_shown, 32, c.width - 230, bold=True))
        c.text(210, 145, t["role"], _font(locale, 20), fill="#52606D")
        c.text(210, 190, f"{t['contact_label']}:", _font(locale, 16), fill="#52606D")
        c.text(210, 214, persona.email, email_font, force_ltr=True)

    elif style == "banner":
        c.text(40, 50, t["banner_headline"], _fit(locale, t["banner_headline"], 30, c.width - 80, bold=True),
               fill="#0B3C5D")
        c.avatar(100, 170, 55, persona)
        c.text(180, 130, name_shown, _fit(locale, name_shown, 28, c.width - 210, bold=True))
        c.text(180, 178, persona.email, email_font, force_ltr=True)

    elif style == "testimonial":
        c.text(40, 60, t["quote"], _fit(locale, t["quote"], 20, c.width - 80), fill="#3E4C59")
        c.avatar(90, 210, 45, persona)
        c.text(160, 180, name_shown, _fit(locale, name_shown, 24, c.width - 190, bold=True))
        c.text(160, 220, persona.email, _latin_font(18), force_ltr=True)

    elif style == "signature":
        c.avatar(70, 110, 40, persona)
        c.text(130, 55, name_shown, _fit(locale, name_shown, 24, c.width - 150, bold=True))
        c.text(130, 95, t["signature_tagline"], _font(locale, 16), fill="#52606D")
        c.text(130, 125, persona.email, _latin_font(18), force_ltr=True)
        c.text(130, 155, config.DOMAIN, _latin_font(14), fill="#7B8794", force_ltr=True)

    else:
        raise ValueError(f"Unknown persona style: {style}")

    c.save(path)


def render_product(path, locale, caption, background, accent):
    """Draw a plain product picture with no person in it: a few shapes and a caption."""
    c = _Canvas("product", locale, background)
    c.brand_bar()
    d = c.draw
    # A simple 'device' 60 to 240 pixels from the start edge, with white bars inside.
    left, right = sorted((c.x(60), c.x(240)))
    d.rounded_rectangle([left, 60, right, 260], radius=16, fill=accent)
    for i, h in enumerate((60, 110, 85, 140)):
        d.rectangle([left + 25 + i * 35, 240 - h, left + 45 + i * 35, 240], fill="#FFFFFF")
    c.text(280, 130, caption, _fit(locale, caption, 30, c.width - 300, bold=True), fill="#1F2933")
    c.save(path)
