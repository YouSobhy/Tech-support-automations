# Tech-support-automations

A Python automation toolkit for **Bayzat Tech Support** – an HRMS SaaS platform
that helps companies manage their HR operations. The toolkit reduces manual effort
for support specialists by automating ticket triage, first-response drafting, SLA
tracking, knowledge-base search, and dashboard reporting.

---

## Features

| Module | What it does |
|---|---|
| **Ticket Classifier** | Detects the HR module (Payroll, Leave, Attendance, etc.) and urgency level from free-text subject/description. Suggests the right team queue. |
| **Auto Responder** | Generates personalised first-response emails with SLA commitments, escalation notices, and resolution summaries. |
| **SLA Monitor** | Evaluates every open ticket against its SLA deadline (CRITICAL 1 h / HIGH 4 h / MEDIUM 8 h / LOW 24 h). Flags at-risk and breached tickets with recommended actions. |
| **Knowledge Base** | Stores 10 built-in troubleshooting articles covering common Bayzat issues. Supports keyword search, category filtering, and JSON import/export. |
| **Report Generator** | Produces a live text dashboard and a CSV export covering ticket counts by status, priority, category, and SLA compliance %. |

---

## Project structure

```
Tech-support-automations/
├── bayzat_support/
│   ├── __init__.py
│   ├── models.py            # Ticket, Priority, Category, Status, SLA_HOURS
│   ├── ticket_classifier.py # Keyword-based classification + routing
│   ├── auto_responder.py    # First-response, escalation, resolution messages
│   ├── sla_monitor.py       # SLA evaluation and compliance summary
│   ├── knowledge_base.py    # Built-in KB articles + search
│   └── report_generator.py  # Dashboard and CSV export
├── tests/
│   ├── test_models.py
│   ├── test_ticket_classifier.py
│   ├── test_auto_responder.py
│   ├── test_sla_monitor.py
│   ├── test_knowledge_base.py
│   └── test_report_generator.py
├── main.py                  # End-to-end demo
├── requirements.txt
└── README.md
```

---

## Quick start

```bash
# 1. Clone and enter the repo
git clone https://github.com/YouSobhy/Tech-support-automations.git
cd Tech-support-automations

# 2. Install dependencies (Python 3.10+ recommended)
pip install -r requirements.txt

# 3. Run the end-to-end demo
python main.py
```

---

## Running tests

```bash
pytest tests/ -v
```

All 81 tests should pass.

---

## Usage examples

### Classify a ticket and generate a first response

```python
from bayzat_support import Ticket, TicketClassifier, AutoResponder

ticket = Ticket(
    ticket_id="BZ-2001",
    subject="Payslip not generated for March pay run",
    description="Three employees are missing payslips. Deadline today.",
    customer_email="hr@company.com",
    customer_name="Sara Khan",
    company_name="Innovate Technologies",
)

classifier = TicketClassifier()
classifier.classify(ticket)
print(ticket.category)   # Category.PAYROLL
print(ticket.priority)   # Priority.HIGH

responder = AutoResponder()
print(responder.generate(ticket))
```

### Check SLA compliance across your queue

```python
from bayzat_support import SLAMonitor

monitor = SLAMonitor()
breached = monitor.get_breached(tickets)
for s in breached:
    print(s.recommended_action)

print(monitor.summary(tickets))
# {'total': 42, 'healthy': 30, 'at_risk': 8, 'breached': 4, 'compliance_pct': 90.5}
```

### Search the knowledge base

```python
from bayzat_support import KnowledgeBase

kb = KnowledgeBase()
suggestion = kb.get_suggested_resolution("employee cannot login 2fa locked out")
print(suggestion)
```

### Export a CSV report

```python
from bayzat_support import ReportGenerator

gen = ReportGenerator()
gen.export_csv_to_file(tickets, "reports/daily_report.csv")
print(gen.dashboard(tickets))
```

---

## SLA tiers

| Priority | SLA (response time) | Default for |
|---|---|---|
| CRITICAL | 1 hour | System-wide outages |
| HIGH | 4 hours | Payroll, access issues |
| MEDIUM | 8 hours | Most functional issues |
| LOW | 24 hours | General enquiries |

---

## Extending the knowledge base

Add custom articles at runtime or load from a JSON file:

```python
kb.add_article({
    "id": "KB011",
    "title": "Custom troubleshooting guide",
    "category": "payroll",
    "tags": ["custom", "payroll"],
    "content": "Step-by-step resolution ...",
    "resolution_time_minutes": 20,
})

# Or persist/load the whole knowledge base
kb.save_to_file("data/knowledge_base.json")
kb.load_from_file("data/knowledge_base.json")
```
