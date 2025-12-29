#!/usr/bin/env python3
"""
Test script for Nested Overlays and Holographic Merge.
"""

import os
import time
from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def main():
    print("🔹 RiceDB Nested Overlays Test")

    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print("❌ Failed to connect to RiceDB server")
        return

    client.login("admin", PASSWORD)

    # 1. Create Base Node
    print("\n1. Inserting Base Node (ID 100)...")
    client.insert(100, "Base Knowledge", {"source": "base"}, user_id=1)

    # 2. Create Supervisor Session
    print("\n2. Creating Supervisor Session...")
    supervisor_id = client.create_session()
    print(f"   Supervisor ID: {supervisor_id}")

    # 3. Modify Node in Supervisor Session
    print("   -> Supervisor updates Node 100...")
    client.insert(
        100, "Supervisor Knowledge", {"source": "supervisor"}, user_id=1, session_id=supervisor_id
    )

    # 4. Create Worker Session (Nested)
    print("\n3. Creating Worker Session (Child of Supervisor)...")
    try:
        worker_id = client.create_session(parent_session_id=supervisor_id)
        print(f"   Worker ID: {worker_id}")
    except TypeError:
        print("❌ Client does not support parent_session_id yet!")
        return

    # 5. Worker Reads Node 100 (Should see Supervisor's version)
    print("   -> Worker searching for Node 100...")
    res = client.search("knowledge", user_id=1, k=1, session_id=worker_id)
    if res and res[0]["metadata"]["source"] == "supervisor":
        print("✅ Worker sees Supervisor's update (Inheritance).")
    else:
        print(f"❌ Worker saw: {res[0]['metadata'] if res else 'Nothing'}")

    # 6. Worker Updates Node 100
    print("   -> Worker updates Node 100...")
    client.insert(100, "Worker Knowledge", {"source": "worker"}, user_id=1, session_id=worker_id)

    # 7. Commit Worker to Supervisor (Merge)
    print("\n4. Committing Worker Session to Supervisor...")
    # Use bundle strategy (just to test API, though text bundling isn't implemented in server logic for insert, only vector)
    # But insert updates vector.
    client.commit_session(worker_id, merge_strategy="overwrite")
    print("✅ Worker committed.")

    # 8. Verify Supervisor sees Worker's update
    print("   -> Supervisor searching for Node 100...")
    res = client.search("knowledge", user_id=1, k=1, session_id=supervisor_id)
    if res and res[0]["metadata"]["source"] == "worker":
        print("✅ Supervisor sees Worker's update (Merge Up).")
    else:
        print(f"❌ Supervisor saw: {res[0]['metadata'] if res else 'Nothing'}")

    # 9. Verify Base is UNTOUCHED
    print("   -> Checking Base...")
    res = client.search("knowledge", user_id=1, k=1)
    # Search might return node 100 from base.
    # Note: Search results are vectors.
    # We need to check metadata.
    # Since we didn't commit Supervisor to Base, Base should be original.

    # Wait, search returns merged view if session_id is provided. If not provided, it returns Base.
    # But we updated ID 100 in base? Yes in step 1.
    if res and res[0]["metadata"]["source"] == "base":
        print("✅ Base is untouched.")
    else:
        print(f"❌ Base was modified! Saw: {res[0]['metadata'] if res else 'Nothing'}")

    client.disconnect()


if __name__ == "__main__":
    main()
