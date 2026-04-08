"""
CBDI Quick Start Example
========================

Demonstrates the core workflow:
1. Build a column-balanced matrix
2. Verify it passes the CBDI check
3. Inject an error
4. Detect and localize the error using the syndrome
"""

import cbdi
import numpy as np

# ── 1. Build a column-balanced Latin square ──

M = cbdi.latin_square(8)
print("8x8 Latin square:")
print(M)
print(f"\nColumn sums: {cbdi.column_sums(M)}")

# ── 2. Verify integrity ──

ok, syndrome = cbdi.check(M)
print(f"\nCBDI check: {'PASS' if ok else 'FAIL'}")
print(f"Syndrome:   {syndrome}")

# ── 3. Inject an adjacent transposition error ──

corrupted = cbdi.inject_transposition(M, row=3, col=4)
print(f"\nInjected transposition: row 3, swap cols (4, 5)")
print(f"Original row 3:  {M[3]}")
print(f"Corrupted row 3: {corrupted[3]}")

# ── 4. Detect and localize ──

ok, syndrome = cbdi.check(corrupted)
print(f"\nCBDI check: {'PASS' if ok else 'FAIL'}")
print(f"Syndrome:   {syndrome}")

result = cbdi.localize(syndrome)
print(f"\nLocalization:")
print(f"  Pattern:   {result['pattern']}")
print(f"  Columns:   {result['columns']}")
print(f"  Magnitude: {result['magnitude']}")
print(f"  Details:   {result['details']}")

# ── 5. Full diagnostic ──

print("\n--- Full Diagnostic ---")
diag = cbdi.diagnose(corrupted)
for key, val in diag.items():
    print(f"  {key}: {val}")

# ── 6. Custom value set ──

print("\n--- Custom Values ---")
M2 = cbdi.column_balanced_matrix(9, 3, values=[10, 20, 30])
print(f"9x3 matrix with values {{10, 20, 30}}:")
print(M2)
print(f"Column sums: {cbdi.column_sums(M2)}")
print(f"Balanced: {cbdi.is_column_balanced(M2)}")

# ── 7. Parity row construction ──

print("\n--- Parity Row ---")
data = np.array([[1, 3, 2], [3, 2, 1]])
parity = cbdi.parity_row(data)
print(f"Data rows:\n{data}")
print(f"Parity row: {parity}")
full = np.vstack([data, parity])
print(f"Full matrix:\n{full}")
print(f"Column sums: {cbdi.column_sums(full)}")
print(f"Balanced: {cbdi.is_column_balanced(full)}")
