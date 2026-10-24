import unittest

from helpers import org, ctl, checks, run, risk


class TestControlChecks(unittest.TestCase):
    def test_clean_org_has_no_issues(self):
        self.assertEqual(checks(org()), set())

    def test_exclusion_needs_justification(self):
        bad = org({"8.30": ctl(applicable=False, justification="", status=None)})
        good = org({"8.30": ctl(applicable=False, justification="No outsourced development", status=None)})
        self.assertIn(("EXCLUDED_NO_JUSTIFICATION", "8.30"), checks(bad))
        self.assertNotIn(("EXCLUDED_NO_JUSTIFICATION", "8.30"), checks(good))
        self.assertIn(("EXCLUDED_NO_JUSTIFICATION", "8.30"), checks(org({"8.30": ctl(applicable=False, justification="   ", status=None)})))

    def test_evidence_required_for_implemented_and_partial_only(self):
        self.assertIn(("NO_EVIDENCE", "5.1"), checks(org({"5.1": ctl(evidence="")})))
        self.assertIn(("NO_EVIDENCE", "5.1"), checks(org({"5.1": ctl(status="partial", evidence="")})))
        self.assertNotIn(("NO_EVIDENCE", "5.1"), checks(org({"5.1": ctl(status="planned", evidence="")})))

    def test_staleness_boundary(self):
        # as-of 2026-10-24: reviewed 2025-10-24 is exactly 12 months (ok); 2025-10-23 is stale
        self.assertNotIn(("EVIDENCE_STALE", "5.1"), checks(org({"5.1": ctl(last_reviewed="2025-10-24")})))
        self.assertIn(("EVIDENCE_STALE", "5.1"), checks(org({"5.1": ctl(last_reviewed="2025-10-23")})))

    def test_missing_controls_reported_once(self):
        o = org()
        for cid in ("5.1", "5.2", "5.3"):
            del o["controls"][cid]
        found = [i for i in run(o)["issues"] if i.check == "NOT_ASSESSED"]
        self.assertEqual(len(found), 1)
        self.assertIn("3 Annex A controls", found[0].title)

    def test_owner_check_ignores_excluded(self):
        self.assertIn(("NO_OWNER", "SoA"), checks(org({"5.1": ctl(owner="")})))
        ex = org({"5.1": ctl(applicable=False, justification="n/a", owner="", status=None)})
        self.assertNotIn(("NO_OWNER", "SoA"), checks(ex))


