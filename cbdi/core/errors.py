"""Error injection for testing and simulation."""

import numpy as np


def inject_transposition(matrix, row, col):
    """Swap adjacent entries at (row, col) and (row, col+1)."""
    if col >= matrix.shape[1] - 1:
        raise ValueError(f"col must be < {matrix.shape[1] - 1}, got {col}")

    out = matrix.copy()
    out[row, col], out[row, col + 1] = out[row, col + 1], out[row, col]
    return out


def inject_corruption(matrix, row, col, new_value):
    """Overwrite the entry at (row, col) with new_value."""
    out = matrix.copy()
    out[row, col] = new_value
    return out


def inject_random_transposition(matrix, rng=None):
    """Inject a random adjacent transposition. Returns (matrix, row, col)."""
    if rng is None:
        rng = np.random.default_rng()

    m, n = matrix.shape
    row = rng.integers(0, m)
    col = rng.integers(0, n - 1)
    return inject_transposition(matrix, row, col), row, col
