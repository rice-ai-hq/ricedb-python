"""
Embedding utilities for RiceDB.
"""

from typing import List, Optional, Union
import requests

try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None


class EmbeddingModel:
    """Wrapper for sentence-transformers models."""

    def __init__(self, model_name: str = "all-distilroberta-v1"):
        """Initialize the embedding model.

        Args:
            model_name: Name of the sentence-transformer model
        """
        if SentenceTransformer is None:
            raise ImportError(
                "sentence-transformers is not installed. "
                "Install with: pip install ricedb[embeddings]"
            )
        self.model = SentenceTransformer(model_name)

    def encode(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Encode text into embeddings.

        Args:
            text: Text string or list of strings

        Returns:
            Embedding vector (List[float]) or list of vectors
        """
        embeddings = self.model.encode(text)
        return embeddings.tolist()


class RemoteEmbeddingModel:
    """Client for remote embedding service."""

    def __init__(self, service_url: str = "http://localhost:8080"):
        """Initialize the remote embedding model.

        Args:
            service_url: Base URL of the embedding service
        """
        self.service_url = service_url.rstrip("/")

    def encode(self, text: Union[str, List[str]]) -> Union[List[float], List[List[float]]]:
        """Encode text using the remote service.

        Args:
            text: Text string or list of strings

        Returns:
            Embedding vector (List[float]) or list of vectors
        """
        url = f"{self.service_url}/encode"
        try:
            response = requests.post(url, json={"text": text})
            response.raise_for_status()
            result = response.json()
            return result["embedding"]
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to get embeddings from service: {e}")
