"""Tests for validation utilities."""

import pytest
import numpy as np
from ricedb.utils.validation import (
    validate_vector,
    validate_metadata,
    validate_node_id,
    validate_user_id,
    validate_search_params,
    sanitize_metadata
)


class TestValidation:
    """Test validation functions."""

    def test_validate_vector_valid(self):
        """Test valid vector validation."""
        vector = [0.1, 0.2, 0.3, 0.4]
        validate_vector(vector)  # Should not raise

        validate_vector(vector, dimensions=4)  # Should not raise

    def test_validate_vector_invalid_type(self):
        """Test vector validation with invalid type."""
        with pytest.raises(ValueError, match="Vector must be a list"):
            validate_vector(np.array([0.1, 0.2, 0.3]))

    def test_validate_vector_empty(self):
        """Test vector validation with empty vector."""
        with pytest.raises(ValueError, match="Vector cannot be empty"):
            validate_vector([])

    def test_validate_vector_non_numeric(self):
        """Test vector validation with non-numeric values."""
        with pytest.raises(ValueError, match="Vector must contain only numeric"):
            validate_vector([0.1, "invalid", 0.3])

    def test_validate_vector_wrong_dimensions(self):
        """Test vector validation with wrong dimensions."""
        vector = [0.1, 0.2, 0.3]
        with pytest.raises(ValueError, match="Vector must have exactly 4 dimensions"):
            validate_vector(vector, dimensions=4)

    def test_validate_vector_nan_inf(self):
        """Test vector validation with NaN or Inf values."""
        with pytest.raises(ValueError, match="Vector cannot contain NaN or Inf"):
            validate_vector([0.1, np.nan, 0.3])

        with pytest.raises(ValueError, match="Vector cannot contain NaN or Inf"):
            validate_vector([0.1, np.inf, 0.3])

    def test_validate_metadata_valid(self):
        """Test valid metadata validation."""
        metadata = {"title": "Test", "count": 10, "active": True}
        validate_metadata(metadata)  # Should not raise

    def test_validate_metadata_invalid_type(self):
        """Test metadata validation with invalid type."""
        with pytest.raises(ValueError, match="Metadata must be a dictionary"):
            validate_metadata("invalid")

    def test_validate_metadata_non_serializable(self):
        """Test metadata validation with non-serializable values."""
        # Custom object
        class CustomObject:
            pass

        metadata = {"obj": CustomObject()}
        with pytest.raises(ValueError, match="Metadata must be JSON-serializable"):
            validate_metadata(metadata)

    def test_validate_node_id_valid(self):
        """Test valid node ID validation."""
        validate_node_id(1)  # Should not raise
        validate_node_id(0)  # Should not raise

    def test_validate_node_id_invalid(self):
        """Test node ID validation with invalid values."""
        with pytest.raises(ValueError, match="Node ID must be an integer"):
            validate_node_id("1")

        with pytest.raises(ValueError, match="Node ID must be non-negative"):
            validate_node_id(-1)

    def test_validate_user_id_valid(self):
        """Test valid user ID validation."""
        validate_user_id(100)  # Should not raise
        validate_user_id(0)  # Should not raise

    def test_validate_user_id_invalid(self):
        """Test user ID validation with invalid values."""
        with pytest.raises(ValueError, match="User ID must be an integer"):
            validate_user_id("100")

        with pytest.raises(ValueError, match="User ID must be non-negative"):
            validate_user_id(-1)

    def test_validate_search_params_valid(self):
        """Test valid search parameters validation."""
        validate_search_params(10)  # Should not raise
        validate_search_params(1)  # Should not raise

    def test_validate_search_params_invalid(self):
        """Test search parameters validation with invalid values."""
        with pytest.raises(ValueError, match="k must be an integer"):
            validate_search_params("10")

        with pytest.raises(ValueError, match="k must be positive"):
            validate_search_params(0)

        with pytest.raises(ValueError, match="k must be positive"):
            validate_search_params(-1)

    def test_sanitize_metadata(self):
        """Test metadata sanitization."""
        metadata = {
            "title": "Test",
            123: "numeric key",
            "description": None,
            "tags": ["tag1", "tag2"],
            "active": True
        }

        sanitized = sanitize_metadata(metadata)

        # Check non-string keys are converted
        assert "123" in sanitized
        assert isinstance(sanitized["123"], str)

        # Check None values are removed
        assert "description" not in sanitized

        # Check other values are preserved
        assert sanitized["title"] == "Test"
        assert sanitized["tags"] == ["tag1", "tag2"]
        assert sanitized["active"] is True