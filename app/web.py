"""Flask web application for the RAG Policy Assistant.

Provides:
- / : Web chat interface
- /chat : API endpoint for questions (POST)
- /health : Health check endpoint (GET)
"""

import os
import time

from flask import Flask, jsonify, render_template, request

from app.config import SECRET_KEY

# Global pipeline instance (lazy-loaded)
_pipeline = None


def get_pipeline():
    """Lazy-load the RAG pipeline to avoid slow startup."""
    global _pipeline
    if _pipeline is None:
        from app.rag_pipeline import RAGPipeline
        _pipeline = RAGPipeline()
    return _pipeline


def create_app():
    """Create and configure the Flask application."""
    app = Flask(
        __name__,
        template_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "templates"),
        static_folder=os.path.join(os.path.dirname(os.path.dirname(__file__)), "static"),
    )
    app.secret_key = SECRET_KEY

    @app.route("/")
    def index():
        """Serve the web chat interface."""
        return render_template("index.html")

    @app.route("/chat", methods=["POST"])
    def chat():
        """API endpoint that receives user questions and returns answers with citations.

        Request body (JSON):
            {"question": "What is the PTO policy?"}

        Response (JSON):
            {
                "question": "...",
                "answer": "...",
                "citations": [...],
                "snippets": [...],
                "latency_ms": 1234.56
            }
        """
        data = request.get_json()

        if not data or "question" not in data:
            return jsonify({"error": "Missing 'question' field in request body"}), 400

        question = data["question"].strip()

        if not question:
            return jsonify({"error": "Question cannot be empty"}), 400

        if len(question) > 1000:
            return jsonify({"error": "Question too long (max 1000 characters)"}), 400

        pipeline = get_pipeline()
        result = pipeline.query(question)

        return jsonify(result)

    @app.route("/health", methods=["GET"])
    def health():
        """Health check endpoint returning simple JSON status."""
        return jsonify({
            "status": "healthy",
            "service": "RAG Policy Assistant",
            "version": "1.0.0",
            "timestamp": time.time(),
        })

    return app


# Application entry point
app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
