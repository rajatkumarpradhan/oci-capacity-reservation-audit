"""CAPR001-CAPR004 rules."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .model import LOW_UTILIZATION


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    reservation: str
    detail: str


def rule_fully_unused(reservations: tuple, as_of: date) -> list:
    """CAPR001 HIGH: ACTIVE reservation with zero instances placed."""
    del as_of
    return [
        Finding("CAPR001", "HIGH", r.name,
                f"ACTIVE reservation with {r.reserved} instance(s) reserved and 0 placed; per OCI docs "
                f"unused reserved capacity bills at 85% of the regular rate - review whether it is still needed")
        for r in reservations if r.state == "ACTIVE" and r.used == 0 and r.reserved > 0
    ]


def rule_low_utilization(reservations: tuple, as_of: date) -> list:
    """CAPR002 MEDIUM: utilization below LOW_UTILIZATION (and not fully unused)."""
    del as_of
    out = []
    for r in reservations:
        if r.state == "ACTIVE" and r.reserved > 0 and 0 < r.used and r.utilization() < LOW_UTILIZATION:
            out.append(
                Finding("CAPR002", "MEDIUM", r.name,
                        f"utilization {r.used}/{r.reserved} = {r.utilization():.0%} is below "
                        f"{LOW_UTILIZATION:.0%}; most recorded capacity pays the unused rate")
            )
    return out


def rule_stale_record(reservations: tuple, as_of: date) -> list:
    """CAPR003 MEDIUM: ends_at in the past but the reservation is still listed."""
    return [
        Finding("CAPR003", "MEDIUM", r.name,
                f"recorded ends_at {r.ends_at.isoformat()} is in the past as of {as_of.isoformat()}; "
                f"stale record in this export - confirm the reservation still exists")
        for r in reservations if r.ends_at is not None and r.ends_at < as_of
    ]


def rule_unlabeled(reservations: tuple, as_of: date) -> list:
    """CAPR004 LOW: no description and no freeform tags recorded."""
    del as_of
    return [
        Finding("CAPR004", "LOW", r.name,
                "no description and no freeform tags recorded; an unlabeled reservation is hard to "
                "trace to an owner or purpose")
        for r in reservations if not r.description.strip() and not r.tags
    ]


ALL_RULES = (
    rule_fully_unused,
    rule_low_utilization,
    rule_stale_record,
    rule_unlabeled,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(reservations: tuple, as_of: date) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(reservations, as_of))
    findings.sort(key=lambda x: (_SEVERITY_RANK[x.severity], x.rule, x.reservation))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
