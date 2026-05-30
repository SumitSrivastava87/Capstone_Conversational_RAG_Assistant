from dataclasses import dataclass, field
from typing import Optional, TypedDict


@dataclass
class AgentState:
    message: str
    intent: Optional[str] = None
    confidence: Optional[float] = None
    policy_chunks: list[str] = field(default_factory=list)
    source_refs: list[str] = field(default_factory=list)
    draft_response: Optional[str] = None
    escalate: bool = False
    metadata: dict = field(default_factory=dict)
    history: list[dict] = field(default_factory=list)  # [{"role": "user"|"assistant", "content": "..."}]


class GraphState(TypedDict, total=False):
    """TypedDict used as LangGraph StateGraph state — mirrors AgentState fields."""
    message: str
    intent: Optional[str]
    confidence: Optional[float]
    policy_chunks: list
    source_refs: list
    draft_response: Optional[str]
    escalate: bool
    metadata: dict
    history: list
