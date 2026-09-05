# MathScienceCompendium

A connected mathematics learning album: start with precalculus, learn the
prerequisites for an advanced question, then examine what the mathematics and
evidence establish.

**[Start with the reading routes](docs/learning/README.md).**

## The three books

| Book | Purpose | Canonical source |
|---|---|---|
| A Precalculus Compendium | Historical context, visual constructions, functions, and foundational operations | [precalc_paper](https://github.com/Oichkatzelesfrettschen/precalc_paper) |
| From Precalculus to Mathematical Physics | Ten bridge chapters with worked examples and solved exercises | [papers/learning/main.tex](papers/learning/main.tex) |
| Claim, Evidence, and Falsification | Advanced mathematical baseline, computational evidence, and physical-claim audit | [papers/main.tex](papers/main.tex) |

The combined PDF includes the complete pinned precalculus book, the bridge
book, and the existing critical review. Clickable reading routes and preserved
book outlines support independent paths through symmetry, simulation, shape,
and quantum states/evidence. Each book retains its source ownership; the album
assembles their PDFs rather than maintaining duplicate manuscript text.

The bridge chapters introduce selected undergraduate tools. Their solved
assessments establish bounded learning objectives, not completion of entire
graduate courses. The advanced review distinguishes theorem support,
computational checks, hypotheses, and empirical evidence. A passing artifact
check establishes its declared contract, not a physical theory.

## Build the learning album

The precalculus checkout belongs at `~/Github/precalc_paper`. The library
manifest records its exact reviewed commit. Setup and revision instructions
are in the [learning guide](docs/learning/README.md).

```sh
python3 -m venv .venv
.venv/bin/python -m pip install -r docs/learning/requirements.txt
make learning-check
make album PRECALC_ROOT="$HOME/Github/precalc_paper"
```

Outputs:

- `build/album/album.pdf`: complete album with navigation.
- `build/album/manifest.json`: input hashes, source dependencies, and destinations.
- `build/learning/main.pdf`: standalone bridge book.
- `papers/main.pdf`: standalone critical review.

The TeX builds require TeX Live, `latexmk`, BibTeX, and makeindex. Precalculus
uses LuaLaTeX and its own font checks; the other books use pdfLaTeX. The full
album target also runs the precalculus source and equation checks. Python
requirements for the advanced repository's evidence generators are declared
in `pyproject.toml`; use `make install` when those dependencies are absent.

## Research and computation

`src/mathphysics/` contains the reusable Python package; `experiments/`
contains experiment drivers; `data/registry/` and retained evidence document
provenance and scientific admission boundaries. See the
[architecture](docs/ARCHITECTURE.md), [framework authority surfaces](docs/framework/AUTHORITY_SURFACES.md),
and [offline reproducibility guide](docs/OFFLINE_REPRODUCIBILITY.md).

```sh
make install
make lint
make test
make papers
```

The files `papers/sections/vol*_*.tex` retain an earlier manuscript. The active
review and learning album exclude those files. Their historical status and
remaining claims should be assessed before reuse.

## Add another book

The [library manifest](docs/learning/library.json) separates books, lessons,
prerequisites, and reading routes. A new book can branch from the precalculus
foundation without turning MathScienceCompendium into the owner of its text.
Follow the [extension contract](docs/learning/README.md#add-another-book) and
run `make learning-check` before publishing a new route.
