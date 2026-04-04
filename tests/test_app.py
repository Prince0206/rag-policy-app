"""Tests for the RAG Policy Assistant application."""

import json
import os
import sys

import pytest

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.config import CHUNK_OVERLAP, CHUNK_SIZE, DOCUMENTS_DIR
from app.generator import is_policy_question
from app.ingestion import chunk_text, parse_markdown


class TestConfig:
    """Test configuration loading."""

    def test_chunk_size_is_positive(self):
        assert CHUNK_SIZE > 0

    def test_chunk_overlap_less_than_size(self):
        assert CHUNK_OVERLAP < CHUNK_SIZE

    def test_documents_dir_exists(self):
        assert os.path.isdir(DOCUMENTS_DIR)


class TestIngestion:
    """Test document parsing and chunking."""

    def test_parse_markdown_basic(self):
        """Test parsing a markdown policy document."""
        # Use the first policy document
        doc_path = os.path.join(DOCUMENTS_DIR, "01-pto-leave-policy.md")
        if os.path.exists(doc_path):
            result = parse_markdown(doc_path)
            assert "text" in result
            assert "title" in result
            assert "doc_id" in result
            assert result["title"] != ""
            assert result["doc_id"] == "POL-001"
            assert len(result["text"]) > 100

    def test_parse_markdown_extracts_metadata(self):
        """Test that metadata extraction works correctly."""
        doc_path = os.path.join(DOCUMENTS_DIR, "05-information-security.md")
        if os.path.exists(doc_path):
            result = parse_markdown(doc_path)
            assert result["doc_id"] == "POL-005"
            assert "Information Technology" in result["department"]

    def test_chunk_text_produces_chunks(self):
        """Test that chunking produces non-empty chunks."""
        text = "Section 1\n\nThis is a paragraph.\n\n## Section 2\n\nAnother paragraph."
        chunks = chunk_text(text, chunk_size=100, overlap=10)
        assert len(chunks) > 0
        for chunk in chunks:
            assert len(chunk) > 0

    def test_chunk_text_respects_size(self):
        """Test that chunks generally respect the size limit."""
        long_text = "\n\n".join([f"Paragraph {i}. " * 10 for i in range(50)])
        chunks = chunk_text(long_text, chunk_size=200, overlap=20)
        # Most chunks should be within a reasonable size
        for chunk in chunks:
            # Allow some tolerance for section-based splitting
            assert len(chunk) < 1000

    def test_chunk_text_handles_empty_input(self):
        """Test chunking with empty input."""
        chunks = chunk_text("")
        assert len(chunks) == 0

    def test_chunk_text_handles_short_input(self):
        """Test chunking with input shorter than chunk size."""
        text = "This is a short text."
        chunks = chunk_text(text, chunk_size=1000)
        assert len(chunks) == 1
        assert chunks[0] == text

    def test_all_documents_parseable(self):
        """Test that all markdown documents in the documents directory can be parsed."""
        for filename in sorted(os.listdir(DOCUMENTS_DIR)):
            if filename.endswith(".md"):
                doc_path = os.path.join(DOCUMENTS_DIR, filename)
                result = parse_markdown(doc_path)
                assert result["text"], f"Empty text for {filename}"
                assert result["title"], f"No title for {filename}"


class TestGenerator:
    """Test the generator module."""

    def test_policy_question_detection_positive(self):
        """Test that policy-related questions are detected."""
        assert is_policy_question("What is the PTO policy?") is True
        assert is_policy_question("How many sick days do I get?") is True
        assert is_policy_question("What are the company holidays?") is True
        assert is_policy_question("How do I submit expenses?") is True

    def test_policy_question_detection_negative(self):
        """Test that off-topic questions are filtered."""
        assert is_policy_question("What is the weather today?") is False
        assert is_policy_question("Tell me a joke") is False
        assert is_policy_question("") is False
        assert is_policy_question("ab") is False

    def test_policy_question_edge_cases(self):
        """Test edge cases for policy question detection."""
        # These should pass since they could be policy-related
        assert is_policy_question("Can I work from home?") is True
        assert is_policy_question("What is my salary?") is True


class TestWebApp:
    """Test Flask web application endpoints."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        from app.web import create_app
        app = create_app()
        app.config["TESTING"] = True
        with app.test_client() as client:
            yield client

    def test_health_endpoint(self, client):
        """Test the /health endpoint returns correct JSON."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert data["service"] == "RAG Policy Assistant"
        assert "version" in data
        assert "timestamp" in data

    def test_index_page(self, client):
        """Test the / endpoint serves the chat interface."""
        response = client.get("/")
        assert response.status_code == 200
        assert b"Acme Corp Policy Assistant" in response.data

    def test_chat_endpoint_missing_question(self, client):
        """Test /chat with missing question field."""
        response = client.post(
            "/chat",
            data=json.dumps({}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_chat_endpoint_empty_question(self, client):
        """Test /chat with empty question."""
        response = client.post(
            "/chat",
            data=json.dumps({"question": "   "}),
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_chat_endpoint_too_long_question(self, client):
        """Test /chat with excessively long question."""
        response = client.post(
            "/chat",
            data=json.dumps({"question": "x" * 1001}),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "too long" in data["error"].lower()
