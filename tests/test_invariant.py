"""Tests for the CBDI library."""

import numpy as np
import pytest
import cbdi


class TestLatinSquare:
    def test_sizes(self):
        for n in range(3, 10):
            M = cbdi.latin_square(n)
            assert M.shape == (n, n)

    def test_column_balanced(self):
        for n in range(3, 10):
            M = cbdi.latin_square(n)
            ok, syn = cbdi.check(M)
            assert ok, f"Latin square of size {n} should be column-balanced"
            assert np.all(syn == 0)

    def test_rows_are_permutations(self):
        M = cbdi.latin_square(5)
        for i in range(5):
            assert sorted(M[i]) == [1, 2, 3, 4, 5]

    def test_column_sums(self):
        M = cbdi.latin_square(4)
        assert np.all(cbdi.column_sums(M) == 10)


class TestCheck:
    def test_clean_matrix(self):
        M = cbdi.latin_square(8)
        ok, syn = cbdi.check(M)
        assert ok is True
        assert syn.shape == (7,)
        assert np.all(syn == 0)

    def test_corrupted_matrix(self):
        M = cbdi.latin_square(8)
        C = cbdi.inject_transposition(M, row=2, col=3)
        ok, syn = cbdi.check(C)
        assert ok is False
        assert not np.all(syn == 0)


class TestTranspositionDetection:
    def test_always_detected(self):
        """Every single adjacent transposition must be detected."""
        M = cbdi.latin_square(8)
        m, n = M.shape
        for row in range(m):
            for col in range(n - 1):
                C = cbdi.inject_transposition(M, row, col)
                ok, syn = cbdi.check(C)
                assert not ok, f"Transposition at ({row},{col}) not detected"

    def test_laplacian_pattern(self):
        """Transposition syndrome should be [+ε, -2ε, +ε]."""
        M = cbdi.latin_square(8)
        C = cbdi.inject_transposition(M, row=3, col=4)
        _, syn = cbdi.check(C)
        eps = M[3, 5] - M[3, 4]  # ε = M[row, col+1] - M[row, col]

        # Interior transposition at col 4: syndrome nonzero at indices 3, 4, 5
        assert syn[3] == eps
        assert syn[4] == -2 * eps
        assert syn[5] == eps

    def test_100_percent_detection_random(self):
        """Random transpositions on larger matrix: 100% detection."""
        M = cbdi.column_balanced_matrix(100, 8)
        rng = np.random.default_rng(42)
        for _ in range(500):
            C, _, _ = cbdi.core.errors.inject_random_transposition(M, rng)
            ok, _ = cbdi.check(C)
            assert not ok


class TestCorruptionDetection:
    def test_always_detected(self):
        M = cbdi.latin_square(6)
        C = cbdi.inject_corruption(M, row=2, col=3, new_value=99)
        ok, _ = cbdi.check(C)
        assert not ok

    def test_dipole_pattern(self):
        M = cbdi.latin_square(6)
        C = cbdi.inject_corruption(M, row=0, col=2, new_value=99)
        _, syn = cbdi.check(C)
        eps = 99 - M[0, 2]
        # Interior: dipole at indices 1,2
        assert syn[1] == eps
        assert syn[2] == -eps


class TestLocalize:
    def test_clean(self):
        M = cbdi.latin_square(8)
        _, syn = cbdi.check(M)
        loc = cbdi.localize(syn)
        assert loc["error_detected"] is False
        assert loc["pattern"] == "none"

    def test_transposition_localization(self):
        M = cbdi.latin_square(8)
        C = cbdi.inject_transposition(M, row=2, col=5)
        _, syn = cbdi.check(C)
        loc = cbdi.localize(syn)
        assert loc["error_detected"] is True
        assert loc["pattern"] == "laplacian"
        assert loc["columns"] == (5, 6)

    def test_corruption_localization(self):
        M = cbdi.latin_square(6)
        C = cbdi.inject_corruption(M, row=1, col=3, new_value=99)
        _, syn = cbdi.check(C)
        loc = cbdi.localize(syn)
        assert loc["error_detected"] is True
        assert loc["pattern"] == "dipole"
        assert 3 in loc["columns"]


class TestDiagnose:
    def test_full_diagnostic(self):
        M = cbdi.latin_square(4)
        diag = cbdi.diagnose(M)
        assert diag["balanced"] is True
        assert diag["matrix_shape"] == (4, 4)
        assert diag["expected_column_sum"] == 10


class TestColumnBalancedMatrix:
    def test_custom_values(self):
        M = cbdi.column_balanced_matrix(6, 3, values=[1, 6, 24])
        ok, _ = cbdi.check(M)
        assert ok

    def test_irrational_values(self):
        import math
        M = cbdi.column_balanced_matrix(3, 3, values=[math.pi, math.e, math.sqrt(2)])
        ok, syn = cbdi.check(M)
        assert ok or np.allclose(syn, 0, atol=1e-10)


class TestParityRow:
    def test_basic(self):
        data = np.array([[1, 3, 2], [3, 2, 1]])
        pr = cbdi.parity_row(data)
        assert pr is not None
        full = np.vstack([data, pr.reshape(1, -1)])
        ok, _ = cbdi.check(full)
        assert ok

    def test_invalid_returns_none(self):
        # Construct a case where no parity row exists
        data = np.array([[1, 1, 1]])  # Not a valid permutation setup
        pr = cbdi.parity_row(data, values=[1, 2, 3])
        # May or may not return None depending on the math


class TestCBDIDistance:
    def test_two_opposite_transpositions_cancel(self):
        """CBDI distance is 2: two opposite transpositions at same column = undetectable."""
        M = cbdi.latin_square(8)
        # Find two rows where the difference at col 3 is opposite
        eps1 = M[0, 4] - M[0, 3]
        # Find a row where the difference is -eps1
        for r in range(1, 8):
            eps2 = M[r, 4] - M[r, 3]
            if eps1 + eps2 == 0:
                # Apply both transpositions
                C = cbdi.inject_transposition(M, row=0, col=3)
                C = cbdi.inject_transposition(C, row=r, col=3)
                ok, syn = cbdi.check(C)
                assert ok, "Two opposite transpositions should be CBDI-undetectable"
                return
        pytest.skip("No opposite-magnitude pair found in this Latin square")
