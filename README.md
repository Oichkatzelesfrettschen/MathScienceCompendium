# MathScienceCompendium

**What should I learn next, and why?**

A learning album that continues from the independent
[Precalculus Through Problems of the Past](https://github.com/Oichkatzelesfrettschen/precalc_paper)
into mathematical physics and the evaluation of research claims. Keep the books
beside one another; the album supplies their handoff and reading routes.

| Your purpose | Start here |
|---|---|
| Build foundations | [Find an operation and check your readiness](docs/learning/routes/foundations.md) |
| Study mathematical physics | [Choose a topic and its prerequisites](docs/learning/README.md#learn-a-topic) |
| Evaluate research claims | [Follow the evidence method](docs/learning/routes/claims.md) |

[Look up a method](docs/learning/METHOD_FINDER.md) ·
[Examine a claim's evidence](docs/learning/EVIDENCE_GUIDE.md) ·
[Companion handoff](docs/learning/README.md#continue-from-the-companion)

## The books and the workbench

| Work | Purpose | Source |
|---|---|---|
| Precalculus Through Problems of the Past | Compact foundations through historical problems, worked practice, and reference strips | [Independent companion](https://github.com/Oichkatzelesfrettschen/precalc_paper) |
| From Precalculus to Mathematical Physics | Twelve bridge chapters with explicit prerequisites, solved practice, and next-step checks | [Bridge book](papers/learning/main.tex) |
| Claim, Evidence, and Falsification | Established mathematics, computational observations, hypotheses, and bounded negative results | [Critical review](papers/main.tex) |
| Executable mathematical-physics framework | Reproduce selected calculations with declared inputs and evidence boundaries | [Architecture](docs/ARCHITECTURE.md) |

The companion owns its text and supplies the teaching and visual reference.
The bridge begins where the compact companion ends, including new preparation
in matrix maps and complex arithmetic. The review evaluates what claims can
support. A passing computation establishes its declared contract; physical
admission needs the separate evidence specified for the claim.

## Build the separate-book album

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r docs/learning/requirements.txt 'pytest>=7.4,<9'
make companion-prepare
make album
```

The external checkout belongs at `~/Github/precalc_paper`. Preparation reads that
checkout and builds a local working-edition snapshot; the source checkout remains
read-only. The [learning guide](docs/learning/README.md#build-and-provenance)
explains revision and source-hash admission.

Open `build/album/index.html` or `build/album/navigation.pdf`. The album folder
contains separate `precalculus.pdf`, `bridge.pdf`, and `review.pdf`, plus
`manifest.json` with input hashes and verified book/page destinations. The bridge
also builds independently as `build/learning/main.pdf`; the review builds as
`papers/main.pdf`.

TeX builds require TeX Live, LuaLaTeX, pdfLaTeX, `latexmk`, BibTeX, and makeindex.
The companion checks its own fonts. Research evidence generators use dependencies
in `pyproject.toml`; run `make install` when that environment needs installation.

## Research and computation

Start with [a bounded learning computation](docs/learning/EVIDENCE_GUIDE.md#choose-a-bounded-computation)
or a particular claim's reproduction record. Then use the
[framework authority surfaces](docs/framework/AUTHORITY_SURFACES.md) and
[offline reproducibility guide](docs/OFFLINE_REPRODUCIBILITY.md).

```sh
make install
make lint
make test
make papers
```

`src/mathphysics/` owns reusable implementations, `experiments/` owns experiment
drivers, and `data/registry/` owns scientific records. The retained
`papers/sections/vol*_*.tex` manuscript sources and archived reports are historical
inputs; active review sections begin with `review_`.
