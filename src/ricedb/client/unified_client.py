"""
Unified client interface that automatically selects the best transport.
"""

from typing import Any, Dict, Iterator, List, Optional

from ..exceptions import ConnectionError, RiceDBError
from .base_client import BaseRiceDBClient
from .grpc_client import GrpcRiceDBClient
from .http_client import HTTPRiceDBClient


class Memory:
    """Helper class for Agent Memory operations."""

    def __init__(self, client: BaseRiceDBClient):
        self.client = client

    def add(
        self,
        session_id: str,
        agent: str,
        content: str,
        metadata: Optional[Dict[str, str]] = None,
        ttl: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add to agent memory.

        Args:
            session_id: Session ID
            agent: Agent ID
            content: Memory content
            metadata: Additional metadata
            ttl: Time-to-live in seconds
        """
        return self.client.add_memory(session_id, agent, content, metadata, ttl)

    def get(
        self,
        session_id: str,
        limit: int = 50,
        after: Optional[int] = None,
        filter: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get agent memory.

        Args:
            session_id: Session ID
            limit: Max entries to return
            after: Timestamp to start after
            filter: Metadata filter
        """
        return self.client.get_memory(session_id, limit, after, filter)

    def clear(self, session_id: str) -> Dict[str, Any]:
        """Clear agent memory."""
        return self.client.clear_memory(session_id)

    def watch(self, session_id: str):
        """Watch for new memory events in a session (gRPC only)."""
        return self.client.watch_memory(session_id)


class RiceDBClient(BaseRiceDBClient):
    """Unified client that automatically selects the best transport method.

    This client tries to connect via gRPC first for maximum performance,
    and falls back to HTTP if gRPC is not available.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: Optional[int] = None,
        transport: str = "auto",
        http_port: int = 3000,
        grpc_port: int = 50051,
        **kwargs,
    ):
        """Initialize the unified client.

        Args:
            host: Server hostname
            port: Server port (if specified, used for both transports)
            transport: Transport method - "auto", "http", or "grpc"
            http_port: Port for HTTP server
            grpc_port: Port for gRPC server
            **kwargs: Additional arguments passed to the underlying client
        """
        # Initialize base with default values
        super().__init__(host, http_port)

        self.transport_type = transport.lower()
        self.http_port = port if port is not None else http_port
        self.grpc_port = port if port is not None else grpc_port
        self.kwargs = kwargs
        self._client: Optional[BaseRiceDBClient] = None
        self.memory = Memory(self)

        # Validate transport type
        if self.transport_type not in ["auto", "http", "grpc"]:
            raise ValueError(f"Invalid transport type: {transport}. Use 'auto', 'http', or 'grpc'")

    def _get_client(self) -> BaseRiceDBClient:
        """Get or create the appropriate client instance."""
        if self._client is not None:
            return self._client

        if self.transport_type == "auto":
            # Try gRPC first, then HTTP
            try:
                self._client = GrpcRiceDBClient(host=self.host, port=self.grpc_port, **self.kwargs)
                if self._client.connect():
                    print(f"✓ Connected via gRPC to {self.host}:{self.grpc_port}")
                    return self._client
            except (ConnectionError, ImportError) as e:
                print(f"DEBUG: gRPC connection failed: {e}")
                pass
            except Exception as e:
                print(f"DEBUG: Unexpected gRPC error: {e}")
                pass

            # Fall back to HTTP
            try:
                self._client = HTTPRiceDBClient(host=self.host, port=self.http_port, **self.kwargs)
                if self._client.connect():
                    print(f"✓ Connected via HTTP to {self.host}:{self.http_port}")
                    return self._client
            except ConnectionError:
                pass

            raise ConnectionError(
                f"Failed to connect to RiceDB server on {self.host} "
                f"(tried gRPC:{self.grpc_port} and HTTP:{self.http_port})"
            )

        elif self.transport_type == "grpc":
            try:
                self._client = GrpcRiceDBClient(host=self.host, port=self.grpc_port, **self.kwargs)
            except ImportError as e:
                raise RiceDBError(
                    "gRPC transport requires grpcio package. "
                    "Install it with: pip install ricedb[grpc]"
                ) from e

        elif self.transport_type == "http":
            self._client = HTTPRiceDBClient(host=self.host, port=self.http_port, **self.kwargs)

        return self._client  # ty:ignore[invalid-return-type]

    def connect(self) -> bool:
        """Connect to the RiceDB server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            client = self._get_client()
            if not client._connected:
                result = client.connect()
                if result:
                    self._connected = True
                    self.port = client.port
                return result
            return True
        except Exception:
            return False

    def disconnect(self):
        """Disconnect from the RiceDB server."""
        if self._client:
            self._client.disconnect()
            self._connected = False

    def health(self) -> Dict[str, Any]:
        """Check server health.

        Returns:
            Health information from the server
        """
        client = self._get_client()
        return client.health()

    def login(self, username: str, password: str) -> str:
        """Login to the server.

        Args:
            username: Username
            password: Password

        Returns:
            Access token
        """
        client = self._get_client()
        return client.login(username, password)

    def create_user(self, username: str, password: str, role: str = "user") -> int:
        """Create a new user (Admin only).

        Args:
            username: Username
            password: Password
            role: User role ("admin" or "user")

        Returns:
            User ID
        """
        client = self._get_client()
        return client.create_user(username, password, role)

    def delete_user(self, username: str) -> bool:
        """Delete a user (Admin only).

        Args:
            username: Username to delete

        Returns:
            True if successful
        """
        client = self._get_client()
        return client.delete_user(username)

    def get_user(self, username: str) -> Dict[str, Any]:
        """Get user details.

        Args:
            username: Username to fetch

        Returns:
            User details (username, user_id, role)
        """
        client = self._get_client()
        return client.get_user(username)

    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (Admin only).

        Returns:
            List of users
        """
        client = self._get_client()
        return client.list_users()

    def delete(self, node_id: int, session_id: Optional[str] = None) -> bool:
        """Delete a document by ID.

        Args:
            node_id: Node ID to delete
            session_id: Optional Session ID for scratchpad (tombstoning)

        Returns:
            True if successful
        """
        client = self._get_client()
        return client.delete(node_id, session_id=session_id)

    def insert(
        self,
        node_id: int,
        text: str,
        metadata: Dict[str, Any],
        user_id: int = 1,
        session_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Insert a document into RiceDB.

        Args:
            node_id: Unique identifier for the document
            text: Text content to insert
            metadata: Document metadata
            user_id: User ID for ACL
            session_id: Optional Session ID for working memory overlay

        Returns:
            Insert response
        """
        client = self._get_client()
        return client.insert(node_id, text, metadata, user_id, session_id)

    def search(
        self, query: str, user_id: int, k: int = 10, session_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            query: Query text
            user_id: User ID for ACL filtering
            k: Number of results to return
            session_id: Optional Session ID for working memory overlay

        Returns:
            List of search results
        """
        client = self._get_client()
        return client.search(query, user_id, k, session_id)

    def create_session(self, parent_session_id: Optional[str] = None) -> str:
        """Create a new scratchpad session."""
        client = self._get_client()
        return client.create_session(parent_session_id=parent_session_id)

    def snapshot_session(self, session_id: str, path: str) -> bool:
        """Save session to disk."""
        client = self._get_client()
        return client.snapshot_session(session_id, path)

    def load_session(self, path: str) -> str:
        """Load session from disk."""
        client = self._get_client()
        return client.load_session(path)

    def commit_session(self, session_id: str, merge_strategy: str = "overwrite") -> bool:
        """Commit session changes to base storage."""
        client = self._get_client()
        return client.commit_session(session_id, merge_strategy=merge_strategy)

    def drop_session(self, session_id: str) -> bool:
        """Discard session."""
        client = self._get_client()
        return client.drop_session(session_id)

    def batch_insert(
        self, documents: List[Dict[str, Any]], user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Batch insert multiple documents.

        Args:
            documents: List of documents to insert
            user_id: Default user ID for documents without one

        Returns:
            Batch insert response
        """
        client = self._get_client()
        return client.batch_insert(documents, user_id)

    def stream_search(self, query: str, user_id: int, k: int = 10):
        """Stream search results as they're found (gRPC only).

        Args:
            query: Query text
            user_id: User ID for ACL filtering
            k: Number of results to return

        Yields:
            Search results as they arrive

        Note:
            Only available when using gRPC transport. Will raise an error
            if connected via HTTP.
        """
        client = self._get_client()
        if not isinstance(client, GrpcRiceDBClient):
            raise RiceDBError("Stream search is only available with gRPC transport")
        return client.stream_search(query, user_id, k)

    def write_memory(self, address: Any, data: Any, user_id: int = 1) -> Dict[str, Any]:
        """Write to Sparse Distributed Memory.

        Args:
            address: Address BitVector
            data: Data BitVector
            user_id: User ID for ACL

        Returns:
            Write response
        """
        client = self._get_client()
        return client.write_memory(address, data, user_id)

    def read_memory(self, address: Any, user_id: int = 1) -> Any:
        """Read from Sparse Distributed Memory.

        Args:
            address: Address BitVector
            user_id: User ID for ACL

        Returns:
            Data BitVector
        """
        client = self._get_client()
        return client.read_memory(address, user_id)

    def grant_permission(
        self, node_id: int, user_id: int, permissions: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Grant permissions to a user for a node.

        Args:
            node_id: Node ID to grant permissions for
            user_id: User ID to grant permissions to
            permissions: Dictionary with read/write/delete boolean flags

        Returns:
            Grant permission response

        Note:
            Only supported with HTTP transport. gRPC will raise an error.
        """
        client = self._get_client()
        return client.grant_permission(node_id, user_id, permissions)

    def revoke_permission(self, node_id: int, user_id: int) -> Dict[str, Any]:
        """Revoke all permissions for a user on a node.

        Args:
            node_id: Node ID to revoke permissions for
            user_id: User ID to revoke permissions from

        Returns:
            Revoke permission response

        Note:
            Only supported with HTTP transport. gRPC will raise an error.
        """
        client = self._get_client()
        return client.revoke_permission(node_id, user_id)

    def check_permission(self, node_id: int, user_id: int, permission_type: str) -> bool:
        """Check if a user has a specific permission on a node.

        Args:
            node_id: Node ID to check permissions for
            user_id: User ID to check permissions for
            permission_type: Type of permission to check ("read", "write", "delete")

        Returns:
            True if user has permission, False otherwise

        Note:
            Only supported with HTTP transport. gRPC will raise an error.
        """
        client = self._get_client()
        return client.check_permission(node_id, user_id, permission_type)

    def batch_grant(self, grants: List[tuple]) -> Dict[str, Any]:
        """Grant permissions to multiple users/nodes in batch.

        Args:
            grants: List of tuples (node_id, user_id, permissions_dict)

        Returns:
            Batch grant response

        Note:
            Only supported with HTTP transport. gRPC will raise an error.
        """
        client = self._get_client()
        return client.batch_grant(grants)

    def insert_with_acl(
        self,
        node_id: int,
        text: str,
        metadata: Dict[str, Any],
        user_permissions: List[tuple],
    ) -> Dict[str, Any]:
        """Insert a document with multiple user permissions.

        Args:
            node_id: Unique identifier for the document
            text: Text content
            metadata: Document metadata
            user_permissions: List of (user_id, permissions_dict) tuples

        Returns:
            Insert response with ACL information

        Note:
            For full multi-user support, use HTTP transport.
            gRPC will fall back to single-user insert.
        """
        client = self._get_client()
        return client.insert_with_acl(node_id, text, metadata, user_permissions)

    def get_transport_info(self) -> Dict[str, Any]:
        """Get information about the current transport.

        Returns:
            Dictionary with transport details
        """
        client = self._get_client()
        transport_type = type(client).__name__

        if isinstance(client, GrpcRiceDBClient):
            return {
                "type": "grpc",
                "port": self.grpc_port,
                "class": transport_type,
                "features": ["streaming", "batch operations", "high performance"],
                "acl_support": False,
            }
        elif isinstance(client, HTTPRiceDBClient):
            return {
                "type": "http",
                "port": self.http_port,
                "class": transport_type,
                "features": [
                    "rest api",
                    "easy debugging",
                    "broad compatibility",
                    "acl support",
                ],
                "acl_support": True,
            }

        return {
            "type": "unknown",
            "class": transport_type,
            "features": [],
            "acl_support": False,
        }

    def add_memory(
        self,
        session_id: str,
        agent_id: str,
        content: str,
        metadata: Optional[Dict[str, str]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add to agent memory."""
        client = self._get_client()
        return client.add_memory(session_id, agent_id, content, metadata, ttl_seconds)

    def get_memory(
        self,
        session_id: str,
        limit: int = 50,
        after: Optional[int] = None,
        filter: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get agent memory."""
        client = self._get_client()
        return client.get_memory(session_id, limit, after, filter)

    def clear_memory(self, session_id: str) -> Dict[str, Any]:
        """Clear agent memory."""
        client = self._get_client()
        return client.clear_memory(session_id)

    def watch_memory(self, session_id: str):
        """Watch for new memory events in a session."""
        client = self._get_client()
        return client.watch_memory(session_id)

    def link(self, source_id: int, relation: str, target_id: int, weight: float = 1.0) -> bool:
        """Create a semantic link between two nodes."""
        return self.add_edge(source_id, target_id, relation, weight)

    def add_edge(self, from_node: int, to_node: int, relation: str, weight: float = 1.0) -> bool:
        """Add an edge between two nodes."""
        client = self._get_client()
        return client.add_edge(from_node, to_node, relation, weight)

    def get_neighbors(self, node_id: int, relation: Optional[str] = None) -> List[int]:
        """Get neighbors of a node."""
        client = self._get_client()
        return client.get_neighbors(node_id, relation)

    def traverse(self, start_node: int, max_depth: int = 1) -> List[int]:
        """Traverse the graph from a start node."""
        client = self._get_client()
        return client.traverse(start_node, max_depth)

    def sample_graph(self, limit: int = 100) -> Dict[str, Any]:
        """Get a random sample of the graph for visualization."""
        client = self._get_client()
        return client.sample_graph(limit)

    def subscribe(
        self,
        filter_type: str = "all",
        node_id: Optional[int] = None,
        vector: Optional[List[float]] = None,
        threshold: float = 0.8,
    ) -> Iterator[Dict[str, Any]]:
        """Subscribe to real-time events."""
        client = self._get_client()
        return client.subscribe(
            filter_type=filter_type, node_id=node_id, vector=vector, threshold=threshold
        )
