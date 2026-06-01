"""Tests for bayzat_support.models."""

from datetime import datetime, timedelta

import pytest

from bayzat_support.models import (
    Category,
    Priority,
    SLA_HOURS,
    Status,
    Ticket,
)


def make_ticket(**kwargs) -> Ticket:
    defaults = dict(
        ticket_id="T001",
        subject="Test subject",
        description="Test description",
        customer_email="user@example.com",
        customer_name="Alice Smith",
        company_name="Acme Corp",
    )
    defaults.update(kwargs)
    return Ticket(**defaults)


class TestSLADeadline:
    def test_deadline_computed_from_priority(self):
        for priority, hours in SLA_HOURS.items():
            ticket = make_ticket(ticket_id="TX", priority=priority)
            expected = ticket.created_at + timedelta(hours=hours)
            assert ticket.sla_deadline() == expected

    def test_critical_deadline_is_one_hour(self):
        ticket = make_ticket(priority=Priority.CRITICAL)
        delta = ticket.sla_deadline() - ticket.created_at
        assert delta == timedelta(hours=1)


class TestIsSLABreached:
    def test_not_breached_when_within_window(self):
        ticket = make_ticket(priority=Priority.HIGH)
        # Reference time = 1 hour after creation (SLA is 4 hours)
        ref = ticket.created_at + timedelta(hours=1)
        assert not ticket.is_sla_breached(ref)

    def test_breached_when_past_deadline(self):
        ticket = make_ticket(priority=Priority.HIGH)
        # Reference time = 5 hours after creation (SLA is 4 hours)
        ref = ticket.created_at + timedelta(hours=5)
        assert ticket.is_sla_breached(ref)

    def test_resolved_ticket_is_never_breached(self):
        ticket = make_ticket(priority=Priority.CRITICAL, status=Status.RESOLVED)
        # Even if far past the deadline it should not be breached
        ref = ticket.created_at + timedelta(hours=100)
        assert not ticket.is_sla_breached(ref)

    def test_closed_ticket_is_never_breached(self):
        ticket = make_ticket(priority=Priority.CRITICAL, status=Status.CLOSED)
        ref = ticket.created_at + timedelta(hours=100)
        assert not ticket.is_sla_breached(ref)


class TestToDict:
    def test_to_dict_contains_all_keys(self):
        ticket = make_ticket()
        d = ticket.to_dict()
        expected_keys = {
            "ticket_id", "subject", "description", "customer_email",
            "customer_name", "company_name", "created_at", "updated_at",
            "priority", "category", "status", "assigned_to",
            "resolution_notes", "tags",
        }
        assert expected_keys.issubset(d.keys())

    def test_to_dict_uses_enum_values(self):
        ticket = make_ticket(priority=Priority.HIGH, category=Category.PAYROLL)
        d = ticket.to_dict()
        assert d["priority"] == "high"
        assert d["category"] == "payroll"
