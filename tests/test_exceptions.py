"""Tests for RiceDB exceptions."""

import pytest

from ricedb.exceptions import (
    AuthenticationError,
    ConnectionError,
    InsertError,
    RiceDBError,
    SearchError,
    TransportError,
    ValidationError,
)


class TestExceptions:
    """Test exception classes."""

    def test_base_exception(self):
        """Test base RiceDBError exception."""
        with pytest.raises(RiceDBError):
            raise RiceDBError("Test error")

        error = RiceDBError("Test message")
        assert str(error) == "Test message"

    def test_connection_error(self):
        """Test ConnectionError exception."""
        with pytest.raises(ConnectionError):
            raise ConnectionError("Connection failed")

        with pytest.raises(RiceDBError):  # Should inherit from RiceDBError
            raise ConnectionError("Connection failed")

        error = ConnectionError("Cannot connect to server")
        assert str(error) == "Cannot connect to server"

    def test_insert_error(self):
        """Test InsertError exception."""
        with pytest.raises(InsertError):
            raise InsertError("Insert failed")

        with pytest.raises(RiceDBError):  # Should inherit from RiceDBError
            raise InsertError("Insert failed")

        error = InsertError("Document insertion failed")
        assert str(error) == "Document insertion failed"

    def test_search_error(self):
        """Test SearchError exception."""
        with pytest.raises(SearchError):
            raise SearchError("Search failed")

        with pytest.raises(RiceDBError):  # Should inherit from RiceDBError
            raise SearchError("Search failed")

        error = SearchError("Search query invalid")
        assert str(error) == "Search query invalid"

    def test_authentication_error(self):
        """Test AuthenticationError exception."""
        with pytest.raises(AuthenticationError):
            raise AuthenticationError("Auth failed")

        with pytest.raises(RiceDBError):  # Should inherit from RiceDBError
            raise AuthenticationError("Auth failed")

        error = AuthenticationError("Invalid credentials")
        assert str(error) == "Invalid credentials"

    def test_validation_error(self):
        """Test ValidationError exception."""
        with pytest.raises(ValidationError):
            raise ValidationError("Validation failed")

        with pytest.raises(RiceDBError):  # Should inherit from RiceDBError
            raise ValidationError("Validation failed")

        error = ValidationError("Invalid input")
        assert str(error) == "Invalid input"

    def test_transport_error(self):
        """Test TransportError exception."""
        with pytest.raises(TransportError):
            raise TransportError("Transport failed")

        with pytest.raises(RiceDBError):  # Should inherit from RiceDBError
            raise TransportError("Transport failed")

        error = TransportError("gRPC error")
        assert str(error) == "gRPC error"

    def test_exception_chaining(self):
        """Test exception chaining."""
        try:
            try:
                raise ValueError("Original error")
            except ValueError as e:
                raise ConnectionError("Connection failed") from e
        except ConnectionError as conn_error:
            assert str(conn_error) == "Connection failed"
            assert conn_error.__cause__ is not None
            assert str(conn_error.__cause__) == "Original error"
