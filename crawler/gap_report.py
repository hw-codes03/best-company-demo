"""Writes gap_report.md: what the client audit got wrong, compared with the crawl.

Sections: images the audit missed, its false positives, its duplicate rows, and pages
missing from sitemap.xml. Each section says in plain English how it was worked out.
Image previews use relative paths into site/, so GitHub shows them inline.
"""

from collections import defaultdict

from .settings import GAP_REPORT_MD, OUTDATED_PERSONA, PUBLIC_BASE

STATUS_WORDS = {
    "outdated": "teal avatar: the outdated persona",
    "approved": "orange avatar: the approved persona",
    "other_person": "a round avatar in a different colour: someone else",
    "no_person": "no avatar at all",
    "not_found": "the image could not be downloaded",
}


def _short(url):
    """Turn a public URL into a short path like /en-US/team.html for readability."""
    return url.replace(PUBLIC_BASE, "")


def _thumb(asset_url, width=240):
    path = "site" + _short(asset_url)
    return f'<img src="{path}" width="{width}" alt="{_short(asset_url)}">'


class _Facts:
    """Everything the report needs, worked out once from the crawl, audit and manifest."""

    def __init__(self, crawler, audit_rows, manifest):
        self.crawler, self.audit, self.manifest = crawler, audit_rows, manifest
        self.pages = crawler.pages
        self.status_of = {r.asset_url: r for r in manifest}  # same file, same status
        self.uses = defaultdict(list)  # asset URL -> manifest rows seen by the crawler
        for r in manifest:
            if r.source != "client_audit":
                self.uses[r.asset_url].append(r)
        self.audit_urls = {a.image_url for a in audit_rows}
        self.audit_pairs = {(a.page_url, a.image_url) for a in audit_rows}
        self.outdated_urls = sorted({r.asset_url for r in manifest if r.status == "outdated"})

    def why_hard(self, asset_url):
        """Explain why a crawler that only reads the sitemap and src would miss this file."""
        uses = self.uses[asset_url]
        hidden = all(not self.pages[u.page_url].in_sitemap for u in uses)
        lazy = all(u.load_attributes == "data-src" for u in uses)
        if hidden and lazy:
            return "only on a footer-only page, and only lazy-loaded via `data-src`"
        if hidden:
            return "only on a footer-only page that is missing from `sitemap.xml`"
        if lazy:
            return "only lazy-loaded: its real URL is in `data-src`, not `src`"
        return "a normal `<img src>` on a page in the sitemap; the audit simply missed it"


def _summary(f, missed, fps, exact, same_file, hidden_pages):
    caught = len(set(f.outdated_urls) & f.audit_urls)
    return [
        "# Gap report: client audit vs. full crawl",
        "",
        "Synthetic data only. Best Company, its people and every `example.com` address are fictional.",
        "",
        f"The crawler served `site/` locally, followed every link and downloaded every image. "
        f"It then compared what it found with the {len(f.audit)} rows of `client_audit.csv`.",
        "",
        "| Measure | Count |",
        "|---|---|",
        f"| Pages found by following links | {len(f.pages)} |",
        f"| Pages listed in `sitemap.xml` | {sum(p.in_sitemap for p in f.pages.values())} |",
        f"| Image uses found (page + image pairs) | {sum(1 for r in f.manifest if r.source != 'client_audit')} |",
        f"| Distinct image URLs | {len(f.uses)} |",
        f"| Distinct image contents (by SHA-256) | {len({r.file_sha256 for r in f.manifest if r.file_sha256})} |",
        f"| Image URLs showing the outdated persona | {len(f.outdated_urls)} |",
        f"| ...of which the client audit listed | {caught} ({100 * caught / max(len(f.outdated_urls), 1):.0f}%) |",
        f"| **Outdated images the audit missed** | **{len(missed)}** |",
        f"| **Audit false positives** | **{len(fps)}** |",
        f"| **Audit duplicate rows** | **{len(exact) + len(same_file)}** "
        f"({len(exact)} exact, {len(same_file)} same file from another page) |",
        f"| **Pages missing from the sitemap** | **{len(hidden_pages)}** |",
        "",
    ]


def _missed_section(f, missed):
    out = ["## 1. Outdated images the client audit missed", "",
           "**How this was found:** the detector checked every downloaded image for a round "
           f"{OUTDATED_PERSONA['avatar']} avatar (the outdated persona in the client brief). Any such image "
           "whose URL appears in no audit row is listed here. The reason column says what made each "
           "one easy to overlook.", ""]
    out += ["| Preview | Image | Used on | Why it was easy to miss |", "|---|---|---|---|"]
    for url in missed:
        used_on = "<br>".join(f"`{_short(u.page_url)}` ({u.load_attributes})" for u in f.uses[url])
        out.append(f"| {_thumb(url)} | `{_short(url)}` | {used_on} | {f.why_hard(url)} |")

    # Files the audit did list, but not on every page where they appear.
    partial = [r for r in f.manifest if r.status == "outdated" and r.source == "crawler"
               and r.asset_url in f.audit_urls]
    if partial:
        out += ["", "**Also worth knowing:** these files are in the audit, but they appear on more "
                "pages than it lists. Replacing the file fixes every page, so no extra work is "
                "needed. Just check those pages afterwards.", ""]
        out += [f"- `{_short(r.asset_url)}` also appears on `{_short(r.page_url)}`" for r in partial]
    return out + [""]


