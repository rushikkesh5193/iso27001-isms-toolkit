"""Load an ISMS data file, score readiness and run consistency checks.

Everything here is a rule over the data you give it. It cannot judge whether
a control is really effective, only whether the records are complete, current
and consistent with each other.
"""
from __future__ import annotations

import calendar
import json
from dataclasses import dataclass, asdict
from datetime import date
from pathlib import Path

from .annex_a import CONTROLS, THEMES

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3}
STATUSES = ("implemented", "partial", "planned", "not_implemented")
TREATMENTS = ("mitigate", "accept", "transfer", "avoid", "none")
FINDING_TYPES = ("major_nc", "minor_nc", "observation", "ofi")


@dataclass
class Issue:
    area: str          # controls | risks | audit | programme
    check: str
    severity: str
    ref: str
    title: str
    detail: str
    action: str

    def as_dict(self):
        return asdict(self)


def load_config(path=None):
    p = Path(path) if path else Path(__file__).with_name("config.json")
    return json.loads(p.read_text(encoding="utf-8"))


def pdate(v, what="date"):
    if v in (None, ""):
        return None
    try:
        return date.fromisoformat(str(v))
    except ValueError as exc:
        raise ValueError(f"bad {what} {v!r}: expected YYYY-MM-DD") from exc


def add_months(d: date, n: int) -> date:
    i = d.month - 1 + n
    y, m = d.year + i // 12, i % 12 + 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def load_org(path):
    """Read and validate an ISMS data file; raises ValueError with a clear message."""
    org = json.loads(Path(path).read_text(encoding="utf-8"))
    for cid, rec in org.get("controls", {}).items():
        if cid not in CONTROLS:
            raise ValueError(f"unknown Annex A control id {cid!r}")
        st = rec.get("status")
        if rec.get("applicable", True) and st is not None and st not in STATUSES:
            raise ValueError(f"control {cid}: status must be one of {STATUSES}, got {st!r}")
        pdate(rec.get("last_reviewed"), f"last_reviewed for {cid}")
    seen = set()
    for r in org.get("risks", []):
        if r["id"] in seen:
            raise ValueError(f"duplicate risk id {r['id']}")
        seen.add(r["id"])
        for k in ("likelihood", "impact", "residual_likelihood", "residual_impact"):
            if k in r and not 1 <= int(r[k]) <= 5:
                raise ValueError(f"risk {r['id']}: {k} must be 1..5")
        if r.get("treatment_option", "none") not in TREATMENTS:
            raise ValueError(f"risk {r['id']}: treatment_option must be one of {TREATMENTS}")
    for f in org.get("audit_findings", []):
        if f["type"] not in FINDING_TYPES:
            raise ValueError(f"finding {f['id']}: type must be one of {FINDING_TYPES}")
    return org


# ---------------------------------------------------------------- controls

def control_rows(org):
    """One row per Annex A control (all 93), including ones never assessed."""
    rows = []
    recs = org.get("controls", {})
    for cid, meta in CONTROLS.items():
        rec = recs.get(cid)
        if rec is None:
            state, applicable = "not_assessed", None
        elif not rec.get("applicable", True):
            state, applicable = "excluded", False
        else:
            state, applicable = rec.get("status") or "not_assessed", True
        rows.append({"id": cid, "title": meta["title"], "theme": meta["theme"],
                     "new_in_2022": meta["new_in_2022"], "state": state, "applicable": applicable,
                     "justification": (rec or {}).get("justification", ""),
                     "owner": (rec or {}).get("owner", ""),
                     "evidence": (rec or {}).get("evidence", ""),
                     "last_reviewed": (rec or {}).get("last_reviewed", "")})
    return rows


def readiness(rows, cfg):
    """Share of in-scope controls implemented. Unassessed controls count as in scope with no credit."""
    def calc(rs):
        inscope = [r for r in rs if r["applicable"] is not False]
        credit = sum(cfg["status_credit"].get(r["state"], 0.0) for r in inscope)
        return {"controls": len(rs), "in_scope": len(inscope),
                "excluded": sum(1 for r in rs if r["applicable"] is False),
                "not_assessed": sum(1 for r in rs if r["state"] == "not_assessed"),
                "implemented": sum(1 for r in inscope if r["state"] == "implemented"),
                "partial": sum(1 for r in inscope if r["state"] == "partial"),
                "score": round(100 * credit / len(inscope), 1) if inscope else None}
    out = {"overall": calc(rows), "themes": {}}
    for t in THEMES.values():
        out["themes"][t] = calc([r for r in rows if r["theme"] == t])
    return out


GAP_RANK = {"not_implemented": 0, "planned": 1, "partial": 2}


