"""Tests for HTTP RiceDB client."""

from unittest.mock import MagicMock, patch

import pytest
import requests

from ricedb.client.http_client import HTTPRiceDBClient
from ricedb.exceptions import ConnectionError, InsertError, SearchError
from ricedb.utils.sdm import BitVector


class TestHTTPRiceDBClient:
    """Test HTTPRiceDBClient class."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return HTTPRiceDBClient(host="localhost", port=3000)

    @pytest.fixture
    def mock_session(self, client):
        """Mock the requests session."""
        with patch.object(client, "session", autospec=True) as mock:
            yield mock

    def test_init(self):
        """Test initialization."""
        client = HTTPRiceDBClient(host="test", port=1234, timeout=10)
        assert client.base_url == "http://test:1234"
        assert client.timeout == 10
        assert isinstance(client.session, requests.Session)

    def test_connect_success(self, client, mock_session):
        """Test successful connection."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_session.get.return_value = mock_response

        assert client.connect() is True
        mock_session.get.assert_called_with("http://localhost:3000/health", timeout=30)
        assert client._connected is True

    def test_connect_failure(self, client, mock_session):
        """Test connection failure."""
        mock_session.get.side_effect = requests.RequestException("Connection refused")

        with pytest.raises(ConnectionError, match="Failed to connect"):
            client.connect()
        assert client._connected is False

    def test_disconnect(self, client, mock_session):
        """Test disconnect."""
        client.disconnect()
        mock_session.close.assert_called_once()
        assert client._connected is False

    def test_health_success(self, client, mock_session):
        """Test successful health check."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok", "version": "0.1.0"}
        mock_session.get.return_value = mock_response

        result = client.health()
        assert result == {"status": "ok", "version": "0.1.0"}

    def test_health_failure(self, client, mock_session):
        """Test health check failure."""
        mock_session.get.side_effect = requests.RequestException("Error")

        with pytest.raises(ConnectionError, match="Health check failed"):
            client.health()

    def test_create_user(self, client, mock_session):
        """Test create user."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"user_id": 123}
        mock_session.post.return_value = mock_response

        user_id = client.create_user("user", "pass", role="user")
        assert user_id == 123

        mock_session.post.assert_called_with(
            "http://localhost:3000/auth/create_user",
            json={"username": "user", "password": "pass", "role": "user"},
            timeout=30,
        )

    def test_delete_user(self, client, mock_session):
        """Test delete user."""
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_session.delete.return_value = mock_response

        assert client.delete_user("user") is True

        mock_session.delete.assert_called_with(
            "http://localhost:3000/auth/delete_user",
            json={"username": "user"},
            timeout=30,
        )

    def test_insert_success(self, client, mock_session):
        """Test successful insertion."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "message": "Inserted"}
        mock_session.post.return_value = mock_response

        result = client.insert(1, "test text", {"key": "val"})
        assert result["success"] is True

        mock_session.post.assert_called_with(
            "http://localhost:3000/insert",
            json={
                "id": 1,
                "text": "test text",
                "metadata": {"key": "val"},
                "user_id": 1,
            },
            timeout=30,
        )

    def test_insert_failure_response(self, client, mock_session):
        """Test insertion with failure response from server."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": False, "message": "Error"}
        mock_session.post.return_value = mock_response

        with pytest.raises(InsertError, match="Error"):
            client.insert(1, "text", {})

    def test_insert_request_error(self, client, mock_session):
        """Test insertion with request error."""
        mock_session.post.side_effect = requests.RequestException("Network error")

        with pytest.raises(InsertError, match="Insert request failed"):
            client.insert(1, "text", {})

    def test_search_success(self, client, mock_session):
        """Test successful search."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": 1, "score": 0.9}]
        mock_session.post.return_value = mock_response

        result = client.search("query text", user_id=1, k=5)
        assert len(result) == 1
        assert result[0]["id"] == 1

        mock_session.post.assert_called_with(
            "http://localhost:3000/search",
            json={"query": "query text", "user_id": 1, "k": 5},
            timeout=30,
        )

    def test_search_failure(self, client, mock_session):
        """Test search failure."""
        mock_session.post.side_effect = requests.RequestException("Error")

        with pytest.raises(SearchError, match="Search request failed"):
            client.search("query", 1)

    def test_batch_insert(self, client, mock_session):
        """Test batch insert."""
        documents = [
            {"id": 1, "vector": [0.1], "metadata": {}},
            {"id": 2, "vector": [0.2], "metadata": {}},
        ]
        mock_response = MagicMock()
        mock_response.json.return_value = {"count": 2}
        mock_session.post.return_value = mock_response

        result = client.batch_insert(documents)
        assert result["count"] == 2

    def test_sdm_write(self, client, mock_session):
        """Test SDM write."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.post.return_value = mock_response

        addr = BitVector([0] * 16)
        data = BitVector([1] * 16)

        client.write_memory(addr, data)

        mock_session.post.assert_called()
        assert "sdm/write" in mock_session.post.call_args[0][0]

    def test_sdm_read(self, client, mock_session):
        """Test SDM read."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"data": [1] * 16}
        mock_session.post.return_value = mock_response

        addr = BitVector([0] * 16)
        result = client.read_memory(addr)

        assert isinstance(result, BitVector)
        assert result.chunks == [1] * 16

    def test_get_metadata(self, client, mock_session):
        """Test get metadata."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"key": "val"}
        mock_session.get.return_value = mock_response

        result = client.get_metadata(1)
        assert result == {"key": "val"}
        mock_session.get.assert_called_with("http://localhost:3000/node/1", timeout=30)

    def test_update_metadata(self, client, mock_session):
        """Test update metadata."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.put.return_value = mock_response

        client.update_metadata(1, {"new": "val"})
        mock_session.put.assert_called()
        assert "node/1" in mock_session.put.call_args[0][0]

    def test_delete_node(self, client, mock_session):
        """Test delete node."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.delete.return_value = mock_response

        client.delete_node(1)
        mock_session.delete.assert_called()
        assert "node/1" in mock_session.delete.call_args[0][0]

    def test_grant_permission(self, client, mock_session):
        """Test grant permission."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.post.return_value = mock_response

        perms = {"read": True}
        client.grant_permission(1, 100, perms)

        mock_session.post.assert_called_with(
            "http://localhost:3000/acl/grant",
            json={"node_id": 1, "user_id": 100, "permissions": perms},
            timeout=30,
        )

    def test_revoke_permission(self, client, mock_session):
        """Test revoke permission."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.post.return_value = mock_response

        client.revoke_permission(1, 100)

        mock_session.post.assert_called_with(
            "http://localhost:3000/acl/revoke", json={"node_id": 1, "user_id": 100}, timeout=30
        )

    def test_check_permission(self, client, mock_session):
        """Test check permission."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"allowed": True}
        mock_session.post.return_value = mock_response

        assert client.check_permission(1, 100, "read") is True

    def test_batch_grant(self, client, mock_session):
        """Test batch grant (client-side implementation)."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.post.return_value = mock_response

        grants = [(1, 100, {"read": True}), (2, 101, {"write": True})]

        result = client.batch_grant(grants)

        assert result["total"] == 2
        assert result["successful"] == 2
        assert mock_session.post.call_count == 2

    def test_insert_with_acl(self, client, mock_session):
        """Test insert with ACL."""
        # Mock insert response
        insert_response = MagicMock()
        insert_response.json.return_value = {"success": True, "node_id": 1}

        # Mock grant response
        grant_response = MagicMock()
        grant_response.json.return_value = {"success": True}

        # Configure side effects for sequential calls
        # First call is insert, subsequent calls are grants (via batch_grant)
        mock_session.post.side_effect = [insert_response, grant_response, grant_response]

        user_perms = [
            (1, {"owner": True}),  # Primary user
            (2, {"read": True}),  # Additional user
        ]

        result = client.insert_with_acl(1, [0.1], {}, user_perms)

        assert result["success"] is True
        assert "acl_grants" in result
        assert len(result["acl_users"]) == 2

    def test_insert_with_acl_no_users(self, client):
        """Test insert with ACL with empty user list."""
        with pytest.raises(ValueError, match="At least one user permission"):
            client.insert_with_acl(1, [0.1], {}, [])

    def test_create_session(self, client, mock_session):
        """Test create session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "session_id": "uuid"}
        mock_session.post.return_value = mock_response

        assert client.create_session() == "uuid"

        mock_session.post.assert_called_with(
            "http://localhost:3000/session/create",
            timeout=30,
        )

    def test_snapshot_session(self, client, mock_session):
        """Test snapshot session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.post.return_value = mock_response

        assert client.snapshot_session("sess1", "path") is True

        mock_session.post.assert_called_with(
            "http://localhost:3000/session/sess1/snapshot",
            json={"path": "path"},
            timeout=30,
        )

    def test_load_session(self, client, mock_session):
        """Test load session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "session_id": "uuid"}
        mock_session.post.return_value = mock_response

        assert client.load_session("path") == "uuid"

        mock_session.post.assert_called_with(
            "http://localhost:3000/session/load",
            json={"path": "path"},
            timeout=30,
        )

    def test_commit_session(self, client, mock_session):
        """Test commit session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.post.return_value = mock_response

        assert client.commit_session("sess1") is True

        mock_session.post.assert_called_with(
            "http://localhost:3000/session/sess1/commit",
            timeout=30,
        )

    def test_drop_session(self, client, mock_session):
        """Test drop session."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True}
        mock_session.delete.return_value = mock_response

        assert client.drop_session("sess1") is True

        mock_session.delete.assert_called_with(
            "http://localhost:3000/session/sess1/drop",
            timeout=30,
        )
