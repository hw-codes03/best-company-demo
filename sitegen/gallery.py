"""Writes gallery.md: a sample of the generated images that GitHub shows inline.

Image links are relative paths, so they work on GitHub and in a local checkout.
The captions deliberately say nothing about who is in each picture, so the gallery
never gives away the answer key. Spotting the decoys is up to you.
"""

import random

from . import config

KINDS = ["jordan_vale", "priya_nair", "jordan_vail", None]


def _pick_sample(plan):
    """One image of each kind per locale (12 total), in a seeded random order."""
    rng = random.Random(f"{config.SEED}-gallery")
    sample = []
    for locale in config.LOCALES:
        local = [a for a in plan.images if a.locale == locale and not a.path.startswith("assets/shared/")]
        picks = [rng.choice([a for a in local if a.persona_key == k]) for k in KINDS]
        rng.shuffle(picks)
        sample += picks
    return sample


def write_gallery(plan):
    sample = _pick_sample(plan)
    lines = [
        "# Gallery: sample of generated images",
        "",
        f"{len(sample)} of the {len(plan.images)} image files in `site/assets/`, four per locale. "
        "Each locale's four include the outdated persona, the approved persona, a look-alike "
        "decoy and a product image, but the captions don't say which is which.",
        "",
        "Everything here is synthetic: the brand, the people and every example.com email are made up.",
        "",
    ]
    for locale in config.LOCALES:
        lines += [f"## {locale} ({config.LOCALES[locale]['dir'].upper()})", "",
                  "| Image | File | Shown on | Loaded via |", "|---|---|---|---|"]
        for a in (x for x in sample if x.locale == locale):
            pages = "<br>".join(f"`{p}`" for p, _ in a.refs)
            methods = ", ".join(sorted({m for _, m in a.refs}))
            lines.append(f'| <img src="site/{a.path}" width="320" alt="{a.path}"> '
                         f"| `{a.path}` | {pages} | `{methods}` |")
        lines.append("")
    config.GALLERY_MD.write_text("\n".join(lines), encoding="utf-8")
