"""Setup configuration for Mathematical Physics Experimental Framework."""

from setuptools import setup, find_packages
from pathlib import Path

# Read the contents of README file if it exists
this_directory = Path(__file__).parent
long_description = ""
readme_path = this_directory / "README.md"
if readme_path.exists():
    long_description = readme_path.read_text()

setup(
    name="mathphysics-experiments",
    version="1.0.0",
    author="Mathematical Physics Research",
    description="A comprehensive Python framework for computational experiments in mathematical physics",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/MathScienceCompendium",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering :: Mathematics",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
    ],
    python_requires=">=3.9",
    install_requires=[
        "numpy>=1.24.0",
        "scipy>=1.11.0",
        "matplotlib>=3.7.0",
        "sympy>=1.12",
        "numba>=0.58.0",
        "pillow>=10.0.0",
        "networkx>=3.1",
        "pandas>=2.0.0",
        "seaborn>=0.12.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.4.0",
            "pytest-cov>=4.1.0",
            "jupyter>=1.0.0",
            "ipykernel>=6.25.0",
            "plotly>=5.15.0",
        ],
        "viz": [
            "plotly>=5.15.0",
            "seaborn>=0.12.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "mathphysics-exp=mathphysics.main:main",
        ],
    },
)