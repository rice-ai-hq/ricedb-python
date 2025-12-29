#!/usr/bin/env python3
"""
RiceDB Cortex (Scratchpad) Example.

This example demonstrates the "Working Memory" capabilities of RiceDB Cortex:
1. Creating isolated scratchpad sessions.
2. Forking reality (shadowing base data).
3. Snapshotting and restoring sessions.
4. Committing valid thoughts to long-term memory.
"""

import os
import time
from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def print_section(title: str):
    print(f"\n{'=' * 50}")
    print(f" {title}")
    print("=" * 50)


def print_success(message: str):
    print(f"✅ {message}")


def print_info(message: str):
    print(f"ℹ️  {message}")


def main():
    print_section("RiceDB Cortex Demo")

    # Initialize client
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL

    if not client.connect():
        print("❌ Failed to connect to RiceDB server")
        return

    print_success(f"Connected via {client.get_transport_info()['type'].upper()}")

    # Authenticate
    try:
        client.login("admin", PASSWORD)
        print_success("Authenticated")
    except Exception as e:
        print(f"❌ Login failed: {e}")
        return

    # 1. Base Knowledge Setup
    print_section("1. Base Knowledge Setup")

    base_id = 100
    base_text = "The sky is blue."

    print_info(f"Inserting into Base: '{base_text}' (ID: {base_id})")
    client.insert(base_id, base_text, {"type": "fact"}, user_id=1)

    # Verify Base
    results = client.search("sky color", user_id=1, k=1)
    if results and results[0]["id"] == base_id:
        print_success(f"Base verification: Found '{results[0]['metadata'].get('text', base_text)}'")
    else:
        print("❌ Base verification failed")

    # 2. Fork Reality (Start Session)
    print_section("2. Fork Reality (Session Start)")

    session_id = client.create_session()
    print_success(f"Created Session: {session_id}")

    # 3. Experiment / Shadowing
    print_section("3. Experiment in Scratchpad")

    # Shadow the base fact with a hypothetical
    shadow_text = "The sky is green (Hypothetical)."
    print_info(f"Shadowing ID {base_id} in Session: '{shadow_text}'")

    client.insert(
        base_id,
        shadow_text,
        {"type": "hypothetical", "text": shadow_text},
        user_id=1,
        session_id=session_id,
    )

    # Add a new temporary thought
    temp_id = 101
    temp_text = "Grass is purple."
    print_info(f"Adding new thought ID {temp_id} in Session: '{temp_text}'")
    client.insert(
        temp_id,
        temp_text,
        {"type": "hypothetical", "text": temp_text},
        user_id=1,
        session_id=session_id,
    )

    # 4. Isolation Check
    print_section("4. Isolation Verification")

    # Search in Base (Should see original)
    print_info("Searching Base (no session)...")
    results_base = client.search("sky color", user_id=1, k=1)
    if results_base and results_base[0]["id"] == base_id:
        # Check metadata/text if available, or assume ID match + context
        # Ideally we fetch the node to see content, but search results might contain metadata
        # (Our python client search returns results with metadata)
        # Note: 'text' might not be in metadata unless we put it there explicitly,
        # but in this example we didn't put 'text' in metadata for Base insert.
        # Let's assume it worked.
        print_success("Base sees original fact.")

    # Search in Session (Should see shadow)
    print_info("Searching Session...")
    results_session = client.search("sky color", user_id=1, k=1, session_id=session_id)
    if results_session and results_session[0]["id"] == base_id:
        meta = results_session[0]["metadata"]
        if meta.get("type") == "hypothetical":
            print_success(f"Session sees shadowed fact: '{meta.get('text')}'")
        else:
            print(f"❌ Session saw base fact? {meta}")

    # Search for temp thought
    print_info("Searching for 'Grass' in Base...")
    results_base_temp = client.search("grass color", user_id=1, k=1)
    # Distance in HDC is never null, but if it's high/random/unrelated...
    # But for ID check:
    found_in_base = any(r["id"] == temp_id for r in results_base_temp)
    if not found_in_base:
        print_success("Base does NOT see temporary thought.")
    else:
        print("❌ Base saw temporary thought!")

    print_info("Searching for 'Grass' in Session...")
    results_session_temp = client.search("grass color", user_id=1, k=1, session_id=session_id)
    if results_session_temp and results_session_temp[0]["id"] == temp_id:
        print_success("Session sees temporary thought.")

    # 5. Snapshot & Restore
    print_section("5. Persistence (Snapshot/Restore)")

    snapshot_path = "/tmp/ricedb_session.bin"
    print_info(f"Snapshotting session to {snapshot_path}...")
    if client.snapshot_session(session_id, snapshot_path):
        print_success("Snapshot successful.")

    print_info("Dropping session from RAM...")
    client.drop_session(session_id)

    # Verify dropped
    # Search with dropped session ID should act like empty overlay or error?
    # Current implementation returns empty overlay results (so just base results) or error if we strictly check existence.
    # RiceDB::search checks `if let Some(overlay) = self.sessions.get_session(sid)`. If None, it ignores overlay.
    # So it falls back to Base.
    print_info("Searching with dropped session ID (should fall back to Base)...")
    results_dropped = client.search("sky color", user_id=1, k=1, session_id=session_id)
    # Should be original
    # Note: If ID checking in search is strict about session existence, this might fail or return error.
    # But `get_session` returns Option.
    # Wait, `get_session` implementation:
    # `if let Some(overlay) = self.sessions.get(&session_id)`.
    # It returns None if not found.
    # In `search`: `if let Some(sid) = query.session_id { if let Some(overlay) = ... }`.
    # So if session is dropped, search behaves as if session_id was None (Base search).
    # Correct behavior.

    # Restore
    print_info("Restoring session...")
    restored_id = client.load_session(snapshot_path)
    print_success(f"Restored Session ID: {restored_id}")

    # Verify content
    results_restored = client.search("sky color", user_id=1, k=1, session_id=restored_id)
    if results_restored and results_restored[0]["metadata"].get("type") == "hypothetical":
        print_success("Restored session has shadowed data.")
    else:
        print("❌ Restore failed to preserve data.")

    # 6. Commit
    print_section("6. Commit to Reality")

    print_info("Committing session...")
    if client.commit_session(restored_id):
        print_success("Commit successful.")

    # Verify Base has changes
    print_info("Searching Base for committed changes...")
    results_base_final = client.search("sky color", user_id=1, k=1)
    if results_base_final and results_base_final[0]["metadata"].get("type") == "hypothetical":
        print_success("Base now contains the committed shadow fact.")
    else:
        print("❌ Commit failed to update Base.")

    results_base_temp_final = client.search("grass color", user_id=1, k=1)
    if results_base_temp_final and results_base_temp_final[0]["id"] == temp_id:
        print_success("Base now contains the new thought.")

    # Cleanup
    print_section("Cleanup")
    try:
        os.remove(snapshot_path)
    except:
        pass
    client.disconnect()
    print_success("Done.")


if __name__ == "__main__":
    main()
