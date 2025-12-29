#!/usr/bin/env python3
"""
Extensive Multi-Agent Workflow Example using RiceDB Cortex (Scratchpads).

Scenario: Collaborative Software Evolution
------------------------------------------
We simulate a team of AI agents working on a codebase stored in RiceDB.

1.  **Base State**: The "Legacy Codebase" stored in persistent memory.
2.  **Agent A (Architect)**: Forks reality to design a major refactor (Session A).
    -   Replaces `AuthModule` with `OAuthService` (Shadowing).
    -   Deletes `LegacyLogin` (Tombstoning).
3.  **Agent B (Feature Dev)**: Forks reality to add a minor feature (Session B).
    -   Modifies `UserProfile` to add fields.
    -   Should NOT see Agent A's changes (Isolation).
4.  **Agent C (Reviewer)**: Inspects Agent A's proposal.
    -   Connects to Session A to validate the architecture.
5.  **Resolution**:
    -   Agent A's refactor is approved and COMMITTED.
    -   Agent B's feature is discarded (DROPPED).
6.  **Final Verification**:
    -   Base storage now reflects the Refactor.
"""

import os
import time
import json
from typing import Dict, Any, Optional
from dotenv import load_dotenv
from ricedb import RiceDBClient

load_dotenv()

HOST = os.environ.get("HOST", "localhost")
PORT = int(os.environ.get("PORT", "50051"))
PASSWORD = os.environ.get("PASSWORD", "admin")
SSL = os.environ.get("SSL", "false").lower() == "true"


def print_header(title: str):
    print(f"\n{'-' * 80}")
    print(f"🔹 {title}")
    print(f"{'-' * 80}")


def print_step(emoji: str, title: str):
    print(f"\n{emoji}  {title}")


def print_success(message: str):
    print(f"✅ {message}")


def print_info(message: str):
    print(f"ℹ️  {message}")


def print_node(node: Dict[str, Any], label: str = "Node"):
    meta = node.get("metadata", {})
    print(f"   📄 [{label}] ID: {node['id']}")
    print(f"       Name: {meta.get('name', 'Unknown')}")
    print(f"       Content: {meta.get('content', '')[:60]}...")
    print(f"       Tags: {meta.get('tags', [])}")


