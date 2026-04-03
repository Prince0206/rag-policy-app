# Design and Evaluation Document

## RAG Policy Assistant — Acme Corporation

---

## 1. Architecture Overview

The RAG Policy Assistant is a Retrieval-Augmented Generation (RAG) application that enables employees to ask natural language questions about company policies and receive accurate, cited answers. The system follows a standard RAG architecture:

```
User Question → Embedding → Vector Search → Re-ranking → LLM Generation → Answer + Citations
```

### Component Diagram

```
┌─────────────────────────────────────────────────────────┐
│                    Flask Web App                         │
│  ┌──────────┐  ┌──────────┐  ┌────────────────────┐    │
│  │  / (UI)  │  │  /chat   │  │  /health           │    │
│  │  Chat    │  │  POST API│  │  GET status check  │    │
│  └──────────┘  └──────────┘  └────────────────────┘    │
└────────────────────┬────────────────────────────────────┘
                     │
              ┌──────▼──────┐
              │ RAG Pipeline │
              └──────┬──────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
   ┌─────▼─────┐ ┌──▼──┐ ┌─────▼─────┐
   │ Retriever  │ │Re-  │ │ Generator │
   │ (ChromaDB) │ │rank │ │(OpenRouter│
   │            │ │     │ │  + LLM)   │
   └─────┬─────┘ └─────┘ └───────────┘
         │
   ┌─────▼─────┐
   │ Ingestion  │
   │ Pipeline   │
   │ (Parse →   │
   │  Chunk →   │
   │  Embed)    │
   └────────────┘
```

---

## 2. Design Decisions

### 2.1 Embedding Model: `all-MiniLM-L6-v2`

**Choice:** Sentence-Transformers `all-MiniLM-L6-v2` (local, free)

**Why:**
- **Cost:** Completely free — runs locally with no API calls needed.
- **Performance:** Excellent quality-to-speed ratio. Produces 384-dimensional embeddings.
- **Speed:** Fast inference (~14ms per sentence on CPU), suitable for real-time applications.
- **Quality:** Strong performance on semantic textual similarity benchmarks (STSb: 0.8474).
- **Size:** Small model (~80MB), easy to deploy and low memory footprint.

**Alternatives considered:**
- OpenAI `text-embedding-3-small`: Excellent quality but requires API key and has cost.
- Cohere `embed-english-v3.0`: Good free tier but adds external dependency.
- `all-mpnet-base-v2`: Higher quality but 3x slower; not justified for this corpus size.

### 2.2 Vector Store: ChromaDB

**Choice:** ChromaDB with persistent local storage

**Why:**
- **Simplicity:** Lightweight, embeddable vector database — no separate server needed.
- **Python-native:** Pure Python with great API ergonomics.
- **Persistence:** Supports persistent storage to disk, avoiding re-indexing on restart.
- **Cost:** Completely free and open-source.
- **Metadata filtering:** Supports rich metadata queries alongside vector search.
- **HNSW index:** Uses efficient approximate nearest neighbor search.

**Alternatives considered:**
- Pinecone: Cloud-hosted, excellent for production but adds external dependency and free tier limits.
- FAISS: Facebook's library is very fast but lacks built-in metadata filtering and persistence.
- Weaviate: Full-featured but heavyweight for this use case.

### 2.3 Chunking Strategy: Heading-Aware with Overlap

**Choice:** Section-based chunking with paragraph-level fallback and 50-character overlap

**Parameters:**
- `CHUNK_SIZE`: 512 characters
- `CHUNK_OVERLAP`: 50 characters

**Why:**
- **Heading-aware:** Splits on markdown headings (`##`) to preserve semantic coherence within chunks. Policy documents have clear section structure, and keeping sections intact improves retrieval quality.
- **Overlap:** 50-character overlap ensures context isn't lost at chunk boundaries. This is especially important for policies where a key detail might span paragraph boundaries.
- **512-char size:** Balances between having enough context for meaningful retrieval and keeping chunks focused enough to be relevant. Larger chunks (1000+) would dilute relevance scores; smaller chunks (<200) would lose context.

**Alternatives considered:**
- Fixed token windows (e.g., 256 tokens): Simpler but ignores document structure.
- Recursive character splitting (LangChain default): Generic but doesn't leverage the heading structure of policy documents.
- Sentence-level splitting: Too granular for policy documents.

### 2.4 LLM: Google Gemini 2.0 Flash (via OpenRouter Free Tier)

**Choice:** `google/gemini-2.0-flash-exp:free` via OpenRouter API

**Why:**
- **Cost:** Free tier on OpenRouter — no charges for inference.
- **Quality:** Gemini 2.0 Flash offers strong instruction-following and factual accuracy.
- **Speed:** Flash models are optimized for low latency.
- **Context window:** Large context window (1M tokens) easily handles retrieved chunks.
- **OpenRouter:** Single API interface with fallback to many models if one is unavailable.

