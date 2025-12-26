"""Integrated Mathematical Physics Framework - CLI Entry Point.

Provides a unified interface for executing experiments, generating 
visualizations, and performing algebraic validations.
"""

from __future__ import annotations
import argparse
from pathlib import Path
from typing import Optional

from .config import Config
from .algebras.cayley_dickson import analyze_algebra_properties
from .algebras.roots import ExceptionalLieAlgebras
from .lattice_theory import analyze_lattice_properties
from .modular_forms import analyze_modular_forms
from .fractal_analysis import analyze_fractal_dimensions

def run_experiments(output_dir: Optional[Path] = None) -> None:
    """Run all experimental validations."""
    if output_dir is None:
        output_dir = Config.RESULTS_DIR

    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Executing validation suite. Results in {output_dir}")
    analyze_algebra_properties(output_dir)
    analyze_lattice_properties(output_dir)
    analyze_modular_forms(output_dir)
    analyze_fractal_dimensions(output_dir)

def main() -> None:
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(description="MathPhysics Framework CLI")
    parser.add_argument("--run", action="store_true", help="Run validation suite")
    parser.add_argument("--module", choices=["algebra", "e8", "lattice", "modular", "fractal"], 
                        help="Analyze specific module")
    parser.add_argument("--output", type=str, help="Output directory")
    
    args = parser.parse_args()
    
    output_dir = Path(args.output) if args.output else Config.RESULTS_DIR
    
    if args.run:
        run_experiments(output_dir)
    elif args.module:
        if args.module == "algebra":
            analyze_algebra_properties(output_dir)
        elif args.module == "e8":
            print(ExceptionalLieAlgebras.get_all())
        elif args.module == "lattice":
            analyze_lattice_properties(output_dir)
        elif args.module == "modular":
            analyze_modular_forms(output_dir)
        elif args.module == "fractal":
            analyze_fractal_dimensions(output_dir)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
