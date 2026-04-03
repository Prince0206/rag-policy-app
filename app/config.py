"""Configuration module for the RAG Policy Assistant."""

import os
import random

import numpy as np
from dotenv import load_dotenv

load_dotenv()

# Fixed seeds for reproducibility
RANDOM_SEED = 42
random.seed(RANDOM_SEED)
np.random.seed(RANDOM_SEED)

# OpenRouter API configuration
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
LLM_MODEL = os.getenv("LLM_MODEL", "google/gemini-2.0-flash-exp:free")

# Embedding model configuration (local, free via sentence-transformers)
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2")

# Retrieval configuration
RETRIEVAL_TOP_K = int(os.getenv("RETRIEVAL_TOP_K", "5"))
CHUNK_SIZE = int(os.getenv("CHUNK_SIZE", "512"))
CHUNK_OVERLAP = int(os.getenv("CHUNK_OVERLAP", "50"))

# App configuration
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key-change-in-production")
MAX_OUTPUT_TOKENS = int(os.getenv("MAX_OUTPUT_TOKENS", "500"))

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCUMENTS_DIR = os.path.join(BASE_DIR, "documents")
CHROMA_PERSIST_DIR = os.path.join(BASE_DIR, "chroma_db")

# ChromaDB collection name
COLLECTION_NAME = "policy_documents"
