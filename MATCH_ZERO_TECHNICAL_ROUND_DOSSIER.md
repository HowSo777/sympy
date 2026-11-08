# MATCH ZERO | TECHNICAL ROUND DOSSIER
**Date:** 07 NOV 2026  
**Project:** Preserving eigenvalue multiplicities during symbolic simplification in SymPy  
**Reported Defect:** [SymPy Issue #30900, item M3-1](https://github.com/sympy/sympy/issues/30900)  
**Shared Fork:** [github.com/arushigarg2709-git/sympy](https://github.com/arushigarg2709-git/sympy)  

---

## Page 1 · Round 1: Missing Eigenvalue

### MISSING EIGENVALUE.
**Preserving eigenvalue multiplicities during symbolic simplification in SymPy**

> **Technical thesis:** When normalization maps several symbolic keys to one key, their multiplicities must be accumulated. Rebuilding a dictionary by replacement silently destroys information.

### 01) Problem selection and thought process
We selected reported defect M3-1 from the SymPy matrix audit because a diagonal matrix gives us a direct way to verify the expected eigenvalue counts. We traced the failure to simplification and focused our fix on the exact point where multiplicities were lost.

### The mathematical contract
For $A = \operatorname{diag}(a, a, b, 7)$, let $a = \sin^2(x)$ and $b = 1 - \cos^2(x)$. The identity $b = a$ makes the eigenvalue $a$ occur three times. Its algebraic multiplicity is 3: the characteristic polynomial has the factor $(t - a)^3$.

> [!IMPORTANT]
> **Invariant:** For this complete 4-by-4 spectrum, the multiplicities must sum to 4. The faulty result sums to 2. The corrected result sums to 4.

*Prepared from the supplied team log, dated 7 November 2026. Round 2 results are reported evidence. Round 3 completion is not yet documented.*

---

## Page 2 · Round 1: The Shopping-Cart Model

### The shopping-cart model
**Same mathematical item. Different labels. One combined count.**

### 1) Before simplifying the labels

| Cart entry | Label | Count |
| :--- | :--- | :---: |
| Box 1 | `sin(x)**2` | 2 |
| Box 2 | `1 - cos(x)**2` | 1 |
| Separate item | `7` | 1 |

Think of each dictionary entry as a product label and a quantity. Before simplification, the two trigonometric expressions are structurally different keys even though they denote the same value.

### 2) Normalize the keys
For this example, `simplify()` turns `1 - cos(x)**2` into `sin(x)**2`. Both boxes now carry the same label. This is a **normalization-induced key collision**: two inputs map to one output key.

### 3) Why replacement loses items
The old construction first stores the count 2 under `sin(x)**2`. When the second expression simplifies to that same key, assignment stores 1 at the existing key and erases 2. No exception is raised, so the output looks valid while its count is wrong.

### 4) Add the quantities
The corrected aggregation starts from zero for an unseen label and adds every incoming count. Existing count 2 + incoming count 1 = 3. The separate eigenvalue 7 retains count 1.

| Result | `sin(x)**2` | `7` | Total |
| :--- | :---: | :---: | :---: |
| Faulty output in the log | 1 | 1 | 2 |
| Correct output | 3 | 1 | 4 |

> [!TIP]
> **Judge-ready line:** *"Simplification changes the labels, not the number of items. Our fix preserves the count when labels merge."*

---

## Page 3 · Round 2: Locate the Information Loss

### Locate the information loss
**From a public eigenvalue call to the final aggregation boundary**

### 02) Execution path
`Matrix.eigenvals(simplify=True)` delegates through `matrixbase.py` to the eigenvalue implementation in `sympy/matrices/eigen.py`. In the relevant path, `_eigenvals_dict` has already collected roots and their multiplicities. The final simplification step transforms the keys.

The upstream source inspected for this report ends that path with a dictionary comprehension. A comprehension can transform keys, but repeated keys retain only the last assigned value. It performs no multiplicity reduction.

### Old behavior versus corrected behavior

| Dimension | Old (wrong) behavior | Corrected behavior |
| :--- | :--- | :--- |
| **Key transformation** | Simplify each eigenvalue key. | Simplify each eigenvalue key once. |
| **Collision handling** | Replace the earlier count. | Add to the existing count. |
| **Meaning** | Last assignment wins. | Weighted aggregation by simplified key. |
| **Order sensitivity** | A colliding count can depend on insertion order. | For the same simplified keys, integer sums are order independent. |
| **Cost after simplification** | One dictionary insertion per entry. | One lookup and update per entry with the same linear traversal. |

### Technical interpretation
Simplify the keys, then sum their counts. This weighted aggregation preserves multiplicity when equivalent expressions merge.

*For $n$ entries and $u$ simplified keys: $O(n)$ dictionary operations and $O(u)$ output space, excluding simplification cost. Only keys made identical by the simplifier are merged.*

---

## Page 4 · Round 2: The Corrected Implementation

### The corrected implementation
**Only fixed code is displayed. The preceding table explains the wrong behavior.**

### 03) Replacement for the final simplification block
Place this block inside `_eigenvals_dict`, after `all_eigs` has been computed. It preserves the existing no-simplification path and the FunctionType-based simplifier selection. `_simplify` and `FunctionType` are existing module imports. This is a proposed replacement block, not a verified extraction of the local commit.

```python
if not simplify:
    return all_eigs
if not isinstance(simplify, FunctionType):
    simplify = _simplify

simplified_eigs = {}
for eigenvalue, multiplicity in all_eigs.items():
    key = simplify(eigenvalue)
    simplified_eigs[key] = (
        simplified_eigs.get(key, 0) + multiplicity
    )
return simplified_eigs
```

### Why each operation matters
- **Normalize:** compute the target key once per entry.
- **Initialize:** `get(key, 0)` supplies the additive identity for a new key.
- **Reduce:** add the full incoming multiplicity, rather than incrementing by one.
- **Return:** retain the eigenvalue-to-count dictionary contract.

### Regression case to run on the patched checkout

```python
from sympy import Matrix, Symbol, cos, sin

x = Symbol("x")
a = sin(x)**2
matrix = Matrix.diag(a, a, 1 - cos(x)**2, 7)
expected = {a: 3, 7: 1}

assert matrix.eigenvals(simplify=True) == expected
values = matrix.eigenvals(simplify=True, multiple=True)
assert len(values) == 4
assert values.count(a) == 3
assert values.count(7) == 1
```

*Unequal merging counts (2 and 1) expose overwrite loss. The separate value 7 detects accidental over-merging. List checks validate count expansion without depending on eigenvalue order.*

---

## Page 5 · Round 2: Failures, Evidence, Decisions

### Failures, evidence, decisions
**Separate the algorithmic defect from setup and delivery issues.**

| Failure or obstacle | Diagnosis and response |
| :--- | :--- |
| **Silent multiplicity loss** | Normalization merged distinct dictionary keys. Replace overwrite semantics with additive accumulation. |
| **Earlier candidate expanded in scope** | The transpose fix exposed a separate multiplication/indexing error. Select the smaller eigenvalue defect for a focused contribution. |
| **Source archive lacked Git metadata** | We set up a full clone and fetched upstream release tags for development version identification (recorded in our log). |
| **Existing tests passed on faulty code** | Coverage did not capture unequal counts merging after simplification. Add a targeted regression with an independent count oracle. |
| **New regression failed before the fix** | We recorded count 1 where 3 was expected. This connects the new test to the actual defect. |
| **HTTPS push was rejected** | Password authentication failed. A local commit does not establish remote publication or a pull request. |

### Reported validation - not rerun for this PDF
Our supplied log reports: **20 passed, 1 expected failure, 3 deselected** in the focused suite, and Ruff passing on both changed files. It also reports dictionary and repeated-list checks passing after the change. These results are our recorded evidence, not a fresh execution in this document workspace.

**Local reference:** branch `fix/eigenvalue-multiplicity`, commit `6e82712026`. The actual checkout and commit were not supplied here, so the exact committed diff has not been verified.

### Evidence boundary
The original defect and the documented fix concern multiplicity aggregation. Jordan form and downstream machine-learning pipelines were outside the recorded validation. Do not claim benchmark gains, broad downstream correctness, upstream acceptance, or completed publication from these results.

---

## Page 6 · Round 3: Defend, Verify, Hand Off

### Defend, verify, hand off
**Presentation and completion plan - Round 3 outcomes remain pending.**

### 04) A clear technical defense
- **What failed?** A many-to-one symbolic transformation was followed by replacement instead of aggregation.
- **Why is the answer 3?** Three diagonal entries are mathematically equal; the corresponding characteristic factor has exponent 3.
- **Why is the fix local?** The solver already found the counts. The loss occurs at the final key-normalization boundary.
- **Why add the multiplicity?** An entry may represent several roots, so adding only 1 would still undercount.
- **What does the test prove?** It targets this collision case and verifies both public result formats. It does not establish all symbolic equivalences.

### Round 3 verification and release gates
1. Inspect the committed diff and run the targeted regression, full eigenvalue test module, and Ruff in the development checkout.
2. Verify the fix branch exists on the shared fork, open a review PR and record its link and exact commit.
3. Confirm teammate collaborator access and the event submission receipt.
4. Record the reviewer, date, checks, unresolved limitations, and final status. Mark each item complete only after evidence exists.

### Suggested closing statement
> *"Our contribution fixes a silent counting error in symbolic eigenvalue simplification. We traced the loss to a dictionary-key collision, changed the reduction to preserve multiplicities, and documented a regression that fails before the fix and passes after it. The change is small because we repair the exact boundary where information disappears."*

### Sources and submission integrity
- **Primary project record:** supplied `README-MACHZERO.md`, dated 7 November 2026. It reports the local implementation and Round 2 checks. OpenAI Codex assisted the implementation, regression test, and documentation. Include the applicable AI disclosure and human review in the submission.
- **Shared fork:** [github.com/arushigarg2709-git/sympy](https://github.com/arushigarg2709-git/sympy)
- **Reported defect:** SymPy issue [#30900](https://github.com/sympy/sympy/issues/30900), M3-1
- **Source inspected for the final dictionary construction:** `sympy/matrices/eigen.py` (upstream master). Master is mutable. Verify the submission checkout separately.
