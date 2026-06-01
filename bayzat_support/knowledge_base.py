"""Knowledge Base – stores and retrieves troubleshooting articles.

Articles are plain Python dictionaries so that the knowledge base can be
loaded from a JSON file, a database, or defined inline.  The search
function uses simple keyword matching with TF-IDF-style scoring so that the
most relevant article is returned first without any external dependencies.
"""

import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Built-in knowledge base articles
# ---------------------------------------------------------------------------

DEFAULT_ARTICLES: List[Dict] = [
    {
        "id": "KB001",
        "title": "Employee Cannot Login to Bayzat",
        "category": "access",
        "tags": ["login", "password", "access", "locked", "2fa", "sso"],
        "content": (
            "Troubleshooting steps for login issues:\n"
            "1. Ask the employee to use the 'Forgot Password' link on the login page.\n"
            "2. Ensure the employee's account is Active (HR Admin > Employees > Status).\n"
            "3. Check whether the company SSO configuration is correct in Settings > Integrations.\n"
            "4. If 2FA is enabled, ask the employee to use a backup code or contact their HR Admin "
            "to temporarily disable 2FA.\n"
            "5. Clear browser cache and cookies, then retry.\n"
            "6. If the issue persists, collect the browser console logs and escalate to the "
            "Technical Support Team."
        ),
        "resolution_time_minutes": 15,
    },
    {
        "id": "KB002",
        "title": "Payslip Not Generated for Pay Run",
        "category": "payroll",
        "tags": ["payslip", "pay slip", "pay run", "payroll", "salary", "missing"],
        "content": (
            "Steps to investigate missing payslips:\n"
            "1. Confirm the pay run status is 'Completed' (Payroll > Pay Runs).\n"
            "2. Verify the employee was included in the pay run (check the employee list).\n"
            "3. Ensure the employee has a valid bank account on file.\n"
            "4. Check that salary components are configured for the employee.\n"
            "5. Re-process the payslip if the pay run is still in Draft status.\n"
            "6. If the pay run is finalised, create a correction run or off-cycle run."
        ),
        "resolution_time_minutes": 30,
    },
    {
        "id": "KB003",
        "title": "Leave Balance Incorrect",
        "category": "leave",
        "tags": ["leave", "balance", "vacation", "annual leave", "accrual", "incorrect"],
        "content": (
            "Troubleshooting leave balance discrepancies:\n"
            "1. Navigate to HR Admin > Leave > Employee Leave Balance.\n"
            "2. Verify the leave policy assigned to the employee is correct.\n"
            "3. Check the accrual frequency (monthly/yearly) and start date.\n"
            "4. Look for any manual adjustments in the Leave Adjustments log.\n"
            "5. Confirm that approved leaves are correctly deducted.\n"
            "6. If needed, perform a manual balance adjustment with justification notes."
        ),
        "resolution_time_minutes": 20,
    },
    {
        "id": "KB004",
        "title": "Attendance Not Syncing / Check-in Not Recorded",
        "category": "attendance",
        "tags": ["attendance", "check in", "check-in", "sync", "geofence", "location", "shift"],
        "content": (
            "Steps to resolve attendance sync issues:\n"
            "1. Ask the employee to update the Bayzat mobile app to the latest version.\n"
            "2. Ensure location permissions are granted for the Bayzat app on the device.\n"
            "3. Verify the company geofence radius is set correctly (Settings > Attendance).\n"
            "4. Check whether the employee's shift is configured correctly.\n"
            "5. Ask the employee to manually record attendance if the auto-check fails.\n"
            "6. If the issue is company-wide, check the attendance integration settings."
        ),
        "resolution_time_minutes": 25,
    },
    {
        "id": "KB005",
        "title": "New Employee Onboarding Account Setup",
        "category": "onboarding",
        "tags": ["onboarding", "new hire", "new employee", "setup", "account", "invite", "email"],
        "content": (
            "Steps for setting up a new employee account:\n"
            "1. Navigate to HR Admin > Employees > Add Employee.\n"
            "2. Fill in the required fields: name, email, job title, department, and start date.\n"
            "3. Assign the appropriate role and permissions.\n"
            "4. Click 'Send Invitation' to email the employee their login credentials.\n"
            "5. Ensure the employee receives the invitation email (check spam folder).\n"
            "6. Assign a leave policy, attendance schedule, and payroll component."
        ),
        "resolution_time_minutes": 20,
    },
    {
        "id": "KB006",
        "title": "WPS File Generation Failure",
        "category": "payroll",
        "tags": ["wps", "payroll", "salary transfer", "bank file", "sif", "mol"],
        "content": (
            "Resolving WPS file generation issues:\n"
            "1. Verify all employees have a valid IBAN / bank account number.\n"
            "2. Check that the company's WPS routing number is configured correctly.\n"
            "3. Ensure the pay run is in 'Completed' status before generating the WPS file.\n"
            "4. Download the SIF file from Payroll > Pay Runs > WPS Export.\n"
            "5. If validation errors appear, review the error report for missing employee data.\n"
            "6. Re-upload a corrected file to the bank portal."
        ),
        "resolution_time_minutes": 45,
    },
    {
        "id": "KB007",
        "title": "Employee Benefits Enrolment Issue",
        "category": "benefits",
        "tags": ["benefits", "insurance", "enrolment", "enrollment", "medical", "health"],
        "content": (
            "Troubleshooting benefits enrolment problems:\n"
            "1. Confirm the benefits plan is active and the enrolment window is open.\n"
            "2. Verify the employee meets the eligibility criteria for the plan.\n"
            "3. Check for any pending tasks or forms that need to be completed.\n"
            "4. Re-send the enrolment invitation from HR Admin > Benefits.\n"
            "5. If the plan is via an insurance provider integration, verify the API credentials.\n"
            "6. Escalate to the Benefits Team if the issue is with the external insurer."
        ),
        "resolution_time_minutes": 30,
    },
    {
        "id": "KB008",
        "title": "Performance Appraisal Cycle Not Visible",
        "category": "performance",
        "tags": ["performance", "appraisal", "review", "cycle", "kpi", "visible", "missing"],
        "content": (
            "Steps to resolve missing appraisal cycles:\n"
            "1. Verify the appraisal cycle dates are set and the cycle is 'Active'.\n"
            "2. Check that the employee is included in the appraisal cycle's scope.\n"
            "3. Ensure the employee's manager is assigned correctly.\n"
            "4. Confirm that the employee's role qualifies for this cycle.\n"
            "5. Ask the HR Admin to re-publish the cycle if it was saved as a draft.\n"
            "6. Clear the browser cache and log in again."
        ),
        "resolution_time_minutes": 15,
    },
    {
        "id": "KB009",
        "title": "Document / NOC Letter Not Generating",
        "category": "documents",
        "tags": ["document", "noc", "letter", "certificate", "salary certificate", "generate"],
        "content": (
            "Steps for document generation issues:\n"
            "1. Navigate to HR Admin > Documents > Letter Templates.\n"
            "2. Verify the letter template is active and published.\n"
            "3. Check that all required employee data fields are populated.\n"
            "4. Re-generate the document from the employee's profile.\n"
            "5. If the PDF is blank, ensure the template does not have broken variable tags.\n"
            "6. Test with a different browser or download the PDF directly."
        ),
        "resolution_time_minutes": 15,
    },
    {
        "id": "KB010",
        "title": "API Integration Errors / Webhook Not Firing",
        "category": "integration",
        "tags": ["api", "integration", "webhook", "sync", "error", "third party", "connect"],
        "content": (
            "Troubleshooting API integration and webhook issues:\n"
            "1. Check the integration log in Settings > Integrations > Logs.\n"
            "2. Verify the API credentials (client ID, secret) are valid and not expired.\n"
            "3. Confirm the webhook URL is reachable from Bayzat's servers.\n"
            "4. Review the HTTP response codes in the integration log for hints.\n"
            "5. Re-authenticate the integration if a token has expired.\n"
            "6. Escalate to the Technical Support Team for deep-dive API investigation."
        ),
        "resolution_time_minutes": 60,
    },
]


