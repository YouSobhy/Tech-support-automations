"""Auto-responder – generates the first automated response for a new ticket.

The response is personalised with the customer name, ticket ID, category,
priority and SLA commitment so that customers receive instant acknowledgement
with meaningful information.
"""

from datetime import datetime
from typing import Optional

from bayzat_support.models import Category, Priority, Ticket


# ---------------------------------------------------------------------------
# Response templates  (keyed by Category)
# ---------------------------------------------------------------------------

CATEGORY_TEMPLATES: dict[Category, str] = {
    Category.PAYROLL: (
        "Thank you for reaching out about a payroll matter. "
        "Our Payroll & Compensation specialists have been notified and will "
        "investigate your payslip, salary transfer or WPS-related concern "
        "as a priority."
    ),
    Category.LEAVE: (
        "Thank you for contacting us about a leave management issue. "
        "Our HR Operations team will review your leave balance, request or "
        "approval concern and get back to you shortly."
    ),
    Category.ATTENDANCE: (
        "Thank you for reporting an attendance issue. "
        "Our team will look into your check-in/check-out, shift schedule or "
        "geofence configuration and respond with a resolution."
    ),
    Category.ONBOARDING: (
        "Welcome! Thank you for reaching out about an onboarding matter. "
        "Our Implementation team will help set up the new employee's account "
        "and ensure a smooth first-day experience."
    ),
    Category.OFFBOARDING: (
        "Thank you for contacting us regarding an offboarding request. "
        "Our HR Operations team will coordinate the necessary steps including "
        "final settlement, clearance and account deactivation."
    ),
    Category.BENEFITS: (
        "Thank you for getting in touch about an employee benefits issue. "
        "Our Benefits team will review the insurance, allowance or "
        "reimbursement concern and follow up with you."
    ),
    Category.PERFORMANCE: (
        "Thank you for reaching out about a performance management matter. "
        "Our HR Operations team will review the appraisal, KPI or goal "
        "configuration and respond with guidance."
    ),
    Category.DOCUMENTS: (
        "Thank you for contacting us about a document request. "
        "Our team will process your certificate, NOC, visa letter or "
        "report and provide it as soon as possible."
    ),
    Category.ACCESS: (
        "Thank you for reporting an access issue. "
        "Our Technical Support team has been alerted and will restore your "
        "login, reset your password or adjust permissions promptly."
    ),
    Category.INTEGRATION: (
        "Thank you for reaching out about an integration issue. "
        "Our Technical Support team will investigate the API, webhook or "
        "data sync problem and work towards a resolution."
    ),
    Category.GENERAL: (
        "Thank you for contacting Bayzat Tech Support. "
        "One of our specialists will review your request and respond shortly."
    ),
}

PRIORITY_COMMITMENT: dict[Priority, str] = {
    Priority.CRITICAL: (
        "Given the critical nature of this issue, we are treating it with the "
        "highest urgency and aim to provide an initial update within **1 hour**."
    ),
    Priority.HIGH: (
        "We have flagged this as a high-priority ticket and will respond "
        "within **4 hours**."
    ),
    Priority.MEDIUM: (
        "We aim to respond to this ticket within **8 business hours**."
    ),
    Priority.LOW: (
        "We aim to respond to this ticket within **24 business hours**."
    ),
}


class AutoResponder:
    """Generates automated first-response messages for support tickets.

    Usage::

        responder = AutoResponder()
        message = responder.generate(ticket)
    """

    def generate(
        self,
        ticket: Ticket,
        agent_name: Optional[str] = None,
        support_email: str = "support@bayzat.com",
    ) -> str:
        """Return a formatted first-response message for *ticket*.

        Args:
            ticket: The classified :class:`~bayzat_support.models.Ticket`.
            agent_name: Optional name of the assigned support agent.
            support_email: Reply-to address included in the footer.

        Returns:
            A ready-to-send plain-text response string.
        """
        category_msg = CATEGORY_TEMPLATES.get(
            ticket.category, CATEGORY_TEMPLATES[Category.GENERAL]
        )
        priority_msg = PRIORITY_COMMITMENT.get(
            ticket.priority, PRIORITY_COMMITMENT[Priority.MEDIUM]
        )

        deadline = ticket.sla_deadline()
        deadline_str = deadline.strftime("%d %b %Y %H:%M UTC")

        agent_line = (
            f"Your ticket has been assigned to **{agent_name}**.\n\n"
            if agent_name
            else ""
        )

        response = (
            f"Dear {ticket.customer_name},\n\n"
            f"Thank you for contacting Bayzat Tech Support.\n\n"
            f"We have received your request and created ticket "
            f"**#{ticket.ticket_id}** on your behalf.\n\n"
            f"{category_msg}\n\n"
            f"{priority_msg}\n\n"
            f"{agent_line}"
            f"Your SLA deadline is: **{deadline_str}**\n\n"
            f"You can track the status of your ticket by replying to this "
            f"email or referencing ticket **#{ticket.ticket_id}**.\n\n"
            f"Best regards,\n"
            f"Bayzat Tech Support Team\n"
            f"{support_email}"
        )
        return response

    def generate_escalation_notice(self, ticket: Ticket, escalated_to: str) -> str:
        """Return an internal escalation notification message.

        Args:
            ticket: The ticket being escalated.
            escalated_to: Name or team the ticket is escalated to.

        Returns:
            A formatted plain-text escalation notice.
        """
        now = datetime.utcnow().strftime("%d %b %Y %H:%M UTC")
        return (
            f"[ESCALATION NOTICE – {now}]\n\n"
            f"Ticket #{ticket.ticket_id} has been escalated to {escalated_to}.\n\n"
            f"Customer : {ticket.customer_name} <{ticket.customer_email}>\n"
            f"Company  : {ticket.company_name}\n"
            f"Subject  : {ticket.subject}\n"
            f"Category : {ticket.category.value.title()}\n"
            f"Priority : {ticket.priority.value.upper()}\n"
            f"Status   : {ticket.status.value.replace('_', ' ').title()}\n"
            f"Created  : {ticket.created_at.strftime('%d %b %Y %H:%M UTC')}\n\n"
            f"Please review and take ownership of this ticket immediately."
        )

    def generate_resolution_message(
        self, ticket: Ticket, resolution_notes: str, support_email: str = "support@bayzat.com"
    ) -> str:
        """Return a customer-facing resolution message.

        Args:
            ticket: The resolved ticket.
            resolution_notes: Summary of how the issue was resolved.
            support_email: Reply-to address included in the footer.

        Returns:
            A formatted plain-text resolution message.
        """
        return (
            f"Dear {ticket.customer_name},\n\n"
            f"We are pleased to inform you that ticket **#{ticket.ticket_id}** "
            f"has been resolved.\n\n"
            f"**Resolution Summary:**\n{resolution_notes}\n\n"
            f"If you have any further questions or if the issue recurs, please "
            f"do not hesitate to contact us by replying to this email.\n\n"
            f"We appreciate your patience and thank you for using Bayzat.\n\n"
            f"Best regards,\n"
            f"Bayzat Tech Support Team\n"
            f"{support_email}"
        )
