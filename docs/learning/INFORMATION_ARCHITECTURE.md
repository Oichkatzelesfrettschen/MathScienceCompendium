# Reader journeys and companion navigation

The album answers **What should I learn next, and why?** through a purpose chooser,
a prerequisite graph, solved checks, and a separate-book directory. The compact
precalculus companion owns its manuscript. MathScienceCompendium owns the
continuation and its links into the critical review.

## Delivered design

| Starting item | Implemented mechanism | Authoritative surface |
|---|---|---|
| Audience and entry points | Foundation, mathematical-physics, and claim-evaluation entries; topic choice follows purpose | Root README and learning guide |
| Content hierarchy | Independent foundation book, twelve teaching chapters, critical review, optional executable workbench | Learning guide and library book roles |
| Learning progression | 25 nodes with outcomes, required lessons, helpful background, entry/repair checks, readiness solutions, and next-step reasons | `library.json`, schema version 2 |
| Navigation | Six generated route pages, 25 lesson pages, method finder, PDF entry/readiness cards, solution appendix, and standalone-book directory | `scripts/render_learning_routes.py` and `scripts/assemble_learning_album.py` |
| Representative prototype | Balanced equations lead into coordinate vectors, matrix composition, transpose, dot product, and norm, with a labeled account diagram | `papers/learning/chapters/matrix_maps.tex` |
| Remaining entry gap | Complex arithmetic, conjugation, length, division, inner product, and normalization, with a redundant-line-style diagram | `papers/learning/chapters/complex_numbers.tex` |
| Lesson design across the book | Shared entry card, Notice cue, worked examples, solved practice, readiness check, and final reference strip | `papers/learning/main.tex` and chapter sources |
| Evidence communication | Explicit evidence labels, a reader exercise, and nearby links to the exact negative-result records | `EVIDENCE_GUIDE.md`, review method and hypothesis chapters |
| Separate publication | Byte-preserved book PDFs, HTML directory, cross-file PDF navigation, named route bookmarks, physical page locators, and a manifest | `build/album/` |

The original [inventory](CONTENT_INVENTORY_AND_READER_JOURNEYS.md) remains a record
of the starting condition. Its counts and proposed dependencies describe that
snapshot; `library.json` owns the implemented graph.

## The handoff and curriculum boundary

The companion teaches equations, functions, trigonometry, growth, and finite
sums through historical problems. The album starts its handoff at **Choose a
Method**, using a rectangle problem to test equation setup, domain, and units.
The local matrix-map lesson teaches operations previously assumed at entry.
The local complex-number lesson completes the preparation for quantum states,
hypercomplex arithmetic, and complex analysis. Calculus develops controlled
limits from the companion's geometric-tail example.

Required edges describe learning dependencies. Helpful background supplies
context without imposing another whole chapter. The spectral-theorem discussion
names its imported compactness and differentiation locally; readers can return
after studying analysis. That local dependency avoids a whole-chapter cycle.
Next-step links explain a use, and each destination still exposes its remaining
prerequisites. Claim readers enter the review method as orientation and use
repair links for technical reasoning. Quantum studies retain their own route.

The chapters teach bounded operations. Full courses in real analysis,
representation theory, fluid mechanics, and quantum mechanics remain beyond
the album's curriculum claim. The evidence guide makes that scope visible at
the point where a reader could otherwise overinterpret a successful calculation.

## Metadata and generated surfaces

Every node retains book ownership, source, PDF outline title, and `requires`.
Schema version 2 adds:

- `question`, `role`, and `outcomes` for purpose and observable learning;
- `helpful` for background separate from required edges;
- `entry_check.prompt`, `answer`, and `repair` for a recoverable starting point;
- `readiness.prompt` and `answer` for a bounded exit check;
- `reference.use` and `watch` for lookup and assumptions;
- `next`, a list of destination IDs with a reason for each continuation.

Each route records purpose, question, starting knowledge, and ordered nodes.
The validator rejects missing or malformed teaching fields, unknown repair or
next destinations, cycles, invalid source paths, absent headings, skipped
prerequisites, and unreachable lessons. Repair links name the owner of the
operation, rather than mechanically selecting the graph's preceding node.

