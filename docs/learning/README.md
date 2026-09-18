# What should I learn next, and why?

Choose your purpose first. The independent **Precalculus Through Problems of the
Past** teaches the foundations through compact historical problems. The bridge
book continues from its final **Choose a Method** section. The critical review
asks what mathematical arguments, computations, and measurements establish.

| Your purpose | Your starting point | Why start there? |
|---|---|---|
| Build foundations | [Foundation route](routes/foundations.md) | Find the needed operation in the companion, then explain why the reasoning works |
| Study mathematical physics | [Choose a topic below](#learn-a-topic) | Follow only the prerequisite operations needed for your question |
| Evaluate research claims | [Claim-evaluation route](routes/claims.md) | Learn the evidence method first; repair mathematical gaps at the point of use |

For a quick return, [look up a method](METHOD_FINDER.md) or
[locate a claim's evidence](EVIDENCE_GUIDE.md). Reading the books requires a PDF
reader. Python setup belongs to a chosen computational or build task.

## Continue from the companion

The companion's transfer problems ask you to name a quantity, state its domain,
choose an operation, and check the answer. Try one handoff check: a rectangle has
perimeter 28 and area 45. Find its sides and check both measurements.

<details><summary>Check your handoff answer</summary>

If one side is x, the other is 14-x, with 0<x<14. Solve x(14-x)=45 by
factoring x^2-14x+45=(x-5)(x-9). The sides are 5 and 9. Their perimeter
is 28 and their product is 45. Return to **Equations and Balance** or **Choose
a Method** in the companion if setting up the relationship needs practice.

</details>

[Open the independently maintained companion](https://github.com/Oichkatzelesfrettschen/precalc_paper).
The local album references an explicitly recorded working edition: 34 standard
pages, identified by [PDF and source hashes](precalculus_edition.json). The
upstream repository link can advance independently; the album manifest identifies
the exact bundled PDF. The companion owns its manuscript.

Matrix and vector notation start here in
[From balanced equations to matrix maps](lessons/matrix_maps.md).
[Complex multiplication, length, and conjugation](lessons/complex_numbers.md)
prepare the quantum and geometry routes. The companion's geometric-tail examples
lead into [controlled limits](lessons/calculus.md).

## Learn a topic

| Question | Route | What you can do at its destination |
|---|---|---|
| What does a symmetry preserve? | [Symmetry and algebra](routes/symmetry.md) | Separate an algebraic construction from a proposed physical interpretation |
| How do local rules produce changing fields? | [Change and simulation](routes/simulation.md) | Distinguish conservation, numerical convergence, and a controlled comparison |
| How do shape and complex structure constrain a function? | [Shape and complex functions](routes/shape.md) | Check the assumptions behind a dimension or modular-form claim |
| How do complex states give probabilities? | [Quantum states and probabilities](routes/quantum.md) | Compute normalization and identify the physical postulate |

Every lesson page states a question, required lessons, helpful background,
observable outcomes, an entry check with a repair link, a readiness check with
solution, and a reason for the next useful lesson. Pass the entry check when
using prior knowledge; follow the required lessons when an operation is unfamiliar.
A readiness result covers the named task rather than an entire university course.

## Keep the books beside one another

The album publishes a directory and **separate PDFs**. Open `build/album/index.html`
for the local directory, or `build/album/navigation.pdf` for a printable route
book. Each destination names its book, section, and physical PDF page. PDF viewers
vary in support for cross-file actions; the visible locator and book outline
provide a second way to reach the section. Use the browser's back action to
return to the directory; the local bridge and review also have online return links.

| Work | Role | Local album file |
|---|---|---|
| Precalculus Through Problems of the Past | Independent foundations, practice, historical sources, quick reference | `precalculus.pdf` |
| From Precalculus to Mathematical Physics | Twelve bridge chapters, solved practice, readiness solutions | `bridge.pdf` |
| Claim, Evidence, and Falsification | Mathematical reference and research-evidence review | `review.pdf` |
| Reader directory | Purpose chooser, routes, locators, and solutions | `index.html`, `navigation.pdf` |

The [executable framework](../ARCHITECTURE.md) supports selected investigations.
The [evidence guide](EVIDENCE_GUIDE.md#choose-a-bounded-computation) gives a small
first task and its expected result. Retained legacy manuscripts stay outside the
active reading sequence.

## Build and provenance

The root README gives dependency installation. Prepare the companion in a local
snapshot, then build the album:

```sh
make companion-prepare
make learning-check
make album
```

`companion-prepare` reads `~/Github/precalc_paper`, copies its declared working
sources into `build/companion-working-edition`, and builds only in that local
snapshot. It checks the external source hashes, index, HEAD, refs, and status
before and after preparation. An existing snapshot must match its recorded source
and remain unedited; a changed edition needs a fresh output path and an explicit
edition review. `PRECALC_SOURCE_ROOT` selects the read-only original and
`PRECALC_ROOT` selects the admitted local snapshot.

The assembler checks `precalculus_edition.json`, the source recorder, PDF freshness,
and exact outline destinations. It copies each book's PDF bytes intact, creates
cross-file navigation, and records hashes and page locators in
`build/album/manifest.json`. Passing those checks establishes identity and
navigation contracts; mathematical, historical, and visual evidence have their
own records. The companion working edition uses source hashes as well as HEAD,
since HEAD alone omits its local edits.

To review a new companion edition, prepare a fresh snapshot, review its teaching
and rendered changes, then run `scripts/record_learning_companion.py` with that
snapshot root. Commit its changed edition record and book revision together.
The command records the specific PDF; it does not silently refresh admission
during ordinary assembly.

## Maintain a route or add a book

`library.json` schema version 2 owns the learner metadata. After an edit, run:

```sh
python3 scripts/render_learning_routes.py
make learning-check
```

The generator writes route pages, lesson pages, the method finder, PDF lesson
cards, and the readiness solution appendix. Edit the manifest rather than those
generated files. Each node needs real source and an exact PDF heading, required
lesson IDs, helpful background, outcomes, entry and readiness answers, repair
links, reference cautions, and next-step reasons. Each route needs purpose,
question, starting knowledge, and a prerequisite-valid order. A new external
book also needs a revision and an admitted prebuilt edition; the assembler accepts
`--book-root ID=PATH` and keeps its PDF separate.

Design and verification records:

- [Content inventory and original reader-journey map](CONTENT_INVENTORY_AND_READER_JOURNEYS.md)
- [Information architecture implementation and verification](INFORMATION_ARCHITECTURE.md)
- [Bridge mathematical and historical audit](AUDIT.md)
