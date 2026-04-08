"""
Syndrome analysis: interpret the CBDI delta syndrome to localize errors.

Syndrome patterns:
    - Single corruption at column j:
        Dipole: [..., +ε, -ε, ...]  at positions (j-1, j)

    - Adjacent transposition at columns (j, j+1):
        Laplacian: [..., +ε, -2ε, +ε, ...] at positions (j-1, j, j+1)
"""

import numpy as np
from numpy.typing import NDArray


def localize(syndrome: NDArray) -> dict:
    """Analyze a CBDI syndrome to localize the error.

    Args:
        syndrome: The delta syndrome from cbdi.check().

    Returns:
        Dictionary with:
        - error_detected (bool): Whether an error was found.
        - pattern (str): 'none', 'dipole', 'laplacian', or 'complex'.
        - columns (tuple|None): Affected column pair.
        - magnitude (int|float): |ε| of the error.
        - details (str): Human-readable description.

    Example:
        >>> import cbdi
        >>> M = cbdi.latin_square(8)
        >>> corrupted = cbdi.inject_transposition(M, row=3, col=4)
        >>> _, syn = cbdi.check(corrupted)
        >>> cbdi.localize(syn)
        {'error_detected': True, 'pattern': 'laplacian', 'columns': (4, 5), ...}
    """
    if np.all(syndrome == 0):
        return {
            "error_detected": False,
            "pattern": "none",
            "columns": None,
            "magnitude": 0,
            "details": "No error detected. Matrix is column-balanced.",
        }

    nonzero_idx = np.nonzero(syndrome)[0]
    n_nonzero = len(nonzero_idx)

    # Single nonzero → boundary corruption
    if n_nonzero == 1:
        idx = nonzero_idx[0]
        eps = abs(int(syndrome[idx]))
        if idx == 0:
            col = 0
        else:
            col = len(syndrome)
        return {
            "error_detected": True,
            "pattern": "dipole",
            "columns": (col,),
            "magnitude": eps,
            "details": f"Entry corruption at column {col}, |ε| = {eps}.",
        }

    # Two adjacent nonzero entries
    if n_nonzero == 2 and nonzero_idx[1] - nonzero_idx[0] == 1:
        i, j = nonzero_idx
        s_i, s_j = syndrome[i], syndrome[j]

        # Check for dipole: +ε, -ε
        if abs(s_i + s_j) < 1e-10:
            col = i + 1  # the affected column
            return {
                "error_detected": True,
                "pattern": "dipole",
                "columns": (col,),
                "magnitude": abs(int(s_i)),
                "details": f"Entry corruption at column {col}, |ε| = {abs(int(s_i))}.",
            }

        # Check for boundary laplacian: -2ε, +ε or +ε, -2ε
        ratio = s_i / s_j if s_j != 0 else float('inf')
        if abs(ratio + 2) < 1e-10:  # s_i = -2ε, s_j = +ε → boundary transposition at (0,1)
            eps = abs(int(s_j))
            return {
                "error_detected": True,
                "pattern": "laplacian",
                "columns": (i, i + 1),
                "magnitude": eps,
                "details": f"Adjacent transposition at columns ({i}, {i+1}), |ε| = {eps}.",
            }
        if abs(ratio + 0.5) < 1e-10:  # s_i = +ε, s_j = -2ε → boundary transposition
            eps = abs(int(s_i))
            return {
                "error_detected": True,
                "pattern": "laplacian",
                "columns": (j, j + 1),
                "magnitude": eps,
                "details": f"Adjacent transposition at columns ({j}, {j+1}), |ε| = {eps}.",
            }

    # Three adjacent nonzero entries → interior laplacian
    if n_nonzero == 3:
        i, j, k = nonzero_idx
        if j - i == 1 and k - j == 1:
            s_i, s_j, s_k = int(syndrome[i]), int(syndrome[j]), int(syndrome[k])
            # Check ratio +1 : -2 : +1 (flanking equal, center = -2× flanking)
            if (abs(s_i - s_k) < 1e-10 and
                    abs(s_j + 2 * s_i) < 1e-10):
                eps = abs(s_i)
                return {
                    "error_detected": True,
                    "pattern": "laplacian",
                    "columns": (j, j + 1),
                    "magnitude": eps,
                    "details": (
                        f"Adjacent transposition at columns ({j}, {j+1}), "
                        f"|ε| = {eps}. "
                        f"Syndrome: [{s_i:+d}, {s_j:+d}, {s_k:+d}]."
                    ),
                }

    # Complex pattern → multiple errors or non-standard corruption
    return {
        "error_detected": True,
        "pattern": "complex",
        "columns": tuple(nonzero_idx.tolist()),
        "magnitude": int(np.max(np.abs(syndrome))),
        "details": (
            f"Complex error pattern. {n_nonzero} nonzero syndrome entries "
            f"at positions {nonzero_idx.tolist()}. May indicate multiple errors."
        ),
    }


def diagnose(matrix: NDArray) -> dict:
    """Full diagnostic: run CBDI check and localize any error.

    Args:
        matrix: An m×n matrix to diagnose.

    Returns:
        Dictionary with full diagnostic info including column sums,
        syndrome, and error localization.

    Example:
        >>> import cbdi
        >>> M = cbdi.latin_square(4)
        >>> cbdi.diagnose(M)
        {'balanced': True, 'column_sums': array([10, 10, 10, 10]), ...}
    """
    cs = matrix.sum(axis=0)
    syndrome = np.diff(cs)
    balanced = bool(np.all(syndrome == 0))
    loc = localize(syndrome)

    return {
        "balanced": balanced,
        "column_sums": cs,
        "syndrome": syndrome,
        "localization": loc,
        "matrix_shape": matrix.shape,
        "expected_column_sum": int(cs[0]) if balanced else None,
    }
