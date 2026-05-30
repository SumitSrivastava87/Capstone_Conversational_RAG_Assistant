"""
Policy retriever: takes a query + intent, returns top-k policy chunks with source references.
Fans out across intent-routed namespaces and deduplicates by source.
"""

from dataclasses import dataclass

from agent2.routing import get_namespaces
from agent2.vector_store import similarity_search


@dataclass
class RetrievalResult:
    chunks: list[str]
    source_refs: list[str]
    scores: list[float]


def retrieve(query: str, intent: str, k: int = 4) -> RetrievalResult:
    """
    Query all namespaces for this intent, merge results, deduplicate, return top-k.
    """
    namespaces = get_namespaces(intent)
    seen_sources: set[str] = set()
    all_results: list[tuple] = []  # (score, chunk_text, source)

    for ns in namespaces:
        hits = similarity_search(query, ns, k=k)
        for doc, score in hits:
            source = doc.metadata.get("source", "unknown")
            # Deduplicate by (source, first 80 chars of content)
            dedup_key = f"{source}:{doc.page_content[:80]}"
            if dedup_key not in seen_sources:
                seen_sources.add(dedup_key)
                all_results.append((score, doc.page_content, source))

    # Sort by score descending, take top-k overall
    all_results.sort(key=lambda x: x[0], reverse=True)
    top = all_results[:k]

    return RetrievalResult(
        chunks=[r[1] for r in top],
        source_refs=[r[2] for r in top],
        scores=[r[0] for r in top],
    )
