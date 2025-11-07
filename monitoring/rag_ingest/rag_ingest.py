#!/usr/bin/env python3
"""
robust rag_ingest.py
- Scans ./docs for .txt files
- Builds FAISS index + metadata.json
- Exposes Prometheus metrics at :8000/metrics
- Works from any directory (absolute paths)
"""

import os
import json
import time
import re
import numpy as np
from tqdm import tqdm
from sentence_transformers import SentenceTransformer
from prometheus_client import start_http_server, Counter, Gauge

try:
    import faiss
except ImportError:
    raise SystemExit("❌ FAISS not installed. Run: pip install faiss-cpu")


# Directories and constants

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
INDEX_FILE = os.path.join(BASE_DIR, "vector_index.faiss")
META_FILE = os.path.join(BASE_DIR, "metadata.json")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
PROM_PORT = 8000
CHUNK_SIZE = 400


# Prometheus Metrics

rag_ingested_chunks_total = Counter(
    "rag_ingested_chunks_total", "Total document chunks ingested"
)
rag_index_size = Gauge(
    "rag_index_size", "Number of vectors currently in FAISS index"
)
rag_last_index_unix = Gauge(
    "rag_last_index_unix", "Unix timestamp of last index update"
)


# Helper Functions

def ensure_docs_dir():
    os.makedirs(DOCS_DIR, exist_ok=True)
    txts = [f for f in os.listdir(DOCS_DIR) if f.endswith(".txt")]
    if not txts:
        print(f"⚠️ No .txt files found in {DOCS_DIR}. Please add text files and re-run.")
        time.sleep(5)
        return False
    return True

def read_text_files():
    """Read all .txt files from docs folder"""
    texts = []
    for file_name in sorted(os.listdir(DOCS_DIR)):
        if file_name.endswith(".txt"):
            with open(os.path.join(DOCS_DIR, file_name), "r", encoding="utf-8") as f:
                texts.append((file_name, f.read()))
    return texts

def chunk_text(text, size=CHUNK_SIZE):
    """Split text into fixed-length word chunks"""
    words = text.split()
    for i in range(0, len(words), size):
        yield " ".join(words[i:i + size])


# Core Ingestion Logic

def build_index_once():
    if not ensure_docs_dir():
        return

    print(f"📚 Loading model: {MODEL_NAME}")
    model = SentenceTransformer(MODEL_NAME)

    docs = read_text_files()
    if not docs:
        print("⚠️ No text documents found. Exiting.")
        return

    print(f"🔍 Building FAISS index from {len(docs)} files...")
    all_embeddings = []
    metadata = []

    for file_name, content in tqdm(docs, desc="Processing"):
        for chunk in chunk_text(content):
            emb = model.encode(chunk, convert_to_numpy=True)
            all_embeddings.append(emb)
            metadata.append({
                "file": file_name,
                "text": chunk[:300] + ("..." if len(chunk) > 300 else "")
            })
            rag_ingested_chunks_total.inc()

    emb_matrix = np.array(all_embeddings, dtype=np.float32)
    faiss.normalize_L2(emb_matrix)

    index = faiss.IndexFlatIP(emb_matrix.shape[1])
    index.add(emb_matrix)
    faiss.write_index(index, INDEX_FILE)

    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2)

    rag_index_size.set(len(all_embeddings))
    rag_last_index_unix.set(time.time())

    print(f"✅ Indexed {len(all_embeddings)} chunks across {len(docs)} documents.")
    print(f"📦 Saved index: {INDEX_FILE}")
    print(f"🧾 Saved metadata: {META_FILE}")


# Entrypoint

if __name__ == "__main__":
    print(f"🚀 Starting RAG ingestion + Prometheus exporter (port {PROM_PORT})")
    start_http_server(PROM_PORT, addr="0.0.0.0")

    try:
        build_index_once()
    except Exception as e:
        print(f"❌ Fatal error: {e}")

    print(f"📡 Metrics exposed at http://localhost:{PROM_PORT}/metrics")
    print("⏳ Waiting... (Press CTRL+C to exit)")
    while True:
        time.sleep(10)
