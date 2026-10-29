#!/usr/bin/env python3
"""Diagnose a cigar burn, draw or wrapper fault.

Reads the decision tree in `references/defect-diagnosis.md` and returns a
structured diagnosis: storage cause vs construction cause, then the specific
fault handling steps.

Usage:
    python3 scripts/diagnose.py --symptom canoeing --scope one
    python3 scripts/diagnose.py --symptom tunneling --scope several --box "same box"
    python3 scripts/diagnose.py --list

Exit codes: 0 ok, 1 usage error.
"""

from __future__ import annotations

import argparse
import json
import sys

# The one question that decides everything downstream. Asked before any
# symptom-specific handling.
FIRST_SPLIT = {
    "one": {
        "reads_as": "construction cause",
        "what_to_change": "Treat the single cigar; leave the storage environment alone.",
        "note": (
            "Only valid if the rest of the box has been smoked at the measured "
            "RH of that container. If this is the only cigar smoked from it, "
            "storage cannot be ruled out yet: check the container's actual RH "
            "against its flavour-group target first."
        ),
    },
    "several": {
        "reads_as": "storage or batch cause",
        "what_to_change": "Investigate the environment or the box, not rolling technique.",
        "subcases": {
            "different_brands": (
                "Several cigars, different brands, all failing at once -> "
                "storage (humidity / temperature). Fix the environment."
            ),
            "same_box": (
                "Several from the same box, same symptom -> that box or batch. "
                "Isolate the box and check its RH."
            ),
            "always_this_model": (
                "Always this model, never others -> a characteristic of that vitola. "
                "Change size, or smoke it drier."
            ),
        },
    },
}

