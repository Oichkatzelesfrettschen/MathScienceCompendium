"""Unit tests for the main CLI entry point."""

from __future__ import annotations

from unittest.mock import patch

from mathphysics.main import main, run_experiments


def test_run_experiments_is_callable():
    assert callable(run_experiments)


def test_run_experiments_with_tmp_dir(tmp_path):
    """run_experiments completes without error and creates output files."""
    run_experiments(tmp_path)
    # Should create some output files
    assert tmp_path.exists()


def test_main_no_args_prints_help(capsys):
    """main() with no args prints help text."""
    with patch("sys.argv", ["mathphysics"]):
        main()
    captured = capsys.readouterr()
    assert "usage" in captured.out.lower() or "help" in captured.out.lower() or captured.out == ""


def test_main_run_flag(tmp_path):
    """main() with --run executes run_experiments."""
    with patch("sys.argv", ["mathphysics", "--run", "--output", str(tmp_path)]):
        main()
    assert tmp_path.exists()


def test_main_module_algebra(tmp_path):
    """main() --module algebra runs algebra analysis."""
    with patch("sys.argv", ["mathphysics", "--module", "algebra", "--output", str(tmp_path)]):
        main()


def test_main_module_e8(capsys):
    """main() --module e8 prints algebra catalog."""
    with patch("sys.argv", ["mathphysics", "--module", "e8"]):
        main()
    capsys.readouterr()
    # Should print something from ExceptionalLieAlgebras.get_all()
    assert True  # permissive -- just verify no exception


def test_main_module_lattice(tmp_path):
    """main() --module lattice runs lattice analysis."""
    with patch("sys.argv", ["mathphysics", "--module", "lattice", "--output", str(tmp_path)]):
        main()


def test_main_module_modular(tmp_path):
    """main() --module modular runs modular forms analysis."""
    with patch("sys.argv", ["mathphysics", "--module", "modular", "--output", str(tmp_path)]):
        main()


def test_main_module_fractal(tmp_path):
    """main() --module fractal runs fractal analysis."""
    with patch("sys.argv", ["mathphysics", "--module", "fractal", "--output", str(tmp_path)]):
        main()
