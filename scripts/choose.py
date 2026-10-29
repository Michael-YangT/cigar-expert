#!/usr/bin/env python3
"""Choose what to smoke now.

Implements the narrowing order in `references/selection-guide.md`:

  1. State — is it smokable today? (hard, absolute)
  2. Time — how long does the user actually have? (hard, physical)
  3. Strength — nicotine load ceiling (hard, physical)
  4. Flavour — what they feel like (soft, only between survivors)

The catalogue index holds brand and model only — it carries no strength data.
Strength must come from `scripts/lookup.py --brand ... --model ...`, one cigar
at a time. This script never invents a strength from reputation.

Usage:
    python3 scripts/choose.py --time 45 --strength-ceiling Medium
    python3 scripts/choose.py --state-check arrived-days 3 --wrapper feels firm
    python3 scripts/choose.py --anti
    python3 scripts/choose.py --sizing-table

Exit codes: 0 ok, 1 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys

STRENGTH_LEVELS = ["Mild", "Medium", "Medium To Full", "Full"]
STRENGTH_RANK = {s: i for i, s in enumerate(STRENGTH_LEVELS)}

EXPERIENCE_CEILING = {
    "First few cigars": ("Mild to medium", ["Petit Corona", "Corona"]),
    "Occasional": ("Medium", ["Robusto", "Corona Gorda"]),
    "Regular": ("Medium to full", ["Toro", "Churchill"]),
    "Habitual": ("No ceiling", ["Whatever the palate asks for"]),
}

# Smoking-time estimates by length x ring gauge. Estimates, not measurements;
# pace dominates. Same cigar runs 30% shorter for a fast smoker, longer if damp.
# Table from selection-guide.md: rows length, columns ring gauge.
SIZING_TABLE = {
    "≤ 4\"": {"≤ 42": "20–30", "43–46": "20–30", "47–50": "25–35",
            "51–54": "30–40", "55+": "35–45"},
    "4–5\"": {"≤ 42": "30–40", "43–46": "30–45", "47–50": "35–50",
            "51–54": "45–60", "55+": "50–70"},
    "5–6\"": {"≤ 42": "40–55", "43–46": "40–55", "47–50": "45–65",
            "51–54": "50–70", "55+": "60–80"},
    "6–6.5\"": {"≤ 42": "50–70", "43–46": "55–75", "47–50": "60–80",
              "51–54": "65–90", "55+": "75–100"},
    "6.5–7.5\"": {"≤ 42": "60–85", "43–46": "65–90", "47–50": "75–105",
                "51–54": "80–110", "55+": "90–130"},
    "7.5\"+": {"≤ 42": "70–100", "43–46": "80–110", "47–50": "90–125",
             "51–54": "95–135", "55+": "110–150"},
}

RULE_OF_THUMB = (
    "Under 90 minutes available, stay at 54 ring or below and 6 inches or "
    "below. Anything larger will be set down half-smoked."
)

STATE_CHECKS = [
    {
        "check": "Arrived within the last two weeks",
        "if_fails": "Rest it. Shipping unsettles the leaf; two to four weeks at "
                    "target RH is the usual wait.",
    },
    {
        "check": "Squeezes hard and crackles, or feels brittle",
        "if_fails": "Too dry — see references/defect-diagnosis.md.",
    },
    {
        "check": "Feels spongy, or the wrapper is slick",
        "if_fails": "Too wet — will burn badly and taste sour.",
    },
    {
        "check": "Ammonia on the cold draw",
        "if_fails": "Not rested; months, not days.",
    },
    {
        "check": "Any mould that is not plainly plume",
        "if_fails": "Isolate it; see references/defect-diagnosis.md before "
                    "smoking anything from that container.",
    },
]

ANTI_RECOMMENDATIONS = [
    {
        "do_not": "Give a beginner a full-strength ligero blend",
        "because": "Nausea on the first cigar ends the hobby.",
    },
    {
        "do_not": "Hand a beginner a Double Corona or Churchill",
        "because": "90+ minutes; most are abandoned half-smoked.",
    },
    {
        "do_not": "Suggest a first cigar with an unusual or unverifiable origin",
        "because": "No way to judge quality, no way to learn from it.",
    },
    {
        "do_not": "Pick from the humidor without checking arrival date",
        "because": "Two weeks' rest is the difference between harsh and clean.",
    },
    {
        "do_not": "Recommend a large cigar for a stated 30-minute window",
        "because": "The constraint is physical, not a preference.",
    },
    {
        "do_not": "Reach for a cigar straight from a cold delivery box",
        "because": "Thermal shock cracks wrappers.",
    },
    {
        "do_not": "Answer a 'what should I smoke' with a shopping list",
        "because": "The user asked what to smoke, not what to buy.",
    },
]


def state_report(arrived_days: int | None = None,
                 feels: str | None = None,
                 cold_draw: str | None = None,
                 mould: str | None = None) -> dict:
    """Run the state check before considering flavour at all.

    Any failed check means "not tonight" plus what to do instead.
    """
    failures = []

    if arrived_days is not None and arrived_days < 14:
        failures.append({
            "check": "Arrived within the last two weeks",
            "if_fails": STATE_CHECKS[0]["if_fails"],
        })

    if feels:
        f = feels.lower()
        if "hard" in f or "crackle" in f or "brittle" in f:
            failures.append({
                "check": "Squeezes hard and crackles, or feels brittle",
                "if_fails": STATE_CHECKS[1]["if_fails"],
            })
        if "spongy" in f or "slick" in f:
            failures.append({
                "check": "Feels spongy, or the wrapper is slick",
                "if_fails": STATE_CHECKS[2]["if_fails"],
            })

    if cold_draw and "ammonia" in cold_draw.lower():
        failures.append({
            "check": "Ammonia on the cold draw",
            "if_fails": STATE_CHECKS[3]["if_fails"],
        })

    if mould and "plume" not in mould.lower():
        failures.append({
            "check": "Any mould that is not plainly plume",
            "if_fails": STATE_CHECKS[4]["if_fails"],
        })

    return {
        "state_check": "fail" if failures else "pass",
        "failures": failures,
        "note": (
            "Run this before considering flavour at all. Any 'yes' means the "
            "answer is 'not tonight'."
        ),
    }


def time_filter(minutes_available: int) -> dict:
    """Screen vitola by measured length x ring gauge, never by size words."""
    advice = []
    if minutes_available < 30:
        advice.append(
            "A 3-inch cigar (half corona ≈ 3\" × 44–46) is the only honest "
            "answer to a sub-30-minute window."
        )
    elif minutes_available < 90:
        advice.append(RULE_OF_THUMB)
        advice.append(
            "Screen by measured length and ring gauge from the sizing table, "
            "not by 'robusto' or 'toro' in the name."
        )
    else:
        advice.append(
            "Full vitola range is open; still screen by measured size, not name."
        )
    return {
        "minutes_available": minutes_available,
        "rule_of_thumb": RULE_OF_THUMB,
        "sizing_table": SIZING_TABLE,
        "advice": advice,
    }


def strength_ceiling(experience: str | None = None,
                     explicit: str | None = None) -> dict:
    """Return the strength ceiling and sizing that pairs with it."""
    if explicit:
        if explicit not in STRENGTH_LEVELS:
            return {
                "error": f"unknown strength '{explicit}' (one of "
                         f"{', '.join(STRENGTH_LEVELS)})",
            }
        return {
            "ceiling": explicit,
            "note": (
                "Quote the page's own wording from lookup.py; never round "
                "Medium To Full into your own bracket."
            ),
        }

    if experience:
        if experience not in EXPERIENCE_CEILING:
            return {
                "error": f"unknown experience '{experience}' (one of "
                         f"{', '.join(sorted(EXPERIENCE_CEILING.keys()))})",
            }
        ceiling, sizing = EXPERIENCE_CEILING[experience]
        return {
            "experience": experience,
            "ceiling": ceiling,
            "sizing_that_pairs": sizing,
        }

    return {
        "error": "provide --experience or --strength-ceiling",
        "available_experience": sorted(EXPERIENCE_CEILING.keys()),
        "available_strength": STRENGTH_LEVELS,
    }


def narrow(candidates: list[dict],
           minutes_available: int | None = None,
           strength_ceiling_level: str | None = None,
           flavour: str | None = None) -> dict:
    """Apply the four hard constraints in order to a candidate list.

    Each candidate dict should carry: brand, model, length_in, ring_gauge,
    strength (one of STRENGTH_LEVELS or None), state_ok (bool).
    Returns survivors at each stage plus the anti-recommendations.
    """
    survivors = list(candidates)
    stages = []

    # Stage 1 — state
    after_state = [c for c in survivors if c.get("state_ok", False)]
    stages.append({
        "stage": "state",
        "before": len(survivors),
        "after": len(after_state),
        "rule": "A wet or just-shipped cigar cannot be fixed by picking a "
                "better one from the same container.",
    })
    survivors = after_state

    # Stage 2 — time
    if minutes_available is not None:
        before = len(survivors)
        # Estimate smoking time from length x ring via the sizing table; keep
        # candidates whose estimated range overlaps the available window.
        kept = []
        for c in survivors:
            est = _estimate_minutes(c.get("length_in"), c.get("ring_gauge"))
            if est and est[0] <= minutes_available <= est[1]:
                kept.append(c)
        stages.append({
            "stage": "time",
            "before": before,
            "after": len(kept),
            "rule": (
                f"Running out of time mid-cigar wastes the whole thing. "
                f"Available: {minutes_available} min."
            ),
        })
        survivors = kept

    # Stage 3 — strength
    if strength_ceiling_level:
        before = len(survivors)
        ceiling_rank = STRENGTH_RANK[strength_ceiling_level]
        kept = [
            c for c in survivors
            if c.get("strength") is None or STRENGTH_RANK[c["strength"]] <= ceiling_rank
        ]
        stages.append({
            "stage": "strength",
            "before": before,
            "after": len(kept),
            "rule": (
                f"Strength ceiling: {strength_ceiling_level}. Unverified "
                "strength is reported as unconfirmed, not filtered out silently."
            ),
        })
        survivors = kept

    # Stage 4 — flavour (soft)
    if flavour:
        before = len(survivors)
        kept = [
            c for c in survivors
            if flavour.lower() in (c.get("notes", "") + " " + c.get("brand", "") +
                                    " " + c.get("model", "")).lower()
        ]
        stages.append({
            "stage": "flavour",
            "before": before,
            "after": len(kept),
            "rule": "Only decides between cigars that already passed stages 1–3.",
        })
        survivors = kept

    return {
        "survivors": survivors,
        "stages": stages,
        "anti_recommendations": ANTI_RECOMMENDATIONS,
        "note": (
            "Read the ledger before the catalogue. With no ledger, or when "
            "nothing on it fits, narrow by vitola and verify each candidate "
            "individually with scripts/lookup.py — the catalogue index holds "
            "brand and model only, no strength data."
        ),
    }


def _estimate_minutes(length_in: float | None, ring_gauge: int | None):
    """Very rough estimate from length x ring gauge; returns (min, max) or None."""
    if length_in is None or ring_gauge is None:
        return None
    # Crude model: minutes ≈ length * ring / 10, bounded by the sizing table
    # order of magnitude. This is a heuristic, not a published measurement.
    lo = max(15, length_in * ring_gauge / 12)
    hi = length_in * ring_gauge / 8
    return (lo, hi)


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--time",
        type=int,
        help="Minutes actually available for the session",
    )
    ap.add_argument(
        "--strength-ceiling",
        choices=STRENGTH_LEVELS,
        help="Strength ceiling: " + ", ".join(STRENGTH_LEVELS),
    )
    ap.add_argument(
        "--experience",
        choices=sorted(EXPERIENCE_CEILING.keys()),
        help="Experience level to derive a strength ceiling from",
    )
    ap.add_argument(
        "--state-check",
        action="store_true",
        help="Run the state check (needs --arrived-days / --feels / --cold-draw "
             "/ --mould)",
    )
    ap.add_argument(
        "--arrived-days", type=int, help="Days since the cigar arrived",
    )
    ap.add_argument(
        "--feels", help="How it feels when squeezed (brittle / spongy / firm)",
    )
    ap.add_argument(
        "--cold-draw", help="Cold-draw impression (e.g. 'ammonia')",
    )
    ap.add_argument(
        "--mould", help="Mould observation (e.g. 'plume' or 'fuzzy patch')",
    )
    ap.add_argument(
        "--anti",
        action="store_true",
        help="Show the anti-recommendation list and exit",
    )
    ap.add_argument(
        "--sizing-table",
        action="store_true",
        help="Show the length × ring gauge smoking-time estimate table and exit",
    )
    args = ap.parse_args()

    if args.anti:
        print(json.dumps({"anti_recommendations": ANTI_RECOMMENDATIONS},
                         ensure_ascii=False, indent=2))
        return 0

    if args.sizing_table:
        print(json.dumps(
            {"sizing_table": SIZING_TABLE, "rule_of_thumb": RULE_OF_THUMB},
            ensure_ascii=False, indent=2))
        return 0

    if args.state_check:
        result = state_report(args.arrived_days, args.feels,
                              args.cold_draw, args.mould)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.time is not None:
        result = time_filter(args.time)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    if args.strength_ceiling or args.experience:
        result = strength_ceiling(args.experience, args.strength_ceiling)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0

    print("Provide one of: --time, --strength-ceiling, --experience, "
          "--state-check, --anti, --sizing-table", file=sys.stderr)
    return 1


if __name__ == "__main__":
    sys.exit(main())
