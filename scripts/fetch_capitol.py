#!/usr/bin/env python3
"""Refresh the offline Cigar Capitol extracts in references/.

Cigar Capitol publishes records at https://cigarcapitol.com/dictionary/<slug>/
each one carrying Definition / Why it matters / In context / Related terms.
Those three blocks are what makes the source worth caching: the "context"
sentence is the everyday phrasing, which is what a bilingual answer needs.

This writes two files:

    references/storage-terms.md   the Storage & Aging set
    references/terroir.md         the growing regions referenced most often

Re-run it when Cigar Capitol updates. If the network is unavailable the existing
files are left untouched, so this script is safe to run anywhere.

Usage:
    python3 scripts/fetch_capitol.py
    python3 scripts/fetch_capitol.py --outdir references
"""

from __future__ import annotations

import argparse
import html
import re
import sys
import urllib.request
from pathlib import Path

ROOT = "https://cigarcapitol.com/dictionary/{}/"
USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"
TIMEOUT = 30

STORAGE = [
    "acclimation", "boveda-packs", "cabinet-humidor", "cigar-beetle", "coolerdor",
    "desktop-humidor", "distilled-water", "dry-boxing", "freezing-protocol",
    "humidification-beads", "humidor", "hygrometer", "over-humidification",
    "relative-humidity", "salt-test-calibration", "seasoning-a-humidor",
    "spanish-cedar", "tupperdor", "wineador",
]

TERROIR = [
    "esteli", "jalapa", "vuelta-abajo", "connecticut-river-valley",
    "connecticut-broadleaf", "san-andres-veracruz", "cibao-valley", "condega",
    "jamastran", "oriente", "partido", "remedios", "semi-vuelta", "los-rios-quevedo",
]

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


def fetch(slug: str) -> str:
    req = urllib.request.Request(ROOT.format(slug), headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(req, timeout=TIMEOUT) as resp:
        return resp.read().decode("utf-8", errors="replace")


def clean(raw: str) -> str:
    raw = re.sub(r"<[^>]+>", " ", raw)
    text = html.unescape(re.sub(r"\s+", " ", raw)).strip()
    return html.unescape(text)


def extract(page: str) -> dict[str, str]:
    """Pull the named blocks out of one dictionary entry."""
    # Strip style/script first: inline CSS contains braces and quotes that
    # otherwise bleed into the extracted definitions.
    page = re.sub(r"<script.*?</script>", "", page, flags=re.S)
    page = re.sub(r"<style.*?</style>", "", page, flags=re.S)

    out: dict[str, str] = {}
    for m in FIELD_RE.finditer(page):
        label = clean(m.group("label"))
        body = m.group("body")
        if label in ("Related terms",):
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


def title_of(slug: str) -> str:
    return " ".join(w.capitalize() if w.islower() else w for w in slug.split("-"))


def render(slugs: list[str], heading: str, intro: str) -> tuple[str, int]:
    lines = [f"# {heading}", "", intro, ""]
    ok = 0
    for slug in slugs:
        try:
            page = fetch(slug)
        except urllib.error.URLError as exc:
            print(f"  skip {slug}: {exc}", file=sys.stderr)
            continue
        blocks = extract(page)
        if not blocks or "Definition" not in blocks:
            print(f"  skip {slug}: no content blocks found", file=sys.stderr)
            continue
        ok += 1
        name = blocks.get("_term", title_of(slug))
        pron = blocks.get("_pron", "")
        cat = blocks.get("_category", "")
        lines.append(f"## {name}")
        meta = " | ".join(x for x in (pron, cat) if x)
        if meta:
            lines.append(f"*{meta}*")
        lines.append(f"`<https://cigarcapitol.com/dictionary/{slug}/>`")
        for key in ("Definition", "Why it matters", "In context", "Related terms"):
            if blocks.get(key):
                lines.append(f"- **{key}**: {blocks[key]}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n", ok


def main() -> int:
    here = Path(__file__).resolve().parent
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--outdir", type=Path, default=here.parent / "references")
    args = ap.parse_args()
    args.outdir.mkdir(parents=True, exist_ok=True)

    storage_intro = (
        "Verbatim from Cigar Capitol (Storage & Aging category), extracted to keep this "
        "skill usable offline and to keep phrasing faithful to the source. Chinese renderings "
        "in answers must be paraphrases of these definitions, never a claim of translated canon."
    )
    terroir_intro = (
        "Verbatim from Cigar Capitol (Growing & Terroir). These are the primary source for "
        "which flavour group a wrapper belongs to - see references/flavour-groups.md."
    )

    total = 0
    for (fname, slugs, heading, intro) in (
        ("storage-terms.md", STORAGE, "Storage & Aging Terms", storage_intro),
        ("terroir.md", TERROIR, "Growing Regions & Leaf Behaviour", terroir_intro),
    ):
        print(f"fetching {len(slugs)} entries for {fname} ...", file=sys.stderr)
        text, ok = render(slugs, heading, intro)
        if ok == 0:
            print(f"error: nothing retrieved for {fname}; keeping existing file", file=sys.stderr)
            return 1
        (args.outdir / fname).write_text(text, encoding="utf-8")
        print(f"  wrote {args.outdir / fname} ({ok} entries)")
        total += ok
    return 0


if __name__ == "__main__":
    sys.exit(main())
