"""
Validation utilities for RiceDB client.
"""

from typing import Any, Dict, List, Optional

import numpy as np


def validate_vector(vector: List[float], dimensions: Optional[int] = None) -> None:
    """Validate a vector embedding.

    Args:
        vector: The vector to validate
        dimensions: Expected dimensions (optional)

    Raises:
        ValueError: If vector is invalid
    """
    if not isinstance(vector, list):
        raise ValueError("Vector must be a list of floats")

    if not vector:
        raise ValueError("Vector cannot be empty")

    if not all(isinstance(x, (int, float)) for x in vector):
        raise ValueError("Vector must contain only numeric values")

    if dimensions is not None and len(vector) != dimensions:
        raise ValueError(f"Vector must have exactly {dimensions} dimensions, got {len(vector)}")

    # Check for NaN or Inf values
    if any(np.isnan(x) or np.isinf(x) for x in vector):
        raise ValueError("Vector cannot contain NaN or Inf values")


def validate_metadata(metadata: Dict[str, Any]) -> None:
    """Validate metadata dictionary.

    Args:
        metadata: The metadata to validate

    Raises:
        ValueError: If metadata is invalid
    """
    if not isinstance(metadata, dict):
        raise ValueError("Metadata must be a dictionary")

    # Check for JSON-serializable values
    try:
        import json

        json.dumps(metadata)
    except (TypeError, ValueError) as e:
        raise ValueError(f"Metadata must be JSON-serializable: {e}") from e


def validate_node_id(node_id: int) -> None:
    """Validate node ID.

    Args:
        node_id: The node ID to validate

    Raises:
        ValueError: If node_id is invalid
    """
    if not isinstance(node_id, int):
        raise ValueError("Node ID must be an integer")

    if node_id < 0:
        raise ValueError("Node ID must be non-negative")


def validate_user_id(user_id: int) -> None:
    """Validate user ID.

    Args:
        user_id: The user ID to validate

    Raises:
        ValueError: If user_id is invalid
    """
    if not isinstance(user_id, int):
        raise ValueError("User ID must be an integer")

    if user_id < 0:
        raise ValueError("User ID must be non-negative")


def validate_search_params(k: int) -> None:
    """Validate search parameters.

    Args:
        k: Number of results to return

    Raises:
        ValueError: If parameters are invalid
    """
    if not isinstance(k, int):
        raise ValueError("k must be an integer")

    if k <= 0:
        raise ValueError("k must be positive")


def sanitize_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """Sanitize metadata dictionary.

    Args:
        metadata: The metadata to sanitize

    Returns:
        Sanitized metadata
    """
    # Convert any non-string keys to strings
    sanitized = {str(k): v for k, v in metadata.items()}

    # Remove None values
    sanitized = {k: v for k, v in sanitized.items() if v is not None}

    return sanitized
