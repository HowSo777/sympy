# Match Zero · Quickstart Guide for Teammates & Judges

Welcome to the Match Zero project for SymPy Issue #30900: **Missing Eigenvalue Fix**!

## Included Files in this Bundle
1. `README-MACHZERO.md` - Complete team log, Round 1-3 progress, mathematical contracts, and exact Before vs After code blocks.
2. `MATCH_ZERO_TECHNICAL_ROUND_DOSSIER.md` - Technical dossier covering the shopping-cart model and root cause analysis.
3. `app_prototype.py` - Streamlit Web Dashboard: **SymPy Issue #30900 · Missing Eigenvalue Fix**.
4. `prototype_demo.py` - Standalone CLI terminal demonstration (zero external dependencies).
5. `RUN_WEB_PROTOTYPE.bat` - 1-Click launcher for the Streamlit Web Dashboard.
6. `RUN_TERMINAL_DEMO.bat` - 1-Click launcher for the CLI Terminal Demo.
7. `match_zero_sympy_issue_30900.patch` - Standard Git patch containing commits 6672955 and 9222443.
8. `requirements.txt` - Dependency specification (core, dev, presentation).
9. `verify_integration.py` - Zero-dependency live mainline integration verification script.
10. `INTEGRATION_PROOF.md` - Mainline architectural call dispatch and verification guide.
11. `sympy/matrices/eigen.py` - Patched SymPy source file with accumulator and Jordan rank guard.
12. `sympy/matrices/tests/test_eigen.py` - Regression test suite (3 new tests, 22 total passing).

---

## How to Run

### Option 1: Interactive Web Dashboard (Recommended for Presentations)
Double-click `RUN_WEB_PROTOTYPE.bat` or run:
```bash
pip install -r requirements.txt
streamlit run app_prototype.py
```
Open your browser at `http://localhost:8501`.

### Option 2: Live Mainline Integration Verification Script (<2s)
```bash
python verify_integration.py
```

### Option 3: Standalone Terminal CLI Demo
Double-click `RUN_TERMINAL_DEMO.bat` or run:
```bash
python prototype_demo.py
```

### Option 4: Apply Git Patch to Existing SymPy Repository
```bash
git apply match_zero_sympy_issue_30900.patch
pytest sympy/matrices/tests/test_eigen.py -v
```

Shared Fork Remote: https://github.com/arushigarg2709-git/sympy.git
Branch: fix/eigenvals-missing-multiplicity-jordan
