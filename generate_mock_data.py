import json, random
from datetime import datetime, timedelta

data = []
now = datetime.utcnow()

metrics = [
    "rag_ingested_docs_total",
    "rag_index_size",
    "rag_queries_total",
    "rag_retrieval_time_seconds",
    "rag_generation_time_seconds"
]

for i in range(0, 120):  # 120 data points (last 2 hours if spaced 1 min apart)
    ts = now - timedelta(minutes=(120 - i))
    for metric in metrics:
        data.append({
            "@timestamp": ts.isoformat() + "Z",
            "metric": metric,
            "value": round(random.uniform(0.1, 100.0), 2),
            "labels": {"job": "rag_system", "instance": "host.docker.internal:8000"}
        })

with open("mock_metrics.json", "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)

print(f"✅ Generated {len(data)} mock metric points.")
