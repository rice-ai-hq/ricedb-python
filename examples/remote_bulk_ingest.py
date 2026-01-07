#!/usr/bin/env python3
"""
Remote Bulk Ingest Example for RiceDB (HDC).

This example demonstrates how to ingest data to a remote RiceDB instance
using the Python client with HTTP transport.

Target Instance: Remote (api.ricedb-test-2.ricedb.tryrice.com)
"""

import os
import time
import random
import uuid
from typing import List, Dict, Any
from dotenv import load_dotenv

from ricedb import RiceDBClient

load_dotenv()

# Configuration
HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"

BATCH_SIZE = 100
TOTAL_DOCS = 1000

# Data Generation Helpers (from bulk_ingest_example.py)
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
    print(" RiceDB Remote Bulk Ingest Example\n")

    # 1. Connect
    print(f"1  Connecting to {HOST}:{PORT}...")
    # Using transport="grpc"
    client = RiceDBClient(HOST, port=PORT, transport="grpc")
    client.ssl = SSL

    if not client.connect():
        print("    Failed to connect to RiceDB server")
        return
    print(f"    Connected via {client.get_transport_info()['type'].upper()}")

    # 2. Login
    print("    Logging in...")
    try:
        client.login("admin", PASSWORD)
        print("    Logged in successfully")
    except Exception as e:
        print(f"    Login failed: {e}")
        return

    # 3. Generate Data
    print("\n2  Generating Data...")
    raw_docs = generate_corpus(TOTAL_DOCS)
    print(f"    Generated {len(raw_docs)} documents")

    # 4. Bulk Ingest
    print(f"\n3  Starting Bulk Ingest (Batch Size: {BATCH_SIZE})...")
    start_time = time.time()
    total_inserted = 0

    # Process in batches
    for i in range(0, len(raw_docs), BATCH_SIZE):
        batch = raw_docs[i : i + BATCH_SIZE]

        # Create unique integer IDs for RiceDB
        batch_docs = []

        for j, doc in enumerate(batch):
            # Start ID high to avoid conflicts with existing data
            node_id = 2_000_000 + total_inserted + j

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
                    f"    Batch {i // BATCH_SIZE + 1}: Inserted {count} docs (Total: {total_inserted})"
                )

        except Exception as e:
            print(f"    Batch {i // BATCH_SIZE + 1} failed: {e}")
            # Add small delay on error
            time.sleep(1)

    duration = time.time() - start_time
    print(f"\n Ingest Complete!")
    print(f"   Total Documents: {total_inserted}")
    print(f"   Time Taken: {duration:.2f}s")
    if duration > 0:
        print(f"   Rate: {total_inserted / duration:.2f} docs/sec")

    # 5. Verify Search
    print("\n4  Verifying with Search...")
    query = "server outage"
    print(f"   Query: '{query}'")

    try:
        search_start = time.time()
        results = client.search(query, user_id=1, k=3)
        search_duration = time.time() - search_start
        print(f"   Search took {search_duration:.4f}s")

        for i, res in enumerate(results, 1):
            meta = res["metadata"]
            # text is stored as 'stored_text' in metadata
            text_preview = meta.get("stored_text", "")  # [:80]
            print(
                f"   {i}. [{meta.get('source', 'Unknown')}] {text_preview}... (Score: {res['similarity']:.4f})"
            )
    except Exception as e:
        print(f"    Search failed: {e}")

    client.disconnect()


if __name__ == "__main__":
    main()
