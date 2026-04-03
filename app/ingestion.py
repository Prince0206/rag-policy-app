"""Document ingestion and indexing module.

Handles parsing, cleaning, chunking, embedding, and storing documents
in the ChromaDB vector database.
"""

import hashlib
import os
import re

import chromadb
import markdown
from bs4 import BeautifulSoup
from sentence_transformers import SentenceTransformer

from app.config import (
    CHUNK_OVERLAP,
    CHUNK_SIZE,
    CHROMA_PERSIST_DIR,
    COLLECTION_NAME,
    DOCUMENTS_DIR,
    EMBEDDING_MODEL,
    RANDOM_SEED,
)


def parse_markdown(file_path: str) -> dict:
    """Parse a markdown file and extract text content and metadata."""
    with open(file_path, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Extract document metadata from the header
    title = ""
    doc_id = ""
    department = ""

    lines = raw_text.split("\n")
    for line in lines:
        if line.startswith("# ") and not title:
            title = line.replace("# ", "").strip()
        if "**Document ID:**" in line:
            doc_id = line.split("**Document ID:**")[1].strip()
        if "**Department:**" in line:
            department = line.split("**Department:**")[1].strip()

    # Convert markdown to HTML then extract plain text
    html = markdown.markdown(raw_text, extensions=["tables", "fenced_code"])
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(separator="\n")

    # Clean up whitespace
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.strip()

    return {
        "text": text,
        "title": title,
        "doc_id": doc_id,
        "department": department,
        "source_file": os.path.basename(file_path),
    }


def parse_text_file(file_path: str) -> dict:
    """Parse a plain text file."""
    with open(file_path, "r", encoding="utf-8") as f:
        text = f.read().strip()

    return {
        "text": text,
        "title": os.path.splitext(os.path.basename(file_path))[0],
        "doc_id": "",
        "department": "",
        "source_file": os.path.basename(file_path),
    }


def parse_document(file_path: str) -> dict:
    """Parse a document based on its file extension."""
    ext = os.path.splitext(file_path)[1].lower()
    if ext == ".md":
        return parse_markdown(file_path)
    elif ext == ".txt":
        return parse_text_file(file_path)
    else:
        raise ValueError(f"Unsupported file type: {ext}")


def chunk_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    """Split text into overlapping chunks by character count with section awareness.

    Uses heading-based splitting when possible, falling back to paragraph-based
    splitting with overlap for long sections.
    """
    # Split by sections (headings)
    sections = re.split(r"\n(?=##?\s)", text)
    chunks = []

    for section in sections:
        section = section.strip()
        if not section:
            continue

        if len(section) <= chunk_size:
            chunks.append(section)
        else:
            # Split long sections into overlapping chunks by paragraphs
            paragraphs = section.split("\n\n")
            current_chunk = ""

            for paragraph in paragraphs:
                paragraph = paragraph.strip()
                if not paragraph:
                    continue

                if len(current_chunk) + len(paragraph) + 2 <= chunk_size:
                    current_chunk = (current_chunk + "\n\n" + paragraph).strip()
                else:
                    if current_chunk:
                        chunks.append(current_chunk)
                        # Keep overlap from the end of the previous chunk
                        overlap_text = current_chunk[-overlap:] if overlap > 0 else ""
                        current_chunk = (overlap_text + "\n\n" + paragraph).strip()
                    else:
                        # Single paragraph is larger than chunk_size, split by sentences
                        sentences = re.split(r"(?<=[.!?])\s+", paragraph)
                        for sentence in sentences:
                            if len(current_chunk) + len(sentence) + 1 <= chunk_size:
                                current_chunk = (current_chunk + " " + sentence).strip()
                            else:
                                if current_chunk:
                                    chunks.append(current_chunk)
                                current_chunk = sentence

            if current_chunk:
                chunks.append(current_chunk)

    return chunks


def generate_chunk_id(doc_id: str, chunk_index: int, chunk_text: str) -> str:
    """Generate a deterministic ID for a chunk."""
    content_hash = hashlib.md5(chunk_text.encode()).hexdigest()[:8]
    return f"{doc_id}_chunk_{chunk_index}_{content_hash}"


def load_embedding_model() -> SentenceTransformer:
    """Load the sentence transformer embedding model."""
    model = SentenceTransformer(EMBEDDING_MODEL)
    return model


def build_index(documents_dir: str = DOCUMENTS_DIR, persist_dir: str = CHROMA_PERSIST_DIR) -> chromadb.Collection:
    """Build the vector index from all documents in the documents directory.

    Steps:
    1. Parse all supported documents
    2. Chunk each document
    3. Generate embeddings using sentence-transformers
    4. Store in ChromaDB with metadata
    """
    # Initialize embedding model
    model = load_embedding_model()

    # Initialize ChromaDB
    client = chromadb.PersistentClient(path=persist_dir)

    # Delete existing collection if it exists (for rebuilding)
    try:
        client.delete_collection(COLLECTION_NAME)
    except ValueError:
        pass

    collection = client.create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )

    all_chunks = []
    all_ids = []
    all_metadatas = []
    all_embeddings = []

    # Process each document
    supported_extensions = {".md", ".txt"}
    doc_files = sorted([
        f for f in os.listdir(documents_dir)
        if os.path.splitext(f)[1].lower() in supported_extensions
    ])

    print(f"Processing {len(doc_files)} documents...")

    for file_name in doc_files:
        file_path = os.path.join(documents_dir, file_name)
        print(f"  Parsing: {file_name}")

        doc = parse_document(file_path)
        chunks = chunk_text(doc["text"])

        print(f"    Generated {len(chunks)} chunks")

        for i, chunk in enumerate(chunks):
            doc_id = doc["doc_id"] if doc["doc_id"] else file_name
            chunk_id = generate_chunk_id(doc_id, i, chunk)

            all_chunks.append(chunk)
            all_ids.append(chunk_id)
            all_metadatas.append({
                "source_file": doc["source_file"],
                "doc_id": doc["doc_id"],
                "title": doc["title"],
                "department": doc["department"],
                "chunk_index": i,
                "total_chunks": len(chunks),
            })

    # Generate embeddings in batch
    print(f"Generating embeddings for {len(all_chunks)} chunks...")
    embeddings = model.encode(all_chunks, show_progress_bar=True, seed=RANDOM_SEED)
    all_embeddings = embeddings.tolist()

    # Add to ChromaDB in batches (ChromaDB has a batch limit)
    batch_size = 100
    for i in range(0, len(all_chunks), batch_size):
        end = min(i + batch_size, len(all_chunks))
        collection.add(
            ids=all_ids[i:end],
            embeddings=all_embeddings[i:end],
            documents=all_chunks[i:end],
            metadatas=all_metadatas[i:end],
        )

    print(f"Index built successfully with {collection.count()} chunks.")
    return collection


def get_collection(persist_dir: str = CHROMA_PERSIST_DIR) -> chromadb.Collection:
    """Get the existing ChromaDB collection."""
    client = chromadb.PersistentClient(path=persist_dir)
    return client.get_collection(name=COLLECTION_NAME)


if __name__ == "__main__":
    build_index()
    print("Indexing complete!")
