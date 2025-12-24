#!/usr/bin/env python3
"""
gRPC usage example for RiceDB Python client.
Forces gRPC transport.
"""

from ricedb import RiceDBClient
from ricedb.utils import DummyEmbeddingGenerator


def main():
    print("🍚 RiceDB Python Client - gRPC Usage Example\n")

    # Initialize client (force gRPC)
    client = RiceDBClient("localhost", transport="grpc")

    # Connect to the server
    print("1️⃣  Connecting to RiceDB server (gRPC)...")
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
    # ... simplified for brevity

    print("\n2️⃣  Test Insert...")
    embedding_gen = DummyEmbeddingGenerator(dimensions=384)
    try:
        result = client.insert_text(
            node_id=1,
            text="gRPC Test Document",
            metadata={"test": "grpc"},
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

    # Streaming search (gRPC only)
    print("\n4️⃣  Test Stream Search...")
    try:
        stream = client.stream_search(vector=embedding_gen.encode("test"), user_id=1)
        count = 0
        for res in stream:
            count += 1
        print(f"   ✓ Streamed {count} results")
    except Exception as e:
        print(f"   ❌ Stream search error: {e}")

    client.disconnect()


if __name__ == "__main__":
    main()
