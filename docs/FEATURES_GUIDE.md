# RiceDB Python SDK - Complete Features Guide

> Comprehensive documentation of all features provided by the RiceDB Python SDK for building multi-agent AI applications.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Installation](#installation)
3. [Quick Start](#quick-start)
4. [Transport Layer](#transport-layer)
5. [Semantic Search](#semantic-search)
6. [Agent Memory (Scratchpad)](#agent-memory-scratchpad)
7. [Graph Database](#graph-database)
8. [Access Control Lists (ACL)](#access-control-lists-acl)
9. [Sparse Distributed Memory (SDM)](#sparse-distributed-memory-sdm)
10. [Real-time Pub/Sub](#real-time-pubsub)
11. [Batch Operations](#batch-operations)
12. [Authentication & User Management](#authentication--user-management)
13. [Error Handling](#error-handling)
14. [Best Practices](#best-practices)
15. [API Reference](#api-reference)

---

## Introduction

RiceDB is a high-performance, ACID-compliant database specifically designed for **Multi-Agent AI Systems**. It combines vector search, graph traversal, and agent memory in a unified engine, eliminating the need to coordinate between multiple databases.

### Why RiceDB?

| Challenge                         | RiceDB Solution                                        |
| --------------------------------- | ------------------------------------------------------ |
| Agents need semantic search       | HNSW-based vector index with SIMD optimizations        |
| Multiple agents need coordination | Native Agent Memory (scratchpad) for real-time sharing |
| Knowledge has relationships       | Integrated Graph Database for semantic linking         |
| Multi-tenant environments         | Bitmap-based ACL for zero-latency permission checks    |
| High-frequency updates            | LSM-tree storage with Write-Ahead Log (WAL)            |
| Real-time notifications           | Pub/Sub with semantic subscriptions                    |

### Core Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     RiceDB Python SDK                        │
├──────────────────┬──────────────────┬───────────────────────┤
│   HTTP Client    │   gRPC Client    │   Unified Client      │
│   (Port 3000)    │   (Port 50051)   │   (Auto-select)       │
├──────────────────┴──────────────────┴───────────────────────┤
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ Semantic    │ │ Graph       │ │ Agent       │            │
│  │ Search      │ │ Database    │ │ Memory      │            │
│  │ (HNSW)      │ │ (DashMap)   │ │ (Scratchpad)│            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐            │
│  │ ACL         │ │ SDM         │ │ Pub/Sub     │            │
│  │ (Bitmaps)   │ │ (1024-bit)  │ │ (Streaming) │            │
│  └─────────────┘ └─────────────┘ └─────────────┘            │
│                                                              │
│  ┌──────────────────────────────────────────────┐           │
│  │         LSM-Tree Storage Engine              │           │
│  │   WAL → MemTable → SSTable (Memory-mapped)   │           │
│  └──────────────────────────────────────────────┘           │
└─────────────────────────────────────────────────────────────┘
```

---

## Installation

### Basic Installation

```bash
# Basic installation (HTTP transport only)
pip install ricedb
```

### With Optional Dependencies

```bash
# With gRPC support (recommended for production)
pip install ricedb[grpc]

# All features
pip install ricedb[all]
```

### From Source

```bash
cd ricedb-python
pip install -e ".[all]"
```

---

## Quick Start

```python
from ricedb import RiceDBClient

# 1. Connect to RiceDB server
client = RiceDBClient("localhost")
client.connect()

# 2. Authenticate
client.login("admin", "admin")

# 3. Insert a document (Server handles embedding)
client.insert(
    node_id=1,
    text="Machine learning fundamentals",
    metadata={"title": "ML Basics", "category": "AI"},
    user_id=100
)

# 4. Search for similar documents
results = client.search(
    query="deep learning concepts",
    user_id=100,
    k=5
)

for result in results:
    print(f"ID: {result['id']}, Similarity: {result['similarity']:.4f}")
    print(f"Metadata: {result['metadata']}")

# 5. Disconnect
client.disconnect()
```

---

## Transport Layer

RiceDB Python SDK supports two transport mechanisms, each with its own strengths:

### HTTP Transport (Port 3000)

**Best for:**

- Simple deployments
- Debugging and development
- Broad compatibility
- Full ACL management support

```python
from ricedb import RiceDBClient

client = RiceDBClient(
    host="localhost",
    transport="http",
    port=3000,
    timeout=30  # Request timeout in seconds
)
```

### gRPC Transport (Port 50051)

**Best for:**

- High-performance production deployments
- Streaming operations
- Real-time subscriptions
- Batch operations

```python
from ricedb import RiceDBClient

client = RiceDBClient(
    host="localhost",
    transport="grpc",
    port=50051,
    max_message_length=50 * 1024 * 1024,  # 50MB
    keepalive_time_ms=30000,
    keepalive_timeout_ms=10000
)
```

### Auto-Detection (Recommended)

The unified client (`RiceDBClient`) automatically detects the best transport:

```python
client = RiceDBClient("localhost")  # Tries gRPC first, falls back to HTTP
```

### Checking Transport Info

```python
client.connect()
info = client.get_transport_info()
print(f"Transport: {info['type']}")       # "grpc" or "http"
print(f"Port: {info['port']}")
print(f"Features: {info['features']}")
print(f"ACL Support: {info['acl_support']}")
```

---

## Semantic Search

RiceDB uses **HDC (Hyperdimensional Computing)** based semantic encoding performed on the server. The client simply sends text, and the server generates the corresponding hypervector for indexing and search.

### Inserting Documents

```python
# Single insert
result = client.insert(
    node_id=1,
    text="Quarterly financial report for Q4 2024",
    metadata={"title": "Document 1", "type": "report"},
    user_id=100
)
```

### Searching

```python
# Semantic search
results = client.search(
    query="financial data analysis",
    user_id=100,
    k=10  # Top 10 results
)

# Results structure
for result in results:
    print(f"Node ID: {result['id']}")
    print(f"Similarity: {result['similarity']}")  # Hamming distance based score
    print(f"Metadata: {result['metadata']}")
```

### Streaming Search (gRPC only)

Get results as they're found for faster time-to-first-result:

```python
if client.get_transport_info()["type"] == "grpc":
    for result in client.stream_search("financial data", user_id=100, k=10):
        print(f"Found: {result['id']} (similarity: {result['similarity']:.4f})")
        # Process immediately without waiting for all results
```

---

## Agent Memory (Scratchpad)

Agent Memory is a **lightweight, high-performance scratchpad** for multi-agent coordination. Unlike vector storage, it's optimized for:

- **Fast writes**: No embedding computation
- **Time-ordered retrieval**: Chat-like message history
- **Session isolation**: Separate memory spaces per task
- **TTL support**: Auto-expiring entries
- **Metadata filtering**: Query by tags/status

### Adding Memory

```python
# Basic usage
client.memory.add(
    session_id="code-review-task-123",
    agent="ReviewerAgent",
    content="Found potential SQL injection in auth.py line 42",
    metadata={"severity": "high", "file": "auth.py"}
)

# With TTL (auto-expire after 1 hour)
client.memory.add(
    session_id="code-review-task-123",
    agent="ScannerAgent",
    content="Temporary analysis result",
    ttl=3600  # seconds
)
```

### Retrieving Memory

```python
# Get all entries for a session
history = client.memory.get(session_id="code-review-task-123")

# Limit results
history = client.memory.get(session_id="code-review-task-123", limit=10)

# Get entries after a timestamp (for polling)
import time
last_check = int(time.time()) - 60  # 1 minute ago
new_entries = client.memory.get(
    session_id="code-review-task-123",
    after=last_check
)

# Filter by metadata
critical_findings = client.memory.get(
    session_id="code-review-task-123",
    filter={"severity": "high"}
)
```

### Entry Structure

```python
{
    "id": "uuid-string",
    "session_id": "code-review-task-123",
    "agent_id": "ReviewerAgent",
    "content": "Found potential SQL injection...",
    "timestamp": 1703433600,  # Unix timestamp
    "metadata": {"severity": "high", "file": "auth.py"},
    "expires_at": 1703437200  # Optional, if TTL was set
}
```

### Watching for Updates (gRPC only)

Real-time updates using server-side streaming:

```python
if client.get_transport_info()["type"] == "grpc":
    # This blocks and yields new entries as they arrive
    for event in client.memory.watch("code-review-task-123"):
        print(f"[{event['entry']['agent_id']}] {event['entry']['content']}")
```

### Clearing Memory

```python
client.memory.clear("code-review-task-123")
```

---

## Graph Database

RiceDB includes an integrated graph database for representing relationships between entities. This enables **Graph-RAG** patterns combining semantic similarity with graph traversal.

### Adding Edges

```python
# Link two nodes with a relation
client.add_edge(
    from_node=101,  # Document about Python
    to_node=102,    # Document about Machine Learning
    relation="RELATED_TO",
    weight=0.9
)

# Using the convenience method
client.link(
    source_id=102,
    relation="MENTIONS",
    target_id=103,
    weight=0.8
)
```

### Querying Neighbors

```python
# Get all neighbors
neighbors = client.get_neighbors(node_id=101)
print(f"Connected nodes: {neighbors}")

# Filter by relation type
related = client.get_neighbors(node_id=101, relation="RELATED_TO")
```

### Graph Traversal

```python
# BFS traversal from a starting node
visited = client.traverse(
    start_node=101,
    max_depth=2  # Up to 2 hops away
)
print(f"Reachable nodes: {visited}")
```

### Graph Sampling (HTTP only)

Get a random sample of the graph for visualization:

```python
sample = client.sample_graph(limit=100)
print(f"Nodes: {sample['nodes']}")
print(f"Edges: {sample['edges']}")
```

---

## Access Control Lists (ACL)

RiceDB uses **Roaring Bitmaps** for high-performance ACL checks. Permissions are checked during search with zero additional latency.

### Permission Types

- **read**: Can retrieve the document in search results
- **write**: Can update the document metadata
- **delete**: Can delete the document

### User-Specific Data Isolation

Documents are automatically filtered based on user_id during search:

```python
# Insert as User 100
client.insert(
    node_id=1,
    text="Confidential HR document",
    metadata={"type": "hr"},
    user_id=100
)

# Search as User 100 - finds the document
results = client.search("HR document", user_id=100, k=10)
print(len(results))  # 1

# Search as User 200 - document is hidden
results = client.search("HR document", user_id=200, k=10)
print(len(results))  # 0
```

### Granting Permissions

```python
# Grant read access to another user
client.grant_permission(
    node_id=1,
    user_id=200,  # Target user
    permissions={"read": True, "write": False, "delete": False}
)

# Now User 200 can also find the document
results = client.search("HR document", user_id=200, k=10)  # Returns document
```

### Revoking Permissions

```python
# Remove all permissions for a user on a node
client.revoke_permission(node_id=1, user_id=200)
```

### Checking Permissions

```python
can_read = client.check_permission(
    node_id=1,
    user_id=200,
    permission_type="read"
)
print(f"User 200 can read node 1: {can_read}")
```

### Batch Permission Management

```python
# Grant permissions to multiple users/nodes at once
grants = [
    (1, 200, {"read": True, "write": False, "delete": False}),
    (1, 201, {"read": True, "write": True, "delete": False}),
    (2, 200, {"read": True, "write": False, "delete": False}),
]
result = client.batch_grant(grants)
print(f"Successful: {result['successful']}, Failed: {result['failed']}")
```

### Insert with Multi-User ACL

```python
# Insert a document accessible by multiple users
result = client.insert_with_acl(
    node_id=10,
    text="Shared team document",
    metadata={"team": "engineering"},
    user_permissions=[
        (100, {"read": True, "write": True, "delete": True}),   # Owner
        (101, {"read": True, "write": True, "delete": False}),  # Editor
        (102, {"read": True, "write": False, "delete": False}), # Viewer
    ]
)
```

---

## Sparse Distributed Memory (SDM)

RiceDB implements **Sparse Distributed Memory** for associative, content-addressable storage.

### BitVector Class

```python
from ricedb.utils import BitVector

# Create a zero vector
bv = BitVector()

# Create a random vector
random_bv = BitVector.random()

# Calculate Hamming distance
distance = bv.hamming_distance(random_bv)
print(f"Hamming distance: {distance} bits")
```

### Writing to SDM

```python
# Create address and data vectors
address = BitVector.random()
data = BitVector.random()

# Write to SDM
result = client.write_memory(
    address=address,
    data=data,
    user_id=100
)
print(f"Write result: {result}")
```

### Reading from SDM

```python
# Read from a similar address (tolerates noise)
noisy_address = address  # In practice, this might be slightly different
retrieved_data = client.read_memory(
    address=noisy_address,
    user_id=100
)

# Compare with original
distance = data.hamming_distance(retrieved_data)
print(f"Retrieval error: {distance} bits")
```

---

## Real-time Pub/Sub

RiceDB includes a Pub/Sub system for real-time event notifications.

### Subscribing to Events (gRPC only)

```python
if client.get_transport_info()["type"] == "grpc":
    # Subscribe to all events
    for event in client.subscribe(filter_type="all"):
        print(f"Event: {event['type']}, Node: {event['node_id']}")

    # Subscribe to specific node
    for event in client.subscribe(filter_type="node", node_id=123):
        if event['type'] == "updated":
            print(f"Node 123 was updated!")
```

---

## Batch Operations

For high-throughput scenarios, use batch operations to reduce round-trips.

### Batch Insert

```python
# Prepare documents
documents = [
    {
        "id": 1,
        "text": "Document 1 content",
        "metadata": {"title": "Doc 1"},
    },
    {
        "id": 2,
        "text": "Document 2 content",
        "metadata": {"title": "Doc 2"},
    },
    # ... many more
]

# Batch insert
result = client.batch_insert(documents, user_id=100)
print(f"Inserted {result['count']} documents")
print(f"Node IDs: {result['node_ids']}")
```

### Streaming Batch Insert (gRPC)

gRPC uses streaming for batch insert, allowing progress tracking:

```python
# With gRPC, batch_insert uses bidirectional streaming
# Documents are sent as they're prepared
def generate_documents():
    for i in range(10000):
        yield {
            "id": i,
            "text": f"Document {i}",
            "metadata": {"index": i},
        }

# The gRPC client streams documents efficiently
result = client.batch_insert(list(generate_documents()), user_id=100)
```

---

## Authentication & User Management

### Login

```python
# Login with username/password
token = client.login("admin", "admin_password")
print(f"Logged in with token: {token[:20]}...")

# Token is automatically attached to subsequent requests
```

### Creating Users (Admin only)

```python
# Login as admin first
client.login("admin", "admin_password")

# Create a new user
user_id = client.create_user(
    username="alice",
    password="secure_password",
    role="user"  # or "admin"
)
print(f"Created user with ID: {user_id}")
```

### Deleting Users (Admin only)

```python
success = client.delete_user("alice")
print(f"User deleted: {success}")
```

---

## Error Handling

The SDK provides typed exceptions for different error scenarios:

```python
from ricedb import RiceDBClient
from ricedb.exceptions import (
    RiceDBError,        # Base exception
    ConnectionError,    # Connection failures
    InsertError,        # Insert operation failures
    SearchError,        # Search operation failures
    AuthenticationError,# Auth/permission failures
    ValidationError,    # Input validation failures
    TransportError,     # Transport-specific errors
)

try:
    client.connect()
except ConnectionError as e:
    print(f"Failed to connect: {e}")
    # Retry or fallback logic

try:
    client.insert(1, "text", metadata, user_id=100)
except InsertError as e:
    print(f"Insert failed: {e}")
    # Handle duplicate ID, etc.
```

---

## API Reference

### RiceDBClient

#### Connection

| Method                         | Description            |
| ------------------------------ | ---------------------- |
| `connect() -> bool`            | Connect to server      |
| `disconnect()`                 | Disconnect from server |
| `health() -> Dict`             | Check server health    |
| `get_transport_info() -> Dict` | Get transport details  |

#### Authentication

| Method                                         | Description          |
| ---------------------------------------------- | -------------------- |
| `login(username, password) -> str`             | Login, returns token |
| `create_user(username, password, role) -> int` | Create user (admin)  |
| `delete_user(username) -> bool`                | Delete user (admin)  |

#### Semantic Operations

| Method                                             | Description             |
| -------------------------------------------------- | ----------------------- |
| `insert(node_id, text, metadata, user_id) -> Dict` | Insert document         |
| `search(query, user_id, k) -> List[Dict]`          | Search similar          |
| `batch_insert(documents, user_id) -> Dict`         | Batch insert            |
| `stream_search(query, user_id, k) -> Iterator`     | Streaming search (gRPC) |
| `delete(node_id) -> bool`                          | Delete document         |

#### Agent Memory

| Method                                                  | Description              |
| ------------------------------------------------------- | ------------------------ |
| `memory.add(session_id, agent, content, metadata, ttl)` | Add entry                |
| `memory.get(session_id, limit, after, filter)`          | Get entries              |
| `memory.clear(session_id)`                              | Clear session            |
| `memory.watch(session_id)`                              | Watch for updates (gRPC) |

#### Graph Operations

| Method                                                   | Description         |
| -------------------------------------------------------- | ------------------- |
| `add_edge(from_node, to_node, relation, weight) -> bool` | Add edge            |
| `link(source_id, relation, target_id, weight) -> bool`   | Alias for add_edge  |
| `get_neighbors(node_id, relation) -> List[int]`          | Get neighbors       |
| `traverse(start_node, max_depth) -> List[int]`           | BFS traversal       |
| `sample_graph(limit) -> Dict`                            | Sample graph (HTTP) |

#### ACL Operations

| Method                                                        | Description     |
| ------------------------------------------------------------- | --------------- |
| `grant_permission(node_id, user_id, permissions) -> Dict`     | Grant access    |
| `revoke_permission(node_id, user_id) -> Dict`                 | Revoke access   |
| `check_permission(node_id, user_id, permission_type) -> bool` | Check access    |
| `batch_grant(grants) -> Dict`                                 | Batch grant     |
| `insert_with_acl(node_id, text, metadata, user_permissions)`  | Insert with ACL |

#### SDM Operations

| Method                                         | Description   |
| ---------------------------------------------- | ------------- |
| `write_memory(address, data, user_id) -> Dict` | Write to SDM  |
| `read_memory(address, user_id) -> BitVector`   | Read from SDM |

#### Pub/Sub

| Method                                                           | Description      |
| ---------------------------------------------------------------- | ---------------- |
| `subscribe(filter_type, node_id, vector, threshold) -> Iterator` | Subscribe (gRPC) |

---

## Conclusion

RiceDB Python SDK provides a comprehensive toolkit for building multi-agent AI applications. By combining vector search, graph traversal, agent memory, and access control in a single database, it simplifies the architecture of complex AI systems.

For more examples, see the [examples/](../examples/) directory.

For server setup and deployment, see the main [RiceDB documentation](../../README.md).

---

_Documentation generated for RiceDB Python SDK v0.1.0_
