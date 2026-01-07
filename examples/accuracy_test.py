#!/usr/bin/env python3
"""
Accuracy Test for RiceDB (HDC).

Tests various retrieval scenarios to ensure Bag-of-Words HDC encoding works as expected.
"""

import os
from dotenv import load_dotenv
from ricedb import RiceDBClient
import time

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def print_result(name, passed, detail=""):
    icon = "" if passed else ""
    print(f"   {icon} {name}: {detail}")


def main():
    print(" RiceDB Accuracy Test\n")
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print(" Connection failed")
        return

    try:
        client.login("admin", PASSWORD)
    except Exception as e:
        print(f" Login failed: {e}")
        return

    # Clear memory/data? Ideally yes, but we might disrupt other tests.
    # We will use unique IDs to avoid conflict.
    base_id = 2000

    print("1  Ingesting Test Corpus...")
    corpus = [
        (base_id + 1, "The quick brown fox jumps over the lazy dog.", "fox"),
        (base_id + 2, "A fast brown wolf leaps over the sleepy canine.", "wolf"),
        (base_id + 3, "RiceDB uses Hyperdimensional Computing for fast retrieval.", "ricedb"),
        (base_id + 4, "Vector databases use float embeddings from LLMs.", "vector"),
        (base_id + 5, "Apples and oranges are fruits.", "fruit"),
    ]

    for node_id, text, tag in corpus:
        client.insert(node_id, text, {"tag": tag}, user_id=1)

    print("    Ingested 5 documents")

    print("\n2  Running Queries...")

    # Test 1: Exact keyword match
    results = client.search("brown fox", k=10, user_id=1)
    # Check if base_id + 1 is in results
    found_item = next((r for r in results if r["id"] == base_id + 1), None)
    match = found_item is not None

    detail = "Not found in top 10"
    if found_item:
        rank = results.index(found_item) + 1
        detail = f"Found at rank {rank}. Score: {found_item['similarity']}"
    elif results:
        top = results[0]
        detail = f"Top: {top['id']} (Score: {top['similarity']})"

    print_result("Keyword Match ('brown fox')", match, detail)

    # Test 2: Partial overlap (Bag of Words)
    # "quick dog" should match "The quick ... dog"
    results = client.search("quick dog", k=1, user_id=1)
    match = results and results[0]["id"] == base_id + 1
    top_meta = results[0]["metadata"] if results else {}
    print_result(
        "Partial Overlap ('quick dog')",
        match,
        f"Top: {top_meta.get('tag')} (ID: {results[0]['id'] if results else 'None'})",
    )

    # Test 3: Sentence subset
    results = client.search("Hyperdimensional Computing", k=1, user_id=1)
    match = results and results[0]["id"] == base_id + 3
    top_meta = results[0]["metadata"] if results else {}
    print_result(
        "Subset Match ('Hyperdimensional Computing')",
        match,
        f"Top: {top_meta.get('tag')} (ID: {results[0]['id'] if results else 'None'})",
    )

    # Test 4: Irrelevant query
    # "Space rockets" should not match any well, or match randomly.
    # Scores should be around 5000 (0.5).
    results = client.search("Space rockets to Mars", k=1, user_id=1)
    dist = results[0]["similarity"] if results else 0
    # In HDC 10k bits, random distance is ~5000.
    # If distance is close to 5000, it means no meaningful match.
    # If distance < 4500, it might be a match.
    is_random = dist > 4500
    print_result(
        "Irrelevant Query ('Space rockets...')",
        is_random,
        f"Distance: {dist:.1f} (Should be high ~5000)",
    )

    # Test 5: Distractor
    # "Apples" should match doc 5, not doc 1
    results = client.search("Apples", k=1, user_id=1)
    match = results and results[0]["id"] == base_id + 5
    top_meta = results[0]["metadata"] if results else {}
    print_result(
        "Distractor Test ('Apples')",
        match,
        f"Top: {top_meta.get('tag')} (ID: {results[0]['id'] if results else 'None'})",
    )

    client.disconnect()


if __name__ == "__main__":
    main()
