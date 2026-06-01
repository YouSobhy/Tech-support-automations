"""Core data models for the Bayzat Tech Support Automation system."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import List, Optional


class Priority(Enum):
    """Ticket priority levels aligned with Bayzat SLA tiers."""

    CRITICAL = "critical"   # System-wide outage; SLA: 1 hour
    HIGH = "high"           # Core feature broken; SLA: 4 hours
    MEDIUM = "medium"       # Feature degraded; SLA: 8 hours
    LOW = "low"             # General enquiry / cosmetic; SLA: 24 hours


class Category(Enum):
    """HR module categories supported on the Bayzat platform."""

    PAYROLL = "payroll"
    LEAVE = "leave"
    ATTENDANCE = "attendance"
    ONBOARDING = "onboarding"
    OFFBOARDING = "offboarding"
    BENEFITS = "benefits"
    PERFORMANCE = "performance"
    DOCUMENTS = "documents"
    ACCESS = "access"
    INTEGRATION = "integration"
    GENERAL = "general"


class Status(Enum):
    """Lifecycle states of a support ticket."""

    OPEN = "open"
    IN_PROGRESS = "in_progress"
    PENDING_CUSTOMER = "pending_customer"
    ESCALATED = "escalated"
    RESOLVED = "resolved"
    CLOSED = "closed"


# SLA response-time thresholds in hours, keyed by Priority
SLA_HOURS: dict[Priority, int] = {
    Priority.CRITICAL: 1,
    Priority.HIGH: 4,
    Priority.MEDIUM: 8,
    Priority.LOW: 24,
}


@dataclass
class Ticket:
    """Represents a single tech-support ticket."""

    ticket_id: str
    subject: str
    description: str
    customer_email: str
    customer_name: str
    company_name: str
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    priority: Priority = Priority.MEDIUM
    category: Category = Category.GENERAL
    status: Status = Status.OPEN
    assigned_to: Optional[str] = None
    resolution_notes: Optional[str] = None
    tags: List[str] = field(default_factory=list)

    def sla_deadline(self) -> datetime:
        """Return the SLA deadline datetime for this ticket."""
        from datetime import timedelta

        hours = SLA_HOURS[self.priority]
        return self.created_at + timedelta(hours=hours)

    def is_sla_breached(self, reference_time: Optional[datetime] = None) -> bool:
        """Return True if the SLA deadline has passed."""
        now = reference_time or datetime.utcnow()
        return now > self.sla_deadline() and self.status not in (
            Status.RESOLVED,
            Status.CLOSED,
        )

    def to_dict(self) -> dict:
        """Serialize the ticket to a plain dictionary."""
        return {
            "ticket_id": self.ticket_id,
            "subject": self.subject,
            "description": self.description,
            "customer_email": self.customer_email,
            "customer_name": self.customer_name,
            "company_name": self.company_name,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "priority": self.priority.value,
            "category": self.category.value,
            "status": self.status.value,
            "assigned_to": self.assigned_to,
            "resolution_notes": self.resolution_notes,
            "tags": self.tags,
        }
