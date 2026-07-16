"""
Local embedding pipeline using sentence-transformers. Runs on CPU, no API
key needed, model is downloaded once and cached by HuggingFace on first use.
"""
from functools import lru_cache
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def get_embedder() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def embed_text(text: str) -> list[float]:
    return get_embedder().encode(text).tolist()


def embed_batch(texts: list[str]) -> list[list[float]]:
    return get_embedder().encode(texts).tolist()
