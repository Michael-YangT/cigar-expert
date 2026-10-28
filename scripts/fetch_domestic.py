#!/usr/bin/env python3
"""Index and read 雪茄123 (xuejia123.com), the only source for Chinese cigars.

Cigar Century carries no Chinese domestic models at all, so asking it about
长城 or 黄鹤楼 returns nothing. This script covers that gap from the one site
that documents them.

Three jobs:

  1. build   walk the 雪茄数据库 tree and record every detail page locally
  2. find    search that local index by Chinese or English keyword
  3. detail  pull one page and return structured fields

The detail pages are unusually well formed - 品牌 / 系列 / 工艺 / 尺寸 / 浓度 /
包装 / 产地 / 原料配方 / 风味品鉴 / 综合评价 - and the 尺寸 line carries length,
ring gauge and vitola together, which is exactly what leads identification.

Index building is the only bulk step, and it touches listing pages only. Detail
pages are fetched one at a time, on request.

Usage:
    python3 scripts/fetch_domestic.py --build-index
    python3 scripts/fetch_domestic.py --find 长城
    python3 scripts/fetch_domestic.py --detail https://www.xuejia123.com/baike1/guochan/changcheng/132/91932.html
    python3 scripts/fetch_domestic.py --check

Exit codes: 0 ok, 1 usage/index problem, 2 network failure.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
INDEX = ROOT / "data" / "xuejia-index.tsv"
SITE = "https://www.xuejia123.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
DELAY = 0.4  # be polite to a small site

# The three top-level sections of 雪茄数据库.
SECTIONS = {
    "guochan": "国产",
    "cuba": "古巴",
    "feigu": "非古",
}

DETAIL_RE = re.compile(r'href="(/baike1/(?:guochan|cuba|feigu)/[^"]*?/(\d+)\.html)"')
# Same pattern without the attribute wrapper, for matching a bare href.
DETAIL_HREF_RE = re.compile(r"(/baike1/(?:guochan|cuba|feigu)/[^/]+(?:/[^/]+)?/\d+\.html)")
ANCHOR_RE = re.compile(r'<a\s[^>]*href="(?P<href>[^"]*)"[^>]*>(?P<text>.*?)</a>', re.S | re.I)

# Field labels on a detail page. Both colon widths occur.
LABELS = [
    "品牌",
    "系列",
    "工艺",
    "尺寸",
    "浓度",
    "包装",
    "产地",
]
SECTION_HEADS = ["基础参数", "原料配方", "风味品鉴", "综合评价"]


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def clean(raw: str) -> str:
    return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", raw))).strip()


def plain(page: str) -> list[str]:
    """Split a page into visible lines, dropping scripts and styles."""
    body = re.sub(r"<script.*?</script>", "", page, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", "|", body))
    return [s.strip() for s in re.sub(r"\|{2,}", "|", text).split("|") if s.strip()]


def title_map(page: str) -> dict[str, str]:
    """Map every detail URL on a listing page to its anchor text."""
    out: dict[str, str] = {}
    for m in ANCHOR_RE.finditer(page):
        # Some links carry a zero-width space; stripping it keeps the request
        # from failing on a path that is otherwise perfectly valid.
        href = re.sub(r"[\u200b-\u200f\ufeff]", "", m.group("href"))
        text = clean(m.group("text"))
        if DETAIL_HREF_RE.fullmatch(href) and text:
            out.setdefault(href, text)
    return out


def build(args: argparse.Namespace) -> int:
    found: dict[str, tuple[str, str, str, str]] = {}  # url -> (title, section, group, subseries)
    seen_pages: set[str] = set()
    queue: list[str] = []

    for slug in SECTIONS:
        queue.append(f"/baike1/{slug}/")

    errors = 0
    while queue:
        path = queue.pop(0)
        if path in seen_pages:
            continue
        seen_pages.add(path)
        url = SITE + path
        try:
            page = get(url)
        except Exception as exc:
            print(f"  skip {path}: {exc}", file=sys.stderr)
            errors += 1
            continue

        titles = title_map(page)

        # This site publishes no usable category links, so sub-series directories
        # are found by walking up from the detail pages already in hand. That
        # reaches entries the landing page never links.
        for href in titles:
            parts = href.strip("/").split("/")
            for depth in range(len(parts) - 1, 2, -1):
                candidate = "/" + "/".join(parts[:depth]) + "/"
                if candidate not in seen_pages:
                    queue.append(candidate)

        for href, text in titles.items():
            if href in found:
                continue
            rel = href[len("/baike1/") :].strip("/")
            bits = rel.split("/")
            section = SECTIONS.get(bits[0], "?")
            group = bits[1] if len(bits) > 1 else "-"
            subseries = bits[2] if len(bits) > 2 else "-"
            found[href] = (text, section, group, subseries)

        time.sleep(DELAY)

    if not found:
        print("No detail pages discovered - network problem?", file=sys.stderr)
        return 2

    INDEX.parent.mkdir(parents=True, exist_ok=True)
    rows = sorted(found.items())
    with INDEX.open("w", encoding="utf-8") as fh:
        fh.write("url\ttitle\tsection\tgroup\tsubseries\n")
        for href, (title, section, group, subseries) in rows:
            fh.write(f"{href}\t{title}\t{section}\t{group}\t{subseries}\n")

    counts: dict[str, int] = {}
    for _, (_, section, _, _) in rows:
        counts[section] = counts.get(section, 0) + 1
    print(f"Indexed {len(rows)} pages across {len(seen_pages)} listing pages -> {INDEX}")
    for k, v in sorted(counts.items()):
        print(f"  {k}: {v}")
    if errors:
        print(f"  ({errors} listing pages failed - rerun to fill the gaps)", file=sys.stderr)
    return 0


def load_index() -> list[dict[str, str]]:
    if not INDEX.exists():
        print(
            f"Missing {INDEX}. Build it with:\n  python3 scripts/fetch_domestic.py --build-index",
            file=sys.stderr,
        )
        raise SystemExit(1)
    rows = []
    with INDEX.open(encoding="utf-8") as fh:
        header = next(fh).rstrip("\n").split("\t")
        for line in fh:
            if line.strip():
                rows.append(dict(zip(header, line.rstrip("\n").split("\t"))))
    return rows


def find(args: argparse.Namespace) -> int:
    rows = load_index()
    terms = [t.lower() for t in args.find.split() if t]
    hits = []
    for r in rows:
        blob = f"{r['title']} {r['group']} {r['subseries']} {r['url']}".lower()
        if all(t in blob for t in terms):
            hits.append(r)
    payload = {
        "status": "ok",
        "query": args.find,
        "count": len(hits),
        "results": [
            {
                "title": r["title"],
                "section": r["section"],
                "brand_slug": r["group"],
                "series_slug": r["subseries"],
                "url": SITE + r["url"],
            }
            for r in hits[: args.limit]
        ],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


SIZE_RE = re.compile(r"长度\s*(\d+)\s*mm", re.I)
RING_RE = re.compile(r"环径\s*(\d+)", re.I)


def parse_detail(page: str) -> dict:
    lines = plain(page)
    title = ""
    # Title appears after the breadcrumb, as "<cn>｜<en>" or just Chinese.
    for i, line in enumerate(lines):
        if line.startswith("更多+") or line == "加载中...":
            break
        if "｜" in line and not line.startswith(("品牌", "系列", "工艺", "尺寸")):
            title = line
            break
    if not title and len(lines) > 2:
        title = lines[2]

    fields: dict[str, str] = {}
    for line in lines:
        m = re.match(r"^(?P<key>[品牌系列工艺尺寸浓度包装产地]{2,4})[：:]\s*(?P<val>.+)$", line)
        if m:
            key, val = m.group("key"), m.group("val").strip()
            fields.setdefault(key, val)

    # Free-text blocks follow their heading.
    blocks: dict[str, str] = {}
    for head in SECTION_HEADS:
        try:
            i = lines.index(head)
        except ValueError:
            continue
        collected = []
        for line in lines[i + 1 :]:
            if line in SECTION_HEADS or line.startswith("更多") or line == "加载中...":
                break
            if re.match(r"^[品牌系列工艺尺寸浓度包装产地]{2,4}[：:]", line):
                continue
            collected.append(line)
        if collected:
            blocks[head] = " ".join(collected)

    spec = dict(fields)
    size_line = fields.get("尺寸", "")
    derived: dict[str, str] = {}
    if m := SIZE_RE.search(size_line):
        derived["Length_mm"] = m.group(1)
    if m := RING_RE.search(size_line):
        derived["Ring_Gauge"] = m.group(1)

    vitola = ""
    for part in re.split(r"[，,]", size_line):
        if re.search(r"[A-Za-z]{4,}", part):
            vitola = part.strip()
            break
    if vitola:
        derived["Vitola_raw"] = vitola

    return {
        "title": title,
        "url": None,
        "spec": spec,
        "derived": derived,
        "blocks": blocks,
    }


def detail(args: argparse.Namespace) -> int:
    slug = args.detail.strip()
    url = slug if slug.startswith("http") else SITE + slug
    if "/baike1/" not in url or not url.endswith(".html"):
        print(f"Not a 雪茄数据库 detail URL: {url}", file=sys.stderr)
        return 1
    try:
        page = get(url)
    except Exception as exc:
        print(f"Fetch failed: {exc}", file=sys.stderr)
        return 2
    out = parse_detail(page)
    out["url"] = url
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


def check(args: argparse.Namespace) -> int:
    missing = []
    if INDEX.exists():
        rows = load_index()
        from collections import Counter

        c = Counter(r["section"] for r in rows)
        print(f"index ok: {len(rows)} entries ({', '.join(f'{k} {v}' for k, v in sorted(c.items()))})")
    else:
        missing.append(str(INDEX))
        print(f"index missing: {INDEX}", file=sys.stderr)
    try:
        get(SITE + "/baike1/guochan/")
        print("network ok: 雪茄123 reachable")
    except Exception as exc:
        print(f"network FAIL: {exc}", file=sys.stderr)
        return 2
    return 0 if not missing else 1


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--build-index", action="store_true", help="walk the tree and write data/xuejia-index.tsv")
    g.add_argument("--find", metavar="KEYWORDS", help="search the local index")
    g.add_argument("--detail", metavar="URL", help="fetch and parse one detail page")
    g.add_argument("--check", action="store_true", help="verify index and network")
    ap.add_argument("--limit", type=int, default=30, help="max results for --find (default 30)")
    args = ap.parse_args()

    if args.build_index:
        return build(args)
    if args.find:
        return find(args)
    if args.detail:
        return detail(args)
    return check(args)


if __name__ == "__main__":
    sys.exit(main())
