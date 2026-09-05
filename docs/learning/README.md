# Start with a question

The album combines three complete PDFs: the independently maintained
precalculus compendium, ten prerequisite chapters, and the advanced critical
review. Begin with the route matching your question. Each chapter includes
worked examples and three exercises with full solutions; try the exercise
before uncovering its solution.

## Reading routes

| Question | Reading order | Advanced destination |
|---|---|---|
| What does a symmetry preserve? | Precalculus -> proof -> linear algebra -> algebra -> hypercomplex construction | Mathematical Baseline: exceptional and Cayley-Dickson algebras |
| How do local rules produce changing fields? | Precalculus -> proof -> linear algebra -> calculus -> multivariable -> dynamics -> probability -> numerical reasoning -> fluid moments | Computational Evidence Portfolio |
| How do shape and complex structure constrain a function? | Precalculus -> proof -> linear algebra -> calculus -> multivariable -> algebra -> geometry/complex analysis | Modular forms and fractal dimensions |
| What does a probability or successful check establish? | Precalculus -> proof -> linear algebra -> probability -> quantum states | Scope, Questions, and Review Method |

The combined PDF supplies actual links at each route step. The full chapter
on advanced entry points contains three independently usable sections:
hypercomplex algebras, quantum states, and fluid moments. Read the section
selected by your route; the chapter's opening card lists the prerequisites
for reading all three together.

## What the bridges teach

1. **Proof:** domains, quantifiers, direct arguments, contrapositive, induction,
   and the difference between examples and universal reasoning.
2. **Linear algebra:** spaces, maps, bases, eigenvectors, rank-nullity, and the
   assumptions behind the symmetric spectral theorem.
3. **Calculus:** controlled limits, derivatives, integration, the fundamental
   theorem, and Taylor remainders.
4. **Multivariable calculus:** gradients, Jacobians, coordinate integration,
   divergence, and conservation.
5. **Dynamics:** linear ODEs, stability, heat flow, Fourier modes, and discrete
   time-step restrictions.
6. **Probability:** conditional experiments, Bayes's rule, variance, interval
   assumptions, and controls.
7. **Numerical reasoning:** conditioning, roundoff, truncation, iteration,
   refinement, and error bounds.
8. **Algebra:** groups and actions, matrix commutators, A2 roots, and exact E8
   enumeration and Cartan determinant.
9. **Geometry and analysis:** metrics, compactness, Cantor dimension, complex
   differentiability, modular transformations, and cusp conditions.
10. **Advanced entry points:** Cayley-Dickson multiplication, quantum-state
    normalization, unitary evolution, and lattice-Boltzmann moment obligations.

These are introductory, explicit bridges into the review's vocabulary and
selected derivations. Complete real analysis, measure theory, representation
theory, quantum mechanics, and fluid mechanics require further study. A new
book can develop any of those branches with its own assessment and evidence
contract.

## Build and provenance

The root README gives dependency installation. The standalone book checks are:

```sh
make learning-check
make learning
make papers
make album PRECALC_ROOT="$HOME/Github/precalc_paper"
```

`library.json` pins the reviewed precalculus commit. The assembler rejects a
different commit, dirty tracked precalculus sources, missing compiled PDFs,
missing input recorders, and PDFs older than their recorded source inputs.
Use a separate checkout at the pinned commit when the precalculus main branch
has advanced; preserve a working checkout's edits.

`build/album/manifest.json` records PDF hashes, recorded TeX input hashes,
source commits, page counts, and every lesson's actual destination. Included
PDFs retain their internal links and outlines. The assembler checks every
added route link after reopening the written album. Source claims remain
subject to the separate content audit.

Review records:

- [Precalculus mathematics](https://github.com/Oichkatzelesfrettschen/precalc_paper/blob/main/docs/mathematical_factcheck.md)
- [Precalculus history](https://github.com/Oichkatzelesfrettschen/precalc_paper/blob/main/docs/history_factcheck.md)
- [Precalculus figures](https://github.com/Oichkatzelesfrettschen/precalc_paper/blob/main/docs/figure_factcheck.md)
- [Bridge audit](AUDIT.md)

## Add another book

Keep a book's manuscript in its owning repository or a clearly named local
book directory. Add its title, entry point, compiled PDF location, and role
to `library.json`. External books require an immutable 40-character commit
and a local checkout supplied to the assembler. Retain attribution and
confirm the license permits including the work.

Add lesson nodes with existing source files, exact PDF outline headings,
prerequisite IDs, and an assessment. Add a route listing lessons in a valid
prerequisite order. Each lesson must occur in at least one route. The validator
rejects cycles, duplicate IDs, unwritten local lessons, escaped source paths,
and routes that skip their prerequisites. A proposed unwritten book belongs
in planning prose until it has real source and assessment artifacts.

Build each external book with its own checks, then supply additional roots:

```sh
.venv/bin/python scripts/assemble_learning_album.py \
  --precalc-root "$HOME/Github/precalc_paper" \
  --book-root another_book=/path/to/its/pinned/checkout
```

The existing `make album` target builds the three initial books. A new external
book also needs its own build command before assembly; the assembler verifies
its revision and PDF inputs. The number of branches is a content choice,
with source ownership and prerequisite checks applying to each addition.
