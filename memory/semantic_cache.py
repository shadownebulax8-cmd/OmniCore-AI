"""
Semantic Cache Engine. If a near-duplicate question was already answered,
return the cached answer instead of paying for another LLM call. Uses a
separate ChromaDB collection from the knowledge base, keyed on cosine
similarity of the question embedding.
"""
import time
import uuid
import chromadb
from config.settings import settings
from memory.embedder import embed_text


class SemanticCache:
    def __init__(self):
        self.client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_CACHE,
            metadata={"hnsw:space": "cosine"},
        )
        self.threshold = settings.SEMANTIC_CACHE_SIMILARITY_THRESHOLD

    def get(self, query: str) -> str | None:
        if self.collection.count() == 0:
            return None

        results = self.collection.query(query_embeddings=[embed_text(query)], n_results=1)
        distances = (results.get("distances") or [[]])[0]
        metadatas = (results.get("metadatas") or [[]])[0]
        if not distances:
            return None

        # Collection uses cosine space, so Chroma's returned "distance" is
        # (1 - cosine_similarity); convert back to a similarity score.
        similarity = 1 - distances[0]
        if similarity >= self.threshold:
            return metadatas[0].get("answer")
        return None

    def set(self, query: str, answer: str) -> None:
        self.collection.add(
            ids=[str(uuid.uuid4())],
            embeddings=[embed_text(query)],
            documents=[query],
            metadatas=[{"answer": answer, "cached_at": time.time()}],
        )
