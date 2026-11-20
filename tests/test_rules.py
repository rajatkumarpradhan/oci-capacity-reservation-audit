import unittest
from datetime import date, timedelta

from cap_audit.model import Reservation
from cap_audit.rules import (
    exit_code,
    rule_fully_unused,
    rule_low_utilization,
    rule_stale_record,
    rule_unlabeled,
    run_all,
)

AS_OF = date(2026, 11, 21)


def res(name="r", state="ACTIVE", reserved=4, used=4, ends_at=None, description="desc", tags=("owner:x",)):
    return Reservation(name=name, state=state, reserved=reserved, used=used,
                       ends_at=ends_at, description=description, tags=tuple(tags))


class TestCapr001(unittest.TestCase):
    def test_fires_zero_used(self):
        out = rule_fully_unused((res(used=0),), AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")

    def test_quiet_non_active(self):
        self.assertEqual(rule_fully_unused((res(state="DELETED", used=0),), AS_OF), [])

    def test_quiet_partially_used(self):
        self.assertEqual(rule_fully_unused((res(used=1),), AS_OF), [])


class TestCapr002(unittest.TestCase):
    def test_fires_below_half(self):
        out = rule_low_utilization((res(reserved=10, used=4),), AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "MEDIUM")

    def test_boundary_half_quiet(self):
        self.assertEqual(rule_low_utilization((res(reserved=10, used=5),), AS_OF), [])

    def test_zero_used_handled_by_capr001_only(self):
        self.assertEqual(rule_low_utilization((res(used=0),), AS_OF), [])


class TestCapr003(unittest.TestCase):
    def test_fires_past_end(self):
        out = rule_stale_record((res(ends_at=AS_OF - timedelta(days=1)),), AS_OF)
        self.assertEqual(len(out), 1)

    def test_quiet_today(self):
        self.assertEqual(rule_stale_record((res(ends_at=AS_OF),), AS_OF), [])

    def test_quiet_no_end(self):
        self.assertEqual(rule_stale_record((res(),), AS_OF), [])


class TestCapr004(unittest.TestCase):
    def test_fires_both_missing(self):
        out = rule_unlabeled((res(description="  ", tags=()),), AS_OF)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "LOW")

    def test_quiet_description_only(self):
        self.assertEqual(rule_unlabeled((res(tags=()),), AS_OF), [])

    def test_quiet_tags_only(self):
        self.assertEqual(rule_unlabeled((res(description=""),), AS_OF), [])


class TestAggregation(unittest.TestCase):
    def test_exit_2_on_high(self):
        self.assertEqual(exit_code(run_all((res(used=0),), AS_OF)), 2)

    def test_exit_1_medium_only(self):
        self.assertEqual(exit_code(run_all((res(reserved=10, used=2),), AS_OF)), 1)

    def test_exit_0_clean(self):
        self.assertEqual(exit_code(run_all((res(),), AS_OF)), 0)


if __name__ == "__main__":
    unittest.main()