def gaps(rows):
    g = [r for r in rows if r["applicable"] and r["state"] in GAP_RANK]
    return sorted(g, key=lambda r: (GAP_RANK[r["state"]], [int(x) for x in r["id"].split(".")]))


def _ids(ids, cfg):
    n = cfg["max_ids_listed"]
    s = ", ".join(ids[:n])
    return s + (f" and {len(ids) - n} more" if len(ids) > n else "")


def check_controls(rows, cfg, as_of):
    out = []
    na = [r["id"] for r in rows if r["state"] == "not_assessed"]
    if na:
        out.append(Issue("controls", "NOT_ASSESSED", "medium", "SoA",
                         f"{len(na)} Annex A controls have not been assessed",
                         f"Statement of Applicability is incomplete: {_ids(na, cfg)}.",
                         "Decide applicability and status for each control, with a justification for any exclusion."))
    for r in rows:
        if r["applicable"] is False and not r["justification"].strip():
            out.append(Issue("controls", "EXCLUDED_NO_JUSTIFICATION", "high", r["id"],
                             f"Control {r['id']} excluded without justification",
                             f"{r['title']} is marked not applicable with no reason recorded.",
                             "Record why the control is not applicable; auditors will ask."))
        if r["applicable"] and r["state"] in ("implemented", "partial") and not r["evidence"].strip():
            out.append(Issue("controls", "NO_EVIDENCE", "medium", r["id"],
                             f"Control {r['id']} is {r['state']} but has no evidence reference",
                             r["title"], "Link the policy, record or screenshot that proves it."))
        if r["applicable"] and r["state"] in ("implemented", "partial") and r["last_reviewed"]:
            limit = add_months(pdate(r["last_reviewed"]), cfg["evidence_max_age_months"])
            if as_of > limit:
                out.append(Issue("controls", "EVIDENCE_STALE", "medium", r["id"],
                                 f"Control {r['id']} not reviewed in over {cfg['evidence_max_age_months']} months",
                                 f"{r['title']}: last reviewed {r['last_reviewed']}.",
                                 "Re-review the control and refresh the evidence."))
    noown = [r["id"] for r in rows if r["applicable"] and r["state"] != "not_assessed" and not r["owner"].strip()]
    if noown:
        out.append(Issue("controls", "NO_OWNER", "low", "SoA", f"{len(noown)} in-scope controls have no owner",
                         _ids(noown, cfg) + ".", "Assign an accountable owner to each control."))
    return out


# ---------------------------------------------------------------- risks

def score(l, i):
    return int(l) * int(i)


def rating(s, cfg):
    t = cfg["risk_rating"]
    return "critical" if s >= t["critical"] else "high" if s >= t["high"] else "medium" if s >= t["medium"] else "low"


def risk_rows(org, cfg):
    out = []
    for r in org.get("risks", []):
        inh = score(r["likelihood"], r["impact"])
        res = score(r.get("residual_likelihood", r["likelihood"]), r.get("residual_impact", r["impact"]))
        out.append({**r, "inherent": inh, "residual": res,
                    "inherent_rating": rating(inh, cfg), "residual_rating": rating(res, cfg)})
    return sorted(out, key=lambda x: (-x["residual"], x["id"]))


