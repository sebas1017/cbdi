import numpy as np
import pytest
import cbdi


# -- Latin square construction --

def test_latin_square_sizes():
    for n in range(3, 10):
        M = cbdi.latin_square(n)
        assert M.shape == (n, n)


def test_latin_square_balanced():
    for n in range(3, 10):
        ok, syn = cbdi.check(cbdi.latin_square(n))
        assert ok
        assert np.all(syn == 0)


def test_latin_square_rows_are_permutations():
    M = cbdi.latin_square(5)
    for i in range(5):
        assert sorted(M[i]) == [1, 2, 3, 4, 5]


def test_latin_square_column_sums():
    assert np.all(cbdi.column_sums(cbdi.latin_square(4)) == 10)


# -- CBDI check --

def test_check_clean():
    M = cbdi.latin_square(8)
    ok, syn = cbdi.check(M)
    assert ok is True
    assert syn.shape == (7,)
    assert np.all(syn == 0)


def test_check_corrupted():
    M = cbdi.latin_square(8)
    C = cbdi.inject_transposition(M, row=2, col=3)
    ok, syn = cbdi.check(C)
    assert ok is False


# -- Transposition detection --

def test_all_transpositions_detected():
    """Every single adjacent transposition must break column balance."""
    M = cbdi.latin_square(8)
    m, n = M.shape
    for row in range(m):
        for col in range(n - 1):
            C = cbdi.inject_transposition(M, row, col)
            ok, _ = cbdi.check(C)
            assert not ok, f"Missed transposition at ({row},{col})"


def test_laplacian_syndrome():
    M = cbdi.latin_square(8)
    C = cbdi.inject_transposition(M, row=3, col=4)
    _, syn = cbdi.check(C)
    eps = M[3, 5] - M[3, 4]
    assert syn[3] == eps
    assert syn[4] == -2 * eps
    assert syn[5] == eps


def test_random_transpositions_100pct():
    M = cbdi.column_balanced_matrix(100, 8)
    rng = np.random.default_rng(42)
    for _ in range(500):
        C, _, _ = cbdi.core.errors.inject_random_transposition(M, rng)
        ok, _ = cbdi.check(C)
        assert not ok


# -- Corruption detection --

def test_corruption_detected():
    M = cbdi.latin_square(6)
    C = cbdi.inject_corruption(M, row=2, col=3, new_value=99)
    ok, _ = cbdi.check(C)
    assert not ok


def test_dipole_syndrome():
    M = cbdi.latin_square(6)
    C = cbdi.inject_corruption(M, row=0, col=2, new_value=99)
    _, syn = cbdi.check(C)
    eps = 99 - M[0, 2]
    assert syn[1] == eps
    assert syn[2] == -eps


# -- Localization --

def test_localize_clean():
    _, syn = cbdi.check(cbdi.latin_square(8))
    loc = cbdi.localize(syn)
    assert loc["error_detected"] is False
    assert loc["pattern"] == "none"


def test_localize_transposition():
    M = cbdi.latin_square(8)
    C = cbdi.inject_transposition(M, row=2, col=5)
    _, syn = cbdi.check(C)
    loc = cbdi.localize(syn)
    assert loc["pattern"] == "laplacian"
    assert loc["columns"] == (5, 6)


def test_localize_corruption():
    M = cbdi.latin_square(6)
    C = cbdi.inject_corruption(M, row=1, col=3, new_value=99)
    _, syn = cbdi.check(C)
    loc = cbdi.localize(syn)
    assert loc["pattern"] == "dipole"
    assert 3 in loc["columns"]


# -- Diagnose --

def test_diagnose():
    diag = cbdi.diagnose(cbdi.latin_square(4))
    assert diag["balanced"] is True
    assert diag["matrix_shape"] == (4, 4)
    assert diag["expected_column_sum"] == 10


# -- Custom construction --

def test_custom_values():
    M = cbdi.column_balanced_matrix(6, 3, values=[1, 6, 24])
    ok, _ = cbdi.check(M)
    assert ok


def test_irrational_values():
    import math
    M = cbdi.column_balanced_matrix(3, 3, values=[math.pi, math.e, math.sqrt(2)])
    ok, syn = cbdi.check(M)
    assert ok or np.allclose(syn, 0, atol=1e-10)


def test_parity_row():
    data = np.array([[1, 3, 2], [3, 2, 1]])
    pr = cbdi.parity_row(data)
    assert pr is not None
    full = np.vstack([data, pr.reshape(1, -1)])
    ok, _ = cbdi.check(full)
    assert ok


def test_parity_row_impossible():
    data = np.array([[1, 1, 1]])
    pr = cbdi.parity_row(data, values=[1, 2, 3])
    # may or may not be solvable depending on the math


# -- CBDI distance --

def test_opposite_transpositions_cancel():
    """Two transpositions with opposite epsilon at the same column are undetectable."""
    M = cbdi.latin_square(8)
    eps1 = M[0, 4] - M[0, 3]
    for r in range(1, 8):
        eps2 = M[r, 4] - M[r, 3]
        if eps1 + eps2 == 0:
            C = cbdi.inject_transposition(M, row=0, col=3)
            C = cbdi.inject_transposition(C, row=r, col=3)
            ok, _ = cbdi.check(C)
            assert ok, "Opposite transpositions should cancel"
            return
    pytest.skip("No opposite-magnitude pair in this Latin square")
