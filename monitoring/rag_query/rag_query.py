#!/usr/bin/env python3
"""
Autonomous RAG Query Service (fixed)
- Loads FAISS index and metadata
- Retrieves top-K document chunks per query
- Uses local Ollama model for contextual answers
- Exposes Prometheus metrics at /metrics (same port as API)
- Logs query performance + results to Elasticsearch (with small retries)
"""

import os
import json
import time
import faiss
import numpy as np
import requests
from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse, Response
from sentence_transformers import SentenceTransformer
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
import uvicorn
from datetime import datetime
from typing import Any


# Paths & Constants

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_FILE = os.path.join(BASE_DIR, "vector_index.faiss")
META_FILE = os.path.join(BASE_DIR, "metadata.json")
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
OLLAMA_MODEL = "llama3"
APP_PORT = 8011
TOP_K = 3

# Elasticsearch: index and document endpoint
ELASTIC_INDEX = "rag_queries"
ELASTIC_INDEX_URL = f"http://host.docker.internal:9200/{ELASTIC_INDEX}"

ELASTIC_DOC_URL = f"{ELASTIC_INDEX_URL}/_doc"


# Prometheus Metrics

rag_queries_total = Counter("rag_queries_total", "Total number of RAG queries processed", ["status"])
rag_retrieval_time = Histogram("rag_retrieval_time_seconds", "Time taken for document retrieval")
rag_generation_time = Histogram("rag_generation_time_seconds", "Time taken for LLM generation")
faiss_index_size = Counter("rag_faiss_index_vectors", "Number of vectors in the FAISS index")


# FastAPI App

app = FastAPI(
    title="RAG Query API",
    description="Query your documents using FAISS + Ollama + Elasticsearch + Prometheus",
    version="2.2"
)


# Ensure Elasticsearch index exists (mapping)

DEFAULT_MAPPING = {
    "mappings": {
        "properties": {
            "@timestamp": {"type": "date"},
            "query": {"type": "text", "fields": {"keyword": {"type": "keyword"}}},
            "response": {"type": "text"},
            "retrieval_time": {"type": "float"},
            "generation_time": {"type": "float"},
            "status": {"type": "keyword"},
            "source": {"type": "keyword"}
        }
    }
}


def ensure_elastic_index(timeout: float = 3.0) -> bool:
    
    try:
        r = requests.get(ELASTIC_INDEX_URL, timeout=timeout)
        if r.status_code == 200:
            print(f"✅ Elasticsearch index '{ELASTIC_INDEX}' exists.")
            return True
    except requests.exceptions.RequestException:
        
        pass

    try:
        r = requests.put(ELASTIC_INDEX_URL, json=DEFAULT_MAPPING, timeout=timeout)
        if r.status_code in (200, 201):
            print(f"✅ Created Elasticsearch index '{ELASTIC_INDEX}'.")
            return True
        else:
            print(f"⚠️ Failed to create index '{ELASTIC_INDEX}': {r.status_code} {r.text}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"⚠️ Could not reach Elasticsearch to create index '{ELASTIC_INDEX}': {e}")
        return False



# Initialization

print("🧠 Loading model and FAISS index...")

_elastic_ready = ensure_elastic_index()


model = SentenceTransformer(MODEL_NAME)
if not os.path.exists(INDEX_FILE) or not os.path.exists(META_FILE):
    raise FileNotFoundError("❌ Missing FAISS index or metadata.json. Run rag_ingest.py first.")

index = faiss.read_index(INDEX_FILE)
with open(META_FILE, "r", encoding="utf-8") as f:
    metadata = json.load(f)
print(f"✅ Loaded index with {index.ntotal} vectors and {len(metadata)} metadata entries.")

try:
    faiss_index_size.inc(int(index.ntotal))
except Exception:
    faiss_index_size.inc()


# Ollama Interaction Helper

def run_ollama(prompt: str) -> str:
    """
    Query the local Ollama server through its HTTP API (streaming).
    Returns full response string or an error string.
    """
    try:
        resp = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": OLLAMA_MODEL,
                "prompt": prompt,
                "options": {"num_predict": 400, "temperature": 0.8, "top_p": 0.9}
            },
            timeout=90,
            stream=True
        )
        resp.raise_for_status()

        parts = []
        for line in resp.iter_lines(decode_unicode=True):
            if not line:
                continue
            
            try:
                data = json.loads(line)
            except Exception:
                continue
            if isinstance(data, dict):
                chunk = data.get("response", "")
                if chunk:
                    parts.append(chunk)
                if data.get("done"):
                    break

        full = "".join(parts).strip()
        return full if full else "[No response]"

    except requests.exceptions.RequestException as e:
        return f"[Ollama HTTP call failed: {e}]"
    except Exception as e:
        return f"[Ollama parse failed: {e}]"



