"""python -m cap_audit.cli EXPORT [--as-of YYYY-MM-DD]"""

from __future__ import annotations

import argparse
import sys
from datetime import date, datetime

from .model import ExportError, load_export
from .rules import exit_code, run_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="capacity-reservation-audit",
        description="Audit an offline export of OCI Compute capacity reservations for idle-cost and hygiene gaps.",
    )
    p.add_argument("export", help="path to the JSON export")
    p.add_argument("--as-of", default=None, help="reference date YYYY-MM-DD (default: today, UTC)")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    if args.as_of:
        try:
            as_of = datetime.strptime(args.as_of, "%Y-%m-%d").date()
        except ValueError:
            print(f"error: --as-of {args.as_of!r} is not YYYY-MM-DD", file=sys.stderr)
            return 2
    else:
        as_of = date.today()
    try:
        reservations = load_export(args.export)
    except ExportError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = run_all(reservations, as_of)
    total_reserved = sum(r.reserved for r in reservations)
    total_used = sum(r.used for r in reservations)
    print(
        f"Capacity reservation audit as of {as_of.isoformat()} - {len(reservations)} reservation(s), "
        f"{total_used}/{total_reserved} instance(s) placed, {len(findings)} finding(s)"
    )
    for x in findings:
        print(f"[{x.severity:6s}] {x.rule} reservation={x.reservation}")
        print(f"         {x.detail}")
    code = exit_code(findings)
    print({0: "RESULT: clean", 1: "RESULT: warnings only", 2: "RESULT: HIGH findings present"}[code])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
