#!/usr/bin/env python3
"""Regression tests for scripts/choose.py - state/time/strength/flavour narrowing.

Run from the skill root:

    python3 -m unittest tests.test_choose

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
import choose  # noqa: E402  (import after path insert)


class TestChooseUnit(unittest.TestCase):
    def test_state_report_pass(self):
        res = choose.state_report(arrived_days=20, feels="firm",
                                  cold_draw="clean", mould="plume")
        self.assertEqual(res["state_check"], "pass")
        self.assertEqual(res["failures"], [])

    def test_state_report_arrival_fail(self):
        res = choose.state_report(arrived_days=3, feels="firm")
        self.assertEqual(res["state_check"], "fail")
        self.assertEqual(len(res["failures"]), 1)
        self.assertEqual(res["failures"][0]["check"],
                         "Arrived within the last two weeks")

    def test_state_report_dry(self):
        res = choose.state_report(arrived_days=20, feels="hard and crackles")
        self.assertEqual(res["state_check"], "fail")
        checks = [f["check"] for f in res["failures"]]
        self.assertIn("Squeezes hard and crackles, or feels brittle", checks)

    def test_state_report_spongy(self):
        res = choose.state_report(arrived_days=20, feels="spongy")
        self.assertEqual(res["state_check"], "fail")
        checks = [f["check"] for f in res["failures"]]
        self.assertIn("Feels spongy, or the wrapper is slick", checks)

    def test_state_report_ammonia(self):
        res = choose.state_report(arrived_days=20, feels="firm", cold_draw="ammonia")
        self.assertEqual(res["state_check"], "fail")
        checks = [f["check"] for f in res["failures"]]
        self.assertIn("Ammonia on the cold draw", checks)

    def test_state_report_mould_not_plume(self):
        res = choose.state_report(arrived_days=20, feels="firm",
                                  mould="fuzzy green patch")
        self.assertEqual(res["state_check"], "fail")
        checks = [f["check"] for f in res["failures"]]
        self.assertIn("Any mould that is not plainly plume", checks)

    def test_time_filter_under_30(self):
        res = choose.time_filter(20)
        self.assertEqual(res["minutes_available"], 20)
        self.assertTrue(any("3-inch" in a for a in res["advice"]))

    def test_time_filter_under_90(self):
        res = choose.time_filter(45)
        self.assertEqual(res["rule_of_thumb"], choose.RULE_OF_THUMB)
        self.assertIn("sizing_table", res)
        self.assertIn("5–6\"", res["sizing_table"])
        self.assertEqual(len(res["advice"]), 2)

    def test_time_filter_90_plus(self):
        res = choose.time_filter(120)
        self.assertEqual(len(res["advice"]), 1)
        self.assertIn("Full vitola range is open", res["advice"][0])

    def test_strength_ceiling_experience(self):
        res = choose.strength_ceiling(experience="First few cigars")
        self.assertEqual(res["ceiling"], "Mild to medium")
        self.assertIn("Petit Corona", res["sizing_that_pairs"])

    def test_strength_ceiling_habitual(self):
        res = choose.strength_ceiling(experience="Habitual")
        self.assertEqual(res["ceiling"], "No ceiling")

    def test_strength_ceiling_explicit(self):
        res = choose.strength_ceiling(explicit="Full")
        self.assertEqual(res["ceiling"], "Full")

    def test_strength_ceiling_unknown_explicit(self):
        res = choose.strength_ceiling(explicit="Extra Full")
        self.assertIn("error", res)

    def test_strength_ceiling_missing(self):
        res = choose.strength_ceiling()
        self.assertIn("error", res)
        self.assertIn("available_experience", res)
        self.assertIn("available_strength", res)

    def test_estimate_minutes(self):
        est = choose._estimate_minutes(5.5, 52)
        self.assertIsNotNone(est)
        self.assertEqual(len(est), 2)
        self.assertTrue(est[0] <= est[1])
        self.assertIsNone(choose._estimate_minutes(None, 52))
        self.assertIsNone(choose._estimate_minutes(5.5, None))

    def test_narrow_state_stage(self):
        cands = [
            {"brand": "A", "model": "X", "state_ok": True},
            {"brand": "B", "model": "Y", "state_ok": False},
        ]
        res = choose.narrow(cands)
        self.assertEqual(len(res["survivors"]), 1)
        self.assertEqual(res["survivors"][0]["model"], "X")
        stage = res["stages"][0]
        self.assertEqual(stage["stage"], "state")
        self.assertEqual(stage["before"], 2)
        self.assertEqual(stage["after"], 1)

    def test_narrow_strength_ceiling_keeps_unverified(self):
        cands = [
            {"brand": "A", "model": "X", "state_ok": True, "strength": None},
            {"brand": "B", "model": "Y", "state_ok": True, "strength": "Full"},
        ]
        res = choose.narrow(cands, strength_ceiling_level="Medium")
        self.assertEqual(len(res["survivors"]), 1)
        self.assertEqual(res["survivors"][0]["model"], "X")

    def test_narrow_strength_filters_confirmed(self):
        cands = [
            {"brand": "A", "model": "X", "state_ok": True, "strength": "Medium"},
            {"brand": "B", "model": "Y", "state_ok": True, "strength": "Full"},
        ]
        res = choose.narrow(cands, strength_ceiling_level="Medium")
        self.assertEqual(len(res["survivors"]), 1)
        self.assertEqual(res["survivors"][0]["model"], "X")

    def test_narrow_flavour_soft(self):
        cands = [
            {"brand": "Oliva", "model": "Serie V", "state_ok": True,
             "notes": "coffee and leather"},
            {"brand": "Oliva", "model": "Serie G", "state_ok": True,
             "notes": "cedar and nuts"},
        ]
        res = choose.narrow(cands, flavour="coffee")
        self.assertEqual(len(res["survivors"]), 1)
        self.assertEqual(res["survivors"][0]["model"], "Serie V")

    def test_narrow_full_pipeline(self):
        cands = [
            {"brand": "A", "model": "X", "state_ok": True,
             "length_in": 7.0, "ring_gauge": 52, "strength": "Medium",
             "notes": "cedar"},
            {"brand": "B", "model": "Y", "state_ok": False,
             "length_in": 5.0, "ring_gauge": 50, "strength": "Medium",
             "notes": "cedar"},
            {"brand": "C", "model": "Z", "state_ok": True,
             "length_in": 7.0, "ring_gauge": 54, "strength": "Full",
             "notes": "cedar"},
        ]
        res = choose.narrow(cands, minutes_available=45,
                            strength_ceiling_level="Medium", flavour="cedar")
        self.assertEqual(len(res["survivors"]), 1)
        self.assertEqual(res["survivors"][0]["model"], "X")
        self.assertEqual([s["stage"] for s in res["stages"]],
                         ["state", "time", "strength", "flavour"])

    def test_anti_recommendations_present(self):
        self.assertGreaterEqual(len(choose.ANTI_RECOMMENDATIONS), 3)
        for item in choose.ANTI_RECOMMENDATIONS:
            self.assertIn("do_not", item)
            self.assertIn("because", item)


class TestChooseCli(unittest.TestCase):
    def run_choose(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "choose.py"), *args],
            capture_output=True, text=True,
        )

    def test_anti(self):
        res = self.run_choose("--anti")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertIn("anti_recommendations", payload)

    def test_sizing_table(self):
        res = self.run_choose("--sizing-table")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertIn("sizing_table", payload)
        self.assertIn("rule_of_thumb", payload)

    def test_state_check_pass(self):
        res = self.run_choose("--state-check", "--arrived-days", "20", "--feels",
                              "firm", "--cold-draw", "", "--mould", "plume")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["state_check"], "pass")

    def test_state_check_fail(self):
        res = self.run_choose("--state-check", "--arrived-days", "3")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["state_check"], "fail")

    def test_time(self):
        res = self.run_choose("--time", "45")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["minutes_available"], 45)

    def test_strength_ceiling_cli(self):
        res = self.run_choose("--strength-ceiling", "Full")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["ceiling"], "Full")

    def test_no_args_exit_one(self):
        res = self.run_choose()
        self.assertEqual(res.returncode, 1)


if __name__ == "__main__":
    unittest.main()