# Elasticsearch Logging Helper (with retries)

def _post_json_with_retries(url: str, payload: Any, attempts: int = 3, backoff: float = 0.5) -> requests.Response:
    last_exc = None
    for i in range(attempts):
        try:
            res = requests.post(url, headers={"Content-Type": "application/json"}, data=json.dumps(payload), timeout=5)
            return res
        except Exception as e:
            last_exc = e
            time.sleep(backoff * (i + 1))
    raise last_exc


def log_to_elasticsearch(q: str, answer: str, retrieval_time: float, gen_time: float, status: str = "success") -> None:
    """Log RAG query details into Elasticsearch (best-effort with retries)."""
    log_entry = {
        "@timestamp": datetime.utcnow().isoformat(),
        "query": q,
        "response": answer[:1000],  # truncate to avoid insanely large docs
        "retrieval_time": round(retrieval_time, 3),
        "generation_time": round(gen_time, 3),
        "status": status,
        "source": "rag_query"
    }

    print("\n🧾 [DEBUG] Attempting to send log to Elasticsearch...")
    print("🧾 [DEBUG] URL:", ELASTIC_DOC_URL)
    
    print("🧾 [DEBUG] Payload preview:", json.dumps(log_entry, indent=2)[:500])

    try:
        res = _post_json_with_retries(ELASTIC_DOC_URL, log_entry, attempts=3, backoff=0.5)
        print("🧾 [DEBUG] Elasticsearch response:", res.status_code)
        if res.status_code in (200, 201):
            print("✅ Successfully logged query to Elasticsearch.")
        else:
            print(f"⚠️ Failed to log. Status: {res.status_code} -> {res.text[:300]}")
    except Exception as e:
        print(f"🚨 Logging failed after retries: {e}")



# Core Retrieval + Generation Endpoint

@app.get("/query")
def query_docs(q: str = Query(..., description="User question")):
    print(f"\n🔎 Received query: {q}")
    start_retrieval = time.time()

    try:
        
        emb = model.encode(q, convert_to_numpy=True).astype("float32")
        faiss.normalize_L2(emb.reshape(1, -1))
        scores, idxs = index.search(emb.reshape(1, -1), TOP_K)
        retrieval_time = time.time() - start_retrieval
        rag_retrieval_time.observe(retrieval_time)

        contexts = [metadata[i]["text"] for i in idxs[0] if i < len(metadata)]
        context_combined = "\n\n".join(contexts)
        print(f"📚 Retrieved {len(contexts)} chunks in {retrieval_time:.3f}s")

        
        start_gen = time.time()
        prompt = (
            "You are a helpful assistant.\n"
            f"Context:\n{context_combined}\n\n"
            f"Question: {q}\n\n"
            "Answer concisely and factually using only the context above."
        )
        answer = run_ollama(prompt)
        gen_time = time.time() - start_gen
        rag_generation_time.observe(gen_time)
        rag_queries_total.labels(status="success").inc()

        print(f"💬 Response generated in {gen_time:.3f}s")

        
        try:
            log_to_elasticsearch(q, answer, retrieval_time, gen_time, status="success")
        except Exception as e:
            print(f"⚠️ Logging attempt raised (shouldn't stop response): {e}")

        
        return JSONResponse({
            "query": q,
            "response": answer,
            "retrieval_time": round(retrieval_time, 3),
            "generation_time": round(gen_time, 3),
            "context_used": contexts,
        })

    except Exception as e:
        rag_queries_total.labels(status="error").inc()
        try:
            log_to_elasticsearch(q, str(e), 0.0, 0.0, status="error")
        except Exception:
            pass
        return JSONResponse({"error": str(e)}, status_code=500)



# Prometheus Metrics Endpoint

@app.get("/metrics")
def metrics():
    """Expose Prometheus metrics."""
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)



# Entrypoint

if __name__ == "__main__":
    print(f"🚀 RAG Query API running on http://localhost:{APP_PORT}")
    print(f"📡 Metrics exposed at http://localhost:{APP_PORT}/metrics")
    uvicorn.run(app, host="0.0.0.0", port=APP_PORT)
