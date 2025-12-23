"""
Base abstract class for RiceDB clients.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Iterator, List, Optional


class BaseRiceDBClient(ABC):
    """Abstract base class for RiceDB clients."""

    def __init__(self, host: str = "localhost", port: int = 3000):
        """Initialize the client.

        Args:
            host: Server hostname
            port: Server port
        """
        self.host = host
        self.port = port
        self._connected = False

    @abstractmethod
    def connect(self) -> bool:
        """Connect to the RiceDB server.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def disconnect(self):
        """Disconnect from the RiceDB server."""
        pass

    @abstractmethod
    def health(self) -> Dict[str, Any]:
        """Check server health.

        Returns:
            Health information from the server
        """
        pass

    @abstractmethod
    def login(self, username: str, password: str) -> str:
        """Login to the server.

        Args:
            username: Username
            password: Password

        Returns:
            Access token
        """
        pass

    @abstractmethod
    def register(self, username: str, password: str) -> int:
        """Register a new user.

        Args:
            username: Username
            password: Password

        Returns:
            User ID
        """
        pass

    @abstractmethod
    def delete(self, node_id: int) -> bool:
        """Delete a document by ID.

        Args:
            node_id: Node ID to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def insert(
        self,
        node_id: int,
        vector: List[float],
        metadata: Dict[str, Any],
        user_id: int = 1,
    ) -> Dict[str, Any]:
        """Insert a document into RiceDB.

        Args:
            node_id: Unique identifier for the document
            vector: Feature vector
            metadata: Document metadata
            user_id: User ID for ACL

        Returns:
            Insert response
        """
        pass

    @abstractmethod
    def search(self, vector: List[float], user_id: int, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            vector: Query vector
            user_id: User ID for ACL filtering
            k: Number of results to return

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def write_memory(
        self,
        address: Any,  # BitVector
        data: Any,  # BitVector
        user_id: int = 1,
    ) -> Dict[str, Any]:
        """Write to Sparse Distributed Memory.

        Args:
            address: Address BitVector
            data: Data BitVector
            user_id: User ID for ACL

        Returns:
            Write response
        """
        pass

    @abstractmethod
    def read_memory(
        self,
        address: Any,  # BitVector
        user_id: int = 1,
    ) -> Any:  # BitVector
        """Read from Sparse Distributed Memory.

        Args:
            address: Address BitVector
            user_id: User ID for ACL

        Returns:
            Data BitVector
        """
        pass

    def insert_text(
        self,
        node_id: int,
        text: str,
        metadata: Optional[Dict[str, Any]] = None,
        embedding_generator=None,
        user_id: int = 1,
    ) -> Dict[str, Any]:
        """Insert a document with text embedding.

        Args:
            node_id: Unique identifier for the document
            text: Text content to embed
            metadata: Additional document metadata
            embedding_generator: Embedding generator instance
            user_id: User ID for ACL

        Returns:
            Insert response
        """
        if embedding_generator is None:
            from ..utils import DummyEmbeddingGenerator

            embedding_generator = DummyEmbeddingGenerator()

        if metadata is None:
            metadata = {}

        metadata["text"] = text
        vector = embedding_generator.encode(text)

        return self.insert(node_id, vector, metadata, user_id)

    def search_text(
        self, query: str, embedding_generator=None, user_id: int = 1, k: int = 10
    ) -> List[Dict[str, Any]]:
        """Search using text query.

        Args:
            query: Query text
            embedding_generator: Embedding generator instance
            user_id: User ID for ACL filtering
            k: Number of results to return

        Returns:
            List of search results
        """
        if embedding_generator is None:
            from ..utils import DummyEmbeddingGenerator

            embedding_generator = DummyEmbeddingGenerator()

        query_vector = embedding_generator.encode(query)
        return self.search(query_vector, user_id, k)

    @abstractmethod
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
        """
        pass

    @abstractmethod
    def revoke_permission(self, node_id: int, user_id: int) -> Dict[str, Any]:
        """Revoke all permissions for a user on a node.

        Args:
            node_id: Node ID to revoke permissions for
            user_id: User ID to revoke permissions from

        Returns:
            Revoke permission response
        """
        pass

    @abstractmethod
    def check_permission(self, node_id: int, user_id: int, permission_type: str) -> bool:
        """Check if a user has a specific permission on a node.

        Args:
            node_id: Node ID to check permissions for
            user_id: User ID to check permissions for
            permission_type: Type of permission to check ("read", "write", "delete")

        Returns:
            True if user has permission, False otherwise
        """
        pass

    @abstractmethod
    def batch_grant(self, grants: List[tuple]) -> Dict[str, Any]:
        """Grant permissions to multiple users/nodes in batch.

        Args:
            grants: List of tuples (node_id, user_id, permissions_dict)

        Returns:
            Batch grant response
        """
        pass

    @abstractmethod
    def insert_with_acl(
        self,
        node_id: int,
        vector: List[float],
        metadata: Dict[str, Any],
        user_permissions: List[tuple],
    ) -> Dict[str, Any]:
        """Insert a document with multiple user permissions.

        Args:
            node_id: Unique identifier for the document
            vector: Feature vector
            metadata: Document metadata
            user_permissions: List of (user_id, permissions_dict) tuples

        Returns:
            Insert response
        """
        pass

    @abstractmethod
    def add_memory(
        self,
        session_id: str,
        agent_id: str,
        content: str,
        metadata: Optional[Dict[str, str]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add to agent memory.

        Args:
            session_id: Session ID
            agent_id: Agent ID
            content: Memory content
            metadata: Additional metadata
            ttl_seconds: Time-to-live in seconds

        Returns:
            Response with entry
        """
        pass

    @abstractmethod
    def get_memory(
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
            filter: Metadata filter (key-value pairs)

        Returns:
            List of memory entries
        """
        pass

    @abstractmethod
    def clear_memory(self, session_id: str) -> Dict[str, Any]:
        """Clear agent memory.

        Args:
            session_id: Session ID

        Returns:
            Response
        """
        pass

    @abstractmethod
    def watch_memory(self, session_id: str):
        """Watch for new memory events in a session.

        Args:
            session_id: Session ID to watch

        Yields:
            Memory events
        """
        pass

    def link(self, source_id: int, relation: str, target_id: int, weight: float = 1.0) -> bool:
        """Create a semantic link between two nodes.

        Alias for add_edge.

        Args:
            source_id: Source Node ID
            relation: Relationship type (e.g., "IMPORTS", "DEPENDS_ON")
            target_id: Target Node ID
            weight: Edge weight

        Returns:
            True if successful
        """
        return self.add_edge(source_id, target_id, relation, weight)

    @abstractmethod
    def add_edge(self, from_node: int, to_node: int, relation: str, weight: float = 1.0) -> bool:
        """Add an edge between two nodes.

        Args:
            from_node: Source Node ID
            to_node: Target Node ID
            relation: Relationship label
            weight: Edge weight

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_neighbors(self, node_id: int, relation: Optional[str] = None) -> List[int]:
        """Get neighbors of a node.

        Args:
            node_id: Node ID
            relation: Optional relation type filter

        Returns:
            List of neighbor node IDs
        """
        pass

    @abstractmethod
    def traverse(self, start_node: int, max_depth: int = 1) -> List[int]:
        """Traverse the graph from a start node.

        Args:
            start_node: Starting node ID
            max_depth: Maximum traversal depth

        Returns:
            List of visited node IDs
        """
        pass

    @abstractmethod
    def subscribe(
        self,
        filter_type: str = "all",
        node_id: Optional[int] = None,
        vector: Optional[List[float]] = None,
        threshold: float = 0.8,
    ) -> Iterator[Dict[str, Any]]:
        """Subscribe to real-time events.

        Args:
            filter_type: Filter type ("all", "node", "vector")
            node_id: Node ID (for "node" filter)
            vector: Query vector (for "vector" filter)
            threshold: Similarity threshold (for "vector" filter)

        Yields:
            Events as dictionaries
        """
        pass

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
        results = []
        for doc in documents:
            doc_user_id = doc.get("user_id", user_id if user_id is not None else 1)
            result = self.insert(
                node_id=doc["id"],
                vector=doc["vector"],
                metadata=doc["metadata"],
                user_id=doc_user_id,
            )
            results.append(result)

        return {"count": len(results), "results": results}
