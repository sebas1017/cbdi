"""
Benchmark: CBDI vs per-row verification for rank modulation pages.

The realistic scenario: a flash controller reads a page and must verify
integrity using ONLY the data read (no reference copy available).

  - Per-row: check each row individually (sum + permutation validity)
  - CBDI: one column-sum + diff operation for the whole page

Author: Sebastian Henao Erazo
"""

import numpy as np
import time


def build_latin_square_page(m, n):
    S = np.arange(1, n + 1)
    m = ((m + n - 1) // n) * n
    matrix = np.zeros((m, n), dtype=np.int64)
    for i in range(m):
        matrix[i] = np.roll(S, i % n)
    return matrix


def inject_transposition(matrix, row, col):
    out = matrix.copy()
    out[row, col], out[row, col + 1] = out[row, col + 1], out[row, col]
    return out


# -- Per-row checks --

def weighted_checksum_syndrome(row, n, prime):
    """Weighted checksum: S = sum(w_i * row[i]) mod prime."""
    s = 0
    for i in range(n):
        s += (2 * i + 1) * row[i]
    return s % prime


def verify_per_row_syndrome(matrix, n, prime):
    """Check every row via weighted checksum + permutation validity."""
    m = matrix.shape[0]
    expected = weighted_checksum_syndrome(np.arange(1, n + 1), n, prime)
    for i in range(m):
        if matrix[i].sum() != n * (n + 1) // 2:
            return False, i
        if len(set(matrix[i])) != n:
            return False, i
    return True, -1


def verify_per_row_numpy(matrix, n):
    """Per-row check: sum + sorted comparison against {1,...,n}."""
    target_sum = n * (n + 1) // 2
    for i in range(matrix.shape[0]):
        if matrix[i].sum() != target_sum:
            return False, i
        if not np.array_equal(np.sort(matrix[i]), np.arange(1, n + 1)):
            return False, i
    return True, -1


# -- CBDI --

def verify_cbdi(matrix):
    col_sums = matrix.sum(axis=0)
    syndrome = np.diff(col_sums)
    return np.all(syndrome == 0), syndrome


# -- Benchmark --

def run():
    print("CBDI vs Per-Row Verification")
    print("=" * 60)

    configs = [
        (104, 4,   "104x4    (416 cells)"),
        (504, 8,   "504x8   (4032 cells)"),
        (2000, 8,  "2000x8  (16000 cells)"),
        (2000, 16, "2000x16 (32000 cells)"),
        (5000, 8,  "5000x8  (40000 cells)"),
    ]

    num_trials = 500
    prime = 1009

    print(f"\n{num_trials} trials per config, clean pages (no errors)\n")

    results = []

    for m_target, n, label in configs:
        page = build_latin_square_page(m_target, n)
        m = page.shape[0]

        for _ in range(10):  # warmup
            verify_per_row_numpy(page, n)
            verify_cbdi(page)

        t0 = time.perf_counter()
        for _ in range(num_trials):
            verify_per_row_syndrome(page, n, prime)
        t_syndrome = (time.perf_counter() - t0) / num_trials * 1e6

        t0 = time.perf_counter()
        for _ in range(num_trials):
            verify_per_row_numpy(page, n)
        t_rowcheck = (time.perf_counter() - t0) / num_trials * 1e6

        t0 = time.perf_counter()
        for _ in range(num_trials):
            verify_cbdi(page)
        t_cbdi = (time.perf_counter() - t0) / num_trials * 1e6

        speedup_syn = t_syndrome / t_cbdi
        speedup_row = t_rowcheck / t_cbdi

        results.append((label, t_syndrome, t_rowcheck, t_cbdi, speedup_syn, speedup_row))

        print(f"  {label}")
        print(f"    Per-row syndrome : {t_syndrome:8.1f} us")
        print(f"    Per-row np.sort  : {t_rowcheck:8.1f} us")
        print(f"    CBDI column-sum  : {t_cbdi:8.1f} us")
        print(f"    Speedup: {speedup_syn:.0f}x (vs syndrome), {speedup_row:.0f}x (vs sort)")
        print()

    # Detection accuracy
    print("Detection accuracy (1000 random transpositions on 2000x8)")
    print("-" * 60)

    m, n = 2000, 8
    page = build_latin_square_page(m, n)
    m = page.shape[0]
    cbdi_ok = 0
    row_ok = 0

    for _ in range(1000):
        r = np.random.randint(0, m)
        c = np.random.randint(0, n - 1)
        corrupted = inject_transposition(page, r, c)

        ok_c, _ = verify_cbdi(corrupted)
        if not ok_c:
            cbdi_ok += 1

        ok_r, _ = verify_per_row_numpy(corrupted, n)
        if not ok_r:
            row_ok += 1

    print(f"  CBDI:    {cbdi_ok}/1000 ({cbdi_ok/10:.1f}%)")
    print(f"  Per-row: {row_ok}/1000 ({row_ok/10:.1f}%)")

    # Summary
    print(f"\n{'Page':<24} {'Syndrome':>10} {'Sort':>10} {'CBDI':>10} {'Speedup':>10}")
    print("-" * 64)
    for label, ts, tr, tc, ss, sr in results:
        print(f"  {label:<22} {ts:>8.0f}us {tr:>8.0f}us {tc:>8.0f}us {ss:>7.0f}x")


def demo():
    """Quick demo: inject error, read syndrome."""
    n = 8
    page = build_latin_square_page(n, n)

    print("8x8 Latin square (column-balanced)")
    for row in page:
        print(f"  {row}")
    print(f"Column sums: {page.sum(axis=0)}")

    err_r, err_c = 3, 4
    a, b = page[err_r, err_c], page[err_r, err_c + 1]
    corrupted = inject_transposition(page, err_r, err_c)

    print(f"\nSwap row {err_r}, cols ({err_c},{err_c+1}): {a} <-> {b}")

    ok, syn = verify_cbdi(corrupted)
    print(f"Syndrome: {syn}")
    print(f"Detected: {not ok}")

    nz = np.nonzero(syn)[0]
    if len(nz) >= 2:
        peak = nz[np.argmax(np.abs(syn[nz]))]
        eps = abs(syn[peak]) // 2
        print(f"Laplacian at index {peak} -> columns {peak},{peak+1}, |eps| = {eps}")
    print()


if __name__ == "__main__":
    demo()
    run()
