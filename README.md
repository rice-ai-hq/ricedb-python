# RiceDB Python Client

A Python client for connecting to RiceDB, a high-performance database designed for Multi-Agent AI Systems.

| Challenge                         | RiceDB Solution                                        |
| --------------------------------- | ------------------------------------------------------ |
| Multiple agents need coordination | Native Agent Memory (scratchpad) for real-time sharing |
| Knowledge has relationships       | Integrated semantic linking                            |
| Multi-tenant environments         | Bitmap-based ACL for zero-latency permission checks    |
| High-frequency updates            | LSM-tree storage with Write-Ahead Log (WAL)            |
| Real-time notifications           | Pub/Sub with semantic subscriptions                    |

## Features

- **High Performance**: Supports both HTTP and gRPC transports
- **Agent Memory**: Lightweight time-ordered scratchpad for multi-agent coordination
- **Multi-User ACL**: Bitmap-based access control with zero-latency permission checks
- **Real-time Pub/Sub**: Server-side streaming with semantic subscriptions (gRPC)

## Requirements

- Python 3.10+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip

## Installation

### Installing uv

If you don't have uv installed, install it with:

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Or via Homebrew
brew install uv
```

### As a dependency in your project (Recommended)

Add to your `pyproject.toml`:

```toml
[project]
dependencies = [
    "ricedb[grpc,embeddings] @ git+https://github.com/shankha98/ricedb-python.git",
]
```

Then sync:

```bash
uv sync
```

### From Source

```bash
git clone https://github.com/shankha98/ricedb-python.git
cd ricedb-python
uv sync --extra dev --extra grpc --extra embeddings
```

## Quick Start

```python
from ricedb import RiceDBClient

# Connect to server (auto-detects transport)
client = RiceDBClient("localhost")
client.connect()

# Login (required for authenticated operations)
client.login("admin", "admin")

# Insert a document
client.insert_text(
    node_id=1,
    text="Financial report for Q4 2023",
    metadata={"department": "finance", "year": 2023},
    user_id=100
)

# Search for similar documents
results = client.search_text(
    query="quarterly financial data",
    user_id=100,
    k=5
)

for result in results:
    print(f"Found: {result['metadata']['text']} "
          f"(similarity: {result['similarity']:.4f})")

# Disconnect when done
client.disconnect()
```

## Transport Options

### Auto-Detection (Recommended)

```python
client = RiceDBClient("localhost")  # Tries gRPC first, falls back to HTTP
```

### Explicit Transport Selection

```python
# HTTP only
client = RiceDBClient("localhost", transport="http", port=3000)

# gRPC only
client = RiceDBClient("localhost", transport="grpc", port=50051)
```

### Feature Comparison

| Feature           | HTTP | gRPC            |
| ----------------- | ---- | --------------- |
| Basic CRUD        | Yes  | Yes             |
| Vector Search     | Yes  | Yes             |
| Batch Insert      | Yes  | Yes (Streaming) |
| Stream Search     | No   | Yes             |
| Agent Memory      | Yes  | Yes             |
| Memory Watch      | No   | Yes             |
| ACL Management    | Yes  | Yes             |
| Graph Operations  | Yes  | Yes             |
| Pub/Sub Subscribe | No   | Yes             |
| Graph Sample      | Yes  | No              |

## Embedding Generators

### Dummy Embeddings (for testing)

```python
from ricedb.utils import DummyEmbeddingGenerator

embed_gen = DummyEmbeddingGenerator(dimensions=384)
```

### Sentence Transformers

```python
from ricedb.utils import SentenceTransformersEmbeddingGenerator

embed_gen = SentenceTransformersEmbeddingGenerator(
    model_name="all-MiniLM-L6-v2"
)
```

### OpenAI

```python
from ricedb.utils import OpenAIEmbeddingGenerator

embed_gen = OpenAIEmbeddingGenerator(
    model="text-embedding-ada-002",
    api_key="your-api-key"
)
```

### Hugging Face

```python
from ricedb.utils import HuggingFaceEmbeddingGenerator

