"""Run with: python -m streamlit run app.py"""

import streamlit as st
from sympy import Matrix, Symbol, cos, latex, sec, simplify, sin, tan

st.set_page_config(page_title="Match Zero - SymPy Demo", layout="wide")

st.markdown(
    """
    <style>
    .stApp {background: linear-gradient(135deg, #edf6ff, #b7d8ff); color: #12345a;}
    [data-testid="stHeader"] {background: transparent;}
    h1, h2, h3 {color: #153f72;}
    </style>
    """,
    unsafe_allow_html=True,
)

# These strings are also used to display the two functions to the judges.
WRONG_CODE = '''def wrong_code(raw_eigenvalues):
    result = {}diff --git a/sympy/matrices/eigen.py b/sympy/matrices/eigen.py
index 4033d9b..20425e0 100644
--- a/sympy/matrices/eigen.py
+++ b/sympy/matrices/eigen.py
@@ -323,7 +323,11 @@ def _eigenvals_dict(
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
@@ -366,7 +370,7 @@ def _eigenvects_sympy(
         simplify: bool | Callable[[Expr], Expr] = True,
         **flags: Any,
     ) -> list[tuple[Expr, int, list[Tmat]]]:
-    eigenvals = M.eigenvals(rational=False, **flags)
+    eigenvals = M.eigenvals(rational=False, simplify=simplify, **flags)
 
     # Make sure that we have all roots in radical form
     for x in eigenvals:
@@ -1275,6 +1279,18 @@ def pick_vec(small_basis, big_basis):
 
     # first calculate the jordan block structure
     eigs = mat.eigenvals()
+    merged_eigs: dict[Expr, int] = {}
+    for k, v in eigs.items():
+        found = False
+        for mk in merged_eigs:
+            diff = k - mk
+            if diff == 0 or getattr(diff, 'is_zero', False) or _iszero(diff) or _iszero(_simplify(diff)):
+                merged_eigs[mk] += v
+                found = True
+                break
+        if not found:
+            merged_eigs[k] = v
+    eigs = merged_eigs
 
     # Make sure that we have all roots in radical form
     for x in eigs:
@@ -1293,11 +1309,11 @@ def pick_vec(small_basis, big_basis):
         if not calc_transform:
             return restore_floats1(jordan_mat)
 
-        jordan_basis = [eig_mat(eig, 1).nullspace()[0]
-                for eig in blocks]
+        jordan_basis = [ns[0] for eig in blocks if (ns := eig_mat(eig, 1).nullspace())]
         basis_mat    = mat.hstack(*jordan_basis)
 
-        return restore_floats2(basis_mat, jordan_mat)
+        if len(jordan_basis) == mat.cols and basis_mat.rank() == mat.cols:
+            return restore_floats2(basis_mat, jordan_mat)
 
     block_structure = []
 
diff --git a/sympy/matrices/tests/test_eigen.py b/sympy/matrices/tests/test_eigen.py
index e393dc2..7dc06dd 100644
--- a/sympy/matrices/tests/test_eigen.py
+++ b/sympy/matrices/tests/test_eigen.py
@@ -807,3 +807,49 @@ def test_issue_28793():
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
+    assert matrix.eigenvals(simplify=True, multiple=True) == [sin(x)**2, sin(x)**2, sin(x)**2, S(7)]
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
+
+
+def test_eigenvals_simplify_edge_cases():
+    x = Symbol('x')
+    e1, e2, e3 = sin(x)**2, 1 - cos(x)**2, (1 - cos(2*x))/2
+
+    # Edge case 1: Monolithic spectrum where all 4 entries collapse to 1 eigenvalue
+    M_mono = Matrix.diag(e1, e2, e3, e1)
+    assert M_mono.eigenvals(simplify=True) == {sin(x)**2: 4}
+    assert len(M_mono.eigenvals(simplify=True, multiple=True)) == 4
+
+    # Edge case 2: 3x3 defective Jordan block with 3 unsimplified equivalent roots
+    M_jordan3 = Matrix([[e1, 1, 0], [0, e2, 1], [0, 0, e3]])
+    assert M_jordan3.is_diagonalizable() is False
+    P3, J3 = M_jordan3.jordan_form()
+    assert simplify(P3.det()) != 0
+    assert simplify(M_jordan3 * P3 - P3 * J3) == Matrix.zeros(3, 3)
+
+    # Edge case 3: 1x1 boundary matrix
+    M_1x1 = Matrix([[e2]])
+    assert M_1x1.eigenvals(simplify=True) == {sin(x)**2: 1}
+
+
+

    for eigenvalue, count in raw_eigenvalues.items():
        key = simplify(eigenvalue)
        result[key] = count
    return result'''

CORRECT_CODE = '''def correct_code(raw_eigenvalues):
    result = {}
    for eigenvalue, count in raw_eigenvalues.items():
        key = simplify(eigenvalue)
        old_count = result.get(key, 0)
        result[key] = old_count + count
    return result'''

# The wrong function replaces a count when two keys simplify to the same value.
def wrong_code(raw_eigenvalues):
    result = {}
    for eigenvalue, count in raw_eigenvalues.items():
        key = simplify(eigenvalue)
        result[key] = count
    return result


# The correct function adds the counts instead of replacing them.
def correct_code(raw_eigenvalues):
    result = {}
    for eigenvalue, count in raw_eigenvalues.items():
        key = simplify(eigenvalue)
        old_count = result.get(key, 0)
        result[key] = old_count + count
    return result


def show_code():
    left, right = st.columns(2)
    with left:
        st.subheader("Wrong code")
        st.code(WRONG_CODE, language="python")
    with right:
        st.subheader("Correct code")
        st.code(CORRECT_CODE, language="python")


