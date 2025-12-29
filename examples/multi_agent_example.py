#!/usr/bin/env python3
"""
Multi-user ACL example for RiceDB.

This example demonstrates:
1. Access Control List (ACL) functionality
2. Multiple users with different permissions
3. User-specific data isolation
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
    print("🍚 RiceDB Python Client - Multi-User ACL Example\n")

    # Initialize client
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL

    # Connect to the server
    print("1️⃣  Connecting to RiceDB server...")
    if not client.connect():
        print("   ❌ Failed to connect to RiceDB server")
        return
    print(f"   ✓ Connected via {client.get_transport_info()['type'].upper()}")

    # Authenticate as Admin
    print("   🔑 Logging in as Admin...")
    try:
        client.login("admin", PASSWORD)
    except Exception as e:
        print(f"   ❌ Login failed: {e}")
        return

    # User configuration
    users_config = {
        "alice": {"role": "Manager", "dept": "Finance", "pass": "alice123"},
        "bob": {"role": "Engineer", "dept": "Engineering", "pass": "bob123"},
        "charlie": {"role": "Marketing", "dept": "Marketing", "pass": "charlie123"},
        "diana": {"role": "HR", "dept": "Human Resources", "pass": "diana123"},
    }

    # Create users and get real IDs
    print("\n2️⃣  Creating users...")
    users = {}
    user_clients = {}

    for name, info in users_config.items():
        try:
            # Cleanup if exists
            try:
                client.delete_user(name)
            except:
                pass

            user_id = client.create_user(name, info["pass"], role="user")
            users[name] = {**info, "id": user_id}
            print(f"   ✓ Created {name} (ID: {user_id})")

            # Create authenticated client for this user
            u_client = RiceDBClient(HOST, port=PORT)
            u_client.ssl = SSL
            u_client.connect()
            u_client.login(name, info["pass"])
            user_clients[name] = u_client

        except Exception as e:
            print(f"   ❌ Failed to create {name}: {e}")

    # Prepare documents for each user
    print("\n3️⃣  Preparing user-specific documents...")

    documents_by_user = {
        "alice": [  # Alice - Finance Manager
            {"id": 1001, "text": "Q4 Budget Report", "type": "Financial Report"},
            {"id": 1002, "text": "Salary Structure Review", "type": "HR Document"},
            {
                "id": 1003,
                "text": "Investment Portfolio Analysis",
                "type": "Financial Analysis",
            },
        ],
        "bob": [  # Bob - Engineer
            {"id": 2001, "text": "API Documentation", "type": "Technical Doc"},
            {
                "id": 2002,
                "text": "System Architecture Design",
                "type": "Technical Spec",
            },
            {"id": 2003, "text": "Code Review Guidelines", "type": "Process Doc"},
        ],
        "charlie": [  # Charlie - Marketing
            {"id": 3001, "text": "Product Launch Campaign", "type": "Marketing Plan"},
            {"id": 3002, "text": "Social Media Strategy", "type": "Marketing Doc"},
            {"id": 3003, "text": "Brand Guidelines", "type": "Brand Doc"},
        ],
        "diana": [  # Diana - HR
            {"id": 4001, "text": "Employee Handbook", "type": "HR Policy"},
            {"id": 4002, "text": "Performance Review Process", "type": "HR Process"},
            {"id": 4003, "text": "Training Programs", "type": "Training Doc"},
        ],
    }

    # Insert documents for each user (using their own client)
    print("\n4️⃣  Inserting documents with user-specific ACL...")
    for user_name, docs in documents_by_user.items():
        user_id = users[user_name]["id"]
        u_client = user_clients[user_name]

        print(f"\n   Inserting documents for {user_name.title()} (User ID: {user_id}):")

        for doc in docs:
            try:
                # We use insert. Note that user_id param is ignored by server for ownership,
                # but might be used by client logic if we pass it.
                # Since u_client is authenticated as user, they become the owner.
                result = u_client.insert(
                    node_id=doc["id"],
                    text=doc["text"],
                    metadata={
                        "type": doc["type"],
                        "owner": user_name,
                        "department": users[user_name]["dept"],
                    },
                )
                print(f"     ✓ {doc['text']} ({doc['type']})")
            except Exception as e:
                print(f"     ❌ Failed to insert: {e}")

    # Search as each user
    print("\n5️⃣  Searching as each user (ACL-enforced)...")
    search_query = "guidelines"

    for user_name, user_info in users.items():
        user_id = user_info["id"]
        u_client = user_clients[user_name]

        print(f"\n   Search as {user_name.title()} (User ID: {user_id}):")
        print(f"   Query: '{search_query}'")

        try:
            results = u_client.search(
                query=search_query,
                k=5,
                user_id=user_id,
            )

            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                owner = metadata.get("owner", "Unknown")
                doc_type = metadata.get("type", "Unknown")
                text = metadata.get("text", "No text")
                print(f"   {i}. [{owner}] {text} ({doc_type})")

            if len(results) == 0:
                print("   (No accessible documents - ACL working!)")

        except Exception as e:
            print(f"   ❌ Search error: {e}")

    # Cross-user access attempt
    print("\n6️⃣  Testing cross-user access control...")
    alice_client = user_clients["alice"]
    bob_client = user_clients["bob"]

    # Alice trying to search Bob's documents
    print(f"\n   Alice searching for 'API' (Bob's docs):")
    try:
        results = alice_client.search(query="API", k=5, user_id=users["alice"]["id"])
        print(f"   Alice found {len(results)} API-related documents")
        # Should find 0 if ACL is working properly
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Bob searching for his own API documents
    print(f"\n   Bob searching for 'API':")
    try:
        results = bob_client.search(query="API", k=5, user_id=users["bob"]["id"])
        print(f"   Bob found {len(results)} API-related documents:")
        for result in results:
            metadata = result["metadata"]
            text = metadata.get("text", "No text")
            print(f"     - {text}")
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Shared document example (accessible by all)
    print("\n7️⃣  Inserting a shared document...")
    try:
        # Alice creates a document and shares it with everyone
        shared_text = "Company Holiday Schedule 2024"
        shared_id = 9999

        alice_client.insert(
            node_id=shared_id,
            text=shared_text,
            metadata={"type": "Company Policy", "access": "all", "shared": True},
        )
        print(f"   ✓ Alice inserted '{shared_text}'")

        # Alice grants read permission to others
        print("   ✓ Granting read access to Bob, Charlie, Diana...")
        for name in ["bob", "charlie", "diana"]:
            uid = users[name]["id"]
            alice_client.grant_permission(
                shared_id, uid, {"read": True, "write": False, "delete": False}
            )

        # Each user should now be able to find it
        print("\n   All users searching for 'holiday schedule':")
        for user_name, u_client in user_clients.items():
            results = u_client.search(
                query="holiday schedule",
                k=3,
                user_id=users[user_name]["id"],
            )
            print(f"   - {user_name.title()}: Found {len(results)} result(s)")

    except Exception as e:
        print(f"   ❌ Shared document error: {e}")

    # Cleanup
    print("\n8️⃣  Cleanup...")
    for c in user_clients.values():
        c.disconnect()
    client.disconnect()
    print("   ✓ Disconnected from server")

    print("\n✅ Multi-user ACL example completed!")


if __name__ == "__main__":
    main()
