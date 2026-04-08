"""
CBDI — Column-Balanced Delta Invariant

Error detection for permutation matrices via column-sum invariance.

    >>> import cbdi
    >>> M = cbdi.latin_square(4)
    >>> cbdi.check(M)
    (True, array([0, 0, 0]))
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
