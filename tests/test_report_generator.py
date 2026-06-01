"""Tests for bayzat_support.report_generator."""

from datetime import datetime, timedelta

from bayzat_support.models import Category, Priority, Status, Ticket
from bayzat_support.report_generator import ReportGenerator


def make_ticket(ticket_id="T001", priority=Priority.MEDIUM, status=Status.OPEN,
                category=Category.GENERAL, created_at=None) -> Ticket:
    return Ticket(
        ticket_id=ticket_id,
        subject="Test subject",
        description="",
        customer_email="x@x.com",
        customer_name="Test User",
        company_name="Test Corp",
        priority=priority,
        status=status,
        category=category,
        created_at=created_at or datetime(2024, 1, 1, 9, 0, 0),
    )


def make_sample_tickets():
    return [
        make_ticket("T1", Priority.CRITICAL, Status.OPEN, Category.ACCESS),
        make_ticket("T2", Priority.HIGH, Status.IN_PROGRESS, Category.PAYROLL),
        make_ticket("T3", Priority.MEDIUM, Status.RESOLVED, Category.LEAVE),
        make_ticket("T4", Priority.LOW, Status.CLOSED, Category.ATTENDANCE),
        make_ticket("T5", Priority.HIGH, Status.ESCALATED, Category.PAYROLL),
    ]


generator = ReportGenerator()


class TestSummary:
    def test_total_count(self):
        tickets = make_sample_tickets()
        s = generator.summary(tickets)
        assert s["total"] == 5

    def test_by_status_counts(self):
        tickets = make_sample_tickets()
        s = generator.summary(tickets)
        assert s["by_status"]["open"] == 1
        assert s["by_status"]["resolved"] == 1
        assert s["by_status"]["closed"] == 1

    def test_by_priority_counts(self):
        tickets = make_sample_tickets()
        s = generator.summary(tickets)
        assert s["by_priority"]["high"] == 2
        assert s["by_priority"]["critical"] == 1

    def test_by_category_counts(self):
        tickets = make_sample_tickets()
        s = generator.summary(tickets)
        assert s["by_category"]["payroll"] == 2

    def test_generated_at_present(self):
        s = generator.summary([])
        assert "generated_at" in s

    def test_sla_sub_dict_present(self):
        s = generator.summary([])
        assert "sla" in s
        assert "total" in s["sla"]


class TestDashboard:
    def test_dashboard_contains_title(self):
        tickets = make_sample_tickets()
        output = generator.dashboard(tickets, title="My Dashboard")
        assert "My Dashboard" in output

    def test_dashboard_contains_total(self):
        tickets = make_sample_tickets()
        output = generator.dashboard(tickets)
        assert "5" in output  # total count

    def test_dashboard_is_string(self):
        output = generator.dashboard([])
        assert isinstance(output, str)


class TestCSVExport:
    def test_csv_has_header_row(self):
        tickets = make_sample_tickets()
        csv_output = generator.export_csv(tickets)
        first_line = csv_output.splitlines()[0]
        assert "ticket_id" in first_line
        assert "priority" in first_line

    def test_csv_row_count_matches_ticket_count(self):
        tickets = make_sample_tickets()
        csv_output = generator.export_csv(tickets)
        lines = [l for l in csv_output.splitlines() if l.strip()]
        # header + 5 data rows
        assert len(lines) == 6

    def test_csv_contains_ticket_id(self):
        tickets = [make_ticket("UNIQUE_XYZ")]
        csv_output = generator.export_csv(tickets)
        assert "UNIQUE_XYZ" in csv_output

    def test_empty_tickets_produces_header_only(self):
        csv_output = generator.export_csv([])
        lines = [l for l in csv_output.splitlines() if l.strip()]
        assert len(lines) == 1  # header only