class TestRiskChecks(unittest.TestCase):
    def issues(self, ctrl_overrides=None, **rk):
        return {(i.check, i.severity) for i in run(org(ctrl_overrides, risks=[risk(**rk)]))["issues"]}

    def test_unknown_control_reference(self):
        self.assertIn(("RISK_UNKNOWN_CONTROL", "medium"), self.issues(controls=["9.9"]))

    def test_credit_for_unimplemented_control(self):
        # residual lowered, control not implemented -> flagged; partial is medium, planned is high
        base = dict(likelihood=4, impact=4, residual_likelihood=2, residual_impact=4, treatment_option="mitigate",
                    treatment_owner="o", treatment_due="2027-01-01", treatment_status="open")
        self.assertIn(("RISK_RELIES_ON_GAP", "high"),
                      self.issues({"8.12": ctl(status="planned")}, controls=["8.12"], **base))
        self.assertIn(("RISK_RELIES_ON_GAP", "medium"),
                      self.issues({"8.12": ctl(status="partial")}, controls=["8.12"], **base))
        self.assertNotIn("RISK_RELIES_ON_GAP", {c for c, _ in self.issues(controls=["8.12"], **base)})

    def test_no_credit_taken_means_no_reliance_flag(self):
        i = self.issues({"8.12": ctl(status="planned")}, controls=["8.12"], likelihood=3, impact=3)
        self.assertNotIn("RISK_RELIES_ON_GAP", {c for c, _ in i})

    def test_untreated_only_when_high_or_critical(self):
        self.assertIn(("RISK_UNTREATED", "high"), self.issues(likelihood=4, impact=3))        # 12
        self.assertNotIn("RISK_UNTREATED", {c for c, _ in self.issues(likelihood=3, impact=3)})  # 9
        self.assertIn(("RISK_UNTREATED", "critical"), self.issues(likelihood=5, impact=4))    # 20

    def test_acceptance_rules(self):
        c = {x for x, _ in self.issues(treatment_option="accept")}
        self.assertIn("RISK_ACCEPT_NO_APPROVAL", c)
        c = {x for x, _ in self.issues(treatment_option="accept", approved_by="CEO")}
        self.assertNotIn("RISK_ACCEPT_NO_APPROVAL", c)
        c = {x for x, _ in self.issues(treatment_option="accept", approved_by="CEO", likelihood=5, impact=4)}
        self.assertIn("CRITICAL_RISK_ACCEPTED", c)
        c = {x for x, _ in self.issues(treatment_option="accept", approved_by="CEO", review_date="2026-10-23")}
        self.assertIn("RISK_ACCEPT_REVIEW_OVERDUE", c)
        c = {x for x, _ in self.issues(treatment_option="accept", approved_by="CEO", review_date="2026-10-24")}
        self.assertNotIn("RISK_ACCEPT_REVIEW_OVERDUE", c)

    def test_treatment_overdue(self):
        base = dict(treatment_option="mitigate", treatment_owner="o")
        self.assertIn("TREATMENT_OVERDUE", {c for c, _ in self.issues(treatment_due="2026-10-23", treatment_status="open", **base)})
        self.assertNotIn("TREATMENT_OVERDUE", {c for c, _ in self.issues(treatment_due="2026-10-24", treatment_status="open", **base)})
        self.assertNotIn("TREATMENT_OVERDUE", {c for c, _ in self.issues(treatment_due="2026-01-01", treatment_status="complete", **base)})


class TestAuditAndProgramme(unittest.TestCase):
    def f(self, **kw):
        d = dict(id="F", type="major_nc", control="8.8", title="t", due="2026-10-01", owner="o")
        d.update(kw)
        return org(audit_findings=[d])

    def test_overdue_severity_by_type(self):
        for t, sev in (("major_nc", "high"), ("minor_nc", "medium"), ("observation", "low"), ("ofi", "low")):
            iss = [i for i in run(self.f(type=t))["issues"] if i.check == "FINDING_OVERDUE"]
            self.assertEqual([i.severity for i in iss], [sev], t)

    def test_closed_or_not_due_not_flagged(self):
        self.assertEqual(checks(self.f(closed="2026-10-05")), set())
        self.assertEqual(checks(self.f(due="2026-10-24")), set())

    def test_internal_audit_window(self):
        self.assertIn(("INTERNAL_AUDIT_OVERDUE", "Cl. 9.2"), checks(org(audit_programme=[{"date": "2025-10-23"}])))
        self.assertNotIn(("INTERNAL_AUDIT_OVERDUE", "Cl. 9.2"), checks(org(audit_programme=[{"date": "2025-10-24"}])))
        self.assertIn(("INTERNAL_AUDIT_OVERDUE", "Cl. 9.2"), checks(org(audit_programme=[])))

    def test_uses_latest_audit_not_first(self):
        o = org(audit_programme=[{"date": "2023-01-01"}, {"date": "2026-06-01"}])
        self.assertNotIn(("INTERNAL_AUDIT_OVERDUE", "Cl. 9.2"), checks(o))

    def test_management_review_and_risk_assessment(self):
        self.assertIn(("MGMT_REVIEW_OVERDUE", "Cl. 9.3"), checks(org(management_reviews=[])))
        self.assertIn(("RISK_ASSESSMENT_STALE", "Cl. 6.1.2"), checks(org(last_risk_assessment="2025-01-01")))


if __name__ == "__main__":
    unittest.main()