def main():
    print_header("RiceDB Cortex: Multi-Agent Workflow Simulation")

    # 1. Setup & Connection
    client = RiceDBClient(HOST, port=PORT)
    client.ssl = SSL
    if not client.connect():
        print("❌ Failed to connect to RiceDB server")
        return
    client.login("admin", PASSWORD)

    # 2. Initialize Base Reality (The "Main Branch")
    print_header("1. Initializing 'Main Branch' (Base Storage)")

    # Define initial codebase nodes
    codebase = [
        {
            "id": 500,
            "text": "Main Application Entry Point. Initializes AuthModule and UserProfile.",
            "metadata": {
                "name": "MainApp",
                "type": "code",
                "content": "fn main() { init_auth(); }",
                "tags": ["core"],
            },
        },
        {
            "id": 501,
            "text": "Legacy Authentication Module. Uses simple password hashing.",
            "metadata": {
                "name": "AuthModule",
                "type": "code",
                "content": "class Auth { login(u,p) }",
                "tags": ["security", "legacy"],
            },
        },
        {
            "id": 502,
            "text": "User Profile Module. Stores username and email.",
            "metadata": {
                "name": "UserProfile",
                "type": "code",
                "content": "struct User { name, email }",
                "tags": ["data"],
            },
        },
    ]

    print_step("🌱", "Ingesting Base Codebase...")
    for doc in codebase:
        client.insert(doc["id"], doc["text"], doc["metadata"], user_id=1)
        print(f"   ✓ Created {doc['metadata']['name']} (ID: {doc['id']})")

    # 3. Agent A: The Architect (Session A)
    print_header("2. Agent A (Architect) Starts Work")
    print_step("🧠", "Architect creates a Scratchpad Session...")
    session_a = client.create_session()
    print(f"   ✓ Session A ID: {session_a}")

    print_step("🛠️", "Architect performs refactoring in Session A...")

    # 3.1 Shadowing: Modify MainApp to use new system
    print("   -> Modifying 'MainApp' to use OAuth (Shadowing ID 500)...")
    client.insert(
        500,
        "Main Application Entry Point. Initializes OAuthService.",
        {
            "name": "MainApp",
            "type": "code",
            "content": "fn main() { init_oauth(); }",
            "tags": ["core", "refactored"],
        },
        user_id=1,
        session_id=session_a,
    )

    # 3.2 Tombstoning: Delete Legacy Auth
    print("   -> Deleting 'AuthModule' (Tombstoning ID 501)...")
    # Using the newly implemented delete with session_id support
    client.delete(501, session_id=session_a)
    print("   ✓ Marked 'AuthModule' as deleted in Session A")

    # 3.3 New Node: Add OAuthService
    print("   -> Adding 'OAuthService' (New Node ID 600)...")
    client.insert(
        600,
        "Modern OAuth2 Authentication Service.",
        {
            "name": "OAuthService",
            "type": "code",
            "content": "class OAuth { ... }",
            "tags": ["security", "modern"],
        },
        user_id=1,
        session_id=session_a,
    )

    # 4. Agent B: The Feature Dev (Session B)
    print_header("3. Agent B (Feature Dev) Starts Work (Parallel Universe)")
    print_step("🧠", "Feature Dev creates a separate Scratchpad Session...")
    session_b = client.create_session()
    print(f"   ✓ Session B ID: {session_b}")

    print_step("🔨", "Feature Dev modifies UserProfile...")
    # Modifies ID 502
    client.insert(
        502,
        "User Profile with Avatar support.",
        {
            "name": "UserProfile",
            "type": "code",
            "content": "struct User { name, email, avatar }",
            "tags": ["data", "enhanced"],
        },
        user_id=1,
        session_id=session_b,
    )

    # 5. Verify Isolation
    print_header("4. Verifying Reality Isolation")

    # Check Base
    print_step("🔍", "Searching BASE (Global State)...")
    res = client.search("authentication", user_id=1, k=5)  # No session_id
    print(f"   Found {len(res)} results.")
    # Should see Legacy Auth (501) as original
    found_legacy = any(r["id"] == 501 and "legacy" in r["metadata"]["tags"] for r in res)
    found_oauth = any(r["id"] == 600 for r in res)
    if found_legacy and not found_oauth:
        print_success("Base sees Legacy Code. No OAuth.")
    else:
        print(f"   ❌ Base state incorrect! (Legacy: {found_legacy}, OAuth: {found_oauth})")

    # Check Session A (Architect)
    print_step("🔍", "Searching SESSION A (Architect)...")
    res_a = client.search("authentication", user_id=1, k=5, session_id=session_a)
    found_deprecated = any(r["id"] == 501 and "deprecated" in r["metadata"]["tags"] for r in res_a)
    found_oauth_a = any(r["id"] == 600 for r in res_a)

    if found_deprecated:
        print_success("Architect sees AuthModule as DEPRECATED (Shadowed).")
    if found_oauth_a:
        print_success("Architect sees new OAuthService.")

    # Check if Architect sees Feature Dev's changes?
    res_a_profile = client.search("avatar", user_id=1, k=1, session_id=session_a)
    # "avatar" is in ID 502 of Session B only.
    # In Base, 502 is just "username and email". "avatar" keyword shouldn't match well or at least not the updated text.
    # We check if metadata contains "enhanced" tag which we added in Session B.
    if res_a_profile and "enhanced" in res_a_profile[0]["metadata"].get("tags", []):
        print("   ❌ Architect saw Feature Dev's changes! (Leak)")
    else:
        print_success("Architect is ISOLATED from Feature Dev.")

    # Check Session B (Feature Dev)
    print_step("🔍", "Searching SESSION B (Feature Dev)...")
    res_b = client.search("authentication", user_id=1, k=5, session_id=session_b)
    # Should see Legacy Auth (501) as original (inherited from Base), NOT deprecated
    found_original_auth = any(r["id"] == 501 and "legacy" in r["metadata"]["tags"] for r in res_b)
    if found_original_auth:
        print_success("Feature Dev sees original Legacy Auth (Isolated from Architect).")

    # 6. Agent C: The Reviewer
    print_header("5. Agent C (Reviewer) Validates Architect's Plan")
    print_step("👀", "Reviewer joins Architect's Reality...")

    # Reviewer simply uses session_a ID
    print(f"   Reviewing Session {session_a}...")

    # Fetch MainApp from Session A
    res_review = client.search("Main Application", k=1, user_id=1, session_id=session_a)
    if res_review:
        node = res_review[0]
        content = node["metadata"].get("content", "")
        print(f"   Reviewer sees MainApp content: '{content}'")
        if "init_oauth" in content:
            print_success("Reviewer confirms MainApp uses OAuth.")
            print_step("✅", "Reviewer APPROVES the refactor.")
            approved = True
        else:
            print("   ❌ MainApp content mismatch.")
            approved = False

    # 7. Commit
    if approved:
        print_header("6. Committing Architect's Plan")
        print_step("💾", "Committing Session A to Base...")
        if client.commit_session(session_a):
            print_success("Session A Committed.")
        else:
            print("   ❌ Commit failed.")

        # Verify Base again
        print_step("🌍", "Global State Updated:")
        res_base_new = client.search("authentication", user_id=1, k=5)
        found_oauth_base = any(r["id"] == 600 for r in res_base_new)
        if found_oauth_base:
            print_success("Base now contains OAuthService.")
        else:
            print("   ❌ Base update missing.")

    # 8. Feature Dev Conflict?
    print_header("7. Feature Dev's Fate")
    print("   Feature Dev continues working in Session B...")
    # Feature Dev had a shadow on ID 102. Base ID 102 was NOT touched by Architect.
    # So Feature Dev is safe.
    # But what if Feature Dev checks MainApp?
    # In Session B, MainApp (100) was NOT shadowed. So it falls through to Base.
    # Since Base updated ID 100 (Architect commit), Feature Dev NOW SEES the updated MainApp!
    # This is "Live Rebase" behavior.

    res_b_main = client.search("Main Application", k=1, user_id=1, session_id=session_b)
    if res_b_main:
        content = res_b_main[0]["metadata"].get("content", "")
        print(f"   Feature Dev now sees MainApp content: '{content}'")
        if "init_oauth" in content:
            print_success(
                "Feature Dev automatically sees Base updates for non-shadowed nodes (Live Update)."
            )
        else:
            print("   ⚠️  Feature Dev sees old Base? (Stale Read or Logic differs)")

    print_step("🗑️", "Dropping Session B (Feature cancelled)")
    client.drop_session(session_b)
    print_success("Session B Dropped.")

    client.disconnect()
    print("\n✅ Workflow Simulation Complete.")


if __name__ == "__main__":
    main()
