import json
import requests

ES_URL = "http://localhost:9200/prometheus_bridge/_bulk"
FILE = "mock_metrics.json"

with open(FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

# Prepare NDJSON bulk body
bulk_lines = []
for doc in data:
    bulk_lines.append(json.dumps({"index": {"_index": "prometheus_bridge"}}))
    bulk_lines.append(json.dumps(doc))
bulk_body = "\n".join(bulk_lines) + "\n"

r = requests.post(ES_URL, data=bulk_body, headers={"Content-Type": "application/x-ndjson"})

print("Status:", r.status_code)
print("Response:", r.text[:500])
