#!/usr/bin/env python3
"""
Metadata Filtering Example for RiceDB.

This example demonstrates how to filter search results using metadata fields.
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
    print(" RiceDB Metadata Filtering Example\n")

    # Initialize client (auto-selects transport)
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL

    # Connect to the server
    if not client.connect():
        print(" Failed to connect to RiceDB server")
        return
    client.login("admin", PASSWORD)

    # 1. Insert Documents with Metadata
    print("1. Inserting documents...")

    docs = [
        (1, "The quick brown fox", {"category": "animal", "color": "brown"}),
        (2, "The lazy dog", {"category": "animal", "color": "white"}),
        (3, "The red apple", {"category": "fruit", "color": "red"}),
        (4, "The brown bear", {"category": "animal", "color": "brown"}),
    ]

    for node_id, text, meta in docs:
        client.insert(node_id, text, meta, user_id=1)
        print(f"   Inserted ID {node_id}: {text} ({meta})")

    # 2. Search without filter
    print("\n2. Search 'brown' without filter:")
    results = client.search("brown", user_id=1, k=5)
    for res in results:
        print(f"   - ID {res['id']}: {res['metadata']}")

    # 3. Search with Filter (Category: animal)
    print("\n3. Search 'brown' with filter {'category': 'animal'}:")
    results = client.search("brown", user_id=1, k=5, filter={"category": "animal"})
    for res in results:
        print(f"   - ID {res['id']}: {res['metadata']}")

    # 4. Search with Filter (Color: brown)
    print("\n4. Search 'brown' with filter {'color': 'brown'}:")
    results = client.search("brown", user_id=1, k=5, filter={"color": "brown"})
    for res in results:
        print(f"   - ID {res['id']}: {res['metadata']}")

    # 5. Search with ID Filter (Metadata ID)
    # Assuming we added an external_id in metadata
    print("\n5. Inserting doc with external_id...")
    client.insert(5, "Special Document", {"external_id": "ext-123"}, user_id=1)

    print("   Searching with filter {'external_id': 'ext-123'}:")
    results = client.search("Special", user_id=1, k=5, filter={"external_id": "ext-123"})
    for res in results:
        print(f"   - ID {res['id']}: {res['metadata']}")

    client.disconnect()


if __name__ == "__main__":
    main()
