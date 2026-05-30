"""
Intent-aware namespace routing.
Maps each classified intent to the FAISS namespace that holds the relevant policies.
"""

# Maps intent → list of namespaces to query (ordered by priority)
INTENT_NAMESPACE_MAP: dict[str, list[str]] = {
    "complaint": ["complaint", "general"],
    "refund": ["refund", "complaint", "general"],
    "product_info": ["product_info", "general"],
    "escalate": ["escalate", "complaint", "general"],
    "general": ["general"],
}

# Fallback when intent is unknown or low-confidence
FALLBACK_NAMESPACES = ["general"]


def get_namespaces(intent: str) -> list[str]:
    """Return ordered list of FAISS namespaces to search for a given intent."""
    return INTENT_NAMESPACE_MAP.get(intent, FALLBACK_NAMESPACES)
