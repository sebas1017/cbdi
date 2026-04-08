# CBDI — Column-Balanced Delta Invariant

Error detection for permutation matrices via column-sum invariance.

```bash
pip install cbdi
```

## Theorem

For any *m x n* matrix whose rows are permutations of a fixed set *S*:

> The sum of all row-wise consecutive differences is zero **if and only if** every column has the same sum.

This lets you verify an entire permutation matrix with a single column-sum operation instead of checking row by row.

## Usage

```python
import cbdi

M = cbdi.latin_square(8)
ok, syndrome = cbdi.check(M)       # True, [0 0 0 0 0 0 0]

# inject error
corrupted = cbdi.inject_transposition(M, row=3, col=4)
ok, syndrome = cbdi.check(corrupted)  # False, [0 0 0 1 -2 1 0]

cbdi.localize(syndrome)
# {'pattern': 'laplacian', 'columns': (5, 6), 'magnitude': 1, ...}
```

When an error occurs, the syndrome reveals its type:

| Error | Syndrome | Tells you |
|:---|:---|:---|
| Entry corruption at col *j* | `[..., +ε, -ε, ...]` (dipole) | Which column |
| Transposition at *(j, j+1)* | `[..., +ε, -2ε, +ε, ...]` (laplacian) | Which column pair |

## Installation

```bash
git clone https://github.com/sebas1017/cbdi.git
cd cbdi
pip install -e .
```

Requires Python 3.10+ and NumPy >= 1.24.

## Benchmark

CBDI replaces *m* per-row checks with one vectorized column-sum. On clean pages (the common case), nothing else is needed.

| Page | Per-row syndrome | Per-row sort | CBDI | Speedup |
|:---|---:|---:|---:|---:|
| 104x4 | 2,320 us | 434 us | 50 us | 47x |
| 504x8 | 11,620 us | 2,370 us | 80 us | 145x |
| 2000x8 | 46,200 us | 9,110 us | 230 us | 201x |
| 2000x16 | 93,200 us | 18,580 us | 400 us | 233x |
| 5000x8 | 117,000 us | 22,730 us | 570 us | 205x |

Detection: 100% on single transposition errors (1,000 random trials).

Reproduce with `python benchmark_cbdi.py`.

## API

**Verification**

- `cbdi.check(matrix)` — returns `(bool, syndrome)`
- `cbdi.is_column_balanced(matrix)` — bool
- `cbdi.total_delta(matrix)` — syndrome vector
- `cbdi.column_sums(matrix)` — column sums
- `cbdi.delta_vectors(matrix)` — per-row deltas

**Syndrome analysis**

- `cbdi.localize(syndrome)` — classify error pattern and location
- `cbdi.diagnose(matrix)` — full diagnostic report

**Construction**

- `cbdi.latin_square(n)` — cyclic Latin square
- `cbdi.column_balanced_matrix(m, n, values=None)` — balanced matrix
- `cbdi.parity_row(data_rows, values=None)` — parity permutation

**Error injection (testing)**

- `cbdi.inject_transposition(matrix, row, col)`
- `cbdi.inject_corruption(matrix, row, col, new_value)`

## Use cases

**Rank modulation (flash memory)** — Flash stores data as permutations of charge levels. CBDI gives a page-level check that complements per-row Kendall-tau codes: CBDI finds which columns, Kendall-tau finds which row, together they pinpoint the cell.

**Combinatorial verification** — Check structural properties of Latin squares, Sudoku grids, and similar objects without scanning every element.

**Data integrity** — Any system storing permutation arrays (schedules, assignments, experimental designs) can use CBDI as a consistency check.

## Tests

```bash
pip install pytest
pytest -v
```

## Citation

```bibtex
@software{henao2025cbdi,
  author  = {Henao Erazo, Sebastian},
  title   = {{CBDI}: Column-Balanced Delta Invariant},
  year    = {2025},
  url     = {https://github.com/sebas1017/cbdi},
  license = {MIT}
}
```

## License

[MIT](LICENSE) — Sebastian Henao Erazo
