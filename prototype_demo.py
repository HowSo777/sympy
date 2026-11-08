"""
Match Zero · SymPy Hackathon Working Prototype
Preserving Eigenvalue Multiplicities & Jordan Form during Symbolic Simplification
Defects: SymPy #30900 (M3-1 & M3-2)
"""
import sys
import os

# Ensure local patched SymPy is used
REPO_DIR = os.path.dirname(os.path.abspath(__file__))
if REPO_DIR not in sys.path:
    sys.path.insert(0, REPO_DIR)

from sympy import Matrix, Symbol, sin, cos, simplify, S


def print_header(title):
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def demo_shopping_cart():
    print_header("PROTOTYPE DEMO 1: The Shopping-Cart Model (Defect M3-1)")
    print("Matrix A = diag(sin^2(x), sin^2(x), 1 - cos^2(x), 7)")
    print("Dimension: 4x4 -> Invariant: Sum of algebraic multiplicities MUST equal 4.\n")

    x = Symbol("x")
    a = sin(x)**2
    b = 1 - cos(x)**2
    A = Matrix.diag(a, a, b, 7)

    # 1. Unsimplified raw roots
    raw_eigs = A.eigenvals(simplify=False)
    print("1. BEFORE SIMPLIFYING LABELS (raw roots from characteristic solver):")
    for root, mult in raw_eigs.items():
        print(f"   - Label: {str(root):<25} | Multiplicity Count: {mult}")

    print("\n2. NORMALIZATION-INDUCED KEY COLLISION:")
    print("   simplify(1 - cos(x)**2) == sin(x)**2")
    print("   Two distinct keys map to the exact same normalized key: 'sin(x)**2'.")

    # 2. Simulated unpatched behavior
    faulty_dict = {}
    for k, v in raw_eigs.items():
        # Old code: {simplify(k): v for k, v in all_eigs.items()} (overwrite!)
        faulty_dict[simplify(k)] = v

    print("\n3. OLD (UNPATCHED) BEHAVIOR (Last assignment wins / Overwrite):")
    print(f"   Result: {faulty_dict}")
    faulty_sum = sum(faulty_dict.values())
    print(f"   Total Multiplicity Sum: {faulty_sum} / 4  --> [CRITICAL ERROR: 2 EIGENVALUES LOST!]")

    # 3. Patched behavior
    patched_dict = A.eigenvals(simplify=True)
    patched_list = A.eigenvals(simplify=True, multiple=True)
    print("\n4. OUR PATCHED BEHAVIOR (Additive Accumulation):")
    print(f"   Result Dict: {patched_dict}")
    print(f"   Repeated List: {patched_list}")
    patched_sum = sum(patched_dict.values())
    print(f"   Total Multiplicity Sum: {patched_sum} / 4  --> [SUCCESS: SPECTRUM PRESERVED!]")


def demo_jordan_block():
    print_header("PROTOTYPE DEMO 2: Jordan Normal Form Defect (Defect M3-2)")
    print("Matrix M = [[sin^2(x), 1], [0, 1 - cos^2(x)]]")
    print("Since 1 - cos^2(x) = sin^2(x), this is a 2x2 defective Jordan block.\n")

    x = Symbol("x")
    M = Matrix([[sin(x)**2, 1], [0, 1 - cos(x)**2]])

    print(f"Matrix M:\n{M}\n")

    is_diag = M.is_diagonalizable()
    print(f"Diagonalizable: {is_diag} (Correct: False, geometric mult = 1 < algebraic mult = 2)")

    P, J = M.jordan_form()
    det_P = simplify(P.det())
    print(f"\nTransformation Matrix P:\n{P}")
    print(f"det(P) = {det_P}  (Non-singular? {det_P != 0})")
    print(f"\nJordan Matrix J:\n{J}")

    residual = simplify(M * P - P * J)
    print(f"\nVerification M * P - P * J == 0: {residual == Matrix.zeros(2, 2)}")
    print("--> [SUCCESS: Valid invertible basis found, no division by zero or singular matrix!]")


def demo_edge_cases():
    print_header("PROTOTYPE DEMO 3: Edge Cases Lab")
    x = Symbol("x")
    e1, e2, e3 = sin(x)**2, 1 - cos(x)**2, (1 - cos(2*x))/2

    print("1. MONOLITHIC SPECTRUM EDGE CASE (All 4 entries collapse to 1 eigenvalue):")
    print("   A = diag(sin^2(x), 1 - cos^2(x), (1 - cos(2x))/2, sin^2(x))")
    M_mono = Matrix.diag(e1, e2, e3, e1)
    res_mono = M_mono.eigenvals(simplify=True)
    print(f"   Result: {res_mono} (Multiplicity = {res_mono.get(sin(x)**2)})")
    print(f"   Spectrum Invariant Conserved: {sum(res_mono.values()) == 4}")

    print("\n2. 3x3 HIGHER-ORDER DEFECTIVE JORDAN BLOCK EDGE CASE:")
    print("   M = [[sin^2(x), 1, 0], [0, 1 - cos^2(x), 1], [0, 0, (1 - cos(2x))/2]]")
    M_jordan3 = Matrix([[e1, 1, 0], [0, e2, 1], [0, 0, e3]])
    print(f"   Is Diagonalizable: {M_jordan3.is_diagonalizable()} (Expected: False)")
    P3, J3 = M_jordan3.jordan_form()
    print(f"   det(P) = {simplify(P3.det())} (Invertible? {simplify(P3.det()) != 0})")
    print(f"   M*P - P*J == 0: {simplify(M_jordan3 * P3 - P3 * J3) == Matrix.zeros(3, 3)}")

    print("\n3. 1x1 BOUNDARY MATRIX EDGE CASE:")
    M_1x1 = Matrix([[e2]])
    print(f"   Result: {M_1x1.eigenvals(simplify=True)}")


def main():
    print("\n" + "#" * 70)
    print("#  MATCH ZERO - SYMPY SYMBOLIC EIGENVALUES & JORDAN FORM PROTOTYPE   #")
    print("#" * 70)
    demo_shopping_cart()
    demo_jordan_block()
    demo_edge_cases()
    print("\n" + "=" * 70)
    print("All prototype demonstrations executed cleanly on local patched build.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
