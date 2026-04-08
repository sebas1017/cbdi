"""
Core CBDI computation functions.

The Column-Balanced Delta Invariant states:
    For any m×n matrix M,
    Δ_total = 0  ⟺  all columns have the same sum.
"""

import numpy as np
from numpy.typing import NDArray


def column_sums(matrix: NDArray) -> NDArray:
    """Compute column sums of a matrix.

    Args:
        matrix: An m×n matrix (numpy array).

    Returns:
        Array of n column sums.

    Example:
        >>> column_sums(np.array([[1,2,3],[3,1,2],[2,3,1]]))
        array([6, 6, 6])
    """
    return matrix.sum(axis=0)


def total_delta(matrix: NDArray) -> NDArray:
    """Compute the total delta vector (CBDI syndrome).

    The j-th component equals C[j+1] - C[j] where C[j] is column j sum.
    For a column-balanced matrix, this is the zero vector.

    Args:
        matrix: An m×n matrix.

    Returns:
        Array of n-1 differences (the delta syndrome).

    Example:
        >>> total_delta(np.array([[1,2,3],[3,1,2],[2,3,1]]))
        array([0, 0])
    """
    return np.diff(column_sums(matrix))


def delta_vectors(matrix: NDArray) -> NDArray:
    """Compute the delta vector for each row.

    For row [a₁, a₂, ..., aₙ], the delta vector is
    [a₁-a₂, a₂-a₃, ..., aₙ₋₁-aₙ].

    Args:
        matrix: An m×n matrix.

    Returns:
        m×(n-1) matrix of row-wise consecutive differences.

    Example:
        >>> delta_vectors(np.array([[1,3,2],[3,1,2]]))
        array([[-2,  1],
               [ 2, -1]])
    """
    return matrix[:, :-1] - matrix[:, 1:]


def is_column_balanced(matrix: NDArray) -> bool:
    """Check if a matrix is column-balanced (all column sums equal).

    Args:
        matrix: An m×n matrix.

    Returns:
        True if all columns have the same sum.

    Example:
        >>> is_column_balanced(np.array([[1,2,3],[3,1,2],[2,3,1]]))
        True
    """
    cs = column_sums(matrix)
    return bool(np.all(cs == cs[0]))


def check(matrix: NDArray) -> tuple[bool, NDArray]:
    """Run the CBDI check on a matrix.

    This is the primary function for error detection.
    On a clean (column-balanced) matrix, returns (True, zeros).
    On a corrupted matrix, returns (False, syndrome) where the
    syndrome reveals the error location.

    Args:
        matrix: An m×n matrix to verify.

    Returns:
        Tuple of (is_valid, syndrome).
        - is_valid: True if the matrix passes the CBDI check.
        - syndrome: The delta syndrome vector (n-1 entries).

    Example:
        >>> import cbdi
        >>> M = cbdi.latin_square(4)
        >>> ok, syn = cbdi.check(M)
        >>> ok
        True
        >>> syn
        array([0, 0, 0])
    """
    syndrome = total_delta(matrix)
    return bool(np.all(syndrome == 0)), syndrome