def check_risks(risks, rows, cfg, as_of):
    by_id = {r["id"]: r for r in rows}
    out = []
    for r in risks:
        opt = r.get("treatment_option", "none")
        rt = r["residual_rating"]
        taking_credit = r["residual"] < r["inherent"]
        for cid in r.get("controls", []):
            c = by_id.get(cid)
            if c is None:
                out.append(Issue("risks", "RISK_UNKNOWN_CONTROL", "medium", r["id"],
                                 f"Risk {r['id']} cites unknown control {cid}", r["title"],
                                 "Correct the control reference."))
            elif taking_credit and c["state"] != "implemented":
                sev = "medium" if c["state"] == "partial" else "high"
                out.append(Issue("risks", "RISK_RELIES_ON_GAP", sev, r["id"],
                                 f"Risk {r['id']} lowered by control {cid} which is {c['state'].replace('_', ' ')}",
                                 f"{r['title']}: residual {r['residual']} < inherent {r['inherent']}, but {cid} ({c['title']}) is not fully implemented.",
                                 "Either finish the control or restore the risk score until it is in place."))
        if rt in ("high", "critical") and opt == "none":
            out.append(Issue("risks", "RISK_UNTREATED", rt if rt == "critical" else "high", r["id"],
                             f"{rt.capitalize()} risk {r['id']} has no treatment decision",
                             f"{r['title']} (residual {r['residual']}).",
                             "Choose to mitigate, transfer, avoid or formally accept, with an owner and date."))
        if opt == "accept":
            if not r.get("approved_by"):
                out.append(Issue("risks", "RISK_ACCEPT_NO_APPROVAL", "high", r["id"],
                                 f"Risk {r['id']} accepted without recorded approval", r["title"],
                                 "Obtain and record sign-off from the risk owner / management."))
            if rt == "critical":
                out.append(Issue("risks", "CRITICAL_RISK_ACCEPTED", "high", r["id"],
                                 f"Critical risk {r['id']} is being accepted",
                                 f"{r['title']} (residual {r['residual']}).", "Confirm top management has explicitly agreed."))
            rd = pdate(r.get("review_date"))
            if rd and rd < as_of:
                out.append(Issue("risks", "RISK_ACCEPT_REVIEW_OVERDUE", "medium", r["id"],
                                 f"Accepted risk {r['id']} is past its review date",
                                 f"Review was due {rd}.", "Re-confirm the acceptance or choose a treatment."))
        due = pdate(r.get("treatment_due"))
        if opt in ("mitigate", "transfer", "avoid") and r.get("treatment_status") != "complete" and due and due < as_of:
            out.append(Issue("risks", "TREATMENT_OVERDUE", "high" if rt in ("high", "critical") else "medium", r["id"],
                             f"Treatment for risk {r['id']} is overdue",
                             f"{r['title']}: due {due} ({(as_of - due).days} days late), owner {r.get('treatment_owner') or 'unassigned'}.",
                             "Re-baseline the date with the owner or escalate."))
    return out


# ---------------------------------------------------------------- audit & programme

def check_findings(org, cfg, as_of):
    out = []
    sev = {"major_nc": "high", "minor_nc": "medium", "observation": "low", "ofi": "low"}
    for f in org.get("audit_findings", []):
        if f.get("control") and f["control"] not in CONTROLS:
            out.append(Issue("audit", "FINDING_UNKNOWN_CONTROL", "low", f["id"],
                             f"Finding {f['id']} cites unknown control {f['control']}", f.get("title", ""), "Correct the reference."))
        due, closed = pdate(f.get("due")), pdate(f.get("closed"))
        if closed is None and due and due < as_of:
            out.append(Issue("audit", "FINDING_OVERDUE", sev[f["type"]], f["id"],
                             f"Open {f['type'].replace('_', ' ')} {f['id']} is past its due date",
                             f"{f.get('title', '')}. Due {due} ({(as_of - due).days} days late), owner {f.get('owner') or 'unassigned'}.",
                             "Agree a dated corrective action and verify closure."))
    return out


def _stale(dates, months, as_of):
    ds = [pdate(d) for d in dates if d]
    return (not ds) or as_of > add_months(max(ds), months), (max(ds) if ds else None)


def check_programme(org, cfg, as_of):
    out = []
    bad, last = _stale([a.get("date") for a in org.get("audit_programme", [])], cfg["internal_audit_max_age_months"], as_of)
    if bad:
        out.append(Issue("programme", "INTERNAL_AUDIT_OVERDUE", "high", "Cl. 9.2",
                         "No internal audit in the last 12 months",
                         f"Last internal audit: {last or 'none recorded'}.",
                         "Plan and complete an internal audit covering the ISMS scope."))
    bad, last = _stale([m.get("date") for m in org.get("management_reviews", [])], cfg["management_review_max_age_months"], as_of)
    if bad:
        out.append(Issue("programme", "MGMT_REVIEW_OVERDUE", "medium", "Cl. 9.3",
                         "No management review in the last 12 months",
                         f"Last management review: {last or 'none recorded'}.",
                         "Hold a management review and minute the inputs and decisions."))
    bad, last = _stale([org.get("last_risk_assessment")], cfg["risk_assessment_max_age_months"], as_of)
    if bad:
        out.append(Issue("programme", "RISK_ASSESSMENT_STALE", "medium", "Cl. 6.1.2",
                         "Risk assessment not refreshed in the last 12 months",
                         f"Last risk assessment: {last or 'none recorded'}.", "Re-run the risk assessment."))
    return out


def analyse(org, cfg, as_of):
    rows = control_rows(org)
    risks = risk_rows(org, cfg)
    issues = (check_controls(rows, cfg, as_of) + check_risks(risks, rows, cfg, as_of)
              + check_findings(org, cfg, as_of) + check_programme(org, cfg, as_of))
    issues.sort(key=lambda i: (SEV_ORDER[i.severity], i.area, i.ref, i.check))
    return {"rows": rows, "readiness": readiness(rows, cfg), "gaps": gaps(rows),
            "risks": risks, "issues": issues}
