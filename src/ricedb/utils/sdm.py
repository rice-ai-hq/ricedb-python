"""
Sparse Distributed Memory (SDM) utilities.
"""

from typing import List, Union
import random

ADDRESS_SIZE_U64 = 16
ADDRESS_SIZE_BITS = ADDRESS_SIZE_U64 * 64

class BitVector:
    """A 1024-bit vector used for SDM addresses and data."""

    def __init__(self, chunks: Union[List[int], None] = None):
        """Initialize BitVector.

        Args:
            chunks: List of 16 unsigned 64-bit integers. If None, initializes to zeros.
        """
        if chunks is None:
            self.chunks = [0] * ADDRESS_SIZE_U64
        else:
            if len(chunks) != ADDRESS_SIZE_U64:
                raise ValueError(f"BitVector must have {ADDRESS_SIZE_U64} chunks")
            self.chunks = list(chunks)

    @classmethod
    def random(cls) -> 'BitVector':
        """Create a random BitVector."""
        chunks = [random.getrandbits(64) for _ in range(ADDRESS_SIZE_U64)]
        return cls(chunks)

    def to_list(self) -> List[int]:
        """Convert to list of u64 chunks."""
        return self.chunks

    def hamming_distance(self, other: 'BitVector') -> int:
        """Calculate Hamming distance to another BitVector."""
        distance = 0
        for i in range(ADDRESS_SIZE_U64):
            # XOR and count set bits
            xor_val = self.chunks[i] ^ other.chunks[i]
            distance += xor_val.bit_count()
        return distance

    def __eq__(self, other):
        if not isinstance(other, BitVector):
            return False
        return self.chunks == other.chunks

    def __repr__(self):
        return f"BitVector(chunks={self.chunks})"
