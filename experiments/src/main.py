"""Main entry point for Mathematical Physics Experimental Framework.

This script runs all experiments and generates comprehensive results.
"""

import sys
from pathlib import Path
import argparse
import time

# Import all modules
from cayley_dickson import run_comprehensive_validation as run_cayley
from fractal_analysis import analyze_known_fractals, demonstrate_methods
from lie_algebras import analyze_e8_properties, demonstrate_root_operations
from lattice_theory import analyze_lattice_properties, demonstrate_e8_structure
from modular_forms import analyze_modular_forms, demonstrate_modular_transformations
from visualization import create_all_visualizations


def run_all_experiments(output_dir: Path = None):
    """Run all experimental validations."""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "results"

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("MATHEMATICAL PHYSICS EXPERIMENTAL FRAMEWORK")
    print("Comprehensive Validation Suite")
    print("=" * 80)

    start_time = time.time()

    # 1. Cayley-Dickson Algebras
    print("\n" + "-" * 80)
    print("MODULE 1: CAYLEY-DICKSON ALGEBRAS")
    print("-" * 80)
    try:
        cayley_results = run_cayley(output_dir)
        print("SUCCESS: Cayley-Dickson validation complete")
    except Exception as e:
        print(f"ERROR in Cayley-Dickson: {e}")

    # 2. Fractal Analysis
    print("\n" + "-" * 80)
    print("MODULE 2: FRACTAL DIMENSION ANALYSIS")
    print("-" * 80)
    try:
        fractal_results = analyze_known_fractals(output_dir)
        print("SUCCESS: Fractal analysis complete")
    except Exception as e:
        print(f"ERROR in Fractal Analysis: {e}")

    # 3. E_8 Lie Algebra
    print("\n" + "-" * 80)
    print("MODULE 3: E_8 LIE ALGEBRA")
    print("-" * 80)
    try:
        e8_results = analyze_e8_properties(output_dir)
        print("SUCCESS: E_8 analysis complete")
    except Exception as e:
        print(f"ERROR in E_8 Analysis: {e}")

    # 4. Lattice Theory
    print("\n" + "-" * 80)
    print("MODULE 4: LATTICE THEORY")
    print("-" * 80)
    try:
        lattice_results = analyze_lattice_properties(output_dir)
        print("SUCCESS: Lattice analysis complete")
    except Exception as e:
        print(f"ERROR in Lattice Analysis: {e}")

    # 5. Modular Forms
    print("\n" + "-" * 80)
    print("MODULE 5: MODULAR FORMS")
    print("-" * 80)
    try:
        modular_results = analyze_modular_forms(output_dir)
        print("SUCCESS: Modular forms analysis complete")
    except Exception as e:
        print(f"ERROR in Modular Forms: {e}")

    # 6. Visualizations
    print("\n" + "-" * 80)
    print("MODULE 6: VISUALIZATIONS")
    print("-" * 80)
    try:
        create_all_visualizations(output_dir / "figures")
        print("SUCCESS: Visualizations generated")
    except Exception as e:
        print(f"ERROR in Visualizations: {e}")

    elapsed_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 80)
    print("EXPERIMENTAL VALIDATION COMPLETE")
    print("=" * 80)
    print(f"Total execution time: {elapsed_time:.2f} seconds")
    print(f"Results saved to: {output_dir.absolute()}")
    print("\nGenerated files:")
    print("  - cayley_dickson_*_validation.json")
    print("  - fractal_dimensions.json")
    print("  - e8_analysis.json")
    print("  - lattice_analysis.json")
    print("  - modular_forms_analysis.json")
    print("  - figures/ (visualizations)")
    print("=" * 80)


def main():
    """Main entry point with CLI argument parsing."""
    parser = argparse.ArgumentParser(
        description="Mathematical Physics Experimental Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py --all              Run all experiments
  python main.py --module cayley    Run Cayley-Dickson experiments only
  python main.py --module fractals  Run fractal analysis only
  python main.py --visualize        Generate visualizations only
        """
    )

    parser.add_argument(
        "--all", action="store_true",
        help="Run all experiments (default)"
    )
    parser.add_argument(
        "--module", type=str, choices=["cayley", "fractals", "e8", "lattice", "modular"],
        help="Run specific module only"
    )
    parser.add_argument(
        "--visualize", action="store_true",
        help="Generate visualizations only"
    )
    parser.add_argument(
        "--output", type=str,
        help="Output directory (default: ../results)"
    )

    args = parser.parse_args()

    # Determine output directory
    if args.output:
        output_dir = Path(args.output)
    else:
        output_dir = Path(__file__).parent.parent / "results"

    output_dir.mkdir(parents=True, exist_ok=True)

    # Execute requested operations
    if args.visualize:
        print("Generating visualizations...")
        create_all_visualizations(output_dir / "figures")

    elif args.module:
        print(f"Running module: {args.module}")

        if args.module == "cayley":
            run_cayley(output_dir)
        elif args.module == "fractals":
            analyze_known_fractals(output_dir)
            demonstrate_methods()
        elif args.module == "e8":
            analyze_e8_properties(output_dir)
            demonstrate_root_operations()
        elif args.module == "lattice":
            analyze_lattice_properties(output_dir)
            demonstrate_e8_structure()
        elif args.module == "modular":
            analyze_modular_forms(output_dir)
            demonstrate_modular_transformations()

    else:
        # Default: run all
        run_all_experiments(output_dir)


if __name__ == "__main__":
    main()