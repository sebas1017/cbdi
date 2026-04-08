"""
Syndrome analysis — interpret the CBDI delta syndrome to localize errors.

Patterns:
    - Corruption at column j  →  Dipole:    [..., +ε, -ε, ...]
    - Transposition (j, j+1)  →  Laplacian: [..., +ε, -2ε, +ε, ...]
"""

import numpy as np


def localize(syndrome):
    """Classify the syndrome and return the error location.

    Returns a dict with: error_detected, pattern, columns, magnitude, details.
    """
    if np.all(syndrome == 0):
        return {
            "error_detected": False,
            "pattern": "none",
            "columns": None,
            "magnitude": 0,
            "details": "No error detected.",
        }

    nonzero_idx = np.nonzero(syndrome)[0]
    n_nonzero = len(nonzero_idx)

    # Single nonzero → boundary corruption
    if n_nonzero == 1:
        idx = nonzero_idx[0]
        eps = abs(int(syndrome[idx]))
        col = 0 if idx == 0 else len(syndrome)
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

        # Dipole: +ε, -ε
        if abs(s_i + s_j) < 1e-10:
            col = i + 1
            return {
                "error_detected": True,
                "pattern": "dipole",
                "columns": (col,),
                "magnitude": abs(int(s_i)),
                "details": f"Entry corruption at column {col}, |ε| = {abs(int(s_i))}.",
            }

        # Boundary laplacian: -2ε, +ε or +ε, -2ε
        ratio = s_i / s_j if s_j != 0 else float('inf')
        if abs(ratio + 2) < 1e-10:
            eps = abs(int(s_j))
            return {
                "error_detected": True,
                "pattern": "laplacian",
                "columns": (i, i + 1),
                "magnitude": eps,
                "details": f"Adjacent transposition at columns ({i}, {i+1}), |ε| = {eps}.",
            }
        if abs(ratio + 0.5) < 1e-10:
            eps = abs(int(s_i))
            return {
                "error_detected": True,
                "pattern": "laplacian",
                "columns": (j, j + 1),
                "magnitude": eps,
                "details": f"Adjacent transposition at columns ({j}, {j+1}), |ε| = {eps}.",
            }

    # Three adjacent nonzero → interior laplacian
    if n_nonzero == 3:
        i, j, k = nonzero_idx
        if j - i == 1 and k - j == 1:
            s_i, s_j, s_k = int(syndrome[i]), int(syndrome[j]), int(syndrome[k])
            if abs(s_i - s_k) < 1e-10 and abs(s_j + 2 * s_i) < 1e-10:
                eps = abs(s_i)
                return {
                    "error_detected": True,
                    "pattern": "laplacian",
                    "columns": (j, j + 1),
                    "magnitude": eps,
                    "details": (
                        f"Adjacent transposition at columns ({j}, {j+1}), "
                        f"|ε| = {eps}. Syndrome: [{s_i:+d}, {s_j:+d}, {s_k:+d}]."
                    ),
                }

    # Anything else
    return {
        "error_detected": True,
        "pattern": "complex",
        "columns": tuple(nonzero_idx.tolist()),
        "magnitude": int(np.max(np.abs(syndrome))),
        "details": (
            f"Complex pattern: {n_nonzero} nonzero entries "
            f"at positions {nonzero_idx.tolist()}."
        ),
    }


def diagnose(matrix):
    """Full diagnostic: CBDI check + syndrome localization."""
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