def _tokenize(text: str) -> List[str]:
    """Return a list of lower-cased word tokens from *text*."""
    return re.findall(r"[a-z0-9]+", text.lower())


def _score_article(article: Dict, query_tokens: List[str]) -> float:
    """Return a relevance score for *article* against *query_tokens*."""
    searchable = " ".join(
        [article.get("title", ""), article.get("content", "")]
        + article.get("tags", [])
    ).lower()
    article_tokens = _tokenize(searchable)
    token_set = set(article_tokens)

    score = 0.0
    for token in query_tokens:
        if token in token_set:
            # Weight title / tag matches more heavily
            title_tokens = set(_tokenize(article.get("title", "")))
            tag_tokens = set(
                _tokenize(" ".join(article.get("tags", [])))
            )
            if token in title_tokens:
                score += 3.0
            elif token in tag_tokens:
                score += 2.0
            else:
                score += 1.0
    return score


class KnowledgeBase:
    """Search and manage troubleshooting articles for Bayzat Tech Support.

    Usage::

        kb = KnowledgeBase()
        results = kb.search("employee cannot login 2fa")
        article = kb.get("KB001")
    """

    def __init__(self, articles: Optional[List[Dict]] = None) -> None:
        self._articles: Dict[str, Dict] = {}
        for article in articles or DEFAULT_ARTICLES:
            self.add_article(article)

    # ------------------------------------------------------------------
    # Article management
    # ------------------------------------------------------------------

    def add_article(self, article: Dict) -> None:
        """Add or replace an article in the knowledge base."""
        article_id = article.get("id")
        if not article_id:
            raise ValueError("Article must have an 'id' field.")
        self._articles[article_id] = article

    def remove_article(self, article_id: str) -> bool:
        """Remove an article by ID.  Returns True if it existed."""
        if article_id in self._articles:
            del self._articles[article_id]
            return True
        return False

    def get(self, article_id: str) -> Optional[Dict]:
        """Return the article with *article_id*, or None if not found."""
        return self._articles.get(article_id)

    def list_all(self) -> List[Dict]:
        """Return all articles sorted by ID."""
        return sorted(self._articles.values(), key=lambda a: a.get("id", ""))

    def list_by_category(self, category: str) -> List[Dict]:
        """Return articles whose category matches *category*."""
        cat = category.lower()
        return [a for a in self._articles.values() if a.get("category", "").lower() == cat]

    # ------------------------------------------------------------------
    # Search
    # ------------------------------------------------------------------

    def search(self, query: str, top_n: int = 3) -> List[Tuple[Dict, float]]:
        """Return the top *top_n* articles most relevant to *query*.

        Args:
            query: Free-text search string.
            top_n: Maximum number of results to return.

        Returns:
            A list of ``(article, score)`` tuples ordered by relevance
            (highest score first).  Articles with a score of zero are
            excluded.
        """
        query_tokens = _tokenize(query)
        if not query_tokens:
            return []

        scored = [
            (article, _score_article(article, query_tokens))
            for article in self._articles.values()
        ]
        scored = [(a, s) for a, s in scored if s > 0]
        scored.sort(key=lambda x: x[1], reverse=True)
        return scored[:top_n]

    def get_suggested_resolution(self, query: str) -> Optional[str]:
        """Return the content of the best-matching article, or None.

        Convenience wrapper around :meth:`search` for the common case
        where only the top result is needed.
        """
        results = self.search(query, top_n=1)
        if results:
            article, _ = results[0]
            return (
                f"[{article['id']}] {article['title']}\n\n"
                f"{article['content']}"
            )
        return None

    # ------------------------------------------------------------------
    # Persistence
    # ------------------------------------------------------------------

    def load_from_file(self, path: str) -> None:
        """Load and merge articles from a JSON file at *path*."""
        with open(path, encoding="utf-8") as fh:
            articles = json.load(fh)
        for article in articles:
            self.add_article(article)

    def save_to_file(self, path: str) -> None:
        """Persist all articles to a JSON file at *path*."""
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(self.list_all(), fh, indent=2, ensure_ascii=False)
