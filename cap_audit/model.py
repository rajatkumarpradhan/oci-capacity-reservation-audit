"""Data model + export loading for the capacity reservation audit."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional


class ExportError(ValueError):
    """Raised when an export file is malformed."""


LOW_UTILIZATION = 0.5


def parse_date(value: str, what: str) -> date:
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except (TypeError, ValueError) as exc:
        raise ExportError(f"invalid date for {what}: {value!r} (expected YYYY-MM-DD)") from exc


@dataclass(frozen=True)
class Reservation:
    name: str
    state: str          # e.g. ACTIVE
    reserved: int       # instances of capacity reserved
    used: int           # instances currently placed against the reservation
    ends_at: Optional[date] = None
    description: str = ""
    tags: tuple = ()    # freeform tag keys recorded

    def utilization(self) -> float:
        if self.reserved <= 0:
            return 0.0
        return self.used / self.reserved


def load_export(path: str) -> tuple:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise ExportError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("reservations"), list):
        raise ExportError(f"{path}: top level must be an object with a 'reservations' list")
    out = []
    for i, r in enumerate(raw["reservations"]):
        where = f"reservations[{i}]"
        for req in ("name", "state", "reserved", "used"):
            if req not in r:
                raise ExportError(f"{where}: missing required field {req!r}")
        if not isinstance(r["reserved"], int) or not isinstance(r["used"], int):
            raise ExportError(f"{where}: 'reserved' and 'used' must be integers")
        if r["used"] < 0 or r["reserved"] < 0:
            raise ExportError(f"{where}: counts must be non-negative")
        if r["used"] > r["reserved"]:
            raise ExportError(f"{where}: used ({r['used']}) exceeds reserved ({r['reserved']})")
        ends = r.get("ends_at")
        out.append(Reservation(
            name=r["name"],
            state=r["state"].upper(),
            reserved=r["reserved"],
            used=r["used"],
            ends_at=parse_date(ends, f"{where}.ends_at") if ends else None,
            description=r.get("description", "") or "",
            tags=tuple(r.get("tags", [])),
        ))
    return tuple(out)
