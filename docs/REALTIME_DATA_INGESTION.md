# Incident Copilot AI - Real-Time Data Ingestion for Testing

Guide for real-time telemetry ingestion in pre-production and production environments.


## Table of Contents

1. [Overview](#overview)
2. [Ingestion Methods](#ingestion-methods)
3. [Pre-Production Testing](#pre-production-testing)
4. [Production Data Sources](#production-data-sources)
5. [Load Generators and Synthetic Data](#load-generators-and-synthetic-data)
6. [Prometheus Integration](#prometheus-integration)
7. [Log Forwarding (Fluent Bit / Vector)](#log-forwarding-fluent-bit--vector)
8. [Setup Scripts and Examples](#setup-scripts-and-examples)


## Overview

Incident Copilot AI ingests **logs** and **metrics** via REST API. For pre-production and production testing, you need real-time or near-real-time data flowing into the Ingestion service.

| Environment | Goal | Recommended Approach |
|-------------|------|----------------------|
| **Pre-production (Staging)** | Validate pipeline end-to-end | Synthetic load generator + optional Prometheus scrape |
| **Production** | Real observability | Prometheus metrics, log forwarders, or application instrumentation |


## Ingestion Methods

### 1. REST API (Primary)

Incident Copilot Ingestion exposes:

- `POST /ingest/logs` - Single log
- `POST /ingest/logs/batch` - Batch of logs
- `POST /ingest/metrics` - Single metric

**Log payload:**
```json
{
  "level": "info",
  "message": "Connection established",
  "source": "api",
  "service": "payment-service",
  "metadata": {"request_id": "abc123"}
}
```

**Metric payload:**
```json
{
  "name": "cpu_usage",
  "value": 75.5,
  "labels": {"pod": "payment-1"},
  "service": "payment-service"
}
```

### 2. Batch Ingestion

For high volume, use `/ingest/logs/batch`:

```bash
curl -X POST http://<ingestion-url>:8001/ingest/logs/batch \
  -H "Content-Type: application/json" \
  -d '[{"level":"error","message":"Timeout","service":"api"}, ...]'
```


## Pre-Production Testing

### Goal

- Generate continuous logs and metrics
- Trigger anomaly detection (spikes, error bursts)
- Verify prediction and recommendation flows

### Option A: Python Load Script (Recommended)

Run the included load generator:

```bash
INGESTION_URL=http://localhost:8001 python scripts/load_generator.py

# Or with options (K8s: use ingestion service URL)
python scripts/load_generator.py --url http://ingestion:8001 --duration 300 --interval 1
```

The script sends:
- Baseline metrics (CPU, memory, latency) and logs every 1s
- Metric spike every 60 iterations
- Error burst every 30 iterations

After running, trigger anomaly detection: `curl http://<api-gateway>:8002/detect`

### Option B: curl Loop

```bash
INGESTION_URL="http://localhost:8001"  # or LoadBalancer IP
while true; do
  curl -s -X POST "$INGESTION_URL/ingest/metrics" \
    -H "Content-Type: application/json" \
    -d "{\"name\":\"cpu_usage\",\"value\":$(shuf -i 40-90 -n 1),\"service\":\"test\"}"
  sleep 1
done
```

### Option C: Use seed_demo_data.py + Anomaly Trigger

```bash
python scripts/seed_demo_data.py
curl http://<api-gateway>:8002/detect   # Run anomaly detection
curl http://<api-gateway>:8003/predict  # Run prediction
```


## Production Data Sources

### 1. Application Instrumentation

Have your apps POST logs/metrics directly:

```python
# Python example
import httpx
httpx.post(
    "http://incident-copilot-ingestion:8001/ingest/logs",
    json={"level": "error", "message": "DB connection failed", "service": "api"}
)
```

### 2. Prometheus (Metrics)

Use Prometheus to scrape your app metrics, then a sidecar or exporter that forwards to Incident Copilot Ingestion. See [Prometheus Integration](#prometheus-integration).

### 3. Log Forwarders

Use Fluent Bit, Vector, or Logstash to tail logs and POST to Ingestion. See [Log Forwarding](#log-forwarding-fluent-bit--vector).


## Load Generators and Synthetic Data

### Continuous Load Generator Script

A script that runs indefinitely, sending realistic log and metric patterns with occasional anomalies for testing:

| Pattern | Description |
|---------|-------------|
| Baseline | Steady metrics (50–70% CPU), info logs |
| Spike | Sudden metric jump (e.g., 90% CPU) |
| Error burst | Multiple error logs in short window |
| Gradual drift | Slowly increasing values over time |

### Sample Load Generator Logic

```
Every 1s: Send 1–3 metrics (cpu_usage, memory_usage, request_latency)
Every 5s: Send 2–5 logs (info/warn/error mix)
Every 60s: Inject anomaly (spike or error burst)
```


## Prometheus Integration

### Architecture

```
Prometheus (scrapes app) → Remote Write or Exporter → Incident Copilot Ingestion
```

### Option 1: Prometheus Remote Write Adapter

Create a small adapter that receives Prometheus remote-write format and converts to Incident Copilot `/ingest/metrics` calls.

### Option 2: Prometheus Exporter Sidecar

Run a sidecar that:
1. Scrapes Prometheus /metrics
2. Parses Prometheus text format
3. POSTs to Incident Copilot Ingestion

### Option 3: Kubernetes Metrics

If using Kubernetes, the metrics-server and kube-state-metrics expose pod/container metrics. An adapter can scrape these and forward to Incident Copilot.


## Log Forwarding (Fluent Bit / Vector)

### Fluent Bit Configuration

```ini
[INPUT]
    Name              tail
    Path              /var/log/app/*.log
    Tag               app

[FILTER]
    Name              lua
    Script            to_incident-copilot.lua
    Call              format_for_incident-copilot

[OUTPUT]
    Name              http
    Match             *
    Host              incident-copilot-ingestion
    Port              8001
    URI               /ingest/logs
    Format            json
```

### Vector Configuration (example)

```toml
[sources.app_logs]
type = "file"
include = ["/var/log/app/*.log"]

[sinks.incident-copilot]
type = "http"
inputs = ["app_logs"]
uri = "http://incident-copilot-ingestion:8001/ingest/logs"
encoding.codec = "json"
```


## Setup Scripts and Examples

### Run Load Generator (Pre-Prod)

```bash
# From Incident Copilot root
INGESTION_URL=http://<api-gateway-or-ingestion>:8001 python scripts/load_generator.py
```

### Trigger Anomaly Detection

```bash
# After ingesting data
curl http://<api-gateway>:8002/detect
```

### Verify Pipeline

```bash
# Check ingestion
curl http://<api-gateway>:8001/logs?limit=10

# Check anomalies
curl http://<api-gateway>:8002/anomalies

# Check prediction
curl http://<api-gateway>:8003/predict
```
