"""
Agent 1 — Intent Classifier.
Calls a Groq-hosted LLM to classify a customer message into one of 5 intents
and returns a confidence score (0–1). Low-confidence results are auto-flagged
for escalation so the orchestrator can route them to a human agent.
"""

import json
import os

from groq import Groq

from shared.state import AgentState

INTENTS = ["complaint", "refund", "product_info", "escalate", "general"]
LOW_CONFIDENCE_THRESHOLD = float(os.getenv("CLASSIFIER_CONFIDENCE_THRESHOLD", "0.70"))
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client

_PROMPT = """\
You are an intent classifier for a customer service pipeline.

Classify the message below into exactly one intent:
  • complaint    – unhappy about a product, service, or experience
  • refund       – wants money back, a return, or an exchange
  • product_info – wants information about a product or service
  • escalate     – demands a manager or expresses extreme, unresolved frustration
  • general      – anything else

Return ONLY a JSON object with these keys:
  "intent":     one of the five strings above
  "confidence": float 0.0–1.0 (how certain you are)
  "reasoning":  one sentence

Customer message:
\"\"\"{message}\"\"\"
"""


def classify(state: AgentState) -> AgentState:
    """Classify the message in *state* and update intent, confidence, and escalate flag."""
    response = _get_client().chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=256,
        response_format={"type": "json_object"},
        messages=[{"role": "user", "content": _PROMPT.format(message=state.message)}],
    )

    data = json.loads(response.choices[0].message.content.strip())
    intent: str = data["intent"]
    confidence: float = float(data["confidence"])

    state.intent = intent
    state.confidence = confidence

    if confidence < LOW_CONFIDENCE_THRESHOLD:
        state.escalate = True
        state.metadata["escalation_reason"] = (
            f"Low classifier confidence ({confidence:.2f} < {LOW_CONFIDENCE_THRESHOLD})"
        )
    elif intent == "escalate":
        state.escalate = True
        state.metadata["escalation_reason"] = "Customer explicitly requested escalation"

    state.metadata["classifier_reasoning"] = data.get("reasoning", "")
    return state
