#!/usr/bin/env python3
"""
Example using RiceDB with Sentence Transformers for real embeddings.

This example demonstrates:
1. Using real text embeddings from Sentence Transformers
2. More semantic search capabilities
3. Batch operations with text

Prerequisites:
    pip install ricedb[embeddings]
"""

from ricedb import RiceDBClient
from ricedb.utils import SentenceTransformersEmbeddingGenerator


def main():
    print("🍚 RiceDB Python Client - Sentence Transformers Example\n")

    # Initialize client
    client = RiceDBClient("localhost")

    # Connect to the server
    print("1️⃣  Connecting to RiceDB server...")
    try:
        if not client.connect():
            print("   ❌ Failed to connect to RiceDB server")
            return
        transport_info = client.get_transport_info()
        print(f"   ✓ Connected via {transport_info['type'].upper()}")

        # Login
        print("   🔑 Logging in...")
        client.login("admin", "admin")
        print("   ✓ Logged in as admin")
    except Exception as e:
        print(f"   ❌ Connection error: {e}")
        return

    # Initialize Sentence Transformers embedding generator
    print("\n2️⃣  Initializing Sentence Transformers...")
    try:
        embed_gen = SentenceTransformersEmbeddingGenerator(model_name="all-MiniLM-L6-v2")
        print(f"   ✓ Model loaded: {embed_gen.model_name}")
    except Exception as e:
        print(f"   ❌ Failed to load model: {e}")
        print("   Make sure to install: pip install ricedb[embeddings]")
        return

    # Prepare documents with real text
    print("\n3️⃣  Preparing documents...")
    documents = [
        {
            "id": 101,
            "text": "Artificial Intelligence and Machine Learning are transforming industries",
            "metadata": {"category": "Technology", "year": 2023},
        },
        {
            "id": 102,
            "text": "Climate change requires urgent global action to reduce carbon emissions",
            "metadata": {"category": "Environment", "year": 2023},
        },
        {
            "id": 103,
            "text": "The stock market showed volatility amid economic uncertainty",
            "metadata": {"category": "Finance", "year": 2023},
        },
        {
            "id": 104,
            "text": "Space exploration advances with new missions to Mars and beyond",
            "metadata": {"category": "Science", "year": 2023},
        },
        {
            "id": 105,
            "text": "Renewable energy sources like solar and wind are becoming more efficient",
            "metadata": {"category": "Environment", "year": 2023},
        },
    ]

    print(f"   ✓ Prepared {len(documents)} documents")

    # Batch insert documents
    print("\n4️⃣  Batch inserting documents...")
    try:
        # Prepare batch data
        batch_docs = []
        for doc in documents:
            embedding = embed_gen.encode(doc["text"])
            batch_docs.append(
                {
                    "id": doc["id"],
                    "vector": embedding,
                    "metadata": {**doc["metadata"], "text": doc["text"]},
                    "user_id": 100,
                }
            )

        # Perform batch insert
        result = client.batch_insert(batch_docs)
        print(f"   ✓ Inserted {result['count']} documents in batch")
    except Exception as e:
        print(f"   ❌ Batch insert error: {e}")
        return

    # Semantic search queries
    print("\n5️⃣  Performing semantic searches...")
    queries = [
        "technology and innovation",
        "environmental sustainability",
        "economic markets",
        "scientific discoveries",
    ]

    for query in queries:
        print(f"\n   Query: '{query}'")
        try:
            # Generate embedding for query
            query_embedding = embed_gen.encode(query)

            # Search
            results = client.search(query_embedding, user_id=100, k=3)

            print(f"   Found {len(results)} results:")
            for i, result in enumerate(results, 1):
                metadata = result["metadata"]
                text = metadata.get("text", "No text")
                category = metadata.get("category", "Unknown")
                similarity = result.get("similarity", 0)
                print(f"   {i}. [{category}] {text[:60]}... - similarity: {similarity:.4f}")
        except Exception as e:
            print(f"   ❌ Search error: {e}")

    # Find similar documents
    print("\n6️⃣  Finding similar documents...")
    try:
        # Use one document to find similar ones
        reference_embedding = embed_gen.encode("AI technology and automation")

        results = client.search(reference_embedding, user_id=100, k=2)
        print("   Documents similar to 'AI technology and automation':")

        for result in results:
            metadata = result["metadata"]
            text = metadata.get("text", "No text")
            category = metadata.get("category", "Unknown")
            similarity = result.get("similarity", 0)
            print(f"   - [{category}] {text}")
            print(f"     Similarity: {similarity:.4f}")
    except Exception as e:
        print(f"   ❌ Similarity search error: {e}")

    # Demonstrate text-based operations
    print("\n7️⃣  Text-based operations...")
    try:
        # Insert new document using text method
        client.insert_text(
            node_id=106,
            text="Blockchain technology enables secure decentralized transactions",
            metadata={
                "category": "Technology",
                "tags": ["blockchain", "cryptocurrency"],
            },
            embedding_generator=embed_gen,
            user_id=100,
        )
        print("   ✓ Inserted new document with ID: 106")

        # Search for it
        results = client.search_text(
            query="cryptocurrency and digital currency",
            embedding_generator=embed_gen,
            user_id=100,
            k=3,
        )
        print(f"   ✓ Found {len(results)} documents about cryptocurrency")
    except Exception as e:
        print(f"   ❌ Text operation error: {e}")

    # Cleanup
    print("\n8️⃣  Cleanup...")
    client.disconnect()
    print("   ✓ Disconnected from server")

    print("\n✅ Sentence Transformers example completed!")
    print("\n💡 Tip: The embeddings capture semantic meaning,")
    print("   so queries like 'economic markets' can find documents")
    print("   about 'stock market' even without exact keyword matches.")


if __name__ == "__main__":
    main()
