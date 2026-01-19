#!/usr/bin/env python3
"""
Remote 50k Bulk Ingest Benchmark for RiceDB (gRPC).

This script inserts 50,000 documents into a REMOTE RiceDB instance using gRPC.
Target: grpc.ricedb-test-2.ricedb.tryrice.com

Usage:
    python3 remote_50k_insert_grpc.py
"""

import os
import time
import random
import uuid
import sys
import json
from typing import List, Dict, Any

try:
    import ijson
except ImportError:
    ijson = None

# Try to import ricedb, adding src to path if needed (for dev repo usage)
try:
    from ricedb import RiceDBClient
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
    from ricedb import RiceDBClient

# Configuration - Remote Instance (gRPC)
# Note: Switched subdomain to 'grpc' for gRPC ingress
HOST = "grpc.ricedb-test-2.ricedb.tryrice.com"
PORT = 80
SSL = False
PASSWORD = "ed294b4085f0959974cd6e0ca7dfffbd"
BATCH_SIZE = 100
TOTAL_DOCS = 50000


def generate_corpus(count: int) -> List[Dict[str, Any]]:
    """Generate corpus by sampling from LongMemEval dataset."""
    dataset_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "../../datasets/longmemeval_s_cleaned.json")
    )
    print(f"Loading data from {dataset_path}...")

    texts = []
    start_load = time.time()

    try:
        if ijson:
            with open(dataset_path, "rb") as f:
                # Stream items to avoid loading massive file at once
                items = ijson.items(f, "item")
                for item in items:
                    if "haystack_sessions" in item:
                        for session in item["haystack_sessions"]:
                            for msg in session:
                                content = msg.get("content", "")
                                if content:
                                    texts.append(content)
        else:
            print("ijson not found, falling back to json (might be slow/memory intensive)...")
            with open(dataset_path, "r") as f:
                data = json.load(f)
                for item in data:
                    if "haystack_sessions" in item:
                        for session in item["haystack_sessions"]:
                            for msg in session:
                                content = msg.get("content", "")
                                if content:
                                    texts.append(content)

    except Exception as e:
        print(f"Error loading dataset: {e}")
        print("Please ensure datasets/longmemeval_s_cleaned.json exists.")
        sys.exit(1)

    if not texts:
        print("No texts found in dataset.")
        sys.exit(1)

    print(f"Found {len(texts)} unique texts in {time.time() - start_load:.2f}s")
    print(f"Sampling {count} documents (with replacement)...")

    # Sample with replacement to reach requested count
    sampled_texts = random.choices(texts, k=count)

    documents = []
    for txt in sampled_texts:
        doc = {
            "text": txt,
            "stored_text": txt,  # Store text in metadata for retrieval
            "source": "longmemeval",
            "timestamp": int(time.time()),
            # Add some synthetic metadata for variety
            "type": random.choice(["chat", "transcript", "note"]),
        }
        documents.append(doc)

    return documents


def main():
    print(" RiceDB Remote 50k Ingest Benchmark (gRPC)\n")
    print(f" Target: {HOST}:{PORT} (SSL={SSL})")
    print(f" Docs:   {TOTAL_DOCS}")
    print(f" Batch:  {BATCH_SIZE}")

    # 1. Connect
    print("\n1. Connecting (gRPC)...")
    # transport="grpc" ensures we use the gRPC client
    client = RiceDBClient(HOST, port=PORT, transport="grpc")
    client.ssl = SSL

    # Note: gRPC client might not throw on init, need to call connect/health
    if not client.connect():
        print("    Failed to connect to RiceDB server.")
        return
    print(f"    Connected via {client.get_transport_info()['type'].upper()}")

    # 2. Login
    try:
        client.login("admin", PASSWORD)
        print("    Logged in as 'admin'")
    except Exception as e:
        print(f"    Login failed: {e}")
        return

    # 3. Generate Data
    print("\n2. Generating Data...")
    raw_docs = generate_corpus(TOTAL_DOCS)

    # 4. Bulk Ingest
    print(f"\n3. Starting Bulk Ingest...")
    start_time = time.time()
    total_inserted = 0
    errors = 0

    # Process in batches
    for i in range(0, len(raw_docs), BATCH_SIZE):
        batch = raw_docs[i : i + BATCH_SIZE]

        # Prepare batch for RiceDB (requires 'id', 'text', 'metadata', 'user_id')
        batch_docs = []
        for j, doc in enumerate(batch):
            # Use simple sequential IDs starting from 1,000,000
            node_id = 1_000_000 + i + j

            item = {
                "id": node_id,
                "text": doc["text"],
                "metadata": {k: v for k, v in doc.items() if k != "text"},
                "user_id": 1,  # Admin user ID usually
            }
            batch_docs.append(item)

        try:
            result = client.batch_insert(batch_docs)
            count = result.get("count", 0)
            total_inserted += count

            # Progress bar
            if (i // BATCH_SIZE) % 10 == 0:
                progress = (i + len(batch)) / TOTAL_DOCS * 100
                sys.stdout.write(f"\r    Progress: {progress:.1f}% ({total_inserted} docs)")
                sys.stdout.flush()

        except Exception as e:
            errors += 1
            print(f"\n    Batch failed: {e}")

    duration = time.time() - start_time
    print(f"\n\n Ingest Complete!")
    print(f"   Total Inserted: {total_inserted}")
    print(f"   Errors:         {errors} batches")
    print(f"   Time Taken:     {duration:.2f}s")
    if duration > 0:
        print(f"   Throughput:     {total_inserted / duration:.2f} docs/sec")

    client.disconnect()


if __name__ == "__main__":
    main()
