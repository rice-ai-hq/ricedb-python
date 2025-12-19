#!/usr/bin/env python3
"""
Agent Memory (Scratchpad) Example for RiceDB.

This example demonstrates how to use the native Agent Memory feature to:
1. Store temporary agent thoughts and plans without polluting the main vector index.
2. Retrieve agent history for a specific session.
3. Coordinate multiple agents using shared memory.
"""

import time
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


def main():
    print_section("RiceDB Agent Memory Demo")

    # Initialize client (auto-detects transport)
    # Ensure RiceDB server is running (e.g., make run-http or make run)
    client = RiceDBClient("localhost")

    if not client.connect():
        print("❌ Failed to connect to RiceDB server")
        return

    print_success(f"Connected via {client.get_transport_info()['type'].upper()}")

    # Scenario: Code Review Session
    session_id = "code-review-101"
    
    # 1. Clear previous session memory (for a fresh start)
    print_section("1. Initialization")
    print_info(f"Clearing memory for session: {session_id}")
    client.memory.clear(session_id)
    print_success("Memory cleared")

    # 2. Agents interacting via Shared Memory
    print_section("2. Multi-Agent Interaction")

    # Agent 1: Scanner
    print_info("ScannerAgent is analyzing the codebase...")
    client.memory.add(
        session_id=session_id,
        agent="ScannerAgent",
        content="Started static analysis on src/auth/mod.rs",
        metadata={"status": "in-progress", "target": "src/auth/mod.rs"}
    )
    time.sleep(0.5) # Simulate work

    client.memory.add(
        session_id=session_id,
        agent="ScannerAgent",
        content="Found potential hardcoded secret in login function.",
        metadata={"priority": "high", "line": "42"}
    )
    print_success("ScannerAgent logged findings.")

    # Agent 2: Reviewer (Reacts to Scanner)
    print_info("ReviewerAgent is checking memory for new findings...")
    
    # Retrieve last 5 entries
    history = client.memory.get(session_id=session_id, limit=5)
    
    print("\n[Current Memory State]")
    for entry in history:
        print(f"  - [{entry['agent_id']}] {entry['content']} (meta: {entry.get('metadata')})")

    # Reviewer takes action based on memory
    last_entry = history[-1]
    if last_entry['agent_id'] == "ScannerAgent" and "secret" in last_entry['content']:
        print("\nReviewerAgent noticed the secret issue.")
        client.memory.add(
            session_id=session_id,
            agent="ReviewerAgent",
            content="I verified the finding. It is indeed a hardcoded string.",
            metadata={"verdict": "confirmed", "refers_to": last_entry['id']}
        )
        print_success("ReviewerAgent added confirmation.")

    # 3. Filtering and Polling
    print_section("3. Advanced Retrieval")
    
    # Simulate a time gap
    timestamp_mark = int(time.time())
    time.sleep(1)

    # Agent 3: Fixer (Comes in later)
    client.memory.add(
        session_id=session_id,
        agent="FixerAgent",
        content="Applied patch to remove hardcoded secret.",
        metadata={"action": "patch", "commit": "a1b2c3d"}
    )
    print_success("FixerAgent applied patch.")

    # Retrieve only new messages (since timestamp_mark)
    print_info("Retrieving only new messages since the Reviewer checked...")
    new_entries = client.memory.get(session_id=session_id, after=timestamp_mark)
    
    for entry in new_entries:
        print(f"  - [NEW] [{entry['agent_id']}] {entry['content']}")

    print_section("Summary")
    print("The Agent Memory feature allows fast, lightweight coordination between agents")
    print("without the overhead of vector embeddings or polluting the main search index.")

    client.disconnect()

if __name__ == "__main__":
    main()
