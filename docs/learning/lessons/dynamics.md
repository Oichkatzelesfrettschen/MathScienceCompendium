# Dynamics: equations, modes, and trustworthy computation

[Start here](../README.md) | [Method finder](../METHOD_FINDER.md) | [Evidence guide](../EVIDENCE_GUIDE.md)

**You are here:** From Precalculus to Mathematical Physics / teaching

**Question:** When does a numerical step respect decay?

[Read the source](../../../papers/learning/chapters/dynamics.tex). In the separate PDF, open **Dynamics: equations, modes, and trustworthy computation** in **From Precalculus to Mathematical Physics**. The built album directory supplies the verified physical page and PDF link.

## Bring forward

[Several variables: local maps and conservation](multivariable.md)

**Helpful background:** Heat flow gives a physical model; boundary conditions remain essential.

## What you will learn

- Solve exponential relaxation and distinguish model stability from step stability.

## Entry check

Differentiate exp(-2t).

<details><summary>Check your entry answer</summary>

The chain rule gives -2 exp(-2t).

</details>

**If a step is unfamiliar:** [Calculus: local change and accumulated change](calculus.md).

## Practice and readiness

Euler stepping for y'= -2y uses factor 1-2h. For which positive h does its magnitude remain below one?

<details><summary>Read the worked readiness solution</summary>

Solve -1<1-2h<1 to obtain 0<h<1. At h=1 the factor is -1 and the numerical solution does not decay.

</details>

Continue when you can explain the operations and assumptions as well as the value. Otherwise revisit the lesson method and try its solved practice.

## Quick reference

**Use:** Solve exponential relaxation and distinguish model stability from step stability.

**Watch:** State initial data and boundary conditions before interpreting a solution.

## Next useful question

- [Numerical reasoning: approximation with an error budget](numerical.md): Check the errors introduced by a finite update. Check that lesson's remaining prerequisites before continuing.

**Evidence and computation:** [Classify the claim and locate its supporting record](../EVIDENCE_GUIDE.md).
