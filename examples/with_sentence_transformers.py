#!/usr/bin/env python3
"""
Example: Using client-side embeddings (Sentence Transformers).

This example demonstrates how to:
1. Generate embeddings on the client side using `sentence-transformers`.
2. Insert documents with pre-computed embeddings (bypassing server-side BERT).
3. Search using pre-computed query embeddings.
4. Measure performance.

Prerequisites:
    pip install ricedb[embeddings]
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add src to path if running from examples dir without install
try:
    import ricedb
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ricedb import RiceDBClient

try:
    from ricedb.utils.embeddings import EmbeddingModel
except ImportError:
    print("Error: sentence-transformers not installed.")
    print("Please install with: pip install ricedb[embeddings]")
    sys.exit(1)

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def main():
    print(" RiceDB Client-Side Embeddings Example\n")

    # 1. Initialize Embedding Model (Client-side)
    print("1. Loading Embedding Model (all-distilroberta-v1)...")
    try:
        encoder = EmbeddingModel("all-distilroberta-v1")
    except Exception as e:
        print(f"Failed to load model: {e}")
        return

    # 2. Connect to RiceDB
    print("\n2. Connecting to RiceDB...")
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print(" Failed to connect")
        return

    try:
        client.login("admin", PASSWORD)
    except Exception as e:
        print(f" Login failed: {e}")
        return

    # 3. Insert with Pre-computed Embeddings
    print("\n3. Inserting Documents (Client-side Encoding)...")

    # Use IDs in a new range to avoid conflicts with previous tests
    documents = [
        (5000001, "The quick brown fox jumps over the lazy dog."),
        (5000002, "Artificial Intelligence is transforming the world."),
        (5000003, "RiceDB uses Hyperdimensional Computing for efficiency."),
    ]

    for node_id, text in documents:
        print(f"   Processing doc {node_id}...")

        # 1. Measure Client-side Encoding Time
        t0 = time.perf_counter()
        vector = encoder.encode(text)
        t1 = time.perf_counter()
        encoding_time = (t1 - t0) * 1000
        print(f"     Encoding time: {encoding_time:.2f}ms")

        # 2. Measure Server Insert Time (should be fast as it skips BERT)
        t2 = time.perf_counter()
        result = client.insert(
            node_id=node_id,
            text=text,
            metadata={"source": "client-side-embedding", "content": text},
            embedding=vector,
            user_id=1,
        )
        t3 = time.perf_counter()
        insert_time = (t3 - t2) * 1000
        print(f"     Insert API time: {insert_time:.2f}ms")
        print(f"     Total time:      {encoding_time + insert_time:.2f}ms")

    # 4. Search with Pre-computed Query Embedding
    print("\n4. Searching (Client-side Query Encoding)...")
    # Using a specific query to find the newly inserted documents
    query = "RiceDB hyperdimensional efficiency"
    print(f"   Query: '{query}'")

    # Measure Query Encoding
    t0 = time.perf_counter()
    query_vector = encoder.encode(query)
    t1 = time.perf_counter()
    print(f"   Query Encoding time: {(t1 - t0) * 1000:.2f}ms")

    # Measure Search API
    t2 = time.perf_counter()
    results = client.search(
        query=query,
        query_embedding=query_vector,
        user_id=1,
        k=3,
    )
    t3 = time.perf_counter()
    print(f"   Search API time:     {(t3 - t2) * 1000:.2f}ms")

    for i, res in enumerate(results, 1):
        meta = res["metadata"]
        # Try multiple fields for text content
        content = meta.get("content") or meta.get("stored_text") or meta.get("text") or "Unknown"
        print(f"   {i}. ID: {res['id']} (Score: {res['similarity']:.4f})")
        print(f"      Content: {content}")

    client.disconnect()


if __name__ == "__main__":
    main()
