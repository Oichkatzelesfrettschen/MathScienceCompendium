# A lattice-Boltzmann step has exact moment obligations

[Start here](../README.md) | [Method finder](../METHOD_FINDER.md) | [Evidence guide](../EVIDENCE_GUIDE.md)

**You are here:** From Precalculus to Mathematical Physics / teaching

**Question:** Which moments must a lattice rule conserve?

[Read the source](../../../papers/learning/chapters/advanced.tex). In the separate PDF, open **A lattice-Boltzmann step has exact moment obligations** in **From Precalculus to Mathematical Physics**. The built album directory supplies the verified physical page and PDF link.

## Bring forward

[Numerical reasoning: approximation with an error budget](numerical.md)

**Helpful background:** Continuum mechanics helps interpret a hydrodynamic limit.

## What you will learn

- Check discrete moments and distinguish conservation from convergence.

## Entry check

Explain the difference between roundoff and truncation.

<details><summary>Check your entry answer</summary>

Roundoff comes from finite arithmetic; truncation comes from replacing a limiting operation by a finite approximation.

</details>

**If a step is unfamiliar:** [Numerical reasoning: approximation with an error budget](numerical.md).

## Practice and readiness

At rest, D2Q9 weights are 4/9, four copies of 1/9, and four copies of 1/36. Check their sum and first moment.

<details><summary>Read the worked readiness solution</summary>

The sum is 4/9+4/9+1/9=1. Opposite velocities have equal weights, so each component of the first moment cancels.

</details>

Continue when you can explain the operations and assumptions as well as the value. Otherwise revisit the lesson method and try its solved practice.

## Quick reference

**Use:** Check discrete moments and distinguish conservation from convergence.

**Watch:** Exact moments alone do not establish convergence, stability, or physical validation.

## Next useful question

- [Computational Evidence Portfolio](review_computation.md): Compare a model with its oracle and controls after probability. Check that lesson's remaining prerequisites before continuing.

**Evidence and computation:** [Classify the claim and locate its supporting record](../EVIDENCE_GUIDE.md).
