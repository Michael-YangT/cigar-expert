#!/usr/bin/env python3
"""Drink and food pairing for a cigar.

Implements the matrix in `references/drink-pairing.md`:

  1. Match intensity first (cigar body × drink → ✓ / ○ / ✗).
  2. Then overlay the wrapper group (what the aroma actually meets).
  3. Then food and serving order rules.

Never pairs by brand, never recommends a specific bottle/shop/price, and never
claims a pairing is canonical.

Usage:
    python3 scripts/pair.py --body Medium --wrapper "Dark fermented"
    python3 scripts/pair.py --drink "Aged rum"
    python3 scripts/pair.py --food
    python3 scripts/pair.py --rules

Exit codes: 0 ok, 1 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys

# Rows are cigar body. Columns are drinks. Values: "recommended", "acceptable",
# "avoid". Rendered as ✓ / ○ / ✗ in the human summary.
BODY_LEVELS = ["Light", "Medium", "Med-full", "Full"]

DRINK_MATRIX = {
    "Pilsner / light lager": {"Light": "recommended", "Medium": "recommended",
                              "Med-full": "acceptable", "Full": "avoid"},
    "Dry white / Champagne": {"Light": "recommended", "Medium": "acceptable",
                              "Med-full": "avoid", "Full": "avoid"},
    "Fino / Manzanilla sherry": {"Light": "recommended", "Medium": "recommended",
                                 "Med-full": "acceptable", "Full": "avoid"},
    "Cider / sake": {"Light": "recommended", "Medium": "acceptable",
                     "Med-full": "avoid", "Full": "avoid"},
    "Bourbon": {"Light": "acceptable", "Medium": "recommended", "Med-full": "recommended",
                "Full": "acceptable"},
    "Rye": {"Light": "avoid", "Medium": "acceptable", "Med-full": "recommended",
            "Full": "acceptable"},
    "Peated Scotch": {"Light": "avoid", "Medium": "avoid", "Med-full": "acceptable",
                      "Full": "recommended"},
    "Cognac / Armagnac": {"Light": "acceptable", "Medium": "recommended",
                          "Med-full": "recommended", "Full": "acceptable"},
    "Aged rum": {"Light": "acceptable", "Medium": "recommended", "Med-full": "recommended",
                 "Full": "recommended"},
    "Tequila reposado": {"Light": "avoid", "Medium": "acceptable", "Med-full": "recommended",
                         "Full": "acceptable"},
    "Espresso": {"Light": "acceptable", "Medium": "recommended", "Med-full": "recommended",
                 "Full": "recommended"},
    "Black coffee / Americano": {"Light": "recommended", "Medium": "recommended",
                                 "Med-full": "acceptable", "Full": "acceptable"},
    "Black tea / puer": {"Light": "acceptable", "Medium": "recommended",
                         "Med-full": "recommended", "Full": "acceptable"},
    "Cola / sweet soda": {"Light": "recommended", "Medium": "acceptable",
                          "Med-full": "recommended", "Full": "recommended"},
    "Still water": {"Light": "recommended", "Medium": "recommended",
                    "Med-full": "recommended", "Full": "recommended"},
}

# Wrapper group -> what it does in a pairing -> lean towards.
WRAPPER_GROUPS = {
    "Light": {
        "zh": "浅发酵（Connecticut Shade, Claro）",
        "does": "Delicate, easily overwhelmed.",
        "lean": "Dry white, pilsner, light tea, water.",
    },
    "Neutral": {
        "zh": "中性（Habano, Corojo, Sumatra）",
        "does": "Takes most things.",
        "lean": "Bourbon, dry sherry, coffee.",
    },
    "Cuban": {
        "zh": "古巴",
        "does": "Earthy, distinctive, wants company that does not compete.",
        "lean": "Aged rum, cognac, mild tea.",
    },
    "Dark fermented": {
        "zh": "深发酵（Maduro, San Andrés, Broadleaf）",
        "does": "Sweet, dense, stands up to power.",
        "lean": "Espresso, aged rum, peated Scotch, dark chocolate.",
    },
    "Chinese domestic": {
        "zh": "国产",
        "does": "Often lighter and sweeter than expected.",
        "lean": "Light tea, lager, water.",
    },
}

FOOD = {
    "Dark chocolate (70%+)": (
        "Most reliable match for maduro and for coffee-forward cigars. "
        "Fat and bitterness both carry."
    ),
    "Nuts (almond, walnut, roasted cashew)": (
        "Neutral, resets the palate, works at any body."
    ),
    "Aged hard cheese": (
        "Stands up to full-bodied cigars; soft fresh cheese does not pair "
        "with anything here."
    ),
    "Grilled red meat": (
        "Conventional and defensible, mainly because of the fat."
    ),
    "Citrus / orange peel": (
        "The traditional cleaner between cigar and drink."
    ),
}
FOOD_AVOID = (
    "Strong spice and vinegar with anything light — the cigar will not "
    "survive the contact."
)

ORDER_AND_TECHNIQUE = [
    "Drink first, then smoke, then drink again — the sequence that shows what "
    "each did to the other. Most people get this backwards.",
    "Work from mild to strong across a session. A strong cigar first makes "
    "everything after it taste like paper.",
    "Rinse with water between drinks. Sweet drinks especially leave a film "
    "that mutes the next third of the cigar.",
    "Do not serve anything ice-cold and expect it to pair. Numbing the palate "
    "is not a pairing.",
]

WHAT_NOT_TO_DO = [
    "Do not pair by brand. There is no drink that goes with a name.",
    "Do not recommend a specific bottle, bar, shop or price. Pairing advice "
    "ends at the category; this skill gives no retail or purchasing guidance.",
    "Do not claim a pairing is canonical. Say what works and why, and let "
    "the user disagree.",
    "Do not ignore the storage state. A cigar stored too wet tastes flat, "
    "and no pairing fixes that — check defect-diagnosis.md before blaming "
    "the whisky.",
]


def body_for_drink(drink: str) -> dict[str, str]:
    """Return the rating of one drink across all four body levels."""
    if drink not in DRINK_MATRIX:
        return {}
    return DRINK_MATRIX[drink]


def drinks_for_body(body: str) -> dict[str, str]:
    """Return all drinks rated for one body level."""
    if body not in BODY_LEVELS:
        return {}
    return {drink: ratings[body] for drink, ratings in DRINK_MATRIX.items()}


def render_rating(value: str) -> str:
    return {"recommended": "✓", "acceptable": "○", "avoid": "✗"}.get(value, "?")


def pair(body: str | None = None, wrapper: str | None = None, drink: str | None = None) -> dict:
    result: dict = {}

    if drink:
        if drink not in DRINK_MATRIX:
            result["error"] = f"unknown drink '{drink}'"
            result["available_drinks"] = sorted(DRINK_MATRIX.keys())
            return result
        result["drink"] = drink
        result["by_body"] = {
            level: render_rating(DRINK_MATRIX[drink][level]) + " "
            + DRINK_MATRIX[drink][level]
            for level in BODY_LEVELS
        }
    elif body:
        if body not in BODY_LEVELS:
            result["error"] = f"unknown body '{body}' (one of {BODY_LEVELS})"
            return result
        rated = drinks_for_body(body)
        result["body"] = body
        result["recommended"] = sorted(
            d for d, v in rated.items() if v == "recommended"
        )
        result["acceptable"] = sorted(
            d for d, v in rated.items() if v == "acceptable"
        )
        result["avoid"] = sorted(d for d, v in rated.items() if v == "avoid")
    else:
        result["error"] = "provide --body or --drink"
        return result

    if wrapper:
        if wrapper not in WRAPPER_GROUPS:
            result["wrapper_error"] = (
                f"unknown wrapper group '{wrapper}' (one of "
                + ", ".join(sorted(WRAPPER_GROUPS.keys())) + ")"
            )
        else:
            wg = WRAPPER_GROUPS[wrapper]
            result["wrapper_group"] = {
                "group": wrapper,
                "zh": wg["zh"],
                "does": wg["does"],
                "lean_towards": wg["lean"],
            }

    result["food"] = FOOD
    result["food_avoid"] = FOOD_AVOID
    result["order_and_technique"] = ORDER_AND_TECHNIQUE
    result["what_not_to_do"] = WHAT_NOT_TO_DO
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--body",
        choices=BODY_LEVELS,
        help="Cigar body: " + ", ".join(BODY_LEVELS),
    )
    ap.add_argument(
        "--wrapper",
        help="Wrapper group: " + ", ".join(sorted(WRAPPER_GROUPS.keys())),
    )
    ap.add_argument(
        "--drink",
        help="Look up one drink across all body levels: "
        + ", ".join(sorted(DRINK_MATRIX.keys())),
    )
    ap.add_argument(
        "--food",
        action="store_true",
        help="Show food pairing guidance and exit",
    )
    ap.add_argument(
        "--rules",
        action="store_true",
        help="Show serving order and what-not-to-do rules and exit",
    )
    args = ap.parse_args()

    if args.food:
        print(
            json.dumps(
                {"food": FOOD, "avoid": FOOD_AVOID},
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    if args.rules:
        print(
            json.dumps(
                {
                    "order_and_technique": ORDER_AND_TECHNIQUE,
                    "what_not_to_do": WHAT_NOT_TO_DO,
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 0

    result = pair(args.body, args.wrapper, args.drink)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if "error" not in result and "wrapper_error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
