from scripts.build_registries import include_artifact


def test_include_artifact_excludes_latex_intermediates_and_sources() -> None:
    assert include_artifact("papers/main.pdf")
    assert not include_artifact("papers/main.aux")
    assert not include_artifact("papers/main.tex")
    assert not include_artifact("papers/sections/review_scope_method.tex")


def test_include_artifact_keeps_source_pdfs_only() -> None:
    assert include_artifact("source_materials/pdfs/source.pdf")
    assert not include_artifact("source_materials/pdfs/extracted/source.txt")


def test_include_artifact_keeps_result_and_figure_files() -> None:
    assert include_artifact("results/highres_lbm_000500.parquet")
    assert include_artifact("figures/e8_roots.png")
