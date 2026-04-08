"""
Construction of column-balanced permutation matrices.
"""

import numpy as np
from numpy.typing import NDArray


def latin_square(n: int) -> NDArray:
    """Generate an n×n cyclic Latin square over {1, ..., n}.

    Each row is a cyclic shift of [1, 2, ..., n].
    This is always column-balanced (each column sums to n(n+1)/2).

    Args:
        n: Size of the Latin square.

    Returns:
        n×n numpy array.

    Example:
        >>> latin_square(4)
        array([[1, 2, 3, 4],
               [4, 1, 2, 3],
               [3, 4, 1, 2],
               [2, 3, 4, 1]])
    """
    S = np.arange(1, n + 1)
    return np.array([np.roll(S, i) for i in range(n)])


def column_balanced_matrix(m: int, n: int, values: NDArray | list | None = None) -> NDArray:
    """Generate an m×n column-balanced matrix.

    Each row is a permutation of the value set. Column balance is achieved
    by using complete blocks of cyclic Latin squares.

    Args:
        m: Number of rows (will be rounded up to nearest multiple of n).
        n: Number of columns.
        values: Optional array of n distinct values. Defaults to {1,...,n}.

    Returns:
        m_actual×n numpy array (m_actual >= m, multiple of n).

    Example:
        >>> M = column_balanced_matrix(12, 4)
        >>> M.shape
        (12, 4)
        >>> all(M.sum(axis=0) == M.sum(axis=0)[0])
        True

        >>> M = column_balanced_matrix(6, 3, values=[1, 6, 24])
        >>> M.sum(axis=0)
        array([62, 62, 62])
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


def parity_row(data_rows: NDArray, values: NDArray | list | None = None) -> NDArray | None:
    """Compute a parity row that makes the matrix column-balanced.

    Given (m-1) rows, find a permutation of the value set such that
    appending it as the m-th row makes all column sums equal.

    Args:
        data_rows: (m-1)×n matrix of permutation rows.
        values: The value set. Defaults to {1,...,n}.

    Returns:
        Array of n values (the parity row), or None if no valid
        parity permutation exists.

    Example:
        >>> data = np.array([[1, 3, 2], [3, 2, 1]])
        >>> parity_row(data)
        array([2, 1, 3])
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
        return None  # Column balance impossible with these parameters

    current_col_sums = data_rows.sum(axis=0)
    needed = target_col_sum - current_col_sums

    # Check if 'needed' is a permutation of S
    if sorted(needed) == sorted(S):
        return needed.astype(S.dtype)

    return None