**Alternatives considered:**
- OpenAI GPT-4o-mini: Excellent quality but not free.
- Meta Llama 3: Available free on some platforms but variable availability.
- Local LLM (Ollama): No API cost but requires significant compute resources.

### 2.5 Retrieval: Top-K with Cross-Encoder Re-ranking

**Choice:** Top-15 retrieval → Cross-encoder re-ranking → Top-5 results

**Why:**
- **Two-stage retrieval:** Bi-encoder (sentence-transformers) for fast initial recall, then cross-encoder for precise re-ranking. This combines speed with accuracy.
- **Re-ranker model:** `cross-encoder/ms-marco-MiniLM-L-6-v2` — specifically trained for passage ranking on MS MARCO dataset. Free and runs locally.
- **K=5:** Provides enough context for the LLM without overwhelming the prompt. Testing showed diminishing returns beyond 5 chunks for this corpus.
- **Over-fetch 3x:** Retrieving 15 candidates and re-ranking to 5 gives the re-ranker enough candidates to improve precision significantly.

### 2.6 Prompt Engineering & Guardrails

**Design:**
- **System prompt:** Establishes the assistant's role, scope limitations, and citation requirements.
- **Guardrails implemented:**
  1. Pre-filter: Lightweight keyword check rejects obviously off-topic queries before hitting the LLM.
  2. System prompt instruction: "ONLY answer questions related to company policies."
  3. Citation requirement: "ALWAYS cite the specific policy document(s)."
  4. Output length limit: `MAX_OUTPUT_TOKENS=500` prevents runaway generation.
  5. Low temperature: `temperature=0.1` for factual, deterministic responses.
- **Context injection:** Retrieved chunks are formatted with source labels `[Source N: Title (DocID)]` to make citation easy for the LLM.

### 2.7 Web Framework: Flask

**Choice:** Flask with vanilla HTML/CSS/JS frontend

**Why:**
- **Simplicity:** Lightweight, well-documented, minimal boilerplate.
- **Flexibility:** Easy to add API endpoints alongside HTML views.
- **No frontend build step:** Single HTML file with embedded CSS/JS — no npm/webpack needed.
- **Production-ready:** Works well with Gunicorn for deployment.

**Alternatives considered:**
- Streamlit: Faster prototyping but less control over the API layer and UI.
- FastAPI: Great for APIs but the assignment specifically mentioned Flask as an option.
- Django: Too heavyweight for this application.

---

## 3. Evaluation Approach

### 3.1 Evaluation Set

- **25 questions** covering all 15 policy documents.
- Topics: PTO, holidays, remote work, expenses, security, code of conduct, performance reviews, onboarding/offboarding, acceptable use, health & safety, benefits, data privacy, travel, intellectual property, DEI.
- Each question has an expected answer and the relevant document IDs for citation accuracy checking.

### 3.2 Metrics

#### Answer Quality (Required)

1. **Groundedness (%):** Percentage of answers whose content is factually consistent with and fully supported by the retrieved evidence. Evaluated using LLM-as-judge — the same LLM evaluates whether each claim in the answer is supported by the retrieved passages.

2. **Citation Accuracy (%):** Percentage of answers whose listed citations correctly point to the specific document(s) that contain the answer. Evaluated by comparing cited document IDs against the expected relevant document IDs.

3. **Partial Match (%) (Optional):** Percentage of answers that contain key phrases from the expected gold answer. Uses substring matching on normalized text.

#### System Metrics (Required)

1. **Latency:**
   - **p50 (median):** Typical response time.
   - **p95:** Worst-case response time for 95% of queries.
   - Measured end-to-end from question receipt to answer delivery.
   - Broken down into retrieval latency and generation latency.

### 3.3 Evaluation Results

Results are generated by running the evaluation script (`python run.py --evaluate`) and saved to `evaluation/eval_results.json`. See the evaluation results file for detailed per-question metrics.

**Summary of results** (run the evaluation to get current numbers):
- Groundedness: Measures factual consistency between answer and retrieved evidence.
- Citation Accuracy: Measures correct attribution to source policy documents.
- Latency: End-to-end response time including retrieval, re-ranking, and LLM generation.

---

## 4. Potential Improvements

1. **Hybrid search:** Combine vector search with BM25 keyword search for better recall.
2. **Conversation memory:** Add multi-turn conversation support with chat history.
3. **Streaming responses:** Use SSE to stream LLM responses for better UX.
4. **Fine-tuned embeddings:** Fine-tune the embedding model on policy-specific queries.
5. **Caching:** Cache frequent queries to reduce latency and API costs.
6. **Feedback loop:** Add thumbs up/down to collect user feedback for evaluation.
7. **Multi-format support:** Add PDF and HTML parsing for broader document support.
