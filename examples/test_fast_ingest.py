#!/usr/bin/env python3
"""
Test Fast Ingest (Python SDK).
"""

import os
import sys
import random
import time

# Add src to path if needed
try:
    import ricedb
except ImportError:
    sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from ricedb import RiceDBClient

HOST = "localhost"
PORT = 50051
PASSWORD = "admin"
DOC_COUNT = 5000


def generate_data(count: int):
    print(f"Generating {count} documents...")
    docs = []
    topics = ["AI", "Database", "Performance"]

    for i in range(count):
        topic = random.choice(topics)
        docs.append(
            {
                "id": i + 100000,  # Offset
                "text": f"Fast ingest test document {i}. Topic: {topic}",
                "metadata": {"topic": topic, "index": i},
            }
        )
    return docs


def main():
    print(f"Connecting to {HOST}:{PORT}...")
    # Default to gRPC for performance
    client = RiceDBClient(HOST, port=PORT, transport="grpc")

    if hasattr(client, "fast_ingest"):
        print("fast_ingest method verified on client.")
    else:
        print("Error: fast_ingest method missing.")

    try:
        if not client.connect():
            print("Failed to connect to RiceDB.")
            return

        client.login("admin", PASSWORD)
        print("Connected and logged in.")

        # Generate data
        docs = generate_data(DOC_COUNT)

        # Test fast_ingest
        print(f"\nRunning fast_ingest with {DOC_COUNT} docs...")
        result = client.fast_ingest(docs, batch_size=500, max_workers=4, user_id=1)

        print("\nIngest Summary:")
        print(f"Total Inserted: {result['total_inserted']}")
        print(f"Failed Batches: {result['failed_batches']}")
        print(f"Time Taken: {result['time_taken']:.4f}s")
        print(f"Throughput: {result['throughput']:.2f} docs/sec")

        if result["errors"]:
            print("\nErrors:", result["errors"])

    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        client.disconnect()


if __name__ == "__main__":
    main()
