"""
AI and NLP analysis service.

Uses fastembed for semantic similarity between page content
and the user's search query.
"""
import numpy as np
from fastembed import TextEmbedding


model = TextEmbedding("BAAI/bge-small-en-v1.5")


def chunk_text(text: str, chunk_size: int = 4, overlap: int = 1) -> list[str]:
    sentences = text.split(". ")
    chunks = []
    i = 0
    while i < len(sentences):
        chunk = ". ".join(sentences[i:i + chunk_size])
        chunks.append(chunk)
        i += chunk_size - overlap
    return chunks


def cosine_similarity_matrix(query: np.ndarray, vectors: np.ndarray) -> np.ndarray:
    query_norm = query / np.linalg.norm(query)
    vectors_norm = vectors / np.linalg.norm(vectors, axis=1, keepdims=True)
    return vectors_norm @ query_norm


# Weighted mean — rewards pages where many chunks are relevant
def weighted_mean(scores: np.ndarray, threshold: float = 0.7) -> float:
    weights = np.where(scores >= threshold, scores, 0)
    return weights.mean()


def compute_similarity(text: str, query: str) -> float:
    """
    Compute the average semantic similarity between *text* and *query*.

    Returns a float in [0, 1] where 1 is identical meaning.
    Runs synchronously — call via asyncio.to_thread in async contexts.
    """
    query_vec = np.array(list(model.embed([query])))[0]   # (384,)
    text_vecs = np.array(list(model.embed([text])))        # (1, 384)
    return cosine_similarity_matrix(query=query_vec, vectors=text_vecs).max()


def relevance_score(scores: np.ndarray, threshold: float = 0.7) -> float:
    """
    Computes an overall relevancy score via weighted mean — rewards pages where many chunks are relevant
    """
    return weighted_mean(scores=scores, threshold=threshold)


def compute_relevance_score(text: str, query: str, threshold: float = 0.7) -> float:
    """
    Chunk *text*, embed all chunks, and return the weighted-mean relevance score.

    Rewards pages where many chunks are semantically relevant to *query*.
    Runs synchronously — call via asyncio.to_thread in async contexts.
    """
    chunks = chunk_text(text)
    query_vec = np.array(list(model.embed([query])))[0]         # (384,)
    chunk_vecs = np.array(list(model.embed(chunks)))            # (n_chunks, 384)
    scores = cosine_similarity_matrix(query=query_vec, vectors=chunk_vecs)
    return relevance_score(scores=scores, threshold=threshold)
