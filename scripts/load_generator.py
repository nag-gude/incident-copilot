#!/usr/bin/env python3
"""
Incident Copilot - Real-time load generator for pre-production and production testing.

Generates logs and metrics with configurable patterns including baseline, spikes,
and error bursts to trigger anomaly detection and prediction.

Usage:
  INGESTION_URL=http://localhost:8001 python scripts/load_generator.py
  python scripts/load_generator.py --url http://ingestion:8001 --duration 300
"""

import argparse
import json
import random
import sys
import time
from datetime import datetime

try:
    import httpx
except ImportError:
    print("Install httpx: pip install httpx")
    sys.exit(1)

INGESTION_URL = "http://localhost:8001"
SERVICES = ["api", "worker", "payment", "auth"]
LOG_LEVELS = ["info", "info", "info", "warn", "error"]
METRIC_NAMES = ["cpu_usage", "memory_usage", "request_latency_ms", "error_rate"]


def ingest_log(level: str, message: str, service: str):
    try:
        httpx.post(
            f"{INGESTION_URL}/ingest/logs",
            json={
                "level": level,
                "message": message,
                "source": "load_generator",
                "service": service,
            },
            timeout=5,
        )
    except Exception as e:
        print(f"Log ingest error: {e}")


def ingest_metric(name: str, value: float, service: str):
    try:
        httpx.post(
            f"{INGESTION_URL}/ingest/metrics",
            json={"name": name, "value": value, "service": service},
            timeout=5,
        )
    except Exception as e:
        print(f"Metric ingest error: {e}")


def run_baseline(iteration: int):
    """Normal baseline: steady metrics, mostly info logs."""
    for _ in range(random.randint(1, 3)):
        svc = random.choice(SERVICES)
        ingest_metric("cpu_usage", random.uniform(40, 70), svc)
        ingest_metric("memory_usage", random.uniform(50, 80), svc)
        ingest_metric("request_latency_ms", random.uniform(50, 200), svc)
    for _ in range(random.randint(1, 3)):
        level = random.choice(LOG_LEVELS)
        msg = f"Request processed" if level == "info" else f"Warning: high load" if level == "warn" else "Connection timeout"
        ingest_log(level, msg, random.choice(SERVICES))


def run_spike(iteration: int):
    """Inject metric spike to trigger anomaly."""
    svc = random.choice(SERVICES)
    for _ in range(10):
        ingest_metric("cpu_usage", random.uniform(85, 98), svc)
        ingest_metric("memory_usage", random.uniform(90, 99), svc)
    ingest_log("error", f"Spike injected at iteration {iteration}", svc)


def run_error_burst(iteration: int):
    """Inject error log burst."""
    svc = random.choice(SERVICES)
    for _ in range(5):
        ingest_log("error", f"Simulated error burst iteration {iteration}", svc)
    ingest_metric("error_rate", random.uniform(10, 50), svc)


def main():
    parser = argparse.ArgumentParser(description="Incident Copilot load generator")
    parser.add_argument("--url", default=INGESTION_URL, help="Ingestion service URL")
    parser.add_argument("--duration", type=int, default=0, help="Run for N seconds (0=forever)")
    parser.add_argument("--interval", type=float, default=1.0, help="Seconds between iterations")
    args = parser.parse_args()

    global INGESTION_URL
    INGESTION_URL = args.url.rstrip("/")

    print(f"Load generator -> {INGESTION_URL}")
    print("Ctrl+C to stop")
    start = time.time()
    iteration = 0

    try:
        while True:
            iteration += 1
            run_baseline(iteration)

            if iteration % 60 == 0:
                run_spike(iteration)
            elif iteration % 30 == 0:
                run_error_burst(iteration)

            if args.duration and (time.time() - start) >= args.duration:
                break
            time.sleep(args.interval)
    except KeyboardInterrupt:
        pass

    print(f"Stopped after {iteration} iterations.")
    print("Trigger anomaly: curl http://<anomaly-host>:8002/detect")


if __name__ == "__main__":
    main()
