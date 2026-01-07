#!/usr/bin/env python3
"""
HTTP usage example for RiceDB Python client.
Forces HTTP transport.
"""

import os
from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def main():
    print(" RiceDB Python Client - HTTP Usage Example\n")

    # Initialize client (force HTTP)
    client = RiceDBClient(HOST, port=PORT, transport="http")
    client.ssl = SSL

    # Connect to the server
    print("1  Connecting to RiceDB server (HTTP)...")
    try:
        if client.connect():
            transport_info = client.get_transport_info()
            print(f"    Connected via {transport_info['type'].upper()}")

            # Login
            print("    Logging in...")
            client.login("admin", PASSWORD)
            print("    Logged in successfully")
        else:
            print("    Failed to connect to RiceDB server")
            return
    except Exception as e:
        print(f"    Connection error: {e}")
        return

    # Basic insert/search (same as basic_usage)
    # ... simplified for brevity, just one insert/search

    print("\n2  Test Insert...")
    try:
        result = client.insert(
            node_id=1,
            text="HTTP Test Document",
            metadata={"test": "http"},
        )
        print(f"    Inserted: {result.get('success')}")
    except Exception as e:
        print(f"    Insert error: {e}")

    print("\n3  Test Search...")
    try:
        results = client.search(query="test document", user_id=1)
        print(f"    Found {len(results)} results")
    except Exception as e:
        print(f"    Search error: {e}")

    client.disconnect()


if __name__ == "__main__":
    main()
