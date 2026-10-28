#!/usr/bin/env python3
"""Resolve a cigar to its Cigar Century record, the careful way.

Two jobs:

  1. find   map a (brand, model) pair onto candidate product slugs
  2. fetch  pull the full spec sheet for one resolved slug

Why this exists rather than a plain substring search - all three mistakes below
were reproduced against a real 666-cigar ledger during development:

  "Great Wall 雪之梦6"  -> "262-allegiance-corona"   a bare digit matched inside
                                                     another slug's number
  "Quintero Brevas"     -> "arturo-fuente-...-brevas-royal-i"
                                                     a shared word crossed brands
  "Macanudo Red Robusto"-> "...-red-toro"            dropping the vitola as a
                                                     "stop word" silently swapped
                                                     the size

So matching is three stages and every stage is mandatory:

  lock the brand -> match the product line -> verify the size

Nothing is written anywhere. This script only reads indexes and prints JSON.

Usage:
    python3 scripts/lookup.py --brand "Oliva" --model "Serie V Melanio Robusto"
    python3 scripts/lookup.py --brand "Cohiba" --model "Wide Short" --top 5
    python3 scripts/lookup.py --url https://www.cigarcentury.com/en/cigars/oliva-serie-v-melanio-robusto
    python3 scripts/lookup.py --check        # confirm the indexes are present

Exit codes: 0 ok, 1 usage/index problem, 2 network failure.
"""

from __future__ import annotations

import argparse
import html
import json
import re
import sys
import unicodedata
import urllib.request
from pathlib import Path

BASE = "https://www.cigarcentury.com/en/cigars/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
TIMEOUT = 45

# Words shared across dozens of brands. They carry no brand identity on their
# own, so they are never enough to lock a brand - see LOCK_MIN_ALPHA.
AMBIGUOUS = frozenset(
    """selection reserve reserva limited edition especial special classic reserve
    maduro natural connecticut habano corojo sumatra oscuro claro colorado rosado
    nicaragua dominican honduran cuban mexican american ecuadorian brazilian
    anniversary coleccion colección coleccion-habanos habanos-collection
    original selección seleccion signature series serie blend combination
    no-1 no-2 no-3 no-4 no-5 no-6"""

    .split()
)

# Size words are IDENTIFYING, not noise. Dropping them is what caused the
# Robusto -> Toro swap. They are matched strictly, on token boundaries.
SIZE_WORDS = frozenset(
    """robusto toro corona churchill lancero torpedo belicoso piramide perfecto
    figurado panetela petit double gran gordo presidente prominente demi-tasse
    rothschild cazadores hermoso mareva nub salomon diadema campana chisel
    corona-gorda robusto-extra double-corona double-robusto double-toro
    petit-corona petit-robusto short-robusto half-corona gran-corona toro-grande""".split()
)

NUMERIC_TOKEN = re.compile(r"^\d+$")

FIELD_RE = re.compile(
    r'<div class="nombre">\s*(?P<key>[^<]+?)\s*</div>\s*<div class="valor[^"]*">(?P<val>.*?)</div>',
    re.S,
)
STRENGTH_RE = re.compile(r'<div class="nombre">\s*Strength\s*</div>.*?title="(?P<val>[^"]*)"', re.S)
TITLE_RE = re.compile(r"<h1[^>]*>(?P<t>.*?)</h1>", re.S | re.I)


def slugify(text: str) -> str:
    """Lowercase, strip accents and CJK, keep [a-z0-9-] only."""
    text = unicodedata.normalize("NFKD", str(text))
    text = "".join(c for c in text if not unicodedata.combining(c))
    # Drop CJK outright - brand columns often read "奥利瓦 Oliva".
    text = "".join(c if ord(c) < 0x2E80 else " " for c in text)
    text = text.lower()
    for ch in ("ø", "Ø", "đ", "Đ", "æ", "Æ", "œ", "Œ"):
        text = text.replace(ch, {"ø": "o", "Ø": "o", "đ": "d", "Đ": "d", "æ": "ae", "Æ": "ae", "œ": "oe", "Œ": "oe"}[ch])
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")


def tokens(slug: str) -> list[str]:
    return [t for t in slug.split("-") if t]


def alpha_len(slug: str) -> int:
    return sum(1 for c in slug if c.isalpha())


def load_lines(path: Path) -> list[str]:
    if not path.exists():
        raise SystemExit(
            f"error: missing index {path}\nRun: python3 scripts/build_index.py"
        )
    return [l.strip() for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]


def lock_brand(raw_brand: str, brands: list[str]) -> list[str]:
    """Stage 1 - find plausible brand slugs for a (possibly bilingual) brand string."""
    s = slugify(raw_brand)
    if not s:
        return []

    exact = [b for b in brands if b == s]
    if exact:
        return exact

    # Longest slug fully contained at the start of the query, or vice versa.
    prefixes = [b for b in brands if s.startswith(b + "-") or s == b]
    prefixes += [b for b in brands if b.startswith(s + "-")]
    out = set(prefixes)

    # A pure number must never become the brand ("Undercrown 10" is not brand 10).
    # Nor may an ambiguous word alone decide the brand.
    out = {b for b in out if alpha_len(b) >= 3 and b not in AMBIGUOUS}

    # Prefer longer, more specific slugs.
    return sorted(out, key=lambda b: (-len(b), b))


def score_product(candidate_tail: str, model_toks: list[str]) -> tuple[int, list[str]]:
    """Stage 2/3 - score how much of the requested model is present.

    Returns (score, unmatched_tokens). Digits are compared as whole tokens so
    "6" can never hide inside "262".
    """
    ctoks = set(tokens(candidate_tail))
    score = 0
    missing = []
    for tok in model_toks:
        if tok in ctoks:
            score += 2 if tok in SIZE_WORDS else 1
        else:
            missing.append(tok)
    return score, missing


