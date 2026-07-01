"""
Hybrid BM25 + TF-IDF retrieval with reciprocal rank fusion.
"""
import re
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity
from backend.services import catalog as _cat

# Standard RRF constant — higher value reduces the impact of rank differences
RRF_K = 60


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


def _bm25_search(query: str, k: int) -> list[tuple[float, int]]:
    tokens = _tokenize(query)
    scores = _cat._bm25.get_scores(tokens)
    top_idx = np.argsort(scores)[::-1][:k]
    return [(float(scores[i]), int(i)) for i in top_idx if scores[i] > 0]


def _tfidf_search(query: str, k: int) -> list[tuple[float, int]]:
    vec = _cat._tfidf.transform([query])
    sims = cosine_similarity(vec, _cat._tfidf_matrix).flatten()
    top_idx = np.argsort(sims)[::-1][:k]
    return [(float(sims[i]), int(i)) for i in top_idx if sims[i] > 0]


def hybrid_search(query: str, k: int = 20) -> list[dict]:
    """BM25 + TF-IDF with reciprocal rank fusion."""
    if _cat._bm25 is None:
        raise RuntimeError("Catalog not indexed. Call load_and_index() first.")

    bm25_results = _bm25_search(query, k=60)
    tfidf_results = _tfidf_search(query, k=60)

    rrf: dict[int, float] = {}
    for rank, (_, idx) in enumerate(bm25_results):
        rrf[idx] = rrf.get(idx, 0) + 1.0 / (rank + RRF_K)
    for rank, (_, idx) in enumerate(tfidf_results):
        rrf[idx] = rrf.get(idx, 0) + 1.0 / (rank + RRF_K)

    results = []
    for idx in sorted(rrf, key=lambda x: -rrf[x])[:k]:
        item = dict(_cat._catalog[idx])
        item["_score"] = rrf[idx]
        results.append(item)
    return results


def build_catalog_context(query: str, k: int = 20) -> str:
    results = hybrid_search(query, k=k)
    if not results:
        return "No relevant assessments found in catalog for this query."
    lines = ["=== CATALOG CONTEXT (use only these assessments) ==="]
    for i, item in enumerate(results, 1):
        type_labels = ", ".join(item.get("test_type_labels", []))
        type_codes = ", ".join(item.get("test_types", []))
        levels = ", ".join(item.get("job_levels", []))
        dur = item.get("duration", "N/A")
        desc = (item.get("description", "") or "")[:250]
        lines.append(
            f"{i}. **{item['name']}**\n"
            f"   URL: {item['url']}\n"
            f"   Type: {type_labels} [{type_codes}] | Duration: {dur} | Levels: {levels}\n"
            f"   {desc}"
        )
    return "\n".join(lines)
