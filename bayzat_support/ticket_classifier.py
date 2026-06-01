"""Ticket classifier – automatically assigns Category and Priority to incoming tickets.

The classifier uses keyword matching against the ticket subject and description
to determine the most appropriate HR module category and urgency level.  This
approach requires no external ML dependencies and can be extended by updating
the keyword dictionaries below.
"""

import re
from typing import Dict, List, Tuple

from bayzat_support.models import Category, Priority, Ticket


# ---------------------------------------------------------------------------
# Keyword mappings
# ---------------------------------------------------------------------------

# Map each category to a list of keywords/phrases (lower-cased).
CATEGORY_KEYWORDS: Dict[Category, List[str]] = {
    Category.PAYROLL: [
        "payroll", "salary", "payslip", "pay slip", "pay run", "wps",
        "overtime pay", "bonus", "deduction", "end of service", "gratuity",
        "net pay", "gross pay", "tax", "bank transfer", "payment",
    ],
    Category.LEAVE: [
        "leave", "vacation", "annual leave", "sick leave", "maternity",
        "paternity", "unpaid leave", "leave balance", "leave request",
        "leave approval", "time off", "pto", "days off",
    ],
    Category.ATTENDANCE: [
        "attendance", "check in", "check-in", "check out", "check-out",
        "clock in", "clock out", "geofence", "location", "shift",
        "schedule", "late arrival", "early departure", "absent",
        "biometric", "fingerprint",
    ],
    Category.ONBOARDING: [
        "onboard", "new hire", "new employee", "joining", "welcome",
        "account setup", "first day", "contract", "offer letter",
    ],
    Category.OFFBOARDING: [
        "offboard", "termination", "resignation", "last day",
        "exit interview", "end of service", "clearance",
    ],
    Category.BENEFITS: [
        "benefit", "insurance", "medical", "health", "dental", "vision",
        "gym", "reimbursement", "allowance", "housing", "transportation",
    ],
    Category.PERFORMANCE: [
        "performance", "appraisal", "review", "kpi", "goal", "okr",
        "evaluation", "feedback", "rating",
    ],
    Category.DOCUMENTS: [
        "document", "certificate", "noc", "letter", "visa", "passport",
        "eid", "upload", "download", "file", "report",
    ],
    Category.ACCESS: [
        "login", "password", "reset", "access", "permission", "role",
        "two factor", "2fa", "sso", "single sign on", "locked out",
        "account", "user",
    ],
    Category.INTEGRATION: [
        "integration", "api", "webhook", "sync", "connect", "import",
        "export", "third party", "erp", "accounting",
    ],
}

# Map each priority keyword/phrase to a Priority level.
PRIORITY_KEYWORDS: Dict[Priority, List[str]] = {
    Priority.CRITICAL: [
        "urgent", "critical", "emergency", "system down", "outage",
        "cannot login", "all employees", "entire company", "production",
        "immediately", "asap",
    ],
    Priority.HIGH: [
        "high priority", "important", "blocking", "payroll run",
        "payroll processing", "deadline", "today", "tonight",
    ],
    Priority.LOW: [
        "low priority", "minor", "cosmetic", "when possible", "no rush",
        "question", "enquiry", "how to",
    ],
}


def _normalize(text: str) -> str:
    """Lower-case and collapse whitespace for reliable matching."""
    return re.sub(r"\s+", " ", text.lower().strip())


def _count_keyword_hits(text: str, keywords: List[str]) -> int:
    """Return how many keywords from the list appear in *text*."""
    return sum(1 for kw in keywords if kw in text)


class TicketClassifier:
    """Classifies a :class:`~bayzat_support.models.Ticket` by category and priority.

    Usage::

        classifier = TicketClassifier()
        ticket = classifier.classify(ticket)
    """

    def classify(self, ticket: Ticket) -> Ticket:
        """Classify *ticket* in-place and return it.

        Sets ``ticket.category`` and ``ticket.priority`` based on keyword
        analysis of the ticket subject and description.
        """
        combined = _normalize(f"{ticket.subject} {ticket.description}")
        ticket.category = self._detect_category(combined)
        ticket.priority = self._detect_priority(combined, ticket.category)
        return ticket

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _detect_category(self, text: str) -> Category:
        """Return the best-matching :class:`~bayzat_support.models.Category`."""
        scores: Dict[Category, int] = {}
        for category, keywords in CATEGORY_KEYWORDS.items():
            score = _count_keyword_hits(text, keywords)
            if score:
                scores[category] = score

        if not scores:
            return Category.GENERAL

        return max(scores, key=lambda c: scores[c])

    def _detect_priority(self, text: str, category: Category) -> Priority:
        """Return the best-matching :class:`~bayzat_support.models.Priority`.

        Falls back to a category-based default when no explicit priority
        keyword is found.
        """
        # Explicit priority keywords override everything
        for priority in (Priority.CRITICAL, Priority.HIGH, Priority.LOW):
            if _count_keyword_hits(text, PRIORITY_KEYWORDS[priority]):
                return priority

        # Category-based defaults – payroll/access issues default to HIGH
        if category in (Category.PAYROLL, Category.ACCESS):
            return Priority.HIGH

        return Priority.MEDIUM

    def bulk_classify(self, tickets: List[Ticket]) -> List[Ticket]:
        """Classify a list of tickets and return them."""
        return [self.classify(t) for t in tickets]

    def get_routing_suggestion(self, ticket: Ticket) -> str:
        """Return a suggested team/queue name for the ticket."""
        routing: Dict[Category, str] = {
            Category.PAYROLL: "Payroll & Compensation Team",
            Category.LEAVE: "HR Operations Team",
            Category.ATTENDANCE: "HR Operations Team",
            Category.ONBOARDING: "Implementation Team",
            Category.OFFBOARDING: "HR Operations Team",
            Category.BENEFITS: "Benefits Team",
            Category.PERFORMANCE: "HR Operations Team",
            Category.DOCUMENTS: "HR Operations Team",
            Category.ACCESS: "Technical Support Team",
            Category.INTEGRATION: "Technical Support Team",
            Category.GENERAL: "Technical Support Team",
        }
        return routing.get(ticket.category, "Technical Support Team")
