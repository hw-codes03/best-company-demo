"""Writes the fake website to disk: PNG images, one HTML file per page, and sitemap.xml."""

import shutil
from html import escape

from . import config
from .personas import ALL_PERSONAS
from .render import render_persona, render_product
from .strings import LANGUAGE_NAMES, PAGE_TITLES, TEXT

# A 1x1 transparent GIF. Lazy-loaded images show this until a script swaps in data-src.
PLACEHOLDER = "data:image/gif;base64,R0lGODlhAQABAAAAACH5BAEKAAEALAAAAAABAAEAAAICTAEAOw=="

# The fixed "last modified" date written into sitemap.xml, so output never changes between runs.
SITEMAP_LASTMOD = "2026-11-02"

LAZY_SCRIPT = """<script>
  // Swap each lazy image's data-src into src (a stand-in for a real lazy-loading library).
  document.querySelectorAll("img[data-src]").forEach(function (img) {
    img.src = img.dataset.src;
  });
</script>"""


def _render_images(plan):
    """Draw every distinct image file once, however many pages use it."""
    for asset in plan.images:
        out = config.SITE_DIR / asset.path
        if asset.persona_key:
            persona = ALL_PERSONAS[asset.persona_key]
            render_persona(out, asset.style, asset.locale, persona, asset.name_shown, asset.background)
        else:
            render_product(out, asset.locale, asset.caption, asset.background, asset.accent)


def _img_tag(asset, method, locale):
    """Build one <img> tag. Lazy images keep the real URL in data-src, not src."""
    url = "../" + asset.path  # pages live one folder down, e.g. site/en-US/team.html
    alt = TEXT[locale]["alt_person" if asset.persona_key else "alt_product"]
    if method == "data-src":
        return (f'<img class="lazyload" src="{PLACEHOLDER}" data-src="{url}" '
                f'alt="{escape(alt)}" loading="lazy">')
    return f'<img src="{url}" alt="{escape(alt)}">'


def _page_html(page, plan):
    """Build the full HTML for one page: menu, images, and a footer with the hidden links."""
    loc = page.locale
    info = config.LOCALES[loc]
    titles = PAGE_TITLES[loc]
    menu = "\n".join(f'      <a href="{slug}.html">{escape(titles[slug])}</a>'
                     for slug in ("index", "about", "team", "news", "contact"))
    images = "\n".join(f"      <figure>{_img_tag(a, m, loc)}</figure>" for a, m in page.slots)

    # The footer is the ONLY place that links to this locale's hidden pages.
    hidden_links = "\n".join(
        f'      <a href="{p.slug}.html">{escape(titles[p.slug])}</a>'
        for p in plan.pages if p.locale == loc and p.hidden)
    # Language switcher: same page in other locales if it exists, otherwise their home page.
    existing = {p.key for p in plan.pages}
    languages = "\n".join(
        f'      <a href="../{other}/{page.slug if f"{other}/{page.slug}" in existing else "index"}.html" '
        f'hreflang="{other}">{LANGUAGE_NAMES[other]}</a>'
        for other in config.LOCALES if other != loc)

    canonical = f"{config.BASE_URL}/{page.path}"
    return f"""<!doctype html>
<html lang="{loc}" dir="{info['dir']}">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{escape(titles[page.slug])} | {config.BRAND_NAME}</title>
  <link rel="canonical" href="{canonical}">
</head>
<body>
  <header>
    <a class="brand" href="index.html">{config.BRAND_NAME}</a>
    <nav>
{menu}
    </nav>
  </header>
  <main>
    <h1>{escape(titles[page.slug])}</h1>
    <section class="images">
{images}
    </section>
  </main>
  <footer>
    <p>{escape(TEXT[loc]['footer_copyright'])}</p>
    <nav class="footer-links">
{hidden_links}
    </nav>
    <nav class="languages" aria-label="{escape(TEXT[loc]['language_label'])}">
{languages}
    </nav>
  </footer>
{LAZY_SCRIPT}
</body>
</html>
"""


def _sitemap_xml(plan):
    """List every page EXCEPT the hidden ones; leaving them out is one of the traps."""
    urls = "\n".join(
        f"  <url><loc>{config.BASE_URL}/{p.path}</loc><lastmod>{SITEMAP_LASTMOD}</lastmod></url>"
        for p in plan.pages if not p.hidden)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
            f"{urls}\n</urlset>\n")


def write_site(plan):
    """Delete any previous output and write the whole site from the plan."""
    if config.SITE_DIR.exists():
        shutil.rmtree(config.SITE_DIR)  # only ever removes the generated site/ folder
    _render_images(plan)
    for page in plan.pages:
        out = config.SITE_DIR / page.path
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(_page_html(page, plan), encoding="utf-8")
    (config.SITE_DIR / "sitemap.xml").write_text(_sitemap_xml(plan), encoding="utf-8")
