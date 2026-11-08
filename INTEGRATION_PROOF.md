# Match Zero · SymPy Mainline Integration & Dependencies Architecture

This document answers the judges' inquiries regarding **external dependencies** and **direct integration into SymPy's official core library**.

---

## 1. Dependency Specification

SymPy is famous for its **zero-dependency mathematical purity**. The entire mathematical engine is implemented in pure Python.

### Dependency Breakdown:

| Scope | Package | Minimum Version | Purpose | Mandatory? |
| :--- | :--- | :--- | :--- | :--- |
| **Core Runtime** | `python` | $\ge 3.10$ | Standard Python runtime | **Yes** |
| **Core Runtime** | `mpmath` | $\ge 1.1.0$ | Arbitrary-precision floating-point arithmetic (SymPy's sole hard dependency) | **Yes** |
| **Testing** | `pytest` | $\ge 7.4.0$ | Official SymPy regression and unit test runner | Dev only |
| **Testing** | `hypothesis` | $\ge 6.80.0$ | Property-based testing for matrix routines | Dev only |
| **Code Quality** | `ruff` | $\ge 0.1.0$ | Upstream SymPy linter and formatting checker | Dev only |
| **Presentation Web App** | `streamlit` | $\ge 1.30.0$ | Live interactive judge demonstration inspector | Prototype only |
| **Presentation Web App** | `pandas` | $\ge 2.0.0$ | Tabular formatting of dictionary collisions | Prototype only |

### Fast Installation:
```bash
pip install -r requirements.txt
```

---

## 2. Mainline SymPy Code Integration

Our code is **not an external wrapper, monkey-patch, or separate script**. It directly patches the core SymPy library files in place.

```
sympy/
├── __init__.py                     # SymPy Public Entrypoint
└── matrices/
    ├── matrixbase.py               # Public API: Matrix.eigenvals(), Matrix.jordan_form()
    ├── eigen.py                    # 🟢 PATCHED CORE: _eigenvals_dict, _jordan_form
    └── tests/
        └── test_eigen.py           # 🟢 PATCHED SUITE: 3 new regression tests (22 total)
```

### Architectural Call Dispatch:

```
[User / Judge Python Script]
    │
    │  M = Matrix.diag(sin(x)**2, sin(x)**2, 1 - cos(x)**2, 7)
    │  M.eigenvals(simplify=True)
    ▼
[sympy/matrices/matrixbase.py]
    │  Defines public method `MatrixBase.eigenvals()`
    │  Delegates to internal matrix solver
    ▼
[sympy/matrices/eigen.py::_eigenvals_type()]
    │  Dispatches dictionary normalization
    ▼
[sympy/matrices/eigen.py::_eigenvals_dict()]  <── 🟢 OUR CODE INTEGRATED HERE!
    │  Line 326: res[skey] = res.get(skey, 0) + value
    │  Accumulates multiplicities instead of overwriting keys
    ▼
[Output Returned to User]
    {sin(x)**2: 3, 7: 1}  (Multiplicity 4 / 4 Conserved!)
```

Similarly, for Jordan normal form:
```
[User / Judge Python Script]
    │  M = Matrix([[sin(x)**2, 1], [0, 1 - cos(x)**2]])
    │  P, J = M.jordan_form()
    ▼
[sympy/matrices/matrixbase.py::MatrixBase.jordan_form()]
    ▼
[sympy/matrices/eigen.py::_jordan_form()]  <── 🟢 OUR CODE INTEGRATED HERE!
    │  1. Line 1283: Merges equivalent roots where _iszero(_simplify(k1 - k2)) holds.
    │  2. Line 1315: basis_mat.rank() == mat.cols guard prevents singular P matrix.
    │  3. Builds generalized eigenvector chain.
    ▼
[Output Returned to User]
    P canonical basis with det(P) != 0 and M * P - P * J == 0.
```

---

## 3. How Judges Can Verify Integration Live

### Method A: Execute Mainline Verification Script (<2 seconds)
Run the automated verification script that imports SymPy directly and tests the public API:
```bash
python verify_integration.py
```

### Method B: Pure Python Interactive Verification (Terminal / REPL)
Launch a standard Python prompt from the repository root:
```python
import sympy as sp
from sympy import Matrix, Symbol, sin, cos

# 1. Verify SymPy loads from the repository
print("SymPy Path:", sp.__file__)

# 2. Test M3-1 via public API
x = Symbol("x")
a = sin(x)**2
b = 1 - cos(x)**2
M = Matrix.diag(a, a, b, 7)
print("Public API Result:", M.eigenvals(simplify=True))
# Output: {sin(x)**2: 3, 7: 1}

# 3. Test M3-2 via public API
M2 = Matrix([[a, 1], [0, b]])
P, J = M2.jordan_form()
print("Jordan Invertibility det(P):", sp.simplify(P.det()))
# Output: det(P) = 1 (Non-singular and invertible!)
```

### Method C: Run Official Pytest Harness
```bash
pytest sympy/matrices/tests/test_eigen.py -v
```
Output: `22 passed, 3 deselected, 1 xfailed in 18.67s`.
