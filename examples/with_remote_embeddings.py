#!/usr/bin/env python3
"""
Example: Using remote embedding service.

This example demonstrates how to:
1. Generate embeddings using the standalone embedding service.
2. Insert documents with pre-computed embeddings.
3. Search using pre-computed query embeddings.

Prerequisites:
    1. Embedding service running (e.g. at http://localhost:8080)
    2. pip install ricedb requests
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
from ricedb.utils.embeddings import RemoteEmbeddingModel

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"
EMBEDDING_SERVICE_URL = os.environ.get("EMBEDDING_SERVICE_URL", "http://localhost:8080")


def main():
    print(" RiceDB Remote Embeddings Example\n")

    # 1. Initialize Remote Embedding Model
    print(f"1. Connecting to Embedding Service at {EMBEDDING_SERVICE_URL}...")
    try:
        encoder = RemoteEmbeddingModel(EMBEDDING_SERVICE_URL)
        # Test connection with health check
        import requests

        health = requests.get(f"{EMBEDDING_SERVICE_URL}/health")
        health.raise_for_status()
        print(f"   Service status: {health.json()}")
    except Exception as e:
        print(f"Failed to connect to embedding service: {e}")
        print("Please ensure the service is running (see deploy/embedding-service/README.md)")
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

    # 3. Insert with Remote Embeddings
    print("\n3. Inserting Documents (Remote Encoding)...")

    documents = [
        (6000001, "Distributed systems are complex but powerful."),
        (6000002, "Microservices allow independent scaling of components."),
        (6000003, "RiceDB decoupled architecture improves ingestion latency."),
    ]

    for node_id, text in documents:
        print(f"   Processing doc {node_id}...")

        # 1. Measure Remote Encoding Time
        t0 = time.perf_counter()
        vector = encoder.encode(text)
        t1 = time.perf_counter()
        encoding_time = (t1 - t0) * 1000
        print(f"     Encoding time: {encoding_time:.2f}ms")

        # 2. Measure Server Insert Time
        t2 = time.perf_counter()
        result = client.insert(
            node_id=node_id,
            text=text,
            metadata={"source": "remote-embedding", "content": text},
            embedding=vector,
            user_id=1,
        )
        t3 = time.perf_counter()
        insert_time = (t3 - t2) * 1000
        print(f"     Insert API time: {insert_time:.2f}ms")
        print(f"     Total time:      {encoding_time + insert_time:.2f}ms")

    # 4. Search with Remote Query Embedding
    print("\n4. Searching (Remote Query Encoding)...")
    query = "decoupled architecture latency"
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
        content = meta.get("content") or meta.get("stored_text") or meta.get("text") or "Unknown"
        print(f"   {i}. ID: {res['id']} (Score: {res['similarity']:.4f})")
        print(f"      Content: {content}")

    client.disconnect()


if __name__ == "__main__":
    main()
