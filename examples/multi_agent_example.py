#!/usr/bin/env python3
"""
Multi-user ACL example for RiceDB.

This example demonstrates:
1. Access Control List (ACL) functionality
2. Multiple users with different permissions
3. User-specific data isolation
"""

from ricedb import RiceDBClient
from ricedb.utils import DummyEmbeddingGenerator


def main():
    print("🍚 RiceDB Python Client - Multi-User ACL Example\n")

    # Initialize client
    client = RiceDBClient("localhost")

    # Connect to the server
    print("1️⃣  Connecting to RiceDB server...")
    if not client.connect():
        print("   ❌ Failed to connect to RiceDB server")
        return
    print(f"   ✓ Connected via {client.get_transport_info()['type'].upper()}")

    # User IDs for different roles
    users = {
        "alice": {"id": 100, "role": "Manager", "dept": "Finance"},
        "bob": {"id": 200, "role": "Engineer", "dept": "Engineering"},
        "charlie": {"id": 300, "role": "Marketing", "dept": "Marketing"},
        "diana": {"id": 400, "role": "HR", "dept": "Human Resources"},
    }

    print("\n2️⃣  User configuration:")
    for name, info in users.items():
        print(
            f"   - {name.title()} (ID: {info['id']}): {info['role']} in {info['dept']}"
        )

    # Prepare documents for each user
    print("\n3️⃣  Preparing user-specific documents...")
    embedding_gen = DummyEmbeddingGenerator()

    documents_by_user = {
        100: [  # Alice - Finance Manager
            {"id": 1001, "text": "Q4 Budget Report", "type": "Financial Report"},
            {"id": 1002, "text": "Salary Structure Review", "type": "HR Document"},
            {
                "id": 1003,
                "text": "Investment Portfolio Analysis",
                "type": "Financial Analysis",
            },
        ],
        200: [  # Bob - Engineer
            {"id": 2001, "text": "API Documentation", "type": "Technical Doc"},
            {
                "id": 2002,
                "text": "System Architecture Design",
                "type": "Technical Spec",
            },
            {"id": 2003, "text": "Code Review Guidelines", "type": "Process Doc"},
        ],
        300: [  # Charlie - Marketing
            {"id": 3001, "text": "Product Launch Campaign", "type": "Marketing Plan"},
            {"id": 3002, "text": "Social Media Strategy", "type": "Marketing Doc"},
            {"id": 3003, "text": "Brand Guidelines", "type": "Brand Doc"},
        ],
        400: [  # Diana - HR
            {"id": 4001, "text": "Employee Handbook", "type": "HR Policy"},
            {"id": 4002, "text": "Performance Review Process", "type": "HR Process"},
            {"id": 4003, "text": "Training Programs", "type": "Training Doc"},
        ],
    }

    # Insert documents for each user
    print("\n4️⃣  Inserting documents with user-specific ACL...")
    for user_id, docs in documents_by_user.items():
        user_name = next(name for name, info in users.items() if info["id"] == user_id)
        print(f"\n   Inserting documents for {user_name.title()} (User ID: {user_id}):")

        for doc in docs:
            try:
                result = client.insert_text(
                    node_id=doc["id"],
                    text=doc["text"],
                    metadata={
                        "type": doc["type"],
                        "owner": user_name,
                        "department": users[user_name]["dept"],
                    },
                    embedding_generator=embedding_gen,
                    user_id=user_id,
                )
                print(f"     ✓ {doc['text']} ({doc['type']})")
            except Exception as e:
                print(f"     ❌ Failed to insert: {e}")

    # Search as each user
    print("\n5️⃣  Searching as each user (ACL-enforced)...")
    search_query = "guidelines"

    for user_id, user_info in users.items():
        user_name = (
            user_info["name"]
            if "name" in user_info
            else next(name for name, info in users.items() if info["id"] == user_id)
        )
        print(f"\n   Search as {user_name.title()} (User ID: {user_id}):")
        print(f"   Query: '{search_query}'")

        try:
            results = client.search_text(
                query=search_query,
                embedding_generator=embedding_gen,
                user_id=user_id,
                k=5,
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
    alice_id = users["alice"]["id"]
    bob_id = users["bob"]["id"]

    # Alice trying to search Bob's documents
    print(f"\n   Alice (User ID: {alice_id}) searching for Bob's documents:")
    try:
        # Alice searches for "API" which should be in Bob's documents
        results = client.search_text(
            query="API", embedding_generator=embedding_gen, user_id=alice_id, k=5
        )
        print(f"   Alice found {len(results)} API-related documents")
        # Should find 0 if ACL is working properly
    except Exception as e:
        print(f"   ❌ Error: {e}")

    # Bob searching for his own API documents
    print(f"\n   Bob (User ID: {bob_id}) searching for API documents:")
    try:
        results = client.search_text(
            query="API", embedding_generator=embedding_gen, user_id=bob_id, k=5
        )
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
        # Insert a document as user 100 but make it accessible to others
        # Note: In a real implementation, you'd need ACL modification APIs
        # For now, we'll insert documents for each user with the same content
        shared_text = "Company Holiday Schedule 2024"
        shared_type = "Company Policy"

        for user_id in users.values():
            user_id = user_id["id"]
            shared_doc_id = 5000 + user_id  # Unique ID per user

            client.insert_text(
                node_id=shared_doc_id,
                text=shared_text,
                metadata={"type": shared_type, "access": "all", "shared": True},
                embedding_generator=embedding_gen,
                user_id=user_id,
            )

        print(f"   ✓ Inserted '{shared_text}' for all users")

        # Each user should now be able to find it
        print("\n   All users searching for 'holiday schedule':")
        for user_info in users.values():
            user_id = user_info["id"]
            user_name = next(
                name for name, info in users.items() if info["id"] == user_id
            )

            results = client.search_text(
                query="holiday schedule",
                embedding_generator=embedding_gen,
                user_id=user_id,
                k=3,
            )
            print(f"   - {user_name.title()}: Found {len(results)} result(s)")

    except Exception as e:
        print(f"   ❌ Shared document error: {e}")

    # Cleanup
    print("\n8️⃣  Cleanup...")
    client.disconnect()
    print("   ✓ Disconnected from server")

    print("\n✅ Multi-user ACL example completed!")
    print("\n💡 Key observations:")
    print("   - Users can only see their own documents")
    print("   - ACL enforcement happens at the server level")
    print("   - Shared documents can be implemented per user")
    print("   - User isolation ensures data privacy")


if __name__ == "__main__":
    main()
