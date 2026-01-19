#!/usr/bin/env python3
"""
Local 50k Query Benchmark for RiceDB.

This script performs search queries against the locally running RiceDB instance.
It extracts real questions from the LongMemEval dataset to use as queries.

Usage:
    python3 local_50k_query.py
"""

import os
import time
import sys
import json
import statistics
from typing import List

try:
    import ijson
except ImportError:
    ijson = None

# Try to import ricedb, adding src to path if needed
try:
    from ricedb import RiceDBClient
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from ricedb import RiceDBClient

# Configuration
HOST = "localhost"
PORT = 50051
SSL = False
QUERY_COUNT = 100
TOP_K = 5
USER_ID = 1  # Must match the user_id used during insertion (default 1 in local_50k_insert.py)


def load_queries(count: int) -> List[str]:
    """Load questions from LongMemEval dataset."""
    dataset_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../datasets/longmemeval_s_cleaned.json")
    )
    print(f"Loading queries from {dataset_path}...")

    questions = []
    try:
        if ijson:
            with open(dataset_path, "rb") as f:
                items = ijson.items(f, "item")
                for item in items:
                    q = item.get("question")
                    if q:
                        questions.append(q)
                        if len(questions) >= count:
                            break
        else:
            print("ijson not found, using json fallback...")
            with open(dataset_path, "r") as f:
                data = json.load(f)
                for item in data:
                    q = item.get("question")
                    if q:
                        questions.append(q)
                        if len(questions) >= count:
                            break
    except Exception as e:
        print(f"Error loading queries: {e}")
        return ["test query " + str(i) for i in range(count)]

    return questions


def measure_latency(client, queries):
    print(f"\nRunning {len(queries)} queries (k={TOP_K})...")
    latencies = []
    output_file = "query_results.txt"

    print(f"Writing all results to {output_file}...")

    with open(output_file, "w") as f:
        for i, q in enumerate(queries):
            start = time.perf_counter()
            try:
                results = client.search(q, user_id=USER_ID, k=TOP_K)
                duration = (time.perf_counter() - start) * 1000  # ms
                latencies.append(duration)

                # Write results to file
                f.write(f"\nQuery {i + 1}: '{q}'\n")
                f.write(f"Time: {duration:.2f}ms\n")
                for j, res in enumerate(results):
                    meta = res["metadata"]
                    # Try stored_text first (as per updated insert script), then text
                    text = (meta.get("stored_text") or meta.get("text") or "").replace("\n", " ")
                    f.write(
                        f"  {j + 1}. [Score: {res['similarity']:.4f}] (ID: {res['id']}) {text}...\n"
                    )
                f.write("-" * 40 + "\n")

            except Exception as e:
                print(f"Query failed: {e}")
                f.write(f"Query failed: {e}\n")

    return latencies


def main():
    print(" RiceDB Local Query Benchmark\n")

    # 1. Connect
    client = RiceDBClient(HOST, port=PORT, transport="grpc")
    client.ssl = SSL

    print("1. Connecting...")
    if not client.connect():
        print("   Failed to connect to localhost.")
        return

    client.login("admin", "admin")

    # 2. Load Queries
    queries = load_queries(QUERY_COUNT)
    if not queries:
        print("No queries found.")
        return

    # 3. Run Benchmark
    latencies = measure_latency(client, queries)

    # 4. Stats
    if latencies:
        avg = statistics.mean(latencies)
        p95 = sorted(latencies)[int(0.95 * len(latencies))]
        p99 = sorted(latencies)[int(0.99 * len(latencies))]

        print(f"\nResults ({len(latencies)} queries):")
        print(f"  Avg Latency: {avg:.2f} ms")
        print(f"  P95 Latency: {p95:.2f} ms")
        print(f"  P99 Latency: {p99:.2f} ms")
        print(f"  Min: {min(latencies):.2f} ms")
        print(f"  Max: {max(latencies):.2f} ms")

        rate = 1000 / avg
        print(f"  Est. Throughput: {rate:.2f} qps (single-threaded)")

    client.disconnect()


if __name__ == "__main__":
    main()
