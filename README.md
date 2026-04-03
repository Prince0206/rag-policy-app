# RAG Policy Assistant

A Retrieval-Augmented Generation (RAG) application that answers questions about Acme Corporation's company policies and procedures. Built with Flask, ChromaDB, Sentence-Transformers, and OpenRouter (Google Gemini).

## Features

- **Intelligent Q&A:** Ask natural language questions about company policies and get accurate, cited answers.
- **Citation Support:** Every answer includes source document references and relevant snippets.
- **Guardrails:** Refuses to answer out-of-scope questions; always cites sources; limits output length.
- **Web Interface:** Clean chat UI with sample questions and expandable retrieved passages.
- **REST API:** JSON API endpoint for programmatic access.
- **Evaluation Suite:** 25-question evaluation set measuring groundedness, citation accuracy, and latency.
- **CI/CD:** GitHub Actions workflow for automated build and test checks.

## Architecture

```
User Question -> Embed (MiniLM) -> ChromaDB Search -> Re-rank (Cross-Encoder) -> LLM (Gemini) -> Answer + Citations
```

| Component        | Technology                              | Cost    |
|------------------|-----------------------------------------|---------|
| Embeddings       | sentence-transformers/all-MiniLM-L6-v2  | Free    |
| Re-ranker        | cross-encoder/ms-marco-MiniLM-L-6-v2    | Free    |
| Vector Store     | ChromaDB (local persistent)             | Free    |
| LLM              | Google Gemini 2.0 Flash via OpenRouter   | Free    |
| Web Framework    | Flask                                   | Free    |

## Quick Start

### Prerequisites

- Python 3.10+
- An OpenRouter API key ([get one free](https://openrouter.ai/keys))

### 1. Clone the Repository

```bash
git clone https://github.com/Prince0206/rag-policy-app.git
cd rag-policy-app
```

### 2. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
# Edit .env and add your OpenRouter API key
```

Set the `OPENROUTER_API_KEY` in your `.env` file:
```
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

### 5. Build the Document Index

```bash
python run.py --index
```

This parses all policy documents, chunks them, generates embeddings, and stores them in ChromaDB.

### 6. Start the Web Server

```bash
python run.py --serve
```

The application will be available at [http://localhost:5000](http://localhost:5000).

## Usage

### Web Interface

Navigate to `http://localhost:5000` to use the chat interface. Type your question or click a sample question to get started.

### API Endpoint

**POST** `/chat`

```bash
curl -X POST http://localhost:5000/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "How many PTO days do new employees get?"}'
```

**Response:**
```json
{
  "question": "How many PTO days do new employees get?",
  "answer": "New employees (0-2 years of service) receive 15 PTO days per year...",
  "citations": [
    {
      "doc_id": "POL-001",
      "title": "Paid Time Off (PTO) and Leave Policy",
      "source_file": "01-pto-leave-policy.md",
      "department": "Human Resources"
    }
  ],
  "snippets": ["..."],
  "latency_ms": 2345.67
}
```

### Health Check

**GET** `/health`

```bash
curl http://localhost:5000/health
```

Returns: `{"status": "healthy", "service": "RAG Policy Assistant", "version": "1.0.0"}`

## Running Evaluation

```bash
python run.py --evaluate
```

This runs 25 evaluation questions and reports:
- **Groundedness:** % of answers supported by retrieved evidence
- **Citation Accuracy:** % of correctly attributed source documents
- **Partial Match:** % of answers containing expected key phrases
- **Latency:** p50 and p95 response times

Results are saved to `evaluation/eval_results.json`.

## Running Tests

```bash
pytest tests/ -v
```

## Project Structure

```
rag-policy-app/
├── app/
│   ├── __init__.py          # Package initialization
│   ├── config.py            # Configuration and environment variables
│   ├── ingestion.py         # Document parsing, chunking, embedding, indexing
│   ├── retriever.py         # Top-k retrieval with cross-encoder re-ranking
│   ├── generator.py         # LLM interaction via OpenRouter with guardrails
│   ├── rag_pipeline.py      # Full RAG pipeline orchestration
│   └── web.py               # Flask web application
├── documents/               # Company policy documents (15 markdown files)
├── evaluation/
│   ├── eval_questions.json  # 25 evaluation questions with expected answers
│   └── evaluate.py          # Evaluation script (groundedness, citations, latency)
├── templates/
│   └── index.html           # Chat interface HTML
├── tests/
│   └── test_app.py          # Unit and integration tests
├── .github/workflows/
│   └── ci.yml               # GitHub Actions CI/CD pipeline
├── requirements.txt         # Python dependencies
├── run.py                   # CLI entry point
├── .env.example             # Example environment configuration
├── design-and-evaluation.md # Design decisions and evaluation documentation
├── ai-tooling.md            # AI tools used in development
└── README.md                # This file
```

## Policy Corpus

The application includes 15 synthetic company policy documents covering:

| Document | Topic |
|----------|-------|
| POL-001  | PTO and Leave Policy |
| POL-002  | Company Holidays |
| POL-003  | Remote Work and Flexible Work |
| POL-004  | Expense Reimbursement |
| POL-005  | Information Security |
| POL-006  | Code of Conduct and Ethics |
| POL-007  | Performance Management |
| POL-008  | Onboarding and Offboarding |
| POL-009  | Acceptable Use of Technology |
| POL-010  | Workplace Health and Safety |
| POL-011  | Benefits and Compensation |
| POL-012  | Data Privacy and Protection |
| POL-013  | Business Travel |
| POL-014  | Intellectual Property |
| POL-015  | Diversity, Equity, and Inclusion |

## Configuration

All configuration is done via environment variables (`.env` file):

| Variable            | Default                         | Description                    |
|---------------------|---------------------------------|--------------------------------|
| OPENROUTER_API_KEY  | (required)                      | OpenRouter API key             |
| LLM_MODEL           | google/gemini-2.0-flash-exp:free | LLM model identifier          |
| EMBEDDING_MODEL     | all-MiniLM-L6-v2                | Sentence transformer model     |
| RETRIEVAL_TOP_K     | 5                               | Number of chunks to retrieve   |
| CHUNK_SIZE          | 512                             | Maximum chunk size (chars)     |
| CHUNK_OVERLAP       | 50                              | Overlap between chunks (chars) |
| MAX_OUTPUT_TOKENS   | 500                             | Max LLM response tokens        |

## License

This project is for educational purposes.
