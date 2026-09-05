# Bridge content and visual audit

The learning album adds ten introductory chapters between the independently
maintained precalculus book and the existing advanced review. The audit covers
those ten chapter sources, four instructional diagrams, their thirty solved
exercises, and the selected rendered pages enumerated below. The checks establish
specific mathematical examples, editorial repairs, and observed layout quality.
They do not certify every claim in the precalculus book, the advanced review, or
the combined corpus.

## Mathematical and instructional coverage

The source review follows the argument in each bridge chapter and checks whether
its definitions, assumptions, examples, and conclusions fit the stated domain.
Every chapter contains three exercises followed by full solutions. Counting
`\paragraph{Solution.}` in the ten chapter files returns 30; that count measures
solution presence, while the argument review evaluates their substance.

| Chapter | Reviewed mathematical boundary |
|---|---|
| Proof | Quantifier order, domains, direct proof, contrapositive, induction base/step, counterexamples, and finite versus universal verification |
| Linear algebra | Vector-space operations, basis coordinates, polynomial map, rank-nullity argument, eigenvector examples, symmetric spectral proof outline, and scope counterexamples |
| Calculus | Epsilon-delta choices, derivative rules, Riemann sums, fundamental theorem, Taylor remainder, and smooth versus analytic functions |
| Multivariable | Partial derivatives versus differentiability, gradient bound, Jacobian and area factor, divergence, and boundary-dependent conservation |
| Dynamics | Initial-data assumptions, exponential and matrix modes, heat solutions, boundary energy balance, and explicit numerical stability |
| Probability | Finite distributions, expectation/variance, dependence, diagnostic conditioning, coverage assumptions, and causal inference limits |
| Numerical reasoning | Truncation versus roundoff, conditioning, exact trapezoidal error, convergent iteration, residual interpretation, and refinement scope |
| Algebra | Groups/actions, fields/spaces/algebras, matrix brackets, A2 roots, E8 root count and lengths, and exact Cartan determinant |
| Geometry and analysis | Metrics, compactness, Cantor covering arguments, Hausdorff lower-bound outline, complex differentiability, and modular cusp conditions |
| Advanced entry points | Fixed Cayley-Dickson convention, quaternion norms, sedenion witness, unitary qubit example, Born-rule status, and lattice-Boltzmann moments |

The substantive repairs make prerequisite dependencies and inference boundaries
explicit:

- The polynomial map is defined by its coefficient rule before calculus identifies
  the rule as differentiation.
- The calculus chapter derives the sine/cosine rules from the unit-circle squeeze
  and angle addition, and connects logarithm/exponential derivatives to the
  fundamental theorem and inverse rule.
- The directional-derivative example derives its unit-vector Cauchy-Schwarz bound
  from a nonnegative squared norm.
- Taylor-series equality requires a vanishing remainder; a smooth nonanalytic
  function supplies a counterexample to a broader assertion.
- E8 coordinates give 112 integer roots and 128 half-integer roots, each with
  squared length two. A specified Cartan tree gives determinant one.
- The sedenion multiplication witness declares its recursive basis convention.
- The fluid example separates exact discrete moments, boundary conventions,
  stability, and hydrodynamic assumptions from physical validation.
- Four diagrams show eigen-directions, conditional probability, A2 roots, and
  Cantor construction. Their captions explain how to read the mathematics.
- Iteration, inverse Cartan, Jordan-block, and projection matrices use display
  equations where inline versions impaired readability.

The symmetric spectral proof explicitly imports compactness and differentiation.
ODE linearization, infinite Fourier-series convergence, measure construction,
classification, and hydrodynamic limits retain named assumptions and references.
The chapters introduce these subjects; complete courses in real analysis,
representation theory, quantum information, and continuum mechanics remain
separate learning destinations.

## Executable examples and mutation evidence

Run the deterministic standard-library verifier from the repository root:

```sh
python scripts/verify_learning_examples.py --output build/learning/examples.json
```

The reviewed run passes 47 bounded checks. The JSON records the ten chapter
hashes, individual check names, and explicit limits. Exact arithmetic covers E8
count/norms/opposite closure/Cartan determinant, Cayley-Dickson products, D2Q9
polynomial moment coefficients, Bayes's posterior, trapezoidal errors, and
geometric remainders. Other checks sample heat amplification, Euler factors,
a sine remainder, and positive decay in the smooth-function counterexample.
The samples illustrate stated cases; the written limiting arguments carry the
universal analytic claims.