# Symptom -> handling steps. Cigar Capitol links where a cited entry exists;
# sections without a link are observation and experience, not cited definitions.
SYMPTOMS = {
    "canoeing": {
        "zh": "斜烧",
        "source": "https://cigarcapitol.com/dictionary/canoeing/",
        "most_likely": "Lit unevenly, or smoked outdoors in moving air.",
        "handling": (
            "Let it rest; a mild canoe often self-corrects as the slower side "
            "catches up once the coal evens out. If it does not, touch the flame "
            "to the lagging side only."
        ),
        "prevention": (
            "Toast the whole foot until the rim glows evenly before the first draw "
            "— an uneven start is the single most common cause."
        ),
    },
    "tunneling": {
        "zh": "隧道烧",
        "source": "https://cigarcapitol.com/dictionary/tunneling/",
        "most_likely": (
            "Storage RH too high, or an underfilled bunch. Tunneling is the classic "
            "wet-cigar signature — a tight draw and flat flavour usually come with it."
        ),
        "handling": (
            "Purge the cigar gently to push air through, then relight. It will not "
            "fully recover; the fix is drying, not technique."
        ),
        "prevention": (
            "Drop storage RH toward that group's own target in flavour-groups.md "
            "— 62% for dark fermented, 69% for light, 65% for the rest — rather "
            "than assuming 70% is right."
        ),
    },
    "runner": {
        "zh": "快烧线",
        "source": None,
        "source_note": "Observation, not a cited Cigar Capitol entry.",
        "most_likely": (
            "Construction. Uneven filler density or a thin patch in binder or "
            "wrapper. Unlike canoeing, a runner tends to persist."
        ),
        "handling": (
            "Touch the flame only to the slow side, repeatedly if needed."
        ),
        "prevention": (
            "None at the smoking end; if a whole box runners, it is a bad box."
        ),
    },
    "coning": {
        "zh": "锥形烧",
        "source": None,
        "source_note": "Observation, not a cited Cigar Capitol entry.",
        "most_likely": (
            "Shape and bunch design, not a defect. Common in figurados and in "
            "cigars whose bunch is deliberately looser at the foot."
        ),
        "handling": (
            "Normal; nothing to correct unless the wrapper stops burning entirely, "
            "which makes it tunneling instead."
        ),
        "prevention": None,
    },
    "extinguishing": {
        "zh": "熄火",
        "source": None,
        "source_note": "Observation, not a cited Cigar Capitol entry.",
        "most_likely": (
            "Puffed too slowly, or over-humidified, or both."
        ),
        "handling": (
            "Knock off the dead ash, purge the stale smoke, toast the exposed "
            "foot, then draw. Relighting without purging is why a re-lit cigar "
            "tastes bitter."
        ),
        "prevention": (
            "One draw every 30–60 seconds; slower than that the coal cools. "
            "If a box keeps going out regardless of pace, it is too wet."
        ),
    },
    "plug": {
        "zh": "堵塞",
        "source": "https://cigarcapitol.com/dictionary/plug/",
        "most_likely": (
            "Construction. A folded leaf, a piece of stem left in the bunch, or "
            "over-compression. Cannot be fixed by storage."
        ),
        "handling": (
            "Check the cut first — too small a cut mimics a plug. If it is a true "
            "plug, massaging the cigar sometimes shifts the fold; a stem plug "
            "usually does not clear. Do not drill it."
        ),
        "prevention": (
            "None. Note the box; if several are plugged, it is a bad box."
        ),
    },
    "tight-draw": {
        "zh": "吸阻大",
        "source": "https://cigarcapitol.com/dictionary/tight-draw/",
        "most_likely": (
            "Overfilled bunches, a folded filler leaf, or too small a cut."
        ),
        "handling": (
            "Re-cut slightly wider first. Persistent tightness in a whole box "
            "usually means the box is stored too wet — dry it and retest."
        ),
        "prevention": None,
        "split": (
            "If the cigar feels firm along its whole length, it is overfilled. "
            "If it feels firm at one spot only, it is a plug."
        ),
    },
    "open-draw": {
        "zh": "吸阻过小",
        "source": "https://cigarcapitol.com/dictionary/open-draw/",
        "most_likely": (
            "Underfilled or loosely bunched, sometimes a cheap blend. Also the "
            "smoking-side symptom of a dried-out cigar."
        ),
        "handling": (
            "Slow the pace down. An open draw overheats quickly and turns bitter."
        ),
        "prevention": None,
    },
    "too-dry": {
        "zh": "过干",
        "source": "https://cigarcapitol.com/dictionary/dry-boxing/",
        "signs": (
            "Brittle wrapper, cracks when handled, burns hot and fast, thin "
            "flavour, wrapper splits at the foot."
        ),
        "handling": (
            "Raise RH gradually over two to four weeks. Rapid re-humidification "
            "splits wrappers that were already brittle."
        ),
        "prevention": (
            "Check the seal and the pack, not just the gauge."
        ),
    },
    "too-wet": {
        "zh": "过湿",
        "source": "https://cigarcapitol.com/dictionary/over-humidification/",
        "signs": (
            "Spongy feel, tight draw, tunneling, flat flavour, goes out often, "
            "wrapper darkens and can spot."
        ),
        "handling": (
            "Dry at the target RH for the cigar's group rather than lower in the "
            "abstract."
        ),
        "prevention": (
            "Sort by group and set RH per group — see flavour-groups.md."
        ),
    },
    "cracked-wrapper": {
        "zh": "爆衣",
        "source": None,
        "source_note": "Observation, not a cited Cigar Capitol entry.",
        "most_likely": (
            "Handled dry, or re-humidified too fast, or cold-to-warm transition "
            "with condensation."
        ),
        "handling": (
            "A small crack at the foot rarely matters; a long split down the body "
            "will not hold a burn."
        ),
        "prevention": (
            "Never handle a cigar that feels crisp; let it come to room "
            "temperature in its wrapper before opening."
        ),
    },
    "mold-vs-bloom": {
        "zh": "发霉与开花",
        "source": "https://cigarcapitol.com/dictionary/plume-vs-mold/",
        "most_likely": None,
        "handling": (
            "Plume brushes off cleanly and leaves no mark; mould is raised, "
            "patchy, stains the leaf and smells musty. Brushing off cleanly is "
            "the test — confirm it really is plume before saying so."
        ),
        "mould_action": (
            "Isolate, then wipe and re-store at lower RH; check the neighbours in "
            "the same container, because they were exposed to the same conditions."
        ),
        "plume_action": "Nothing to do.",
        "prevention": None,
    },
    "beetle": {
        "zh": "虫害",
        "source": "https://cigarcapitol.com/dictionary/cigar-beetle/",
        "most_likely": None,
        "temperature_dispute": (
            "Sources disagree on the activation temperature: Cigar Capitol states "
            "eggs hatch reliably above roughly 22°C (72°F), while other guidance "
            "cites 24°C. Both figures are given; let the user choose the margin."
        ),
        "signs": (
            "Small round exit holes in the wrapper, fine dust at the foot or in "
            "the box, visible tunnels into the filler."
        ),
        "handling": (
            "Isolate the box immediately; treat the whole container, not just the "
            "affected cigar."
        ),
        "prevention": (
            "Temperature control matters more than humidity here. A cabinet "
            "running at 16–18°C is well below both cited thresholds."
        ),
    },
}

