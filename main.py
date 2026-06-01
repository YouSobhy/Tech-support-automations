#!/usr/bin/env python3
"""Bayzat Tech Support Automation – command-line entry point.

Provides a demonstration of the full automation workflow:

1. Classify incoming tickets by HR module and priority.
2. Generate first-response messages automatically.
3. Monitor SLA compliance and surface at-risk / breached tickets.
4. Search the knowledge base for resolution suggestions.
5. Print a live support dashboard.

Usage::

    python main.py

"""

from datetime import datetime, timedelta

from bayzat_support.auto_responder import AutoResponder
from bayzat_support.knowledge_base import KnowledgeBase
from bayzat_support.models import Category, Priority, Status, Ticket
from bayzat_support.report_generator import ReportGenerator
from bayzat_support.sla_monitor import SLAMonitor
from bayzat_support.ticket_classifier import TicketClassifier


# ---------------------------------------------------------------------------
# Sample incoming tickets (simulating a real-time queue)
# ---------------------------------------------------------------------------

SAMPLE_TICKETS = [
    Ticket(
        ticket_id="BZ-1001",
        subject="Employees cannot login – urgent",
        description=(
            "Since this morning all employees in our UAE office are locked out. "
            "The system is showing a '401 Unauthorized' error on login."
        ),
        customer_email="it.admin@globalcorp.ae",
        customer_name="Ahmad Al-Farsi",
        company_name="Global Corp UAE",
        created_at=datetime.utcnow() - timedelta(minutes=50),
    ),
    Ticket(
        ticket_id="BZ-1002",
        subject="Payslip not generated for March pay run",
        description=(
            "The March pay run was completed but three employees are missing payslips. "
            "We have a deadline today."
        ),
        customer_email="hr@innovate.com",
        customer_name="Sara Khan",
        company_name="Innovate Technologies",
        created_at=datetime.utcnow() - timedelta(hours=3),
    ),
    Ticket(
        ticket_id="BZ-1003",
        subject="Leave balance wrong after maternity leave",
        description=(
            "An employee returned from maternity leave and her annual leave balance "
            "shows 0 days instead of 30."
        ),
        customer_email="hr.ops@sunrise.co",
        customer_name="Layla Nasser",
        company_name="Sunrise Group",
        created_at=datetime.utcnow() - timedelta(hours=2),
    ),
    Ticket(
        ticket_id="BZ-1004",
        subject="Check-in not recording for field staff",
        description=(
            "Our drivers and field technicians cannot check in via the Bayzat app. "
            "The geofence might be configured incorrectly."
        ),
        customer_email="ops@swift-delivery.ae",
        customer_name="Mohammed Hassan",
        company_name="Swift Delivery LLC",
        created_at=datetime.utcnow() - timedelta(hours=1),
    ),
    Ticket(
        ticket_id="BZ-1005",
        subject="Question about how to download performance appraisal report",
        description="How do I export the Q1 appraisal report as a PDF?",
        customer_email="hr@betacorp.com",
        customer_name="Fatima Al-Zaabi",
        company_name="Beta Corp",
        created_at=datetime.utcnow() - timedelta(minutes=10),
    ),
]


def separator(char: str = "-", width: int = 60) -> str:
    return char * width


def run_demo() -> None:
    classifier = TicketClassifier()
    responder = AutoResponder()
    sla_monitor = SLAMonitor()
    kb = KnowledgeBase()
    report_gen = ReportGenerator(sla_monitor)

    # ------------------------------------------------------------------
    # Step 1 – Classify all tickets
    # ------------------------------------------------------------------
    print(separator("="))
    print(" STEP 1: Ticket Classification ".center(60, "="))
    print(separator("="))

    classified_tickets = classifier.bulk_classify(SAMPLE_TICKETS)

    for ticket in classified_tickets:
        routing = classifier.get_routing_suggestion(ticket)
        print(
            f"\n[{ticket.ticket_id}] {ticket.subject[:45]}"
            f"\n  Category : {ticket.category.value.title()}"
            f"\n  Priority : {ticket.priority.value.upper()}"
            f"\n  Routing  : {routing}"
        )

    # ------------------------------------------------------------------
    # Step 2 – Generate automated first responses
    # ------------------------------------------------------------------
    print(f"\n{separator('=')}")
    print(" STEP 2: Automated First Response ".center(60, "="))
    print(separator("="))

    # Show response for the first ticket only to keep output readable
    first_ticket = classified_tickets[0]
    response = responder.generate(first_ticket)
    print(f"\nFirst response for [{first_ticket.ticket_id}]:\n")
    print(response)

    # ------------------------------------------------------------------
    # Step 3 – SLA Monitoring
    # ------------------------------------------------------------------
    print(f"\n{separator('=')}")
    print(" STEP 3: SLA Monitoring ".center(60, "="))
    print(separator("="))

    statuses = sla_monitor.evaluate(classified_tickets)
    for s in statuses:
        flag = "🚨 BREACHED" if s.is_breached else ("⚠️  AT RISK" if s.is_at_risk else "✅ OK")
        print(f"  [{s.ticket.ticket_id}] {flag} – {s.recommended_action}")

    # ------------------------------------------------------------------
    # Step 4 – Knowledge Base lookup
    # ------------------------------------------------------------------
    print(f"\n{separator('=')}")
    print(" STEP 4: Knowledge Base Suggestions ".center(60, "="))
    print(separator("="))

    for ticket in classified_tickets[:3]:
        query = f"{ticket.subject} {ticket.description}"
        suggestion = kb.get_suggested_resolution(query)
        print(f"\n[{ticket.ticket_id}] Best match:")
        if suggestion:
            # Print first 5 lines of the article
            preview = "\n".join(suggestion.splitlines()[:6])
            print(preview)
        else:
            print("  No matching article found.")

    # ------------------------------------------------------------------
    # Step 5 – Dashboard report
    # ------------------------------------------------------------------
    print(f"\n{separator('=')}")
    print(" STEP 5: Support Dashboard ".center(60, "="))
    print(separator("="))
    print(report_gen.dashboard(classified_tickets))


if __name__ == "__main__":
    run_demo()
