# AI Tooling Usage

## Tools Used

### 1. Devin (Cognition AI)
**How it was used:** Devin was the primary AI coding assistant used to build this project. It helped with:
- Generating the project structure and boilerplate code.
- Creating synthetic company policy documents.
- Implementing the RAG pipeline (ingestion, retrieval, generation).
- Building the Flask web application with the chat interface.
- Writing tests and the evaluation framework.
- Setting up CI/CD with GitHub Actions.
- Writing documentation.

**What worked well:**
- Excellent at generating structured, comprehensive policy documents that feel realistic.
- Strong at implementing the full-stack architecture from ingestion to web UI in a coherent manner.
- Good at following best practices for project structure, testing, and documentation.
- Helpful for writing evaluation scripts with proper metrics.

**What didn't work as well:**
- Required iteration to get the chunking strategy right — initial attempts were too naive (fixed-size windows).
- Prompt engineering for guardrails required manual refinement to avoid both over-filtering and under-filtering.
- The evaluation framework needed careful design to avoid circular evaluation (using the same LLM to both generate and evaluate).

### 2. OpenRouter API (Google Gemini 2.0 Flash)
**How it was used:** Used as the LLM backend for answer generation and for the LLM-as-judge evaluation of groundedness.

**What worked well:**
- Free tier made it accessible with no cost.
- Good instruction-following for the RAG system prompt.
- Generally accurate citations when prompted correctly.

**What didn't work as well:**
- Occasional rate limiting on the free tier during evaluation runs.
- Sometimes generates slightly verbose answers even with max_tokens limit.

### 3. Sentence-Transformers (Hugging Face)
**How it was used:** Used for generating document embeddings (`all-MiniLM-L6-v2`) and for cross-encoder re-ranking (`cross-encoder/ms-marco-MiniLM-L-6-v2`).

**What worked well:**
- Completely free and runs locally.
- Fast inference for both embedding and re-ranking.
- Cross-encoder re-ranking significantly improved retrieval precision.

**What didn't work as well:**
- Initial model download can be slow on first run.
- The 384-dimensional embeddings from MiniLM are lower quality than larger models, but sufficient for this corpus.

### 4. ChromaDB
**How it was used:** Used as the vector database for storing and querying document embeddings.

**What worked well:**
- Easy setup with no external server required.
- Persistent storage works well for the index.
- Good Python API.

**What didn't work as well:**
- Limited batch size for adding documents.
- No built-in support for hybrid search (vector + keyword).

## Summary

AI tools were instrumental in accelerating the development of this project. The combination of Devin for code generation, OpenRouter for LLM inference, and open-source models for embeddings created a fully functional RAG application at zero cost. The main challenges were in fine-tuning the retrieval pipeline and prompt engineering, which required iterative testing beyond what AI tools could automate alone.
