"""Generate a SYNTHETIC ISMS dataset for a fictional company ("ExampleOrg Pvt Ltd").

Most controls are healthy; a set of problems is injected on purpose so the
tests can check the tool finds exactly those and nothing else.

    python3 -m tools.gen_org examples/sample_org.json
"""
from __future__ import annotations

import json
import random
import sys

from isms.annex_a import CONTROLS

OWNERS = ["CISO", "IT Manager", "HR Head", "Facilities Lead", "DevOps Lead", "Compliance Lead"]


def theme_owner(cid):
    return {"5": "Compliance Lead", "6": "HR Head", "7": "Facilities Lead"}.get(cid.split(".")[0], "IT Manager")


def controls():
    rng = random.Random(3)
    out = {}
    for cid in CONTROLS:
        out[cid] = {"applicable": True, "status": "implemented", "owner": theme_owner(cid),
                    "evidence": f"EV-{cid}", "last_reviewed": f"2026-{rng.randint(3, 9):02d}-{rng.randint(1, 28):02d}"}
    # --- injected problems
    for cid in ("5.6", "5.32", "7.12", "7.13", "8.34"):          # never assessed
        del out[cid]
    out["8.4"] = {"applicable": False, "justification": "No in-house source code; all software is procured."}   # benign exclusion
    out["8.30"] = {"applicable": False, "justification": ""}                                                   # exclusion, no reason
    out["5.9"]["evidence"] = ""                                                                                # implemented, no evidence
    out["6.1"]["last_reviewed"] = "2025-06-01"                                                                 # stale
    out["5.7"].update(status="not_implemented", evidence="")
    out["8.12"].update(status="planned", evidence="")
    out["8.16"].update(status="partial")
    out["5.30"].update(status="partial")
    out["7.4"]["owner"] = ""                                                                                   # no owner
    return out


RISKS = [
    dict(id="R01", title="Ransomware encrypts file servers", asset="File servers", likelihood=4, impact=5,
         controls=["8.13", "8.7", "8.16"], residual_likelihood=2, residual_impact=5,
         treatment_option="mitigate", treatment_owner="IT Manager", treatment_due="2027-01-01", treatment_status="open"),
    dict(id="R02", title="Insider copies customer data to personal cloud", asset="Customer data", likelihood=3, impact=4,
         controls=["8.12"], residual_likelihood=2, residual_impact=4,
         treatment_option="mitigate", treatment_owner="CISO", treatment_due="2026-09-15", treatment_status="open"),
    dict(id="R03", title="Phishing leads to credential theft", asset="User accounts", likelihood=4, impact=4,
         controls=["6.3", "8.5"], residual_likelihood=3, residual_impact=4, treatment_option="none"),
    dict(id="R04", title="KYC vendor suffers a breach", asset="Vendor data flow", likelihood=3, impact=5,
         controls=["5.19", "5.20", "5.22"], residual_likelihood=2, residual_impact=5,
         treatment_option="mitigate", treatment_owner="Compliance Lead", treatment_due="2026-08-01", treatment_status="complete"),
    dict(id="R05", title="Unpatched internet-facing server exploited", asset="Web servers", likelihood=3, impact=4,
         controls=["8.8"], residual_likelihood=2, residual_impact=4,
         treatment_option="mitigate", treatment_owner="IT Manager", treatment_due="2027-02-01", treatment_status="open"),
    dict(id="R06", title="Loss of a key team member", asset="People", likelihood=2, impact=3, controls=[],
         treatment_option="accept", approved_by="CEO", review_date="2027-03-01"),
    dict(id="R07", title="Primary data centre outage", asset="Hosting", likelihood=2, impact=5, controls=["5.30"],
         residual_likelihood=1, residual_impact=5, treatment_option="accept", review_date="2026-08-01"),
    dict(id="R08", title="Weak guest Wi-Fi segregation", asset="Network", likelihood=2, impact=2, controls=["9.9"],
         treatment_option="mitigate", treatment_owner="IT Manager", treatment_due="2027-01-15", treatment_status="open"),
    dict(id="R09", title="Legacy unsupported OS still in production", asset="Legacy app server", likelihood=5, impact=4,
         controls=[], treatment_option="accept", approved_by="CEO", review_date="2027-01-01"),
    dict(id="R10", title="Loss of backup media in transit", asset="Backups", likelihood=2, impact=3,
         controls=["7.10", "8.13"], residual_likelihood=1, residual_impact=3,
         treatment_option="mitigate", treatment_owner="IT Manager", treatment_due="2027-03-01", treatment_status="open"),
]

FINDINGS = [
    dict(id="F-01", type="major_nc", control="8.8", title="Critical patches not applied within policy timelines",
         raised="2026-07-15", due="2026-09-30", owner="IT Manager"),
    dict(id="F-02", type="minor_nc", control="5.15", title="Access control policy not reviewed after reorganisation",
         raised="2026-07-15", due="2026-10-01", owner="CISO"),
    dict(id="F-03", type="observation", control="6.3", title="Awareness attendance records incomplete",
         raised="2026-07-15", due="2026-10-10", owner="HR Head"),
    dict(id="F-04", type="minor_nc", control="8.15", title="Log retention shorter than policy",
         raised="2026-07-15", due="2026-09-01", closed="2026-08-25", owner="IT Manager"),
    dict(id="F-05", type="minor_nc", control="5.24", title="Incident response plan not tested this year",
         raised="2026-07-15", due="2026-12-01", owner="CISO"),
    dict(id="F-06", type="ofi", control="9.9", title="Consider automating evidence collection",
         raised="2026-07-15", due="2026-12-31", closed="2026-09-01", owner="Compliance Lead"),
]


def main(path):
    org = {"_note": "SYNTHETIC DATA for a fictional company.", "organisation": "ExampleOrg Pvt Ltd (fictional)",
           "last_risk_assessment": "2026-03-10",
           "audit_programme": [{"date": "2025-09-15", "scope": "Full ISMS"}],
           "management_reviews": [{"date": "2026-04-20"}],
           "controls": controls(), "risks": RISKS, "audit_findings": FINDINGS}
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(org, fh, indent=1)
    print(f"wrote {path}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "examples/sample_org.json")
