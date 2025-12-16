# RiceDB Python Client

A pure Python client for connecting to and interacting with [RiceDB](https://github.com/your-org/ricedb), a high-performance vector-graph database.

> **Note:** This package is **only** the client library. You must have a running instance of the RiceDB server to use this client.

## Features

- 🚀 **High Performance**: Supports both HTTP and gRPC transports
- 🔍 **Vector Search**: Fast similarity search with ACL filtering
- 📝 **Text Embeddings**: Built-in support for multiple embedding providers
- 👥 **Multi-User**: Access control lists (ACL) for data isolation
- 📦 **Easy Installation**: `pip install ricedb` and you're ready to go
- 🔄 **Auto-Transport**: Automatically selects the best available connection method

## Installation

```bash
# Basic installation (HTTP only)
pip install ricedb

# With gRPC support (recommended for performance)
pip install ricedb[grpc]

# With embedding support
pip install ricedb[embeddings]

# With all features
pip install ricedb[all]
```

## Quick Start

```python
from ricedb import RiceDBClient

# Connect to server (auto-detects transport)
# Ensure your RiceDB server is running on localhost
client = RiceDBClient("localhost")

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

### User Access Control
```python
# Insert as user 100
client.insert_text(1, "Secret document", user_id=100)

# Search as user 200 (won't find user 100's documents)
results = client.search_text("secret", user_id=200)  # Returns []

# Search as user 100 (will find their own documents)
results = client.search_text("secret", user_id=100)  # Returns documents
```

## Server Setup

This client requires a RiceDB server. Please follow the instructions in the [main RiceDB repository](https://github.com/your-org/ricedb) to install and start the server.

Generally, you will run something like:

### HTTP Server
```bash
# From the RiceDB server repository
cargo run --example http_server --features http-server
```

### gRPC Server
```bash
# From the RiceDB server repository
cargo run --bin ricedb-server-grpc --features grpc-server
```

## Examples

See the [examples](examples/) directory for more detailed examples:

- [basic_usage.py](examples/basic_usage.py) - Basic CRUD operations
- [with_sentence_transformers.py](examples/with_sentence_transformers.py) - Using real embeddings
- [multi_agent_example.py](examples/multi_agent_example.py) - Multi-user ACL demo

## API Reference

### RiceDBClient

#### Methods

- `connect()` - Connect to the server
- `disconnect()` - Disconnect from the server
- `health()` - Check server health
- `insert(node_id, vector, metadata, user_id)` - Insert a document
- `search(vector, user_id, k)` - Search for similar documents
- `insert_text(node_id, text, metadata, embedding_generator, user_id)` - Insert with text
- `search_text(query, embedding_generator, user_id, k)` - Search with text
- `batch_insert(documents, user_id)` - Batch insert documents
- `get_transport_info()` - Get connection information

## Development

This project uses `uv` for dependency management and `ruff`/`pyrefly` for code quality.

### Prerequisites

- [uv](https://github.com/astral-sh/uv)

### Setup
```bash
git clone https://github.com/your-org/ricedb-python
cd ricedb-python
make setup
```

### Running Tests
```bash
make test
```

### Code Quality
```bash
# Format code
make format

# Lint code
make lint

# Run all checks (format, lint, test)
make check
```

## License

This project is proprietary software. All rights reserved. See the [LICENSE](LICENSE) file for details.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run `make check` to ensure quality
6. Submit a pull request

## Support

- 📖 [Documentation](https://ricedb.readthedocs.io)
- 🐛 [Issue Tracker](https://github.com/your-org/ricedb/issues)
- 💬 [Discussions](https://github.com/your-org/ricedb/discussions)
