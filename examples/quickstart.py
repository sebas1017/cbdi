"""
Quick start: build, verify, corrupt, detect.
"""

import cbdi
import numpy as np

# Build a column-balanced Latin square
M = cbdi.latin_square(8)
print("8x8 Latin square:")
print(M)
print(f"Column sums: {cbdi.column_sums(M)}")

# Verify
ok, syndrome = cbdi.check(M)
print(f"\nCheck: {'PASS' if ok else 'FAIL'}, syndrome = {syndrome}")

# Inject transposition error
corrupted = cbdi.inject_transposition(M, row=3, col=4)
print(f"\nSwapped row 3 cols (4,5): {M[3]} -> {corrupted[3]}")

# Detect
ok, syndrome = cbdi.check(corrupted)
print(f"Check: {'PASS' if ok else 'FAIL'}, syndrome = {syndrome}")

# Localize
loc = cbdi.localize(syndrome)
print(f"Pattern: {loc['pattern']}, columns: {loc['columns']}, |eps| = {loc['magnitude']}")

# Full diagnostic
print(f"\nDiagnostic: {cbdi.diagnose(corrupted)}")

# Parity row
data = np.array([[1, 3, 2], [3, 2, 1]])
parity = cbdi.parity_row(data)
full = np.vstack([data, parity])
print(f"\nParity row for\n{data}\n-> {parity}, balanced: {cbdi.is_column_balanced(full)}")
