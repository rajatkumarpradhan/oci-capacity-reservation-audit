# oci-capacity-reservation-audit

**Category: custom portfolio tool.** The OOTB built-in-services project in this pair is
`oci-ootb-container-instance-check`.

## The problem

OCI Compute capacity reservations start billing the moment they are created: per the OCI
docs, **unused reserved capacity is billed at 85% of the regular rate** until the
reservation is deleted. A reservation made for a migration weekend or a seasonal peak is
easy to forget, and nothing in the platform taps you on the shoulder when one sits fully
idle. This tool audits an offline JSON export of reservations and flags the gaps worth a
human review.

## The rules

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| CAPR001 | HIGH | An ACTIVE reservation has **zero** instances placed against it - every OCPU recorded is unused, and unused capacity bills at 85% (per OCI docs). Review flag: delete it if the need has passed. |
| CAPR002 | MEDIUM | Utilization (`used / reserved`) is below 50% - most of the recorded capacity is paying the unused rate. |
| CAPR003 | MEDIUM | The reservation's recorded `ends_at` is in the past as of the audit date - a stale record in the export. |
| CAPR004 | LOW | No description and no freeform tags recorded - an unlabeled reservation is hard to trace to an owner or purpose. |

Exit code: `2` on any HIGH, `1` on MEDIUM/LOW only, `0` when clean.

## Run it

```bash
python -m cap_audit.cli samples/reservations_messy.json --as-of 2026-11-21   # exits 2, all 4 rules fire
python -m cap_audit.cli samples/reservations_clean.json --as-of 2026-11-21   # exits 0
python -m unittest discover -s tests -v                                      # 18 tests, stdlib only
```

`--as-of` fixes the reference date so date math is reproducible; omit it for today (UTC).

## Honest limits

- **Offline audit**: the JSON export is synthetic; nothing calls the OCI API.
- Findings describe what the export records. CAPR001/CAPR002 are review prompts about
  recorded utilization, not proof of wasted spend - burst/DR reservations are idle by
  design. The 85% unused rate and billing semantics are from the OCI capacity reservation
  docs as of Nov 2026; verify current pricing before acting on a finding.
- The 50% utilization threshold (CAPR002) is a default, not OCI policy.
- No live tenancy was touched.

## Project status

Built as a daily portfolio project. 18 unit tests, green locally and in CI. Free tier only;
no live cloud calls, no spend.