WHAT_NOT_TO_DO = (
    "Do not diagnose from a photograph alone. Tunneling and canoeing look alike, "
    "and a plug cannot be seen at all. Ask which symptom came first: a cigar that "
    "draws badly from the start is a construction problem, one that starts fine "
    "then goes wrong is almost always storage."
)


def list_symptoms() -> list[str]:
    return sorted(SYMPTOMS.keys())


def diagnose(symptom: str, scope: str, box: str | None = None) -> dict:
    if symptom not in SYMPTOMS:
        return {
            "error": f"unknown symptom '{symptom}'",
            "available": sorted(SYMPTOMS.keys()),
        }

    if scope not in FIRST_SPLIT:
        return {
            "error": f"unknown scope '{scope}' (one of {list(FIRST_SPLIT.keys())})",
        }

    split = FIRST_SPLIT[scope]
    entry = SYMPTOMS[symptom]

    result: dict = {
        "symptom": symptom,
        "symptom_zh": entry.get("zh"),
        "scope": scope,
        "first_split": split["reads_as"],
        "what_to_change": split["what_to_change"],
    }

    if scope == "several" and box:
        box_lower = box.lower()
        if box_lower in ("different_brands", "different", "mixed"):
            result["subcase"] = split["subcases"]["different_brands"]
        elif box_lower in ("same_box", "same", "box"):
            result["subcase"] = split["subcases"]["same_box"]
        elif box_lower in ("always_this_model", "this_model", "model"):
            result["subcase"] = split["subcases"]["always_this_model"]
        else:
            result["subcase"] = (
                f"Unrecognised box description '{box}'. Choose one of: "
                + ", ".join(split["subcases"].keys())
            )

    if entry.get("most_likely"):
        result["most_likely"] = entry["most_likely"]
    if entry.get("source"):
        result["source"] = entry["source"]
    if entry.get("source_note"):
        result["source_note"] = entry["source_note"]
    if entry.get("signs"):
        result["signs"] = entry["signs"]
    if entry.get("handling"):
        result["handling"] = entry["handling"]
    if entry.get("mould_action"):
        result["mould_action"] = entry["mould_action"]
    if entry.get("plume_action"):
        result["plume_action"] = entry["plume_action"]
    if entry.get("prevention"):
        result["prevention"] = entry["prevention"]
    if entry.get("temperature_dispute"):
        result["temperature_dispute"] = entry["temperature_dispute"]
    if entry.get("split"):
        result["split"] = entry["split"]

    result["what_not_to_do"] = WHAT_NOT_TO_DO
    return result


def main() -> int:
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument(
        "--symptom",
        help="Fault symptom: " + ", ".join(sorted(SYMPTOMS.keys())),
    )
    ap.add_argument(
        "--scope",
        choices=["one", "several"],
        default="one",
        help="One cigar or several (default: one)",
    )
    ap.add_argument(
        "--box",
        help="For --scope several: different_brands / same_box / always_this_model",
    )
    ap.add_argument(
        "--list",
        action="store_true",
        help="List all recognised symptoms and exit",
    )
    args = ap.parse_args()

    if args.list:
        print(json.dumps({"symptoms": list_symptoms()}, ensure_ascii=False, indent=2))
        return 0

    if not args.symptom:
        print("--symptom is required (or use --list)", file=sys.stderr)
        return 1

    result = diagnose(args.symptom, args.scope, args.box)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if "error" not in result else 1


if __name__ == "__main__":
    sys.exit(main())
