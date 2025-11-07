with open("mock_metrics.json", "r", encoding="utf-8") as f:
    content = f.read()

print("File length:", len(content))
print("First 200 chars:", content[:200])
