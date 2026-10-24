import unittest
from collections import Counter

from isms.annex_a import CONTROLS, NEW_IN_2022
from isms.core import readiness, control_rows, rating, score, add_months, pdate, load_org
from helpers import CFG, org, ctl
from datetime import date
import json, tempfile, os


class TestAnnexA(unittest.TestCase):
    def test_93_controls_in_four_themes(self):
        self.assertEqual(len(CONTROLS), 93)
        self.assertEqual(Counter(c["theme"] for c in CONTROLS.values()),
                         {"Organizational": 37, "People": 8, "Physical": 14, "Technological": 34})

    def test_eleven_new_controls_all_exist(self):
        self.assertEqual(len(NEW_IN_2022), 11)
        self.assertTrue(NEW_IN_2022 <= set(CONTROLS))


class TestReadiness(unittest.TestCase):
    def overall(self, **controls):
        return readiness(control_rows(org(controls)), CFG)["overall"]

    def test_clean_is_100(self):
        self.assertEqual(self.overall()["score"], 100.0)

    def test_partial_counts_half(self):
        o = self.overall(**{"5.1": ctl(status="partial")})
        self.assertEqual(o["score"], round(100 * 92.5 / 93, 1))

    def test_exclusion_removes_from_denominator(self):
        o = self.overall(**{"5.1": ctl(applicable=False, justification="x", status=None)})
        self.assertEqual((o["in_scope"], o["excluded"], o["score"]), (92, 1, 100.0))

    def test_not_assessed_is_in_scope_with_no_credit(self):
        c = org()["controls"]
        del c["5.1"]
        o = readiness(control_rows({"controls": c}), CFG)["overall"]
        self.assertEqual((o["in_scope"], o["not_assessed"]), (93, 1))
        self.assertEqual(o["score"], round(100 * 92 / 93, 1))


class TestHelpers(unittest.TestCase):
    def test_rating_boundaries(self):
        self.assertEqual([rating(s, CFG) for s in (5, 6, 11, 12, 19, 20, 25)],
                         ["low", "medium", "medium", "high", "high", "critical", "critical"])
        self.assertEqual(score(4, 5), 20)

    def test_add_months_clamps(self):
        self.assertEqual(add_months(date(2026, 1, 31), 1), date(2026, 2, 28))

    def test_bad_date(self):
        with self.assertRaises(ValueError):
            pdate("24/10/2026")


class TestLoadValidation(unittest.TestCase):
    def load(self, data):
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            json.dump(data, fh)
        try:
            return load_org(fh.name)
        finally:
            os.unlink(fh.name)

    def test_unknown_control_rejected(self):
        with self.assertRaises(ValueError):
            self.load({"controls": {"9.9": {}}})

    def test_bad_status_rejected(self):
        with self.assertRaises(ValueError):
            self.load({"controls": {"5.1": {"applicable": True, "status": "done"}}})

    def test_risk_score_range_enforced(self):
        with self.assertRaises(ValueError):
            self.load({"risks": [{"id": "R", "likelihood": 6, "impact": 1}]})

    def test_duplicate_risk_ids_rejected(self):
        r = {"id": "R", "likelihood": 1, "impact": 1}
        with self.assertRaises(ValueError):
            self.load({"risks": [r, r]})


if __name__ == "__main__":
    unittest.main()
