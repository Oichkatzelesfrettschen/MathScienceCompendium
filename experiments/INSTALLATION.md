# Installation Guide

## Quick Start

### 1. Navigate to Project Directory

```bash
cd /home/eirikr/MathScienceCompendium/experiments
```

### 2. Install Dependencies

```bash
# Using Make (recommended)
make install

# Or manually
pip3 install -r requirements.txt
pip3 install -e .
```

### 3. Verify Installation

```bash
# Run quick validation
python3 -c "import sys; sys.path.insert(0, 'src'); \
from cayley_dickson import Complex; \
z = Complex([3, 4]); \
print(f'Norm test: {z.norm():.4f} (expected 5.0)'); \
print('Installation successful!')"
```

## Running Experiments

### Option 1: Using Make

```bash
# Run all experiments
make run-all

# Run specific modules
make run-cayley
make run-fractals
make run-e8
make run-lattice
make run-modular

# Generate visualizations
make visualize

# Run tests
make test
```

### Option 2: Direct Python

```bash
# Run all experiments
python3 src/main.py --all

# Run specific module
python3 src/main.py --module cayley
python3 src/main.py --module fractals
python3 src/main.py --module e8
python3 src/main.py --module lattice
python3 src/main.py --module modular

# Generate visualizations only
python3 src/main.py --visualize
```

### Option 3: Individual Modules

```bash
# Cayley-Dickson algebras
cd src && python3 cayley_dickson.py

# Fractal analysis
cd src && python3 fractal_analysis.py

# E_8 Lie algebra
cd src && python3 lie_algebras.py

# Lattice theory
cd src && python3 lattice_theory.py

# Modular forms
cd src && python3 modular_forms.py

# Visualizations
cd src && python3 visualization.py
```

## Testing

```bash
# Quick test
make test

# Verbose output
make test-verbose

# Coverage report
make test-coverage

# Or directly with pytest
cd tests && python3 test_all.py
```

## Using Jupyter Notebooks

```bash
# Install Jupyter (if not already installed)
pip3 install jupyter

# Launch notebook server
jupyter notebook notebooks/

# Open: 01_cayley_dickson_demo.ipynb
```

## Troubleshooting

### Missing Dependencies

If you get import errors:

```bash
# Reinstall all dependencies
pip3 install --force-reinstall -r requirements.txt
```

### Numba Not Available

Numba is optional for performance. If not installed:

```bash
pip3 install numba
```

Or the code will fall back to pure Python (slower but functional).

### Matplotlib Display Issues

If visualizations don't display:

```bash
# Install backend
pip3 install pillow tk
```

### Permission Errors

If you get permission errors during installation:

```bash
# Install for user only
pip3 install --user -r requirements.txt
pip3 install --user -e .
```

## Verification

### Quick Functionality Check

```bash
# Test all major components
python3 << 'EOF'
import sys
sys.path.insert(0, 'src')

# Test imports
from cayley_dickson import Quaternion
from fractal_analysis import FractalGenerator
from lie_algebras import E8RootSystem
from lattice_theory import E8Lattice
from modular_forms import ModularForms

# Test Quaternion
q = Quaternion([1,0,0,0])
i = Quaternion([0,1,0,0])
j = Quaternion([0,0,1,0])
k = i * j
assert k.coeffs[3] == 1.0, "Quaternion multiplication failed"
print("Quaternions: OK")

# Test E_8
e8 = E8RootSystem()
roots = e8.generate_roots()
assert len(roots) == 240, "E_8 root count incorrect"
print("E_8 Lie algebra: OK")

# Test Lattice
lattice = E8Lattice()
kissing = lattice.kissing_number()
assert kissing == 240, "E_8 kissing number incorrect"
print("E_8 Lattice: OK")

# Test Modular Forms
j_coeffs = ModularForms.klein_j_q_expansion(num_coeffs=3)
assert j_coeffs[1] == 744, "j-invariant coefficient incorrect"
print("Modular Forms: OK")

print("\nAll components verified successfully!")
EOF
```

## Performance Optimization

For faster execution:

```bash
# Install optional performance libraries
pip3 install numba
pip3 install scikit-learn

# Use PyPy for pure Python speedup (experimental)
# pypy3 -m pip install -r requirements.txt
```

## Clean Up

```bash
# Remove generated files
make clean

# Remove results
make clean-results

# Complete reset
make clean && make clean-results
```

## Next Steps

After successful installation:

1. Read the main README.md for project overview
2. Run `make run-all` to generate complete results
3. Explore Jupyter notebooks in `notebooks/`
4. Check generated results in `results/`
5. View figures in `results/figures/`

## System Requirements

- **Python**: 3.9 or higher
- **RAM**: 4GB minimum, 8GB recommended
- **Disk Space**: 500MB for dependencies, 100MB for results
- **OS**: Linux, macOS, Windows (WSL)

## Support

If you encounter issues:

1. Check INSTALLATION.md (this file)
2. Review README.md for project details
3. Examine error messages carefully
4. Verify all dependencies are installed
5. Try running individual modules to isolate issues