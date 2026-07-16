"""
Enterprise Long-Term Semantic Retrieval (RAG). Connects to the ChromaDB
server defined by CHROMA_HOST/CHROMA_PORT (the chromadb service in
docker-compose). Embeddings are computed locally via memory/embedder.py -
Chroma stores vectors we hand it, it does not compute its own here.
"""
import uuid
import chromadb
from config.settings import settings
from memory.embedder import embed_text


class KnowledgeBaseStore:
    def __init__(self):
        self.client = chromadb.HttpClient(host=settings.CHROMA_HOST, port=settings.CHROMA_PORT)
        self.collection = self.client.get_or_create_collection(
            name=settings.CHROMA_COLLECTION_KB,
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(self, text: str, metadata: dict | None = None) -> str:
        doc_id = str(uuid.uuid4())
        self.collection.add(
            ids=[doc_id],
            embeddings=[embed_text(text)],
            documents=[text],
            metadatas=[metadata or {}],
        )
        return doc_id

    def query(self, query_text: str, n_results: int = 4) -> list[str]:
        if self.collection.count() == 0:
            return []
        results = self.collection.query(
            query_embeddings=[embed_text(query_text)],
            n_results=min(n_results, self.collection.count()),
        )
        documents = results.get("documents") or [[]]
        return documents[0]
    
    def search(self, query_text: str, n_results: int = 5) -> dict:
        """Full search with metadata and distances for direct API access."""
        if self.collection.count() == 0:
            return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
        results = self.collection.query(
            query_embeddings=[embed_text(query_text)],
            n_results=min(n_results, self.collection.count()),
        )
        return results
