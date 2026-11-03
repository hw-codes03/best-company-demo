"""Crawls the locally served site by following links, starting from the sitemap AND the home page.

For every page it records how it was found, and for every image it records which page
used it and whether the URL came from src, data-src or srcset. Each image file is
downloaded once and fingerprinted with SHA-256.
"""

import hashlib
import re
import urllib.error
import urllib.request
from collections import deque
from dataclasses import dataclass, field
from html.parser import HTMLParser
from urllib.parse import urljoin, urlsplit

from .settings import PUBLIC_BASE, START_PATHS

IMAGE_ATTRIBUTES = ("src", "data-src", "srcset", "data-srcset")


@dataclass
class Link:
    target: str        # public URL of the linked page
    in_footer: bool    # True if the <a> sat inside <footer>


@dataclass
class PageResult:
    url: str                          # public URL
    status: int
    in_sitemap: bool
    found_via: list = field(default_factory=list)   # ("sitemap"|"start"|"link", from_url, in_footer)
    links: list = field(default_factory=list)       # Link objects
    images: list = field(default_factory=list)      # (public image URL, attribute name)
    alts: dict = field(default_factory=dict)        # public image URL -> its alt text


@dataclass
class AssetResult:
    url: str
    status: int
    sha256: str | None
    data: bytes | None


class _PageParser(HTMLParser):
    """Pulls links and image URLs out of one HTML page, noting whether a link is in the footer."""

    def __init__(self):
        super().__init__()
        self.footer_depth = 0
        self.links = []      # (href, in_footer)
        self.images = []     # (url, attribute)
        self.alts = {}       # url -> alt text

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "footer":
            self.footer_depth += 1
        elif tag == "a" and attrs.get("href"):
            self.links.append((attrs["href"], self.footer_depth > 0))
        elif tag == "img":
            for name in IMAGE_ATTRIBUTES:
                value = attrs.get(name)
                if not value:
                    continue
                # srcset lists "url width, url width"; take each URL.
                urls = [part.split()[0] for part in value.split(",")] if "srcset" in name else [value]
                for u in urls:
                    if not u.startswith("data:"):  # skip inline placeholders
                        self.images.append((u, name))
                        self.alts[u] = attrs.get("alt", "")

    def handle_endtag(self, tag):
        if tag == "footer" and self.footer_depth:
            self.footer_depth -= 1


class Crawler:
    def __init__(self, local_base):
        self.local_base = local_base
        self.pages = {}    # public URL -> PageResult
        self.assets = {}   # public URL -> AssetResult

    # --- URL helpers: fetch locally, but always record the public URL. ---
    def to_local(self, public_url):
        return self.local_base + urlsplit(public_url).path

    @staticmethod
    def to_public(path):
        return PUBLIC_BASE + path

    def _fetch(self, public_url):
        try:
            with urllib.request.urlopen(self.to_local(public_url)) as resp:
                return resp.status, resp.read()
        except urllib.error.HTTPError as err:
            return err.code, None

    # --- Crawling ---
    def sitemap_urls(self):
        status, body = self._fetch(PUBLIC_BASE + "/sitemap.xml")
        if status != 200:
            return []
        return [self.to_public(urlsplit(u).path)
                for u in re.findall(r"<loc>\s*(.*?)\s*</loc>", body.decode("utf-8"))]

    def crawl(self):
        """Breadth-first crawl over same-site HTML pages, then download every image found."""
        sitemap = set(self.sitemap_urls())
        queue = deque()
        for url in sorted(sitemap):
            queue.append((url, ("sitemap", None, False)))
        for path in START_PATHS:
            queue.append((self.to_public(path), ("start", None, False)))

        while queue:
            url, via = queue.popleft()
            if url in self.pages:
                self.pages[url].found_via.append(via)
                continue
            status, body = self._fetch(url)
            page = PageResult(url=url, status=status, in_sitemap=url in sitemap, found_via=[via])
            self.pages[url] = page
            if status != 200 or body is None:
                continue
            parser = _PageParser()
            parser.feed(body.decode("utf-8"))
            for href, in_footer in parser.links:
                target = urljoin(url, href).split("#")[0]
                if target.startswith(PUBLIC_BASE) and target.endswith(".html"):
                    page.links.append(Link(target, in_footer))
                    queue.append((target, ("link", url, in_footer)))
            for src, attribute in parser.images:
                page.images.append((urljoin(url, src), attribute))
                page.alts[urljoin(url, src)] = parser.alts.get(src, "")

        for page in self.pages.values():
            for img_url, _ in page.images:
                self.fetch_asset(img_url)
        return self

    def fetch_asset(self, public_url):
        """Download an image once and remember its SHA-256 fingerprint."""
        if public_url not in self.assets:
            status, data = self._fetch(public_url)
            digest = hashlib.sha256(data).hexdigest() if data is not None else None
            self.assets[public_url] = AssetResult(public_url, status, digest, data)
        return self.assets[public_url]
