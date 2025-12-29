#!/usr/bin/env python3
"""
Test RiceDB with LongMemEval dataset (HDC).

This script reads the LongMemEval dataset, ingests it into RiceDB using HDC,
and performs searches to verify retrieval accuracy.
Each test case uses a unique user_id to isolate context (ACL).
"""

import os
import ijson
import time
from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def main():
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print("❌ Failed to connect")
        return

    try:
        client.login("admin", PASSWORD)
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    print("🍚 RiceDB LongMemEval Test\n")

    # Process first 5 items for demonstration
    limit = 5
    count = 0

    try:
        with open("datasets/longmemeval_s_cleaned.json", "rb") as f:
            items = ijson.items(f, "item")

            for item in items:
                if count >= limit:
                    break
                count += 1

                question = item["question"]
                answer = item["answer"]
                q_id = item["question_id"]

                # Use unique user_id per test case to isolate context (ACL feature)
                user_id = 10000 + count

                print(f"\n🧪 Test Case {count} (ID: {q_id})")
                print(f"   Question: {question}")
                print(f"   Expected Answer: {answer}")

                # Collect haystack docs
                docs = []
                doc_id_counter = 0
                expected_doc_ids = []

                if "haystack_sessions" in item:
                    for session in item["haystack_sessions"]:
                        for msg in session:
                            content = msg.get("content", "")
                            if content:
                                doc_id_counter += 1

                                # Check if this doc contains the answer
                                if answer.lower() in content.lower():
                                    expected_doc_ids.append(doc_id_counter)

                                # Flat structure for batch_insert_texts
                                docs.append(
                                    {
                                        "id": doc_id_counter,
                                        "text": content,
                                        "stored_text": content,  # Store copy for display
                                        "role": msg.get("role", "unknown"),
                                        "session_idx": item["haystack_sessions"].index(session),
                                    }
                                )

                print(f"   🎯 Expected Answer Doc IDs: {expected_doc_ids}")
                print(f"   📥 Ingesting {len(docs)} documents for user {user_id}...")
                start_t = time.time()

                # Batch insert in chunks
                chunk_size = 100
                total_ingested = 0
                for i in range(0, len(docs), chunk_size):
                    chunk = docs[i : i + chunk_size]

                    # Reshape for batch_insert
                    batch_docs = []
                    for doc in chunk:
                        batch_docs.append(
                            {
                                "id": doc["id"],
                                "text": doc["text"],
                                "metadata": {
                                    k: v for k, v in doc.items() if k not in ["id", "text"]
                                },
                                "user_id": user_id,
                            }
                        )

                    try:
                        client.batch_insert(batch_docs)
                        total_ingested += len(chunk)
                    except Exception as e:
                        print(f"   ❌ Batch failed: {e}")

                ingest_time = time.time() - start_t
                rate = total_ingested / ingest_time if ingest_time > 0 else 0
                print(
                    f"   ✓ Ingested {total_ingested} docs in {ingest_time:.2f}s ({rate:.1f} docs/sec)"
                )

                # Search
                print("   🔍 Searching...")
                start_t = time.time()
                results = client.search(question, k=3, user_id=user_id)
                search_time = time.time() - start_t

                print(f"   ✓ Found {len(results)} results in {search_time:.4f}s")

                for i, res in enumerate(results):
                    meta = res["metadata"]
                    text = meta.get("stored_text", "")
                    role = meta.get("role", "?")
                    snippet = text[:100].replace("\n", " ")
                    score = res["similarity"]
                    node_id = res["id"]

                    is_expected = node_id in expected_doc_ids
                    marker = "✅" if is_expected else "  "

                    print(
                        f"     {i + 1}. {marker} [{role}] ID: {node_id} - {snippet}... (Score: {score:.4f})"
                    )

                    # Heuristic check: does it contain answer?
                    if answer.lower() in text.lower():
                        print(f"        ✨ Text contains answer string!")

    except FileNotFoundError:
        print("❌ Dataset file 'datasets/longmemeval_s_cleaned.json' not found.")
    except Exception as e:
        print(f"❌ Error: {e}")

    client.disconnect()


if __name__ == "__main__":
    main()
