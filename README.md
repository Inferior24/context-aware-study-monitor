# Tech Stack
- Docker
- Elasticsearch + Kibana + Prometheus + Grafana
- Python + FastAPI + LangChain
- Local LLM integration with Ollama (Llama3)

# Autonomous RAG Monitoring System

The **Autonomous RAG Monitoring System** is a context-aware architecture designed to intelligently manage, monitor, and analyze the performance of Retrieval-Augmented Generation (RAG) pipelines. It integrates vector-based retrieval, RESTful orchestration, and real-time observability through a unified system built with **FastAPI**, **FAISS**, **Elasticsearch**, **Kibana**, and **Prometheus**.

This project demonstrates a comprehensive implementation of how modern AI pipelines can achieve autonomy, scalability, and transparency using distributed monitoring and feedback-driven optimization.

---

## System Overview

The system is divided into two primary functional modules — **RAG Ingestion** and **RAG Query**, each managed as independent yet interconnected FastAPI microservices. These services are supported by a monitoring and analytics stack that ensures end-to-end visibility of data flow, query performance, and retrieval accuracy.

The architecture aims to transform static retrieval pipelines into self-observing systems that continuously evaluate and improve themselves using metric-based insights and elastic observability.

---

## Conceptual Workflow

The workflow of the Autonomous RAG Monitoring System can be divided into four major layers: **Ingestion**, **Retrieval**, **Monitoring**, and **Visualization**.

### 1. Ingestion Layer

The **RAG Ingestion Service** is responsible for processing raw text documents and preparing them for semantic retrieval.  
Its tasks include:
- Text preprocessing and chunking  
- Vectorization of document chunks using language model embeddings  
- Indexing and storage of vectors in a **FAISS** index for similarity search  
- Storing associated metadata (title, source, timestamp) for traceability  
- Logging ingestion events and operational metrics to Elasticsearch and Prometheus

This layer ensures that all data entering the system is structured, searchable, and observable from the moment it’s ingested.

---

### 2. Retrieval Layer

The **RAG Query Service** acts as the intelligent interface between the user and the retrieval engine.  
When a query request is received, the service:
- Accepts the user’s input query via a REST API endpoint  
- Embeds the query into a vector representation  
- Performs nearest-neighbor search using **FAISS** to retrieve top-k semantically relevant chunks  
- Retrieves metadata and context from the FAISS index  
- Passes results to a language model (or response synthesis layer) for contextually aware answer generation  
- Logs latency, hit-rate, and retrieval metrics for further analysis

By coupling FAISS with FastAPI, the query flow remains asynchronous, low-latency, and easily scalable.

---

### 3. Monitoring Layer

To ensure operational transparency and system reliability, a comprehensive monitoring layer is built using **Prometheus** and **Elasticsearch**.

- **Prometheus** collects quantitative system metrics such as:
  - API latency, response times, and error rates  
  - Number of retrieval calls per second  
  - Query cache hits and misses  
  - Document ingestion rate  
  - Resource utilization metrics  

  Each FastAPI endpoint exposes these metrics at a `/metrics` endpoint in Prometheus format.

- **Elasticsearch** stores structured logs and ingestion metadata for qualitative analysis and historical trend evaluation.  
  This enables queries such as:
  - "Which document sources produce the most retrieval hits?"  
  - "What query categories trigger slow responses?"  

Together, these monitoring tools create a feedback loop that transforms the RAG pipeline from a static retrieval system into an adaptive intelligence infrastructure.

---

### 4. Visualization Layer

The visualization layer is powered by **Kibana**, providing real-time dashboards for both operational and analytical insights.

Predefined visualizations display:
- Query throughput and latency distribution  
- Ingestion activity over time  
- FAISS retrieval accuracy and performance  
- Aggregated metrics from Prometheus (response times, success ratios, and load averages)  
- Error and exception tracking across ingestion and query services  

By correlating system logs with performance data, developers can pinpoint inefficiencies and bottlenecks in real time.

---

## System Architecture

The architecture can be logically visualized as a fully integrated data flow:

               ┌────────────────────┐
               │   User / Client    │
               └─────────┬──────────┘
                         │
                  Query Request
                         │
               ┌─────────▼──────────┐
               │     RAG Query      │
               │  (FastAPI + FAISS) │
               └─────────┬──────────┘
                         │
              Retrieved Context / Results
                         │
               ┌─────────▼──────────┐
               │   RAG Ingestion     │
               │ (FastAPI + FAISS)   │
               └─────────┬──────────┘
                         │
               Metadata + Vector Index
                         │
        ┌────────────────┴────────────────┐
        │                                 │
 ┌──────▼───────┐                ┌────────▼────────┐
 │ Prometheus   │                │  Elasticsearch  │
 │ Metrics Store│                │   Log Storage   │
 └──────┬───────┘                └────────┬────────┘
        │                                 │
 ┌──────▼────────┐                ┌───────▼────────┐
 │   Grafana /   │                │     Kibana     │
 │  Visualization│                │   Dashboards   │
 └───────────────┘                └────────────────┘


---

## Data Flow Description

