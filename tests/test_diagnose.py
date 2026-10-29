#!/usr/bin/env python3
"""Regression tests for scripts/diagnose.py - fault diagnosis decision tree.

Run from the skill root:

    python3 -m unittest tests.test_diagnose

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
import diagnose  # noqa: E402  (import after path insert)


class TestDiagnoseUnit(unittest.TestCase):
    def test_unknown_symptom_returns_available(self):
        res = diagnose.diagnose("not-a-real-symptom", "one")
        self.assertEqual(res["error"], "unknown symptom 'not-a-real-symptom'")
        self.assertIn("canoeing", res["available"])
        self.assertIn("beetle", res["available"])

    def test_unknown_scope(self):
        res = diagnose.diagnose("canoeing", "both")
        self.assertEqual(res["error"], "unknown scope 'both' (one of ['one', 'several'])")

    def test_canoeing_one_cigar(self):
        res = diagnose.diagnose("canoeing", "one")
        self.assertEqual(res["symptom"], "canoeing")
        self.assertEqual(res["symptom_zh"], "斜烧")
        self.assertEqual(res["scope"], "one")
        self.assertEqual(res["first_split"], "construction cause")
        self.assertEqual(res["most_likely"], "Lit unevenly, or smoked outdoors in moving air.")
        self.assertEqual(res["source"], "https://cigarcapitol.com/dictionary/canoeing/")
        self.assertIn("handling", res)
        self.assertIn("prevention", res)
        self.assertEqual(res["what_not_to_do"], diagnose.WHAT_NOT_TO_DO)

    def test_runner_has_no_source(self):
        res = diagnose.diagnose("runner", "one")
        self.assertIn("source_note", res)
        self.assertNotIn("source", res)

    def test_tunneling_several_same_box(self):
        res = diagnose.diagnose("tunneling", "several", box="same_box")
        self.assertEqual(res["first_split"], "storage or batch cause")
        self.assertEqual(
            res["subcase"],
            diagnose.FIRST_SPLIT["several"]["subcases"]["same_box"],
        )

    def test_tunneling_several_different_brands(self):
        res = diagnose.diagnose("tunneling", "several", box="different_brands")
        self.assertEqual(
            res["subcase"],
            diagnose.FIRST_SPLIT["several"]["subcases"]["different_brands"],
        )

    def test_tunneling_several_unrecognised_box(self):
        res = diagnose.diagnose("tunneling", "several", box="maybe")
        self.assertIn("Unrecognised box description", res["subcase"])

    def test_mold_vs_bloom_actions(self):
        res = diagnose.diagnose("mold-vs-bloom", "one")
        self.assertIn("mould_action", res)
        self.assertIn("plume_action", res)
        self.assertEqual(res["plume_action"], "Nothing to do.")
        self.assertIn("Isolate", res["mould_action"])

    def test_beetle_temperature_dispute(self):
        res = diagnose.diagnose("beetle", "one")
        self.assertIn("temperature_dispute", res)
        self.assertIn("22", res["temperature_dispute"])
        self.assertIn("24", res["temperature_dispute"])
        self.assertIn("signs", res)
        self.assertIn("handling", res)
        self.assertIn("prevention", res)


class TestDiagnoseCli(unittest.TestCase):
    def run_diagnose(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "diagnose.py"), *args],
            capture_output=True, text=True,
        )

    def test_list(self):
        res = self.run_diagnose("--list")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertIn("canoeing", payload["symptoms"])
        self.assertIn("beetle", payload["symptoms"])

    def test_symptom_exit_zero(self):
        res = self.run_diagnose("--symptom", "canoeing", "--scope", "one")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["symptom"], "canoeing")

    def test_several_with_box(self):
        res = self.run_diagnose("--symptom", "tunneling", "--scope", "several",
                                "--box", "same_box")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["subcase"], diagnose.FIRST_SPLIT["several"]["subcases"]["same_box"])

    def test_unknown_symptom_exit_one(self):
        res = self.run_diagnose("--symptom", "nope")
        self.assertEqual(res.returncode, 1)

    def test_missing_symptom_exit_one(self):
        res = self.run_diagnose()
        self.assertEqual(res.returncode, 1)


if __name__ == "__main__":
    unittest.main()
