#!/usr/bin/env python3
"""
Multi-User ACL Example for RiceDB

This example demonstrates how to:
1. Insert documents with multiple user permissions
2. Grant and revoke permissions
3. Check permissions
4. Perform batch permission operations
5. Search with ACL filtering
"""

import sys

# Add the ricedb package to the path
sys.path.insert(0, "../src")

from ricedb import RiceDBClient


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

    # Initialize client with HTTP transport for ACL support
    print_info("Connecting to RiceDB via HTTP...")
    client = RiceDBClient(
        host="localhost",
        port=3000,
        transport="http",  # Required for ACL support
    )

    try:
        # Connect to the server
        if not client.connect():
            print_error("Failed to connect to RiceDB server")
            print("\nMake sure the HTTP server is running:")
            print("  make run-http")
            return

        print_success("Connected to RiceDB server")

        # Check transport info
        transport_info = client.get_transport_info()
        print_info(f"Using transport: {transport_info['type']}")
        print_info(f"ACL support: {transport_info['acl_support']}")

        # Define users for our demo
        users = {
            "alice": {"id": 100, "role": "Manager", "dept": "Finance"},
            "bob": {"id": 200, "role": "Engineer", "dept": "Engineering"},
            "charlie": {"id": 300, "role": "Analyst", "dept": "Finance"},
            "diana": {"id": 400, "role": "Intern", "dept": "Engineering"},
        }

        print_section("Users in this Demo")
        for name, info in users.items():
            print(
                f"  {name.capitalize()} (ID: {info['id']}) - {info['role']} in {info['dept']}"
            )

        # Create documents with different access patterns
        print_section("1. Inserting Documents with Multi-User ACL")

        # Document 1: Financial Report (Finance team access)
        print_info("\nInserting Q4 Budget Report (Finance team only)...")
        result1 = client.insert_with_acl(
            node_id=1001,
            vector=[0.1, 0.2, 0.3, 0.4, 0.5],
            metadata={
                "title": "Q4 2023 Budget Report",
                "type": "Financial Report",
                "department": "Finance",
                "sensitive": True,
            },
            user_permissions=[
                (
                    users["alice"]["id"],
                    {"read": True, "write": True, "delete": True},
                ),  # Manager - full access
                (
                    users["charlie"]["id"],
                    {"read": True, "write": False, "delete": False},
                ),  # Analyst - read-only
            ],
        )
        print_success(
            f"Document inserted with ACL for {len(result1.get('acl_users', []))} users"
        )

        # Document 2: Technical Spec (Engineering team access)
        print_info("\nInserting API Documentation (Engineering team)...")
        result2 = client.insert_with_acl(
            node_id=2001,
            vector=[0.6, 0.7, 0.8, 0.9, 1.0],
            metadata={
                "title": "API v2 Documentation",
                "type": "Technical Documentation",
                "department": "Engineering",
                "public": False,
            },
            user_permissions=[
                (
                    users["bob"]["id"],
                    {"read": True, "write": True, "delete": False},
                ),  # Engineer - can edit
                (
                    users["diana"]["id"],
                    {"read": True, "write": False, "delete": False},
                ),  # Intern - read-only
            ],
        )
        print_success(
            f"Document inserted with ACL for {len(result2.get('acl_users', []))} users"
        )

        # Document 3: Company Handbook (All employees)
        print_info("\nInserting Company Handbook (All employees)...")
        result3 = client.insert_with_acl(
            node_id=3001,
            vector=[0.2, 0.4, 0.6, 0.8, 1.0],
            metadata={
                "title": "Employee Handbook 2023",
                "type": "Company Policy",
                "public": True,
            },
            user_permissions=[
                (uid, {"read": True, "write": False, "delete": False})
                for uid in [u["id"] for u in users.values()]
            ],
        )
        print_success(
            f"Document inserted with ACL for {len(result3.get('acl_users', []))} users"
        )

        print_section("2. Testing Individual Permissions")

        # Test permissions for each user on each document
        test_cases = [
            (
                1001,
                "Q4 Budget Report",
                [
                    ("Alice", users["alice"]["id"], ["read", "write", "delete"]),
                    ("Charlie", users["charlie"]["id"], ["read"]),
                    ("Bob", users["bob"]["id"], []),
                ],
            ),
            (
                2001,
                "API Documentation",
                [
                    ("Bob", users["bob"]["id"], ["read", "write"]),
                    ("Diana", users["diana"]["id"], ["read"]),
                    ("Alice", users["alice"]["id"], []),
                ],
            ),
            (
                3001,
                "Employee Handbook",
                [
                    ("Alice", users["alice"]["id"], ["read"]),
                    ("Bob", users["bob"]["id"], ["read"]),
                    ("Charlie", users["charlie"]["id"], ["read"]),
                    ("Diana", users["diana"]["id"], ["read"]),
                ],
            ),
        ]

        for doc_id, doc_title, tests in test_cases:
            print(f"\nTesting permissions for: {doc_title}")
            for user_name, user_id, expected_perms in tests:
                for perm in ["read", "write", "delete"]:
                    has_perm = client.check_permission(doc_id, user_id, perm)
                    expected = perm in expected_perms
                    status = "✓" if has_perm == expected else "✗"
                    print(f"  {status} {user_name} can {perm}: {has_perm}")

        print_section("3. Granting Additional Permissions")

        # Grant Diana write access to the API documentation
        print_info("\nGranting Diana write access to API Documentation...")
        client.grant_permission(
            node_id=2001,
            user_id=users["diana"]["id"],
            permissions={"read": True, "write": True, "delete": False},
        )
        print_success("Permission granted successfully")

        # Verify the new permission
        can_write = client.check_permission(2001, users["diana"]["id"], "write")
        print_info(f"Diana can now write to API Documentation: {can_write}")

        print_section("4. Batch Permission Operations")

        # Create a new document that multiple users need access to
        print_info("\nCreating project status update...")
        client.insert(
            node_id=4001,
            vector=[0.3, 0.6, 0.9, 0.2, 0.5],
            metadata={
                "title": "Q1 2024 Project Status",
                "type": "Status Report",
                "cross_departmental": True,
            },
            user_id=users["alice"]["id"],  # Alice creates it
        )
        print_success("Document created by Alice")

        # Batch grant permissions to all users
        print_info("\nGranting read access to all users...")
        batch_grants = [
            (4001, users["bob"]["id"], {"read": True, "write": True}),
            (4001, users["charlie"]["id"], {"read": True, "write": False}),
            (4001, users["diana"]["id"], {"read": True, "write": False}),
        ]
        client.batch_grant(batch_grants)
        print_success(f"Batch granted permissions to {len(batch_grants)} users")

        print_section("5. Searching with ACL Filtering")

        # Test search from different user perspectives
        query_vector = [0.25, 0.35, 0.45, 0.55, 0.65]

        print_info("\nAlice's search results (Finance Manager):")
        alice_results = client.search(query_vector, users["alice"]["id"], k=10)
        for r in alice_results:
            print(
                f"  - {r.get('metadata', {}).get('title', 'Untitled')} (ID: {r.get('id')})"
            )

        print_info("\nBob's search results (Engineer):")
        bob_results = client.search(query_vector, users["bob"]["id"], k=10)
        for r in bob_results:
            print(
                f"  - {r.get('metadata', {}).get('title', 'Untitled')} (ID: {r.get('id')})"
            )

        print_info("\nDiana's search results (Intern):")
        diana_results = client.search(query_vector, users["diana"]["id"], k=10)
        for r in diana_results:
            print(
                f"  - {r.get('metadata', {}).get('title', 'Untitled')} (ID: {r.get('id')})"
            )

        print_section("6. Revoking Permissions")

        # Revoke Charlie's access to the budget report (role change)
        print_info("\nRevoking Charlie's access to Budget Report (role change)...")
        client.revoke_permission(1001, users["charlie"]["id"])
        print_success("Permission revoked")

        # Verify revocation
        can_read = client.check_permission(1001, users["charlie"]["id"], "read")
        print_info(f"Charlie can still read Budget Report: {can_read}")

        print_section("7. Summary")

        print_info("\nDocuments created:")
        print("  1. Q4 Budget Report - Finance team access")
        print("  2. API Documentation - Engineering team access")
        print("  3. Employee Handbook - All employees")
        print("  4. Project Status - Cross-departmental access")

        print_info("\nACL operations demonstrated:")
        print("  ✓ Insert with multiple user permissions")
        print("  ✓ Check individual permissions")
        print("  ✓ Grant additional permissions")
        print("  ✓ Batch permission operations")
        print("  ✓ Search with ACL filtering")
        print("  ✓ Revoke permissions")

        print_success("\nMulti-User ACL Demo completed successfully!")

    except Exception as e:
        print_error(f"Error during demo: {e}")
        print("\nTroubleshooting:")
        print("1. Make sure RiceDB HTTP server is running: make run-http")
        print("2. Check that port 3000 is available")
        print("3. Verify the server has ACL endpoints enabled")

    finally:
        # Disconnect from the server
        client.disconnect()
        print_info("\nDisconnected from RiceDB server")


if __name__ == "__main__":
    main()
