#!/usr/bin/env python3
"""Report whether this skill can answer, and what is missing if it cannot.

Read-only by default. It touches the network only when asked, because the two
things that actually break a fresh install are local: no Python, or no index.

Three states:

    ready        indexes and offline references all present
    partial      offline references fine, catalogue index not built yet
    needs_setup  Python too old, or scripts/ or references/ incomplete

`partial` is the normal state on a fresh clone and is not an error: storage,
terminology and flavour-group answers come from cached references and keep
working; only catalogue lookup needs the index. Reporting a missing index as
"this cigar does not exist" is the failure this script exists to prevent.

Usage:
    python3 scripts/check_environment.py
    python3 scripts/check_environment.py --online     # also probe the five sites

Exit codes: 0 ready or partial, 1 needs_setup.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
MIN_PYTHON = (3, 8)
INDEX_STALE_DAYS = 30

SCRIPTS = [
    "build_index.py",
    "lookup.py",
    "fetch_domestic.py",
    "fetch_rating.py",
    "fetch_news.py",
    "fetch_capitol.py",
]
REFERENCES = [
    "capitol-index.md",
    "storage-terms.md",
    "terroir.md",
    "leaf-varieties.md",
    "production-curing.md",
    "anatomy.md",
    "flavour-tasting.md",
    "matching-rules.md",
    "data-sources.md",
    "flavour-groups.md",
    "setup-guide.md",
]
INDEXES = [
    (DATA / "brands.txt", "non-Chinese brand index"),
    (DATA / "cigars.txt", "non-Chinese model index"),
    (DATA / "xuejia-index.tsv", "Chinese-facing index"),
]
SITES = [
    "https://www.cigarcentury.com/",
    "https://cigarcapitol.com/",
    "https://www.cigaraficionado.com/ratings",
    "https://www.xuejia123.com/",
    "https://halfwheel.com/",
]
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0 Safari/537.36"


def count_lines(path: Path) -> int:
    with path.open(encoding="utf-8", errors="replace") as fh:
        return sum(1 for line in fh if line.strip())


def probe(url: str) -> tuple[bool, str]:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": UA}, method="HEAD")
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.status < 500, f"HTTP {resp.status}"
    except Exception as exc:  # one dead site must not stop the report
        return False, str(exc)[:120]


def build_report(online: bool, stale_check: bool = True) -> dict:
    checks = []
    blocking = False
    stale: list[str] = []

    ok = sys.version_info >= MIN_PYTHON
    checks.append(
        {
            "id": "python",
            "ok": ok,
            "required": True,
            "detail": f"{sys.version.split()[0]} (need >= {MIN_PYTHON[0]}.{MIN_PYTHON[1]})",
        }
    )
    blocking = blocking or not ok

    missing_scripts = [s for s in SCRIPTS if not (ROOT / "scripts" / s).is_file()]
    checks.append(
        {
            "id": "scripts",
            "ok": not missing_scripts,
            "required": True,
            "detail": "all present" if not missing_scripts else "missing " + ", ".join(missing_scripts),
        }
    )
    blocking = blocking or bool(missing_scripts)

    missing_refs = [r for r in REFERENCES if not (ROOT / "references" / r).is_file()]
    checks.append(
        {
            "id": "references",
            "ok": not missing_refs,
            "required": True,
            "detail": "all present" if not missing_refs else "missing " + ", ".join(missing_refs),
        }
    )
    blocking = blocking or bool(missing_refs)

    absent = []
    for path, label in INDEXES:
        if path.is_file():
            detail = f"{count_lines(path)} entries - {label}"
            check = {"id": path.name, "ok": True, "required": False, "detail": detail}
            if stale_check:
                age_days = (time.time() - path.stat().st_mtime) / 86400.0
                if age_days > INDEX_STALE_DAYS:
                    check["ok"] = False
                    check["detail"] = (
                        f"built {age_days:.0f} days ago - rebuild recommended - {label}"
                    )
                    stale.append(path.name)
            checks.append(check)
        else:
            absent.append(path.name)
            checks.append({"id": path.name, "ok": False, "required": False, "detail": f"not built - {label}"})

    # Probed with access(), not by writing a file: a read-only check has no
    # business creating or deleting anything, and a stray probe file in data/
    # would be indistinguishable from real cache content.
    target = DATA if DATA.is_dir() else ROOT
    writable = os.access(target, os.W_OK)
    checks.append(
        {
            "id": "data-writable",
            "ok": writable,
            "required": True,
            "detail": f"{target} writable={writable}" + ("" if DATA.is_dir() else ", data/ not created yet"),
        }
    )
    blocking = blocking or not writable

    if online:
        for url in SITES:
            reachable, detail = probe(url)
            checks.append({"id": url, "ok": reachable, "required": False, "detail": detail})

    missing_lookup = "brands.txt" in absent or "cigars.txt" in absent
    missing_domestic = "xuejia-index.tsv" in absent
    unavailable = []
    if missing_lookup:
        unavailable.append("catalogue lookup by brand and model")
    if missing_domestic:
        unavailable.append("Chinese domestic lookup")
    if stale:
        unavailable.append("catalogue index possibly stale")

    if blocking:
        status = "needs_setup"
        nxt = "Read references/setup-guide.md and fix the failed check above."
    elif absent or stale:
        status = "partial"
        if missing_lookup or any(s in ("brands.txt", "cigars.txt") for s in stale):
            nxt = "python3 scripts/build_index.py"
        elif missing_domestic or "xuejia-index.tsv" in stale:
            nxt = "python3 scripts/fetch_domestic.py --build-index"
        else:
            nxt = "python3 scripts/build_index.py"
    else:
        status = "ready"
        nxt = "Answer normally."

    return {
        "status": status,
        "skill": "cigar-expert",
        "root": str(ROOT),
        "online_checked": online,
        "working_offline": ["storage science", "terminology", "flavour-group assignment"],
        "unavailable_now": unavailable,
        "next": nxt,
        "checks": checks,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--online", action="store_true", help="also probe the reference sites (network access)")
    ap.add_argument(
        "--no-stale-check",
        action="store_true",
        help="skip index freshness check (treat old indexes as ready)",
    )
    args = ap.parse_args()

    report = build_report(args.online, stale_check=not args.no_stale_check)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["status"] == "needs_setup" else 0


if __name__ == "__main__":
    sys.exit(main())
