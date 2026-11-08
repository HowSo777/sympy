# Match Zero · SymPy Team Log & Technical Code Dossier

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://match-zero-sympy-30900.streamlit.app)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/arushigarg2709-git/sympy/blob/fix/eigenvals-missing-multiplicity-jordan/MATCH_ZERO_LIVE_INSPECTOR.ipynb)
[![CI Tests](https://img.shields.io/badge/Pytest-22%20Passed-brightgreen)](https://github.com/arushigarg2709-git/sympy/tree/fix/eigenvals-missing-multiplicity-jordan)

**Project:** Preserve eigenvalue multiplicities during simplification and fix Jordan normal form for equivalent eigenvalues.  
**Live Web Prototype:** [https://match-zero-sympy-30900.streamlit.app](https://match-zero-sympy-30900.streamlit.app)  
**Shared Fork Remote:** [arushigarg2709-git/sympy](https://github.com/arushigarg2709-git/sympy)  
**Target Repository:** `sympy/sympy`  
**Reported Defects:** [SymPy Issue #30900 (Items M3-1 & M3-2)](https://github.com/sympy/sympy/issues/30900)  
**Branch:** `fix/eigenvals-missing-multiplicity-jordan`  

---

## 01. Executive Overview & Problem Selection

During the Match Zero audit of SymPy's matrix module, we isolated two severe related mathematical defects:
1. **Defect M3-1 (`_eigenvals_dict`)**: Algebraic multiplicity lost when distinct unsimplified symbolic roots collapse onto the same canonical key during simplification (e.g., $\sin^2(x)$ and $1 - \cos^2(x)$).
2. **Defect M3-2 (`_jordan_form`)**: Generation of a singular Jordan transformation matrix ($\det(P) = 0$) when equivalent unsimplified roots bypass Jordan chain construction and select duplicate nullspace vectors.

### The Mathematical Contracts
- **Invariant 1 (Algebraic Multiplicity Conservation):**  
  For any $N \times N$ matrix $M$, the sum of algebraic multiplicities of its eigenvalues must strictly equal the dimension $N$:
  $$\sum_{i=1}^k \mu_i = N$$
- **Invariant 2 (Jordan Similarity Invertibility):**  
  For Jordan decomposition $M = P J P^{-1}$, the transformation matrix $P$ must be full rank and strictly invertible:
  $$\det(P) \neq 0 \quad \text{and} \quad M P - P J = \mathbf{0}$$

---

## 02. Exact Code Replacements (Before vs After)

> [!NOTE]
> **Legacy Model (`📦`) vs. Upgraded Model (`🚀`):**  
> For matrices without trigonometric collisions or equivalent unsimplified roots (e.g. control values or distinct diagonal entries), both the legacy model (`📦`) and the upgraded model (`🚀`) return identical, valid mathematical results (⚖️ **Both Models Agree**). The upgraded model serves as an architectural enhancement that guarantees invariant conservation $\sum \mu_i = N$ and non-singular Jordan basis $\det(P) \neq 0$ even when complex algebraic/trigonometric expressions collapse during simplification.

### Replacement 1: Defect M3-1 — Multiplicity Accumulator in `_eigenvals_dict`
- **File:** [sympy/matrices/eigen.py](file:///C:/Users/hp/.gemini/antigravity/scratch/sympy/sympy/matrices/eigen.py#L323-L332)
- **Function:** `_eigenvals_dict(all_eigs, simplify)`

#### 📦 UPSTREAM BASELINE (Legacy Model · Destructive Dict Comprehension):
```python
    if not simplify:
        return all_eigs
    if not isinstance(simplify, FunctionType):
        simplify = _simplify
    # Legacy Model: Overwrites previous dictionary key on collision; last assignment wins!
    return {simplify(key): value for key, value in all_eigs.items()}
```

#### 🚀 MATCH ZERO UPGRADE (Modern Model · Additive Accumulator):
```python
    if not simplify:
        return all_eigs
    if not isinstance(simplify, FunctionType):
        simplify = _simplify
    # Upgraded Model: Additive accumulation preserves algebraic multiplicity on key collisions
    res: dict[Expr, int] = {}
    for key, value in all_eigs.items():
        skey = simplify(key)
        res[skey] = res.get(skey, 0) + value
    return res
```

#### Why Replacement Matters:
In Python dictionaries, keys are hashed by structural equality. When `simplify(1 - cos(x)**2)` evaluates to `sin(x)**2`, both trigonometric expressions map to the identical key `sin(x)**2`. 
- **Legacy Model:** Evaluated `{sin(x)**2: 2, -(cos(x) - 1)*(cos(x) + 1): 1, 7: 1}` $\longrightarrow$ stored `sin(x)**2: 2`, then clobbered it with `sin(x)**2: 1`. Multiplicity sum dropped from $4 \to 2$!
- **Upgraded Model:** Looks up `res.get(skey, 0)` and sums: $2 + 1 = 3$. Multiplicity sum is $3 + 1 = 4$ ($100\%$ conserved).

---

### Replacement 2: Defect M3-1 — Forwarding Simplification to `_eigenvects_sympy`
- **File:** [sympy/matrices/eigen.py](file:///C:/Users/hp/.gemini/antigravity/scratch/sympy/sympy/matrices/eigen.py#L366-L373)
- **Function:** `_eigenvects_sympy(M, ...)`

#### 📦 UPSTREAM BASELINE (Legacy Model):
```python
    # Legacy Model: Omitted simplify argument, causing eigenvals to default to unsimplified roots
    eigenvals = M.eigenvals(rational=False, **flags)
```

#### 🚀 MATCH ZERO UPGRADE (Modern Model):
```python
    # Upgraded Model: Explicitly passes simplify parameter to synchronize with user's simplify flag
    eigenvals = M.eigenvals(rational=False, simplify=simplify, **flags)
```

---

### Replacement 3: Defect M3-2 — Zero-Difference Merging & Rank Guard in `_jordan_form`
- **File:** [sympy/matrices/eigen.py](file:///C:/Users/hp/.gemini/antigravity/scratch/sympy/sympy/matrices/eigen.py#L1275-L1318)
- **Function:** `_jordan_form(mat, calc_transform)`

#### 📦 UPSTREAM BASELINE (Legacy Model · Duplicate Basis & Singular P):
```python
    # first calculate the jordan block structure
    eigs = mat.eigenvals()

    # Make sure that we have all roots in radical form
    for x in eigs:
        if not is_rad(x):
            return jordan_cells(False)

    # try to use simple eigenvectors if possible
    blocks = [eig for eig in eigs for _ in range(eigs[eig])]
    if len(blocks) == mat.cols:
        jordan_mat = diag(*blocks)
        if not calc_transform:
            return restore_floats1(jordan_mat)

        # Legacy Model: Nullspace calculated for unmerged equivalent eigenvalues
        # yields duplicate columns in P -> det(P) == 0 (Singular!)
        jordan_basis = [eig_mat(eig, 1).nullspace()[0]
                for eig in blocks]
        basis_mat    = mat.hstack(*jordan_basis)

        return restore_floats2(basis_mat, jordan_mat)
```

#### 🚀 MATCH ZERO UPGRADE (Modern Model · Equivalence Merging + Full-Rank Guard):
```python
    # first calculate the jordan block structure
    eigs = mat.eigenvals()
    # Upgraded Model (Part 1): Merge equivalent unsimplified eigenvalues where k1 - k2 == 0
    merged_eigs: dict[Expr, int] = {}
    for k, v in eigs.items():
        found = False
        for mk in merged_eigs:
            diff = k - mk
            if diff == 0 or getattr(diff, 'is_zero', False) or _iszero(diff) or _iszero(_simplify(diff)):
                merged_eigs[mk] += v
                found = True
                break
        if not found:
            merged_eigs[k] = v
    eigs = merged_eigs

    # Make sure that we have all roots in radical form
    for x in eigs:
        if not is_rad(x):
            return jordan_cells(False)

    # try to use simple eigenvectors if possible
    blocks = [eig for eig in eigs for _ in range(eigs[eig])]
    if len(blocks) == mat.cols:
        jordan_mat = diag(*blocks)
        if not calc_transform:
            return restore_floats1(jordan_mat)

        jordan_basis = [ns[0] for eig in blocks if (ns := eig_mat(eig, 1).nullspace())]
        basis_mat    = mat.hstack(*jordan_basis)

        # Upgraded Model (Part 2): Only take fast diagonal path if P is guaranteed full-rank
        if len(jordan_basis) == mat.cols and basis_mat.rank() == mat.cols:
            return restore_floats2(basis_mat, jordan_mat)

    block_structure = []
```
```

#### Why Replacement Matters:
For defective matrix $M = \begin{pmatrix} \sin^2(x) & 1 \\ 0 & 1 - \cos^2(x) \end{pmatrix}$:
- **Upstream:** Treated $\sin^2(x)$ and $1 - \cos^2(x)$ as distinct roots with multiplicity 1 each. Computed the 1D nullspace for both: $[1, 0]^T$ and $[1, 0]^T$. Assembled $P = \begin{pmatrix} 1 & 1 \\ 0 & 0 \end{pmatrix} \implies \det(P) = 0$. Downstream inversions crashed!
- **Patched:** Detects $\sin^2(x) - (1 - \cos^2(x)) = 0$, merges into single root with algebraic multiplicity 2. Because geometric multiplicity is 1, `basis_mat.rank()` is 1 (not 2). The rank guard rejects the premature return, falls through to the generalized eigenvector solver, and produces the correct Jordan chain with $\det(P) \neq 0$ and $M P = P J$.

---

## 03. Regression Test Implementations

- **File:** [sympy/matrices/tests/test_eigen.py](file:///C:/Users/hp/.gemini/antigravity/scratch/sympy/sympy/matrices/tests/test_eigen.py)

```python
def test_eigenvals_simplification_preserves_multiplicity():
    """Verify that simplifying eigenvalues accumulates multiplicities instead of overwriting."""
    x = Symbol("x")
    a = sin(x)**2
    b = 1 - cos(x)**2
    matrix = Matrix.diag(a, a, b, 7)
    
    # 1. Test dict output
    eigs = matrix.eigenvals(simplify=True)
    assert eigs.get(sin(x)**2) == 3
    assert eigs.get(sp.S(7)) == 1
    assert sum(eigs.values()) == 4

    # 2. Test list output
    values = matrix.eigenvals(simplify=True, multiple=True)
    assert len(values) == 4
    assert values.count(sin(x)**2) == 3
    assert values.count(sp.S(7)) == 1


def test_eigenvals_simplify_multiplicity_and_jordan():
    """Verify Jordan form and diagonalizability when eigenvalues are equivalent under simplification."""
    x = Symbol("x")
    a = sin(x)**2
    b = 1 - cos(x)**2
    M = Matrix([[a, 1], [0, b]])

    # 1. Algebraic multiplicity sum must equal matrix dimension (2)
    eigs = M.eigenvals(simplify=True)
    assert sum(eigs.values()) == 2

    # 2. Matrix must NOT be diagonalizable
    assert M.is_diagonalizable() is False

    # 3. Jordan form transformation matrix P must be non-singular
    P, J = M.jordan_form()
    assert simplify(P.det()) != 0
    assert simplify(M * P - P * J) == Matrix.zeros(2, 2)


def test_eigenvals_simplify_edge_cases():
    """Edge cases: Monolithic 4x4 spectrum collapse, 3x3 Jordan block, 1x1 boundary."""
    x = Symbol("x")
    e1 = sin(x)**2
    e2 = 1 - cos(x)**2
    e3 = (1 - cos(2*x)) / 2

    # Case 1: Monolithic 4x4 collapse (All 4 entries map to sin²(x))
    M_mono = Matrix.diag(e1, e2, e3, e1)
    eigs_mono = M_mono.eigenvals(simplify=True)
    assert eigs_mono == {sin(x)**2: 4}

    # Case 2: 3x3 Defective Jordan Block
    M_j3 = Matrix([
        [e1, 1, 0],
        [0, e2, 1],
        [0, 0, e3]
    ])
    P3, J3 = M_j3.jordan_form()
    assert simplify(P3.det()) != 0
    assert simplify(M_j3 * P3 - P3 * J3) == Matrix.zeros(3, 3)

    # Case 3: 1x1 Boundary
    M_1x1 = Matrix([1 - cos(x)**2])
    assert M_1x1.eigenvals(simplify=True) == {sin(x)**2: 1}
```

---

## 04. Execution & Verification Evidence

### 1. Pytest Results:
```sh
py -m pytest sympy/matrices/tests/test_eigen.py -v
```
**Output:**
```
======================= 22 passed, 3 deselected, 1 xfailed in 18.67s =======================
```
- `test_eigenvals_simplification_preserves_multiplicity`: **PASSED**
- `test_eigenvals_simplify_multiplicity_and_jordan`: **PASSED**
- `test_eigenvals_simplify_edge_cases`: **PASSED**
- All 19 pre-existing regression tests in `test_eigen.py`: **PASSED**

### 2. Linter & Static Analysis:
```sh
ruff check sympy/matrices/eigen.py sympy/matrices/tests/test_eigen.py
```
**Output:**
```
All checks passed!
```

---

## 05. Comprehensive Deliverables Roster

| Deliverable Artifact | Type & Path | Role & Verification Function |
| :--- | :--- | :--- |
| **`sympy/matrices/eigen.py`** | Core Engine Source | Main patched SymPy file implementing Defect M3-1 additive multiplicity accumulator (`_eigenvals_dict`), eigenvector simplification sync (`_eigenvects_sympy`), and Defect M3-2 zero-difference root merge + full-rank guard (`_jordan_form`). |
| **`sympy/matrices/tests/test_eigen.py`** | Unit Test Suite | Official test file containing all 3 custom regression suites verifying multiplicity preservation, defective Jordan similarity, and monolithic spectrum edge cases. |
| **`sympy/release.py` & `_version.py`** | Cloud Resilience | Eliminates shallow-clone `ImportError` exceptions on cloud runners (Streamlit Cloud, Docker, Colab) by providing static development fallback metadata. |
| **`app_prototype.py`** | Live Interactive UI | Streamlit Web Inspector featuring real-time spectrum comparison, the shopping-cart iteration tracer, neon math operator celebration burst, and instant in-memory test runner (<25ms). |
| **`MATCH_ZERO_LIVE_INSPECTOR.ipynb`** | 1-Click Cloud Notebook | Interactive Google Colab notebook executing the full verification pipeline in Google Cloud with 1 click (zero local setup required). |
| **`verify_integration.py`** | Mainline Proof Script | Zero-dependency standalone Python verification script that introspects the loaded SymPy source, tests public APIs (`M.eigenvals(simplify=True)`, $\det(P) \neq 0$), and runs the test runner in <2 seconds. |
| **`requirements.txt`** | Dependency Manifest | Clean, modular dependency specification separating core runtime, developer testing, and prototype visualization tools. |
| **`INTEGRATION_PROOF.md`** | Architecture Dossier | Technical document demonstrating the exact dispatch call graph from public `MatrixBase` methods to our patched functions in `eigen.py`. |
| **`README-MACHZERO.md`** | Central Team Log | Master team log tracking Rounds 1–3, mathematical contracts, semantic model definitions (`📦` vs `🚀`), and before/after code walkthroughs. |
| **`MATCH_ZERO_TECHNICAL_ROUND_DOSSIER.md`** | Theoretical Dossier | Transcribed 6-page technical dossier covering the shopping-cart dictionary model, failure analysis, and mathematical defense. |
| **`QUICKSTART.md`** | Evaluator Guide | 1-minute quickstart guide for competition judges and teammates. |
| **`prototype_demo.py`** | Terminal CLI Prototype | Lightweight, standalone command-line demonstration for offline terminal environments. |
| **`RUN_WEB_PROTOTYPE.bat`** | Windows Shortcut | 1-click desktop batch launcher for the Streamlit web dashboard. |
| **`RUN_TERMINAL_DEMO.bat`** | Windows Shortcut | 1-click desktop batch launcher for the CLI terminal demonstration. |
| **`match_zero_sympy_issue_30900.patch`** | Unified Git Patch | Standard unified Git patch allowing anyone to apply the complete fix to any clean SymPy checkout with `git apply`. |
| **`MATCH_ZERO_SYMPY_SUBMISSION_BUNDLE.zip`** | Offline Archive | Self-contained 53.8 KB distribution zip bundle holding all above files for offline evaluation. |

---

## 06. Libraries, Packages & Environment Specifications

The following table documents every third-party package, runtime dependency, and Python standard library module utilized during the engineering of this project:

### 1. Third-Party Libraries & External Packages

| Library / Tool | Installed Version | Scope | Purpose & Modules Utilized | Mandatory? |
| :--- | :--- | :--- | :--- | :--- |
| **`python`** | `3.14.0` (Tested $\ge 3.10$) | Core Runtime | Execution environment for the entire pure-Python SymPy computer algebra system. | **Yes** |
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

## 07. Multi-Workspace Access & Live Cloud Execution Links

Judges can inspect and run the solution through multiple channels across any workspace (Cloud, Browser, or Local Terminal):

### 🚀 1. Live Cloud Web App (Streamlit Community Cloud)
- **Direct Live Link:** [https://match-zero-sympy-30900.streamlit.app](https://match-zero-sympy-30900.streamlit.app)
- **Instant Browser Access:** Zero setup required. Runs the interactive dashboard with the math operator celebration burst and spectrum comparisons directly in your browser.

### 🌐 2. One-Click Interactive Cloud Notebook (Google Colab)
Judges can run the live verification in Google Cloud without installing anything locally:
- **Colab Link:** [Open in Google Colab](https://colab.research.google.com/github/arushigarg2709-git/sympy/blob/fix/eigenvals-missing-multiplicity-jordan/MATCH_ZERO_LIVE_INSPECTOR.ipynb)
- **File:** [MATCH_ZERO_LIVE_INSPECTOR.ipynb](file:///C:/Users/hp/.gemini/antigravity/scratch/sympy/MATCH_ZERO_LIVE_INSPECTOR.ipynb)

### 💻 3. Running in Any Judge Workspace (GitHub Codespaces / Mac / Linux / Windows)
If inspecting from a remote workspace or local machine:
```bash
# 1. Clone the verified branch
git clone https://github.com/arushigarg2709-git/sympy.git -b fix/eigenvals-missing-multiplicity-jordan
cd sympy

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the interactive web inspector
streamlit run app_prototype.py
```
*(In GitHub Codespaces / VS Code Remote, port 8501 is automatically forwarded to a private HTTPS preview link).*

### ⚡ 4. Zero-Dependency Terminal Verification Script (<2 seconds)
For an instantaneous verification that tests public APIs and test suites:
```bash
python verify_integration.py
```

### 🖥️ 5. Interactive Web Inspector Features (`app_prototype.py`)
- **Title:** `🧮 SymPy Issue #30900 · Missing Eigenvalue Fix`
- **Features:**
  - Top 4-KPI Scoreboard (Dimension, Legacy Model Loss, Upgraded Model Recovery, Contract Status).
  - Interactive Run Buttons (`🚀 Run Live Spectrum Audit`, `🚀 Verify Jordan Similarity`, `⚡ Run Tests`).
  - Answers and cards stay hidden/locked until the judge clicks the Run button.
  - **Floating Neon Math Operator Burst**: Spawns 70 luminous animated operator particles (`+`, `=`, `XOR`, `÷`, `/`, `⊕`, `×`, `−`, `∑`, `λ`) on successful contract verification.
  - **Case-Insensitive Math Normalization**: Automatically normalizes user inputs like `Cosx`, `Cost`, `sin^2 x`, `1 - Cosx**2` into canonical SymPy expressions.
  - Zero horizontal scrolling: Compact table formatting in Tab 1 and stacked Visual Iteration Cards in Tab 2.
  - Instant In-Memory Test Runner (<25ms) in Tab 4.

### 📟 6. Automated Terminal CLI Demonstration (`prototype_demo.py`)
- **Launch Command:** `python prototype_demo.py` or double-click `RUN_TERMINAL_DEMO.bat`.
