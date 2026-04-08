<p align="center">
  <img src="https://img.shields.io/badge/CBDI-Column--Balanced_Delta_Invariant-0d1117?style=for-the-badge&labelColor=161b22" alt="CBDI" />
</p>

<p align="center">
  <a href="https://www.python.org/"><img src="https://img.shields.io/badge/Python-3.10+-3776AB?style=flat-square&logo=python&logoColor=white" alt="Python" /></a>
  <a href="https://numpy.org/"><img src="https://img.shields.io/badge/NumPy-%E2%89%A51.24-013243?style=flat-square&logo=numpy&logoColor=white" alt="NumPy" /></a>
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-22c55e?style=flat-square" alt="MIT License" /></a>
  <a href="https://github.com/sebas1017/cbdi"><img src="https://img.shields.io/badge/Status-Alpha-f59e0b?style=flat-square" alt="Alpha" /></a>
</p>

<p align="center">
  <b>Ultra-fast error detection for permutation matrices using a single vectorized operation.</b>
</p>

<p align="center">
  <code>pip install cbdi</code>
</p>

---

## The Key Insight

> **Theorem (CBDI).** For any *m* x *n* matrix whose rows are permutations of a fixed set *S*:
>
> *The sum of all row-wise consecutive differences is zero **if and only if** every column has the same sum.*

This means you can verify integrity of an entire permutation matrix with **one column-sum operation** instead of checking each row individually.

```
         Column sums equal?
               |
        ┌──────┴──────┐
       YES             NO
        |               |
   Matrix OK      Read syndrome
                       |
              ┌────────┴────────┐
          Dipole [+ε,-ε]    Laplacian [+ε,-2ε,+ε]
              |                    |
        Entry corrupt      Adjacent transposition
          at column j        at columns (j, j+1)
```

## Quick Start

```python
import cbdi

# Build a column-balanced 8x8 Latin square
M = cbdi.latin_square(8)

# Verify integrity — returns (True, zero_syndrome)
ok, syndrome = cbdi.check(M)
assert ok

# Inject an error: swap adjacent entries in row 3
corrupted = cbdi.inject_transposition(M, row=3, col=4)

# Detect and localize
ok, syndrome = cbdi.check(corrupted)
assert not ok

result = cbdi.localize(syndrome)
print(result)
# {'error_detected': True,
#  'pattern': 'laplacian',
#  'columns': (5, 6),
#  'magnitude': 1,
#  'details': 'Adjacent transposition at columns (5, 6), |ε| = 1. ...'}
```

## Installation

```bash
pip install cbdi
```

Or install from source:

```bash
git clone https://github.com/sebas1017/cbdi.git
cd cbdi
pip install -e .
```

**Requirements:** Python 3.10+ and NumPy >= 1.24

## Performance

CBDI replaces *m* per-row checks with a single vectorized column-sum operation. On clean pages (99.9%+ of real reads), no further processing is needed.

| Page Size | Per-Row Syndrome | Per-Row Sort | **CBDI** | **Speedup** |
|:---|---:|---:|---:|---:|
| 104 x 4 (416 cells) | 2,320 us | 434 us | **50 us** | **47x** |
| 504 x 8 (4K cells) | 11,620 us | 2,370 us | **80 us** | **145x** |
| 2000 x 8 (16K cells) | 46,200 us | 9,110 us | **230 us** | **201x** |
| 2000 x 16 (32K cells) | 93,200 us | 18,580 us | **400 us** | **233x** |
| 5000 x 8 (40K cells) | 117,000 us | 22,730 us | **570 us** | **205x** |

**Detection accuracy:** 100% on single transposition errors (proven by theorem, verified over 1,000 random trials).

> Reproduce: `python benchmark_cbdi.py`

## API Reference

### Core Verification

```python
cbdi.check(matrix)              # -> (bool, syndrome)
cbdi.is_column_balanced(matrix) # -> bool
cbdi.total_delta(matrix)        # -> NDArray (syndrome vector)
cbdi.column_sums(matrix)        # -> NDArray
cbdi.delta_vectors(matrix)      # -> NDArray (per-row deltas)
```