Five isolated temporary manuscript mutations exercised failure detection. Each
mutated copy was supplied through `--chapters-dir`; each invocation exited with
status 1:

| Mutation | Rejected observation |
|---|---|
| Diagnostic prevalence `0.01` to `0.02` | Posterior changes from `1/6` to `99/344` |
| D2Q9 linear velocity coefficient `3` to `4` | Printed equilibrium coefficients disagree with the checked moment construction |
| Sedenion left witness index `10` to `11` | Witness indices differ from the specified exact example |
| Printed E8 determinant `1` to `2` | Rational elimination still returns `1` |
| Heat amplification coefficient `4` to `5` | Printed amplification differs from the centered-space scheme |

Source coupling parses named mathematical parameters and equations. It neither
parses all LaTeX mathematics nor evaluates every sentence. Additional direct
checks confirmed exact Cantor interval counts/lengths, all four Bayes-tree joint
probabilities, their sum of one, and their posterior of one sixth. Those diagram
checks were performed during authoring; the 47-check verifier does not claim to
cover every TikZ coordinate. Ruff lint/format checks on the verifier and
`git diff --check` passed during its integration.

## Historical source access and remaining verification

Historical cards distinguish surviving documents, modern scholarly accounts,
and instructional constructions. The text supplies neither invented dialogue
nor undocumented private thoughts. A citation records where a claim should be
checked; citation presence alone establishes access to neither the document nor
its contents.

| Historical or reference source | Evidence obtained in this audit |
|---|---|
| Euclid, Elements I.47, Joyce edition at Clark University | The proposition page was fetched successfully and read for its deductive presentation. This is a modern mathematical edition, not an ancient manuscript inspection. |
| Cayley, 1858 matrix memoir, DOI `10.1098/rstl.1858.0002` | Precise bibliographic locator supplied; document request returned HTTP 403. The historical card's document-content verification remains open. |
| Newton, Principia, preface and Book I, Cambridge digitization | Precise collection locator supplied; request returned HTTP 403. The cited preface was not fetched in this audit. |
| Wilson, Vector Analysis, 1901, Internet Archive `vectoranalysiste00gibbiala` | Metadata, title page, Gibbs's preface, and Wilson's preface were fetched and read. They support the private pamphlet, lecture-to-textbook, and interleaved-applications account. An initially invalid archive identifier was corrected. |
| Fourier, Analytical Theory of Heat, preliminary discourse, Michigan collection | Precise locator supplied; request returned HTTP 403. Document-content verification remains open. |
| Bayes, 1763 essay, DOI `10.1098/rstl.1763.0053` | Crossref metadata confirms the publication title/date; the title explicitly names the late Bayes and communication by Price. This corroborates those facts, while the introductory letter itself was not fetched. |
| Turing, 1948 rounding-error paper, DOI `10.1093/qjmam/1.1.287` | Precise reference supplied; metadata request returned HTTP 429. Its full text was not fetched. |
| Cartan dissertation; Mandelbrot coastline paper; Baez octonion survey | Existing bibliography entries and the bounded chapter uses were reviewed. A fresh full-text historical-source audit was not completed for these works. |
| Nielsen and Chuang, quantum textbook | Crossref confirms DOI `10.1017/CBO9780511976667` and authors/title. Its online date is 2012; the cited anniversary print edition is 2010. Chapter-content access was not established by that metadata response. |
| Chen and Doolen, lattice-Boltzmann review | Precise DOI supplied; metadata request returned HTTP 429. The full derivation was not fetched. |

The Kac bibliography entry was corrected to the 1990 third-edition Cambridge
University Press book. These access results leave a concrete follow-up: retrieve
the identified inaccessible works and compare each historical card with its
cited passage. The remaining access work prevents an exhaustive historical
fact-check claim for the bridge book.

## Rendered-page review

The reviewed standalone bridge PDF has 45 physical pages. Its SHA-256 is:

```text
40aabed38493b3e0f30b8116d4728a4f9619b46cf14e18b4fd1434cdd36b2502
```

Full-page PNG inspection covers physical pages
**1, 2, 9, 11, 12, 13, 18, 25, 26, 29, 33, 35, 37, 38, and 41**:

