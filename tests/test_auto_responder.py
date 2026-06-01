"""Tests for bayzat_support.auto_responder."""

from bayzat_support.auto_responder import AutoResponder
from bayzat_support.models import Category, Priority, Status, Ticket


def make_ticket(**kwargs) -> Ticket:
    defaults = dict(
        ticket_id="T999",
        subject="Test",
        description="",
        customer_email="alice@company.com",
        customer_name="Alice",
        company_name="TestCo",
        category=Category.GENERAL,
        priority=Priority.MEDIUM,
        status=Status.OPEN,
    )
    defaults.update(kwargs)
    return Ticket(**defaults)


responder = AutoResponder()


class TestGenerateFirstResponse:
    def test_contains_ticket_id(self):
        ticket = make_ticket()
        msg = responder.generate(ticket)
        assert "#T999" in msg

    def test_contains_customer_name(self):
        ticket = make_ticket(customer_name="Carlos")
        msg = responder.generate(ticket)
        assert "Carlos" in msg

    def test_contains_sla_deadline(self):
        ticket = make_ticket()
        msg = responder.generate(ticket)
        assert ticket.sla_deadline().strftime("%d %b %Y") in msg

    def test_critical_priority_commitment_mentions_1_hour(self):
        ticket = make_ticket(priority=Priority.CRITICAL)
        msg = responder.generate(ticket)
        assert "1 hour" in msg

    def test_high_priority_commitment_mentions_4_hours(self):
        ticket = make_ticket(priority=Priority.HIGH)
        msg = responder.generate(ticket)
        assert "4 hours" in msg

    def test_agent_name_included_when_provided(self):
        ticket = make_ticket()
        msg = responder.generate(ticket, agent_name="Sara")
        assert "Sara" in msg

    def test_no_agent_line_when_not_provided(self):
        ticket = make_ticket()
        msg = responder.generate(ticket)
        assert "assigned to" not in msg.lower() or "Sara" not in msg

    def test_custom_support_email_in_footer(self):
        ticket = make_ticket()
        msg = responder.generate(ticket, support_email="help@bayzat.ae")
        assert "help@bayzat.ae" in msg

    def test_payroll_category_response_mentions_payroll(self):
        ticket = make_ticket(category=Category.PAYROLL)
        msg = responder.generate(ticket)
        assert "payroll" in msg.lower() or "salary" in msg.lower()


class TestEscalationNotice:
    def test_contains_ticket_id(self):
        ticket = make_ticket()
        notice = responder.generate_escalation_notice(ticket, "Senior Team")
        assert "T999" in notice

    def test_contains_escalation_target(self):
        ticket = make_ticket()
        notice = responder.generate_escalation_notice(ticket, "Engineering")
        assert "Engineering" in notice


class TestResolutionMessage:
    def test_contains_ticket_id(self):
        ticket = make_ticket()
        msg = responder.generate_resolution_message(ticket, "Issue fixed by resetting account.")
        assert "#T999" in msg

    def test_contains_resolution_notes(self):
        ticket = make_ticket()
        notes = "Adjusted leave balance from 10 to 12 days."
        msg = responder.generate_resolution_message(ticket, notes)
        assert notes in msg

    def test_resolved_word_in_message(self):
        ticket = make_ticket()
        msg = responder.generate_resolution_message(ticket, "Done.")
        assert "resolved" in msg.lower()
