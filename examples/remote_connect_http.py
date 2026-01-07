#!/usr/bin/env python3
"""
Remote connection example for RiceDB (HTTP).
"""

import os
from dotenv import load_dotenv
from ricedb.client.http_client import HTTPRiceDBClient

# Load .env explicitly from the examples directory
env_path = os.path.join(os.path.dirname(__file__), ".env")
load_dotenv(env_path)

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "3000"))
PASSWORD = os.environ.get("PASSWORD", "admin")
# HTTP client uses base_url usually "http://host:port" or just host/port params.
# HTTPRiceDBClient takes (host, port, timeout).


def main():
    print(" RiceDB Remote Connection Example (HTTP)\n")

    print(f"1  Connecting to {HOST}:{PORT} (HTTP)...")

    # Initialize client
    client = HTTPRiceDBClient(host=HOST, port=PORT)

    try:
        # HTTP client usually doesn't have explicit connect() but maybe for consistency
        if hasattr(client, "connect"):
            client.connect()
        print(f"    Client initialized")

        # Login
        print("\n2  Logging in as Admin...")
        try:
            client.login("admin", PASSWORD)
            print("    Logged in successfully")
        except Exception as e:
            print(f"    Login failed: {e}")
            return

        # Check health
        print("\n3  Checking server health...")
        try:
            health = client.health()
            print(f"    Status: {health.get('status', 'Unknown')}")
            print(f"    Version: {health.get('version', 'Unknown')}")
        except Exception as e:
            print(f"    Health check failed: {e}")

        # Basic operation
        print("\n4  Performing test insert...")
        try:
            result = client.insert(
                node_id=999,
                text="Remote connection test HTTP",
                metadata={"source": "remote_script_http"},
                user_id=1,
            )
            print(f"    Insert result: {result}")
        except Exception as e:
            print(f"    Insert failed: {e}")

    except Exception as e:
        print(f"    Error: {e}")
    finally:
        if hasattr(client, "disconnect"):
            client.disconnect()
        print("\n    Disconnected")


if __name__ == "__main__":
    main()