- Pages 1 and 2: title, route orientation, entry checks, and history/evidence rules.
- Pages 11, 26, 35, and 38: all four instructional diagrams and their captions.
- Pages 9, 13, 25, 29, 33, 37, and 41: selected chapter openings and prerequisite cards.
- Pages 11 and 12: the repaired Jordan-block and projection display matrices.
- Page 18: corrected mapping-colon spacing, Jacobian equations, and the Wilson history card.

The sampled render shows readable labels, complete card borders, consistent
headings, and content inside page margins. The four diagrams preserve their
intended geometric and probabilistic meaning. An initial inspection identified
two undersized inline matrices in linear algebra; the final inspection confirms
readable display versions. The remaining twelve previously inspected page PNGs
are byte-identical after that repair. A subsequent mapping-colon spacing change
was inspected on page 18; all fourteen earlier sample images remain byte-identical. The sampled pages show no clipped text,
label collisions, or missing glyphs. This is a fifteen-page visual sample,
rather than an assertion that every page was inspected visually.

`build/learning/main.log` contains zero matches for `Warning`, `Overfull`, or
`Underfull` in the reviewed build. Build-log absence is a separate measurement
from visual quality. The standalone visual sample also does not validate the
combined album's route links, attachment integrity, or every included book;
the assembler's checks and other books' audits own those surfaces.

Local review images and their manifest live under
`build/learning/visual-audit/`. Reproduce a full-page render with:

```sh
pdftoppm -f 11 -l 11 -singlefile -scale-to 1400 -png \
  build/learning/main.pdf build/learning/visual-audit/page-11
```

Observed tool versions: Poppler `pdftoppm 26.08.0`, Python `3.14.7`, and Ruff
`0.14.11`. A rebuilt PDF may change its hash; rerun the example checks and inspect
pages affected by source, font, or layout changes before extending the reviewed
snapshot's claims.

## Assembly admission follow-up

The focused assembly/library suite passes 20 tests after an independent code
review. The repaired admission checks retain local `.bbl` files and originating
`.bib` files resolved from BibTeX auxiliary or latexmk records, reject missing
recorded source inputs, and verify supplied external lesson paths inside their
checkouts. Route pagination measures wrapped assessment height and preserves
text through continuation pages. A referenced duplicate outline title raises
an ambiguity error; repeated unused titles remain admissible.

Source PDF readers and the reopened assembled PDF use strict parsing. A fixture
with valid cross-reference offsets and duplicate `/Group` dictionary keys is
rejected, while the ordinary internal-link, additional-book, and route fixtures
pass. The integration review separately reports an in-memory source-import
comparison of 798 precalculus links, 157 bridge links, and 129 advanced-review
links, with zero mismatches across those 1,084 comparisons. That source-import
measurement is distinct from checking the subsequently written combined PDF.
The final combined-output manifest and link review own the latter measurement.

The focused command uses the PDF tooling environment and excludes the parent
physics-test conftest, whose NumPy dependency belongs to the wider package suite:

```sh
.venv/bin/pytest -q --confcutdir=tests/unit \
  tests/unit/test_learning_album.py tests/unit/test_learning_library.py
```

These admission checks validate source identity, file availability, strict PDF
structure, and tested link/layout mechanisms. They leave the historical-source
access and mathematical scope limits above unchanged.

## Written album verification

The real assembled PDF contains 200 pages: six navigation pages, 109 pages
of precalculus, 45 bridge pages, and 40 pages of the existing review. The
assembler reopens the output and checks all 50 added navigation destinations.
A separate PyMuPDF comparison checks 802+157+129 imported links against their
source books, adjusting internal page destinations by each book's offset.
Counts, link kinds, internal destinations, and external URIs agree for all
1088 compared links. The raw local result is `build/album/imported-links.json`.
The parent viewed all six full-page navigation renders; directory and route
text fits, and the four route sequences preserve their prerequisites. Cover
links open complete books, including their orientation and entry assessment.

Repository validation reports 764 tests passed and three optional-dependency
skips in the system environment. The dedicated PDF environment separately
passes 20 routing/assembly regression tests. Ruff, formatting, type checking,
23 claim contracts, and offline integrity pass. A JAX GPU-plugin warning
records CPU execution for the existing claim checks; the mathematical
content audit does not establish GPU runtime behavior.