def _false_positive_section(f, fps):
    out = ["## 2. Client audit false positives", "",
           "**How this was found:** each audited image was downloaded and checked for the outdated "
           "persona's teal round avatar. These rows point at images that don't have one. The colour "
           "found is shown so you can see why. A round avatar with the same \"JV\" initials but a "
           "different colour is a different person, so replacing it would be a mistake.", "",
           "| Preview | Audit row | Page | Image | What the image actually shows |",
           "|---|---|---|---|---|"]
    for a in fps:
        r = f.status_of[a.image_url]
        colour = f" (`{r.avatar_hex}`)" if r.avatar_hex else ""
        out.append(f"| {_thumb(a.image_url)} | {a.row} | `{_short(a.page_url)}` | "
                   f"`{_short(a.image_url)}` | {STATUS_WORDS[r.status]}{colour} |")
    return out + [""]


def _duplicate_section(f, exact, same_file, same_content):
    out = ["## 3. Duplicate rows in the client audit", "",
           "**How this was found:** audit rows were grouped by page URL plus image URL (exact "
           "duplicates), then by image URL alone (the same file listed again from another page). "
           "Images were also grouped by SHA-256, which catches different URLs serving the very same "
           "picture.", ""]
    out += ["**Exact duplicates** (same page, same image):", ""]
    out += [f"- Rows {', '.join(map(str, rows))}: `{_short(img)}` on `{_short(page)}`"
            for (page, img), rows in exact] or ["- None"]
    out += ["", "**Same file listed again from another page.** One replacement fixes all of them, "
            "so count it as one fix:", ""]
    out += [f"- Rows {', '.join(map(str, rows))}: `{_short(img)}` (listed from "
            f"{', '.join(f'`{_short(p)}`' for p in pages)})"
            for img, rows, pages in same_file] or ["- None"]
    out += ["", "**Same picture at different URLs** (identical SHA-256). Not a duplicate row: each "
            "URL is a separate file to replace, but they can share one new image:", ""]
    out += [f"- `{group}`: " + ", ".join(f"`{_short(u)}`" for u in urls) +
            (f" (audit rows {', '.join(map(str, rows))})" if rows else "")
            for group, urls, rows in same_content] or ["- None"]
    return out + [""]


def _sitemap_section(f, hidden_pages):
    out = ["## 4. Pages missing from the sitemap", "",
           "**How this was found:** the crawler started from every URL in `sitemap.xml` plus the "
           "home page, then followed every link on every page. Any page it reached that isn't in "
           "the sitemap is listed here, along with where its links sit in the HTML.", "",
           "| Page | Linked from | Where the link is | Outdated images on it |", "|---|---|---|---|"]
    for p in hidden_pages:
        # Links from other pages only; a page linking to itself doesn't help anyone find it.
        links_in = [via for via in p.found_via if via[0] == "link" and via[1] != p.url]
        froms = sorted({via[1] for via in links_in})
        places = {via[2] for via in links_in}
        where = "footer only" if places == {True} else ("menu/body only" if places == {False} else "footer and body")
        outdated = [_short(i) for i, _ in p.images if f.status_of[i].status == "outdated"]
        out.append(f"| `{_short(p.url)}` | {len(froms)} other pages: " +
                   ", ".join(f"`{_short(u)}`" for u in froms) +
                   f" | {where} | " + (", ".join(f"`{o}`" for o in outdated) or "none") + " |")
    return out + [""]


def write_gap_report(crawler, audit_rows, manifest):
    f = _Facts(crawler, audit_rows, manifest)

    missed = [u for u in f.outdated_urls if u not in f.audit_urls]
    fps = [a for a in audit_rows if f.status_of[a.image_url].status != "outdated"]

    by_pair, by_image = defaultdict(list), defaultdict(list)
    for a in audit_rows:
        by_pair[(a.page_url, a.image_url)].append(a.row)
        by_image[a.image_url].append(a)
    exact = sorted(((k, v) for k, v in by_pair.items() if len(v) > 1), key=lambda kv: kv[1])
    same_file = []
    for img, rows in sorted(by_image.items()):
        pages = sorted({a.page_url for a in rows})
        if len(pages) > 1:
            same_file.append((img, [a.row for a in rows], pages))

    groups = defaultdict(set)
    for r in manifest:
        if r.duplicate_group_id:
            groups[r.duplicate_group_id].add(r.asset_url)
    same_content = [(g, sorted(urls), sorted(a.row for u in urls for a in by_image.get(u, [])))
                    for g, urls in sorted(groups.items()) if len(urls) > 1]

    hidden_pages = sorted((p for p in crawler.pages.values() if p.status == 200 and not p.in_sitemap),
                          key=lambda p: p.url)

    lines = (_summary(f, missed, fps, exact, same_file, hidden_pages)
             + _missed_section(f, missed) + _false_positive_section(f, fps)
             + _duplicate_section(f, exact, same_file, same_content)
             + _sitemap_section(f, hidden_pages))
    GAP_REPORT_MD.write_text("\n".join(lines), encoding="utf-8")
    return {"missed": missed, "false_positives": fps, "exact_duplicates": exact,
            "same_file_rows": same_file, "same_content_groups": same_content,
            "hidden_pages": hidden_pages}
