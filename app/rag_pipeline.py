"""RAG Pipeline module.

Orchestrates the full Retrieval-Augmented Generation pipeline:
query -> retrieve -> generate -> respond with citations.
"""

import time

from app.generator import generate_answer, is_policy_question
from app.retriever import PolicyRetriever


class RAGPipeline:
    """Main RAG pipeline that orchestrates retrieval and generation."""

    def __init__(self, top_k: int = None, use_reranker: bool = True):
        kwargs = {"use_reranker": use_reranker}
        if top_k is not None:
            kwargs["top_k"] = top_k
        self.retriever = PolicyRetriever(**kwargs)

    def query(self, question: str) -> dict:
        """Process a user question through the full RAG pipeline.

        Args:
            question: The user's question about company policies.

        Returns:
            Dictionary with answer, citations, snippets, and metadata.
        """
        start_time = time.time()

        # Pre-filter check
        if not is_policy_question(question):
            elapsed = time.time() - start_time
            return {
                "question": question,
                "answer": "I can only answer questions about Acme Corporation's company policies and procedures. Your question appears to be outside this scope.",
                "citations": [],
                "snippets": [],
                "latency_ms": round(elapsed * 1000, 2),
                "retrieval_count": 0,
            }

        # Step 1: Retrieve relevant chunks
        retrieval_start = time.time()
        results = self.retriever.retrieve(question)
        retrieval_time = time.time() - retrieval_start

        # Step 2: Format context and extract sources
        context = self.retriever.format_context(results)
        sources = self.retriever.get_sources(results)

        # Step 3: Generate answer with LLM
        generation_start = time.time()
        response = generate_answer(question, context, sources)
        generation_time = time.time() - generation_start

        # Step 4: Build snippets from retrieved chunks
        snippets = []
        for result in results:
            meta = result["metadata"]
            snippets.append({
                "text": result["text"][:300] + ("..." if len(result["text"]) > 300 else ""),
                "source": meta.get("title", "Unknown"),
                "doc_id": meta.get("doc_id", "N/A"),
                "relevance_score": round(result.get("rerank_score", result.get("score", 0)), 4),
            })

        total_time = time.time() - start_time

        return {
            "question": question,
            "answer": response["answer"],
            "citations": response["citations"],
            "snippets": snippets,
            "latency_ms": round(total_time * 1000, 2),
            "retrieval_latency_ms": round(retrieval_time * 1000, 2),
            "generation_latency_ms": round(generation_time * 1000, 2),
            "retrieval_count": len(results),
            "model": response.get("model", ""),
        }
