FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag_ingest.py .
EXPOSE 8000

CMD ["python", "rag_ingest.py"]
