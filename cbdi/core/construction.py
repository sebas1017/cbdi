"""Construction of column-balanced permutation matrices."""

import numpy as np
from numpy.typing import NDArray


def latin_square(n):
    """Generate an n×n cyclic Latin square over {1, ..., n}.

    Each row is a cyclic shift, so every column sums to n(n+1)/2.
    """
    S = np.arange(1, n + 1)
    return np.array([np.roll(S, i) for i in range(n)])


def column_balanced_matrix(m, n, values=None):
    """Generate an m×n column-balanced matrix using cyclic Latin square blocks.

    If m is not a multiple of n, it gets rounded up to guarantee balance.
    Accepts an optional custom value set (must have length n).
    """
    if values is None:
        S = np.arange(1, n + 1)
    else:
        S = np.asarray(values)
        if len(S) != n:
            raise ValueError(f"values must have length {n}, got {len(S)}")

    m_adj = ((m + n - 1) // n) * n
    matrix = np.zeros((m_adj, n), dtype=S.dtype)
    for i in range(m_adj):
        matrix[i] = np.roll(S, i % n)
    return matrix[:m] if m % n == 0 else matrix


def parity_row(data_rows, values=None):
    """Find a permutation row that makes the full matrix column-balanced.

    Given (m-1) rows, returns a permutation of the value set such that
    appending it makes all column sums equal. Returns None if impossible.
    """
    m_minus_1, n = data_rows.shape

    if values is None:
        S = np.arange(1, n + 1)
    else:
        S = np.asarray(values)

    total_sum = S.sum()
    m = m_minus_1 + 1
    target_col_sum = m * total_sum // n

    if m * total_sum % n != 0:
        return None

    current_col_sums = data_rows.sum(axis=0)
    needed = target_col_sum - current_col_sums

    if sorted(needed) == sorted(S):
        return needed.astype(S.dtype)

    return None
