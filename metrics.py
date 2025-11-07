from prometheus_client import Counter, Histogram, Gauge, start_http_server
import atexit

# Define metrics
QUERIES_TOTAL = Counter('chatbot_queries_total', 'Total number of chatbot queries processed')
QUERY_DURATION = Histogram('chatbot_query_duration_seconds', 'Time taken per query')
EMBEDDING_TIME = Histogram('embedding_generation_seconds', 'Time taken to generate embeddings')
FILES_UPLOADED = Counter('files_uploaded_total', 'Total number of files uploaded')
ACTIVE_FILES = Gauge('active_files_count', 'Current active indexed files in FAISS')

def start_metrics_server(port=8000):
    start_http_server(port)
    print(f"✅ Prometheus metrics server running on http://localhost:{port}/metrics")

# Ensure cleanup
atexit.register(lambda: print("🔴 Metrics server stopped."))
