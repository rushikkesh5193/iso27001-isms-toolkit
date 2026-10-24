"""Markdown, JSON and Statement of Applicability (CSV) output."""
from __future__ import annotations

import csv
import io
import json

SEVS = ("critical", "high", "medium", "low")


def soa_csv(rows):
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    w.writerow(["Control", "Title", "Theme", "New in 2022", "Applicable", "Justification",
                "Implementation status", "Owner", "Evidence", "Last reviewed"])
    for r in rows:
        app = {True: "Yes", False: "No", None: "Not assessed"}[r["applicable"]]
        status = r["state"] if r["applicable"] else ("n/a" if r["applicable"] is False else "not assessed")
        w.writerow([r["id"], r["title"], r["theme"], "Yes" if r["new_in_2022"] else "",
                    app, r["justification"], status, r["owner"], r["evidence"], r["last_reviewed"]])
    return buf.getvalue()


def heat_map(risks):
    grid = {(l, i): 0 for l in range(1, 6) for i in range(1, 6)}
    for r in risks:
        grid[(int(r.get("residual_likelihood", r["likelihood"])), int(r.get("residual_impact", r["impact"])))] += 1
    lines = ["| Impact \\ Likelihood | 1 | 2 | 3 | 4 | 5 |", "|---|---|---|---|---|---|"]
    for i in range(5, 0, -1):
        lines.append(f"| **{i}** | " + " | ".join(str(grid[(l, i)] or "·") for l in range(1, 6)) + " |")
    return "\n".join(lines)


def to_markdown(res, org, as_of):
    rd, issues = res["readiness"], res["issues"]
    o = rd["overall"]
    sev = {s: sum(1 for i in issues if i.severity == s) for s in SEVS}
    L = [f"# ISMS Readiness Report: {org.get('organisation', 'Organisation')}", "",
         f"As of **{as_of}**. Based on ISO/IEC 27001:2022 Annex A (93 controls). Data is synthetic unless you supplied your own.", "",
         "## Summary", "",
         f"- Readiness score: **{o['score']}%** ({o['implemented']} implemented, {o['partial']} partial of {o['in_scope']} in-scope controls)",
         f"- Excluded as not applicable: {o['excluded']}. Not yet assessed: {o['not_assessed']}",
         f"- Open issues: {sev['critical']} critical, {sev['high']} high, {sev['medium']} medium, {sev['low']} low",
         f"- Risks on register: {len(res['risks'])}. Control gaps to close: {len(res['gaps'])}", "",
         "### Readiness by theme", "",
         "| Theme | Controls | In scope | Implemented | Partial | Not assessed | Score |", "|---|---|---|---|---|---|---|"]
    for t, v in rd["themes"].items():
        L.append(f"| {t} | {v['controls']} | {v['in_scope']} | {v['implemented']} | {v['partial']} | {v['not_assessed']} | {v['score']}% |")
    L += ["", "## Issues needing action", ""]
    if not issues:
        L += ["No issues found.", ""]
    for s in SEVS:
        g = [i for i in issues if i.severity == s]
        if g:
            L += [f"### {s.capitalize()} ({len(g)})", "", "| Area | Ref | Check | Detail | Action |", "|---|---|---|---|---|"]
            L += [f"| {i.area} | {i.ref} | {i.check} | {i.title}. {i.detail} | {i.action} |" for i in g]
            L.append("")
    L += ["## Control gaps (in scope, not fully implemented)", "",
          "| Control | Title | Status | Owner |", "|---|---|---|---|"]
    L += [f"| {g['id']} | {g['title']} | {g['state'].replace('_', ' ')} | {g['owner'] or '-'} |" for g in res["gaps"]]
    L += ["", "## Risk register (highest residual first)", "",
          "| ID | Risk | Inherent | Residual | Rating | Treatment | Owner |", "|---|---|---|---|---|---|---|"]
    L += [f"| {r['id']} | {r['title']} | {r['inherent']} | {r['residual']} | {r['residual_rating']} | "
          f"{r.get('treatment_option', 'none')} | {r.get('treatment_owner') or '-'} |" for r in res["risks"]]
    L += ["", "### Residual risk heat map (count of risks)", "", heat_map(res["risks"]), "",
          "Scores are likelihood x impact (1-25). Ratings: low <6, medium 6-11, high 12-19, critical 20+ (editable in config.json).", ""]
    return "\n".join(L)


def to_json(res, org, as_of):
    return json.dumps({"as_of": str(as_of), "organisation": org.get("organisation"),
                       "readiness": res["readiness"], "issues": [i.as_dict() for i in res["issues"]],
                       "gaps": [g["id"] for g in res["gaps"]], "risks": res["risks"]}, indent=2, default=str)