def find_candidates(brand_slug: str, model: str, cigars: list[str], top: int) -> list[dict]:
    owned = [c for c in cigars if c.startswith(brand_slug + "-")]
    if not owned:
        return []

    model_toks = [t for t in tokens(slugify(model)) if t]
    if not model_toks:
        return []

    scored = []
    for c in owned:
        tail = c[len(brand_slug) + 1 :]
        if not tail:
            continue
        score, missing = score_product(tail, model_toks)
        if score == 0:
            continue
        # Prefer the tightest fit: highest score, then fewest extra tokens.
        extra = len(tokens(tail)) - len(model_toks)
        scored.append((score, -abs(extra), -len(tail), c))

    scored.sort(reverse=True)
    seen = []
    for score, _, _, c in scored:
        tail = c[len(brand_slug) + 1 :]
        _, missing = score_product(tail, model_toks)
        seen.append(
            {
                "slug": c,
                "url": BASE + c,
                "score": score,
                "missing_tokens": missing,
                "size_confirmed": not any(t in SIZE_WORDS for t in missing),
            }
        )
        if len(seen) >= top:
            break
    return seen


def parse_detail(html_text: str) -> dict:
    """Pull the spec sheet out of a product page."""
    # Trim the sidebar filters and flavour dropdowns, they repeat every field name.
    try:
        start = html_text.index('<div class="nombre">')
    except ValueError:
        start = 0
    body = html_text[start:]

    spec: dict[str, str] = {}
    for m in FIELD_RE.finditer(body):
        key = html.unescape(m.group("key")).strip()
        raw = m.group("val")
        raw = re.sub(r"<[^>]+>", " ", raw)
        val = html.unescape(re.sub(r"\s+", " ", raw)).strip()
        if key and val and key not in spec:
            spec[key] = val

    sm = STRENGTH_RE.search(body)
    if sm:
        spec["Strength"] = html.unescape(sm.group("val")).strip()

    title = ""
    tm = TITLE_RE.search(html_text)
    if tm:
        title = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", tm.group("t")))).strip()

    # Drop form furniture that shares the dato/nombre markup.
    for junk in ("Price:", "Appearance:", "Burn:", "Draw:", "Taste:", "Value For Price:"):
        spec.pop(junk, None)

    # Trailing UI links leak into flavour / country lists.
    for key in list(spec):
        spec[key] = re.sub(r"\s*View all\s*$", "", spec[key]).strip()

    # Price is deliberately not surfaced. The accompanying skill guidance keeps
    # this tool away from purchasing advice, so monetary fields stay out of the
    # payload even when the page carries them.
    for priced in ("Average Price", "MSRP", "Price"):
        spec.pop(priced, None)

    return {"title": title, "spec": spec}


def fetch_detail(url: str) -> dict:
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return parse_detail(resp.read().decode("utf-8", errors="replace"))


def main() -> int:
    here = Path(__file__).resolve().parent
    default_data = here.parent / "data"

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--brand", help='brand as written in your ledger, e.g. "奥利瓦 Oliva"')
    ap.add_argument("--model", help='model line, e.g. "Serie V Melanio Robusto"')
    ap.add_argument("--top", type=int, default=3, help="max candidates to report (default 3)")
    ap.add_argument("--url", help="skip the search and fetch one known product URL")
    ap.add_argument("--datadir", type=Path, default=default_data, help="index directory")
    ap.add_argument("--check", action="store_true", help="verify the indexes are present and exit")
    args = ap.parse_args()

    if args.check:
        for name in ("brands.txt", "cigars.txt"):
            p = args.datadir / name
            ok = p.exists()
            n = len(load_lines(p)) if ok else 0
            print(f"{'ok  ' if ok else 'miss'} {p} ({n} entries)")
        return 0 if (args.datadir / "brands.txt").exists() else 1

    if args.url:
        try:
            detail = fetch_detail(args.url)
        except urllib.error.URLError as exc:
            print(f"error: fetch failed ({exc})", file=sys.stderr)
            return 2
        print(json.dumps(detail, ensure_ascii=False, indent=2))
        return 0

    if not (args.brand and args.model):
        print("error: --brand and --model are both required (or use --url)", file=sys.stderr)
        return 1

    brands = load_lines(args.datadir / "brands.txt")
    cigars = load_lines(args.datadir / "cigars.txt")

    brand_hits = lock_brand(args.brand, brands)
    if not brand_hits:
        print(
            json.dumps(
                {
                    "status": "no_brand_match",
                    "brand_query": args.brand,
                    "advice": "Brand could not be locked. Ask the user to spell the Latin brand name; do not guess a product.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    results = []
    for bslug in brand_hits[:2]:
        cands = find_candidates(bslug, args.model, cigars, args.top)
        if cands:
            results.append({"brand_slug": bslug, "candidates": cands})
            if cands[0]["size_confirmed"]:
                break

    if not results:
        print(
            json.dumps(
                {
                    "status": "no_product_match",
                    "brand_query": args.brand,
                    "brand_slugs_tried": brand_hits[:2],
                    "model_query": args.model,
                    "advice": "Catalogue has no confident entry. Report this as unconfirmed rather than substituting a similar product.",
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    payload = {
        "status": "ok",
        "brand_query": args.brand,
        "model_query": args.model,
        "results": results,
        "confidence": "high" if (results[0]["candidates"][0]["size_confirmed"] and results[0]["candidates"][0]["score"] >= 3) else "review",
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
