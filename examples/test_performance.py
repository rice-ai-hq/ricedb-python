#!/usr/bin/env python3
"""
Performance Test for RiceDB (Local).

This script:
1. Connects to local RiceDB instance.
2. Generates synthetic data.
3. Performs bulk ingest and measures throughput.
4. Performs search queries and measures latency.
"""

import os
import sys
import time
import uuid
import random
import concurrent.futures
from typing import List, Dict, Any

# Add src to path if needed
try:
    import ricedb
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ricedb import RiceDBClient

# Configuration
HOST = "localhost"
PORT = 50051
PASSWORD = "admin"
DOC_COUNT = 5000
BATCH_SIZE = 500
CONCURRENT_CLIENTS = 5


def generate_data(count: int) -> List[Dict[str, Any]]:
    print(f"Generating {count} documents...")
    docs = []
    topics = ["AI", "Database", "Performance", "Vector", "Graph", "Memory", "Agent"]
    actions = ["optimization", "deployment", "testing", "scaling", "debugging", "monitoring"]

    for i in range(count):
        topic = random.choice(topics)
        action = random.choice(actions)
        text = f"RiceDB {topic} {action} log entry number {i}. The system is processing data efficiently."
        docs.append(
            {
                "id": i + 10000,  # Offset to avoid collisions
                "text": text,
                "metadata": {"topic": topic, "action": action, "index": i},
            }
        )
    return docs


def insert_batch(client, batch):
    try:
        client.batch_insert(batch, user_id=1)
        return len(batch)
    except Exception as e:
        print(f"\nBatch failed: {e}")
        return 0


def main():
    print(f"RiceDB Performance Test")
    print(f"Target: {HOST}:{PORT}")
    print(f"Docs: {DOC_COUNT}, Batch: {BATCH_SIZE}, Clients: {CONCURRENT_CLIENTS}")

    # 2. Generate Data
    docs = generate_data(DOC_COUNT)

    # 3. Bulk Ingest
    print(f"\nStarting Bulk Ingest...")
    start_time = time.time()

    # Prepare batches
    batches = [docs[i : i + BATCH_SIZE] for i in range(0, len(docs), BATCH_SIZE)]

    total_inserted = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=CONCURRENT_CLIENTS) as executor:
        # Create a client for each thread (best practice for gRPC usually, or share if thread-safe)
        # RiceDBClient manages its own connection. Let's create new ones to simulate distinct clients.
        futures = []
        for batch in batches:
            # We initialize client inside thread or reuse?
            # Creating client per request is expensive. Let's create a pool of clients.
            # For simplicity in this script, we'll just instantiate in the helper or pass one if thread safe.
            # grpcio channels are thread safe.
            client = RiceDBClient(HOST, port=PORT, transport="grpc")
            client.connect()
            client.login("admin", PASSWORD)
            futures.append(executor.submit(insert_batch, client, batch))

        for future in concurrent.futures.as_completed(futures):
            total_inserted += future.result()
            sys.stdout.write(f"\rProgress: {total_inserted}/{DOC_COUNT}")
            sys.stdout.flush()

    total_time = time.perf_counter() - start_time
    print(f"\n\nIngest Complete!")
    print(f"Total Time: {total_time:.4f}s")
    print(f"Throughput: {total_inserted / total_time:.2f} docs/sec")
    print(f"Avg per doc: {(total_time / total_inserted * 1000) if total_inserted > 0 else 0:.2f}ms")

    # 4. Search
    print("\nStarting Search Test...")
    client = RiceDBClient(HOST, port=PORT, transport="grpc")
    client.connect()
    client.login("admin", PASSWORD)

    query = "database scaling optimization"
    print(f"Query: '{query}'")

    start_search = time.perf_counter()
    results = client.search(query, k=5, user_id=1)
    search_time = time.perf_counter() - start_search

    print(f"Search Time: {search_time:.4f}s")
    print("\nTop Results:")
    for res in results:
        print(f"- ID: {res['id']}, Score: {res['similarity']:.4f}")
        print(f"  Meta: {res['metadata']}")

    client.disconnect()


if __name__ == "__main__":
    main()
