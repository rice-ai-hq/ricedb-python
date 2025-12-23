"""
HTTP client implementation for RiceDB.
"""

from typing import Any, Dict, Iterator, List, Optional

import requests

from ricedb.exceptions import AuthenticationError

from ..exceptions import ConnectionError, InsertError, RiceDBError, SearchError
from ..utils import BitVector
from .base_client import BaseRiceDBClient


class HTTPRiceDBClient(BaseRiceDBClient):
    """HTTP client for RiceDB."""

    def __init__(self, host: str = "localhost", port: int = 3000, timeout: int = 30):
        """Initialize the HTTP client.

        Args:
            host: Server hostname
            port: Server port
            timeout: Request timeout in seconds
        """
        super().__init__(host, port)
        self.base_url = f"http://{host}:{port}"
        self.timeout = timeout
        self.session = requests.Session()
        self.token = None

    def login(self, username: str, password: str) -> str:
        """Login to the server.

        Args:
            username: Username
            password: Password

        Returns:
            Access token
        """
        try:
            response = self.session.post(
                f"{self.base_url}/auth/login",
                json={"username": username, "password": password},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            self.token = data["token"]
            self.session.headers.update({"Authorization": f"Bearer {self.token}"})
            return self.token
        except requests.RequestException as e:
            raise AuthenticationError(f"Login failed: {e}")  # noqa: B904, F821  # ty:ignore[unresolved-reference]

    def register(self, username: str, password: str) -> int:
        """Register a new user.

        Args:
            username: Username
            password: Password

        Returns:
            User ID
        """
        try:
            response = self.session.post(
                f"{self.base_url}/auth/register",
                json={"username": username, "password": password},
                timeout=self.timeout,
            )
            response.raise_for_status()
            data = response.json()
            return data["user_id"]
        except requests.RequestException as e:
            raise AuthenticationError(f"Registration failed: {e}")  # noqa: B904

    def delete(self, node_id: int, user_id: int = 1) -> bool:
        """Delete a document by ID.

        Args:
            node_id: Node ID to delete
            user_id: User ID (unused, kept for compatibility)

        Returns:
            True if successful
        """
        try:
            response = self.session.delete(
                f"{self.base_url}/node/{node_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to delete node: {e}")  # noqa: B904

    def connect(self) -> bool:
        """Connect to the RiceDB server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            self._connected = response.status_code == 200
            return self._connected
        except requests.RequestException as e:
            raise ConnectionError(f"Failed to connect to RiceDB server: {e}")  # noqa: B904

    def disconnect(self):
        """Disconnect from the RiceDB server."""
        if self.session:
            self.session.close()
        self._connected = False

    def health(self) -> Dict[str, Any]:
        """Check server health.

        Returns:
            Health information from the server
        """
        try:
            response = self.session.get(f"{self.base_url}/health", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise ConnectionError(f"Health check failed: {e}")  # noqa: B904

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
        try:
            response = self.session.post(
                f"{self.base_url}/insert",
                json={
                    "id": node_id,
                    "vector": vector,
                    "metadata": metadata,
                    "user_id": user_id,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()

            if not result.get("success", False):
                raise InsertError(result.get("message", "Insert failed"))

            return result
        except requests.RequestException as e:
            raise InsertError(f"Insert request failed: {e}")  # noqa: B904

    def search(self, vector: List[float], user_id: int, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            vector: Query vector
            user_id: User ID for ACL filtering
            k: Number of results to return

        Returns:
            List of search results
        """
        try:
            response = self.session.post(
                f"{self.base_url}/search",
                json={"vector": vector, "user_id": user_id, "k": k},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise SearchError(f"Search request failed: {e}")  # noqa: B904

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
        try:
            payload = []
            for doc in documents:
                doc_user_id = doc.get("user_id", user_id if user_id is not None else 1)
                payload.append(
                    {
                        "id": doc["id"],
                        "vector": doc["vector"],
                        "metadata": doc["metadata"],
                        "user_id": doc_user_id,
                    }
                )

            response = self.session.post(
                f"{self.base_url}/batch_insert", json=payload, timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise InsertError(f"Batch insert request failed: {e}")  # noqa: B904

    def write_memory(self, address: BitVector, data: BitVector, user_id: int = 1) -> Dict[str, Any]:
        """Write to Sparse Distributed Memory."""
        try:
            response = self.session.post(
                f"{self.base_url}/sdm/write",
                json={
                    "address": address.to_list(),
                    "data": data.to_list(),
                    "user_id": user_id,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RiceDBError(f"SDM write failed: {e}")  # noqa: B904

    def read_memory(self, address: BitVector, user_id: int = 1) -> BitVector:
        """Read from Sparse Distributed Memory."""
        try:
            response = self.session.post(
                f"{self.base_url}/sdm/read",
                json={"address": address.to_list(), "user_id": user_id},
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            return BitVector(result["data"])
        except requests.RequestException as e:
            raise RiceDBError(f"SDM read failed: {e}")  # noqa: B904

    def get_metadata(self, node_id: int) -> Dict[str, Any]:
        """Get metadata for a specific node.

        Args:
            node_id: Node ID

        Returns:
            Node metadata
        """
        try:
            response = self.session.get(f"{self.base_url}/node/{node_id}", timeout=self.timeout)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to get node metadata: {e}")  # noqa: B904

    def update_metadata(
        self, node_id: int, metadata: Dict[str, Any], user_id: int = 1
    ) -> Dict[str, Any]:
        """Update metadata for a specific node.

        Args:
            node_id: Node ID
            metadata: New metadata
            user_id: User ID for ACL

        Returns:
            Update response
        """
        try:
            response = self.session.put(
                f"{self.base_url}/node/{node_id}",
                json={"metadata": metadata, "user_id": user_id},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to update node metadata: {e}")  # noqa: B904

    def delete_node(self, node_id: int, user_id: int = 1) -> Dict[str, Any]:
        """Delete a specific node.

        Args:
            node_id: Node ID to delete
            user_id: User ID (unused)

        Returns:
            Delete response
        """
        success = self.delete(node_id, user_id)
        return {"success": success, "message": f"Deleted node {node_id}"}

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
        try:
            response = self.session.post(
                f"{self.base_url}/acl/grant",
                json={
                    "node_id": node_id,
                    "user_id": user_id,
                    "permissions": permissions,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to grant permission: {e}")  # noqa: B904

    def revoke_permission(self, node_id: int, user_id: int) -> Dict[str, Any]:
        """Revoke all permissions for a user on a node.

        Args:
            node_id: Node ID to revoke permissions for
            user_id: User ID to revoke permissions from

        Returns:
            Revoke permission response
        """
        try:
            response = self.session.post(
                f"{self.base_url}/acl/revoke",
                json={"node_id": node_id, "user_id": user_id},
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to revoke permission: {e}")  # noqa: B904

    def check_permission(self, node_id: int, user_id: int, permission_type: str) -> bool:
        """Check if a user has a specific permission on a node.

        Args:
            node_id: Node ID to check permissions for
            user_id: User ID to check permissions for
            permission_type: Type of permission to check ("read", "write", "delete")

        Returns:
            True if user has permission, False otherwise
        """
        try:
            response = self.session.post(
                f"{self.base_url}/acl/check",
                json={
                    "node_id": node_id,
                    "user_id": user_id,
                    "permission_type": permission_type,
                },
                timeout=self.timeout,
            )
            response.raise_for_status()
            result = response.json()
            return result.get("allowed", False)
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to check permission: {e}")  # noqa: B904

    def batch_grant(self, grants: List[tuple]) -> Dict[str, Any]:
        """Grant permissions to multiple users/nodes in batch.

        Note: Since the server doesn't have a batch_grant endpoint yet,
        this implementation makes multiple individual grant requests.

        Args:
            grants: List of tuples (node_id, user_id, permissions_dict)

        Returns:
            Batch grant response with individual results
        """
        results = []
        errors = []

        for i, (node_id, user_id, permissions) in enumerate(grants):
            try:
                result = self.grant_permission(node_id, user_id, permissions)
                results.append(
                    {
                        "index": i,
                        "node_id": node_id,
                        "user_id": user_id,
                        "success": True,
                        "result": result,
                    }
                )
            except Exception as e:
                errors.append(
                    {
                        "index": i,
                        "node_id": node_id,
                        "user_id": user_id,
                        "error": str(e),
                    }
                )

        return {
            "total": len(grants),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors,
        }

    def insert_with_acl(
        self,
        node_id: int,
        vector: List[float],
        metadata: Dict[str, Any],
        user_permissions: List[tuple],
    ) -> Dict[str, Any]:
        """Insert a document with multiple user permissions.

        This is a two-step process:
        1. Insert the document for the primary user
        2. Grant permissions to additional users

        Args:
            node_id: Unique identifier for the document
            vector: Feature vector
            metadata: Document metadata
            user_permissions: List of (user_id, permissions_dict) tuples

        Returns:
            Insert response with ACL information
        """
        # Use the first user as the primary owner
        if not user_permissions:
            raise ValueError("At least one user permission must be provided")

        primary_user_id, primary_permissions = user_permissions[0]

        # First, insert the document for the primary user
        try:
            insert_response = self.insert(
                node_id=node_id,
                vector=vector,
                metadata=metadata,
                user_id=primary_user_id,
            )

            # If there are additional users, grant them permissions
            additional_grants = []
            for user_id, permissions in user_permissions[1:]:
                additional_grants.append((node_id, user_id, permissions))

            if additional_grants:
                grant_response = self.batch_grant(additional_grants)
                insert_response["acl_grants"] = grant_response

            insert_response["acl_users"] = [
                {"user_id": uid, "permissions": perms} for uid, perms in user_permissions
            ]

            return insert_response

        except (InsertError, RiceDBError) as e:
            raise InsertError(f"Failed to insert with ACL: {e}")  # noqa: B904

    def add_memory(
        self,
        session_id: str,
        agent_id: str,
        content: str,
        metadata: Optional[Dict[str, str]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add to agent memory."""
        try:
            payload = {
                "agent_id": agent_id,
                "content": content,
                "metadata": metadata or {},
            }
            if ttl_seconds is not None:
                payload["ttl_seconds"] = ttl_seconds

            response = self.session.post(
                f"{self.base_url}/memory/{session_id}",
                json=payload,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to add memory: {e}")  # noqa: B904

    def get_memory(
        self,
        session_id: str,
        limit: int = 50,
        after: Optional[int] = None,
        filter: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get agent memory."""
        try:
            params = {"limit": limit}
            if after is not None:
                params["after_timestamp"] = after

            # Note: Complex filter map not yet fully supported via simple query params in HTTP
            # endpoint. We skip sending filter for now if it's complex, or we could JSON encode
            # it if server supported it.
            # Server implementation currently ignores filter in HTTP handler for simplicity.

            response = self.session.get(
                f"{self.base_url}/memory/{session_id}",
                params=params,
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json().get("entries", [])
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to get memory: {e}")  # noqa: B904

    def clear_memory(self, session_id: str) -> Dict[str, Any]:
        """Clear agent memory."""
        try:
            response = self.session.delete(
                f"{self.base_url}/memory/{session_id}",
                timeout=self.timeout,
            )
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            raise RiceDBError(f"Failed to clear memory: {e}")  # noqa: B904

    def watch_memory(self, session_id: str):
        """Watch for new memory events in a session."""
        raise RiceDBError("Watch memory is not supported via HTTP transport. Use gRPC.")

    def add_edge(self, from_node: int, to_node: int, relation: str, weight: float = 1.0) -> bool:
        """Add an edge between two nodes."""
        raise RiceDBError("Add edge is not supported via HTTP transport. Use gRPC.")

    def get_neighbors(self, node_id: int, relation: Optional[str] = None) -> List[int]:
        """Get neighbors of a node."""
        raise RiceDBError("Get neighbors is not supported via HTTP transport. Use gRPC.")

    def traverse(self, start_node: int, max_depth: int = 1) -> List[int]:
        """Traverse the graph from a start node."""
        raise RiceDBError("Traverse is not supported via HTTP transport. Use gRPC.")

    def subscribe(
        self,
        filter_type: str = "all",
        node_id: Optional[int] = None,
        vector: Optional[List[float]] = None,
        threshold: float = 0.8,
    ) -> Iterator[Dict[str, Any]]:
        """Subscribe to real-time events."""
        raise RiceDBError("Subscribe is not supported via HTTP transport. Use gRPC.")