The generator owns Markdown routes/lessons, the method finder, TeX route text,
entry/readiness cards, and readiness solutions. `--check` compares every generated
surface against the manifest. The solution appendix prefixes its outline titles
with **Solutions:** so exact lesson title lookup remains unambiguous.

The PDF directory shows concise route steps at eleven points, with full solutions
available in the lesson or HTML directory. The HTML directory retains expandable
entry/readiness solutions and complete metadata. The bridge uses eleven-point
single-column reading; `make learning-largeprint` builds the fourteen-point
variant. `make learning-grayscale` supplies a grayscale inspection edition.
Shared headings wrap; long derivations use separate mathematical lines rather
than smaller type. Short reference strips stay intact.

## Companion source and publication boundary

The inspected external working edition had local modifications and a PDF older
than `main.tex`. Admission therefore required a fresh build, while the original
checkout remained read-only. `prepare_learning_companion.py` clones and overlays
the enumerated working sources into a local snapshot and runs the companion's
build there. The script directs its TeX cache into the snapshot and compares
source-file hashes, index entries, HEAD, refs, and status before and after.
The retained `.companion-snapshot.json` records those observations.

`precalculus_edition.json` records the admitted PDF hash, revision, and 32
recorder-listed local input hashes. The record explicitly identifies a working
edition: its Git HEAD alone does not identify the local manuscript changes.
`record_learning_companion.py` requires an explicit reviewed snapshot; ordinary
assembly checks admission instead of updating the record.

The assembler requires matching source/PDF identity, recorder freshness, and one
exact outline destination per lesson. Each copied PDF retains its original
bytes, outlines, and internal links. Cross-file actions name the separate PDF
and zero-based destination page; the manifest and visible locators report
one-based physical pages. The HTML uses PDF page fragments and section titles.
PDF viewers differ in their handling of remote actions, so book/section/page
locators remain visible. The companion PDF itself receives zero authoring edits;
its reciprocal online link remains owned by the companion project.

The publisher rejects symlink and nonregular managed output paths before writing.
It builds a temporary bundle and validates destinations before replacing regular
published files. The prior concatenated output is retained locally at
`build/concatenated-album-archive/`; `build/album/` owns the separate-book format.

## Verification and evidence limits

Replay the focused gates:

```sh
make learning-check
.venv/bin/python -m pytest --noconftest -q -o addopts='' tests/unit/test_learning*.py
ruff check scripts/*learning*.py tests/unit/test_learning*.py
ruff format --check scripts/*learning*.py tests/unit/test_learning*.py
make album
make learning-largeprint
make learning-grayscale
.venv/bin/python scripts/verify_learning_delivery.py
```

The learning verifier retains its 47 bounded checks across the original ten
chapter snapshots. Separate entry tests check the new matrix and complex-number
examples, including mutation and conjugation negative controls. Navigation tests
exercise full metadata, generated links, repair ownership, prerequisite failure,
exact PDF destinations, long-page layout, source admission, child symlinks, and
preservation of published files when staged generation fails.

The final focused suite passed 45 tests. The independent PyMuPDF reader resolved
74 cross-file links and 19 local navigation links. Standard bridge, review, and
large-print build warning gates passed. The companion source observations match
across its local snapshot build.

The retained validation record in `build/learning/validation.json` records the
final PDF hashes, page counts, destination checks, and rendered sample pages.
Build logs live in `build/learning-build.log`, `build/review-build.log`,
`build/album-build.log`, and the companion/large-print/grayscale build logs.

Agent walkthroughs followed foundation entry, matrix preparation, and claim
interpretation through repair, solution, and continuation links. The walkthroughs
found and repaired incorrect prerequisite-based repair links and missing named
PDF route destinations. Rendered inspection covers all standard bridge and
navigation pages in contact-sheet triage, plus full-page samples of the new
lessons, diagrams, readiness solutions, evidence pages, and grayscale/large-print
components. Triage establishes page-flow observations; full-page inspection
supports only its enumerated pages.

Human learner outcomes and universal PDF-viewer compatibility remain unmeasured.
The delivered artifacts support a future learner study; agent walkthroughs are
reported as agent inspection. Source checks, mathematical examples, render
review, and learner observation remain separate kinds of evidence.
