# How do local rules produce changing fields?

**Purpose:** Study mathematical physics

Explain the companion transfer problems, or begin with its method finder.

[Start here](../README.md) | [Look up a method](../METHOD_FINDER.md) | [Evidence guide](../EVIDENCE_GUIDE.md)

Read in the order below. A passed entry check lets you use prior knowledge; use the repair link when a step is unfamiliar. Helpful background adds context and stays separate from required lessons.

## 1. Precalculus

Which operation fits the quantities?

**Learn to:** Choose an equation or function and check its domain and units.

**Required lessons:** Start with this orientation.

**Helpful background:** Familiarity with school algebra helps; the companion teaches the operations.

**Ready to continue when:** A rectangle has perimeter 28 and area 45. Find its sides.

[Precalculus](../lessons/precalc.md) supplies the entry check, solution, source, and next-step reasons.

## 2. From convincing examples to proof

When does a pattern become a theorem?

**Learn to:** State domains and distinguish a universal argument from a finite observation.

**Required lessons:** [Precalculus](../lessons/precalc.md)

**Helpful background:** Historical proof examples supply context.

**Ready to continue when:** Prove that the sum of two odd integers is even.

[From convincing examples to proof](../lessons/proof.md) supplies the entry check, solution, source, and next-step reasons.

## 3. From balanced equations to matrix maps

How can two accounts become one operation?

**Learn to:** Compute matrix actions, compositions, and real dot products with compatible dimensions.

**Required lessons:** [From convincing examples to proof](../lessons/proof.md)

**Helpful background:** Spatial arrows help interpret a vector; units determine whether a norm is a physical length.

**Ready to continue when:** Apply the matrix with rows (3,1) and (1,2) to (2,5), then subtract the second output from the first.

[From balanced equations to matrix maps](../lessons/matrix_maps.md) supplies the entry check, solution, source, and next-step reasons.

## 4. Linear algebra: coordinates, maps, and modes

Which coordinates expose independent directions?

**Learn to:** Verify a basis image, eigenpair, and projection.

**Required lessons:** [From balanced equations to matrix maps](../lessons/matrix_maps.md)

**Helpful background:** Calculus and compactness support the optional spectral-proof discussion.

**Ready to continue when:** For A with rows (2,1),(1,2), verify two independent eigenvectors.

[Linear algebra: coordinates, maps, and modes](../lessons/linear_algebra.md) supplies the entry check, solution, source, and next-step reasons.

## 5. Calculus: local change and accumulated change

How do local rates connect to accumulated change?

**Learn to:** Derive a local rate and interpret a controlled approximation.

**Required lessons:** [From convincing examples to proof](../lessons/proof.md)

**Helpful background:** Motion supplies an interpretation of rates.

**Ready to continue when:** Derive the derivative of x^2 using a nonzero increment h.

[Calculus: local change and accumulated change](../lessons/calculus.md) supplies the entry check, solution, source, and next-step reasons.

## 6. Several variables: local maps and conservation

How can several inputs describe a local change?

**Learn to:** Compute gradients and Jacobian factors on a stated domain.

**Required lessons:** [Linear algebra: coordinates, maps, and modes](../lessons/linear_algebra.md), [Calculus: local change and accumulated change](../lessons/calculus.md)

**Helpful background:** Field diagrams help connect formulas to spatial quantities.

**Ready to continue when:** For f(x,y)=x^2+3y^2, find its gradient at (1,2).

[Several variables: local maps and conservation](../lessons/multivariable.md) supplies the entry check, solution, source, and next-step reasons.

## 7. Dynamics: equations, modes, and trustworthy computation

When does a numerical step respect decay?

**Learn to:** Solve exponential relaxation and distinguish model stability from step stability.

**Required lessons:** [Several variables: local maps and conservation](../lessons/multivariable.md)

**Helpful background:** Heat flow gives a physical model; boundary conditions remain essential.

**Ready to continue when:** Euler stepping for y'= -2y uses factor 1-2h. For which positive h does its magnitude remain below one?

[Dynamics: equations, modes, and trustworthy computation](../lessons/dynamics.md) supplies the entry check, solution, source, and next-step reasons.

## 8. Probability: uncertainty, evidence, and comparison

What does a positive observation establish?

**Learn to:** Compute a conditional probability and name the experiment behind it.

**Required lessons:** [From convincing examples to proof](../lessons/proof.md)

**Helpful background:** Calculus is helpful for later continuous distributions.

**Ready to continue when:** Among 10000 people, 100 have a condition. A test detects 90 of them and flags 495 of the rest. What fraction of positive results have the condition?

[Probability: uncertainty, evidence, and comparison](../lessons/probability.md) supplies the entry check, solution, source, and next-step reasons.

## 9. Numerical reasoning: approximation with an error budget

How can an approximation justify its precision?

**Learn to:** Separate truncation, roundoff, conditioning, and refinement evidence.

**Required lessons:** [Dynamics: equations, modes, and trustworthy computation](../lessons/dynamics.md)

**Helpful background:** Probability helps interpret an ensemble of runs.

**Ready to continue when:** For trapezoidal integration of x^2 on [0,1], compare one and two equal panels against 1/3.

[Numerical reasoning: approximation with an error budget](../lessons/numerical.md) supplies the entry check, solution, source, and next-step reasons.

## 10. A lattice-Boltzmann step has exact moment obligations

Which moments must a lattice rule conserve?

**Learn to:** Check discrete moments and distinguish conservation from convergence.

**Required lessons:** [Numerical reasoning: approximation with an error budget](../lessons/numerical.md)

**Helpful background:** Continuum mechanics helps interpret a hydrodynamic limit.

**Ready to continue when:** At rest, D2Q9 weights are 4/9, four copies of 1/9, and four copies of 1/36. Check their sum and first moment.

[A lattice-Boltzmann step has exact moment obligations](../lessons/fluids.md) supplies the entry check, solution, source, and next-step reasons.

## 11. Computational Evidence Portfolio

Which comparisons support a computational conclusion?

**Learn to:** Trace a reported result to its inputs, controls, and scope.

**Required lessons:** [A lattice-Boltzmann step has exact moment obligations](../lessons/fluids.md), [Probability: uncertainty, evidence, and comparison](../lessons/probability.md)

**Helpful background:** Use proof and probability to repair reasoning gaps; specialist mathematics follows the selected claim.

**Ready to continue when:** What should accompany a successful simulation check?

[Computational Evidence Portfolio](../lessons/review_computation.md) supplies the entry check, solution, source, and next-step reasons.
