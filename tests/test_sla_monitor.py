"""Tests for bayzat_support.sla_monitor."""

from datetime import datetime, timedelta

import pytest

from bayzat_support.models import Category, Priority, Status, Ticket
from bayzat_support.sla_monitor import SLAMonitor


def make_ticket(priority=Priority.HIGH, status=Status.OPEN, created_at=None) -> Ticket:
    return Ticket(
        ticket_id="T001",
        subject="Test",
        description="",
        customer_email="x@x.com",
        customer_name="X",
        company_name="X Corp",
        priority=priority,
        status=status,
        created_at=created_at or datetime(2024, 1, 1, 9, 0, 0),
    )


class TestEvaluate:
    def test_healthy_ticket(self):
        monitor = SLAMonitor()
        ticket = make_ticket(priority=Priority.HIGH)  # 4-hour SLA
        # 1 hour after creation → 3 hours remaining → healthy
        ref = ticket.created_at + timedelta(hours=1)
        statuses = monitor.evaluate([ticket], reference_time=ref)
        assert len(statuses) == 1
        s = statuses[0]
        assert not s.is_breached
        assert not s.is_at_risk
        assert s.hours_remaining > 0

    def test_breached_ticket(self):
        monitor = SLAMonitor()
        ticket = make_ticket(priority=Priority.HIGH)  # 4-hour SLA
        # 5 hours after creation → breached
        ref = ticket.created_at + timedelta(hours=5)
        statuses = monitor.evaluate([ticket], reference_time=ref)
        s = statuses[0]
        assert s.is_breached
        assert s.hours_remaining < 0

    def test_at_risk_ticket(self):
        monitor = SLAMonitor(warning_threshold_pct=25)
        ticket = make_ticket(priority=Priority.HIGH)  # 4-hour SLA, warning at 1h
        # 3.5 hours after creation → 0.5 hours remaining < 1 hour warning → at risk
        ref = ticket.created_at + timedelta(hours=3, minutes=30)
        statuses = monitor.evaluate([ticket], reference_time=ref)
        s = statuses[0]
        assert not s.is_breached
        assert s.is_at_risk

    def test_resolved_ticket_not_breached(self):
        monitor = SLAMonitor()
        ticket = make_ticket(priority=Priority.CRITICAL, status=Status.RESOLVED)
        # Far past the deadline
        ref = ticket.created_at + timedelta(hours=100)
        statuses = monitor.evaluate([ticket], reference_time=ref)
        s = statuses[0]
        assert not s.is_breached
        assert not s.is_at_risk


class TestGetBreached:
    def test_returns_only_breached(self):
        monitor = SLAMonitor()
        base = datetime(2024, 1, 1, 9, 0, 0)
        healthy = make_ticket(priority=Priority.HIGH, created_at=base)
        healthy.ticket_id = "T_HEALTHY"
        breached = make_ticket(priority=Priority.CRITICAL, created_at=base)
        breached.ticket_id = "T_BREACHED"
        # Reference: 2 hours after base. HIGH (4h SLA) → healthy, CRITICAL (1h SLA) → breached
        ref = base + timedelta(hours=2)
        results = monitor.get_breached([healthy, breached], reference_time=ref)
        assert all(s.is_breached for s in results)
        ids = [s.ticket.ticket_id for s in results]
        assert breached.ticket_id in ids
        assert healthy.ticket_id not in ids


class TestSummary:
    def test_summary_keys(self):
        monitor = SLAMonitor()
        tickets = [make_ticket()]
        s = monitor.summary(tickets)
        assert "total" in s
        assert "healthy" in s
        assert "at_risk" in s
        assert "breached" in s
        assert "compliance_pct" in s

    def test_empty_summary(self):
        monitor = SLAMonitor()
        s = monitor.summary([])
        assert s["total"] == 0
        assert s["compliance_pct"] == 100.0

    def test_all_breached_gives_zero_compliance(self):
        monitor = SLAMonitor()
        ticket = make_ticket(priority=Priority.CRITICAL)
        # 10 hours after creation → well past 1-hour SLA
        ref = ticket.created_at + timedelta(hours=10)
        s = monitor.summary([ticket], reference_time=ref)
        assert s["breached"] == 1
        assert s["compliance_pct"] == 0.0


class TestInvalidWarningThreshold:
    def test_raises_on_zero(self):
        with pytest.raises(ValueError):
            SLAMonitor(warning_threshold_pct=0)

    def test_raises_on_100(self):
        with pytest.raises(ValueError):
            SLAMonitor(warning_threshold_pct=100)
