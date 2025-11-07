#!/usr/bin/env python3
"""
Prometheus → Elasticsearch Bridge
Pulls metrics from /metrics endpoints and pushes to Elasticsearch every few seconds.
"""

import requests, time, re, json
from datetime import datetime

PROM_ENDPOINTS = [
    "http://localhost:8000/metrics",  # rag_ingest
    "http://localhost:8011/metrics",  # rag_query
]

ELASTIC_URL = "http://localhost:9200/rag_metrics/_doc"

def parse_prometheus_metrics(text):
    """Parse Prometheus metrics text into a dictionary."""
    metrics = {}
    for line in text.splitlines():
        if line.startswith("#") or "{" in line:
            continue
        parts = line.strip().split()
        if len(parts) == 2:
            name, value = parts
            try:
                metrics[name] = float(value)
            except ValueError:
                pass
    return metrics

def push_to_elasticsearch(service_name, metrics):
    """Push metrics into Elasticsearch."""
    payload = {
        "@timestamp": datetime.utcnow().isoformat(),
        "service": service_name,
        "metrics": metrics,
    }
    try:
        res = requests.post(ELASTIC_URL, json=payload, timeout=5)
        if res.status_code in (200, 201):
            print(f"✅ Pushed metrics for {service_name}")
        else:
            print(f"⚠️ ES push failed ({res.status_code}): {res.text[:120]}")
    except Exception as e:
        print(f"⚠️ Failed to push to ES: {e}")

def main():
    print("🔁 Prometheus → Elasticsearch bridge running...")
    while True:
        for url in PROM_ENDPOINTS:
            service_name = url.split(":")[2].split("/")[0]
            try:
                r = requests.get(url, timeout=5)
                if r.status_code == 200:
                    metrics = parse_prometheus_metrics(r.text)
                    push_to_elasticsearch(service_name, metrics)
                else:
                    print(f"⚠️ Cannot fetch from {url}: {r.status_code}")
            except Exception as e:
                print(f"⚠️ Error fetching {url}: {e}")
        time.sleep(10)  # refresh every 10s

if __name__ == "__main__":
    main()
