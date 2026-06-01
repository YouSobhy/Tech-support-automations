"""Tests for bayzat_support.knowledge_base."""

import json
import os
import tempfile

import pytest

from bayzat_support.knowledge_base import KnowledgeBase


class TestSearch:
    def setup_method(self):
        self.kb = KnowledgeBase()

    def test_search_returns_relevant_results(self):
        results = self.kb.search("employee cannot login password")
        assert results, "Expected at least one result"
        top_article, top_score = results[0]
        assert top_score > 0
        assert "login" in top_article["title"].lower() or "access" in top_article.get(
            "category", ""
        )

    def test_search_payslip_returns_payroll_article(self):
        results = self.kb.search("payslip not generated pay run")
        assert results
        top_article, _ = results[0]
        assert top_article["category"] == "payroll"

    def test_search_empty_query_returns_empty_list(self):
        assert self.kb.search("") == []

    def test_search_top_n_limits_results(self):
        results = self.kb.search("employee issue problem", top_n=2)
        assert len(results) <= 2

    def test_search_returns_tuples_of_article_and_score(self):
        results = self.kb.search("leave balance")
        for item in results:
            assert isinstance(item, tuple)
            article, score = item
            assert isinstance(article, dict)
            assert isinstance(score, float)


class TestGetSuggestedResolution:
    def setup_method(self):
        self.kb = KnowledgeBase()

    def test_returns_string_for_known_query(self):
        result = self.kb.get_suggested_resolution("leave balance incorrect accrual")
        assert result is not None
        assert isinstance(result, str)
        assert len(result) > 10

    def test_returns_none_for_unknown_query(self):
        result = self.kb.get_suggested_resolution("xyzzy foobar baz")
        assert result is None


class TestArticleManagement:
    def setup_method(self):
        self.kb = KnowledgeBase(articles=[])  # start empty

    def test_add_and_get_article(self):
        article = {"id": "TEST001", "title": "Test Article", "category": "general",
                   "tags": ["test"], "content": "Some content."}
        self.kb.add_article(article)
        retrieved = self.kb.get("TEST001")
        assert retrieved is not None
        assert retrieved["title"] == "Test Article"

    def test_get_unknown_id_returns_none(self):
        assert self.kb.get("UNKNOWN") is None

    def test_remove_article(self):
        article = {"id": "DEL001", "title": "Delete Me", "category": "general",
                   "tags": [], "content": "Will be removed."}
        self.kb.add_article(article)
        removed = self.kb.remove_article("DEL001")
        assert removed is True
        assert self.kb.get("DEL001") is None

    def test_remove_non_existent_returns_false(self):
        assert self.kb.remove_article("DOES_NOT_EXIST") is False

    def test_add_article_without_id_raises(self):
        with pytest.raises(ValueError):
            self.kb.add_article({"title": "No ID article"})

    def test_list_all_sorted_by_id(self):
        for i in ("C", "A", "B"):
            self.kb.add_article({"id": i, "title": i, "category": "x",
                                  "tags": [], "content": ""})
        ids = [a["id"] for a in self.kb.list_all()]
        assert ids == sorted(ids)

    def test_list_by_category(self):
        self.kb.add_article({"id": "P1", "title": "P", "category": "payroll",
                              "tags": [], "content": ""})
        self.kb.add_article({"id": "L1", "title": "L", "category": "leave",
                              "tags": [], "content": ""})
        payroll_articles = self.kb.list_by_category("payroll")
        assert all(a["category"] == "payroll" for a in payroll_articles)
        assert any(a["id"] == "P1" for a in payroll_articles)


class TestPersistence:
    def test_save_and_load_roundtrip(self):
        kb1 = KnowledgeBase(articles=[
            {"id": "RT001", "title": "Roundtrip", "category": "general",
             "tags": ["rt"], "content": "Hello."}
        ])
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            kb1.save_to_file(path)
            kb2 = KnowledgeBase(articles=[])
            kb2.load_from_file(path)
            assert kb2.get("RT001") is not None
            assert kb2.get("RT001")["title"] == "Roundtrip"
        finally:
            os.unlink(path)
