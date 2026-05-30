"""
Tone-aware prompt templates for the response drafter.
Each intent gets a system prompt that sets the right register and a
user prompt template that injects the retrieved policy context.
"""

SYSTEM_PROMPTS: dict[str, str] = {
    "complaint": (
        "You are a compassionate customer service agent. "
        "Acknowledge the customer's frustration with genuine empathy before offering a solution. "
        "Never be dismissive. Use a warm, apologetic tone throughout."
    ),
    "refund": (
        "You are a precise customer service agent handling a refund or return request. "
        "Provide clear, step-by-step instructions. Be direct and action-oriented. "
        "State timelines and conditions explicitly so the customer knows exactly what to expect."
    ),
    "product_info": (
        "You are a knowledgeable product specialist. "
        "Answer helpfully and completely. Use simple language and, where useful, bullet points. "
        "Cite the relevant policy documents to build trust."
    ),
    "escalate": (
        "You are a senior customer service agent handling an escalated case. "
        "Be professional, calm, and reassuring. Acknowledge the gravity of the situation "
        "and communicate next steps with precise timelines. Do not over-promise."
    ),
    "general": (
        "You are a friendly and helpful customer service agent. "
        "Be concise and clear. If the answer is not in the provided context, "
        "politely direct the customer to the appropriate channel."
    ),
}

_USER_TEMPLATE = """\
Customer message:
\"\"\"{message}\"\"\"

Relevant policy context:
{policy_context}

Write a professional response to the customer. Use only the information in the policy context above.
If the context does not cover the question, say so and offer to connect them with a specialist.
Do not reveal internal policy document names verbatim; reference them naturally (e.g. "our refund policy").
"""


def build_user_prompt(message: str, chunks: list[str]) -> str:
    if chunks:
        policy_context = "\n\n---\n\n".join(chunks)
    else:
        policy_context = "(No specific policy context retrieved — use general knowledge and offer to follow up.)"
    return _USER_TEMPLATE.format(message=message, policy_context=policy_context)


def get_system_prompt(intent: str) -> str:
    return SYSTEM_PROMPTS.get(intent, SYSTEM_PROMPTS["general"])
