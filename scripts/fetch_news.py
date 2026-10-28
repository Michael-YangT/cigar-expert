#!/usr/bin/env python3
"""Read halfwheel - release news and industry reporting.

halfwheel is where new products surface first, usually weeks or months before
they reach any reference database. That makes it the answer to "have you heard
of X?" - the question every catalogue lookup fails on.

**This site sits behind a Cloudflare managed challenge**, which plain HTTP
clients cannot pass. Two consequences:

  1. When the challenge fires, this script reports `status: blocked` and prints
     the URL patterns to use with the built-in web-fetch tool instead, which
     runs outside this constraint. That is the normal path - do not treat it as
     an error, and do not "fix" it by hammering the site.
  2. Never attempt the site search from a script. Use the date archive instead,
     which is cheap and stable.

When the site is reachable from wherever this happens to run, the same code
extracts the listing into JSON.

URL patterns worth knowing:
    https://halfwheel.com/                       latest posts
    https://halfwheel.com/date/2026/10/27/       everything published that day
    https://halfwheel.com/<post-slug>/<post-id>/ one article
    https://halfwheel.com/?s=<term>              site search (browser only)

Usage:
    python3 scripts/fetch_news.py
    python3 scripts/fetch_news.py --date 2026/10/27
    python3 scripts/fetch_news.py --limit 10

Exit codes: 0 ok (including a clean `blocked` report), 1 usage problem.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import urllib.error
import urllib.request

SITE = "https://halfwheel.com"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"

ARTICLE_RE = re.compile(r"<article\b.*?</article>", re.S | re.I)
TITLE_RE = re.compile(r'<h2[^>]*class="[^"]*entry-title[^"]*"[^>]*>\s*<a[^>]*href="(?P<href>[^"]+)"[^>]*>(?P<t>.*?)</a>', re.S | re.I)
DATE_RE = re.compile(r'href="https://halfwheel\.com/date/(?P<y>\d{4})/(?P<m>\d{2})/(?P<d>\d{2})/')
AUTHOR_RE = re.compile(r'href="https://halfwheel\.com/author/[^"]*"[^>]*>\s*(?P<a>[^<]+?)\s*<', re.I)
EXCERPT_RE = re.compile(r'<p>(?P<p>.*?)</p>', re.S | re.I)


def squash(s: str) -> str:
    return re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", "", s))).strip()


def fetch(url: str) -> tuple[int, str]:
    """Return (status, body). A 403 body means Cloudflare, not authorization."""
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.status, r.read().decode("utf-8", "replace")
    except urllib.error.HTTPError as exc:
        return exc.code, exc.read().decode("utf-8", "replace")


def is_challenge(status: int, body: str) -> bool:
    return status == 403 or "Just a moment" in body[:4000] or "cf_chl_opt" in body[:20000]


def extract(body: str, limit: int) -> list[dict]:
    """Best-effort WordPress listing parse. Halfwheel uses a standard theme."""
    posts: list[dict] = []
    blocks = ARTICLE_RE.findall(body) or [body]
    seen: set[str] = set()
    for block in blocks:
        for m in TITLE_RE.finditer(block):
            href = m.group("href")
            if href in seen:
                continue
            seen.add(href)
            date = ""
            if d := DATE_RE.search(block):
                date = f"{d.group('y')}-{d.group('m')}-{d.group('d')}"
            author = (AUTHOR_RE.search(block).group("a").strip() if AUTHOR_RE.search(block) else "")
            excerpt = ""
            for p in EXCERPT_RE.finditer(block):
                text = squash(p.group("p"))
                if len(text) > 40 and not text.startswith(("by ", "Read More")):
                    excerpt = text
                    break
            posts.append({"title": squash(m.group("t")), "date": date, "author": author, "url": href, "excerpt": excerpt})
            if len(posts) >= limit:
                return posts
    return posts


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--date", help="archive day as YYYY/MM/DD")
    ap.add_argument("--limit", type=int, default=12, help="max posts (default 12)")
    args = ap.parse_args()

    if args.date:
        if not re.fullmatch(r"\d{4}/\d{2}/\d{2}", args.date):
            print("--date must look like 2026/10/27", file=sys.stderr)
            return 1
        url = f"{SITE}/date/{args.date}/"
    else:
        url = SITE + "/"

    status, body = fetch(url)

    if is_challenge(status, body):
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "http_status": status,
                    "site": "halfwheel",
                    "reason": "Cloudflare managed challenge - no script can pass it, and retrying will not help.",
                    "do_not": ["Retry in a loop.", "Use /?s= from a script.", "Treat this as a failure to fix."],
                    "instead": {
                        "tool": "Use the built-in web-fetch tool, which reaches the page fine.",
                        "urls": {
                            "latest": f"{SITE}/",
                            "archive_by_day": f"{SITE}/date/2026/10/27/",
                            "search_in_browser": f"{SITE}/?s=<brand+model>",
                        },
                        "guidance": "Browse the archive by day rather than searching; halfwheel posts carry a stable /date/ path.",
                    },
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    posts = extract(body, args.limit)
    print(json.dumps({"status": "ok", "source": url, "count": len(posts), "posts": posts}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
