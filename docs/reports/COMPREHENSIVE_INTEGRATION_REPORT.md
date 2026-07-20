# Evidence-Bounded Integration Report

## Authority

The canonical Python package is `src/mathphysics`. The canonical framework is
`docs/framework/UNIFIED_EVIDENCE_FRAMEWORK.md`, backed by
`data/registry/unified_framework_claims.json`. The review paper is
`papers/main.pdf`; its generated tables and figures come from the registries.

This report replaces completion language that treated implemented code,
numerical output, and physical validation as interchangeable. They are not.
An implementation proves only that a specified computation ran. A physical
claim also needs a defined intervention, observable, control, uncertainty
model, and preregistered admission threshold.

## Integrated Results

| Surface | Resolved result | Durable evidence |
|---|---|---|
| Exceptional roots | E6, E7, E8, and F4 root counts, positive roots, Cartan data, and Coxeter numbers use executable root-system gates. | `src/mathphysics/algebras/roots.py`, `tests/unit/test_roots.py` |
| E-series extensions | E9 is affine; E10 is hyperbolic; E11 is indefinite. Physics transfers remain bounded literature claims. | `data/registry/exceptional_group_scope_audit.json` |
| Cayley-Dickson ladder | Dimension doubling is implemented through 1024 dimensions. Algebraic property loss and an exact sedenion zero divisor are explicit. No physical observable follows from dimension alone. | `data/registry/cayley_dickson_property_audit.json` |
| Albert algebra | The carrier is a 3 by 3 Hermitian octonionic matrix. Sedenion and pathion substitutions are rejected. | `src/mathphysics/algebras/jordan.py`, `tests/unit/test_jordan_algebra.py` |
| Fourier quotient | The proposed square-invariant Fourier map does not remove exact triads and therefore fails as a selective interaction mechanism. | `data/registry/fourier_quotient_audit.json` |
| Beta-plane study | The matched beta control produces a nonzero fluid response. The algebraic quotient arm is an exact negative control, and the short runs do not establish persistent jets. | `data/registry/beta_plane_ablation_results.json` |
| Physical proposals | Six proposal families have explicit admission packages. None is admitted as experimentally established. | `data/registry/experimental_admission_packages.json` |
| Claim review | Every durable paper claim routes to an evidence-bearing checker. | `data/registry/claim_gate_results.json` |

## Document and Research Integration

The retained framework corpus contains eight source documents. It is decomposed
into 564 bounded ASCII reading chunks covering 200,920 source lines. The aligned
research corpus contains 37 PDFs and 986 pages. MinerU provides the primary CUDA
decomposition; page-selective 400 DPI Tesseract output is retained only where
the native-text audit requires a fallback.

Exact source bytes remain authoritative. Normalized views carry source paths,
line ranges, and hashes. The overlap audit found no exact whole-document
duplicates, so integration occurs claim by claim rather than by deleting source
documents that merely discuss similar topics.

## Reconciled Incoming Synthesis

An incoming synthesis lane proposed four rhetorical tiers and a second package
under `experiments/src`. The tier idea is retained in stronger form as five
evidence layers: defined objects, typed bridge maps, reproducible computation,
physical hypotheses, and excluded or historical ideation.

The second package is not retained in the live tree. It duplicated canonical
modules, failed the repository lint contract, required an unconfigured Qiskit
test lane, and asserted unmeasured fidelity, amplification, coverage, hardware
readiness, and production readiness. Git history preserves that rejected input.
The live verifier rejects a future `experiments/src` shadow package.

## Verification Contract

Run the integrated checks from the repository root:

```bash
make lint
make check-types
make test
python scripts/run_claim_gates.py
make papers
make verify-offline
git diff --check
```

Qiskit-dependent tests skip when Qiskit is not installed. A skip is an explicit
environment boundary, not evidence of quantum-hardware execution.

## Remaining Boundaries

- No quantum circuit in this repository establishes a physical E7-to-hardware
  correspondence merely because both surfaces use the number 127.
- No simulation establishes vacuum-energy extraction, scalar gravity, novel
  materials behavior, or biological effects.
- No short decaying beta-plane run establishes a persistent zonal jet.
- Novel hypotheses remain useful only while their null model, falsifier, and
  admission package remain visible.

The integrated framework is therefore stronger than the prior documents because
negative results, rejected mappings, and unresolved hypotheses remain durable
parts of the model instead of being rewritten as completion claims.
