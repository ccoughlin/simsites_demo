"""
AI and NLP analysis service.

Uses sentence-transformers for semantic similarity between page content
and the user's search query.
"""

from sentence_transformers import SentenceTransformer, util

# Loaded once at import time so every request reuses the same model.
_model = SentenceTransformer('distiluse-base-multilingual-cased-v1')


def compute_similarity(text: str, query: str) -> float:
    """
    Compute the semantic similarity between *text* and *query*.

    Returns a float in [0, 1] where 1 is identical meaning.
    Runs synchronously — call via asyncio.to_thread in async contexts.
    """
    embeddings = _model.encode([text, query], convert_to_tensor=True)
    raw = float(util.cos_sim(embeddings[0], embeddings[1]))
    return max(0.0, min(1.0, raw))
