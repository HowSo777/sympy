# Match Zero - SymPy multiplicity and Jordan form fix

Team 6 - Saya

Fork: [arushigarg2709-git/sympy](https://github.com/arushigarg2709-git/sympy)

Reported problem: [SymPy issue 30900, M3-1 and M3-2](https://github.com/sympy/sympy/issues/30900)

## Review status - 8 November 2026

This version was checked against the fork's public `master` snapshot
`c4479573f6779ce3af7f73536f5b9045225e7a0b`.
At review time, only `master` was publicly available. The previously documented
fix branches and local commit IDs have not been verified as published.
This README does not claim a live deployment or an upstream pull request.

## 1. The problem

An eigenvalue's multiplicity is the number of times it occurs.
For `diag(sin(x)**2, sin(x)**2, 1 - cos(x)**2, 7)`, the expected answer is
`{sin(x)**2: 3, 7: 1}` because `1 - cos(x)**2 = sin(x)**2`.
The original code replaces a previous count when two expressions simplify
to the same dictionary key. The total count can therefore become too small.

When all eigenvalues are returned, their algebraic multiplicities must sum
to the matrix dimension. A valid Jordan decomposition also needs an
invertible basis `P` satisfying `M * P = P * J`.

## 2. Wrong code before running

Original code in `_eigenvals_dict`:

```python
return {simplify(key): value for key, value in all_eigs.items()}
```

The same operation written as a simple loop:

```python
result = {}
for key, value in all_eigs.items():
    result[simplify(key)] = value
```

Assigning to the same key again replaces its previous count.

## 3. Correct code

```python
res: dict[Expr, int] = {}
for key, value in all_eigs.items():
    skey = simplify(key)
    res[skey] = res.get(skey, 0) + value
return res
```

`res.get(skey, 0)` reads the count already stored, or zero for a new key.
The incoming count is added to it. The example now retains three copies
of `sin(x)**2` and one copy of `7`.

## 4. Eigenvectors and Jordan form

The patch also passes the requested `simplify` setting from
`_eigenvects_sympy` to `M.eigenvals`.

For Jordan form, it merges eigenvalue keys only when simplifying their
difference gives a confirmed zero. It retains an existing representative
instead of replacing every root expression with a new simplified form.

The actual fast path in this source is:

```python
if len(eigs.keys()) == mat.cols:
```

The earlier dossier's `len(blocks) == mat.cols` example did not match this
source and should not be presented as the exact implementation.
The reviewed patch checks basis length before constructing the basis matrix,
then checks full rank before returning the fast-path result. If the basis
is unsuitable, normal Jordan-chain construction continues.

Symbolic simplification is heuristic. These changes and tests do not establish
that every possible pair of equivalent symbolic expressions can be detected.

## 5. Verified results

Environment: Python 3.14, fork source snapshot listed above.
The GitHub archive has no Git version metadata. An isolated local `_version.py`
was supplied for testing only and is not part of this upload or patch.

| Check | Result |
| --- | --- |
| Three added tests on original fork code | 3 failed, 23 deselected |
| Full eigenvalue test module after changes | 22 passed, 3 deselected, 1 xfailed |
| `python bin/test quality` | 6 passed, 1 deselected |
| `ruff check sympy` | All checks passed |
| Presentation app | Three spectrum examples and Jordan reference passed |

The module tests cover dictionary and repeated-list multiplicities, equivalent
roots, diagonalizability, invertible Jordan bases, the similarity identity,
`calc_transform=False`, a 3 by 3 Jordan block, and a 1 by 1 boundary case.
Repeated-list tests check counts without assuming list ordering.

Run these commands from a full Git clone after applying the patch:

```sh
python -m pip install -e .
python -m pip install pytest hypothesis ruff
python -m pytest -q sympy/matrices/tests/test_eigen.py
python bin/test quality
ruff check sympy
```

## 6. Run the presentation in VS Code

Open the repository folder in VS Code and run:

```sh
python -m pip install -r demo/requirements.txt
python -m streamlit run demo/app.py
```

The app displays wrong and correct code before running and again after the
results. It has plain labels, a Run button, a blue background, and falling
balloons. Its aggregation demo runs both functions on raw eigenvalues.
Its Jordan panel is an analytical reference for one example; it is not a
claim that a published library patch is installed.

## 7. Deployment

To deploy with Streamlit Community Cloud, first publish `demo/app.py` and
`demo/requirements.txt` on the chosen branch of this fork. Create a Streamlit
app using that repository, branch, and entry point `demo/app.py`.
Record the actual hosted URL here after deployment succeeds.

Deployment status: not yet deployed.

## 8. Final explanation for judges

Before: simplifying keys can overwrite an existing count.
After: simplifying keys adds the counts, preserving multiplicity in the tests.
For Jordan form, equivalent roots are merged and the fast-path basis is checked
before it is returned.

The exact reviewed changes follow. Save this as documentation, but apply the
patch to the actual source files as well; a README alone does not change SymPy.

## 9. Exact reviewed patch

```diff
diff --git a/sympy/matrices/eigen.py b/sympy/matrices/eigen.py
--- a/sympy/matrices/eigen.py
+++ b/sympy/matrices/eigen.py
@@ -323,7 +323,11 @@
         return all_eigs
     if not isinstance(simplify, FunctionType):
         simplify = _simplify
-    return {simplify(key): value for key, value in all_eigs.items()}
+    res: dict[Expr, int] = {}
+    for key, value in all_eigs.items():
+        skey = simplify(key)
+        res[skey] = res.get(skey, 0) + value
+    return res
 
 
 def _eigenspace(
@@ -366,7 +370,7 @@
         simplify: bool | Callable[[Expr], Expr] = True,
         **flags: Any,
     ) -> list[tuple[Expr, int, list[Tmat]]]:
-    eigenvals = M.eigenvals(rational=False, **flags)
+    eigenvals = M.eigenvals(rational=False, simplify=simplify, **flags)
 
     # Make sure that we have all roots in radical form
     for x in eigenvals:
@@ -1275,6 +1279,15 @@
 
     # first calculate the jordan block structure
     eigs = mat.eigenvals()
+    merged_eigs: dict[Expr, int] = {}
+    for eigenvalue, multiplicity in eigs.items():
+        for existing in merged_eigs:
+            if _iszero(_simplify(eigenvalue - existing)) is True:
+                merged_eigs[existing] += multiplicity
+                break
+        else:
+            merged_eigs[eigenvalue] = multiplicity
+    eigs = merged_eigs
 
     # Make sure that we have all roots in radical form
     for x in eigs:
@@ -1293,11 +1306,16 @@
         if not calc_transform:
             return restore_floats1(jordan_mat)
 
-        jordan_basis = [eig_mat(eig, 1).nullspace()[0]
-                for eig in blocks]
-        basis_mat    = mat.hstack(*jordan_basis)
-
-        return restore_floats2(basis_mat, jordan_mat)
+        jordan_basis = []
+        for eig in blocks:
+            basis = eig_mat(eig, 1).nullspace()
+            if basis:
+                jordan_basis.append(basis[0])
+
+        if len(jordan_basis) == mat.cols:
+            basis_mat = mat.hstack(*jordan_basis)
+            if basis_mat.rank() == mat.cols:
+                return restore_floats2(basis_mat, jordan_mat)
 
     block_structure = []
 
diff --git a/sympy/matrices/tests/test_eigen.py b/sympy/matrices/tests/test_eigen.py
--- a/sympy/matrices/tests/test_eigen.py
+++ b/sympy/matrices/tests/test_eigen.py
@@ -807,3 +807,47 @@
     P, J = A.jordan_form()
     assert P.det() == 16*sqrt(2)
     assert expand(P*J*P.inv()) == expand(A)
+
+
+def test_eigenvals_simplification_preserves_multiplicity():
+    x = Symbol("x")
+    a = sin(x)**2
+    matrix = Matrix.diag(a, a, 1 - cos(x)**2, 7)
+    assert matrix.eigenvals(simplify=True) == {sin(x)**2: 3, S(7): 1}
+    assert len(matrix.eigenvals(simplify=True, multiple=True)) == 4
+    values = matrix.eigenvals(simplify=True, multiple=True)
+    assert values.count(sin(x)**2) == 3
+    assert values.count(S(7)) == 1
+
+
+def test_eigenvals_simplify_multiplicity_and_jordan():
+    x = Symbol('x')
+    M_diag = Matrix([[sin(x)**2, 0], [0, 1 - cos(x)**2]])
+    assert M_diag.eigenvals(simplify=True) == {sin(x)**2: 2}
+    assert len(M_diag.eigenvals(simplify=True, multiple=True)) == 2
+
+    M_jordan = Matrix([[sin(x)**2, 1], [0, 1 - cos(x)**2]])
+    assert M_jordan.is_diagonalizable() is False
+    P, J = M_jordan.jordan_form()
+    assert simplify(P.det()) != 0
+    assert simplify(M_jordan * P - P * J) == Matrix.zeros(2, 2)
+    assert M_jordan.jordan_form(calc_transform=False) == J
+
+
+def test_eigenvals_simplify_edge_cases():
+    x = Symbol('x')
+    e1, e2, e3 = sin(x)**2, 1 - cos(x)**2, (1 - cos(2*x))/2
+
+    M_mono = Matrix.diag(e1, e2, e3, e1)
+    assert M_mono.eigenvals(simplify=True) == {sin(x)**2: 4}
+    assert len(M_mono.eigenvals(simplify=True, multiple=True)) == 4
+
+    M_jordan3 = Matrix([[e1, 1, 0], [0, e2, 1], [0, 0, e3]])
+    assert M_jordan3.is_diagonalizable() is False
+    P3, J3 = M_jordan3.jordan_form()
+    assert simplify(P3.det()) != 0
+    assert simplify(M_jordan3 * P3 - P3 * J3) == Matrix.zeros(3, 3)
+    assert M_jordan3.jordan_form(calc_transform=False) == J3
+
+    M_1x1 = Matrix([[e2]])
+    assert M_1x1.eigenvals(simplify=True) == {sin(x)**2: 1}
```

## Authorship and review

The supplied submission was reviewed and revised with OpenAI Codex (GPT-6).
The revised source, tests, presentation app, and this README require the
maintainer's human review before an upstream submission. No upstream PR was
opened by this review.
