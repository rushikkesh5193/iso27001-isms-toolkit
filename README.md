# iso27001-isms-toolkit

A small Python tool for the day-to-day work of running an **ISO/IEC 27001:2022** information security management system (ISMS): tracking control implementation, keeping a risk register honest, managing internal audit findings and checking that the management-system routines are actually happening.

Python standard library only (tested on 3.13).

> **Data note.** `examples/sample_org.json` is **synthetic**, for a fictional company ("ExampleOrg Pvt Ltd"). It has 19 problems injected on purpose so the tests can check the tool finds exactly those. Nothing here comes from a real organisation.

## What it does

You give it one JSON file describing your ISMS. It returns:

- **Readiness score** across all 93 Annex A controls, overall and by theme (Organizational, People, Physical, Technological).
- **Statement of Applicability** (`soa.csv`): one row per control with applicability, justification, status, owner and evidence.
- **Gap list**: in-scope controls not fully implemented, worst first.
- **Risk register** with likelihood x impact scoring, a residual-risk heat map, and treatment tracking.
- **Ranked issues**: what an internal auditor would likely raise, and what to do about it.

```bash
python3 -m isms examples/sample_org.json --as-of 2026-10-24                 # report to terminal
python3 -m isms examples/sample_org.json --out-dir out                       # report.md, report.json, soa.csv
python3 -m isms examples/sample_org.json --fail-on high                      # exit 1 on high/critical (CI / cron)
python3 -m unittest discover -s tests                                        # 38 tests
bash scripts/run_demo.sh                                                     # regenerate everything
```

## The checks

| Area | Check | Raised when |
|---|---|---|
| Controls | `NOT_ASSESSED` | Annex A controls with no applicability/status decision (counted as in scope with no credit) |
| | `EXCLUDED_NO_JUSTIFICATION` | A control is marked not applicable with no reason recorded |
| | `NO_EVIDENCE` | Control is implemented or partial but no evidence reference |
| | `EVIDENCE_STALE` | Control not reviewed in 12 months |
| | `NO_OWNER` | In-scope controls with no accountable owner |
| Risks | `RISK_RELIES_ON_GAP` | Residual risk is lowered because of a control that is not actually implemented |
| | `RISK_UNTREATED` | High or critical residual risk with no treatment decision |
| | `RISK_ACCEPT_NO_APPROVAL` / `CRITICAL_RISK_ACCEPTED` / `RISK_ACCEPT_REVIEW_OVERDUE` | Risk acceptance not signed off, a critical risk accepted, or the acceptance past its review date |
| | `TREATMENT_OVERDUE` | Treatment plan past its due date and not complete |
| | `RISK_UNKNOWN_CONTROL` | Risk cites a control ID that does not exist |
| Audit | `FINDING_OVERDUE` | Open finding past due: major non-conformity high, minor medium, observation or improvement low |
| | `FINDING_UNKNOWN_CONTROL` | Finding cites a control ID that does not exist |
| Programme | `INTERNAL_AUDIT_OVERDUE` | No internal audit in 12 months (clause 9.2) |
| | `MGMT_REVIEW_OVERDUE` | No management review in 12 months (clause 9.3) |
| | `RISK_ASSESSMENT_STALE` | Risk assessment not refreshed in 12 months (clause 6.1.2) |

The 12-month windows and risk rating bands (low below 6, medium 6-11, high 12-19, critical 20 and above) are defaults in `isms/config.json`. They are my defaults, not requirements of the standard, so adjust them to your own risk methodology.

## Input format

See `examples/sample_org.json`. Top-level keys: `organisation`, `last_risk_assessment`, `audit_programme`, `management_reviews`, `controls` (keyed by Annex A ID), `risks` and `audit_findings`. Unknown control IDs, invalid statuses, scores outside 1-5, duplicate risk IDs and malformed dates are rejected with a clear message (exit code 2).

## Tests

38 tests cover the Annex A reference (93 controls; 37/8/14/34 per theme; the 11 controls new in 2022), readiness maths, every check on both sides of its boundary, input validation and an end-to-end run that must find **exactly** the injected problems. I also broke the code five ways (a flipped boundary, always taking credit for controls, ignoring high risks, using the oldest audit instead of the latest, and dropping unassessed controls from scope) and confirmed the tests fail each time.

## Limitations

- **It checks records, not reality.** It can tell you a control is marked implemented with no evidence, not whether the control works.
- **Control titles only.** `annex_a.py` holds control numbers and short titles, not the standard's text. Check them against your licensed copy of ISO/IEC 27001:2022.
- **Simple risk model.** Likelihood x impact on a 1-5 scale. Your methodology may weight things differently.
- **Not certification advice.** A clean report does not mean you would pass a certification audit.
- **No UI or persistence.** JSON in, reports out.

## Layout

```
isms/        annex_a.py  core.py  report.py  config.json  __main__.py
tools/       gen_org.py              synthetic data generator
tests/       38 tests
examples/    sample_org.json  report.md  report.json  soa.csv
scripts/     run_demo.sh
```
