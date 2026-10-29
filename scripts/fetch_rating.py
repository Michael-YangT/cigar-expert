#!/usr/bin/env python3
"""Read one Cigar Aficionado rating page and return its verdict.

This is deliberately a single-page tool. It does not crawl, does not walk any
sitemap, and does not use the site's search - their robots.txt disallows both
/search and /ratings/search*. Finding which page to read is the caller's job,
normally a web search such as:

    site:cigaraficionado.com/ratings <brand> <model>

which is allowed and takes one request rather than thousands.

The 100-point score is the industry's most cited number, and unlike
community ratings it comes from blind panel tastings. Use it to corroborate,
never as the only evidence.

**Price is quoted verbatim or not at all.** `price_reference` carries the figure
the source site published, with no range derived from it, no currency conversion
and no seller attached. This skill gives no retail or purchasing guidance, so a
number that arrives without a source site behind it is not a price, it is a guess.
If you need a merchant, this is the wrong tool.

Because there is no index to query, the two steps are separated so neither can be
skipped: `--find` prints the search and the follow-up command, `--url` reads the
page that search turned up. `--find` performs no network request of its own — its
`status` field says `needs_web_search` precisely so the caller cannot mistake a
printed query for a performed search.

Usage:
    python3 scripts/fetch_rating.py --find "Tatuaje Cabinet Tainos"
    python3 scripts/fetch_rating.py --url https://www.cigaraficionado.com/ratings/27174/name/tatuaje-cabinet-tainos-double-corona
    python3 scripts/fetch_rating.py --check

Exit codes: 0 ok, 1 usage or not a ratings page, 2 network failure.
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
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"

# A cached rating page older than this is served as-is but flagged so the caller
# does not treat a possibly outdated score as current.
STALE_DAYS = 7

# The exact field order used by the rating template. Each label is followed by
# its value on the next non-empty line.
KEY_ORDER = ["SCORE", "LENGTH", "GAUGE", "STRENGTH"]
DETAIL_KEYS = [
    "Size",
    "Filler",
    "Binder",
    "Wrapper",
    "Country",
    "Issue",
]
# Reported separately from `details`, verbatim, as the site's published figure.
# Never converted, never banded into a range, and never paired with a seller.
PRICE_KEYS = ("Price",)

CACHE_DIR = ROOT / "data" / "ratings"

# The only URL shape the parser below understands. Anything else from a search
# result (a tag page, a brand page, an issue index) is rejected by main() before
# a request is made, so a near-miss costs nothing.
URL_PATTERN = r"https://www\.cigaraficionado\.com/ratings/\d+/name/[a-z0-9-]+"
URL_SHAPE = "https://www.cigaraficionado.com/ratings/<id>/name/<slug>"


def build_search(term: str) -> dict:
    """Emit the search to run and the command that consumes its result."""
    cleaned = re.sub(r"\s+", " ", term).strip()
    return {
        # Not "ok" and not a result: this function searched nothing.
        "status": "needs_web_search",
        "search_query": f"site:cigaraficionado.com/ratings {cleaned}",
        "accept_url_shape": URL_SHAPE,
        "then_run": 'python3 scripts/fetch_rating.py --url "<url from the search>"',
        "rules": [
            "Run the search with the web-search tool, not with this script.",
            "Read at most the one page that matches; never crawl the site.",
            "No matching URL means no published rating - say so, do not substitute a similar cigar.",
        ],
    }


def get(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


def lines_of(page: str) -> list[str]:
    body = re.sub(r"<script.*?</script>", "", page, flags=re.S)
    body = re.sub(r"<style.*?</style>", "", body, flags=re.S)
    text = html.unescape(re.sub(r"<[^>]+>", "|", body))
    text = re.sub(r"\|{2,}", "|", text)
    return [s.strip() for s in text.split("|") if s.strip()]


def squash(raw: str) -> str:
    """Collapse the stray newlines the template leaves inside values."""
    return re.sub(r"\s+", " ", raw).strip()


def parse(page: str) -> dict:
    lines = [squash(s) for s in lines_of(page)]

    def value_after(label: str) -> str:
        for i, line in enumerate(lines):
            if line == label:
                j = i + 1
                while j < len(lines) and lines[j] in ("points", ""):
                    j += 1
                return lines[j] if j < len(lines) else ""
        return ""

    header: dict[str, str] = {}
    for key in KEY_ORDER:
        if v := value_after(key):
            header[key] = v

    # "Details" block - label, then value on the following line.
    details: dict[str, str] = {}
    for key in DETAIL_KEYS:
        label = key + ":"
        for i, line in enumerate(lines):
            if line == label:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    details[key] = lines[j]
                break

    price: dict[str, str] = {}
    for key in PRICE_KEYS:
        label = key + ":"
        for i, line in enumerate(lines):
            if line == label:
                j = i + 1
                while j < len(lines) and not lines[j].strip():
                    j += 1
                if j < len(lines):
                    price[key] = lines[j]
                break

    tasting = ""
    m_idx = None
    for i, line in enumerate(lines):
        if line == "Tasting Note":
            m_idx = i + 1
            break
    if m_idx:
        note = []
        for line in lines[m_idx:]:
            if line in ("Details", "More Reviews of this Cigar") or line.endswith(":"):
                break
            note.append(line)
        tasting = " ".join(note).strip()

    # Repeat reviews appear as "<score> points" followed by an issue/date line.
    # Pair them so each past verdict stays attached to when it was given.
    repeats = []
    i = lines.index("More Reviews of this Cigar") if "More Reviews of this Cigar" in lines else -1
    if i > 0:
        pending = None
        for line in lines[i + 1 : i + 14]:
            if re.fullmatch(r"\d{2,3}", line):
                pending = line
            elif line.lower() in ("points", "point"):
                continue
            elif pending is not None:
                repeats.append({"score": pending, "issue": line.replace("Cigar Aficionado", "").strip(" :–- ")})
                pending = None

    # The primary review's own issue tracker is not rendered there; if the
    # Details block has it, use it for consistency with the repeats above.
    issue = details.get("Issue", "").replace("Cigar Aficionado", "").strip(" :–- ")

    title = lines[0] if lines else ""

    return {
        "title": title,
        "score": header.get("SCORE"),
        "length": header.get("LENGTH"),
        "ring_gauge": header.get("GAUGE"),
        "strength": header.get("STRENGTH"),
        "reviewed_issue": issue,
        "details": details,
        "price_reference": price or None,
        "tasting_note": tasting,
        "other_reviews": repeats,
        "notes": (
            "price_reference is the figure the source site published, quoted verbatim. "
            "It is not a price band, not a currency conversion, and not a place to buy - "
            "quote it as a published reference with the retrieval date, never as guidance."
        ),
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--url", help="one Cigar Aficionado rating page")
    g.add_argument("--find", metavar="BRAND MODEL", help="print the search that leads to a rating page")
    g.add_argument("--check", action="store_true", help="verify reachability")
    ap.add_argument("--no-cache", action="store_true", help="skip the local page cache")
    args = ap.parse_args()

    if args.find is not None:
        if not re.search(r"[a-z0-9]", args.find, re.I):
            print("--find needs a brand or model term.", file=sys.stderr)
            return 1
        print(json.dumps(build_search(args.find), ensure_ascii=False, indent=2))
        return 0

    if args.check:
        url = "https://www.cigaraficionado.com/ratings"
        try:
            get(url)
        except Exception as exc:
            print(f"unreachable: {exc}", file=sys.stderr)
            return 2
        print("Cigar Aficionado reachable. Remember: no crawling, no /search.")
        return 0

    url = args.url.strip().split("#")[0].split("?")[0]
    if not re.fullmatch(URL_PATTERN + r"/?", url):
        # Rejecting here is deliberate: an index or brand page parses into empty
        # fields, which reads like "this cigar has no score" rather than "wrong
        # page". One clear failure beats a plausible-looking blank.
        print("Not a single rating page. Expected " + URL_SHAPE, file=sys.stderr)
        return 1

    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    key = re.sub(r"[^a-zA-Z0-9]+", "_", url.split("/ratings/")[-1])[:80] + ".html"
    cached = CACHE_DIR / key

    if cached.exists() and not args.no_cache:
        page = cached.read_text(encoding="utf-8", errors="replace")
        source = "cache"
    else:
        try:
            page = get(url)
        except Exception as exc:
            print(f"Fetch failed: {exc}", file=sys.stderr)
            return 2
        cached.write_text(page, encoding="utf-8")
        source = "network"

    out = parse(page)
    out["url"] = url
    out["source"] = source
    if source == "cache":
        age_days = (time.time() - cached.stat().st_mtime) / 86400.0
        out["cached_days"] = round(age_days, 1)
        if age_days > STALE_DAYS:
            out["stale"] = True
            out["stale_note"] = (
                f"cached rating page is {age_days:.0f} days old; rerun with --no-cache "
                "to refresh, or treat this score as possibly outdated."
            )
        else:
            out["stale"] = False
    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
