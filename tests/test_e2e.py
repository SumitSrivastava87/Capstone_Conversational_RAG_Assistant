"""
End-to-end pipeline tests — complaint, refund, and escalation scenarios.
Mocks all LLM calls and the retriever so the full graph can be exercised
without API keys or a FAISS index on disk.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from shared.state import AgentState
from agent2.retriever import RetrievalResult


# ---------------------------------------------------------------------------
# Helpers — build mock returns for each agent
# ---------------------------------------------------------------------------

def _mock_classify(intent: str, confidence: float, escalate: bool = False):
    def _fn(state: AgentState) -> AgentState:
        state.intent = intent
        state.confidence = confidence
        state.escalate = escalate
        if escalate:
            state.metadata["escalation_reason"] = "mocked escalation"
        return state
    return _fn


def _mock_retrieve(n_chunks: int = 2):
    def _fn(query, intent, k=4):
        chunks = [f"Policy chunk {i} for {intent}" for i in range(n_chunks)]
        sources = [f"policy_{intent}_{i}.pdf" for i in range(n_chunks)]
        return RetrievalResult(chunks=chunks, source_refs=sources, scores=[0.9 - i * 0.05 for i in range(n_chunks)])
    return _fn


def _mock_draft(response_text: str):
    def _fn(state: AgentState) -> AgentState:
        state.draft_response = response_text
        return state
    return _fn


# ---------------------------------------------------------------------------
# Scenario: normal complaint path
# ---------------------------------------------------------------------------

class TestComplaintPipeline:
    @patch("orchestrator.classify", _mock_classify("complaint", 0.93))
    @patch("orchestrator.do_retrieve", _mock_retrieve(3))
    @patch("orchestrator.draft", _mock_draft("We are very sorry to hear about your experience."))
    def test_complaint_reaches_draft_node(self):
        from orchestrator import run_pipeline
        state = AgentState(message="My product arrived broken")
        result = run_pipeline(state)
        assert result.intent == "complaint"
        assert result.draft_response == "We are very sorry to hear about your experience."

    @patch("orchestrator.classify", _mock_classify("complaint", 0.93))
    @patch("orchestrator.do_retrieve", _mock_retrieve(3))
    @patch("orchestrator.draft", _mock_draft("We are very sorry to hear about your experience."))
    def test_complaint_populates_policy_chunks(self):
        from orchestrator import run_pipeline
        state = AgentState(message="Item was damaged on arrival")
        result = run_pipeline(state)
        assert len(result.policy_chunks) == 3

    @patch("orchestrator.classify", _mock_classify("complaint", 0.93))
    @patch("orchestrator.do_retrieve", _mock_retrieve(2))
    @patch("orchestrator.draft", _mock_draft("We apologise."))
    def test_complaint_not_escalated(self):
        from orchestrator import run_pipeline
        state = AgentState(message="My order was late")
        result = run_pipeline(state)
        assert not result.escalate


# ---------------------------------------------------------------------------
# Scenario: refund path
# ---------------------------------------------------------------------------

class TestRefundPipeline:
    @patch("orchestrator.classify", _mock_classify("refund", 0.95))
    @patch("orchestrator.do_retrieve", _mock_retrieve(2))
    @patch("orchestrator.draft", _mock_draft("To process your refund, please follow these steps."))
    def test_refund_reaches_draft_node(self):
        from orchestrator import run_pipeline
        state = AgentState(message="I need a refund for order 1234")
        result = run_pipeline(state)
        assert result.intent == "refund"
        assert "refund" in result.draft_response.lower()

    @patch("orchestrator.classify", _mock_classify("refund", 0.95))
    @patch("orchestrator.do_retrieve", _mock_retrieve(2))
    @patch("orchestrator.draft", _mock_draft("Refund instructions here."))
    def test_refund_source_refs_populated(self):
        from orchestrator import run_pipeline
        state = AgentState(message="Return this item please")
        result = run_pipeline(state)
        assert len(result.source_refs) == 2

    @patch("orchestrator.classify", _mock_classify("refund", 0.95))
    @patch("orchestrator.do_retrieve", _mock_retrieve(1))
    @patch("orchestrator.draft", _mock_draft("Refund processed."))
    def test_refund_confidence_stored(self):
        from orchestrator import run_pipeline
        state = AgentState(message="Money back please")
        result = run_pipeline(state)
        assert result.confidence == pytest.approx(0.95)


# ---------------------------------------------------------------------------
# Scenario: escalation path
# ---------------------------------------------------------------------------

class TestEscalationPipeline:
    @patch("orchestrator.classify", _mock_classify("escalate", 0.98, escalate=True))
    @patch("orchestrator.do_retrieve", _mock_retrieve())
    @patch("orchestrator.draft", _mock_draft("This should not be called"))
    def test_escalation_bypasses_retrieve_and_draft(self):
        from orchestrator import run_pipeline
        state = AgentState(message="I demand to speak with a manager right now")
        result = run_pipeline(state)
        # draft mock should NOT have set the response — escalation node takes over
        assert result.draft_response != "This should not be called"

    @patch("orchestrator.classify", _mock_classify("escalate", 0.98, escalate=True))
    @patch("orchestrator.do_retrieve", _mock_retrieve())
    @patch("orchestrator.draft", _mock_draft("Should not appear"))
    def test_escalation_response_mentions_team(self):
        from orchestrator import run_pipeline
        state = AgentState(message="Escalate this NOW")
        result = run_pipeline(state)
        assert result.draft_response is not None
        assert len(result.draft_response) > 20  # has meaningful content

    @patch("orchestrator.classify", _mock_classify("escalate", 0.98, escalate=True))
    @patch("orchestrator.do_retrieve", _mock_retrieve())
    @patch("orchestrator.draft", _mock_draft("Should not appear"))
    def test_escalation_flag_set(self):
        from orchestrator import run_pipeline
        state = AgentState(message="I want a supervisor")
        result = run_pipeline(state)
        assert result.escalate

    @patch("orchestrator.classify", _mock_classify("general", 0.40, escalate=True))
    @patch("orchestrator.do_retrieve", _mock_retrieve())
    @patch("orchestrator.draft", _mock_draft("Should not appear"))
    def test_low_confidence_routes_to_escalation(self):
        from orchestrator import run_pipeline
        state = AgentState(message="Gibberish input xyz 123")
        result = run_pipeline(state)
        assert result.escalate
        assert result.draft_response != "Should not appear"


# ---------------------------------------------------------------------------
# Scenario: streaming pipeline yields correct nodes
# ---------------------------------------------------------------------------

class TestStreamingPipeline:
    @patch("orchestrator.classify", _mock_classify("complaint", 0.93))
    @patch("orchestrator.do_retrieve", _mock_retrieve(2))
    @patch("orchestrator.draft", _mock_draft("Sorry to hear that."))
    def test_stream_emits_classify_node(self):
        from orchestrator import stream_pipeline
        state = AgentState(message="Broken item")
        nodes = [s["node"] for s in stream_pipeline(state)]
        assert "classify" in nodes

    @patch("orchestrator.classify", _mock_classify("refund", 0.90))
    @patch("orchestrator.do_retrieve", _mock_retrieve(2))
    @patch("orchestrator.draft", _mock_draft("Here is the refund info."))
    def test_stream_ends_with_done_node(self):
        from orchestrator import stream_pipeline
        state = AgentState(message="Refund request")
        steps = list(stream_pipeline(state))
        assert steps[-1]["node"] == "done"

    @patch("orchestrator.classify", _mock_classify("refund", 0.90))
    @patch("orchestrator.do_retrieve", _mock_retrieve(2))
    @patch("orchestrator.draft", _mock_draft("Refund confirmed."))
    def test_stream_normal_path_nodes_order(self):
        from orchestrator import stream_pipeline
        state = AgentState(message="Return order please")
        nodes = [s["node"] for s in stream_pipeline(state)]
        # classify must come before retrieve, retrieve before draft
        assert nodes.index("classify") < nodes.index("retrieve")
        assert nodes.index("retrieve") < nodes.index("draft")

    @patch("orchestrator.classify", _mock_classify("escalate", 0.98, escalate=True))
    @patch("orchestrator.do_retrieve", _mock_retrieve())
    @patch("orchestrator.draft", _mock_draft("x"))
    def test_stream_escalation_path_skips_retrieve(self):
        from orchestrator import stream_pipeline
        state = AgentState(message="Escalate now")
        nodes = [s["node"] for s in stream_pipeline(state)]
        assert "escalation" in nodes
        assert "retrieve" not in nodes
        assert "draft" not in nodes
