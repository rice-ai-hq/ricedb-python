#!/usr/bin/env python3
"""
Remote connection example for RiceDB.

This script demonstrates connecting to a remote RiceDB instance
deployed on Kubernetes with Nginx Ingress.
"""

import os
from ricedb.client.grpc_client import GrpcRiceDBClient


def main():
    print("🍚 RiceDB Remote Connection Example\n")

    # Configuration from environment or defaults
    HOST = os.environ.get("RICEDB_HOST", "grpc.ricedb-test-2.ricedb.tryrice.com")
    PORT = int(os.environ.get("RICEDB_PORT", "80"))
    PASSWORD = os.environ.get("RICEDB_PASSWORD", "58c4e3a35d0f1188546995f16c14260c")
    SSL = os.environ.get("RICEDB_SSL", "false").lower() == "true"

    print(f"1️⃣  Connecting to {HOST}:{PORT} (SSL={SSL})...")

    # Initialize client directly to see errors
    client = GrpcRiceDBClient(host=HOST, port=PORT)
    client.ssl = SSL

    try:
        # Calling connect directly will raise exception if it fails
        client.connect()
        print(f"   ✓ Connected via gRPC")

        # Login
        print("\n2️⃣  Logging in as Admin...")
        try:
            client.login("admin", PASSWORD)
            print("   ✓ Logged in successfully")
        except Exception as e:
            print(f"   ❌ Login failed: {e}")
            return

        # Check health
        print("\n3️⃣  Checking server health...")
        health = client.health()
        print(f"   ✓ Status: {health.get('status')}")
        print(f"   ✓ Version: {health.get('version')}")

        # Basic operation
        print("\n4️⃣  Performing test insert...")
        try:
            result = client.insert_text(
                node_id=999,
                text="Remote connection test",
                metadata={"source": "remote_script"},
                user_id=1,
            )
            print(f"   ✓ Insert result: {result.get('message', 'Success')}")
        except Exception as e:
            print(f"   ❌ Insert failed: {e}")

    except Exception as e:
        print(f"   ❌ Error: {e}")
    finally:
        client.disconnect()
        print("\n   ✓ Disconnected")


if __name__ == "__main__":
    main()
