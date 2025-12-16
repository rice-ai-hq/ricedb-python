"""
Embedding generator utilities for RiceDB.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Union
import numpy as np


class EmbeddingGenerator(ABC):
    """Abstract base class for embedding generators."""

    @abstractmethod
    def encode(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector as list of floats
        """
        pass

    @abstractmethod
    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        pass


class DummyEmbeddingGenerator(EmbeddingGenerator):
    """Generates deterministic dummy embeddings for testing."""

    def __init__(self, dimensions: int = 384, seed: float = 0.5):
        """Initialize the dummy embedding generator.

        Args:
            dimensions: Embedding dimensions
            seed: Random seed for reproducibility
        """
        self.dimensions = dimensions
        self.seed = seed

    def encode(self, text: str) -> List[float]:
        """Generate deterministic dummy embedding based on text hash.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        # Use text hash for reproducible embeddings
        hash_val = hash(text) % 10000
        np.random.seed(int(hash_val))
        vector = np.random.randn(self.dimensions).astype(float)

        # Normalize the vector
        norm = np.linalg.norm(vector)
        if norm > 0:
            vector = vector / norm

        return vector.tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        return [self.encode(text) for text in texts]


class SentenceTransformersEmbeddingGenerator(EmbeddingGenerator):
    """Uses Sentence Transformers for high-quality text embeddings."""

    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        device: Optional[str] = None
    ):
        """Initialize the Sentence Transformers embedding generator.

        Args:
            model_name: Name of the Sentence Transformers model
            batch_size: Batch size for encoding multiple texts
            device: Device to run the model on (None for auto-detection)
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.device = device
        self._model = None

    @property
    def model(self):
        """Lazy loading of the sentence transformer model."""
        if self._model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._model = SentenceTransformer(self.model_name, device=self.device)
            except ImportError:
                raise ImportError(
                    "sentence-transformers package is required. "
                    "Install it with: pip install ricedb[embeddings]"
                )
        return self._model

    def encode(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        return self.model.encode(text).tolist()

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        return self.model.encode(
            texts,
            batch_size=self.batch_size,
            show_progress_bar=True
        ).tolist()


class OpenAIEmbeddingGenerator(EmbeddingGenerator):
    """Uses OpenAI's API for text embeddings."""

    def __init__(
        self,
        model: str = "text-embedding-ada-002",
        api_key: Optional[str] = None,
        batch_size: int = 100
    ):
        """Initialize the OpenAI embedding generator.

        Args:
            model: OpenAI embedding model name
            api_key: OpenAI API key (or set OPENAI_API_KEY env var)
            batch_size: Number of texts to process in each batch
        """
        self.model = model
        self.api_key = api_key
        self.batch_size = batch_size
        self._client = None

    @property
    def client(self):
        """Lazy loading of the OpenAI client."""
        if self._client is None:
            try:
                import openai
                self._client = openai.OpenAI(api_key=self.api_key)
            except ImportError:
                raise ImportError(
                    "openai package is required. "
                    "Install it with: pip install ricedb[openai]"
                )
        return self._client

    def encode(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        response = self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        embeddings = []
        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            embeddings.extend(batch_embeddings)
        return embeddings


class HuggingFaceEmbeddingGenerator(EmbeddingGenerator):
    """Uses Hugging Face Transformers for text embeddings."""

    def __init__(
        self,
        model_name: str = "sentence-transformers/all-MiniLM-L6-v2",
        device: Optional[str] = None,
        normalize: bool = True
    ):
        """Initialize the Hugging Face embedding generator.

        Args:
            model_name: Hugging Face model name
            device: Device to run the model on
            normalize: Whether to normalize embeddings
        """
        self.model_name = model_name
        self.device = device
        self.normalize = normalize
        self._tokenizer = None
        self._model = None

    @property
    def tokenizer(self):
        """Lazy loading of the tokenizer."""
        if self._tokenizer is None:
            try:
                from transformers import AutoTokenizer
                self._tokenizer = AutoTokenizer.from_pretrained(self.model_name)
            except ImportError:
                raise ImportError(
                    "transformers package is required. "
                    "Install it with: pip install transformers torch"
                )
        return self._tokenizer

    @property
    def model(self):
        """Lazy loading of the model."""
        if self._model is None:
            try:
                from transformers import AutoModel
                self._model = AutoModel.from_pretrained(self.model_name)
                if self.device:
                    self._model = self._model.to(self.device)
            except ImportError:
                raise ImportError(
                    "transformers package is required. "
                    "Install it with: pip install transformers torch"
                )
        return self._model

    def encode(self, text: str) -> List[float]:
        """Generate embedding for a single text.

        Args:
            text: Input text

        Returns:
            Embedding vector
        """
        return self.encode_batch([text])[0]

    def encode_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts.

        Args:
            texts: List of input texts

        Returns:
            List of embedding vectors
        """
        import torch

        # Tokenize texts
        encoded = self.tokenizer(
            texts,
            padding=True,
            truncation=True,
            return_tensors="pt"
        )
        if self.device:
            encoded = {k: v.to(self.device) for k, v in encoded.items()}

        # Get embeddings
        with torch.no_grad():
            outputs = self.model(**encoded)
            # Mean pooling
            embeddings = self._mean_pooling(
                outputs.last_hidden_state,
                encoded['attention_mask']
            )

        # Normalize if requested
        if self.normalize:
            embeddings = torch.nn.functional.normalize(embeddings, p=2, dim=1)

        return embeddings.cpu().numpy().tolist()

    def _mean_pooling(self, last_hidden_state, attention_mask):
        """Mean pooling of token embeddings."""
        import torch
        input_mask_expanded = attention_mask.unsqueeze(-1).expand(last_hidden_state.size()).float()
        return torch.sum(last_hidden_state * input_mask_expanded, 1) / torch.clamp(input_mask_expanded.sum(1), min=1e-9)