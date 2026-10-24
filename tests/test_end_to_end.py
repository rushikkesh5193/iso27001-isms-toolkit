import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from isms.core import load_org, load_config, analyse
from isms.report import soa_csv, to_markdown
from helpers import AS_OF

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "examples" / "sample_org.json"

EXPECTED = {
    ("controls", "SoA", "NOT_ASSESSED"), ("controls", "8.30", "EXCLUDED_NO_JUSTIFICATION"),
    ("controls", "5.9", "NO_EVIDENCE"), ("controls", "6.1", "EVIDENCE_STALE"), ("controls", "SoA", "NO_OWNER"),
    ("risks", "R01", "RISK_RELIES_ON_GAP"), ("risks", "R02", "RISK_RELIES_ON_GAP"), ("risks", "R02", "TREATMENT_OVERDUE"),
    ("risks", "R03", "RISK_UNTREATED"), ("risks", "R07", "RISK_RELIES_ON_GAP"), ("risks", "R07", "RISK_ACCEPT_NO_APPROVAL"),
    ("risks", "R07", "RISK_ACCEPT_REVIEW_OVERDUE"), ("risks", "R08", "RISK_UNKNOWN_CONTROL"), ("risks", "R09", "CRITICAL_RISK_ACCEPTED"),
    ("audit", "F-01", "FINDING_OVERDUE"), ("audit", "F-02", "FINDING_OVERDUE"), ("audit", "F-03", "FINDING_OVERDUE"),
    ("audit", "F-06", "FINDING_UNKNOWN_CONTROL"), ("programme", "Cl. 9.2", "INTERNAL_AUDIT_OVERDUE"),
}


class TestSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.org = load_org(SAMPLE)
        cls.res = analyse(cls.org, load_config(), AS_OF)

    def test_finds_exactly_the_injected_problems(self):
        got = {(i.area, i.ref, i.check) for i in self.res["issues"]}
        self.assertEqual(got - EXPECTED, set(), "false positives")
        self.assertEqual(EXPECTED - got, set(), "missed")

    def test_readiness_numbers(self):
        o = self.res["readiness"]["overall"]
        self.assertEqual((o["in_scope"], o["excluded"], o["not_assessed"], o["implemented"], o["partial"]), (91, 2, 5, 82, 2))
        self.assertEqual(o["score"], 91.2)

    def test_gaps_ordered_worst_first(self):
        self.assertEqual([g["id"] for g in self.res["gaps"]], ["5.7", "8.12", "5.30", "8.16"])

    def test_soa_has_a_row_per_control(self):
        lines = soa_csv(self.res["rows"]).strip().splitlines()
        self.assertEqual(len(lines), 94)

    def test_issues_sorted_by_severity(self):
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        s = [order[i.severity] for i in self.res["issues"]]
        self.assertEqual(s, sorted(s))

    def test_markdown_has_heat_map_and_gaps(self):
        md = to_markdown(self.res, self.org, AS_OF)
        self.assertIn("heat map", md)
        self.assertIn("Threat intelligence", md)


class TestCli(unittest.TestCase):
    def cli(self, *a):
        return subprocess.run([sys.executable, "-m", "isms", *a], cwd=ROOT, capture_output=True, text=True)

    def test_writes_three_files(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.cli(str(SAMPLE), "--as-of", "2026-10-24", "--out-dir", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(sorted(p.name for p in Path(d).iterdir()), ["report.json", "report.md", "soa.csv"])
            self.assertEqual(len(json.loads((Path(d) / "report.json").read_text())["issues"]), len(EXPECTED))

    def test_exit_codes(self):
        self.assertEqual(self.cli(str(SAMPLE), "--as-of", "2026-10-24", "--fail-on", "high").returncode, 1)
        self.assertEqual(self.cli("missing.json").returncode, 2)
        self.assertEqual(self.cli(str(SAMPLE), "--as-of", "nope").returncode, 2)


if __name__ == "__main__":
    unittest.main()
