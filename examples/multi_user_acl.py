#!/usr/bin/env python3
"""
Multi-User ACL Example for RiceDB

This example demonstrates how to:
1. Manage users (Admin operations)
2. Insert documents with permissions
3. Grant and revoke permissions
4. Search with ACL filtering (User context)
"""

import os
import sys
import time
from dotenv import load_dotenv

# Add the ricedb package to the path
sys.path.insert(0, "../src")

from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print("=" * 50)


def print_success(message: str):
    """Print a success message."""
    print(f"✅ {message}")


def print_info(message: str):
    """Print an info message."""
    print(f"ℹ️  {message}")


def print_error(message: str):
    """Print an error message."""
    print(f"❌ {message}")


def main():
    print_section("Multi-User ACL Demo for RiceDB")

    # Initialize admin client
    print_info("Connecting as Admin...")
    # ACL Management is typically done via HTTP admin client on port 3000 by default,
    # but here we use main port/transport from env
    admin_client = RiceDBClient(
        HOST, port=PORT, transport="http"
    )  # Force HTTP for admin ops if needed or use main transport
    # Actually most examples use main client. Let's use env config.
    # Note: multi_user_acl.py used port=3000 hardcoded.
    # If the user sets PORT=50051 (gRPC), we should respect it or use a separate admin port var?
    # For simplicity, let's assume HOST/PORT points to the service we want to use.
    # But if transport="http" is hardcoded, it expects HTTP port.
    # Let's try to infer or just use provided PORT.

    # If user provided 50051 (gRPC), force http might fail if it's strictly gRPC port?
    # RiceDB usually exposes both?
    # Let's trust the env vars. If SSL=true, it might be remote.

    # Update: using standard client init
    admin_client = RiceDBClient(HOST, port=PORT, transport="http")
    admin_client.ssl = SSL

    try:
        if not admin_client.connect():
            print_error("Failed to connect to RiceDB server")
            return

        # Login as admin (default credentials if not changed)
        # In a real scenario, these would come from env vars or secure storage
        try:
            admin_client.login("admin", PASSWORD)
            print_success("Logged in as Admin")
        except Exception as e:
            print_error(f"Admin login failed: {e}")
            print_info("Ensure the server is running and initialized.")
            return

        # Create users
        print_section("1. User Management")
        users_config = {
            "alice": {"role": "user", "dept": "Finance", "pass": "alice123"},
            "bob": {"role": "user", "dept": "Engineering", "pass": "bob123"},
            "charlie": {"role": "user", "dept": "Finance", "pass": "charlie123"},
            "diana": {"role": "user", "dept": "Engineering", "pass": "diana123"},
        }

        user_clients = {}
        users = {}

        for name, info in users_config.items():
            print_info(f"Creating user '{name}'...")
            try:
                # Delete if exists (cleanup from previous runs)
                try:
                    admin_client.delete_user(name)
                except:
                    pass

                user_id = admin_client.create_user(name, info["pass"], info["role"])
                users[name] = {**info, "id": user_id}
                print_success(f"Created {name} (ID: {user_id})")

                # Create client for this user
                client = RiceDBClient(HOST, port=PORT, transport="http")
                client.ssl = SSL
                client.connect()
                client.login(name, info["pass"])
                user_clients[name] = client

            except Exception as e:
                print_error(f"Failed to create/login {name}: {e}")

        # Document 1: Financial Report (Created by Alice)
        print_section("2. Creating Documents")

        print_info("\nAlice inserting Q4 Budget Report...")
        alice_client = user_clients["alice"]

        # Alice inserts and grants read access to Charlie (Analyst)
        # Note: In the new system, insert makes Alice the owner.
        # She then grants permissions to others.
        result1 = alice_client.insert(
            node_id=1001,
            text="Q4 2023 Budget Report - Financial analysis and projections",
            metadata={
                "title": "Q4 2023 Budget Report",
                "type": "Financial Report",
                "department": "Finance",
                "sensitive": True,
            },
        )
        # Alice grants read to Charlie
        alice_client.grant_permission(
            1001, users["charlie"]["id"], {"read": True, "write": False, "delete": False}
        )
        print_success("Document inserted and shared with Charlie")

        # Document 2: Technical Spec (Created by Bob)
        print_info("\nBob inserting API Documentation...")
        bob_client = user_clients["bob"]
        result2 = bob_client.insert(
            node_id=2001,
            text="API v2 Documentation - Endpoints and schemas",
            metadata={
                "title": "API v2 Documentation",
                "type": "Technical Documentation",
                "department": "Engineering",
            },
        )
        # Bob grants read to Diana
        bob_client.grant_permission(
            2001, users["diana"]["id"], {"read": True, "write": False, "delete": False}
        )
        print_success("Document inserted and shared with Diana")

        print_section("3. Testing Permissions")

        # Test: Charlie reading Alice's report
        print_info("Charlie searching for reports...")
        charlie_client = user_clients["charlie"]
        results = charlie_client.search("budget report", user_id=users["charlie"]["id"])
        found = any(r["id"] == 1001 for r in results)
        if found:
            print_success("Charlie found the Budget Report")
        else:
            print_error("Charlie could NOT find the Budget Report")

        # Test: Bob reading Alice's report (Should fail)
        print_info("Bob searching for reports...")
        results = bob_client.search("budget report", user_id=users["bob"]["id"])
        found = any(r["id"] == 1001 for r in results)
        if not found:
            print_success("Bob could NOT find the Budget Report (Correct)")
        else:
            print_error("Bob found the Budget Report (Unexpected)")

        print_section("4. Revoking Permissions")

        # Alice revokes Charlie's access
        print_info("Alice revoking Charlie's access...")
        alice_client.revoke_permission(1001, users["charlie"]["id"])

        # Verify
        results = charlie_client.search("budget report", user_id=users["charlie"]["id"])
        found = any(r["id"] == 1001 for r in results)
        if not found:
            print_success("Charlie can no longer see the report")
        else:
            print_error("Charlie can still see the report")

        print_section("5. Summary")
        print_success("Multi-User ACL Demo completed successfully!")

    except Exception as e:
        print_error(f"Error during demo: {e}")
    finally:
        admin_client.disconnect()
        for c in user_clients.values():
            c.disconnect()


if __name__ == "__main__":
    main()
