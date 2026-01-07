#!/usr/bin/env python3
"""
Benchmark Latency and Accuracy for RiceDB (HDC).
"""

import os
import time
import statistics
from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def measure_latency(func, iterations=100):
    latencies = []
    for _ in range(iterations):
        start = time.perf_counter()
        func()
        latencies.append((time.perf_counter() - start) * 1000)  # ms
    return latencies


def main():
    print(" RiceDB Benchmark (HDC)\n")
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print(" Connection failed")
        return

    try:
        client.login("admin", PASSWORD)
    except Exception as e:
        print(f" Login failed: {e}")
        return

    # 1. Ingest
    print("1  Ingesting 100 documents...")
    docs = []
    for i in range(100):
        docs.append(
            {
                "id": i,
                "text": f"This is document number {i} with some random text about HDC and vector databases.",
                "metadata": {"index": i},
            }
        )

    start = time.perf_counter()
    for doc in docs:
        client.insert(doc["id"], doc["text"], doc["metadata"])
    end = time.perf_counter()
    print(f"    Ingested in {end - start:.4f}s ({(100 / (end - start)):.2f} docs/sec)")

    # 2. Search Latency
    print("\n2  Benchmarking Search Latency (100 iterations)...")

    def search_op():
        client.search("document number 50", user_id=1, k=1)

    latencies = measure_latency(search_op, 100)

    avg = statistics.mean(latencies)
    # quantiles requires python 3.8+
    try:
        p95 = statistics.quantiles(latencies, n=20)[18]
        p99 = statistics.quantiles(latencies, n=100)[98]
    except AttributeError:
        # Fallback for older python if needed, though project requires 3.10
        sorted_lat = sorted(latencies)
        p95 = sorted_lat[int(0.95 * len(latencies))]
        p99 = sorted_lat[int(0.99 * len(latencies))]

    print(f"   Avg: {avg:.2f}ms")
    print(f"   P95: {p95:.2f}ms")
    print(f"   P99: {p99:.2f}ms")

    if avg < 20:
        print("    Sub-20ms latency goal met!")
    else:
        print("     Latency above 20ms target.")

    # 3. Accuracy Test
    print("\n3  Verifying Accuracy...")
    # HDC is approximate, but exact n-gram match should be high similarity
    results = client.search("document number 42", user_id=1, k=1)
    if results and results[0]["id"] == 42:
        print(f"    Found document 42 correctly. Score: {results[0]['similarity']:.4f}")
    else:
        print(
            f"    Failed to find document 42. Top result: {results[0]['id'] if results else 'None'}"
        )
        if results:
            print(f"      Top result meta: {results[0]['metadata']}")

    client.disconnect()


if __name__ == "__main__":
    main()
