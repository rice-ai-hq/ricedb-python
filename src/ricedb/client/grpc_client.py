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

    def connect(self) -> bool:
        """Connect to the RiceDB server.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            self.channel = grpc.insecure_channel(self.address, options=self.options)
            self.stub = ricedb_pb2_grpc.RiceDBStub(self.channel)

            # Test connection with health check
            self.stub.Health(ricedb_pb2.HealthRequest())
            self._connected = True
            return True
        except grpc.RpcError as e:
            raise ConnectionError(f"Failed to connect to RiceDB gRPC server: {e.details()}") from e

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
            response = self.stub.Health(ricedb_pb2.HealthRequest())
            return {"status": response.status, "version": response.version}
        except grpc.RpcError as e:
            raise ConnectionError(f"Health check failed: {e.details()}") from e

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
            request = ricedb_pb2.InsertRequest(
                id=node_id,
                vector=vector,
                metadata=json.dumps(metadata).encode("utf-8"),
                user_id=user_id,
            )
            response = self.stub.Insert(request)

            if not response.success:
                raise InsertError(response.message)

            return {
                "success": response.success,
                "node_id": response.node_id,
                "message": response.message,
            }
        except grpc.RpcError as e:
            raise InsertError(f"Insert request failed: {e.details()}") from e

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
            request = ricedb_pb2.SearchRequest(vector=vector, user_id=user_id, k=k)
            response = self.stub.Search(request)

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
            raise SearchError(f"Search request failed: {e.details()}") from e

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
                yield ricedb_pb2.InsertRequest(
                    id=doc["id"],
                    vector=doc["vector"],
                    metadata=json.dumps(doc["metadata"]).encode("utf-8"),
                    user_id=doc_user_id,
                )

        try:
            response = self.stub.BatchInsert(request_generator())
            return {"count": response.count, "node_ids": list(response.node_ids)}
        except grpc.RpcError as e:
            raise InsertError(f"Batch insert request failed: {e.details()}") from e

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
            request = ricedb_pb2.SearchRequest(vector=vector, user_id=user_id, k=k)

            for result in self.stub.StreamSearch(request):
                metadata = json.loads(result.metadata.decode("utf-8"))
                yield {
                    "id": result.id,
                    "similarity": result.similarity,
                    "metadata": metadata,
                }
        except grpc.RpcError as e:
            raise SearchError(f"Stream search request failed: {e.details()}") from e

    def write_memory(self, address: BitVector, data: BitVector, user_id: int = 1) -> Dict[str, Any]:
        """Write to SDM."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.WriteMemoryRequest(
                address=ricedb_pb2.BitVector(chunks=address.to_list()),
                data=ricedb_pb2.BitVector(chunks=data.to_list()),
                user_id=user_id,
            )
            response = self.stub.WriteMemory(request)
            return {"success": response.success, "message": response.message}
        except grpc.RpcError as e:
            raise RiceDBError(f"SDM write failed: {e.details()}") from e

    def read_memory(self, address: BitVector, user_id: int = 1) -> BitVector:
        """Read from SDM."""
        if not self.stub:
            raise ConnectionError("Not connected to server")

        try:
            request = ricedb_pb2.ReadMemoryRequest(
                address=ricedb_pb2.BitVector(chunks=address.to_list()), user_id=user_id
            )
            response = self.stub.ReadMemory(request)
            return BitVector(list(response.data.chunks))
        except grpc.RpcError as e:
            raise RiceDBError(f"SDM read failed: {e.details()}") from e

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

    def grant_permission(
        self, node_id: int, user_id: int, permissions: Dict[str, bool]
    ) -> Dict[str, Any]:
        """Grant permissions to a user for a node.

        Note: ACL operations are not yet supported in gRPC transport.
        Please use HTTP transport for ACL operations.
        """
        raise RiceDBError(
            "ACL operations are not supported in gRPC transport. "
            "Please use HTTP transport or add ACL support to protobuf definitions."
        )

    def revoke_permission(self, node_id: int, user_id: int) -> Dict[str, Any]:
        """Revoke all permissions for a user on a node.

        Note: ACL operations are not yet supported in gRPC transport.
        Please use HTTP transport for ACL operations.
        """
        raise RiceDBError(
            "ACL operations are not supported in gRPC transport. "
            "Please use HTTP transport or add ACL support to protobuf definitions."
        )

    def check_permission(self, node_id: int, user_id: int, permission_type: str) -> bool:
        """Check if a user has a specific permission on a node.

        Note: ACL operations are not yet supported in gRPC transport.
        Please use HTTP transport for ACL operations.
        """
        raise RiceDBError(
            "ACL operations are not supported in gRPC transport. "
            "Please use HTTP transport or add ACL support to protobuf definitions."
        )

    def batch_grant(self, grants: List[tuple]) -> Dict[str, Any]:
        """Grant permissions to multiple users/nodes in batch.

        Note: ACL operations are not yet supported in gRPC transport.
        Please use HTTP transport for ACL operations.
        """
        raise RiceDBError(
            "ACL operations are not supported in gRPC transport. "
            "Please use HTTP transport or add ACL support to protobuf definitions."
        )

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
