"""Tests for user fetching methods in HTTP client."""

from unittest.mock import MagicMock, patch
import pytest
from ricedb.client.http_client import HTTPRiceDBClient
from ricedb.exceptions import AuthenticationError


class TestUserMethods:
    """Test user fetching methods."""

    @pytest.fixture
    def client(self):
        """Create a client instance for testing."""
        return HTTPRiceDBClient(host="localhost", port=3000)

    @pytest.fixture
    def mock_session(self, client):
        """Mock the requests session."""
        with patch.object(client, "session", autospec=True) as mock:
            yield mock

    def test_get_user(self, client, mock_session):
        """Test getting a user."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"username": "testuser", "user_id": 123, "role": "user"}
        mock_session.get.return_value = mock_response

        user = client.get_user("testuser")
        assert user["username"] == "testuser"
        assert user["user_id"] == 123

        mock_session.get.assert_called_with("http://localhost:3000/auth/users/testuser", timeout=30)

    def test_list_users(self, client, mock_session):
        """Test listing users."""
        mock_response = MagicMock()
        mock_response.json.return_value = [
            {"username": "admin", "user_id": 1, "role": "admin"},
            {"username": "user", "user_id": 2, "role": "user"},
        ]
        mock_session.get.return_value = mock_response

        users = client.list_users()
        assert len(users) == 2
        assert users[0]["username"] == "admin"

        mock_session.get.assert_called_with("http://localhost:3000/auth/users", timeout=30)