embed_gen = HuggingFaceEmbeddingGenerator(
    model_name="sentence-transformers/all-MiniLM-L6-v2"
)
```

## Advanced Usage

### Authentication

All operations require authentication. Login after connecting:

```python
client = RiceDBClient("localhost")
client.connect()
client.login("admin", "admin")

# Admin can create new users
user_id = client.create_user("alice", "password123", role="user")

# Delete users
client.delete_user("alice")
```

### Batch Operations

```python
# Prepare documents
documents = [
    {"id": 1, "vector": [0.1, 0.2, ...], "metadata": {"title": "Doc 1"}},
    {"id": 2, "vector": [0.3, 0.4, ...], "metadata": {"title": "Doc 2"}},
]

# Batch insert
result = client.batch_insert(documents, user_id=100)
print(f"Inserted {result['count']} documents")
```

### Streaming Search (gRPC only)

```python
if client.get_transport_info()["type"] == "grpc":
    for result in client.stream_search(query_vector, user_id=100):
        print(f"Found: {result['metadata']['title']}")
```

### Agent Memory (Scratchpad)

The Agent Memory feature provides a lightweight, time-ordered shared memory for agents. It avoids polluting the main vector index with intermediate thoughts or chat history and is optimized for high-frequency updates.

```python
# 1. Add to memory (No embeddings computed, instant)
client.memory.add(
    session_id="task-123",
    agent="ReviewerAgent",
    content="I found a bug in auth.py",
    metadata={"severity": "high"}
)

# 2. Retrieve history (Time-ordered)
history = client.memory.get(session_id="task-123", limit=10)
for entry in history:
    print(f"[{entry['agent_id']}] {entry['content']}")

# 3. Poll for new messages (using timestamp)
last_check = int(time.time()) - 60
new_msgs = client.memory.get(session_id="task-123", after=last_check)

# 4. Clear session
client.memory.clear("task-123")
```

### User Access Control

```python
# Insert as user 100
client.insert_text(1, "Secret document", user_id=100)

# Search as user 200 (won't find user 100's documents)
results = client.search_text("secret", user_id=200)  # Returns []

# Search as user 100 (will find their own documents)
results = client.search_text("secret", user_id=100)  # Returns documents
```

### Permission Management (HTTP only)

```python
# Grant read/write permissions to another user
client.grant_permission(
    node_id=1,
    user_id=200,
    permissions={"read": True, "write": True, "delete": False}
)

# Check permissions
can_read = client.check_permission(node_id=1, user_id=200, permission_type="read")

# Revoke permissions
client.revoke_permission(node_id=1, user_id=200)

