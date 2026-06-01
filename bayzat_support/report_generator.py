"""Report Generator – produces support metrics summaries and CSV exports.

The generator consumes a list of :class:`~bayzat_support.models.Ticket`
objects and produces:

* A summary dictionary with KPI counts.
* A text-based dashboard string for quick review in the terminal.
* A CSV export for further analysis in spreadsheet tools.
"""

import csv
import io
from collections import Counter
from datetime import datetime
from typing import List, Optional

from bayzat_support.models import Category, Priority, Status, Ticket
from bayzat_support.sla_monitor import SLAMonitor


class ReportGenerator:
    """Generates reports and dashboards from a collection of tickets.

    Usage::

        generator = ReportGenerator()
        summary = generator.summary(tickets)
        print(generator.dashboard(tickets))
        csv_text = generator.export_csv(tickets)
    """

    def __init__(self, sla_monitor: Optional[SLAMonitor] = None) -> None:
        self._sla = sla_monitor or SLAMonitor()

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    def summary(
        self,
        tickets: List[Ticket],
        reference_time: Optional[datetime] = None,
    ) -> dict:
        """Return a comprehensive KPI summary dictionary.

        The returned dictionary contains:

        * ``total``              – total ticket count
        * ``by_status``          – count per :class:`~bayzat_support.models.Status`
        * ``by_priority``        – count per :class:`~bayzat_support.models.Priority`
        * ``by_category``        – count per :class:`~bayzat_support.models.Category`
        * ``sla``                – SLA compliance sub-dict
        * ``generated_at``       – ISO-8601 timestamp of the report
        """
        now = reference_time or datetime.utcnow()

        by_status = Counter(t.status.value for t in tickets)
        by_priority = Counter(t.priority.value for t in tickets)
        by_category = Counter(t.category.value for t in tickets)

        sla_summary = self._sla.summary(tickets, reference_time=now)

        return {
            "total": len(tickets),
            "by_status": dict(by_status),
            "by_priority": dict(by_priority),
            "by_category": dict(by_category),
            "sla": sla_summary,
            "generated_at": now.isoformat(),
        }

    # ------------------------------------------------------------------
    # Dashboard
    # ------------------------------------------------------------------

    def dashboard(
        self,
        tickets: List[Ticket],
        reference_time: Optional[datetime] = None,
        title: str = "Bayzat Tech Support – Live Dashboard",
    ) -> str:
        """Return a formatted text dashboard string.

        Args:
            tickets: Tickets to report on.
            reference_time: Evaluation timestamp (defaults to now).
            title: Dashboard title shown in the header.

        Returns:
            A multi-line string suitable for printing to a terminal.
        """
        now = reference_time or datetime.utcnow()
        data = self.summary(tickets, reference_time=now)
        sla = data["sla"]

        lines = [
            "=" * 60,
            title.center(60),
            f"Generated: {now.strftime('%d %b %Y %H:%M UTC')}".center(60),
            "=" * 60,
            "",
            f"  Total Tickets : {data['total']}",
            "",
            "  ── By Status ──────────────────────────────────────────",
        ]

        for status in Status:
            count = data["by_status"].get(status.value, 0)
            lines.append(f"    {status.value.replace('_', ' ').title():<20} {count:>4}")

        lines += [
            "",
            "  ── By Priority ────────────────────────────────────────",
        ]
        for priority in Priority:
            count = data["by_priority"].get(priority.value, 0)
            lines.append(f"    {priority.value.title():<20} {count:>4}")

        lines += [
            "",
            "  ── By Category ────────────────────────────────────────",
        ]
        # Sort categories by count descending
        cat_items = sorted(
            data["by_category"].items(), key=lambda x: x[1], reverse=True
        )
        for cat, count in cat_items:
            lines.append(f"    {cat.title():<20} {count:>4}")

        lines += [
            "",
            "  ── SLA Compliance ─────────────────────────────────────",
            f"    Healthy   : {sla['healthy']}",
            f"    At Risk   : {sla['at_risk']}",
            f"    Breached  : {sla['breached']}",
            f"    Compliance: {sla['compliance_pct']} %",
            "",
            "=" * 60,
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # CSV export
    # ------------------------------------------------------------------

    def export_csv(self, tickets: List[Ticket]) -> str:
        """Return a CSV string with one row per ticket.

        The CSV includes all key ticket fields and is suitable for
        importing into Excel or Google Sheets.
        """
        output = io.StringIO()
        fieldnames = [
            "ticket_id",
            "subject",
            "customer_name",
            "customer_email",
            "company_name",
            "category",
            "priority",
            "status",
            "assigned_to",
            "created_at",
            "updated_at",
            "sla_deadline",
            "tags",
        ]
        writer = csv.DictWriter(output, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()

        for t in tickets:
            writer.writerow(
                {
                    "ticket_id": t.ticket_id,
                    "subject": t.subject,
                    "customer_name": t.customer_name,
                    "customer_email": t.customer_email,
                    "company_name": t.company_name,
                    "category": t.category.value,
                    "priority": t.priority.value,
                    "status": t.status.value,
                    "assigned_to": t.assigned_to or "",
                    "created_at": t.created_at.isoformat(),
                    "updated_at": t.updated_at.isoformat(),
                    "sla_deadline": t.sla_deadline().isoformat(),
                    "tags": "|".join(t.tags),
                }
            )

        return output.getvalue()

    def export_csv_to_file(self, tickets: List[Ticket], path: str) -> None:
        """Write the CSV export to a file at *path*."""
        from pathlib import Path

        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", newline="", encoding="utf-8") as fh:
            fh.write(self.export_csv(tickets))
