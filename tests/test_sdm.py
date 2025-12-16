"""Tests for SDM utilities."""

import pytest

from ricedb.utils.sdm import ADDRESS_SIZE_BITS, ADDRESS_SIZE_U64, BitVector


class TestBitVector:
    """Test BitVector class."""

    def test_init_default(self):
        """Test default initialization."""
        bv = BitVector()
        assert len(bv.chunks) == ADDRESS_SIZE_U64
        assert all(c == 0 for c in bv.chunks)

    def test_init_with_chunks(self):
        """Test initialization with chunks."""
        chunks = [1] * ADDRESS_SIZE_U64
        bv = BitVector(chunks)
        assert bv.chunks == chunks

    def test_init_invalid_chunks(self):
        """Test initialization with invalid chunks."""
        with pytest.raises(ValueError, match=f"BitVector must have {ADDRESS_SIZE_U64} chunks"):
            BitVector([1])

    def test_random(self):
        """Test random BitVector creation."""
        bv1 = BitVector.random()
        bv2 = BitVector.random()

        assert len(bv1.chunks) == ADDRESS_SIZE_U64
        assert len(bv2.chunks) == ADDRESS_SIZE_U64
        assert bv1 != bv2  # Extremely unlikely to be equal

    def test_to_list(self):
        """Test conversion to list."""
        chunks = [i for i in range(ADDRESS_SIZE_U64)]
        bv = BitVector(chunks)
        assert bv.to_list() == chunks

    def test_hamming_distance_zero(self):
        """Test Hamming distance for identical vectors."""
        bv = BitVector.random()
        assert bv.hamming_distance(bv) == 0

    def test_hamming_distance_max(self):
        """Test Hamming distance for opposite vectors."""
        # Create vector of all zeros
        bv1 = BitVector([0] * ADDRESS_SIZE_U64)

        # Create vector of all ones (2^64 - 1)
        all_ones = (1 << 64) - 1
        bv2 = BitVector([all_ones] * ADDRESS_SIZE_U64)

        assert bv1.hamming_distance(bv2) == ADDRESS_SIZE_BITS

    def test_hamming_distance_known(self):
        """Test Hamming distance with known values."""
        # Chunk 0 has 1 bit difference
        chunks1 = [0] * ADDRESS_SIZE_U64
        chunks2 = [0] * ADDRESS_SIZE_U64

        chunks1[0] = 0b101  # 5
        chunks2[0] = 0b001  # 1
        # Difference is 0b100 (4), which has 1 bit set

        bv1 = BitVector(chunks1)
        bv2 = BitVector(chunks2)

        assert bv1.hamming_distance(bv2) == 1

    def test_equality(self):
        """Test equality operator."""
        bv1 = BitVector([1] * ADDRESS_SIZE_U64)
        bv2 = BitVector([1] * ADDRESS_SIZE_U64)
        bv3 = BitVector([2] * ADDRESS_SIZE_U64)

        assert bv1 == bv2
        assert bv1 != bv3
        assert bv1 != "not a bitvector"

    def test_repr(self):
        """Test string representation."""
        bv = BitVector([0] * ADDRESS_SIZE_U64)
        assert str(bv) == f"BitVector(chunks={[0] * ADDRESS_SIZE_U64})"
