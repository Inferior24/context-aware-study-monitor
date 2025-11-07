import time
import requests
import json
from datetime import datetime

# === CONFIG ===
PROM = "http://localhost:9090"
ES = "http://localhost:9200"
INDEX = "prometheus_bridge"

HEADERS = {"Content-Type": "application/json"}

def fetch_metric_names():
    """Optional utility to list all metrics available in Prometheus"""
    try:
        r = requests.get(f"{PROM}/api/v1/label/__name__/values", timeout=10)
        r.raise_for_status()
        return r.json()["data"]
    except Exception as e:
        print("❌ Failed to fetch metric names:", e)
        return []

def query_instant(metric):
    """Fetch current value of metric (simpler, faster than range)"""
    try:
        r = requests.get(f"{PROM}/api/v1/query", params={"query": metric}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"❌ Query failed for {metric}:", e)
        return {}

def push_bulk_to_es(docs):
    """Efficient bulk insert to Elasticsearch"""
    if not docs:
        return
    bulk_data = ""
    for doc in docs:
        bulk_data += json.dumps({"index": {"_index": INDEX}}) + "\n"
        bulk_data += json.dumps(doc) + "\n"

    try:
        r = requests.post(f"{ES}/_bulk", data=bulk_data, headers={"Content-Type": "application/x-ndjson"}, timeout=15)
        if r.status_code not in (200, 201):
            print("⚠️ Elasticsearch bulk insert failed:", r.status_code, r.text[:300])
    except Exception as e:
        print("❌ Failed pushing to Elasticsearch:", e)

def run_once(metrics_list):
    """Fetch metrics from Prometheus and push to Elasticsearch"""
    doc