# Insert with multiple user permissions
client.insert_with_acl(
    node_id=5,
    vector=[0.1, 0.2, ...],
    metadata={"title": "Shared Doc"},
    user_permissions=[
        (100, {"read": True, "write": True}),
        (200, {"read": True, "write": False}),
    ]
)
```

### Unified Memory Architecture

RiceDB provides multiple memory types that work together for complete AI agent support:

```
┌───────────────────────────────────────────────────────────────────────┐
│                    Memory Types in RiceDB                              │
├───────────────────────────────────────────────────────────────────────┤
│                                                                        │
│   ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐       │
│   │  Vector Search  │  │  Graph Database │  │      SDM        │       │
│   │                 │  │                 │  │                 │       │
│   │  "What's        │  │  "What's        │  │  "Complete      │       │
│   │   similar?"     │  │   connected?"   │  │   this pattern" │       │
│   │                 │  │                 │  │                 │       │
│   │  Semantic       │  │  Structural     │  │  Associative    │       │
│   │  Similarity     │  │  Relationships  │  │  Recall         │       │
│   └─────────────────┘  └─────────────────┘  └─────────────────┘       │
│           │                    │                    │                  │
│           └────────────────────┼────────────────────┘                  │
│                                │                                       │
│                                ▼                                       │
│                    ┌─────────────────────┐                            │
│                    │  Unified Knowledge  │                            │
│                    │       Layer         │                            │
│                    └─────────────────────┘                            │
│                                                                        │
└───────────────────────────────────────────────────────────────────────┘
```

**Sparse Distributed Memory (SDM)** provides neuromorphic, noise-tolerant pattern completion using 1024-bit vectors - useful for associative recall and error-tolerant memory where partial or noisy queries should still retrieve correct data.

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Decision Guide                                    │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  "I need to find similar content"                                   │
│       └──▶ Vector Search                                            │
│                                                                      │
│  "I need to know what's connected to X"                             │
│       └──▶ Graph Database                                           │
│                                                                      │
│  "I need to recall what I did in a similar situation"               │
│       └──▶ SDM                                                       │
│                                                                      │
│  "I need all context about a topic"                                 │
│       └──▶ Vector Search → Graph Expansion → SDM Pattern Recall     │
│                                                                      │
│  "I need to coordinate multiple agents"                             │
│       └──▶ Agent Memory (Scratchpad)                                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Real-time Pub/Sub (gRPC only)

Subscribe to real-time database events with semantic filtering.

```python
if client.get_transport_info()["type"] == "grpc":
    # Subscribe to all events
    for event in client.subscribe(filter_type="all"):
        print(f"Event: {event['type']}, Node: {event['node_id']}")

    # Semantic subscription (wake on similar vectors)
    for event in client.subscribe(
        filter_type="semantic",
        vector=query_vector,
        threshold=0.85
    ):
        print(f"Similar content inserted: {event['node']}")
```

## Examples

See the [examples](examples/) directory for more detailed examples:

| Example                                                                 | Description                                                   |
| ----------------------------------------------------------------------- | ------------------------------------------------------------- |
| [basic_usage.py](examples/basic_usage.py)                               | Basic CRUD operations with vectors and text                   |
| [http_usage.py](examples/http_usage.py)                                 | Force HTTP transport                                          |
| [grpc_usage.py](examples/grpc_usage.py)                                 | Force gRPC transport with streaming                           |
| [with_sentence_transformers.py](examples/with_sentence_transformers.py) | Using real embeddings with Sentence Transformers              |
| [multi_agent_example.py](examples/multi_agent_example.py)               | Multi-user ACL demonstration                                  |
| [multi_user_acl.py](examples/multi_user_acl.py)                         | Advanced permission management                                |
| [agent_memory_example.py](examples/agent_memory_example.py)             | Native Agent Memory (Scratchpad) for multi-agent coordination |
| [remote_connect.py](examples/remote_connect.py)                         | Connecting to remote RiceDB instances                         |

## Development

### Setup with uv (Recommended)

```bash
# Clone the repository
git clone https://github.com/shankha98/ricedb-python.git
cd ricedb-python

# Quick setup (creates venv and installs dependencies)
./setup.sh

# Or manual setup with uv sync
uv sync --extra dev --extra grpc
```

> **Note:** `uv sync` automatically creates a virtual environment, installs dependencies from `pyproject.toml`, and generates a lockfile (`uv.lock`).

### Using Make

```bash
make setup      # Set up the development environment
make test       # Run tests with coverage
make lint       # Run linters (ruff, ty)
make format     # Format code with ruff
make check      # Run format, lint, and test
make clean      # Clean build artifacts
make build      # Build the package
```

### Running Tests

```bash
# Run all tests with coverage
uv run pytest

# Run specific test file
uv run pytest tests/test_embeddings.py

# Verbose output
uv run pytest -v
```

> **Tip:** `uv run` automatically syncs the environment before running commands, ensuring dependencies are up-to-date.

### Code Quality

```bash
# Format code
uv run ruff format src tests

# Lint code
uv run ruff check src tests

# Type checking
uv run ty check src
```

### Adding Dependencies

```bash
# Add a runtime dependency
uv add requests

# Add a dev dependency
uv add --group dev pytest

# Upgrade a dependency
uv lock --upgrade-package requests
```

## License

This project is licensed under the GPLv3 License - see the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request
