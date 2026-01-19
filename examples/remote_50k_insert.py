#!/usr/bin/env python3
"""
Remote 50k Bulk Ingest Benchmark for RiceDB.

This script inserts 50,000 documents into a REMOTE RiceDB instance.
Target: api.ricedb-test-2.ricedb.tryrice.com

Usage:
    python3 remote_50k_insert.py
"""

import os
import time
import random
import uuid
import sys
import json
from typing import List, Dict, Any
import concurrent.futures
from dotenv import load_dotenv

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

load_dotenv()

# Configuration - Remote Instance
HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "80"))
SSL = os.environ.get("SSL", "false").lower() == "true"
PASSWORD = os.environ.get("PASSWORD", "admin")
BATCH_SIZE = 500
TOTAL_DOCS = 50000
MAX_WORKERS = 8


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
    print(" RiceDB Remote 50k Fast Ingest Benchmark\n")
    print(f" Target: {HOST}:{PORT} (SSL={SSL})")
    print(f" Docs:   {TOTAL_DOCS}")
    print(f" Batch:  {BATCH_SIZE}")
    print(f" Workers: {MAX_WORKERS}")

    # 1. Connect
    print("\n1. Connecting...")
    # Use auto transport
    client = RiceDBClient(HOST, port=PORT, transport="auto")
    client.ssl = SSL

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

    # 4. Prepare Data Format for Fast Ingest
    # fast_ingest expects docs with 'id', 'text', 'metadata', 'user_id' keys (optional user_id)
    # generate_corpus returns dicts with 'text', 'stored_text', etc.
    print("\n3. Preparing documents...")
    formatted_docs = []
    for i, doc in enumerate(raw_docs):
        node_id = 1_000_000 + i
        formatted_docs.append(
            {
                "id": node_id,
                "text": doc["text"],
                "metadata": {k: v for k, v in doc.items() if k != "text"},
                "user_id": 1,
            }
        )

    # 5. Fast Ingest (Custom Implementation with Tracking)
    print(f"\n4. Starting Fast Ingest ({TOTAL_DOCS} docs)...")

    start_time = time.time()
    total_inserted = 0
    failed_batches = 0
    errors = []

    # Create batches
    batches = [
        formatted_docs[i : i + BATCH_SIZE] for i in range(0, len(formatted_docs), BATCH_SIZE)
    ]
    total_batches = len(batches)

    print(f"    Processing {total_batches} batches with {MAX_WORKERS} workers...")

    def _process_batch(batch_idx, batch):
        t0 = time.time()
        try:
            res = client.batch_insert(batch, user_id=1)
            duration = time.time() - t0
            return {
                "success": True,
                "count": res.get("count", len(batch)),
                "duration": duration,
                "idx": batch_idx,
            }
        except Exception as e:
            return {"success": False, "error": str(e), "idx": batch_idx}

    completed_batches = 0

    with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        # Submit all batches
        futures = {executor.submit(_process_batch, i, batch): i for i, batch in enumerate(batches)}

        for future in concurrent.futures.as_completed(futures):
            batch_idx = futures[future]
            result = future.result()
            completed_batches += 1

            elapsed = time.time() - start_time
            avg_speed = total_inserted / elapsed if elapsed > 0 else 0

            if result["success"]:
                total_inserted += result["count"]
                # Log every 10 batches or if slow
                if completed_batches % 10 == 0 or total_batches < 20:
                    print(
                        f"    [Batch {result['idx'] + 1}/{total_batches}] Inserted {result['count']} docs in {result['duration']:.2f}s. (Avg Speed: {avg_speed:.1f} docs/s)"
                    )
            else:
                failed_batches += 1
                if len(errors) < 5:
                    errors.append(result["error"])
                print(f"    [Batch {result['idx'] + 1}/{total_batches}] FAILED: {result['error']}")

    total_time = time.time() - start_time
    throughput = total_inserted / total_time if total_time > 0 else 0

    print(f"\n\n Ingest Complete!")
    print(f"   Total Inserted: {total_inserted}")
    print(f"   Failed Batches: {failed_batches}")
    print(f"   Time Taken:     {total_time:.2f}s")
    print(f"   Throughput:     {throughput:.2f} docs/sec")

    if errors:
        print(f"   Errors (first 5): {errors[:5]}")

    client.disconnect()


if __name__ == "__main__":
    main()
