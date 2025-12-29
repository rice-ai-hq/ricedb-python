#!/usr/bin/env python3
"""
gRPC usage example for RiceDB Python client.
Forces gRPC transport.
"""

from ricedb import RiceDBClient
import time


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

    print("\n2️⃣  Test Insert...")
    try:
        result = client.insert(
            node_id=1,
            text="gRPC Test Document: Hyperdimensional Computing is efficient.",
            metadata={"test": "grpc", "topic": "HDC"},
        )
        print(f"   ✓ Inserted: {result.get('success')}")
    except Exception as e:
        print(f"   ❌ Insert error: {e}")

    print("\n3️⃣  Test Search...")
    try:
        # Search using text
        results = client.search(query="efficient computing", user_id=1, k=5)
        print(f"   ✓ Found {len(results)} results")
        for res in results:
            print(f"     - ID: {res['id']}, Score: {res['similarity']:.4f}")
    except Exception as e:
        print(f"   ❌ Search error: {e}")

    # Streaming search (gRPC only)
    print("\n4️⃣  Test Stream Search...")
    try:
        # stream_search now takes query string
        stream = client.stream_search(query="HDC", user_id=1)
        count = 0
        print("   ✓ Streaming results:")
        for res in stream:
            count += 1
            print(f"     - Streamed ID: {res['id']}")
        print(f"   ✓ Streamed {count} total results")
    except Exception as e:
        print(f"   ❌ Stream search error: {e}")

    client.disconnect()


if __name__ == "__main__":
    main()
