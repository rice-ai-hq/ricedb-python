"""
RiceDB Python Client

A Python client for connecting to RiceDB vector-graph database servers.
Supports both HTTP and gRPC transports.
"""

from .client import RiceDBClient
from .exceptions import (
    AuthenticationError,
    ConnectionError,
    InsertError,
    RiceDBError,
    SearchError,
)

__version__ = "0.1.0"
__all__ = [
    "RiceDBClient",
    "RiceDBError",
    "ConnectionError",
    "InsertError",
    "SearchError",
    "AuthenticationError",
]
