"""
Unit tests for Agent 1 — Intent Classifier.
Mocks the Groq client so tests run without an API key.
"""

import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agent1.classifier import classify, INTENTS, LOW_CONFIDENCE_THRESHOLD
from shared.state import AgentState


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_response(intent: str, confidence: float, reasoning: str = "test") -> MagicMock:
    # Groq response shape: response.choices[0].message.content
    message = MagicMock()
    message.content = json.dumps({"intent": intent, "confidence": confidence, "reasoning": reasoning})
    choice = MagicMock()
    choice.message = message
    resp = MagicMock()
    resp.choices = [choice]
    return resp


def _classify_with(intent: str, confidence: float, message: str = "test message") -> AgentState:
    with patch("agent1.classifier._get_client") as mock_get:
        mock_get.return_value.chat.completions.create.return_value = _make_response(intent, confidence)
        state = AgentState(message=message)
        return classify(state)


# ---------------------------------------------------------------------------
# All 5 intent classes
# ---------------------------------------------------------------------------

class TestIntentClassification:
    def test_complaint_intent(self):
        result = _classify_with("complaint", 0.95, "My package arrived completely broken")
        assert result.intent == "complaint"

    def test_refund_intent(self):
        result = _classify_with("refund", 0.92, "I want my money back for this order")
        assert result.intent == "refund"

    def test_product_info_intent(self):
        result = _classify_with("product_info", 0.88, "What is the warranty period?")
        assert result.intent == "product_info"

    def test_escalate_intent(self):
        result = _classify_with("escalate", 0.97, "I want to speak to your manager immediately")
        assert result.intent == "escalate"

    def test_general_intent(self):
        result = _classify_with("general", 0.80, "What are your business hours?")
        assert result.intent == "general"

    def test_all_intents_are_valid(self):
        for intent in INTENTS:
            result = _classify_with(intent, 0.90)
            assert result.intent == intent


# ---------------------------------------------------------------------------
# Confidence scoring
# ---------------------------------------------------------------------------

class TestConfidenceScoring:
    def test_confidence_stored_on_state(self):
        result = _classify_with("complaint", 0.87)
        assert result.confidence == pytest.approx(0.87)

    def test_confidence_is_float(self):
        result = _classify_with("general", 0.5)
        assert isinstance(result.confidence, float)

    def test_high_confidence_no_escalation(self):
        result = _classify_with("complaint", 0.95)
        assert not result.escalate

    def test_low_confidence_triggers_escalation(self):
        result = _classify_with("general", 0.50)
        assert result.escalate

    def test_boundary_confidence_below_threshold_escalates(self):
        # Just below threshold
        result = _classify_with("refund", LOW_CONFIDENCE_THRESHOLD - 0.01)
        assert result.escalate

    def test_boundary_confidence_at_threshold_no_escalation(self):
        # Exactly at threshold
        result = _classify_with("refund", LOW_CONFIDENCE_THRESHOLD)
        assert not result.escalate

    def test_low_confidence_sets_escalation_reason(self):
        result = _classify_with("general", 0.40)
        assert "escalation_reason" in result.metadata
        assert "confidence" in result.metadata["escalation_reason"].lower()


# ---------------------------------------------------------------------------
# Escalation logic
# ---------------------------------------------------------------------------

class TestEscalationFlagging:
    def test_escalate_intent_always_escalates(self):
        # Even with high confidence, explicit escalate intent → escalate
        result = _classify_with("escalate", 0.99, "I demand to speak with a manager NOW")
        assert result.escalate

    def test_escalate_intent_sets_reason(self):
        result = _classify_with("escalate", 0.99)
        assert "escalation_reason" in result.metadata

    def test_non_escalate_intent_high_conf_no_escalation(self):
        for intent in ["complaint", "refund", "product_info", "general"]:
            result = _classify_with(intent, 0.90)
            assert not result.escalate, f"Unexpected escalation for intent '{intent}'"

    def test_reasoning_stored_in_metadata(self):
        with patch("agent1.classifier._get_client") as mock_get:
            mock_get.return_value.chat.completions.create.return_value = _make_response(
                "complaint", 0.95, "clear complaint signal"
            )
            state = AgentState(message="broken item")
            result = classify(state)
        assert "classifier_reasoning" in result.metadata


# ---------------------------------------------------------------------------
# Sample message → expected intent spot-checks
# ---------------------------------------------------------------------------

SAMPLE_CASES = [
    ("My order arrived damaged and I am very upset",          "complaint"),
    ("I need a full refund for order #1234",                  "refund"),
    ("Does this model support 220v?",                         "product_info"),
    ("This is unacceptable, get me your supervisor",          "escalate"),
    ("What are your support hours?",                          "general"),
]


class TestSampleMessages:
    @pytest.mark.parametrize("message,expected_intent", SAMPLE_CASES)
    def test_classifier_returns_expected_intent(self, message, expected_intent):
        result = _classify_with(expected_intent, 0.90, message)
        assert result.intent == expected_intent
