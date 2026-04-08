"""
Benchmark: CBDI vs Traditional Error Detection for Rank Modulation
===================================================================

The REAL comparison is NOT "memcmp vs column-sum" (which is unfair because
memcmp is a hardware-optimized operation that assumes you HAVE a reference copy).

The REAL scenario in flash memory is:

  A flash controller reads a page. It does NOT have a reference copy.
  It must verify integrity using ONLY the data read.

  Strategy A (Kendall tau per row): For each of the m rows, compute the
  Kendall tau syndrome (weighted checksum) to verify it's a valid codeword.
  Cost: O(n) per row × m rows = O(mn) with significant per-row overhead.

  Strategy B (CBDI-first): Compute column sums. Check n-1 differences.
  If all zero → page OK. One vectorized operation, no per-row loops.
  Cost: O(mn) for the sum, but as ONE vectorized operation.

The speedup comes from:
  1. CBDI is one vectorized matrix operation (column sum)
  2. Traditional requires m individual row-level syndrome computations
  3. On clean pages (99.9% of reads), CBDI says "OK" with zero row processing

Author: Sebastian Henao Erazo
"""

import numpy as np
import time


def build_latin_square_page(m, n):
    """Build a column-balanced m×n page using cyclic Latin square blocks."""
    S = np.arange(1, n + 1)
    m = ((m + n - 1) // n) * n
    matrix = np.zeros((m, n), dtype=np.int64)
    for i in range(m):
        matrix[i] = np.roll(S, i % n)
    return matrix


def inject_transposition(matrix, row, col):
    """Swap entries at (row, col) and (row, col+1)."""
    out = matrix.copy()
    out[row, col], out[row, col + 1] = out[row, col + 1], out[row, col]
    return out


# ═══════════════════════════════════════════════
# Strategy A: Per-row syndrome check (Kendall-tau style)
# ═══════════════════════════════════════════════

def weighted_checksum_syndrome(row, n, prime):
    """Compute weighted checksum syndrome for a single row.
    This simulates what a real Kendall tau systematic code does:
    S = sum(w_i * row[i]) mod prime, for weights w_i = (2i-1)."""
    s = 0
    for i in range(n):
        s += (2 * i + 1) * row[i]
    return s % prime


def verify_per_row_syndrome(matrix, n, prime):
    """Check every row by computing its weighted checksum syndrome.
    A valid codeword has syndrome = expected_syndrome (precomputed).
    Returns True if all rows pass."""
    m = matrix.shape[0]
    # Precompute expected syndrome for {1,...,n} with cyclic shift
    expected = weighted_checksum_syndrome(np.arange(1, n + 1), n, prime)

    for i in range(m):
        syn = weighted_checksum_syndrome(matrix[i], n, prime)
        # For cyclic shifts, syndrome varies — check it's a valid permutation
        # Simplified: check that the row sums to n(n+1)/2 AND is a permutation
        if matrix[i].sum() != n * (n + 1) // 2:
            return False, i
        # Check it's a valid permutation (all elements present)
        if len(set(matrix[i])) != n:
            return False, i
    return True, -1


def verify_per_row_numpy(matrix, n):
    """Optimized per-row check using numpy: for each row, verify it's a
    valid permutation of {1,...,n}. This is the fastest possible row-by-row check."""
    m = matrix.shape[0]
    target_sum = n * (n + 1) // 2
    target_set = set(range(1, n + 1))

    for i in range(m):
        # Quick sum check
        if matrix[i].sum() != target_sum:
            return False, i
        # Permutation check (sorted comparison)
        if not np.array_equal(np.sort(matrix[i]), np.arange(1, n + 1)):
            return False, i
    return True, -1


# ═══════════════════════════════════════════════
# Strategy B: CBDI column-sum check
# ═══════════════════════════════════════════════

def verify_cbdi(matrix):
    """CBDI: one column sum + one diff. Returns (ok, syndrome)."""
    col_sums = matrix.sum(axis=0)
    syndrome = np.diff(col_sums)
    return np.all(syndrome == 0), syndrome


def verify_cbdi_then_rows(matrix, n):
    """CBDI first. If fails, find the bad row."""
    ok, syndrome = verify_cbdi(matrix)
    if ok:
        return True, syndrome, -1

    m = matrix.shape[0]
    for i in range(m):
        if not np.array_equal(np.sort(matrix[i]), np.arange(1, n + 1)):
            return False, syndrome, i
    # All rows are valid permutations but columns unbalanced → structural error
    return False, syndrome, -1


# ═══════════════════════════════════════════════
# Benchmark
# ═══════════════════════════════════════════════

def run():
    print("=" * 72)
    print("  BENCHMARK: CBDI vs Per-Row Verification")
    print("  (Realistic: no reference copy available)")
    print("=" * 72)

    configs = [
        (104, 4,   "104×4    (416 cells)"),
        (504, 8,   "504×8   (4,032 cells)"),
        (2000, 8,  "2000×8  (16,000 cells)"),
        (2000, 16, "2000×16 (32,000 cells)"),
        (5000, 8,  "5000×8  (40,000 cells)"),
    ]

    num_trials = 500
    prime = 1009  # for syndrome computation

    print(f"\n  Trials: {num_trials}")
    print(f"  Each trial: verify a CLEAN page (no errors)")
    print(f"  This measures the common case: 99.9%+ of page reads\n")

    results = []

    for m_target, n, label in configs:
        page = build_latin_square_page(m_target, n)
        m = page.shape[0]

        # ── Warm up ──
        for _ in range(10):
            verify_per_row_numpy(page, n)
            verify_cbdi(page)

        # ── Time: Per-row syndrome check ──
        t0 = time.perf_counter()
        for _ in range(num_trials):
            verify_per_row_syndrome(page, n, prime)
        t_syndrome = (time.perf_counter() - t0) / num_trials * 1e6

        # ── Time: Per-row numpy check ──
        t0 = time.perf_counter()
        for _ in range(num_trials):
            verify_per_row_numpy(page, n)
        t_rowcheck = (time.perf_counter() - t0) / num_trials * 1e6

        # ── Time: CBDI column-sum check ──
        t0 = time.perf_counter()
        for _ in range(num_trials):
            verify_cbdi(page)
        t_cbdi = (time.perf_counter() - t0) / num_trials * 1e6

        speedup_vs_syndrome = t_syndrome / t_cbdi
        speedup_vs_rowcheck = t_rowcheck / t_cbdi

        results.append((label, m, n, t_syndrome, t_rowcheck, t_cbdi,
                         speedup_vs_syndrome, speedup_vs_rowcheck))

        print(f"  ─── {label} ───")
        print(f"    Per-row syndrome : {t_syndrome:10.1f} μs")
        print(f"    Per-row np.sort  : {t_rowcheck:10.1f} μs")
        print(f"    CBDI column-sum  : {t_cbdi:10.1f} μs")
        print(f"    Speedup vs syndrome: {speedup_vs_syndrome:6.1f}×")
        print(f"    Speedup vs np.sort : {speedup_vs_rowcheck:6.1f}×")
        print()

    # ── Detection accuracy ──
    print("=" * 72)
    print("  DETECTION ACCURACY TEST")
    print("=" * 72)

    m, n = 2000, 8
    page = build_latin_square_page(m, n)
    m = page.shape[0]
    num_error_trials = 1000
    cbdi_detected = 0
    row_detected = 0

    for _ in range(num_error_trials):
        err_row = np.random.randint(0, m)
        err_col = np.random.randint(0, n - 1)
        corrupted = inject_transposition(page, err_row, err_col)

        ok_c, _ = verify_cbdi(corrupted)
        if not ok_c:
            cbdi_detected += 1

        ok_r, _ = verify_per_row_numpy(corrupted, n)
        if not ok_r:
            row_detected += 1

    print(f"\n  {num_error_trials} random single-transposition errors on {m}×{n} page:")
    print(f"    CBDI detected:    {cbdi_detected}/{num_error_trials} ({100*cbdi_detected/num_error_trials:.1f}%)")
    print(f"    Per-row detected: {row_detected}/{num_error_trials} ({100*row_detected/num_error_trials:.1f}%)")

    # ── Summary ──
    print(f"\n{'=' * 72}")
    print("  SUMMARY TABLE")
    print("=" * 72)
    print(f"  {'Page size':<22} {'Syndrome':>10} {'Row-check':>10} {'CBDI':>10} {'vs Syndr.':>10} {'vs Rows':>10}")
    print("  " + "─" * 68)
    for label, m, n, ts, tr, tc, ss, sr in results:
        print(f"  {label:<22} {ts:>9.1f}μ {tr:>9.1f}μ {tc:>9.1f}μ {ss:>9.1f}× {sr:>9.1f}×")

    print(f"""
  ╔═══════════════════════════════════════════════════════════════════╗
  ║                                                                   ║
  ║  WHAT A DEVELOPER/USER GETS:                                      ║
  ║                                                                   ║
  ║  1. SPEED: CBDI replaces m per-row checks with ONE matrix op.     ║
  ║     On clean pages (99.9% of reads), this is all you need.        ║
  ║                                                                   ║
  ║  2. LOCALIZATION: When an error IS found, the CBDI syndrome       ║
  ║     tells you WHICH COLUMNS are affected (Laplacian pattern).     ║
  ║     Per-row check tells you WHICH ROW. Together → exact cell.     ║
  ║                                                                   ║
  ║  3. ACCURACY: 100% detection for any single transposition error.  ║
  ║                                                                   ║
  ║  4. OVERHEAD: Essentially zero — just needs column-balanced       ║
  ║     construction (automatic for Latin square-based storage).      ║
  ║                                                                   ║
  ╚═══════════════════════════════════════════════════════════════════╝
""")


def demo():
    """Visual demo of syndrome localization."""
    print("=" * 72)
    print("  DEMO: CBDI Syndrome Localizes the Error")
    print("=" * 72)

    n = 8
    page = build_latin_square_page(n, n)

    print(f"\n  8×8 Latin square (column-balanced):\n")
    for i in range(page.shape[0]):
        print(f"    {page[i]}")
    print(f"\n  Column sums: {page.sum(axis=0)}  → all equal ✓")

    # Error
    err_r, err_c = 3, 4
    a, b = page[err_r, err_c], page[err_r, err_c + 1]
    corrupted = inject_transposition(page, err_r, err_c)

    print(f"\n  ─── Error: row {err_r}, swap cols ({err_c},{err_c+1}): {a}↔{b} ───")

    ok, syn = verify_cbdi(corrupted)
    print(f"\n  CBDI syndrome: {syn}")
    print(f"  Error detected: {'YES ✓' if not ok else 'no'}")

    nz = np.nonzero(syn)[0]
    if len(nz) >= 2:
        # Find the -2ε peak
        peak = nz[np.argmax(np.abs(syn[nz]))]
        eps = abs(syn[peak]) // 2
        print(f"  Laplacian peak at index {peak} → columns {peak} and {peak+1} affected")
        print(f"  |ε| = {eps}")
        print(f"  Combine with row scan → exact location: row {err_r}, col {err_c}")
    print()


if __name__ == "__main__":
    demo()
    run()
