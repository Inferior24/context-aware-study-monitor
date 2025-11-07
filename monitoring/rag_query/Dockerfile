FROM python:3.11-slim
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY rag_query.py .
EXPOSE 8001

CMD ["python", "rag_query.py"]
