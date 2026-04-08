"""
CBDI — Column-Balanced Delta Invariant
=======================================

A Python library for error detection in permutation matrices
using the Column-Balanced Delta Invariant.

Usage:
    >>> import cbdi
    >>> matrix = cbdi.latin_square(4)
    >>> cbdi.check(matrix)
    (True, array([0, 0, 0]))

    >>> corrupted = cbdi.inject_transposition(matrix, row=1, col=2)
    >>> ok, syndrome = cbdi.check(corrupted)
    >>> ok
    False
    >>> cbdi.localize(syndrome)
    {'error_detected': True, 'columns': (2, 3), 'magnitude': 1, 'pattern': 'laplacian'}
"""

__version__ = "0.1.0"
__author__ = "Sebastian Henao Erazo"

from cbdi.core.invariant import (
    check,
    delta_vectors,
    total_delta,
    column_sums,
    is_column_balanced,
)
from cbdi.core.syndrome import localize, diagnose
from cbdi.core.construction import (
    latin_square,
    column_balanced_matrix,
    parity_row,
)
from cbdi.core.errors import inject_transposition, inject_corruption

__all__ = [
    "check",
    "delta_vectors",
    "total_delta",
    "column_sums",
    "is_column_balanced",
    "localize",
    "diagnose",
    "latin_square",
    "column_balanced_matrix",
    "parity_row",
    "inject_transposition",
    "inject_corruption",
]
