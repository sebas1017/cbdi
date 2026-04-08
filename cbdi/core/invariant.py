"""
Core CBDI computation functions.

The Column-Balanced Delta Invariant states:
    For any m×n matrix M,
    Δ_total = 0  ⟺  all columns have the same sum.
"""

import numpy as np
from numpy.typing import NDArray


def column_sums(matrix):
    """Sum each column of the matrix."""
    return matrix.sum(axis=0)


def total_delta(matrix):
    """Compute the CBDI syndrome: consecutive differences of column sums.

    Returns the zero vector iff the matrix is column-balanced.
    """
    return np.diff(column_sums(matrix))


def delta_vectors(matrix):
    """Row-wise consecutive differences.

    For row [a₁, a₂, ..., aₙ], returns [a₁-a₂, a₂-a₃, ..., aₙ₋₁-aₙ].
    """
    return matrix[:, :-1] - matrix[:, 1:]


def is_column_balanced(matrix):
    """True if all columns have the same sum."""
    cs = column_sums(matrix)
    return bool(np.all(cs == cs[0]))


def check(matrix):
    """Run the CBDI check. Returns (is_valid, syndrome).

    On a clean matrix the syndrome is all zeros.
    On a corrupted matrix the syndrome reveals the error location.
    """
    syndrome = total_delta(matrix)
    return bool(np.all(syndrome == 0)), syndrome
