"""Visualization Suite for Mathematical Physics Experiments.

Comprehensive visualization tools for:
- Cayley-Dickson algebras
- Fractal analysis
- E_8 root systems
- Lattice structures
- Modular forms
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional, Union
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection
import seaborn as sns
from pathlib import Path
import json


# Set publication-quality defaults
plt.rcParams['figure.dpi'] = 150
plt.rcParams['savefig.dpi'] = 300
plt.rcParams['font.size'] = 10
plt.rcParams['font.family'] = 'serif'
plt.rcParams['axes.labelsize'] = 11
plt.rcParams['axes.titlesize'] = 12
plt.rcParams['legend.fontsize'] = 9
plt.rcParams['xtick.labelsize'] = 9
plt.rcParams['ytick.labelsize'] = 9


class CayleyDicksonVisualizer:
    """Visualizer for Cayley-Dickson algebras."""

    @staticmethod
    def plot_multiplication_table(algebra_class, output_path: Optional[Path] = None):
        """Plot multiplication table for basis elements."""
        from . import cayley_dickson

        dim = algebra_class._dimension_static()
        if dim > 8:
            print(f"Skipping multiplication table for {dim}D (too large)")
            return

        # Generate multiplication table
        table = np.zeros((dim, dim))

        for i in range(dim):
            for j in range(dim):
                ei = algebra_class.basis_element(i)
                ej = algebra_class.basis_element(j)
                product = ei * ej

                # Store the dominant component
                table[i, j] = np.argmax(np.abs(product.coeffs))

        # Plot
        fig, ax = plt.subplots(figsize=(8, 7))

        im = ax.imshow(table, cmap='tab10', aspect='auto')

        # Labels
        ax.set_xticks(range(dim))
        ax.set_yticks(range(dim))

        basis_names = algebra_class.basis_element(0)._basis_names()
        ax.set_xticklabels([f"e{i}" if name == "" else name
                           for i, name in enumerate(basis_names)])
        ax.set_yticklabels([f"e{i}" if name == "" else name
                           for i, name in enumerate(basis_names)])

        ax.set_xlabel("Right operand")
        ax.set_ylabel("Left operand")
        ax.set_title(f"{algebra_class.__name__} Multiplication Table")

        plt.colorbar(im, ax=ax, label="Dominant basis component")
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_norm_distribution(algebra_class, num_samples: int = 1000,
                              output_path: Optional[Path] = None):
        """Plot distribution of norms for random elements."""
        norms = []

        for _ in range(num_samples):
            element = algebra_class.random(scale=1.0)
            norms.append(element.norm())

        fig, ax = plt.subplots(figsize=(10, 6))

        ax.hist(norms, bins=50, density=True, alpha=0.7, edgecolor='black')
        ax.axvline(np.mean(norms), color='red', linestyle='--',
                   label=f'Mean: {np.mean(norms):.3f}')
        ax.axvline(np.median(norms), color='green', linestyle='--',
                   label=f'Median: {np.median(norms):.3f}')

        ax.set_xlabel("Norm")
        ax.set_ylabel("Probability Density")
        ax.set_title(f"{algebra_class.__name__} Norm Distribution")
        ax.legend()
        ax.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_quaternion_rotation(output_path: Optional[Path] = None):
        """Visualize quaternion rotation."""
        from . import cayley_dickson

        fig = plt.figure(figsize=(12, 5))

        # Original vector
        v = np.array([1, 0, 0])

        # Rotation axis and angles
        axis = np.array([0, 0, 1])
        angles = np.linspace(0, 2*np.pi, 8)

        for idx, angle in enumerate(angles):
            ax = fig.add_subplot(2, 4, idx+1, projection='3d')

            # Create rotation quaternion
            q = cayley_dickson.Quaternion.from_axis_angle(axis, angle)

            # Rotate vector (simplified - would need proper implementation)
            # For visualization, just rotate around z-axis
            c, s = np.cos(angle), np.sin(angle)
            v_rot = np.array([c*v[0] - s*v[1], s*v[0] + c*v[1], v[2]])

            # Plot
            ax.quiver(0, 0, 0, v[0], v[1], v[2], color='blue',
                     arrow_length_ratio=0.2, label='Original')
            ax.quiver(0, 0, 0, v_rot[0], v_rot[1], v_rot[2], color='red',
                     arrow_length_ratio=0.2, label='Rotated')

            ax.set_xlim([-1.2, 1.2])
            ax.set_ylim([-1.2, 1.2])
            ax.set_zlim([-1.2, 1.2])
            ax.set_title(f"θ = {angle:.2f}")
            ax.set_xlabel('X')
            ax.set_ylabel('Y')
            ax.set_zlabel('Z')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()


class FractalVisualizer:
    """Visualizer for fractal analysis."""

    @staticmethod
    def plot_fractal(fractal_data: np.ndarray, title: str = "Fractal",
                    output_path: Optional[Path] = None, cmap: str = 'hot'):
        """Plot fractal image."""
        fig, ax = plt.subplots(figsize=(10, 8))

        im = ax.imshow(fractal_data, cmap=cmap, origin='lower',
                      interpolation='bilinear')
        ax.set_title(title)
        ax.axis('off')

        plt.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path, bbox_inches='tight')
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_dimension_calculation(result, output_path: Optional[Path] = None):
        """Plot dimension calculation with log-log plot."""
        from . import fractal_analysis

        if not isinstance(result, fractal_analysis.FractalDimensionResult):
            print("Invalid result type")
            return

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Log-log plot
        log_scales = np.log(result.scales)
        log_measures = np.log(result.measures)

        ax1.scatter(log_scales, log_measures, alpha=0.6, s=50)

        # Fit line
        slope, intercept = np.polyfit(log_scales, log_measures, 1)
        x_fit = np.array([log_scales.min(), log_scales.max()])
        y_fit = slope * x_fit + intercept

        ax1.plot(x_fit, y_fit, 'r--', linewidth=2,
                label=f'Slope = {slope:.4f}')

        ax1.set_xlabel('log(scale)')
        ax1.set_ylabel('log(measure)')
        ax1.set_title(f'{result.method.replace("_", " ").title()}\n'
                     f'Dimension: {result.dimension:.4f} ± {result.error:.4f}')
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # Regular plot
        ax2.loglog(result.scales, result.measures, 'o-', markersize=6)
        ax2.set_xlabel('Scale')
        ax2.set_ylabel('Measure')
        ax2.set_title(f'R² = {result.r_squared:.6f}')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_fractal_comparison(fractals_dict: Dict[str, np.ndarray],
                               output_path: Optional[Path] = None):
        """Plot multiple fractals for comparison."""
        n = len(fractals_dict)
        cols = min(3, n)
        rows = (n + cols - 1) // cols

        fig, axes = plt.subplots(rows, cols, figsize=(5*cols, 5*rows))
        if n == 1:
            axes = [axes]
        else:
            axes = axes.flatten()

        for idx, (name, data) in enumerate(fractals_dict.items()):
            if data.ndim == 2:
                axes[idx].imshow(data, cmap='hot', origin='lower')
            else:
                axes[idx].scatter(data[:, 0], data[:, 1], s=1, alpha=0.5)

            axes[idx].set_title(name)
            axes[idx].axis('off')

        # Hide unused subplots
        for idx in range(n, len(axes)):
            axes[idx].axis('off')

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()


class LieAlgebraVisualizer:
    """Visualizer for Lie algebras."""

    @staticmethod
    def plot_root_system_2d(roots: np.ndarray, title: str = "Root System",
                           output_path: Optional[Path] = None):
        """Plot 2D projection of root system."""
        if roots.shape[1] < 2:
            print("Need at least 2D roots")
            return

        fig, ax = plt.subplots(figsize=(10, 10))

        # Use first two coordinates
        x = roots[:, 0]
        y = roots[:, 1]

        # Color by norm
        norms = np.linalg.norm(roots, axis=1)
        scatter = ax.scatter(x, y, c=norms, cmap='viridis', s=50, alpha=0.7)

        # Draw vectors from origin
        for i in range(min(50, len(roots))):  # Limit for clarity
            ax.arrow(0, 0, x[i]*0.9, y[i]*0.9,
                    head_width=0.05, head_length=0.1,
                    fc='gray', ec='gray', alpha=0.3, linewidth=0.5)

        ax.axhline(0, color='k', linewidth=0.5)
        ax.axvline(0, color='k', linewidth=0.5)
        ax.set_xlabel("Dimension 1")
        ax.set_ylabel("Dimension 2")
        ax.set_title(f"{title}\n{len(roots)} roots")
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.3)

        plt.colorbar(scatter, ax=ax, label="Norm")
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_root_system_3d(roots: np.ndarray, title: str = "Root System",
                           output_path: Optional[Path] = None):
        """Plot 3D projection of root system."""
        if roots.shape[1] < 3:
            print("Need at least 3D roots")
            return

        fig = plt.figure(figsize=(12, 10))
        ax = fig.add_subplot(111, projection='3d')

        # Use first three coordinates
        x = roots[:, 0]
        y = roots[:, 1]
        z = roots[:, 2]

        # Color by norm
        norms = np.linalg.norm(roots, axis=1)
        scatter = ax.scatter(x, y, z, c=norms, cmap='viridis', s=30, alpha=0.6)

        ax.set_xlabel("Dimension 1")
        ax.set_ylabel("Dimension 2")
        ax.set_zlabel("Dimension 3")
        ax.set_title(f"{title}\n{len(roots)} roots (3D projection)")

        plt.colorbar(scatter, ax=ax, label="Norm", shrink=0.5)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_dynkin_diagram(graph, title: str = "Dynkin Diagram",
                           output_path: Optional[Path] = None):
        """Plot Dynkin diagram."""
        import networkx as nx

        fig, ax = plt.subplots(figsize=(12, 6))

        # Position nodes
        pos = nx.spring_layout(graph, k=2, iterations=50)

        # Draw
        nx.draw_networkx_nodes(graph, pos, node_color='lightblue',
                              node_size=800, ax=ax)
        nx.draw_networkx_labels(graph, pos,
                               {i: f"α{i+1}" for i in graph.nodes()},
                               font_size=12, ax=ax)
        nx.draw_networkx_edges(graph, pos, width=2, ax=ax)

        ax.set_title(title)
        ax.axis('off')
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_cartan_matrix(cartan_matrix: np.ndarray, title: str = "Cartan Matrix",
                          output_path: Optional[Path] = None):
        """Plot Cartan matrix as heatmap."""
        fig, ax = plt.subplots(figsize=(8, 7))

        im = ax.imshow(cartan_matrix, cmap='RdBu_r', aspect='auto',
                      vmin=-3, vmax=3)

        # Labels
        n = cartan_matrix.shape[0]
        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels([f"α{i+1}" for i in range(n)])
        ax.set_yticklabels([f"α{i+1}" for i in range(n)])

        # Annotate with values
        for i in range(n):
            for j in range(n):
                text = ax.text(j, i, int(cartan_matrix[i, j]),
                             ha="center", va="center", color="black", fontsize=10)

        ax.set_title(title)
        plt.colorbar(im, ax=ax)
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()


class LatticeVisualizer:
    """Visualizer for lattice structures."""

    @staticmethod
    def plot_lattice_points_2d(points: np.ndarray, title: str = "Lattice",
                              output_path: Optional[Path] = None):
        """Plot 2D lattice points."""
        if points.shape[1] < 2:
            print("Need at least 2D points")
            return

        fig, ax = plt.subplots(figsize=(10, 10))

        # Project to 2D if needed
        x = points[:, 0]
        y = points[:, 1]

        # Color by distance from origin
        distances = np.linalg.norm(points, axis=1)
        scatter = ax.scatter(x, y, c=distances, cmap='plasma',
                           s=20, alpha=0.6)

        # Highlight origin
        ax.scatter([0], [0], c='red', s=200, marker='*',
                  edgecolors='black', linewidths=2, label='Origin')

        ax.axhline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.axvline(0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_xlabel("Dimension 1")
        ax.set_ylabel("Dimension 2")
        ax.set_title(f"{title}\n{len(points)} points")
        ax.set_aspect('equal')
        ax.grid(True, alpha=0.2)
        ax.legend()

        plt.colorbar(scatter, ax=ax, label="Distance from origin")
        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()

    @staticmethod
    def plot_shell_structure(shells: Dict[float, int],
                            title: str = "Shell Structure",
                            output_path: Optional[Path] = None):
        """Plot shell structure histogram."""
        radii = sorted(shells.keys())
        counts = [shells[r] for r in radii]

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

        # Bar plot
        ax1.bar(range(len(radii)), counts, alpha=0.7, edgecolor='black')
        ax1.set_xlabel("Shell index")
        ax1.set_ylabel("Number of points")
        ax1.set_title(f"{title} - Point Count")
        ax1.grid(True, alpha=0.3, axis='y')

        # Log plot
        ax2.semilogy(radii[:20], counts[:20], 'o-', markersize=6)
        ax2.set_xlabel("Radius")
        ax2.set_ylabel("Number of points (log scale)")
        ax2.set_title(f"{title} - Growth Rate")
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()

        if output_path:
            plt.savefig(output_path)
            print(f"Saved to {output_path}")

        plt.close()


def create_all_visualizations(output_dir: Optional[Path] = None):
    """Create all visualizations."""
    if output_dir is None:
        output_dir = Path("/home/eirikr/MathScienceCompendium/experiments/results/figures")

    output_dir.mkdir(parents=True, exist_ok=True)

    print("\n" + "=" * 80)
    print("GENERATING VISUALIZATIONS")
    print("=" * 80)

    # Import modules
    from . import cayley_dickson, fractal_analysis, lie_algebras, lattice_theory

    # 1. Cayley-Dickson visualizations
    print("\n--- Cayley-Dickson Algebras ---")

    print("Complex multiplication table...")
    CayleyDicksonVisualizer.plot_multiplication_table(
        cayley_dickson.Complex,
        output_dir / "complex_multiplication_table.png"
    )

    print("Quaternion multiplication table...")
    CayleyDicksonVisualizer.plot_multiplication_table(
        cayley_dickson.Quaternion,
        output_dir / "quaternion_multiplication_table.png"
    )

    print("Octonion norm distribution...")
    CayleyDicksonVisualizer.plot_norm_distribution(
        cayley_dickson.Octonion,
        num_samples=1000,
        output_path=output_dir / "octonion_norm_distribution.png"
    )

    print("Quaternion rotation visualization...")
    CayleyDicksonVisualizer.plot_quaternion_rotation(
        output_dir / "quaternion_rotation.png"
    )

    # 2. Fractal visualizations
    print("\n--- Fractals ---")

    print("Generating Mandelbrot set...")
    generator = fractal_analysis.FractalGenerator()
    mandelbrot = generator.mandelbrot_set(width=800, height=600, max_iter=100)
    FractalVisualizer.plot_fractal(
        mandelbrot,
        title="Mandelbrot Set",
        output_path=output_dir / "mandelbrot_set.png",
        cmap='hot'
    )

    print("Generating Julia set...")
    julia = generator.julia_set(c_real=-0.7, c_imag=0.27015,
                               width=800, height=600, max_iter=100)
    FractalVisualizer.plot_fractal(
        julia,
        title="Julia Set (c = -0.7 + 0.27015i)",
        output_path=output_dir / "julia_set.png",
        cmap='twilight'
    )

    # 3. E_8 visualizations
    print("\n--- E_8 Lie Algebra ---")

    e8 = lie_algebras.E8RootSystem()
    roots = e8.generate_roots()

    print("E_8 root system 2D projection...")
    LieAlgebraVisualizer.plot_root_system_2d(
        roots,
        title="E_8 Root System (2D Projection)",
        output_path=output_dir / "e8_roots_2d.png"
    )

    print("E_8 root system 3D projection...")
    LieAlgebraVisualizer.plot_root_system_3d(
        roots,
        title="E_8 Root System",
        output_path=output_dir / "e8_roots_3d.png"
    )

    print("E_8 Cartan matrix...")
    cartan = e8.cartan_matrix()
    LieAlgebraVisualizer.plot_cartan_matrix(
        cartan,
        title="E_8 Cartan Matrix",
        output_path=output_dir / "e8_cartan_matrix.png"
    )

    print("E_8 Dynkin diagram...")
    dynkin = e8.dynkin_diagram()
    LieAlgebraVisualizer.plot_dynkin_diagram(
        dynkin,
        title="E_8 Dynkin Diagram",
        output_path=output_dir / "e8_dynkin_diagram.png"
    )

    # 4. Lattice visualizations
    print("\n--- Lattices ---")

    e8_lattice = lattice_theory.E8Lattice()
    lattice_points = e8_lattice.generate_lattice_points(max_norm=5.0)

    print("E_8 lattice points...")
    LatticeVisualizer.plot_lattice_points_2d(
        lattice_points,
        title="E_8 Lattice (2D Projection)",
        output_path=output_dir / "e8_lattice_2d.png"
    )

    print("E_8 shell structure...")
    shells = e8_lattice.shell_structure(num_shells=10)
    LatticeVisualizer.plot_shell_structure(
        shells,
        title="E_8 Lattice Shell Structure",
        output_path=output_dir / "e8_shell_structure.png"
    )

    print("\n" + "=" * 80)
    print(f"All visualizations saved to {output_dir}")
    print("=" * 80)


if __name__ == "__main__":
    create_all_visualizations()