1. **Document Entry** – The ingestion module receives structured or unstructured data and generates embeddings stored in a FAISS index.  
2. **Vector Index Construction** – Each data segment is encoded as a vector and indexed for efficient retrieval.  
3. **Query Handling** – Incoming user queries are converted to vectors and matched against the FAISS index to retrieve semantically relevant content.  
4. **Contextual Response Formation** – Retrieved context is merged with metadata and optionally processed through a language model to produce final responses.  
5. **Metric Emission** – All API requests, retrieval timings, and ingestion events emit metrics to Prometheus and logs to Elasticsearch.  
6. **Dashboard Visualization** – Kibana dashboards present live system health, retrieval accuracy, latency distribution, and ingestion statistics.

---

## Functional Scope

The system’s scope is to autonomously manage and monitor data retrieval workflows in AI systems that rely on RAG.  
It provides:
- Automated data ingestion with full observability  
- Real-time monitoring for latency and performance  
- Comprehensive logging for traceability  
- Visualization dashboards for operational intelligence  
- Modular APIs that can integrate with larger AI pipelines or LLM backends

The design ensures that developers can not only query and retrieve knowledge efficiently but also **observe, measure, and optimize** how the system performs under varying workloads.

---

## Objectives

1. **Autonomy** – Enable the RAG pipeline to self-manage ingestion, retrieval, and monitoring with minimal human intervention.  
2. **Transparency** – Provide full visibility into data flow, query metrics, and operational performance.  
3. **Scalability** – Use microservices and containerization for seamless deployment and horizontal scaling.  
4. **Observability** – Combine quantitative (Prometheus) and qualitative (Elasticsearch) data for 360° system insight.  
5. **Extensibility** – Allow integration of custom models, data sources, or analytics pipelines.

---

## 📊 System Visualizations

Below are key monitoring dashboards demonstrating real-time observability of the **Autonomous RAG Monitoring System** using **Kibana** and **Prometheus**.

---

### 🟢 Prometheus Metrics Overview
> **Figure 1.** Prometheus dashboard tracking API latency, ingestion throughput, and system resource utilization.

<p align="center">
  <img src="docs/images/Prometheus.png" width="80%" alt="Prometheus Metrics Dashboard">
</p>

---

### 🟣 Kibana Dashboards

> **Figure 2.** Query performance trends visualized in Kibana.  
> **Figure 3.** Retrieval latency and response-time correlation.  
> **Figure 4.** Log distribution across ingestion and query services.

<p align="center">
  <img src="docs/images/Kibana_Visual_1.png" width="80%" alt="Kibana Dashboard 1">
  <br><br>
  <img src="docs/images/Kibana_Visual_2.png" width="80%" alt="Kibana Dashboard 2">
  <br><br>
  <img src="docs/images/Kibana_Visual_3.png" width="80%" alt="Kibana Dashboard 3">
</p>

---

These visualizations collectively illustrate the system’s ability to:
- Monitor ingestion rates and query response times in real time  
- Correlate retrieval performance with operational metrics  
- Provide full-stack transparency into RAG workflow health


## Core Components and Responsibilities

| Component | Description |
|------------|-------------|
| **RAG Ingestion Service** | Handles text chunking, embedding generation, FAISS indexing, and metadata management. |
| **RAG Query Service** | Accepts queries, performs semantic search, retrieves top-k results, and logs performance metrics. |
| **FAISS Vector Store** | Stores vector embeddings for high-speed nearest-neighbor searches. |
| **Elasticsearch** | Acts as a central log and metadata store for query and ingestion operations. |
| **Kibana** | Provides visualization dashboards for logs, ingestion stats, and system health. |
| **Prometheus** | Collects and aggregates operational metrics from both FastAPI services. |

---

## Novelty and Contribution

Unlike traditional RAG setups that only focus on retrieval efficiency, this system introduces **autonomous monitoring intelligence**.  
It transforms RAG pipelines into self-observing systems by merging:
- **Retrieval Efficiency Analysis** (via Prometheus metrics)
- **Semantic Log Correlation** (via Elasticsearch and Kibana)
- **Adaptive Observability Feedback Loop** (allowing optimization and fault detection)

This unified approach bridges the gap between **retrieval accuracy**, **system reliability**, and **operational analytics**, providing a framework suitable for production-grade AI applications.

---

## Impact

The Autonomous RAG Monitoring System provides measurable benefits:
- **Enhanced Reliability:** Continuous monitoring prevents silent failures in retrieval and ingestion processes.  
- **Performance Insight:** Real-time dashboards reveal trends in query performance and retrieval precision.  
- **Maintainability:** Modular structure enables isolated debugging and scalable service deployment.  
- **Explainability:** Observability tools make the RAG pipeline auditable and interpretable in production environments.

---

## Summary

This project represents a step toward **self-managing AI infrastructure**, where retrieval systems are not just operationally efficient but also self-aware.  
By combining **FAISS** for vector retrieval, **FastAPI** for orchestration, and **Elastic + Prometheus** for monitoring, the system embodies a full-cycle feedback framework that measures, visualizes, and refines its own performance.

The Autonomous RAG Monitoring System is a practical demonstration of how retrieval-based AI systems can evolve from static data pipelines into **adaptive, transparent, and self-optimizing ecosystems**.

---
