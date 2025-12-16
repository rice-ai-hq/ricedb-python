"""Tests for Unified RiceDB client."""

from unittest.mock import MagicMock, patch

import pytest

from ricedb.client.unified_client import RiceDBClient
from ricedb.exceptions import ConnectionError, RiceDBError


class MockGrpc:
    """Mock gRPC client class."""

    def __init__(self, *args, **kwargs):
        self._connected = False
        self.port = 50051
        self.args = args
        self.kwargs = kwargs

    def connect(self):
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def insert(self, *args, **kwargs):
        pass

    def search(self, *args, **kwargs):
        pass

    def stream_search(self, *args, **kwargs):
        pass

    def health(self):
        return {}

    def batch_insert(self, *args, **kwargs):
        return {}

    def write_memory(self, *args, **kwargs):
        return {}

    def read_memory(self, *args, **kwargs):
        return {}


class MockHttp:
    """Mock HTTP client class."""

    def __init__(self, *args, **kwargs):
        self._connected = False
        self.port = 3000
        self.args = args
        self.kwargs = kwargs

    def connect(self):
        self._connected = True
        return True

    def disconnect(self):
        self._connected = False

    def insert(self, *args, **kwargs):
        pass

    def search(self, *args, **kwargs):
        pass

    def grant_permission(self, *args, **kwargs):
        pass

    def revoke_permission(self, *args, **kwargs):
        pass

    def check_permission(self, *args, **kwargs):
        pass

    def batch_grant(self, *args, **kwargs):
        return {}

    def insert_with_acl(self, *args, **kwargs):
        return {}

    def health(self):
        return {}

    def batch_insert(self, *args, **kwargs):
        return {}

    def write_memory(self, *args, **kwargs):
        return {}

    def read_memory(self, *args, **kwargs):
        return {}


class TestRiceDBClient:
    """Test RiceDBClient class."""

    def test_init_default(self):
        """Test default initialization."""
        client = RiceDBClient()
        assert client.transport_type == "auto"
        assert client.http_port == 3000
        assert client.grpc_port == 50051

    def test_init_invalid_transport(self):
        """Test initialization with invalid transport."""
        with pytest.raises(ValueError, match="Invalid transport type"):
            RiceDBClient(transport="invalid")

    def test_connect_auto_grpc_success(self):
        """Test auto connect selects gRPC when available."""
        with (
            patch("ricedb.client.unified_client.GrpcRiceDBClient", new=MockGrpc),
            patch("ricedb.client.unified_client.HTTPRiceDBClient", new=MockHttp),
        ):
            client = RiceDBClient(transport="auto")
            assert client.connect() is True
            assert isinstance(client._client, MockGrpc)

    def test_connect_auto_fallback(self):
        """Test auto connect falls back to HTTP."""

        # Create a MockGrpc that fails
        class FailingGrpc(MockGrpc):
            def connect(self):
                raise ConnectionError("Fail")

        with (
            patch("ricedb.client.unified_client.GrpcRiceDBClient", new=FailingGrpc),
            patch("ricedb.client.unified_client.HTTPRiceDBClient", new=MockHttp),
        ):
            client = RiceDBClient(transport="auto")
            assert client.connect() is True
            assert isinstance(client._client, MockHttp)

    def test_connect_grpc_only(self):
        """Test connect with explicit gRPC transport."""
        with patch("ricedb.client.unified_client.GrpcRiceDBClient", new=MockGrpc):
            client = RiceDBClient(transport="grpc")
            assert client.connect() is True
            assert isinstance(client._client, MockGrpc)

    def test_connect_http_only(self):
        """Test connect with explicit HTTP transport."""
        with patch("ricedb.client.unified_client.HTTPRiceDBClient", new=MockHttp):
            client = RiceDBClient(transport="http")
            assert client.connect() is True
            assert isinstance(client._client, MockHttp)

    def test_stream_search_grpc(self):
        """Test stream_search works with gRPC."""
        with patch("ricedb.client.unified_client.GrpcRiceDBClient", new=MockGrpc):
            client = RiceDBClient(transport="grpc")
            client.connect()

            client._client.stream_search = MagicMock()
            client.stream_search([1.0], 1)
            client._client.stream_search.assert_called_once()

    def test_stream_search_http_fail(self):
        """Test stream_search fails with HTTP."""
        with patch("ricedb.client.unified_client.HTTPRiceDBClient", new=MockHttp):
            client = RiceDBClient(transport="http")
            client.connect()

            with pytest.raises(RiceDBError, match="Stream search is only available"):
                client.stream_search([1.0], 1)

    def test_get_transport_info_grpc(self):
        """Test transport info for gRPC."""
        with patch("ricedb.client.unified_client.GrpcRiceDBClient", new=MockGrpc):
            client = RiceDBClient(transport="grpc")
            client.connect()

            info = client.get_transport_info()
            assert info["type"] == "grpc"
            assert info["acl_support"] is False

    def test_get_transport_info_http(self):
        """Test transport info for HTTP."""
        with patch("ricedb.client.unified_client.HTTPRiceDBClient", new=MockHttp):
            client = RiceDBClient(transport="http")
            client.connect()

            info = client.get_transport_info()
            assert info["type"] == "http"
            assert info["acl_support"] is True

    def test_insert_delegation(self):
        """Test delegation of insert method."""
        with patch("ricedb.client.unified_client.GrpcRiceDBClient", new=MockGrpc):
            client = RiceDBClient(transport="grpc")
            client.connect()

            client._client.insert = MagicMock()
            client.insert(1, [1.0], {})
            client._client.insert.assert_called_once()
