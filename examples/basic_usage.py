#!/usr/bin/env python3
"""
Basic usage example for RiceDB Python client (HDC Architecture).

This example demonstrates:
1. Connecting to a RiceDB server
2. Inserting documents with raw text (Server-side HDC encoding)
3. Searching for similar documents using text queries
"""

import os
from dotenv import load_dotenv
from ricedb import RiceDBClient
import time

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def main():
    print("🍚 RiceDB Python Client - Basic Usage Example (HDC)\n")

    # Initialize client (auto-selects transport)
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL

    # Connect to the server
    print("1️⃣  Connecting to RiceDB server...")
    try:
        if client.connect():
            transport_info = client.get_transport_info()
            print(f"   ✓ Connected via {transport_info['type'].upper()}")

            # Login as admin (default credentials)
            print("   🔑 Logging in...")
            client.login("admin", PASSWORD)
            print("   ✓ Logged in successfully")
        else:
            print("   ❌ Failed to connect to RiceDB server")
            print("   Make sure the server is running:")
            print("   - HTTP: cargo run --example http_server --features http-server")
            print("   - gRPC: cargo run --bin ricedb-server-grpc --features grpc-server")
            return
    except Exception as e:
        print(f"   ❌ Connection/Login error: {e}")
        return

    # Check server health
    print("\n2️⃣  Checking server health...")
    try:
        health = client.health()
        print(f"   ✓ Server status: {health.get('status', 'Unknown')}")
        print(f"   ✓ Version: {health.get('version', 'Unknown')}")
    except Exception as e:
        print(f"   ❌ Health check failed: {e}")
        return

    # Prepare test data
    print("\n3️⃣  Preparing test data...")
    user_id = 100

    documents = [
        {
            "id": 1,
            "text": "Q4 Budget Report - Financial analysis of quarterly expenses and revenue.",
            "metadata": {
                "title": "Q4 Budget Report",
                "department": "Finance",
                "type": "report",
            },
        },
        {
            "id": 2,
            "text": "Team collaboration guidelines for engineering department. Includes code review process.",
            "metadata": {
                "title": "Team Wiki",
                "department": "Engineering",
                "type": "documentation",
            },
        },
        {
            "id": 3,
            "text": "Project technical requirements specification for the new mobile app.",
            "metadata": {
                "title": "Project Specification",
                "department": "Engineering",
                "type": "specification",
            },
        },
        {
            "id": 4,
            "text": "Alice likes peanuts and goes to the park.",
            "metadata": {"title": "Story 1"},
        },
        {
            "id": 5,
            "text": "Bob is allergic to peanuts and stays home.",
            "metadata": {"title": "Story 2"},
        },
    ]

    print(f"   ✓ Prepared {len(documents)} documents")

    # Insert documents
    print("\n4️⃣  Inserting documents (HDC Encoding)...")
    start_time = time.time()
    try:
        for doc in documents:
            result = client.insert(
                node_id=doc["id"],
                text=doc["text"],
                metadata=doc["metadata"],
                user_id=user_id,
            )
            if result.get("success", True):
                print(f"   ✓ Inserted: {doc['metadata']['title']} (ID: {doc['id']})")
            else:
                print(f"   ❌ Failed to insert: {doc['metadata']['title']}")
    except Exception as e:
        print(f"   ❌ Insert error: {e}")
        return
    print(f"   ⏱️  Insertion took {time.time() - start_time:.4f}s")

    # Search for documents
    print("\n5️⃣  Searching documents (HDC Resonance)...")
    queries = [
        ("financial analysis", "Search for financial documents"),
        ("code review process", "Search for engineering guidelines"),
        ("Alice peanuts", "Search for Alice story"),
        ("mobile app requirements", "Search for project specs"),
    ]

    for query_text, description in queries:
        print(f"\n   {description}:")
        print(f"   Query: '{query_text}'")
        try:
            start_search = time.time()
            # client.search now takes text directly
            results = client.search(query_text, user_id=user_id, k=3)
            duration = time.time() - start_search

            print(f"   Found {len(results)} results in {duration:.4f}s:")
            for i, result in enumerate(results, 1):
                title = result["metadata"].get("title", "Unknown")
                similarity = result.get("similarity", 0)
                # Note: Similarity in HDC is Hamming distance based.
                # Closer to 0 means closer match if it's distance,
                # or closer to 1 if it's similarity (1 - dist/dim).
                # The server returns 'similarity' which we implemented as distance in one place
                # or similarity in another. Let's assume similarity (higher is better) for now
                # or print raw value.
                print(f"   {i}. {title} - Score: {similarity:.4f}")
        except Exception as e:
            print(f"   ❌ Search error: {e}")

    # Cleanup
    print("\n7️⃣  Cleanup...")
    client.disconnect()
    print("   ✓ Disconnected from server")

    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()
