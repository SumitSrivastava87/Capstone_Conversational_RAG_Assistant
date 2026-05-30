"""
Agent 3 — Response Drafter.
Takes the classified intent, retrieved policy chunks, and original message
from AgentState, then uses a Groq-hosted LLM with a tone-appropriate system
prompt to produce a professional customer service reply.
"""

import os

from groq import Groq

from agent3.prompts import build_user_prompt, get_system_prompt
from shared.state import AgentState

GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

_client: Groq | None = None


def _get_client() -> Groq:
    global _client
    if _client is None:
        _client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    return _client


def draft(state: AgentState) -> AgentState:
    """Generate a reply and store it in state.draft_response."""
    system = get_system_prompt(state.intent or "general")
    user = build_user_prompt(state.message, state.policy_chunks)

    # Build messages: system → conversation history → current user turn
    messages = [{"role": "system", "content": system}]
    for turn in state.history:
        messages.append({"role": turn["role"], "content": turn["content"]})
    messages.append({"role": "user", "content": user})

    response = _get_client().chat.completions.create(
        model=GROQ_MODEL,
        max_tokens=1024,
        messages=messages,
    )

    state.draft_response = response.choices[0].message.content.strip()
    return state
