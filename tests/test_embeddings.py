"""Tests for embedding generators."""

import pytest
import numpy as np
from ricedb.utils.embeddings import (
    DummyEmbeddingGenerator,
    SentenceTransformersEmbeddingGenerator,
    OpenAIEmbeddingGenerator,
    HuggingFaceEmbeddingGenerator
)


class TestDummyEmbeddingGenerator:
    """Test the DummyEmbeddingGenerator class."""

    def test_init(self):
        """Test initialization."""
        gen = DummyEmbeddingGenerator(dimensions=128, seed=42)
        assert gen.dimensions == 128
        assert gen.seed == 42

    def test_encode(self):
        """Test single text encoding."""
        gen = DummyEmbeddingGenerator(dimensions=384, seed=0.5)
        text = "Hello world"
        embedding = gen.encode(text)

        assert isinstance(embedding, list)
        assert len(embedding) == 384
        assert all(isinstance(x, float) for x in embedding)

        # Test reproducibility
        embedding2 = gen.encode(text)
        assert embedding == embedding2

        # Test normalization
        embedding_np = np.array(embedding)
        norm = np.linalg.norm(embedding_np)
        assert abs(norm - 1.0) < 1e-6

    def test_encode_different_texts(self):
        """Test encoding different texts produces different embeddings."""
        gen = DummyEmbeddingGenerator(dimensions=384, seed=0.5)
        text1 = "Hello world"
        text2 = "Goodbye world"

        embedding1 = gen.encode(text1)
        embedding2 = gen.encode(text2)

        assert embedding1 != embedding2

    def test_encode_batch(self):
        """Test batch encoding."""
        gen = DummyEmbeddingGenerator(dimensions=384, seed=0.5)
        texts = ["Hello", "world", "test"]

        embeddings = gen.encode_batch(texts)

        assert isinstance(embeddings, list)
        assert len(embeddings) == 3
        assert all(len(emb) == 384 for emb in embeddings)

        # Should match individual encodings
        for i, text in enumerate(texts):
            assert embeddings[i] == gen.encode(text)


class TestEmbeddingGeneratorsOptional:
    """Test optional embedding generators (only run if dependencies are available)."""

    def test_sentence_transformers_import(self):
        """Test SentenceTransformers embedding generator if available."""
        try:
            gen = SentenceTransformersEmbeddingGenerator(
                model_name="all-MiniLM-L6-v2"
            )
            embedding = gen.encode("test")
            assert isinstance(embedding, list)
            assert len(embedding) > 0
        except ImportError:
            pytest.skip("sentence-transformers not installed")

    def test_openai_import(self):
        """Test OpenAI embedding generator if available."""
        try:
            gen = OpenAIEmbeddingGenerator(
                model="text-embedding-ada-002",
                api_key="dummy-key"  # Will fail but tests import
            )
            assert gen.model == "text-embedding-ada-002"
        except ImportError:
            pytest.skip("openai not installed")

    def test_huggingface_import(self):
        """Test HuggingFace embedding generator if available."""
        try:
            gen = HuggingFaceEmbeddingGenerator(
                model_name="sentence-transformers/all-MiniLM-L6-v2"
            )
            assert gen.model_name == "sentence-transformers/all-MiniLM-L6-v2"
        except ImportError:
            pytest.skip("transformers not installed")