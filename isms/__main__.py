"""CLI: python3 -m isms org.json [--as-of YYYY-MM-DD] [--out-dir DIR] [--fail-on SEVERITY] [--config FILE]"""
from __future__ import annotations

import argparse
import sys
from datetime import date
from pathlib import Path

from .core import load_org, load_config, analyse, pdate, SEV_ORDER
from .report import to_markdown, to_json, soa_csv


def main(argv=None):
    ap = argparse.ArgumentParser(prog="isms", description="ISO 27001:2022 ISMS readiness, risk and audit checker")
    ap.add_argument("org", help="ISMS data file (JSON)")
    ap.add_argument("--as-of", help="evaluation date; default today")
    ap.add_argument("--config")
    ap.add_argument("--out-dir", help="write report.md, report.json and soa.csv here")
    ap.add_argument("--fail-on", choices=list(SEV_ORDER), help="exit 1 if any issue at this severity or worse")
    a = ap.parse_args(argv)
    if not Path(a.org).is_file():
        print(f"error: {a.org} not found", file=sys.stderr)
        return 2
    try:
        as_of = pdate(a.as_of, "--as-of") if a.as_of else date.today()
        cfg, org = load_config(a.config), load_org(a.org)
        res = analyse(org, cfg, as_of)
    except (ValueError, KeyError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    md = to_markdown(res, org, as_of)
    if a.out_dir:
        out = Path(a.out_dir)
        out.mkdir(parents=True, exist_ok=True)
        (out / "report.md").write_text(md, encoding="utf-8")
        (out / "report.json").write_text(to_json(res, org, as_of), encoding="utf-8")
        (out / "soa.csv").write_text(soa_csv(res["rows"]), encoding="utf-8")
        o = res["readiness"]["overall"]
        print(f"readiness {o['score']}%, {len(res['issues'])} issues -> {out}/report.md, report.json, soa.csv")
    else:
        print(md)
    return 1 if a.fail_on and any(SEV_ORDER[i.severity] <= SEV_ORDER[a.fail_on] for i in res["issues"]) else 0


if __name__ == "__main__":
    sys.exit(main())
