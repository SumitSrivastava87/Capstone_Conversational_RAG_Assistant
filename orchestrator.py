"""
LangGraph orchestrator — wires Agent 1, 2, and 3 into a single pipeline.

Graph shape:
  START → classify → [escalate | retrieve] → draft → END
                         ↓ (if state.escalate)
                      escalation → END
"""

from dataclasses import asdict

from langgraph.graph import END, START, StateGraph

from agent1.classifier import classify
from agent2.retriever import retrieve as do_retrieve
from agent3.drafter import draft
from shared.state import AgentState, GraphState


# ---------------------------------------------------------------------------
# Helpers: convert between dataclass and TypedDict
# ---------------------------------------------------------------------------

def _to_graph(state: AgentState) -> GraphState:
    return GraphState(**asdict(state))


def _to_agent(gs: GraphState) -> AgentState:
    return AgentState(
        message=gs["message"],
        intent=gs.get("intent"),
        confidence=gs.get("confidence"),
        policy_chunks=gs.get("policy_chunks", []),
        source_refs=gs.get("source_refs", []),
        draft_response=gs.get("draft_response"),
        escalate=gs.get("escalate", False),
        metadata=gs.get("metadata", {}),
        history=gs.get("history", []),
    )


# ---------------------------------------------------------------------------
# Graph nodes — each returns only the fields it modifies
# ---------------------------------------------------------------------------

def classify_node(state: GraphState) -> dict:
    result = classify(_to_agent(state))
    return {
        "intent": result.intent,
        "confidence": result.confidence,
        "escalate": result.escalate,
        "metadata": result.metadata,
    }


def retrieve_node(state: GraphState) -> dict:
    retrieval = do_retrieve(state["message"], state.get("intent", "general"))
    return {
        "policy_chunks": retrieval.chunks,
        "source_refs": retrieval.source_refs,
    }


def draft_node(state: GraphState) -> dict:
    result = draft(_to_agent(state))
    return {"draft_response": result.draft_response}


def escalation_node(state: GraphState) -> dict:
    reason = state.get("metadata", {}).get("escalation_reason", "your request")
    response = (
        f"We sincerely apologise for the inconvenience. Due to {reason}, "
        "your case has been escalated to our senior support team. "
        "A specialist will contact you within 24 hours."
    )
    return {"draft_response": response}


# ---------------------------------------------------------------------------
# Routing
# ---------------------------------------------------------------------------

def _route_after_classify(state: GraphState) -> str:
    return "escalation" if state.get("escalate", False) else "retrieve"


# ---------------------------------------------------------------------------
# Build graph
# ---------------------------------------------------------------------------

_workflow = StateGraph(GraphState)
_workflow.add_node("classify", classify_node)
_workflow.add_node("retrieve", retrieve_node)
_workflow.add_node("draft", draft_node)
_workflow.add_node("escalation", escalation_node)

_workflow.add_edge(START, "classify")
_workflow.add_conditional_edges(
    "classify",
    _route_after_classify,
    {"retrieve": "retrieve", "escalation": "escalation"},
)
_workflow.add_edge("retrieve", "draft")
_workflow.add_edge("draft", END)
_workflow.add_edge("escalation", END)

graph = _workflow.compile()


# ---------------------------------------------------------------------------
# Public helpers used by app.py
# ---------------------------------------------------------------------------

def run_pipeline(state: AgentState) -> AgentState:
    """Run the full pipeline synchronously; return final AgentState."""
    result_gs: GraphState = graph.invoke(_to_graph(state))
    return _to_agent(result_gs)


def stream_pipeline(state: AgentState):
    """
    Yield step dicts suitable for SSE serialisation.
    Each dict: {"node": str, "data": {...relevant fields...}}
    Final dict has node == "done" with the complete result.
    """
    _step_fields = {
        "classify": ("intent", "confidence", "escalate"),
        "retrieve": ("policy_chunks", "source_refs"),
        "draft": ("draft_response",),
        "escalation": ("draft_response",),
    }

    final_gs: GraphState = {}
    for chunk in graph.stream(_to_graph(state)):
        node = next(iter(chunk))
        node_state = chunk[node]
        final_gs.update(node_state)
        fields = _step_fields.get(node, ())
        yield {"node": node, "data": {k: node_state.get(k) for k in fields}}

    yield {"node": "done", "data": dict(final_gs)}
