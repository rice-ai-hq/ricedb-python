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

    # Authenticate
    try:
        # Login
        client.login("admin", "admin")
        print_success("Authenticated as 'admin'")
    except Exception as e:
        print(f"❌ Authentication failed: {e}")
        return

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
        metadata={"status": "in-progress", "target": "src/auth/mod.rs"},
    )
    time.sleep(0.5)  # Simulate work

    client.memory.add(
        session_id=session_id,
        agent="ScannerAgent",
        content="Found potential hardcoded secret in login function.",
        metadata={"priority": "high", "line": "42"},
    )
    print_success("ScannerAgent logged findings.")

    # Agent 2: Reviewer (Reacts to Scanner)
    print_info("ReviewerAgent is filtering memory for 'high' priority findings...")

    # Retrieve only high priority entries using server-side filtering
    high_priority_findings = client.memory.get(session_id=session_id, filter={"priority": "high"})

    print(f"\n[High Priority Findings: {len(high_priority_findings)}]")
    for entry in high_priority_findings:
        print(f"  - [{entry['agent_id']}] {entry['content']}")

    # Reviewer takes action based on memory
    if high_priority_findings:
        last_entry = high_priority_findings[-1]
        print("\nReviewerAgent noticed the issue.")
        client.memory.add(
            session_id=session_id,
            agent="ReviewerAgent",
            content="I verified the finding. It is indeed a hardcoded string.",
            metadata={"verdict": "confirmed", "refers_to": last_entry["id"]},
            ttl=3600,  # Keep this verification for 1 hour only
        )
        print_success("ReviewerAgent added confirmation with 1h TTL.")

    # 3. Real-time Watch (gRPC only)
    print_section("3. Real-time Watch (Pub/Sub)")

    transport = client.get_transport_info()["type"]
    if transport == "grpc":
        print_info("Watching for next message (blocking)...")

        # In a real app, this would be in a separate thread/process
        # Here we simulate a producer in the background?
        # Since we are single-threaded here, we can't easily demo blocking watch
        # AND produce at the same time without threads.
        # Let's just describe it or skip blocking call in this simple script.
        print("   (Skipping blocking watch in single-threaded demo. See docs for usage.)")
        # To demo: client.memory.watch(session_id) yields events
    else:
        print("   (Watch API requires gRPC transport)")

    # 4. Graph Linking
    print_section("4. Graph Knowledge")
    try:
        # Create nodes representing files/concepts
        client.insert_text(101, "auth.ts authentication logic", {"type": "file"}, user_id=1)
        client.insert_text(102, "login.ts user login page", {"type": "file"}, user_id=1)

        # Link them
        print_info("Linking auth.ts -> IMPORTS -> login.ts")
        client.link(102, "IMPORTS", 101)
        print_success("Link created.")

        # Verify neighbors
        neighbors = client.get_neighbors(102, relation="IMPORTS")
        print(f"   Neighbors of login.ts (IMPORTS): {neighbors}")

    except Exception as e:
        print(f"   (Graph op failed: {e})")

    print_section("Summary")
    print("The Agent Memory feature allows fast, lightweight coordination between agents")
    print("without the overhead of vector embeddings or polluting the main search index.")

    client.disconnect()


if __name__ == "__main__":
    main()
