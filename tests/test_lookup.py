#!/usr/bin/env python3
"""Regression tests for scripts/lookup.py - three-stage matching.

Run from the skill root:

    python3 -m unittest tests.test_lookup

No network, no third-party dependencies; builds a tiny index in a temp dir.
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = ROOT / "scripts"

sys.path.insert(0, str(SCRIPTS))
import lookup  # noqa: E402  (import after path insert)


class TestSlugify(unittest.TestCase):
    def test_bilingual_brand_drops_cjk(self):
        self.assertEqual(lookup.slugify("奥利瓦 Oliva"), "oliva")

    def test_pure_number_has_no_alpha(self):
        self.assertEqual(lookup.alpha_len("10"), 0)

    def test_ambiguous_word_is_known(self):
        self.assertIn("reserve", lookup.AMBIGUOUS)
        self.assertIn("maduro", lookup.AMBIGUOUS)

    def test_size_words_are_kept(self):
        self.assertIn("robusto", lookup.SIZE_WORDS)
        self.assertIn("toro", lookup.SIZE_WORDS)


class TestLockBrand(unittest.TestCase):
    BRANDS = ["oliva", "arturo-fuente", "undercrown-10", "cohiba"]

    def test_exact_match(self):
        self.assertEqual(lookup.lock_brand("Oliva", self.BRANDS), ["oliva"])

    def test_bilingual_query_drops_cjk(self):
        self.assertEqual(lookup.lock_brand("奥利瓦 Oliva", self.BRANDS), ["oliva"])

    def test_pure_number_is_not_a_brand(self):
        self.assertEqual(lookup.lock_brand("10", self.BRANDS), [])

    def test_ambiguous_word_alone_is_not_a_brand(self):
        self.assertEqual(lookup.lock_brand("Reserve", self.BRANDS), [])

    def test_unknown_brand(self):
        self.assertEqual(lookup.lock_brand("NoSuchBrand", self.BRANDS), [])

    def test_longer_slug_preferred(self):
        # "undercrown-10" starts with "undercrown" but is longer; prefix query
        # "undercrown" should return the longer, more specific slug.
        self.assertEqual(lookup.lock_brand("undercrown", self.BRANDS), ["undercrown-10"])


class TestScoreProduct(unittest.TestCase):
    def test_size_word_scores_higher(self):
        score, missing = lookup.score_product("serie-v-melanio-robusto", ["serie", "v", "melanio", "robusto"])
        self.assertEqual(missing, [])
        self.assertEqual(score, 5)  # serie+v+melanio = 3, robusto = 2

    def test_missing_token_reported(self):
        score, missing = lookup.score_product("serie-g", ["serie", "v", "melanio"])
        self.assertEqual(score, 1)
        self.assertEqual(missing, ["v", "melanio"])


class TestCountSatisfying(unittest.TestCase):
    CIGARS = [
        "oliva-serie-v-melanio-robusto",
        "oliva-serie-v-melanio-maduro-robusto",
        "oliva-serie-g",
        "arturo-fuente-hemingway-classic",
    ]

    def test_unique_satisfying(self):
        # "Serie G" matches only oliva-serie-g exactly.
        self.assertEqual(lookup.count_satisfying("oliva", "Serie G", self.CIGARS), 1)

    def test_multiple_satisfying_stays_review(self):
        self.assertEqual(
            lookup.count_satisfying("oliva", "Serie V Melanio", self.CIGARS), 2
        )

    def test_no_satisfying(self):
        self.assertEqual(lookup.count_satisfying("oliva", "NonExistent", self.CIGARS), 0)


class TestFindCandidates(unittest.TestCase):
    CIGARS = [
        "oliva-serie-v-melanio-robusto",
        "oliva-serie-v-melanio-maduro-robusto",
        "oliva-serie-g",
        "arturo-fuente-hemingway-classic",
    ]

    def test_exact_match_flag(self):
        cands = lookup.find_candidates("oliva", "Serie V Melanio Robusto", self.CIGARS, top=3)
        self.assertGreaterEqual(len(cands), 1)
        self.assertTrue(cands[0]["exact"])
        self.assertTrue(cands[0]["size_confirmed"])
        self.assertEqual(cands[0]["missing_tokens"], [])
        self.assertIn("url", cands[0])

    def test_no_candidates_when_brand_missing(self):
        self.assertEqual(
            lookup.find_candidates("nosuchbrand", "X", self.CIGARS, 3), []
        )


class TestCliEndToEnd(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        data = Path(self.tmp) / "data"
        data.mkdir()
        (data / "brands.txt").write_text(
            "\n".join(["oliva", "arturo-fuente", "undercrown-10"]) + "\n",
            encoding="utf-8",
        )
        (data / "cigars.txt").write_text(
            "\n".join(
                [
                    "oliva-serie-v-melanio-robusto",
                    "oliva-serie-v-melanio-maduro-robusto",
                    "oliva-serie-g",
                    "arturo-fuente-hemingway-classic",
                    "undercrown-10-something",
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        self.datadir = data

    def tearDown(self):
        shutil.rmtree(self.tmp)

    def run_lookup(self, *args):
        return subprocess.run(
            [sys.executable, str(SCRIPTS / "lookup.py"), "--datadir", str(self.datadir), *args],
            capture_output=True,
            text=True,
        )

    def test_check_reports_present(self):
        res = self.run_lookup("--check")
        self.assertEqual(res.returncode, 0)
        self.assertIn("ok  ", res.stdout)

    def test_exact_match_is_high(self):
        res = self.run_lookup("--brand", "Oliva", "--model", "Serie V Melanio Robusto")
        self.assertEqual(res.returncode, 0)
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["confidence"], "high")

    def test_bilingual_brand_works(self):
        res = self.run_lookup("--brand", "奥利瓦 Oliva", "--model", "Serie G")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["confidence"], "high")

    def test_under_specified_is_review(self):
        res = self.run_lookup("--brand", "Oliva", "--model", "Serie V Melanio")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "ok")
        self.assertEqual(payload["confidence"], "review")

    def test_pure_number_brand_is_no_match(self):
        res = self.run_lookup("--brand", "10", "--model", "X")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "no_brand_match")
        self.assertEqual(res.returncode, 0)

    def test_unknown_brand_is_no_match(self):
        res = self.run_lookup("--brand", "NoSuchBrand", "--model", "X")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "no_brand_match")

    def test_unknown_model_is_no_product_match(self):
        res = self.run_lookup("--brand", "Oliva", "--model", "NonExistent Model")
        payload = json.loads(res.stdout)
        self.assertEqual(payload["status"], "no_product_match")
        self.assertEqual(res.returncode, 0)

    def test_missing_args_errors(self):
        res = self.run_lookup("--brand", "Oliva")
        self.assertEqual(res.returncode, 1)

    def test_url_fetch_fails_on_unreachable_host(self):
        res = self.run_lookup("--url", "http://127.0.0.1:1/nope")
        self.assertEqual(res.returncode, 2)
        self.assertIn("fetch failed", res.stderr)


if __name__ == "__main__":
    unittest.main()
