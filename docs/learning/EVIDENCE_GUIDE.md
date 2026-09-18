# Examine a claim

Start with the statement you want to evaluate. Name its domain and decide what
kind of support could establish it. You can read the review method before working
through every mathematical derivation.

[Follow the claim-evaluation route](routes/claims.md) |
[Repair a mathematical gap](METHOD_FINDER.md) |
[Choose another purpose](README.md)

## Read the label and its boundary

| Label | What to inspect beside the claim | Follow the support |
|---|---|---|
| Definition | Objects, domain, and convention | The definition and its cited mathematical source |
| Established result | Hypotheses, conclusion, and proof or precise reference | [Mathematical baseline](../../papers/sections/review_mathematical_baseline.tex) and [bibliography](../../papers/references.bib) |
| Computational observation | Exact inputs, method, output, tolerance, and finite scope | [Computational portfolio](../../papers/sections/review_computational_evidence.tex), then its named retained artifact |
| Conjecture or open hypothesis | Testable statement, controls, and possible rejection | [Hypothesis registry](../../data/registry/hypothesis_registry.json), search the named hypothesis ID |
| Falsified within the stated scope | Tested statement, counterexample or decision rule, and limits on generalization | [Canonical dispositions](../../data/registry/unified_framework_claims.json) and [independent reproduction records](../../data/registry/independent_reproduction_registry.json) |

The visible label expresses an evidence class, while a registry status records a
particular claim's disposition. Read both. An unsupported claim differs from a
falsified statement; failure to satisfy a positive decision rule can leave
individual component effects unresolved.

## Work through two different negative decisions

**An algebraic specificity claim.** The review reports exact equality between the
quadratic-defect selector and a generic checkerboard kernel at the registered
radii. Equality defeats the registered specificity claim in those cases. Search
`hyp_e7_nonhomomorphic_fourier_selector` in the
[hypothesis registry](../../data/registry/hypothesis_registry.json) for the
statement, then in the [reproduction registry](../../data/registry/independent_reproduction_registry.json)
for the retained repeat. Read the [review's promotion rule](../../papers/sections/review_hypothesis_registry.tex)
for the interpretation boundary. The computation supplies a finite equality
result; a broader physical mechanism needs its own evidence.

**A fluid-model decision.** The preregistered freely decaying beta-plane study
misses its locked transient-zonalization conjunction. Search
`hyp_beta_plane_transient_zonalization` in the same two registries. The negative
decision concerns that model, selector, contrasts, and thresholds. It does not
establish impossibility of forced-dissipative jets or exclude every component
effect separately. [Probability](lessons/probability.md) explains conditioning
and controls; [numerical reasoning](lessons/numerical.md) explains approximation.

## Try the distinction

A program checks ten inputs and passes. A reader says the mathematical identity
holds for every real input. Which extra step needs support?

<details><summary>Read the solution</summary>

The program observed the ten declared inputs. A proof covering every real input,
or a justified reduction to a complete finite domain, must support the universal
claim. Numerical agreement alone also needs an error interpretation.

</details>

## Choose a bounded computation

For a first executable task, run the learning-example verifier from the repository
root using Python 3:

```sh
python3 scripts/verify_learning_examples.py --output build/learning/examples.json
```

The expected result is 47 bounded checks across the original ten bridge chapter
snapshots. The output records individual checks and source hashes. The two added
entry chapters have separate source-coupled tests:

```sh
.venv/bin/python -m pytest --noconftest -q -o addopts='' tests/unit/test_learning_entry_examples.py
```

Those tests exercise matrix actions, composition, complex arithmetic, and
normalization; they do not certify every sentence. For a research reproduction,
start with the [reproducibility appendix](../../papers/sections/review_reproducibility.tex)
and the exact command and environment recorded for the chosen hypothesis.
Opening a retained result and rerunning its computation are different tasks.

The [authority guide](../framework/AUTHORITY_SURFACES.md) identifies the owners
of claim status, consistency contracts, hypotheses, and promotion evidence.
Historical source and reconstruction labels remain a separate distinction in
the teaching chapters. Their [audit](AUDIT.md) records source-access limits.
