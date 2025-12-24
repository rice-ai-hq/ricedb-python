#!/usr/bin/env python3
"""
Basic usage example for RiceDB Python client.

This example demonstrates:
1. Connecting to a RiceDB server
2. Inserting documents with vectors
3. Searching for similar documents
"""

from ricedb import RiceDBClient
from ricedb.utils import DummyEmbeddingGenerator


def main():
    print("🍚 RiceDB Python Client - Basic Usage Example\n")

    # Initialize client (auto-selects transport)
    client = RiceDBClient("localhost")

    # Connect to the server
    print("1️⃣  Connecting to RiceDB server...")
    try:
        if client.connect():
            transport_info = client.get_transport_info()
            print(f"   ✓ Connected via {transport_info['type'].upper()}")

            # Login as admin (default credentials)
            print("   🔑 Logging in...")
            client.login("admin", "admin")
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
    embedding_gen = DummyEmbeddingGenerator(dimensions=384)
    user_id = 100

    documents = [
        {
            "id": 1,
            "vector": embedding_gen.encode("Q4 Budget Report - Financial analysis"),
            "metadata": {
                "title": "Q4 Budget Report",
                "department": "Finance",
                "type": "report",
            },
        },
        {
            "id": 2,
            "vector": embedding_gen.encode("Team collaboration guidelines"),
            "metadata": {
                "title": "Team Wiki",
                "department": "Engineering",
                "type": "documentation",
            },
        },
        {
            "id": 3,
            "vector": embedding_gen.encode("Project technical requirements"),
            "metadata": {
                "title": "Project Specification",
                "department": "Engineering",
                "type": "specification",
            },
        },
    ]

    print(f"   ✓ Prepared {len(documents)} documents")

    # Insert documents
    print("\n4️⃣  Inserting documents...")
    try:
        for doc in documents:
            result = client.insert(
                node_id=doc["id"],
                vector=doc["vector"],
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

    # Search for documents
    print("\n5️⃣  Searching documents...")
    queries = [
        ("financial analysis", "Search for financial documents"),
        ("technical requirements", "Search for technical documents"),
        ("team guidelines", "Search for collaboration documents"),
    ]

    for query_text, description in queries:
        print(f"\n   {description}:")
        print(f"   Query: '{query_text}'")
        try:
            query_vector = embedding_gen.encode(query_text)
            results = client.search(query_vector, user_id=user_id, k=3)

            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                title = result["metadata"].get("title", "Unknown")
                similarity = result.get("similarity", 0)
                print(f"   {i}. {title} - similarity: {similarity:.4f}")
        except Exception as e:
            print(f"   ❌ Search error: {e}")

    # Demonstrate text insertion and search
    print("\n6️⃣  Text insertion and search...")
    try:
        # Insert with text
        client.insert_text(
            node_id=4,
            text="Marketing strategy for product launch",
            metadata={"department": "Marketing", "type": "strategy"},
            embedding_generator=embedding_gen,
            user_id=user_id,
        )
        print("   ✓ Inserted text document with ID: 4")

        # Search with text
        results = client.search_text(
            query="product marketing",
            embedding_generator=embedding_gen,
            user_id=user_id,
            k=2,
        )
        print(f"   ✓ Text search found {len(results)} results:")
        for result in results:
            title = result["metadata"].get("title", "Unknown")
            print(f"     - {title}")
    except Exception as e:
        print(f"   ❌ Text operation error: {e}")

    # Cleanup
    print("\n7️⃣  Cleanup...")
    client.disconnect()
    print("   ✓ Disconnected from server")

    print("\n✅ Example completed successfully!")


if __name__ == "__main__":
    main()
