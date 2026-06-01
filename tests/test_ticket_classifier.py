"""Tests for bayzat_support.ticket_classifier."""

import pytest

from bayzat_support.models import Category, Priority, Ticket
from bayzat_support.ticket_classifier import TicketClassifier


def make_ticket(subject: str, description: str = "") -> Ticket:
    return Ticket(
        ticket_id="T001",
        subject=subject,
        description=description,
        customer_email="user@example.com",
        customer_name="Bob Jones",
        company_name="Beta Ltd",
    )


classifier = TicketClassifier()


class TestCategoryDetection:
    @pytest.mark.parametrize(
        "subject, expected_category",
        [
            ("My payslip is missing for this month", Category.PAYROLL),
            ("Leave balance looks wrong", Category.LEAVE),
            ("Employee cannot check in via the app", Category.ATTENDANCE),
            ("New hire account setup needed", Category.ONBOARDING),
            ("Resignation and offboarding process", Category.OFFBOARDING),
            ("Insurance enrolment issue", Category.BENEFITS),
            ("KPI appraisal not visible", Category.PERFORMANCE),
            ("NOC letter not generating", Category.DOCUMENTS),
            ("Login password reset request", Category.ACCESS),
            ("Webhook not firing for integration", Category.INTEGRATION),
            ("Random general question", Category.GENERAL),
        ],
    )
    def test_category(self, subject, expected_category):
        ticket = make_ticket(subject)
        classified = classifier.classify(ticket)
        assert classified.category == expected_category, (
            f"Expected {expected_category} for '{subject}', "
            f"got {classified.category}"
        )


class TestPriorityDetection:
    def test_critical_keyword_overrides_default(self):
        ticket = make_ticket("URGENT – system down, all employees cannot login")
        classified = classifier.classify(ticket)
        assert classified.priority == Priority.CRITICAL

    def test_high_keyword_sets_high_priority(self):
        ticket = make_ticket("Payroll processing deadline is today – blocking issue")
        classified = classifier.classify(ticket)
        assert classified.priority == Priority.HIGH

    def test_low_keyword_sets_low_priority(self):
        ticket = make_ticket("Minor question about how to download a report")
        classified = classifier.classify(ticket)
        assert classified.priority == Priority.LOW

    def test_payroll_category_defaults_to_high(self):
        ticket = make_ticket("WPS salary transfer not working")
        classified = classifier.classify(ticket)
        # No explicit priority keyword → should default to HIGH due to category
        assert classified.priority == Priority.HIGH

    def test_access_category_defaults_to_high(self):
        ticket = make_ticket("User account login password reset")
        classified = classifier.classify(ticket)
        assert classified.priority == Priority.HIGH

    def test_general_category_defaults_to_medium(self):
        ticket = make_ticket("Some unrelated topic with no priority signal")
        classified = classifier.classify(ticket)
        assert classified.priority == Priority.MEDIUM


class TestBulkClassify:
    def test_bulk_classify_returns_same_count(self):
        tickets = [make_ticket(f"Subject {i}") for i in range(5)]
        results = classifier.bulk_classify(tickets)
        assert len(results) == 5

    def test_bulk_classify_modifies_in_place(self):
        ticket = make_ticket("Payroll salary payment missing")
        [result] = classifier.bulk_classify([ticket])
        assert result is ticket  # same object
        assert ticket.category == Category.PAYROLL


class TestRoutingSuggestion:
    def test_payroll_routes_to_payroll_team(self):
        ticket = make_ticket("Payroll issue")
        classifier.classify(ticket)
        ticket.category = Category.PAYROLL
        assert "Payroll" in classifier.get_routing_suggestion(ticket)

    def test_access_routes_to_technical_team(self):
        ticket = make_ticket("Login issue")
        classifier.classify(ticket)
        ticket.category = Category.ACCESS
        assert "Technical" in classifier.get_routing_suggestion(ticket)
