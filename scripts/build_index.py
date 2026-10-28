#!/usr/bin/env python3
"""Build local search indexes for the cigar skill.

Downloads the Cigar Century sitemap and extracts two plain-text indexes:

    data/brands.txt   one brand slug per line        (~4,700 entries)
    data/cigars.txt   one cigar product slug per line (~19,000 entries)

These indexes let the skill resolve a cigar to its exact product URL without
relying on a site search endpoint (Cigar Century has none). robots.txt for
www.cigarcentury.com declares `Allow: /` and points at this sitemap, so this
fetch is permitted.

Usage:
    python3 scripts/build_index.py                # build into ../data
    python3 scripts/build_index.py --force        # ignore existing sitemap cache
    python3 scripts/build_index.py --outdir DIR   # choose output directory

Exit codes: 0 ok, 1 network or parse failure.
"""

from __future__ import annotations

import argparse
import re
import sys
import urllib.request
from pathlib import Path

SITEMAP_INDEX = "https://www.cigarcentury.com/sitemap.xml"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
TIMEOUT = 60

# Only the English side of the catalogue is indexed; the Spanish mirror duplicates it.
BRAND_RE = re.compile(r"<loc>([^<]*/en/brand/[^<]*)</loc>")
CIGAR_RE = re.compile(r"<loc>([^<]*/en/cigars/[^<]*)</loc>")
SITEMAP_RE = re.compile(r"<loc>([^<]*\.xml)</loc>")


def fetch(url: str) -> str:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def last_part(url: str) -> str:
    return url.rstrip("/").rsplit("/", 1)[-1]


def collect_urls(xml: str, pattern: re.Pattern[str]) -> list[str]:
    seen: dict[str, None] = {}
    for match in pattern.finditer(xml):
        seen[last_part(match.group(1))] = None
    return sorted(seen)


def build(outdir: Path, cache: Path, force: bool) -> tuple[int, int]:
    if force or not cache.exists():
        print(f"fetching sitemap index ...", file=sys.stderr)
        index_xml = fetch(SITEMAP_INDEX)
        cache.write_text(index_xml, encoding="utf-8")
    else:
        print(f"using cached sitemap index at {cache}", file=sys.stderr)
        index_xml = cache.read_text(encoding="utf-8")

    children = SITEMAP_RE.findall(index_xml)
    if not children:
        raise SystemExit("error: no child sitemaps found in the sitemap index")

    brands: list[str] = []
    cigars: list[str] = []
    for child in children:
        print(f"fetching {child} ...", file=sys.stderr)
        xml = fetch(child)
        brands.extend(collect_urls(xml, BRAND_RE))
        cigars.extend(collect_urls(xml, CIGAR_RE))

    # De-duplicate preserving determinism.
    brands = sorted(set(brands))
    cigars = sorted(set(cigars))
    if not cigars:
        raise SystemExit("error: no cigar product URLs found - site layout may have changed")

    outdir.mkdir(parents=True, exist_ok=True)
    (outdir / "brands.txt").write_text("\n".join(brands) + "\n", encoding="utf-8")
    (outdir / "cigars.txt").write_text("\n".join(cigars) + "\n", encoding="utf-8")
    return len(brands), len(cigars)


def main() -> int:
    here = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--outdir", type=Path, default=here.parent / "data", help="where to write the indexes")
    parser.add_argument("--cache", type=Path, default=here.parent / "data" / "sitemap.xml", help="cached sitemap index")
    parser.add_argument("--force", action="store_true", help="refetch even when a cached sitemap exists")
    args = parser.parse_args()

    try:
        n_brands, n_cigars = build(args.outdir, args.cache, args.force)
    except urllib.error.URLError as exc:  # network problems are the common failure
        print(f"error: could not reach cigarcentury.com ({exc})", file=sys.stderr)
        return 1
    except OSError as exc:
        print(f"error: could not write indexes ({exc})", file=sys.stderr)
        return 1

    print(f"built {args.outdir}/brands.txt ({n_brands} brands)")
    print(f"built {args.outdir}/cigars.txt ({n_cigars} cigars)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
