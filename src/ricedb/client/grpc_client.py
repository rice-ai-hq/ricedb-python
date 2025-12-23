"""
gRPC client implementation for RiceDB.
"""

import json
from typing import Any, Dict, Iterator, List, Optional

import grpc

from ..exceptions import ConnectionError, InsertError, RiceDBError, SearchError
from ..protobuf import ricedb_pb2, ricedb_pb2_grpc
from ..utils import BitVector
from .base_client import BaseRiceDBClient


class GrpcRiceDBClient(BaseRiceDBClient):
    """gRPC client for RiceDB."""

    def __init__(
        self,
        host: str = "localhost",
        port: int = 50051,
        max_message_length: int = 50 * 1024 * 1024,
        keepalive_time_ms: int = 30000,
        keepalive_timeout_ms: int = 10000,
    ):
        """Initialize the gRPC client.

        Args:
            host: Server hostname
            port: Server port
            max_message_length: Maximum message size in bytes
            keepalive_time_ms: Keepalive time in milliseconds
            keepalive_timeout_ms: Keepalive timeout in milliseconds
        """
        super().__init__(host, port)
        self.address = f"{host}:{port}"
        self.channel = None
        self.stub = None
        self.token = None
        self.user_id = None

        # gRPC channel options
        self.options = [
            ("grpc.max_send_message_length", max_message_length),
            ("grpc.max_receive_message_length", max_message_length),
            ("grpc.keepalive_time_ms", keepalive_time_ms),
            ("grpc.keepalive_timeout_ms", keepalive_timeout_ms),
            ("grpc.http2.max_pings_without_data", 0),
            ("grpc.http2.min_time_between_pings_ms", 10000),
            ("grpc.http2.min_ping_interval_without_data_ms", 300000),
        ]

    def _metadata(self):
        """Get authentication metadata"""
        if self.token:
            return [("authorization", f"Bearer {self.token}")]
        return []

    def login(self, username: str, password: str) -> str:
        """Login to get access token."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.LoginRequest(username=username, password=password)  # ty:ignore[unresolved-attribute]
            response = self.stub.Login(request)
            self.token = response.token
            self.user_id = response.user_id
            return self.token
        except grpc.RpcError as e:
            raise ConnectionError(f"Login failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def connect(self) -> bool:
        """Connect to the RiceDB server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.channel = grpc.insecure_channel(self.address, options=self.options)
            self.stub = ricedb_pb2_grpc.RiceDBStub(self.channel)

            # Test connection with health check
            self.stub.Health(ricedb_pb2.HealthRequest())  # ty:ignore[unresolved-attribute]
            self._connected = True
            return True
        except grpc.RpcError as e:
            raise ConnectionError(f"Failed to connect to RiceDB gRPC server: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def disconnect(self):
        """Disconnect from the RiceDB server."""
        if self.channel:
            self.channel.close()
        self._connected = False

    def health(self) -> Dict[str, Any]:
        """Check server health.

        Returns:
            Health information from the server
        """
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            response = self.stub.Health(ricedb_pb2.HealthRequest())  # ty:ignore[unresolved-attribute]
            return {"status": response.status, "version": response.version}
        except grpc.RpcError as e:
            raise ConnectionError(f"Health check failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

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
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.InsertRequest(  # ty:ignore[unresolved-attribute]
                id=node_id,
                vector=vector,
                metadata=json.dumps(metadata).encode("utf-8"),
                user_id=user_id,
            )
            response = self.stub.Insert(request, metadata=self._metadata())

            if not response.success:
                raise InsertError(response.message)

            return {
                "success": response.success,
                "node_id": response.node_id,
                "message": response.message,
            }
        except grpc.RpcError as e:
            raise InsertError(f"Insert request failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def search(self, vector: List[float], user_id: int, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar documents.

        Args:
            vector: Query vector
            user_id: User ID for ACL filtering
            k: Number of results to return

        Returns:
            List of search results
        """
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.SearchRequest(vector=vector, user_id=user_id, k=k)  # ty:ignore[unresolved-attribute]
            response = self.stub.Search(request, metadata=self._metadata())

            results = []
            for result in response.results:
                metadata = json.loads(result.metadata.decode("utf-8"))
                results.append(
                    {
                        "id": result.id,
                        "similarity": result.similarity,
                        "metadata": metadata,
                    }
                )
            return results
        except grpc.RpcError as e:
            raise SearchError(f"Search request failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def batch_insert(
        self, documents: List[Dict[str, Any]], user_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Batch insert multiple documents (streaming).

        Args:
            documents: List of documents to insert
            user_id: Default user ID for documents without one

        Returns:
            Batch insert response
        """
        if not self.stub:
            raise ConnectionError("Not connected to server")

        def request_generator():
            for doc in documents:
                doc_user_id = doc.get("user_id", user_id if user_id is not None else 1)
                yield ricedb_pb2.InsertRequest(  # ty:ignore[unresolved-attribute]
                    id=doc["id"],
                    vector=doc["vector"],
                    metadata=json.dumps(doc["metadata"]).encode("utf-8"),
                    user_id=doc_user_id,
                )

        try:
            response = self.stub.BatchInsert(request_generator(), metadata=self._metadata())
            return {"count": response.count, "node_ids": list(response.node_ids)}
        except grpc.RpcError as e:
            raise InsertError(f"Batch insert request failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def stream_search(
        self, vector: List[float], user_id: int, k: int = 10
    ) -> Iterator[Dict[str, Any]]:
        """Stream search results as they're found.

        Args:
            vector: Query vector
            user_id: User ID for ACL filtering
            k: Number of results to return

        Yields:
            Search results as they arrive
        """
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.SearchRequest(vector=vector, user_id=user_id, k=k)  # ty:ignore[unresolved-attribute]

            for result in self.stub.StreamSearch(request, metadata=self._metadata()):
                metadata = json.loads(result.metadata.decode("utf-8"))
                yield {
                    "id": result.id,
                    "similarity": result.similarity,
                    "metadata": metadata,
                }
        except grpc.RpcError as e:
            raise SearchError(f"Stream search request failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def write_memory(self, address: BitVector, data: BitVector, user_id: int = 1) -> Dict[str, Any]:
        """Write to SDM."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.WriteMemoryRequest(  # ty:ignore[unresolved-attribute]
                address=ricedb_pb2.BitVector(chunks=address.to_list()),  # ty:ignore[unresolved-attribute]
                data=ricedb_pb2.BitVector(chunks=data.to_list()),  # ty:ignore[unresolved-attribute]
                user_id=user_id,
            )
            response = self.stub.WriteMemory(request, metadata=self._metadata())
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            raise RiceDBError(f"SDM write failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def read_memory(self, address: BitVector, user_id: int = 1) -> BitVector:
        """Read from SDM."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.ReadMemoryRequest(  # ty:ignore[unresolved-attribute]
                address=ricedb_pb2.BitVector(chunks=address.to_list()),  # ty:ignore[unresolved-attribute]
                user_id=user_id,  # ty:ignore[unresolved-attribute]
            )
            response = self.stub.ReadMemory(request, metadata=self._metadata())
            return BitVector(list(response.data.chunks))
        except grpc.RpcError as e:
            raise RiceDBError(f"SDM read failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def batch_insert_texts(
        self,
        texts_metadata: List[Dict[str, Any]],
        embedding_generator,
        user_id: int = 1,
    ) -> Dict[str, Any]:
        """Batch insert documents with text embeddings.

        Args:
            texts_metadata: List of documents with text content
            embedding_generator: Embedding generator instance
            user_id: User ID for ACL

        Returns:
            Batch insert response
        """
        texts = [item["text"] for item in texts_metadata]
        embeddings = embedding_generator.encode_batch(texts)

        documents = []
        for i, item in enumerate(texts_metadata):
            doc = {
                "id": item["id"],
                "vector": embeddings[i],
                "metadata": {k: v for k, v in item.items() if k not in ["id", "text"]},
                "user_id": user_id,
            }
            documents.append(doc)

        return self.batch_insert(documents)

    def register(self, username: str, password: str) -> int:
        """Register a new user."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.RegisterRequest(username=username, password=password)  # ty:ignore[unresolved-attribute]
            response = self.stub.Register(request)
            return response.user_id
        except grpc.RpcError as e:
            raise ConnectionError(f"Registration failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def get(self, node_id: int) -> Optional[Dict[str, Any]]:
        """Get a document by ID."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.GetNodeRequest(node_id=node_id)  # ty:ignore[unresolved-attribute]
            response = self.stub.GetNode(request, metadata=self._metadata())

            node = response.node
            metadata = json.loads(node.metadata.decode("utf-8"))
            return {
                "id": node.id,
                "vector": list(node.vector),
                "metadata": metadata,
            }
        except grpc.RpcError as e:
            if e.code() == grpc.StatusCode.NOT_FOUND:  # ty:ignore[unresolved-attribute]
                return None
            raise RiceDBError(f"Get failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def delete(self, node_id: int) -> bool:
        """Delete a document by ID."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.DeleteNodeRequest(node_id=node_id)  # ty:ignore[unresolved-attribute]
            response = self.stub.DeleteNode(request, metadata=self._metadata())
            return response.success
        except grpc.RpcError as e:
            raise RiceDBError(f"Delete failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def grant_permission(
        self, node_id: int, target_user_id: int, permissions: Dict[str, bool]
    ) -> bool:  # ty:ignore[invalid-method-override]
        """Grant permissions to a user for a node."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            perms = ricedb_pb2.Permissions(  # ty:ignore[unresolved-attribute]
                read=permissions.get("read", False),
                write=permissions.get("write", False),
                delete=permissions.get("delete", False),
            )
            request = ricedb_pb2.GrantPermissionRequest(  # ty:ignore[unresolved-attribute]
                node_id=node_id, target_user_id=target_user_id, permissions=perms
            )
            response = self.stub.GrantPermission(request, metadata=self._metadata())
            return response.success
        except grpc.RpcError as e:
            raise RiceDBError(f"Grant permission failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def revoke_permission(self, node_id: int, target_user_id: int) -> bool:  # ty:ignore[invalid-method-override]
        """Revoke all permissions for a user on a node."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.RevokePermissionRequest(  # ty:ignore[unresolved-attribute]
                node_id=node_id, target_user_id=target_user_id
            )
            response = self.stub.RevokePermission(request, metadata=self._metadata())
            return response.success
        except grpc.RpcError as e:
            raise RiceDBError(f"Revoke permission failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def add_edge(self, from_node: int, to_node: int, relation: str, weight: float = 1.0) -> bool:
        """Add an edge between two nodes."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            # "from" is a reserved keyword, so we use kwargs
            kwargs = {"from": from_node, "to": to_node, "relation": relation, "weight": weight}
            request = ricedb_pb2.AddEdgeRequest(**kwargs)  # ty:ignore[unresolved-attribute]
            response = self.stub.AddEdge(request, metadata=self._metadata())
            return response.success
        except grpc.RpcError as e:
            raise RiceDBError(f"Add edge failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def get_neighbors(self, node_id: int, relation: Optional[str] = None) -> List[int]:
        """Get neighbors of a node."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.GetNeighborsRequest(node_id=node_id, relation=relation)  # ty:ignore[unresolved-attribute]
            response = self.stub.GetNeighbors(request, metadata=self._metadata())
            return list(response.neighbors)
        except grpc.RpcError as e:
            raise RiceDBError(f"Get neighbors failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def traverse(self, start_node: int, max_depth: int = 1) -> List[int]:
        """Traverse the graph from a start node."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.TraverseGraphRequest(start=start_node, max_depth=max_depth)  # ty:ignore[unresolved-attribute]
            response = self.stub.TraverseGraph(request, metadata=self._metadata())
            return list(response.visited)
        except grpc.RpcError as e:
            raise RiceDBError(f"Traverse failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def subscribe(
        self,
        filter_type: str = "all",
        node_id: Optional[int] = None,
        vector: Optional[List[float]] = None,
        threshold: float = 0.8,
    ) -> Iterator[Dict[str, Any]]:
        """Subscribe to real-time events."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.SubscribeRequest(  # ty:ignore[unresolved-attribute]
                filter_type=filter_type, node_id=node_id, vector=vector, threshold=threshold
            )

            for event in self.stub.Subscribe(request, metadata=self._metadata()):
                result = {"type": event.type, "node_id": event.node_id}
                if event.HasField("node"):
                    metadata = json.loads(event.node.metadata.decode("utf-8"))
                    result["node"] = {
                        "id": event.node.id,
                        "vector": list(event.node.vector),
                        "metadata": metadata,
                    }
                yield result
        except grpc.RpcError as e:
            raise RiceDBError(f"Subscribe failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def insert_with_acl(
        self,
        node_id: int,
        vector: List[float],
        metadata: Dict[str, Any],
        user_permissions: List[tuple],
    ) -> Dict[str, Any]:
        """Insert a document with multiple user permissions.

        Note: Multi-user ACL operations are not yet supported in gRPC transport.
        Please use HTTP transport for ACL operations.
        """
        # Fall back to standard insert with primary user
        if user_permissions:
            primary_user_id = user_permissions[0][0]
            return self.insert(node_id, vector, metadata, primary_user_id)

        return self.insert(node_id, vector, metadata)

    def batch_grant(self, grants: List[tuple]) -> Dict[str, Any]:
        """Grant permissions to multiple users/nodes in batch.

        Args:
            grants: List of tuples (node_id, user_id, permissions_dict)

        Returns:
            Batch grant response
        """
        # TODO: Implement batch grant in gRPC proto
        # For now, loop through grants
        results = []
        for node_id, user_id, permissions in grants:
            try:
                success = self.grant_permission(node_id, user_id, permissions)
                results.append({"node_id": node_id, "user_id": user_id, "success": success})
            except Exception as e:
                results.append(
                    {"node_id": node_id, "user_id": user_id, "success": False, "error": str(e)}
                )

        return {"results": results, "count": len(results)}

    def check_permission(self, node_id: int, user_id: int, permission_type: str) -> bool:
        """Check if a user has a specific permission on a node.

        Args:
            node_id: Node ID to check permissions for
            user_id: User ID to check permissions for
            permission_type: Type of permission to check ("read", "write", "delete")

        Returns:
            True if user has permission, False otherwise
        """
        # Currently not supported in gRPC protocol, would require server update
        # raise RiceDBError("check_permission is not currently supported via gRPC transport")
        print(f"Warning: check_permission not supported in gRPC, assuming False for {node_id}")
        return False

    def add_memory(
        self,
        session_id: str,
        agent_id: str,
        content: str,
        metadata: Optional[Dict[str, str]] = None,
        ttl_seconds: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Add to agent memory."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.AddMemoryRequest(  # ty:ignore[unresolved-attribute]
                session_id=session_id,
                agent_id=agent_id,
                content=content,
                metadata=metadata or {},
                ttl_seconds=ttl_seconds,
            )
            response = self.stub.AddMemory(request, metadata=self._metadata())

            entry = {
                "id": response.entry.id,
                "session_id": response.entry.session_id,
                "agent_id": response.entry.agent_id,
                "content": response.entry.content,
                "timestamp": response.entry.timestamp,
                "metadata": dict(response.entry.metadata),
                "expires_at": response.entry.expires_at
                if response.entry.HasField("expires_at")
                else None,
            }

            return {
                "success": response.success,
                "message": response.message,
                "entry": entry,
            }
        except grpc.RpcError as e:
            raise RiceDBError(f"Add memory failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def get_memory(
        self,
        session_id: str,
        limit: int = 50,
        after: Optional[int] = None,
        filter: Optional[Dict[str, str]] = None,
    ) -> List[Dict[str, Any]]:
        """Get agent memory."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.GetMemoryRequest(  # ty:ignore[unresolved-attribute]
                session_id=session_id,
                limit=limit,
                after_timestamp=after or 0,
                filter=filter or {},
            )
            response = self.stub.GetMemory(request, metadata=self._metadata())

            results = []
            for entry in response.entries:
                item = {
                    "id": entry.id,
                    "session_id": entry.session_id,
                    "agent_id": entry.agent_id,
                    "content": entry.content,
                    "timestamp": entry.timestamp,
                    "metadata": dict(entry.metadata),
                }
                if entry.HasField("expires_at"):
                    item["expires_at"] = entry.expires_at
                results.append(item)
            return results
        except grpc.RpcError as e:
            raise RiceDBError(f"Get memory failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def clear_memory(self, session_id: str) -> Dict[str, Any]:
        """Clear agent memory."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.ClearMemoryRequest(session_id=session_id)  # ty:ignore[unresolved-attribute]
            response = self.stub.ClearMemory(request, metadata=self._metadata())
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            raise RiceDBError(f"Clear memory failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904

    def watch_memory(self, session_id: str):
        """Watch for new memory events in a session."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.WatchMemoryRequest(session_id=session_id)  # ty:ignore[unresolved-attribute]

            for event in self.stub.WatchMemory(request, metadata=self._metadata()):
                entry = event.entry
                yield {
                    "type": event.type,
                    "entry": {
                        "id": entry.id,
                        "session_id": entry.session_id,
                        "agent_id": entry.agent_id,
                        "content": entry.content,
                        "timestamp": entry.timestamp,
                        "metadata": dict(entry.metadata),
                    },
                }
        except grpc.RpcError as e:
            raise RiceDBError(f"Watch memory failed: {e.details()}")  # ty:ignore[unresolved-attribute]  # noqa: B904
