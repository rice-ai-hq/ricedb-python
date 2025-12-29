#!/usr/bin/env python3
"""
Bulk Ingest Example for RiceDB (HDC).

This example demonstrates how to ingest a large corpus of organizational data
using efficient batch insertion with server-side HDC encoding.

Target Instance: Localhost or Remote
"""

import os
import time
import random
import uuid
from typing import List, Dict, Any

from ricedb import RiceDBClient

# Configuration
HOST = os.environ.get("RICEDB_HOST", "localhost")
PORT = int(os.environ.get("RICEDB_PORT", "50051"))
BATCH_SIZE = 100
TOTAL_DOCS = 1000

# Data Generation Helpers
SOURCES = ["Notion", "Gmail", "Slack", "CRM", "Jira"]
DEPARTMENTS = ["Engineering", "Sales", "HR", "Marketing", "Legal"]
TOPICS = [
    "Q4 Strategy",
    "Project Alpha Launch",
    "Customer Feedback",
    "Server Outage Incident",
    "Hiring Pipeline",
    "Budget Review",
    "Compliance Audit",
    "API Documentation",
]


def generate_corpus(count: int) -> List[Dict[str, Any]]:
    """Generate a synthetic corpus of organizational documents."""
    print(f"Generating {count} documents...")
    documents = []

    for i in range(count):
        source = random.choice(SOURCES)
        dept = random.choice(DEPARTMENTS)
        topic = random.choice(TOPICS)

        # Simulate content based on source
        if source == "Slack":
            content = f"Hey @channel, update on {topic}. We need to sync with {dept} ASAP. #urgent"
        elif source == "Jira":
            content = f"Bug report: {topic} failing in production. Assigned to {dept} team. Priority: High"
        elif source == "Notion":
            content = f"Meeting Notes: {topic}. Attendees from {dept}. Action items included."
        elif source == "Gmail":
            content = f"Subject: Re: {topic}\n\nHi Team,\n\nPlease review the attached document regarding {topic}.\n\nBest,\n{dept} Lead"
        else:  # CRM
            content = f"Customer interaction log regarding {topic}. Sentiment: Positive. Handover to {dept}."

        doc = {
            "text": content,
            "stored_text": content,  # Keep a copy in metadata
            "source": source,
            "department": dept,
            "topic": topic,
            "timestamp": int(time.time()),
            "doc_id": str(uuid.uuid4()),
        }
        documents.append(doc)

    return documents


def main():
    print("🍚 RiceDB Bulk Ingest Example (HDC)\n")

    # 1. Connect
    print(f"1️⃣  Connecting to {HOST}:{PORT}...")
    # Defaulting to gRPC for bulk ingest as it is usually faster/streaming
    client = RiceDBClient(HOST, port=PORT)

    if not client.connect():
        print("   ❌ Failed to connect to RiceDB server")
        return
    print(f"   ✓ Connected via {client.get_transport_info()['type'].upper()}")

    # 2. Login
    print("   🔑 Logging in...")
    try:
        client.login("admin", "admin")
        print("   ✓ Logged in successfully")
    except Exception as e:
        print(f"   ❌ Login failed: {e}")
        return

    # 3. Generate Data
    print("\n2️⃣  Generating Data...")
    raw_docs = generate_corpus(TOTAL_DOCS)
    print(f"   ✓ Generated {len(raw_docs)} documents")

    # 4. Bulk Ingest
    print(f"\n3️⃣  Starting Bulk Ingest (Batch Size: {BATCH_SIZE})...")
    start_time = time.time()
    total_inserted = 0

    # Process in batches
    for i in range(0, len(raw_docs), BATCH_SIZE):
        batch = raw_docs[i : i + BATCH_SIZE]

        # Create unique integer IDs for RiceDB
        batch_docs = []

        for j, doc in enumerate(batch):
            node_id = 1_000_000 + total_inserted + j

            # Restructure for batch_insert
            item = {
                "id": node_id,
                "text": doc["text"],
                "metadata": {k: v for k, v in doc.items() if k != "text"},
                "user_id": 1,
            }
            batch_docs.append(item)

        try:
            result = client.batch_insert(batch_docs)

            count = result.get("count", 0)
            total_inserted += count
            if (i // BATCH_SIZE) % 1 == 0:
                print(
                    f"   ✓ Batch {i // BATCH_SIZE + 1}: Inserted {count} docs (Total: {total_inserted})"
                )

        except Exception as e:
            print(f"   ❌ Batch {i // BATCH_SIZE + 1} failed: {e}")

    duration = time.time() - start_time
    print(f"\n✅ Ingest Complete!")
    print(f"   Total Documents: {total_inserted}")
    print(f"   Time Taken: {duration:.2f}s")
    print(f"   Rate: {total_inserted / duration:.2f} docs/sec")

    # 5. Verify Search
    print("\n4️⃣  Verifying with Search...")
    query = "server outage"
    print(f"   Query: '{query}'")

    results = client.search(query, user_id=1, k=3)

    for i, res in enumerate(results, 1):
        meta = res["metadata"]
        # text is stored as 'stored_text' in metadata
        text_preview = meta.get("stored_text", "")  # [:80]
        print(
            f"   {i}. [{meta.get('source', 'Unknown')}] {text_preview}... (Score: {res['similarity']:.4f})"
        )

    client.disconnect()


if __name__ == "__main__":
    main()