def show_balloons():
    # CSS moves the balloons from the top of the screen to the bottom.
    st.html('''
    <style>
    .balloon-layer {position: fixed; inset: 0; z-index: 99999; pointer-events: none; overflow: hidden;}
    .balloon {position: absolute; top: -120px; width: 42px; height: 54px;
        border-radius: 50%; animation: fall 4s ease-in forwards;}
    .balloon::after {content: ''; position: absolute; top: 54px; left: 21px;
        width: 1px; height: 50px; background: #527192;}
    @keyframes fall {to {transform: translateY(calc(100vh + 240px)) rotate(15deg);}}
    @media (prefers-reduced-motion: reduce) {.balloon {animation-duration: .5s;}}
    </style>
    <div class="balloon-layer" aria-hidden="true">
        <span class="balloon" style="left:10%; background:#ff7d9c;"></span>
        <span class="balloon" style="left:25%; background:#ffd166; animation-delay:.3s;"></span>
        <span class="balloon" style="left:40%; background:#70d6c4; animation-delay:.6s;"></span>
        <span class="balloon" style="left:55%; background:#aa91ff; animation-delay:.2s;"></span>
        <span class="balloon" style="left:70%; background:#ffad66; animation-delay:.5s;"></span>
        <span class="balloon" style="left:85%; background:#69baff; animation-delay:.8s;"></span>
    </div>
    ''')


st.title("Match Zero - SymPy Demonstration")
st.write("Problem: equivalent eigenvalues can lose their counts during simplification.")
st.write("Multiplicity means how many times an eigenvalue occurs.")
st.caption("This app demonstrates both aggregation algorithms. It does not modify your installed SymPy.")

st.header("1. Explain the code before running")
st.write("The original code used a dictionary comprehension:")
st.code("return {simplify(key): value for key, value in all_eigs.items()}", language="python")
st.write("The wrong function below expands that line into a loop so it is easier to explain.")
show_code()
st.write("If two expressions become the same key, the wrong code replaces the earlier count. The correct code adds both counts.")

x = Symbol("x", real=True)
a = sin(x) ** 2
b = 1 - cos(x) ** 2

st.header("2. Choose an example")
example = st.selectbox("Test case", ["4 by 4 matrix", "3 by 3 identity collision", "Distinct eigenvalues"])
if example == "4 by 4 matrix":
    matrix = Matrix.diag(a, a, b, 7)
    expected = {a: 3, 7: 1}
elif example == "3 by 3 identity collision":
    matrix = Matrix.diag(sin(x)**2 + cos(x)**2, sec(x)**2 - tan(x)**2, 1)
    expected = {1: 3}
else:
    matrix = Matrix.diag(2, 5, 7)
    expected = {2: 1, 5: 1, 7: 1}

st.latex("A = " + latex(matrix))
st.write("Expected eigenvalues and counts:", {str(k): v for k, v in expected.items()})
st.write("For these examples, the total count should equal the number of rows.")

if st.button("Run", type="primary"):
    st.header("3. Results")
    raw = matrix.eigenvals(simplify=False)
    wrong = wrong_code(raw)
    correct = correct_code(raw)
    st.write("Raw eigenvalues:", {str(k): int(v) for k, v in raw.items()})
    left, right = st.columns(2)
    with left:
        st.subheader("Wrong result")
        st.write({str(k): int(v) for k, v in wrong.items()})
        st.write("Total count:", sum(wrong.values()))
        if wrong == expected:
            st.info("No collision in this example. The wrong code also gives the expected result.")
        else:
            st.error("The wrong code lost a count.")
    with right:
        st.subheader("Correct result")
        st.write({str(k): int(v) for k, v in correct.items()})
        st.write("Total count:", sum(correct.values()))
        if correct == expected and sum(correct.values()) == matrix.rows:
            st.success("The result matches the expected eigenvalues and counts.")
            show_balloons()
        else:
            st.error("The result did not match the expected answer.")

    st.subheader("Step by step")
    trace = []
    old_result = {}
    new_result = {}
    for eigenvalue, count in raw.items():
        key = simplify(eigenvalue)
        previous = new_result.get(key, 0)
        old_result[key] = count
        new_result[key] = previous + count
        trace.append({
            "Raw eigenvalue": str(eigenvalue),
            "Simplified key": str(key),
            "Incoming count": int(count),
            "Wrong count after step": int(old_result[key]),
            "Correct count after step": int(new_result[key]),
        })
    st.table(trace)

    st.header("4. Show the code again at the end")
    show_code()
    st.write("Conclusion: replace the count assignment with count addition.")

st.divider()
st.header("5. Jordan form example")
st.write("This separate example explains the second defect: repeated equivalent roots can produce duplicate basis columns.")
if st.button("Run Jordan example"):
    m = Matrix([[a, 1], [0, b]])
    bad_p = Matrix([[1, 1], [0, 0]])
    st.write("Matrix under test")
    st.latex(latex(m))
    st.write("Illustration of the wrong basis: duplicate columns")
    st.latex(latex(bad_p))
    st.write("Its determinant is", bad_p.det(), "so it cannot be inverted.")
    # This reference is valid for this particular example only.
    p = Matrix.eye(2)
    j = Matrix([[a, 1], [0, a]])
    residual = (m * p - p * j).applyfunc(simplify)
    st.write("Correct reference basis P and Jordan matrix J")
    st.latex("P = " + latex(p) + r",\quad J = " + latex(j))
    st.write("det(P) =", p.det())
    st.write("M P - P J is zero:", residual == Matrix.zeros(2))
    st.caption("This is an analytical reference for this example, not a general Jordan-form patch. The exact submitted library changes are included in the ZIP.")