### Syndrome Analysis

```python
cbdi.localize(syndrome)  # -> dict with pattern, columns, magnitude
cbdi.diagnose(matrix)    # -> full diagnostic report
```

Syndrome patterns:
- **`none`** — No error. Matrix is column-balanced.
- **`dipole`** `[+ε, -ε]` — Single entry corruption at column *j*.
- **`laplacian`** `[+ε, -2ε, +ε]` — Adjacent transposition at columns *(j, j+1)*.
- **`complex`** — Multiple errors or non-standard corruption.

### Construction

```python
cbdi.latin_square(n)                        # -> n×n cyclic Latin square
cbdi.column_balanced_matrix(m, n)           # -> m×n balanced matrix
cbdi.column_balanced_matrix(m, n, values)   # -> custom value set
cbdi.parity_row(data_rows)                  # -> parity permutation for balance
```

### Error Injection (Testing)

```python
cbdi.inject_transposition(matrix, row, col)           # swap (row,col) <-> (row,col+1)
cbdi.inject_corruption(matrix, row, col, new_value)   # overwrite entry
```

## How It Works

Given an *m* x *n* matrix **M** where each row is a permutation of *S = {s_1, ..., s_n}*:

1. **Delta vector** of row *i*: `d_i = [M[i,0]-M[i,1], M[i,1]-M[i,2], ..., M[i,n-2]-M[i,n-1]]`

2. **Total delta**: `D = sum(d_i)` across all rows

3. **The invariant**: `D = 0` if and only if `C[0] = C[1] = ... = C[n-1]` (all column sums equal)

4. **In practice**: `D = diff(column_sums(M))`, which is a single NumPy operation

When an error occurs, the syndrome **D** reveals its structure:

| Error Type | Syndrome Pattern | Information |
|:---|:---|:---|
| Entry corruption at col *j* | `[..., +ε, -ε, ...]` at *(j-1, j)* | Which column |
| Adjacent transposition at *(j, j+1)* | `[..., +ε, -2ε, +ε, ...]` at *(j-1, j, j+1)* | Which column pair |

## Use Cases

### Rank Modulation (Flash Memory)

Flash memory stores data as permutations of charge levels. CBDI provides a page-level integrity check that complements per-row Kendall-tau codes:

- **CBDI** detects errors across columns (vertical) — answers *"which columns?"*
- **Kendall tau** detects errors within rows (horizontal) — answers *"which row?"*
- **Together** they pinpoint the exact cell in a single pass

### Combinatorial Verification

Verify structural properties of Latin squares, Sudoku grids, and other combinatorial objects without exhaustive element checking.

### Data Integrity

Any system that stores data as permutation arrays (tournament schedules, assignment matrices, experimental designs) can use CBDI as a lightweight consistency check.

## Project Structure

```
cbdi/
├── __init__.py                 # Public API
├── core/
│   ├── invariant.py            # check(), total_delta(), column_sums()
│   ├── syndrome.py             # localize(), diagnose()
│   ├── construction.py         # latin_square(), parity_row()
│   └── errors.py               # inject_transposition(), inject_corruption()
├── codes/                      # (planned) Code families
└── applications/               # (planned) Domain integrations
tests/
    test_invariant.py           # 19 tests covering all functionality
benchmark_cbdi.py               # Reproducible performance benchmark
```

## Running Tests

```bash
pip install pytest
pytest -v
```

## Citation

If you use CBDI in your research, please cite:

```bibtex
@software{henao2025cbdi,
  author  = {Henao Erazo, Sebastian},
  title   = {{CBDI}: Column-Balanced Delta Invariant},
  year    = {2025},
  url     = {https://github.com/sebas1017/cbdi},
  license = {MIT}
}
```

## Contributing

Contributions are welcome. Areas of interest:

- Hardware-optimized CBDI for FPGA / embedded controllers
- Higher-order delta invariants for multi-error correction
- Integration with existing flash translation layer (FTL) simulators
- Bindings for C / Rust for production flash controllers

## License

[MIT](LICENSE) — Sebastian Henao Erazo
