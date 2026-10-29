#!/usr/bin/env python3
"""Regression tests for scripts/pair.py - drink/food pairing matrix.

Run from the skill root:

    python3 -m unittest tests.test_pair

No network, no third-party dependencies.
"""

import json
import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import pair  # noqa: E402  (import after path insert)


class TestPairUnit(unittest.TestCase):
    def test_body_levels(self):
        self.assertEqual(pair.BODY_LEVELS, ["Light", "Medium", "Med-full", "Full"])

    def test_body_for_drink_known(self):
        ratings = pair.body_for_drink("Aged rum")
        self.assertEqual(ratings["Light"], "acceptable")
        self.assertEqual(ratings["Full"], "recommended")
        self.assertEqual(ratings["Medium"], "recommended")

    def test_body_for_drink_unknown(self):
        self.assertEqual(pair.body_for_drink("No Such Drink"), {})

    def test_drinks_for_body_full(self):
        rated = pair.drinks_for_body("Full")
        self.assertEqual(rated["Aged rum"], "recommended")
        self.assertEqual(rated["Peated Scotch"], "recommended")
        self.assertEqual(rated["Pilsner / light lager"], "avoid")
        self.assertEqual(rated["Dry white / Champagne"], "avoid")

    def test_drinks_for_body_unknown(self):
        self.assertEqual(pair.drinks_for_body("Extra Full"), {})

    def test_render_rating(self):
        self.assertEqual(pair.render_rating("recommended"), "✓")
        self.assertEqual(pair.render_rating("acceptable"), "○")
        self.assertEqual(pair.render_rating("avoid"), "✗")
        self.assertEqual(pair.render_rating("bogus"), "?")

    def test_pair_body_recommends(self):
        res = pair.pair(body="Medium")
        self.assertEqual(res["body"], "Medium")
        self.assertIn("Aged rum", res["recommended"])
        self.assertIn("Espresso", res["recommended"])
        self.assertIn("Pilsner / light lager", res["recommended"])
        self.assertIn("Peated Scotch", res["avoid"])

    def test_pair_drink_by_body(self):
        res = pair.pair(drink="Aged rum")
        self.assertEqual(res["drink"], "Aged rum")
        self.assertEqual(res["by_body"]["Full"], "✓ recommended")
        self.assertEqual(res["by_body"]["Light"], "○ acceptable")

    def test_pair_wrapper_overlay(self):
        res = pair.pair(body="Full", wrapper="Dark fermented")
        wg = res["wrapper_group"]
        self.assertEqual(wg["group"], "Dark fermented")
        self.assertEqual(wg["zh"], "深发酵（Maduro, San Andrés, Broadleaf）")
        self.assertIn("Espresso", wg["lean_towards"])

    def test_pair_wrapper_overlay_neutral(self):
        res = pair.pair(body="Light", wrapper="Neutral")
        self.assertEqual(wg := res["wrapper_group"]["group"], "Neutral")
        self.assertIn("Bourbon", res["wrapper_group"]["lean_towards"])

    def test_pair_unknown_wrapper(self):
        res = pair.pair(body="Full", wrapper="Not A Group")
        self.assertIn("wrapper_error", res)

    def test_pair_unknown_body(self):
        res = pair.pair(body="Extra Full")
        self.assertIn("error", res)
        self.assertIn("one of", res["error"])

    def test_pair_no_args(self):
        res = pair.pair()
        self.assertIn("error", res)

    def test_food_and_avoid(self):
        self.assertIn("Dark chocolate (70%+)", pair.FOOD)
        self.assertIn("Strong spice", pair.FOOD_AVOID)

    def test_never_pairs_by_brand(self):
        self.assertIn("Do not pair by brand", pair.WHAT_NOT_TO_DO[0])
        self.assertIn("specific bottle", pair.WHAT_NOT_TO_DO[1])
        self.assertIn("canonical", pair.WHAT_NOT_TO_DO[2])


class TestPairCli(unittest.TestCase):
    def run_pair(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "pair.py"), *args],
            capture_output=True, text=True,
        )

    def test_food(self):
        res = self.run_pair("--food")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertIn("Dark chocolate (70%+)", payload["food"])
        self.assertIn("avoid", payload)

    def test_rules(self):
        res = self.run_pair("--rules")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertIn("order_and_technique", payload)
        self.assertIn("what_not_to_do", payload)

    def test_body_wrapper(self):
        res = self.run_pair("--body", "Full", "--wrapper", "Dark fermented")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["body"], "Full")
        self.assertEqual(payload["wrapper_group"]["group"], "Dark fermented")

    def test_drink(self):
        res = self.run_pair("--drink", "Aged rum")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["drink"], "Aged rum")

    def test_unknown_drink_exit_one(self):
        res = self.run_pair("--drink", "Nope")
        self.assertEqual(res.returncode, 1)

    def test_unknown_body_exit_one(self):
        # argparse rejects unknown --body choices with exit code 2.
        res = self.run_pair("--body", "Extra Full")
        self.assertEqual(res.returncode, 2)


if __name__ == "__main__":
    unittest.main()
