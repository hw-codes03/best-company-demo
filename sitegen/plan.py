"""Decides the whole site in memory before anything is written: pages, images and traps.

The plan is the single source of truth. The HTML writer, the client audit and the
answer key are all built from it, so they always agree with each other.

Traps seeded here:
  1. Hidden pages: en-US/legacy-team and ar-SA/press-archive are linked only from the
     footer and are left out of sitemap.xml.
  2. Lazy loading: some <img> tags carry the real URL in data-src, not src.
  3. Reuse: the same image file appears on several pages (one even across locales).
  4. Decoys: images of Jordan Vail, a different person with the same initials.
"""

import random
from dataclasses import dataclass, field

from . import config
from .personas import ALL_PERSONAS, JORDAN_VALE
from .render import BACKGROUNDS
from .strings import TEXT

MENU_PAGES = ["index", "about", "team", "news", "contact"]
HIDDEN_PAGES = {"en-US": ["legacy-team"], "ar-SA": ["press-archive"]}

# Exactly 40 distinct image files: 20 outdated, 6 approved, 5 decoys, 9 with no person.
# Three of the outdated ones are the reused files described in REUSED below.
NEW_IMAGE_QUOTA = {"jordan_vale": 17, "priya_nair": 6, "jordan_vail": 5, None: 9}

# Reused files: (name, locale it is drawn in, style, pages that show it).
REUSED = [
    ("A", "en-US", "team_card", ["en-US/team", "en-US/about", "en-US/legacy-team"]),
    ("B", "ja-JP", "banner", ["ja-JP/index", "ja-JP/news"]),
    ("C", "en-US", "signature", ["en-US/contact", "ar-SA/contact"]),  # shared across locales
]

PERSONA_STYLES = ["team_card", "banner", "testimonial", "signature"]
FILE_PREFIX = {"team_card": "team", "banner": "hero", "testimonial": "quote",
               "signature": "sig", "product": "product"}
PRODUCT_ACCENTS = ["#0B3C5D", "#328CC1", "#1D7874", "#D9B310", "#8E44AD"]
LAZY_LOAD_CHANCE = 0.3  # share of <img> tags that use data-src instead of src


@dataclass
class ImageAsset:
    path: str                 # path inside site/, e.g. "assets/en-US/team-03.png"
    locale: str               # locale whose script and layout the image is drawn in
    style: str
    persona_key: str | None   # None means a product image with no person
    name_shown: str | None
    background: str
    caption: str | None = None
    accent: str | None = None
    refs: list = field(default_factory=list)  # (page path, "src" or "data-src")


@dataclass
class Page:
    locale: str
    slug: str
    hidden: bool              # True = footer-only and missing from sitemap.xml
    slots: list = field(default_factory=list)  # (ImageAsset, "src" or "data-src")

    @property
    def key(self):
        return f"{self.locale}/{self.slug}"

    @property
    def path(self):
        return f"{self.key}.html"


@dataclass
class SitePlan:
    pages: list
    images: list              # distinct image files, in creation order


def _make_pages(rng):
    """Create every page and give 10 of the 17 pages three image slots (the rest get two)."""
    pages = []
    for locale in config.LOCALES:
        pages += [Page(locale, slug, hidden=False) for slug in MENU_PAGES]
        pages += [Page(locale, slug, hidden=True) for slug in HIDDEN_PAGES.get(locale, [])]
    three_slot = set(rng.sample(range(len(pages)), 10))
    sizes = {p.key: (3 if i in three_slot else 2) for i, p in enumerate(pages)}
    return pages, sizes


def _new_asset(rng, locale, style, persona_key, counters, folder=None):
    """Create one image description with random-but-seeded visual details."""
    folder = folder or locale
    counters[folder] = counters.get(folder, 0) + 1
    path = f"assets/{folder}/{FILE_PREFIX[style]}-{counters[folder]:02d}.png"
    asset = ImageAsset(path=path, locale=locale, style=style, persona_key=persona_key,
                       name_shown=None, background=rng.choice(BACKGROUNDS))
    if persona_key:
        asset.name_shown = rng.choice(ALL_PERSONAS[persona_key].names[locale])
    else:
        asset.caption = rng.choice(TEXT[locale]["product_captions"])
        asset.accent = rng.choice(PRODUCT_ACCENTS)
    return asset


def _attempt(rng):
    """Build one candidate plan. It may break a trap rule; build_plan() checks and retries."""
    pages, sizes = _make_pages(rng)
    by_key = {p.key: p for p in pages}
    filled = {p.key: [] for p in pages}
    counters, images = {}, []

    # 1. Place the reused files first.
    for _name, locale, style, page_keys in REUSED:
        folder = "shared" if len({k.split("/")[0] for k in page_keys}) > 1 else None
        asset = _new_asset(rng, locale, style, JORDAN_VALE.key, counters, folder)
        images.append(asset)
        for key in page_keys:
            filled[key].append(asset)

    # 2. Fill every remaining slot with a brand-new image from the shuffled quota.
    quota = [k for k, n in NEW_IMAGE_QUOTA.items() for _ in range(n)]
    rng.shuffle(quota)
    for page in pages:
        while len(filled[page.key]) < sizes[page.key]:
            persona_key = quota.pop()
            style = rng.choice(PERSONA_STYLES) if persona_key else "product"
            asset = _new_asset(rng, page.locale, style, persona_key, counters)
            images.append(asset)
            filled[page.key].append(asset)
    assert not quota, "slot count and image quota must match exactly"

    # 3. Shuffle the order on each page and decide src vs data-src for every tag.
    for page in pages:
        assets = filled[page.key]
        rng.shuffle(assets)
        for asset in assets:
            method = "data-src" if rng.random() < LAZY_LOAD_CHANCE else "src"
            by_key[page.key].slots.append((asset, method))
            asset.refs.append((page.path, method))
    return SitePlan(pages=pages, images=images)


def hard_to_find(asset, pages_by_path):
    """True if a simple crawler would miss this image: every use is on a hidden page or lazy-loaded."""
    return all(pages_by_path[p].hidden or m == "data-src" for p, m in asset.refs)


def _traps_ok(plan):
    """Check that every trap is really present, so no run can silently lose one."""
    pages_by_path = {p.path: p for p in plan.pages}
    outdated = [a for a in plan.images if a.persona_key == "jordan_vale"]
    for locale in config.LOCALES:
        local = [a for a in plan.images if a.locale == locale]
        if not any(a.persona_key == "jordan_vail" for a in local):
            return False  # every locale needs at least one decoy
        if not any(a.persona_key == "priya_nair" for a in local):
            return False  # and at least one already-approved image
    for page in plan.pages:
        if page.hidden and not any(a.persona_key == "jordan_vale" for a, _ in page.slots):
            return False  # each hidden page must hide at least one outdated image
    only_lazy = [a for a in outdated if all(m == "data-src" for _, m in a.refs)]
    hard = [a for a in outdated if hard_to_find(a, pages_by_path)]
    return len(only_lazy) >= 2 and 3 <= len(hard) <= 5


def build_plan(seed=config.SEED):
    """Return the first candidate plan (in seeded order) that contains every trap."""
    rng = random.Random(seed)
    for _ in range(1000):
        plan = _attempt(rng)
        if _traps_ok(plan):
            return plan
    raise RuntimeError("Could not satisfy the trap rules; check the quotas.")
