# Match Zero - SymPy multiplicity and Jordan form fix

Team 6 - Saya

**Forks & Branches:**
- **Primary Team Fork:** [arushigarg2709-git/sympy](https://github.com/arushigarg2709-git/sympy)
- **Deployment Fork:** [HowSo777/sympy](https://github.com/HowSo777/sympy)
- **Active Branch:** `fix/eigenvals-missing-multiplicity-jordan`
- **Live Streamlit Web App:** [https://match-zero-sympy-30900.streamlit.app](https://match-zero-sympy-30900.streamlit.app)
- **1-Click Google Colab Notebook:** [MATCH_ZERO_LIVE_INSPECTOR.ipynb](https://colab.research.google.com/github/arushigarg2709-git/sympy/blob/fix/eigenvals-missing-multiplicity-jordan/MATCH_ZERO_LIVE_INSPECTOR.ipynb)

Reported problem: [SymPy issue 30900, M3-1 and M3-2](https://github.com/sympy/sympy/issues/30900)

## Review status - 8 November 2026

This version was verified against the active feature branch `fix/eigenvals-missing-multiplicity-jordan`
synchronized across both `arushigarg2709-git/sympy` and `HowSo777/sympy`.
All core patches, regression suites, live Streamlit cloud web app, and one-click cloud verification notebook
are verified and live.

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

## 6. Run the presentation & prototypes

### Option A: Interactive Web Dashboard (`app_prototype.py`)
Run the Streamlit live dashboard locally:
```sh
pip install -r requirements.txt
streamlit run app_prototype.py
```
*(Or double-click `RUN_WEB_PROTOTYPE.bat` on Windows).*

The app features:
- Live spectrum comparison (`📦 Legacy Model` vs `🚀 Upgraded Model`)
- Step-by-step shopping-cart dictionary accumulation tracer
- Dynamic neon math operator burst animation (`+`, `=`, `XOR`, `÷`, `/`, `⊕`, `×`, `−`, `∑`, `λ`)
- Case-insensitive trigonometric formula input normalizer (`Cosx`, `Cost`, `sin^2 x`)
- Instant in-memory regression test runner (<25ms).

### Option B: Zero-Dependency Terminal Verification Script
Run the instant mainline verification harness (<2s):
```sh
python verify_integration.py
```

### Option C: Standalone Terminal CLI Prototype
Run the lightweight terminal demonstration:
```sh
python prototype_demo.py
```
*(Or double-click `RUN_TERMINAL_DEMO.bat` on Windows).*

---

## 7. Deployment & Live Cloud Execution Links

- **Live Streamlit Community Cloud App:** [https://match-zero-sympy-30900.streamlit.app](https://match-zero-sympy-30900.streamlit.app)  
  *Status:* **Active & Live.** Zero-setup browser access to the interactive prototype running directly on Streamlit Cloud.
- **One-Click Interactive Cloud Notebook:** [MATCH_ZERO_LIVE_INSPECTOR.ipynb](https://colab.research.google.com/github/arushigarg2709-git/sympy/blob/fix/eigenvals-missing-multiplicity-jordan/MATCH_ZERO_LIVE_INSPECTOR.ipynb)  
  *Status:* **Active & Live.** Runs the entire 4-stage verification harness in Google Cloud with 1 click.

---

## 08. Complete Deliverables Roster

| Deliverable Artifact | Type & Path | Role & Verification Function |
| :--- | :--- | :--- |
| **`sympy/matrices/eigen.py`** | Core Engine Source | Main patched SymPy file implementing Defect M3-1 additive multiplicity accumulator (`_eigenvals_dict`), eigenvector simplification sync (`_eigenvects_sympy`), and Defect M3-2 zero-difference root merge + full-rank guard (`_jordan_form`). |
| **`sympy/matrices/tests/test_eigen.py`** | Unit Test Suite | Official test file containing all 3 custom regression suites verifying multiplicity preservation, defective Jordan similarity, and monolithic spectrum edge cases (22 passed). |
| **`sympy/release.py` & `_version.py`** | Cloud Resilience | Eliminates shallow-clone `ImportError` exceptions on cloud runners (Streamlit Cloud, Docker, Colab) by providing static development fallback metadata. |
| **`app_prototype.py`** | Live Interactive UI | Streamlit Web Inspector featuring real-time spectrum comparison, the shopping-cart iteration tracer, neon math operator celebration burst, and instant in-memory test runner (<25ms). |
| **`MATCH_ZERO_LIVE_INSPECTOR.ipynb`** | 1-Click Cloud Notebook | Interactive Google Colab notebook executing the full verification pipeline in Google Cloud with 1 click (zero local setup required). |
| **`verify_integration.py`** | Mainline Proof Script | Zero-dependency standalone Python verification script that introspects loaded SymPy source, tests public APIs (`M.eigenvals(simplify=True)`, $\det(P) \neq 0$), and runs pytest in <2 seconds. |
| **`requirements.txt`** | Dependency Manifest | Clean, modular dependency specification separating core runtime, developer testing, and prototype visualization tools. |
| **`INTEGRATION_PROOF.md`** | Architecture Dossier | Technical document demonstrating the exact dispatch call graph from public `MatrixBase` methods to our patched functions in `eigen.py`. |
| **`README-MACHZERO.md`** | Central Master Log | Comprehensive technical documentation covering Rounds 1–3, mathematical contracts, semantic models, and before/after code walkthroughs. |
| **`README-MACHZERO-TEAM6-SAYA.md`** | Team Submission Review | Official review document for Team 6 (Saya) detailing problem statements, code diffs, verified results, and execution guides. |
| **`MATCH_ZERO_TECHNICAL_ROUND_DOSSIER.md`** | Theoretical Dossier | Transcribed 6-page technical dossier covering the shopping-cart dictionary model, failure analysis, and mathematical defense. |
| **`QUICKSTART.md`** | Evaluator Guide | 1-minute quickstart guide for competition judges and teammates. |
| **`prototype_demo.py`** | Terminal CLI Prototype | Lightweight, standalone command-line demonstration for offline terminal environments. |
| **`RUN_WEB_PROTOTYPE.bat`** | Windows Shortcut | 1-click desktop batch launcher for the Streamlit web dashboard. |
| **`RUN_TERMINAL_DEMO.bat`** | Windows Shortcut | 1-click desktop batch launcher for the CLI terminal demonstration. |
| **`match_zero_sympy_issue_30900.patch`** | Unified Git Patch | Standard unified Git patch allowing anyone to apply the complete fix to any clean SymPy checkout with `git apply`. |
| **`MATCH_ZERO_SYMPY_SUBMISSION_BUNDLE.zip`** | Offline Archive | Self-contained 58.4 KB distribution zip bundle holding all project deliverables for offline evaluation. |

---

## 09. Libraries, Packages & Environment Specifications

The following tables document every third-party package, runtime dependency, Python standard library module, and environment tool utilized during the engineering of this project:

### 1. Third-Party Libraries & External Packages

| Library / Tool | Installed Version | Scope | Purpose & Modules Utilized | Mandatory? |
| :--- | :--- | :--- | :--- | :--- |
| **`python`** | `3.14.0` (Tested $\ge 3.10$) | Core Runtime | Pure-Python execution environment for the SymPy computer algebra system. | **Yes** |
| **`mpmath`** | `1.4.1` (Required $\ge 1.1.0$) | Core Runtime | SymPy's sole hard runtime dependency; provides arbitrary-precision floating-point arithmetic. | **Yes** |
| **`sympy`** | `1.14.dev0+matchzero` | Core Kernel | The computer algebra system under fix; modules: `sympy.matrices`, `sympy.core`, `sympy.simplify`, `sympy.functions.elementary.trigonometric`. | **Yes** |
| **`pytest`** | `9.0.1` (Required $\ge 7.4.0$) | Testing & CI | Official SymPy test runner; used for regression test execution, test discovery, and assertion evaluation. | Dev Only |
| **`hypothesis`** | `6.80.0+` | Testing & CI | Property-based testing framework used in SymPy's matrix test suite. | Dev Only |
| **`ruff`** | `0.1.0+` | Code Quality | High-speed static analysis and linting engine; verifies upstream SymPy code conventions (0 warnings). | Dev Only |
| **`streamlit`** | `1.62.0` (Required $\ge 1.30.0$) | Presentation UI | Reactive web dashboard framework; powers the live inspector, custom CSS keyframe animations, and session state. | Prototype Only |
| **`pandas`** | `2.3.3` (Required $\ge 2.0.0$) | Presentation UI | High-performance tabular data structures; powers the zero-scroll Quantitative Verification Table in Tab 1. | Prototype Only |

### 2. Python Standard Library Modules Utilized

| Standard Module | Purpose & Specific Implementation in Match Zero |
| :--- | :--- |
| **`os`** | Operating system interfaces; environment variable resolution and working directory isolation across platforms. |
| **`re`** | Regular expressions engine; used in `normalize_math_expression()` for case-insensitive trigonometric input normalization (`Cosx`, `Cost`, `sin^2 x`, `1 - Cosx**2`). |
| **`pathlib.Path`** | Object-oriented filesystem path resolution; ensures cross-platform path compatibility across Windows (`\`), Linux (`/`), Docker, and Streamlit Cloud. |
| **`subprocess`** | Process management; powers the instant in-memory and subprocess Pytest runners, Git metadata inspection, and shallow clone detection. |
| **`sys`** | System-specific parameters and runtime introspection; dynamically configures `sys.path` and handles terminal encoding (`sys.stdout.reconfigure(encoding="utf-8")`). |
| **`time`** | High-resolution microsecond performance profiling via `time.perf_counter()` to benchmark test execution speeds (<25ms in Tab 4). |
| **`random`** | Seed-based particle generator in `trigger_math_operator_burst()` to animate 70 floating neon math symbols with randomized trajectories and rotations. |
| **`json`** | Data serialization; used for Jupyter notebook generation (`MATCH_ZERO_LIVE_INSPECTOR.ipynb`) and live dictionary state display (`st.json()`). |
| **`zipfile` & `shutil`** | Automated compression engine; packages all project assets into `MATCH_ZERO_SYMPY_SUBMISSION_BUNDLE.zip`. |
| **`types.FunctionType`** | Type introspection; allows `_eigenvals_dict` to detect custom user-supplied simplifier functions versus default `_simplify`. |

### 3. Development, Hosting & Cloud Platform Infrastructure

| Tool / Platform | Role & Usage in Match Zero Engineering |
| :--- | :--- |
| **Git (v2.x)** | Distributed version control; managed atomic feature branches, cherry-picks, and generated unified patch `match_zero_sympy_issue_30900.patch`. |
| **GitHub** | Remote synchronization, upstream tracking, team collaboration with Arushi (`arushigarg2709-git/sympy`) and Yashas (`HowSo777/sympy`), and cloud deployment integration. |
| **Streamlit Community Cloud** | Hosted Linux container environment serving the live web app at [match-zero-sympy-30900.streamlit.app](https://match-zero-sympy-30900.streamlit.app). |
| **Google Colab** | Zero-install cloud Jupyter environment executing the complete verification pipeline with a single click. |
| **Cross-Platform Shells** | Dual verification across Windows 11 (PowerShell / `py`) and Linux (Bash / `python3`). |

---

## 10. Final explanation for judges

Before: simplifying keys can overwrite an existing count.
After: simplifying keys adds the counts, preserving multiplicity in the tests.
For Jordan form, equivalent roots are merged and the fast-path basis is checked
before it is returned.

The exact reviewed changes follow. Save this as documentation, but apply the
patch to the actual source files as well; a README alone does not change SymPy.

## 11. Exact reviewed patch

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

## 12. Authorship and review

The supplied submission was reviewed and revised with OpenAI Codex (GPT-6).
The revised source, tests, presentation app, and this README require the
maintainer's human review before an upstream submission. No upstream PR was
opened by this review.
