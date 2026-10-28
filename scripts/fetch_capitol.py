#!/usr/bin/env python3
"""Refresh the offline Cigar Capitol extracts in references/.

Cigar Capitol publishes records at https://cigarcapitol.com/dictionary/<slug>/
each carrying Definition / Why it matters / In context / Related terms. Those
blocks are what makes the source worth caching: the "context" sentence is the
everyday phrasing, which is what a bilingual answer needs.

Two kinds of output:

    references/capitol-index.md   every term on the site - slug, title, one-line
                                  gloss and category. Built from the index page,
                                  one request total.
    references/<category>.md      full Definition / Why it matters / In context
                                  blocks for the categories this skill relies on.

The distinction matters because relevant terms are scattered across categories
rather than living in one. Plume vs Mold - the single most-asked storage
question - sits under Production & Curing, not Storage & Aging, and was missed
by an earlier version that only scraped a hardcoded slug list. Discovery-driven
selection is what prevents that class of gap recurring.

Usage:
    python3 scripts/fetch_capitol.py                       # index + all categories
    python3 scripts/fetch_capitol.py --index-only          # cheap, one request
    python3 scripts/fetch_capitol.py --category "Storage & Aging"
    python3 scripts/fetch_capitol.py --list                # show what exists
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import time
import urllib.request
from pathlib import Path

INDEX_URL = "https://cigarcapitol.com/dictionary"
ROOT = "https://cigarcapitol.com/dictionary/{}/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
TIMEOUT = 30
POLITE_DELAY = 0.3

# Every category this skill's own features rest on:
#   Storage & Aging      -> humidity, beetles, calibration, storage failures
#   Growing & Terroir    -> why a region's leaf behaves the way it does
#   Tobacco & Leaf       -> wrapper varieties, which decide flavour group
#   Production & Curing  -> fermentation, and Plume vs Mold
#   Anatomy              -> wrapper / binder / filler / ligero, the spec fields
#   Flavor & Tasting     -> strength, body, finish, for pairing questions
CATEGORIES = [
    "Storage & Aging",
    "Growing & Terroir",
    "Tobacco & Leaf",
    "Production & Curing",
    "Anatomy",
    "Flavor & Tasting",
]

FILENAMES = {
    "Storage & Aging": "storage-terms.md",
    "Growing & Terroir": "terroir.md",
    "Tobacco & Leaf": "leaf-varieties.md",
    "Production & Curing": "production-curing.md",
    "Anatomy": "anatomy.md",
    "Flavor & Tasting": "flavour-tasting.md",
}

HEADINGS = {
    "Storage & Aging": "Storage & Aging Terms",
    "Growing & Terroir": "Growing Regions & Leaf Behaviour",
    "Tobacco & Leaf": "Leaf Varieties & Wrapper Types",
    "Production & Curing": "Production & Curing",
    "Anatomy": "Cigar Anatomy & Component Terms",
    "Flavor & Tasting": "Flavour, Strength & Tasting Terms",
}

INTROS = {
    "Storage & Aging": (
        "Storage failures - humidity swings, beetles, plume mistaken for mould. Chinese "
        "renderings must paraphrase these definitions, never claim to translate canon."
    ),
    "Growing & Terroir": (
        "Why a region's leaf behaves as it does. The bridge between a spec sheet's wrapper "
        "value and a flavour group - see references/flavour-groups.md."
    ),
    "Tobacco & Leaf": (
        "Wrapper and filler varieties. This is the primary evidence for assigning a cigar "
        "to an odour group, since odour follows wrapper fermentation rather than taste."
    ),
    "Production & Curing": (
        "How leaf is fermented and finished. Carries Plume vs Mold, the criterion behind "
        "the most common false alarm in any collection."
    ),
    "Anatomy": (
        "The component vocabulary used by spec sheets - wrapper, binder, filler and the "
        "priming grades inside the filler."
    ),
    "Flavor & Tasting": (
        "Strength, body and finish. This is what answers how strong a cigar reads and how "
        "it sits alongside a drink."
    ),
}

CARD_RE = re.compile(
    r'<a href="/dictionary/(?P<slug>[a-z0-9-]+)" class="tcard">.*?'
    r'<div class="tt">(?P<title>.*?)</div>'
    r'(?:<div class="pr">(?P<pron>.*?)</div>)?'
    r'<div class="dd">(?P<gloss>.*?)</div>'
    r'<div class="cc">(?P<cat>.*?)</div>',
    re.S,
)

TERM_RE = re.compile(r'<h1 class="term">\s*(?P<t>[^<]+?)\s*</h1>')
PRON_RE = re.compile(r'<div class="pron">\s*(?P<p>[^<]+?)\s*</div>')
VTAG_RE = re.compile(r'<span class="vtag">\s*(?P<c>[^<]+?)\s*</span>')

# A page body is a stack of <div class="field"><div class="lb">label</div>...</div>.
# "In context" stores its sentence in a .quote div rather than .vl.
FIELD_RE = re.compile(
    r'<div class="field">\s*<div class="lb">\s*(?P<label>[^<]+?)\s*</div>\s*'
    r'<div class="(?:vl|quote)">(?P<body>.*?)</div>',
    re.S,
)
PILL_RE = re.compile(r'<a href="/dictionary/[^"]*"\s+class="pill">\s*(?P<t>[^<]+?)\s*</a>')


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean(raw: str) -> str:
    raw = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(re.sub(r"\s+", " ", raw)).strip()
    return html.unescape(text)


def unescape_amp(match: re.Match[str]) -> str:
    return html.unescape(match.group(0))


def discover() -> list[dict[str, str]]:
    """Read the whole dictionary from the index page in a single request."""
    page = get(INDEX_URL)
    terms: list[dict[str, str]] = []
    for m in CARD_RE.finditer(page):
        terms.append(
            {
                "slug": m.group("slug"),
                "title": clean(m.group("title")),
                "pron": clean(m.group("pron")) if m.group("pron") else "",
                "gloss": clean(m.group("gloss")),
                "category": clean(m.group("cat")),
            }
        )
    if not terms:
        raise SystemExit("error: no terms discovered - the index page layout changed")
    return terms


def extract(page: str) -> dict[str, str]:
    """Pull the named blocks out of one dictionary entry."""
    # Strip style/script first: inline CSS holds braces and quotes that
    # otherwise bleed into the extracted definitions.
    page = re.sub(r"<script.*?</script>", "", page, flags=re.S)
    page = re.sub(r"<style.*?</style>", "", page, flags=re.S)

    out: dict[str, str] = {}
    for m in FIELD_RE.finditer(page):
        label = clean(m.group("label"))
        body = m.group("body")
        if label == "Related terms":
            pills = ", ".join(clean(p) for p in PILL_RE.findall(body))
            if pills:
                out[label] = pills
            continue
        text = clean(body)
        if text and label not in out:
            out[label] = text

    tm = TERM_RE.search(page)
    if tm:
        out["_term"] = clean(tm.group("t"))
    pm = PRON_RE.search(page)
    if pm:
        out["_pron"] = clean(pm.group("p"))
    cm = VTAG_RE.search(page)
    if cm:
        out["_category"] = clean(cm.group("c"))
    return out


def render_index(terms: list[dict[str, str]]) -> str:
    lines = [
        "# Cigar Capitol - Complete Term Index",
        "",
        "Every term the dictionary publishes, discovered from the index page rather than",
        "from a hand-kept list. Search here first: if a term exists, this file knows its",
        "slug and category, and the same slug resolves a page with the full entry.",
        "",
        "```bash",
        "# find terms about a subject",
        "grep -n -i 'mold\\|plume\\|beetle' references/capitol-index.md",
        "```",
        "",
        "Short glosses are abridged from the source page. Full entries for the categories",
        "this skill depends on are cached in the sibling files listed at the end.",
        "",
    ]
    by_cat: dict[str, list[dict[str, str]]] = {}
    for t in terms:
        by_cat.setdefault(t["category"], []).append(t)

    for cat in sorted(by_cat, key=lambda c: (c not in CATEGORIES, c)):
        group = sorted(by_cat[cat], key=lambda t: t["title"].lower())
        marker = "" if cat in CATEGORIES else "  (index only — fetch on demand)"
        lines.append(f"## {cat} — {len(group)} terms{marker}")
        lines.append("")
        for t in group:
            pron = f" /{t['pron']}/ | " if t["pron"] else ""
            lines.append(f"### {t['title']}")
            lines.append(f"`{pron}{t['category']}` — `{t['slug']}`")
            lines.append(t["gloss"])
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_category(cat: str, slugs: list[dict[str, str]], outdir: Path) -> int:
    lines = [f"# {HEADINGS[cat]}", "", INTROS[cat], ""]
    ok = 0
    for t in slugs:
        try:
            page = get(ROOT.format(t["slug"]))
        except urllib.error.URLError as exc:
            print(f"  skip {t['slug']}: {exc}", file=sys.stderr)
            continue
        time.sleep(POLITE_DELAY)
        blocks = extract(page)
        if not blocks or "Definition" not in blocks:
            print(f"  skip {t['slug']}: no content blocks found", file=sys.stderr)
            continue
        ok += 1
        name = blocks.get("_term", t["title"])
        pron = blocks.get("_pron", t["pron"])
        lines.append(f"## {name}")
        meta = " | ".join(x for x in (pron, cat) if x)
        if meta:
            lines.append(f"*{meta}*")
        lines.append(f"`<https://cigarcapitol.com/dictionary/{t['slug']}/>`")
        for key in ("Definition", "Why it matters", "In context", "Related terms"):
            if blocks.get(key):
                lines.append(f"- **{key}**: {blocks[key]}")
        lines.append("")

    if ok == 0:
        print(f"error: nothing retrieved for {cat}; keeping existing file", file=sys.stderr)
        return 0
    path = outdir / FILENAMES[cat]
    path.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")
    print(f"  wrote {path} ({ok} entries)")
    return ok


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("--outdir", type=Path, default=here.parent / "references")
    ap.add_argument("--index-only", action="store_true", help="build the index, skip detail fetches")
    ap.add_argument("--category", action="append", choices=CATEGORIES, help="limit to one category")
    ap.add_argument("--list", action="store_true", help="show discovered counts and exit")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    print("discovering terms from the index page ...", file=sys.stderr)
    terms = discover()
    counts: dict[str, int] = {}
    for t in terms:
        counts[t["category"]] = counts.get(t["category"], 0) + 1
    print(f"  {len(terms)} terms available", file=sys.stderr)

    if args.list:
        for cat, n in sorted(counts.items(), key=lambda kv: -kv[1]):
            print(f"  {n:4}  {cat}")
        return 0

    index_path = args.outdir / "capitol-index.md"
    index_path.write_text(render_index(terms), encoding="utf-8")
    print(f"  wrote {index_path} ({len(terms)} terms)")
    if args.index_only:
        return 0

    wanted = args.category or CATEGORIES
    total = 0
    for cat in wanted:
        group = sorted([t for t in terms if t["category"] == cat], key=lambda t: t["title"].lower())
        if not group:
            continue
        print(f"fetching {len(group)} full entries for {cat} ...", file=sys.stderr)
        total += render_category(cat, group, args.outdir)
    print(f"  {total} full entries cached", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
