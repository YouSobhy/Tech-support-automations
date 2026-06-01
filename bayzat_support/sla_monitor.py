"""SLA Monitor – tracks SLA compliance and flags tickets that need escalation.

The monitor evaluates each ticket against its SLA deadline and returns lists of
tickets that are breached or approaching the deadline, together with suggested
escalation actions.
"""

from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import List, Optional, Tuple

from bayzat_support.models import Priority, SLA_HOURS, Status, Ticket


@dataclass
class SLAStatus:
    """SLA evaluation result for a single ticket."""

    ticket: Ticket
    is_breached: bool
    is_at_risk: bool        # within the warning window but not yet breached
    hours_remaining: float  # negative when breached
    sla_deadline: datetime
    recommended_action: str


def _hours_remaining(ticket: Ticket, reference_time: datetime) -> float:
    """Return the number of hours remaining before the SLA deadline.

    Negative values indicate the deadline has already passed.
    """
    delta = ticket.sla_deadline() - reference_time
    return delta.total_seconds() / 3600


class SLAMonitor:
    """Monitors SLA compliance across a collection of tickets.

    Args:
        warning_threshold_pct: Percentage of the SLA window remaining at
            which a ticket is considered "at risk".  Defaults to 25 %.
            For example, a HIGH ticket (4-hour SLA) becomes at-risk when
            fewer than 1 hour remains.

    Usage::

        monitor = SLAMonitor()
        statuses = monitor.evaluate(tickets)
        breached = monitor.get_breached(tickets)
        at_risk  = monitor.get_at_risk(tickets)
    """

    def __init__(self, warning_threshold_pct: float = 25.0) -> None:
        if not (0 < warning_threshold_pct < 100):
            raise ValueError("warning_threshold_pct must be between 0 and 100.")
        self.warning_threshold_pct = warning_threshold_pct

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        tickets: List[Ticket],
        reference_time: Optional[datetime] = None,
    ) -> List[SLAStatus]:
        """Evaluate SLA status for every ticket in *tickets*.

        Args:
            tickets: Tickets to evaluate.
            reference_time: Point-in-time to evaluate against.
                Defaults to ``datetime.utcnow()``.

        Returns:
            A list of :class:`SLAStatus` objects, one per ticket.
        """
        now = reference_time or datetime.utcnow()
        return [self._evaluate_ticket(t, now) for t in tickets]

    def get_breached(
        self,
        tickets: List[Ticket],
        reference_time: Optional[datetime] = None,
    ) -> List[SLAStatus]:
        """Return SLA statuses only for tickets that have breached their SLA."""
        return [s for s in self.evaluate(tickets, reference_time) if s.is_breached]

    def get_at_risk(
        self,
        tickets: List[Ticket],
        reference_time: Optional[datetime] = None,
    ) -> List[SLAStatus]:
        """Return SLA statuses only for tickets approaching their SLA deadline."""
        return [s for s in self.evaluate(tickets, reference_time) if s.is_at_risk]

    def get_healthy(
        self,
        tickets: List[Ticket],
        reference_time: Optional[datetime] = None,
    ) -> List[SLAStatus]:
        """Return SLA statuses for tickets that are within their SLA window."""
        return [
            s
            for s in self.evaluate(tickets, reference_time)
            if not s.is_breached and not s.is_at_risk
        ]

    def summary(
        self,
        tickets: List[Ticket],
        reference_time: Optional[datetime] = None,
    ) -> dict:
        """Return a high-level SLA compliance summary dictionary.

        Example return value::

            {
                "total": 42,
                "healthy": 30,
                "at_risk": 8,
                "breached": 4,
                "compliance_pct": 90.5,
            }
        """
        statuses = self.evaluate(tickets, reference_time)
        total = len(statuses)
        breached_count = sum(1 for s in statuses if s.is_breached)
        at_risk_count = sum(1 for s in statuses if s.is_at_risk)
        healthy_count = total - breached_count - at_risk_count
        compliance_pct = (
            round((healthy_count + at_risk_count) / total * 100, 1) if total else 100.0
        )
        return {
            "total": total,
            "healthy": healthy_count,
            "at_risk": at_risk_count,
            "breached": breached_count,
            "compliance_pct": compliance_pct,
        }

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _warning_hours(self, priority: Priority) -> float:
        """Return the number of hours before deadline at which a ticket is at risk."""
        return SLA_HOURS[priority] * (self.warning_threshold_pct / 100)

    def _evaluate_ticket(self, ticket: Ticket, now: datetime) -> SLAStatus:
        """Build an :class:`SLAStatus` for a single ticket."""
        # Resolved/closed tickets are never breached
        if ticket.status in (Status.RESOLVED, Status.CLOSED):
            return SLAStatus(
                ticket=ticket,
                is_breached=False,
                is_at_risk=False,
                hours_remaining=_hours_remaining(ticket, now),
                sla_deadline=ticket.sla_deadline(),
                recommended_action="No action required – ticket is resolved.",
            )

        remaining = _hours_remaining(ticket, now)
        is_breached = remaining < 0
        is_at_risk = not is_breached and remaining <= self._warning_hours(ticket.priority)

        action = self._recommend_action(ticket, is_breached, is_at_risk, remaining)

        return SLAStatus(
            ticket=ticket,
            is_breached=is_breached,
            is_at_risk=is_at_risk,
            hours_remaining=round(remaining, 2),
            sla_deadline=ticket.sla_deadline(),
            recommended_action=action,
        )

    @staticmethod
    def _recommend_action(
        ticket: Ticket,
        is_breached: bool,
        is_at_risk: bool,
        hours_remaining: float,
    ) -> str:
        if is_breached:
            overdue_mins = int(abs(hours_remaining) * 60)
            return (
                f"SLA BREACHED by {overdue_mins} minutes. "
                f"Escalate ticket #{ticket.ticket_id} to senior support or management immediately."
            )
        if is_at_risk:
            mins_left = int(hours_remaining * 60)
            return (
                f"SLA AT RISK – {mins_left} minutes remaining. "
                f"Prioritise ticket #{ticket.ticket_id} now to avoid a breach."
            )
        hrs = round(hours_remaining, 1)
        return f"Ticket #{ticket.ticket_id} is within SLA – {hrs} hours remaining."
