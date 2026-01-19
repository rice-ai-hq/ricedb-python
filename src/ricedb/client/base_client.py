"""
Base abstract class for RiceDB clients.
"""

from abc import ABC, abstractmethod
import concurrent.futures
import time
from typing import Any, Dict, Iterator, List, Optional


class BaseRiceDBClient(ABC):
    """Abstract base class for RiceDB clients."""

    def __init__(self, host: str = "localhost", port: int = 3000, ssl: bool = False):
        """Initialize the client.

        Args:
            host: Server hostname
            port: Server port
            ssl: Use SSL/TLS connection
        """
        self.host = host
        self.port = port
        self.ssl = ssl
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
    def create_user(self, username: str, password: str, role: str = "user") -> int:
        """Create a new user (Admin only).

        Args:
            username: Username
            password: Password
            role: User role ("admin" or "user")

        Returns:
            User ID
        """
        pass

    @abstractmethod
    def delete_user(self, username: str) -> bool:
        """Delete a user (Admin only).

        Args:
            username: Username to delete

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def get_user(self, username: str) -> Dict[str, Any]:
        """Get user details.

        Args:
            username: Username to fetch

        Returns:
            User details (username, user_id, role)
        """
        pass

    @abstractmethod
    def list_users(self) -> List[Dict[str, Any]]:
        """List all users (Admin only).

        Returns:
            List of users
        """
        pass

    @abstractmethod
    def delete(self, node_id: int, session_id: Optional[str] = None) -> bool:
        """Delete a document by ID.

        Args:
            node_id: Node ID to delete
            session_id: Optional Session ID for scratchpad (tombstoning)

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def insert(
        self,
        node_id: int,
        text: str,
        metadata: Dict[str, Any],
        user_id: int = 1,
        session_id: Optional[str] = None,
        embedding: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Insert a document into RiceDB.

        Args:
            node_id: Unique identifier for the document
            text: Text content to insert (will be encoded on server if embedding not provided)
            metadata: Document metadata
            user_id: User ID for ACL
            session_id: Optional Session ID for working memory overlay
            embedding: Optional pre-computed embedding vector (skips server-side encoding)

        Returns:
            Insert response
        """
        pass

    @abstractmethod
    def search(
        self,
        query: str,
        user_id: int,
        k: int = 10,
        session_id: Optional[str] = None,
        filter: Optional[Dict[str, Any]] = None,
        query_embedding: Optional[List[float]] = None,
    ) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            query: Query text
            user_id: User ID for ACL filtering
            k: Number of results to return
            session_id: Optional Session ID for working memory overlay
            filter: Optional metadata filter
            query_embedding: Optional pre-computed query embedding vector

        Returns:
            List of search results
        """
        pass

    @abstractmethod
    def create_session(self, parent_session_id: Optional[str] = None) -> str:
        """Create a new scratchpad session.

        Args:
            parent_session_id: Optional Parent Session ID for nested overlays

        Returns:
            Session ID
        """
        pass

    @abstractmethod
    def snapshot_session(self, session_id: str, path: str) -> bool:
        """Save session to disk.

        Args:
            session_id: Session ID to snapshot
            path: File path to save snapshot to

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def load_session(self, path: str) -> str:
        """Load session from disk.

        Args:
            path: File path to load snapshot from

        Returns:
            Session ID
        """
        pass

    @abstractmethod
    def commit_session(self, session_id: str, merge_strategy: str = "overwrite") -> bool:
        """Commit session changes to base storage.

        Args:
            session_id: Session ID to commit
            merge_strategy: Merge strategy ("overwrite", "bundle", "average")

        Returns:
            True if successful
        """
        pass

    @abstractmethod
    def drop_session(self, session_id: str) -> bool:
        """Discard session.

        Args:
            session_id: Session ID to drop

        Returns:
            True if successful
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
    def sample_graph(self, limit: int = 100) -> Dict[str, Any]:
        """Get a random sample of the graph for visualization.

        Args:
            limit: Maximum number of nodes to return

        Returns:
            Dictionary with 'nodes' (list of IDs) and 'edges' (list of dicts)
        """
        pass

    @abstractmethod
    def subscribe(
        self,
        filter_type: str = "all",
        node_id: Optional[int] = None,
        vector: Optional[
            List[float]
        ] = None,  # Deprecated/Unused for semantic now unless updated to text
        threshold: float = 0.8,
        query_text: Optional[str] = None,
    ) -> Iterator[Dict[str, Any]]:
        """Subscribe to real-time events.

        Args:
            filter_type: Filter type ("all", "node", "semantic")
            node_id: Node ID (for "node" filter)
            vector: Deprecated
            threshold: Similarity threshold for semantic subscription
            query_text: Query text for semantic subscription

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
                text=doc.get("text", ""),
                metadata=doc["metadata"],
                user_id=doc_user_id,
            )
            results.append(result)

        return {"count": len(results), "results": results}

    def fast_ingest(
        self,
        documents: List[Dict[str, Any]],
        batch_size: int = 500,
        max_workers: int = 4,
        user_id: int = 1,
    ) -> Dict[str, Any]:
        """High-performance bulk ingestion using batches and concurrency.

        Args:
            documents: List of documents to insert
            batch_size: Number of documents per batch
            max_workers: Number of concurrent threads
            user_id: User ID to own the documents

        Returns:
            Summary of ingestion (total_inserted, failed_batches, time_taken)
        """
        start_time = time.time()
        total_inserted = 0
        failed_batches = 0
        errors = []

        # Create batches
        batches = [documents[i : i + batch_size] for i in range(0, len(documents), batch_size)]

        def _process_batch(batch):
            try:
                # Delegate to transport-specific batch_insert
                return self.batch_insert(batch, user_id=user_id)
            except Exception as e:
                return e

        with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all batches
            future_to_batch = {executor.submit(_process_batch, batch): batch for batch in batches}

            for future in concurrent.futures.as_completed(future_to_batch):
                result = future.result()
                if isinstance(result, Exception):
                    failed_batches += 1
                    # Store only first few errors to avoid flooding
                    if len(errors) < 10:
                        errors.append(str(result))
                else:
                    # Assume result has 'count'
                    if isinstance(result, dict) and "count" in result:
                        total_inserted += result["count"]
                    else:
                        # Fallback
                        total_inserted += len(future_to_batch[future])

        total_time = time.time() - start_time
        return {
            "total_inserted": total_inserted,
            "failed_batches": failed_batches,
            "errors": errors,
            "time_taken": total_time,
            "throughput": total_inserted / total_time if total_time > 0 else 0,
        }
