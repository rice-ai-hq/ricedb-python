#!/usr/bin/env python3
"""
HTTP usage example for RiceDB Python client.
Forces HTTP transport.
"""

from ricedb import RiceDBClient
from ricedb.utils import DummyEmbeddingGenerator


def main():
    print("🍚 RiceDB Python Client - HTTP Usage Example\n")

    # Initialize client (force HTTP)
    client = RiceDBClient("localhost", transport="http")

    # Connect to the server
    print("1️⃣  Connecting to RiceDB server (HTTP)...")
    try:
        if client.connect():
            transport_info = client.get_transport_info()
            print(f"   ✓ Connected via {transport_info['type'].upper()}")

            # Login
            print("   🔑 Logging in...")
            client.login("admin", "admin")
            print("   ✓ Logged in successfully")
        else:
            print("   ❌ Failed to connect to RiceDB server")
            return
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return

    # Basic insert/search (same as basic_usage)
    # ... simplified for brevity, just one insert/search

    print("\n2️⃣  Test Insert...")
    embedding_gen = DummyEmbeddingGenerator(dimensions=384)
    try:
        result = client.insert_text(
            node_id=1,
            text="HTTP Test Document",
            metadata={"test": "http"},
            embedding_generator=embedding_gen,
        )
        print(f"   ✓ Inserted: {result.get('success')}")
    except Exception as e:
        print(f"   ❌ Insert error: {e}")

    print("\n3️⃣  Test Search...")
    try:
        results = client.search_text(query="test document", embedding_generator=embedding_gen)
        print(f"   ✓ Found {len(results)} results")
    except Exception as e:
        print(f"   ❌ Search error: {e}")

    client.disconnect()


if __name__ == "__main__":
    main()
