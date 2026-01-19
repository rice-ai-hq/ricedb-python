#!/usr/bin/env python3
"""
Direct performance test for the Embedding Service.

This script sends large batches directly to the embedding service API
to benchmark its raw performance and GPU utilization.
"""

import os
import time
import requests
import statistics
import concurrent.futures
from typing import List

# Configuration
# Default to remote URL from Makefile, can be overridden by env var
DEFAULT_URL = "https://rice-embedding-service-dev-709625386897.us-east4.run.app"
SERVICE_URL = os.environ.get("EMBEDDING_SERVICE_URL", DEFAULT_URL).rstrip("/")
BATCH_SIZE = 500
CONCURRENT_REQUESTS = 5
TOTAL_BATCHES = 10


def generate_texts(count: int) -> List[str]:
    """Generate synthetic texts."""
    base_texts = [
        "RiceDB is a high-performance vector database using Hyperdimensional Computing.",
        "Distributed systems require robust consensus algorithms like Raft or Paxos.",
        "Machine learning models can be deployed on Cloud Run with GPU acceleration.",
        "Optimization of batch processing pipelines reduces latency and improves throughput.",
        "The quick brown fox jumps over the lazy dog.",
    ]
    return [f"{base_texts[i % len(base_texts)]} [Index: {i}]" for i in range(count)]


def send_batch(batch_id: int, texts: List[str]) -> float:
    """Send a batch to the service and return duration in seconds."""
    url = f"{SERVICE_URL}/encode_batch"

    start_time = time.perf_counter()
    try:
        response = requests.post(url, json={"texts": texts})
        response.raise_for_status()

        # Verify response size
        data = response.json()
        embeddings = data.get("embeddings", [])
        if len(embeddings) != len(texts):
            print(f"Warning: Sent {len(texts)} texts but received {len(embeddings)} embeddings")

        duration = time.perf_counter() - start_time
        return duration
    except Exception as e:
        print(f"Batch {batch_id} failed: {e}")
        return 0.0


def main():
    print(f"Embedding Service Benchmark")
    print(f"Target: {SERVICE_URL}")
    print(f"Batch Size: {BATCH_SIZE}")
    print(f"Concurrent Requests: {CONCURRENT_REQUESTS}")
    print(f"Total Batches: {TOTAL_BATCHES}")
    print(f"Total Docs: {TOTAL_BATCHES * BATCH_SIZE}")
    print("-" * 50)

    # Generate data once to reuse (simulate workload)
    print("Generating data...")
    test_batch = generate_texts(BATCH_SIZE)

    print("\nStarting Benchmark...")
    start_total = time.perf_counter()

    durations = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_REQUESTS) as executor:
        futures = [executor.submit(send_batch, i, test_batch) for i in range(TOTAL_BATCHES)]

        for future in concurrent.futures.as_completed(futures):
            durations.append(future.result())

    total_time = time.perf_counter() - start_total
    valid_durations = [d for d in durations if d > 0]

    if not valid_durations:
        print("\nAll requests failed.")
        return

    total_docs = len(valid_durations) * BATCH_SIZE
    avg_latency = statistics.mean(valid_durations)
    p95_latency = (
        sorted(valid_durations)[int(len(valid_durations) * 0.95)] if valid_durations else 0
    )

    print("\nResults:")
    print(f"Total Time (Wall): {total_time:.4f}s")
    print(f"Total Docs Processed: {total_docs}")
    print(f"Throughput: {total_docs / total_time:.2f} docs/sec")
    print(f"Avg Batch Latency: {avg_latency:.4f}s")
    print(f"P95 Batch Latency: {p95_latency:.4f}s")
    print(f"Avg Latency per Doc: {(avg_latency / BATCH_SIZE) * 1000:.2f}ms")


if __name__ == "__main__":
    main()
