"""Retrieval module for the RAG pipeline.

Handles top-k retrieval from ChromaDB with optional re-ranking
using cross-encoder similarity scoring.
"""

from sentence_transformers import CrossEncoder, SentenceTransformer

from app.config import (
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    EMBEDDING_MODEL,
    RETRIEVAL_TOP_K,
)
from app.ingestion import get_collection


class PolicyRetriever:
    """Retrieves relevant policy chunks from the vector database."""

    def __init__(self, top_k: int = RETRIEVAL_TOP_K, use_reranker: bool = True):
        self.top_k = top_k
        self.use_reranker = use_reranker
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)

        if self.use_reranker:
            self.reranker = CrossEncoder("cross-encoder/ms-marco-MiniLM-L-6-v2")

        self.collection = get_collection(CHROMA_PERSIST_DIR)

    def retrieve(self, query: str, top_k: int = None) -> list[dict]:
        """Retrieve the top-k most relevant chunks for a given query.

        Args:
            query: The user's question.
            top_k: Number of results to return. Defaults to self.top_k.

        Returns:
            List of dictionaries with keys: text, metadata, score.
        """
        k = top_k or self.top_k

        # Retrieve more candidates if re-ranking
        fetch_k = k * 3 if self.use_reranker else k

        # Embed the query
        query_embedding = self.embedding_model.encode(query).tolist()

        # Query ChromaDB
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(fetch_k, self.collection.count()),
            include=["documents", "metadatas", "distances"],
        )

        # Format results
        candidates = []
        for i in range(len(results["ids"][0])):
            candidates.append({
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "score": 1 - results["distances"][0][i],  # Convert distance to similarity
                "id": results["ids"][0][i],
            })

        # Re-rank using cross-encoder
        if self.use_reranker and candidates:
            pairs = [(query, c["text"]) for c in candidates]
            rerank_scores = self.reranker.predict(pairs)

            for i, score in enumerate(rerank_scores):
                candidates[i]["rerank_score"] = float(score)

            # Sort by rerank score
            candidates.sort(key=lambda x: x["rerank_score"], reverse=True)

        # Return top-k after re-ranking
        return candidates[:k]

    def format_context(self, results: list[dict]) -> str:
        """Format retrieved results into a context string for the LLM prompt."""
        context_parts = []
        for i, result in enumerate(results, 1):
            meta = result["metadata"]
            source = meta.get("title", meta.get("source_file", "Unknown"))
            doc_id = meta.get("doc_id", "N/A")

            context_parts.append(
                f"[Source {i}: {source} ({doc_id})]\n{result['text']}\n"
            )

        return "\n---\n".join(context_parts)

    def get_sources(self, results: list[dict]) -> list[dict]:
        """Extract source citation information from results."""
        sources = []
        seen = set()

        for result in results:
            meta = result["metadata"]
            source_key = (meta.get("doc_id", ""), meta.get("title", ""))

            if source_key not in seen:
                seen.add(source_key)
                sources.append({
                    "doc_id": meta.get("doc_id", "N/A"),
                    "title": meta.get("title", "Unknown"),
                    "source_file": meta.get("source_file", ""),
                    "department": meta.get("department", ""),
                })

        return sources
