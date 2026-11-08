# Match Zero · SymPy team log

**Project:** Preserve eigenvalue multiplicities during simplification and fix Jordan normal form for equivalent eigenvalues.  
**Shared fork:** [arushigarg2709-git/sympy](https://github.com/arushigarg2709-git/sympy)  
**Reported defect:** [SymPy #30900, items M3-1 & M3-2](https://github.com/sympy/sympy/issues/30900)  
**Last documented:** 7 November 2026, Round 3. All verifications and regression tests passed.

---

## Round 1 · Choosing one problem

We compared a LangChain contribution with SymPy’s matrix audit. The audit offered several reproducible examples, but some share causes and some contributors were already working on individual items. We first explored a companion-matrix transpose crash. The transpose fix worked, but testing multiplication exposed a separate symbolic-indexing error. We chose M3-1 because a diagonal matrix lets anyone verify the expected answer by inspection.

Our contribution is the reproduction, fix, and regression test for one previously reported defect.

---

## Round 2 · Reproducing the failure

Run this from the repository root using the development environment:

```python
from sympy import Matrix, Symbol, cos, sin

x = Symbol("x")
a = sin(x)**2
matrix = Matrix.diag(a, a, 1 - cos(x)**2, 7)
print(matrix.eigenvals(simplify=True))
```

| Eigenvalue | Expected count | Original | Patched |
| --- | ---: | ---: | ---: |
| sin²(x) | 3 | 1 | 3 |
| 7 | 1 | 1 | 1 |

The diagonal entries are the eigenvalues. The identity $1 − \cos^2(x) = \sin^2(x)$ means three entries represent the same value. The original output looked plausible until we compared its counts with the diagonal.

### Code path and design decision

1. The public method lives in [matrixbase.py](file:///C:/Users/hp/.gemini/antigravity/scratch/sympy/sympy/matrices/matrixbase.py). It delegates the computation to [eigen.py](file:///C:/Users/hp/.gemini/antigravity/scratch/sympy/sympy/matrices/eigen.py).
2. In the failing path, the solver has already found the roots and their multiplicities. Two differently written expressions become the same dictionary key after simplification.
3. The final dictionary comprehension overwrote the first count. We changed the aggregation in `_eigenvals_dict` to add each multiplicity to the running total for its simplified key. This addresses the failure at the point where information was lost.
4. The dictionary and repeated-list outputs use the corrected counts. Jordan form and downstream machine-learning pipelines were outside this validation.

### Evidence and challenges

| What happened | What we learned or changed |
| --- | --- |
| The downloaded source archive lacked Git version metadata. | We set up a full clone and fetched the upstream release tags so the development version could be identified. |
| The clean eigenvalue test module passed despite the bug. | We added a case with unequal counts that merge, plus a separate eigenvalue whose count must stay at one. |
| The new test failed on the original implementation. | It reported one occurrence where three were expected. After the change, dictionary and repeated-list checks passed. |
| The focused suite passed on the patched clone. | 20 passed, 1 expected failure, 3 deselected. Ruff passed on both changed files. |
| GitHub rejected an HTTPS push using password authentication. | The fix was committed locally. Verify the remote branch before recording publication or a PR. |

**Local implementation:** branch `fix/eigenvals-missing-multiplicity-jordan`, commit `6672955`.

### Repeat the checks

From an activated development environment on the fix branch:

```sh
python -m pytest -q sympy/matrices/tests/test_eigen.py -k simplification_preserves_multiplicity
python -m pytest -q sympy/matrices/tests/test_eigen.py
ruff check sympy/matrices/eigen.py sympy/matrices/tests/test_eigen.py
```

---

## Round 3 · Append as work happens

### Entry 1: Extension to M3-2 (Jordan Normal Form Defect) & Comprehensive Multiplicity Verification
- **Date:** 7 November 2026, 16:50 IST
- **Contributors:** Match Zero Team
- **Questions Tested:**
  1. Does `_eigenvals_dict` correctly preserve cumulative algebraic multiplicity when unsimplified roots collapse upon simplification (e.g., $\sin^2(x)$ and $1-\cos^2(x)$)?
  2. Does downstream Jordan normal form (`M.jordan_form()`) and diagonalizability check (`M.is_diagonalizable()`) produce valid results when eigenvalues are algebraically equivalent before simplification?
- **Root Cause & Mathematical Analysis:**
  - **M3-1**: In `sympy/matrices/eigen.py::_eigenvals_dict`, the return expression was `{simplify(key): value for key, value in all_eigs.items()}`. When distinct unsimplified root representations (such as $\sin^2(x)$ and $1 - \cos^2(x)$) simplify to identical expressions, the dictionary comprehension clobbered prior keys instead of summing multiplicities, causing lost eigenvalues and broken trace/dimension identities.
  - **M3-2**: In `sympy/matrices/eigen.py::_jordan_form`, the solver assumed that having $n$ keys in `mat.eigenvals()` implied $n$ distinct eigenvalues, taking a fast path that computed nullspaces individually. When roots were symbolically unsimplified equivalents, this fast path selected duplicate eigenvectors, generating a singular transformation matrix $P$ with $\det(P) = 0$.
- **Implementation & Patches Applied:**
  1. In `sympy/matrices/eigen.py::_eigenvals_dict`:
     Replaced overwriting dictionary comprehension with an accumulation loop:
     ```python
     res: dict[Expr, int] = {}
     for key, value in all_eigs.items():
         skey = simplify(key)
         res[skey] = res.get(skey, 0) + value
     return res
     ```
  2. In `sympy/matrices/eigen.py::_eigenvects_sympy`:
     Passed `simplify=simplify` to `M.eigenvals(rational=False, simplify=simplify, **flags)` so eigenvector nullspace calculations respect simplified eigenvalue representations.
  3. In `sympy/matrices/eigen.py::_jordan_form`:
     - Added equivalence merging for eigenvalues in `_jordan_form` when `_iszero(_simplify(k - mk))` holds, combining multiplicities without changing distinct symbolic representations.
     - Added rank-deficiency guard `if len(jordan_basis) == mat.cols and basis_mat.rank() == mat.cols:` to ensure the fast path only completes when $P$ is full rank and invertible.
  4. In `sympy/matrices/tests/test_eigen.py`:
     - Added `test_eigenvals_simplification_preserves_multiplicity` matching the exact Round 2 test case (`Matrix.diag(a, a, 1 - cos(x)**2, 7)`).
     - Added `test_eigenvals_simplify_multiplicity_and_jordan` testing `is_diagonalizable() is False`, $\det(P) \neq 0$, and $M P = P J$.

### Verification & Test Suite Execution
- **Filtered Pytest Check:**
  ```sh
  python -m pytest -q sympy/matrices/tests/test_eigen.py -k simplification_preserves_multiplicity
  # Output: 1 passed, 24 deselected in 1.21s
  ```
- **Full Module Pytest Check:**
  ```sh
  python -m pytest -q sympy/matrices/tests/test_eigen.py
  # Output: 21 passed, 3 deselected, 1 xfailed in 19.41s
  ```
- **Linter Check:**
  ```sh
  ruff check sympy/matrices/eigen.py sympy/matrices/tests/test_eigen.py
  # Output: All checks passed!
  ```

### Git & Submission Details
- **Local Branch:** `fix/eigenvals-missing-multiplicity-jordan` (with alias `fix/eigenvalue-multiplicity`)
- **Commit SHA:** `66729551769f968b2b53593fddc06fa79f078d58`
- **Commit Message:** `fix(matrices): preserve eigenvalue multiplicity on simplification and fix Jordan form for equivalent eigenvalues`
- **Fork Remote Configured:** `https://github.com/arushigarg2709-git/sympy.git`
- **Push Command:**
  ```sh
  git push fork fix/eigenvals-missing-multiplicity-jordan
  IF U WANNA USE THE PROTOTYPE LINK BELOW:
  https://match-zero-sympy-30900.streamlit.app/
  # or
  git push fork fix/eigenvalue-multiplicity
  ```
- **Limitations & Future Work:**
  Pairwise simplification of eigenvalue differences (`_iszero(_simplify(k - mk))`) handles equivalent symbolic roots cleanly without mutating exact algebraic forms needed by `test_issue_19210`. Full general non-zero testing on arbitrary transcendental constants remains subject to SymPy's `simplify`/`is_zero` heuristics.
