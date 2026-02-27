"""Unified Visualization Suite for Mathematical Physics.

Provides high-resolution, publication-quality visualizations for all
framework modules, featuring dark-mode neon aesthetics and standard
scientific plotting with error bars and statistical annotations.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from sklearn.decomposition import PCA

from .config import Config


if TYPE_CHECKING:
    from pathlib import Path


# Configure matplotlib defaults
plt.rcParams.update(
    {
        "figure.dpi": 150,
        "savefig.dpi": 300,
        "font.size": 12,
        "font.family": "serif",
        "axes.labelsize": 14,
        "axes.titlesize": 16,
        "savefig.bbox": "tight",
        "text.usetex": False,  # Set to True if system has LaTeX
    }
)


class ColorScheme(Enum):
    NEON_DARK = "neon_dark"
    CYBERPUNK = "cyberpunk"
    SCIENTIFIC = "scientific"


@dataclass
class VizConfig:
    width_pixels: int = 3160
    height_pixels: int = 2820
    dpi: int = 300
    color_scheme: ColorScheme = ColorScheme.NEON_DARK
    background_color: str = "#0a0a0a"
    text_color: str = "#e0e0e0"
    output_dir: Path = field(default_factory=lambda: Config.FIGURES_DIR)

    def get_size_inches(self) -> tuple[float, float]:
        return (self.width_pixels / self.dpi, self.height_pixels / self.dpi)


class Visualizer:
    """Main visualization engine with statistical rigor."""

    def __init__(self, config: VizConfig | None = None) -> None:
        self.config = config or VizConfig()
        self._setup_style()
        self.colors = self._get_palette()

    def _setup_style(self):
        plt.style.use("dark_background")
        plt.rcParams.update(
            {
                "figure.facecolor": self.config.background_color,
                "axes.facecolor": self.config.background_color,
                "text.color": self.config.text_color,
                "axes.edgecolor": "#444444",
                "grid.color": "#222222",
            }
        )

    def _get_palette(self) -> list[str]:
        if self.config.color_scheme == ColorScheme.CYBERPUNK:
            return ["#00d9ff", "#ff006e", "#ffbe0b", "#8338ec", "#3a86ff"]
        return ["#00ffff", "#ff00ff", "#ffff00", "#00ff00", "#ff0080"]

    def plot_roots_2d(
        self, roots: np.ndarray, title: str = "Root System", weights: np.ndarray | None = None
    ) -> plt.Figure:
        pca = PCA(n_components=2)
        roots_2d = pca.fit_transform(roots)
        fig, ax = plt.subplots(figsize=self.config.get_size_inches())

        c_vals = weights if weights is not None else np.linalg.norm(roots, axis=1)

        scatter = ax.scatter(
            roots_2d[:, 0],
            roots_2d[:, 1],
            c=c_vals,
            cmap="viridis",
            s=100,
            alpha=0.8,
            edgecolors="white",
            linewidth=0.5,
        )

        label = "Harmonic Weight" if weights is not None else "Root Norm ||\u03b1||"
        plt.colorbar(scatter, label=label)
        ax.set_title(title, pad=20)
        ax.set_xlabel("Principal Component 1")
        ax.set_ylabel("Principal Component 2")
        ax.set_aspect("equal")
        ax.grid(True, alpha=0.2)
        return fig

    def plot_time_series_with_stats(
        self,
        x: np.ndarray,
        y: np.ndarray,
        y_err: np.ndarray | None = None,
        title: str = "Metric Evolution",
        xlabel: str = "Step",
        ylabel: str = "Value",
    ) -> plt.Figure:
        """Plot time series with error bars and significance markers."""
        fig, ax = plt.subplots(figsize=self.config.get_size_inches())

        ax.plot(x, y, color=self.colors[0], linewidth=2, label="Mean Trajectory")

        if y_err is not None:
            ax.fill_between(
                x, y - y_err, y + y_err, color=self.colors[0], alpha=0.2, label="1\u03c3 Confidence"
            )
            ax.errorbar(x, y, yerr=y_err, fmt="none", ecolor=self.colors[0], alpha=0.5, capsize=3)

        # Detect and mark significant peaks (p < 0.05)
        z_scores = (y - np.mean(y)) / (np.std(y) + 1e-10)
        significant = np.abs(z_scores) > 1.96
        if np.any(significant):
            ax.scatter(
                x[significant],
                y[significant],
                color=self.colors[1],
                s=50,
                marker="*",
                label="Significant Deviation (p < 0.05)",
                zorder=5,
            )

        ax.set_title(title)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.legend()
        ax.grid(True, alpha=0.1)
        return fig

    def plot_lbm_field(self, field: np.ndarray, title: str = "Simulation Field") -> plt.Figure:
        fig, ax = plt.subplots(figsize=self.config.get_size_inches())
        im = ax.imshow(field, cmap="magma", origin="lower", interpolation="bilinear")
        plt.colorbar(im, ax=ax, label="Magnitude")

        # Annotate max/min
        max_idx = np.unravel_index(np.argmax(field), field.shape)
        min_idx = np.unravel_index(np.argmin(field), field.shape)
        ax.plot(max_idx[1], max_idx[0], "ro", markersize=5, label="Local Max")
        ax.plot(min_idx[1], min_idx[0], "bo", markersize=5, label="Local Min")

        ax.set_title(title)
        ax.set_xlabel("Spatial X")
        ax.set_ylabel("Spatial Y")
        return fig

    def plot_interactive_roots(self, roots: np.ndarray, name: str = "roots"):
        """Generate high-resolution interactive HTML plot."""
        try:
            import pandas as pd  # noqa: PLC0415
            import plotly.express as px  # noqa: PLC0415

            pca = PCA(n_components=3)
            r3d = pca.fit_transform(roots)
            df = pd.DataFrame(r3d, columns=["PC1", "PC2", "PC3"])
            df["Norm"] = np.linalg.norm(roots, axis=1)

            fig = px.scatter_3d(
                df,
                x="PC1",
                y="PC2",
                z="PC3",
                color="Norm",
                template="plotly_dark",
                title=f"3D Root Projection: {name} (Interactive)",
                labels={"PC1": "Dim 1", "PC2": "Dim 2", "PC3": "Dim 3"},
            )
            path = self.config.output_dir / f"{name}_interactive.html"
            fig.write_html(str(path))
            print(f"Interactive plot saved to {path}")
        except ImportError:
            print("Plotly/Pandas not available for interactive plots")

    def plot_voronoi_2d(self, points: np.ndarray, title: str = "Voronoi Tesselation") -> plt.Figure:
        """Plot 2D Voronoi diagram of projected roots/lattice points."""
        from scipy.spatial import Voronoi, voronoi_plot_2d  # noqa: PLC0415

        pca = PCA(n_components=2)
        pts_2d = pca.fit_transform(points)
        vor = Voronoi(pts_2d)

        fig, ax = plt.subplots(figsize=self.config.get_size_inches())
        voronoi_plot_2d(
            vor,
            ax=ax,
            show_vertices=False,
            line_colors="cyan",
            line_width=1,
            line_alpha=0.6,
            point_size=2,
        )

        ax.set_title(title)
        ax.set_aspect("equal")
        ax.grid(False)
        return fig

    def plot_persistence_barcode(
        self, persistence: np.ndarray, title: str = "Persistence Barcode"
    ) -> plt.Figure:
        """Visualize topological features (homology) via barcode."""
        fig, ax = plt.subplots(figsize=self.config.get_size_inches())

        # persistence: array of [dimension, birth, death]
        for i, (dim, birth, death) in enumerate(persistence):
            color = self.colors[int(dim) % len(self.colors)]
            ax.plot([birth, death], [i, i], color=color, linewidth=2)

        ax.set_title(title)
        ax.set_xlabel("Scale (ε)")
        ax.set_ylabel("Feature Index")
        # Custom legend for dimensions
        from matplotlib.lines import Line2D  # noqa: PLC0415

        legend_elements = [
            Line2D([0], [0], color=self.colors[0], lw=2, label="H0 (Components)"),
            Line2D([0], [0], color=self.colors[1], lw=2, label="H1 (Loops)"),
        ]
        ax.legend(handles=legend_elements)
        return fig

    def save(self, fig: plt.Figure, name: str):
        path = self.config.output_dir / f"{name}.png"
        fig.savefig(path, dpi=self.config.dpi)
        plt.close(fig)
        print(f"Figure saved to {path}")


def create_all_plots():
    """Batch generate figures for the compendium."""
    viz = Visualizer()

    # 1. Roots
    from .algebras.roots import E8RootSystem  # noqa: PLC0415

    e8 = E8RootSystem()
    fig = viz.plot_roots_2d(e8.generate_roots(), "E8 Root System (240 Roots)")
    viz.save(fig, "e8_roots_pca")

    # 2. Synthetic Experiment Results (Demonstration)
    x = np.linspace(0, 10, 50)
    y = np.sin(x) + np.random.normal(0, 0.1, 50)
    y_err = np.full_like(y, 0.1)
    fig = viz.plot_time_series_with_stats(
        x,
        y,
        y_err,
        title="Harmonic Coherence Tracking",
        xlabel="Evolution Time (ps)",
        ylabel="Coherence Magnitude",
    )
    viz.save(fig, "coherence_stats")

    # 3. LBM Sample
    sample_field = np.random.randn(128, 128)
    fig = viz.plot_lbm_field(sample_field, "Stochastic Density Snapshot (SM89 Simulated)")
    viz.save(fig, "lbm_sample")
