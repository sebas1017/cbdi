"""
Error injection utilities for testing and simulation.
"""

import numpy as np
from numpy.typing import NDArray


def inject_transposition(matrix: NDArray, row: int, col: int) -> NDArray:
    """Inject an adjacent transposition error.

    Swaps entries at positions (row, col) and (row, col+1).

    Args:
        matrix: The original m×n matrix.
        row: Row index (0-based).
        col: Column index (0-based). Must be < n-1.

    Returns:
        A new matrix with the swap applied.

    Example:
        >>> M = np.array([[1,2,3],[3,1,2],[2,3,1]])
        >>> inject_transposition(M, row=0, col=1)
        array([[1, 3, 2],
               [3, 1, 2],
               [2, 3, 1]])
    """
    if col >= matrix.shape[1] - 1:
        raise ValueError(f"col must be < {matrix.shape[1] - 1}, got {col}")

    out = matrix.copy()
    out[row, col], out[row, col + 1] = out[row, col + 1], out[row, col]
    return out


def inject_corruption(matrix: NDArray, row: int, col: int, new_value: int) -> NDArray:
    """Inject an entry corruption error.

    Changes the entry at (row, col) to new_value.

    Args:
        matrix: The original m×n matrix.
        row: Row index.
        col: Column index.
        new_value: The corrupted value.

    Returns:
        A new matrix with the corruption applied.

    Example:
        >>> M = np.array([[1,2,3],[3,1,2],[2,3,1]])
        >>> inject_corruption(M, row=1, col=2, new_value=5)
        array([[1, 2, 3],
               [3, 1, 5],
               [2, 3, 1]])
    """
    out = matrix.copy()
    out[row, col] = new_value
    return out


def inject_random_transposition(matrix: NDArray, rng: np.random.Generator | None = None) -> tuple[NDArray, int, int]:
    """Inject a random adjacent transposition.

    Args:
        matrix: The original m×n matrix.
        rng: Optional random generator.

    Returns:
        Tuple of (corrupted_matrix, error_row, error_col).
    """
    if rng is None:
        rng = np.random.default_rng()

    m, n = matrix.shape
    row = rng.integers(0, m)
    col = rng.integers(0, n - 1)
    return inject_transposition(matrix, row, col), row, col
