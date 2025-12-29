#!/usr/bin/env python3
"""
Remote connection example for RiceDB.

This script demonstrates connecting to a remote RiceDB instance
deployed on Kubernetes with Nginx Ingress.
"""

import os
from dotenv import load_dotenv
from ricedb.client.grpc_client import GrpcRiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def main():
    print("🍚 RiceDB Remote Connection Example\n")

    print(f"1️⃣  Connecting to {HOST}:{PORT} (SSL={SSL})...")

    # Initialize client directly to see errors
    client = GrpcRiceDBClient(host=HOST, port=PORT)
    client.ssl = SSL

    # Try with certifi properly
    import certifi
    import os

    os.environ["GRPC_DEFAULT_SSL_ROOTS_FILE_PATH"] = certifi.where()

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
