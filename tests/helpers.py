from datetime import date

from isms.core import load_config, analyse
from isms.annex_a import CONTROLS

AS_OF = date(2026, 10, 24)
CFG = load_config()


def ctl(**kw):
    d = {"applicable": True, "status": "implemented", "owner": "o", "evidence": "EV", "last_reviewed": "2026-09-01"}
    d.update(kw)
    return d


def org(controls=None, **kw):
    """A tiny clean ISMS: every control implemented, programme current, no risks or findings."""
    c = {cid: ctl() for cid in CONTROLS}
    c.update(controls or {})
    d = {"organisation": "T", "controls": c, "risks": [], "audit_findings": [],
         "audit_programme": [{"date": "2026-06-01"}], "management_reviews": [{"date": "2026-06-01"}],
         "last_risk_assessment": "2026-06-01"}
    d.update(kw)
    return d


def run(o):
    return analyse(o, CFG, AS_OF)


def checks(o):
    return {(i.check, i.ref) for i in run(o)["issues"]}


def risk(**kw):
    d = dict(id="R1", title="t", likelihood=3, impact=3, controls=[], treatment_option="none")
    d.update(kw)
    return d
