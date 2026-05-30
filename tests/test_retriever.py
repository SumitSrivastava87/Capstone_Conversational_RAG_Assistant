"""
Retrieval quality tests: top-k recall per intent with sample queries.
Uses mock FAISS stores so tests run without real PDFs or an OpenAI key.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent2.retriever import retrieve, RetrievalResult
from agent2.routing import get_namespaces, INTENT_NAMESPACE_MAP


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_doc(content: str, source: str):
    doc = MagicMock()
    doc.page_content = content
    doc.metadata = {"source": source}
    return doc


def _mock_search(query, intent, k=4):
    """Returns two fake hits for any namespace."""
    return [
        (_make_doc(f"Policy chunk for {intent}: {query[:30]}", f"{intent}_policy.pdf"), 0.92),
        (_make_doc(f"General clause for {intent}", "general_policy.pdf"), 0.75),
    ]


# ---------------------------------------------------------------------------
# Routing tests
# ---------------------------------------------------------------------------

class TestIntentRouting:
    def test_all_intents_have_routes(self):
        for intent in ["complaint", "refund", "product_info", "escalate", "general"]:
            namespaces = get_namespaces(intent)
            assert len(namespaces) > 0, f"No namespaces for intent '{intent}'"

    def test_unknown_intent_falls_back_to_general(self):
        namespaces = get_namespaces("unknown_xyz")
        assert "general" in namespaces

    def test_refund_includes_refund_namespace(self):
        assert "refund" in get_namespaces("refund")

    def test_complaint_includes_complaint_namespace(self):
        assert "complaint" in get_namespaces("complaint")

    def test_escalate_includes_escalate_namespace(self):
        assert "escalate" in get_namespaces("escalate")

    def test_product_info_includes_product_info_namespace(self):
        assert "product_info" in get_namespaces("product_info")

    def test_all_routes_include_general_fallback(self):
        for intent, namespaces in INTENT_NAMESPACE_MAP.items():
            assert "general" in namespaces, f"'{intent}' route missing 'general' fallback"


# ---------------------------------------------------------------------------
# Retriever tests
# ---------------------------------------------------------------------------

@patch("agent2.retriever.similarity_search", side_effect=_mock_search)
class TestRetriever:
    def test_returns_retrieval_result(self, _mock):
        result = retrieve("I want a refund", "refund")
        assert isinstance(result, RetrievalResult)

    def test_chunks_not_empty(self, _mock):
        result = retrieve("damaged item complaint", "complaint")
        assert len(result.chunks) > 0

    def test_source_refs_match_chunks_length(self, _mock):
        result = retrieve("product warranty info", "product_info")
        assert len(result.chunks) == len(result.source_refs) == len(result.scores)

    def test_scores_are_floats_between_0_and_1(self, _mock):
        result = retrieve("escalate my issue", "escalate")
        for score in result.scores:
            assert 0.0 <= score <= 1.0

    def test_results_sorted_by_score_descending(self, _mock):
        result = retrieve("general inquiry", "general")
        assert result.scores == sorted(result.scores, reverse=True)

    def test_top_k_respected(self, _mock):
        result = retrieve("how do I return?", "refund", k=2)
        assert len(result.chunks) <= 2

    def test_deduplication_removes_identical_sources(self, _mock):
        result = retrieve("duplicate test", "complaint")
        # source_refs should have no exact duplicates when combined with content key
        seen = set()
        for chunk, source in zip(result.chunks, result.source_refs):
            key = f"{source}:{chunk[:80]}"
            assert key not in seen, f"Duplicate chunk found: {key}"
            seen.add(key)


# ---------------------------------------------------------------------------
# Per-intent recall spot-checks
# ---------------------------------------------------------------------------

SAMPLE_QUERIES = {
    "complaint": [
        "My order arrived damaged",
        "I never received my package",
        "The product stopped working after one day",
    ],
    "refund": [
        "How do I get my money back?",
        "Refund policy for digital goods",
        "Return window for electronics",
    ],
    "product_info": [
        "What is the warranty period?",
        "Does this product support international voltage?",
        "Compatible accessories for model X",
    ],
    "escalate": [
        "I want to speak to a manager",
        "This has not been resolved after three attempts",
        "Legal action notice",
    ],
    "general": [
        "What are your business hours?",
        "How do I contact support?",
        "Where can I find the terms of service?",
    ],
}


@patch("agent2.retriever.similarity_search", side_effect=_mock_search)
class TestPerIntentRecall:
    @pytest.mark.parametrize("query", SAMPLE_QUERIES["complaint"])
    def test_complaint_recall(self, _mock, query):
        result = retrieve(query, "complaint")
        assert len(result.chunks) > 0

    @pytest.mark.parametrize("query", SAMPLE_QUERIES["refund"])
    def test_refund_recall(self, _mock, query):
        result = retrieve(query, "refund")
        assert len(result.chunks) > 0

    @pytest.mark.parametrize("query", SAMPLE_QUERIES["product_info"])
    def test_product_info_recall(self, _mock, query):
        result = retrieve(query, "product_info")
        assert len(result.chunks) > 0

    @pytest.mark.parametrize("query", SAMPLE_QUERIES["escalate"])
    def test_escalate_recall(self, _mock, query):
        result = retrieve(query, "escalate")
        assert len(result.chunks) > 0

    @pytest.mark.parametrize("query", SAMPLE_QUERIES["general"])
    def test_general_recall(self, _mock, query):
        result = retrieve(query, "general")
        assert len(result.chunks) > 0
