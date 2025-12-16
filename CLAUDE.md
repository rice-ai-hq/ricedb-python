# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Environment Setup
```bash
# Quick setup (uses uv package manager)
./setup.sh

# Manual setup
uv venv
source .venv/bin/activate
uv pip install -e ".[dev,grpc]"  # Install with dev dependencies and gRPC support
```

### Testing
```bash
pytest                              # Run all tests with coverage
pytest tests/test_exceptions.py     # Run specific test file
pytest -v                           # Verbose test output
```

### Code Quality
```bash
black src tests                     # Format code (line length: 100)
flake8 src tests                    # Lint code
mypy src                            # Type checking
```

### Installation Options
- Basic: `pip install ricedb`
- With gRPC: `pip install ricedb[grpc]`
- With embeddings: `pip install ricedb[embeddings]`
- With all features: `pip install ricedb[all]`

## Architecture Overview

### Core Design Pattern
The codebase follows a **transport abstraction pattern** with three main client implementations:
- **Base Client** ([src/ricedb/client/base_client.py](src/ricedb/client/base_client.py)): Abstract interface
- **HTTP Client** ([src/ricedb/client/http_client.py](src/ricedb/client/http_client.py)): REST API implementation
- **gRPC Client** ([src/ricedb/client/grpc_client.py](src/ricedb/client/grpc_client.py)): High-performance gRPC implementation
- **Unified Client** ([src/ricedb/client/unified_client.py](src/ricedb/client/unified_client.py)): Auto-selecting transport (main entry point)

### Key Modules
- **Embedding Generators** ([src/ricedb/utils/embeddings.py](src/ricedb/utils/embeddings.py)): Pluggable strategy pattern for text embeddings (Dummy, SentenceTransformers, OpenAI, HuggingFace)
- **Validation** ([src/ricedb/utils/validation.py](src/ricedb/utils/validation.py)): Input validation utilities
- **Session Management** ([src/ricedb/utils/sdm.py](src/ricedb/utils/sdm.py)): Session data management
- **Exceptions** ([src/ricedb/exceptions.py](src/ricedb/exceptions.py)): Custom exception hierarchy

### Transport Selection
The unified client (`RiceDBClient`) automatically detects the best transport:
1. Tries gRPC first (port 50051) for performance
2. Falls back to HTTP (port 3000) if gRPC unavailable
3. Can be forced to use specific transport with `transport` parameter

### User Access Control
All operations support `user_id` parameter for ACL-based data isolation. Documents inserted by one user are not visible to other users unless explicitly shared.

### Testing Structure
- Tests follow pytest conventions in `tests/` directory
- Coverage reporting enabled with `--cov=src/ricedb`
- Three main test files: exceptions, embeddings, validation

### Build System
- Uses modern `pyproject.toml` with setuptools backend
- Supports Python 3.8-3.12
- Optional dependencies managed with extras (`[grpc]`, `[embeddings]`, `[openai]`)
- gRPC protobuf files pre-generated in `src/ricedb/protobuf/`

### Examples
Four practical examples in `examples/` directory:
1. `basic_usage.py` - CRUD operations
2. `with_sentence_transformers.py` - Real embeddings
3. `multi_agent_example.py` - Multi-user ACL
4. `multi_user_acl.py` - Access control demo

When adding new features:
- Follow the transport abstraction pattern
- Add tests to appropriate `test_*.py` file
- Update both HTTP and gRPC clients if modifying core functionality
- Use type hints consistently (mypy is strict)
- Keep the unified client as the primary interface