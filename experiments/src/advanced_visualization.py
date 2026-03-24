"""Advanced Visualization Engine for Mathematical Physics Compendium.

This module provides publication-quality visualization capabilities for the entire
Mathematical Physics Compendium, including E7/E8 root systems, quantum circuits,
harmonic evolution, LBM density fields, AQGM spectral analysis, and projective geometry.

Features:
- High-resolution (3160x2820 pixels) publication-quality figures
- Dark mode aesthetics with neon color schemes
- Colorblind-friendly palette options
- Support for PNG, SVG, and PDF exports
- Batch figure generation capabilities
- Integration with all compendium modules

Technical Specifications:
- DPI: 300 (print quality), 150 (display quality)
- Color schemes: Dark backgrounds with neon/cyberpunk aesthetics
- Fonts: DejaVu Sans, Computer Modern (LaTeX), or system defaults
- Grid overlays and proper axis labeling
- Comprehensive legend and annotation support

Author: Claude Code
Date: January 2025
"""

from __future__ import annotations
from typing import List, Tuple, Dict, Any, Optional, Union, Callable
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch, Circle, Rectangle, Polygon, Wedge, PathPatch
from matplotlib.path import Path as MPath
from matplotlib.collections import LineCollection, PatchCollection
from matplotlib.colors import LinearSegmentedColormap, ListedColormap, Normalize
from matplotlib.cm import ScalarMappable
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import Axes3D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection, Line3DCollection
import seaborn as sns
from scipy.spatial.distance import pdist, squareform
from scipy.linalg import svd
from sklearn.decomposition import PCA
from sklearn.preprocessing import StandardScaler
import warnings
from pathlib import Path
import json
from dataclasses import dataclass, field
from enum import Enum
import colorsys

# Import quantum visualization tools
try:
    from qiskit.visualization import circuit_drawer
    QISKIT_AVAILABLE = True
except ImportError:
    QISKIT_AVAILABLE = False
    warnings.warn("Qiskit not available for circuit visualization")

# Configure matplotlib for publication quality
plt.rcParams.update({
    'figure.dpi': 150,
    'savefig.dpi': 300,
    'font.size': 12,
    'font.family': 'sans-serif',
    'font.sans-serif': ['DejaVu Sans', 'Helvetica', 'Arial'],
    'axes.labelsize': 14,
    'axes.titlesize': 16,
    'legend.fontsize': 11,
    'xtick.labelsize': 11,
    'ytick.labelsize': 11,
    'lines.linewidth': 2,
    'lines.markersize': 8,
    'axes.linewidth': 1.5,
    'axes.grid': True,
    'grid.alpha': 0.3,
    'grid.linestyle': '--',
    'axes.axisbelow': True,
    'figure.autolayout': False,
    'figure.constrained_layout.use': True,
    'savefig.bbox': 'tight',
    'savefig.pad_inches': 0.1,
    'text.usetex': False,  # Set to True if LaTeX is available
    'mathtext.fontset': 'stix',
    'mathtext.default': 'regular'
})


class ColorScheme(Enum):
    """Available color schemes for visualizations."""
    NEON_DARK = "neon_dark"
    CYBERPUNK = "cyberpunk"
    SCIENTIFIC = "scientific"
    COLORBLIND = "colorblind"
    MONOCHROME = "monochrome"


class ExportFormat(Enum):
    """Supported export formats."""
    PNG = "png"
    SVG = "svg"
    PDF = "pdf"
    EPS = "eps"


@dataclass
class VisualizationConfig:
    """Configuration for advanced visualizations."""

    # Resolution settings
    width_pixels: int = 3160
    height_pixels: int = 2820
    dpi: int = 300

    # Color scheme
    color_scheme: ColorScheme = ColorScheme.NEON_DARK
    background_color: str = '#0a0a0a'
    grid_color: str = '#333333'
    text_color: str = '#e0e0e0'

    # Export settings
    export_format: ExportFormat = ExportFormat.PNG
    output_dir: Path = Path("figures")
    filename_prefix: str = "mathphys"

    # Style settings
    use_dark_mode: bool = True
    show_grid: bool = True
    grid_alpha: float = 0.3
    use_glow_effect: bool = True
    glow_intensity: float = 0.5

    # Font settings
    title_size: int = 18
    label_size: int = 14
    tick_size: int = 11
    legend_size: int = 11

    # Layout settings
    tight_layout: bool = True
    constrained_layout: bool = True
    subplot_spacing: float = 0.3

    def __post_init__(self):
        """Validate and create output directory."""
        self.output_dir = Path(self.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def get_figure_size(self) -> Tuple[float, float]:
        """Calculate figure size in inches."""
        width_inches = self.width_pixels / self.dpi
        height_inches = self.height_pixels / self.dpi
        return (width_inches, height_inches)


class ColorPalettes:
    """Collection of color palettes for different visualization needs."""

    @staticmethod
    def get_neon_colors() -> List[str]:
        """Get neon color palette for dark backgrounds."""
        return [
            '#00ffff',  # Cyan
            '#ff00ff',  # Magenta
            '#ffff00',  # Yellow
            '#00ff00',  # Lime
            '#ff0080',  # Pink
            '#80ff00',  # Chartreuse
            '#ff8000',  # Orange
            '#00ff80',  # Spring green
            '#8000ff',  # Violet
            '#ff0040',  # Red-pink
        ]

    @staticmethod
    def get_cyberpunk_colors() -> List[str]:
        """Get cyberpunk-themed colors."""
        return [
            '#00d9ff',  # Electric blue
            '#ff006e',  # Hot pink
            '#ffbe0b',  # Cyber yellow
            '#fb5607',  # Orange red
            '#8338ec',  # Purple
            '#3a86ff',  # Blue
            '#06ffa5',  # Mint
            '#ff4365',  # Radical red
            '#00f5ff',  # Cyan
            '#c77dff',  # Lavender
        ]

    @staticmethod
    def get_colorblind_safe() -> List[str]:
        """Get colorblind-safe palette (Paul Tol's scheme)."""
        return [
            '#332288',  # Dark blue
            '#88CCEE',  # Light blue
            '#44AA99',  # Teal
            '#117733',  # Green
            '#999933',  # Olive
            '#DDCC77',  # Sand
            '#CC6677',  # Rose
            '#882255',  # Purple
            '#AA4499',  # Magenta
            '#DDDDDD',  # Light gray
        ]

    @staticmethod
    def get_scientific_colors() -> List[str]:
        """Get traditional scientific color palette."""
        return [
            '#1f77b4',  # Blue
            '#ff7f0e',  # Orange
            '#2ca02c',  # Green
            '#d62728',  # Red
            '#9467bd',  # Purple
            '#8c564b',  # Brown
            '#e377c2',  # Pink
            '#7f7f7f',  # Gray
            '#bcbd22',  # Olive
            '#17becf',  # Cyan
        ]

    @staticmethod
    def create_glow_effect(color: str, num_layers: int = 5) -> List[Tuple[str, float]]:
        """Create glow effect layers for a color.

        Args:
            color: Base color in hex format
            num_layers: Number of glow layers

        Returns:
            List of (color, alpha) tuples for layered plotting
        """
        # Convert hex to RGB
        color_rgb = tuple(int(color.lstrip('#')[i:i+2], 16)/255 for i in (0, 2, 4))

        layers = []
        for i in range(num_layers):
            alpha = 0.3 * (1 - i/num_layers)
            width_mult = 1 + 2 * i
            layers.append((color, alpha, width_mult))

        return layers


class AdvancedVisualizer:
    """Main class for advanced scientific visualizations."""

    def __init__(self, config: Optional[VisualizationConfig] = None):
        """Initialize visualizer with configuration."""
        self.config = config or VisualizationConfig()
        self._setup_style()
        self.colors = self._get_color_palette()

    def _setup_style(self) -> None:
        """Setup matplotlib style based on configuration."""
        if self.config.use_dark_mode:
            plt.style.use('dark_background')

        # Update rcParams based on config
        plt.rcParams.update({
            'figure.facecolor': self.config.background_color,
            'axes.facecolor': self.config.background_color,
            'axes.edgecolor': self.config.text_color,
            'axes.labelcolor': self.config.text_color,
            'text.color': self.config.text_color,
            'xtick.color': self.config.text_color,
            'ytick.color': self.config.text_color,
            'grid.color': self.config.grid_color,
            'grid.alpha': self.config.grid_alpha,
            'legend.facecolor': self.config.background_color,
            'legend.edgecolor': self.config.text_color,
            'font.size': self.config.label_size,
            'axes.titlesize': self.config.title_size,
            'axes.labelsize': self.config.label_size,
            'xtick.labelsize': self.config.tick_size,
            'ytick.labelsize': self.config.tick_size,
            'legend.fontsize': self.config.legend_size,
        })

    def _get_color_palette(self) -> List[str]:
        """Get color palette based on configuration."""
        if self.config.color_scheme == ColorScheme.NEON_DARK:
            return ColorPalettes.get_neon_colors()
        elif self.config.color_scheme == ColorScheme.CYBERPUNK:
            return ColorPalettes.get_cyberpunk_colors()
        elif self.config.color_scheme == ColorScheme.COLORBLIND:
            return ColorPalettes.get_colorblind_safe()
        elif self.config.color_scheme == ColorScheme.SCIENTIFIC:
            return ColorPalettes.get_scientific_colors()
        else:
            # Monochrome
            return ['#ffffff'] * 10

    def save_figure(self, fig: plt.Figure, name: str) -> Path:
        """Save figure with configured settings.

        Args:
            fig: Matplotlib figure
            name: Base filename (without extension)

        Returns:
            Path to saved figure
        """
        filename = f"{self.config.filename_prefix}_{name}.{self.config.export_format.value}"
        filepath = self.config.output_dir / filename

        fig.savefig(
            filepath,
            dpi=self.config.dpi,
            facecolor=self.config.background_color,
            edgecolor='none',
            bbox_inches='tight',
            pad_inches=0.1
        )

        print(f"Saved figure to {filepath}")
        return filepath

    def plot_e7_root_system_2d(self, root_system: Optional[np.ndarray] = None) -> plt.Figure:
        """Create 2D PCA projection of E7 root system.

        Args:
            root_system: Optional pre-computed root system array

        Returns:
            Matplotlib figure
        """
        # Import E7 module
        from e7_root_system import E7RootSystem

        if root_system is None:
            e7 = E7RootSystem()
            root_system = e7.generate_roots(include_zero=True)  # 127 vectors

        # Perform PCA
        pca = PCA(n_components=2)
        roots_2d = pca.fit_transform(root_system)

        # Separate integer and half-integer roots
        is_integer = np.all(np.abs(root_system % 1) < 1e-10, axis=1)

        # Create figure
        fig, ax = plt.subplots(figsize=self.config.get_figure_size())

        # Plot with glow effect if enabled
        if self.config.use_glow_effect:
            # Integer roots
            for color, alpha, width in ColorPalettes.create_glow_effect(self.colors[0]):
                ax.scatter(roots_2d[is_integer, 0], roots_2d[is_integer, 1],
                          c=color, alpha=alpha, s=50*width, label=None)

            # Half-integer roots
            for color, alpha, width in ColorPalettes.create_glow_effect(self.colors[1]):
                ax.scatter(roots_2d[~is_integer, 0], roots_2d[~is_integer, 1],
                          c=color, alpha=alpha, s=50*width, marker='^', label=None)

        # Plot main points
        ax.scatter(roots_2d[is_integer, 0], roots_2d[is_integer, 1],
                  c=self.colors[0], s=100, label='Integer roots', zorder=10)
        ax.scatter(roots_2d[~is_integer, 0], roots_2d[~is_integer, 1],
                  c=self.colors[1], s=100, marker='^', label='Half-integer roots', zorder=10)

        # Add Weyl chamber boundaries (simplified)
        theta = np.linspace(0, 2*np.pi, 7, endpoint=False)
        for t in theta:
            ax.plot([0, 3*np.cos(t)], [0, 3*np.sin(t)],
                   color=self.config.grid_color, linestyle='--', alpha=0.5)

        ax.set_xlabel(f'PC1 ({pca.explained_variance_ratio_[0]:.1%} variance)')
        ax.set_ylabel(f'PC2 ({pca.explained_variance_ratio_[1]:.1%} variance)')
        ax.set_title('E7 Root System - 2D PCA Projection (126 roots + zero)',
                    fontsize=self.config.title_size)
        ax.legend(loc='upper right')
        ax.grid(True, alpha=self.config.grid_alpha)
        ax.set_aspect('equal')

        return fig

    def plot_e8_root_system_3d(self, root_system: Optional[np.ndarray] = None,
                               angles: List[Tuple[float, float]] = None) -> plt.Figure:
        """Create 3D PCA projection of E8 root system with multiple views.

        Args:
            root_system: Optional pre-computed E8 root system
            angles: List of (elevation, azimuth) viewing angles

        Returns:
            Matplotlib figure with multiple 3D views
        """
        # Import E8 module
        from quantum_e8_circuits import E8RootSystem

        if root_system is None:
            e8 = E8RootSystem()
            root_system = e8.generate_roots()  # 240 roots

        if angles is None:
            angles = [(30, 45), (30, 135), (60, 45), (15, 225)]

        # Perform PCA
        pca = PCA(n_components=3)
        roots_3d = pca.fit_transform(root_system)

        # Classify roots
        is_integer = np.all(np.abs(root_system % 1) < 1e-10, axis=1)

        # Create figure with subplots
        fig = plt.figure(figsize=self.config.get_figure_size())
        gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.2)

        for idx, (elev, azim) in enumerate(angles):
            ax = fig.add_subplot(gs[idx // 2, idx % 2], projection='3d')

            # Plot integer roots
            ax.scatter(roots_3d[is_integer, 0],
                      roots_3d[is_integer, 1],
                      roots_3d[is_integer, 2],
                      c=self.colors[0], s=20, alpha=0.8, label='Integer')

            # Plot half-integer roots
            ax.scatter(roots_3d[~is_integer, 0],
                      roots_3d[~is_integer, 1],
                      roots_3d[~is_integer, 2],
                      c=self.colors[1], s=20, alpha=0.8, marker='^', label='Half-integer')

            # Add coordinate axes
            axis_length = np.max(np.abs(roots_3d)) * 0.8
            ax.plot([0, axis_length], [0, 0], [0, 0], 'r-', alpha=0.3, linewidth=2)
            ax.plot([0, 0], [0, axis_length], [0, 0], 'g-', alpha=0.3, linewidth=2)
            ax.plot([0, 0], [0, 0], [0, axis_length], 'b-', alpha=0.3, linewidth=2)

            ax.set_xlabel('PC1', labelpad=10)
            ax.set_ylabel('PC2', labelpad=10)
            ax.set_zlabel('PC3', labelpad=10)
            ax.set_title(f'View: elev={elev}, azim={azim}', fontsize=12)
            ax.view_init(elev=elev, azim=azim)

            if idx == 0:
                ax.legend(loc='upper left', fontsize=9)

            # Set background
            ax.xaxis.pane.fill = False
            ax.yaxis.pane.fill = False
            ax.zaxis.pane.fill = False
            ax.grid(True, alpha=self.config.grid_alpha)

        fig.suptitle('E8 Root System - 3D PCA Projections (240 roots)',
                    fontsize=self.config.title_size, y=0.98)

        return fig

    def plot_quantum_circuit(self, circuit_type: str = 'e7_oracle') -> plt.Figure:
        """Visualize quantum circuits for E7/E8 operations.

        Args:
            circuit_type: Type of circuit ('e7_oracle', 'e8_oracle', 'grover', 'state_prep')

        Returns:
            Matplotlib figure
        """
        if not QISKIT_AVAILABLE:
            fig, ax = plt.subplots(figsize=self.config.get_figure_size())
            ax.text(0.5, 0.5, 'Qiskit not available for circuit visualization',
                   ha='center', va='center', fontsize=20)
            ax.set_xlim(0, 1)
            ax.set_ylim(0, 1)
            ax.axis('off')
            return fig

        from qiskit import QuantumCircuit

        # Create sample circuits
        if circuit_type == 'e7_oracle':
            qc = self._create_e7_oracle_circuit()
        elif circuit_type == 'e8_oracle':
            qc = self._create_e8_oracle_circuit()
        elif circuit_type == 'grover':
            qc = self._create_grover_circuit()
        else:  # state_prep
            qc = self._create_state_prep_circuit()

        # Draw circuit
        fig = circuit_drawer(qc, output='mpl', style={
            'backgroundcolor': self.config.background_color,
            'textcolor': self.config.text_color,
            'linecolor': self.colors[0],
            'creglinecolor': self.colors[1],
            'gatetextcolor': self.config.text_color,
            'gatefacecolor': self.colors[2],
            'barrierfacecolor': self.colors[3],
        }, fold=20, fontsize=10)

        # Adjust figure size
        fig.set_size_inches(self.config.get_figure_size())

        return fig

    def _create_e7_oracle_circuit(self) -> 'QuantumCircuit':
        """Create sample E7 oracle circuit."""
        from qiskit import QuantumCircuit

        # Simplified 7-qubit demonstration
        qc = QuantumCircuit(7, name='E7 Oracle')

        # Add Hadamard gates
        for i in range(7):
            qc.h(i)

        qc.barrier()

        # Add oracle structure
        qc.cx(0, 1)
        qc.cx(1, 2)
        qc.cx(2, 3)
        qc.cx(3, 4)
        qc.cx(4, 5)
        qc.cx(5, 6)
        qc.cx(6, 0)  # Cycle

        qc.barrier()

        # Multi-controlled phase
        qc.mcp(np.pi, list(range(6)), 6)

        return qc

    def _create_e8_oracle_circuit(self) -> 'QuantumCircuit':
        """Create sample E8 oracle circuit."""
        from qiskit import QuantumCircuit

        # Simplified 8-qubit demonstration
        qc = QuantumCircuit(8, name='E8 Oracle')

        # Hadamard layer
        for i in range(8):
            qc.h(i)

        qc.barrier()

        # E8 structure with entangling gates
        for i in range(7):
            qc.cx(i, i+1)
        qc.cx(7, 0)  # Close the loop

        # Add controlled rotations
        for i in range(0, 8, 2):
            qc.cry(np.pi/4, i, (i+1)%8)

        qc.barrier()

        return qc

    def _create_grover_circuit(self) -> 'QuantumCircuit':
        """Create sample Grover iteration circuit."""
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(5, name='Grover Iteration')

        # Oracle
        qc.h(4)
        qc.mct([0, 1, 2, 3], 4)
        qc.h(4)

        qc.barrier()

        # Diffuser
        for i in range(4):
            qc.h(i)
            qc.x(i)

        qc.h(3)
        qc.mct([0, 1, 2], 3)
        qc.h(3)

        for i in range(4):
            qc.x(i)
            qc.h(i)

        return qc

    def _create_state_prep_circuit(self) -> 'QuantumCircuit':
        """Create sample state preparation circuit."""
        from qiskit import QuantumCircuit

        qc = QuantumCircuit(4, name='State Preparation')

        # Prepare superposition
        for i in range(4):
            qc.h(i)

        # Entangle pairs
        qc.cx(0, 1)
        qc.cx(2, 3)

        # Rotation layer
        for i in range(4):
            qc.ry(np.pi/6, i)

        # Final entanglement
        qc.cx(1, 2)

        return qc

    def plot_harmonic_evolution(self, genesis_harmonics: Optional[Any] = None,
                               timesteps: int = 6) -> plt.Figure:
        """Plot harmonic evolution with ZPE envelopes.

        Args:
            genesis_harmonics: Optional harmonics data
            timesteps: Number of time steps to show

        Returns:
            Matplotlib figure
        """
        from genesis_harmonics import GenesisHarmonics, MaterialType

        if genesis_harmonics is None:
            genesis_harmonics = GenesisHarmonics(
                num_layers=7,
                base_frequency=1e14,
                material=MaterialType.TOURMALINE
            )

        # Generate evolution data
        times = np.linspace(0, 1e-12, timesteps)

        fig = plt.figure(figsize=self.config.get_figure_size())
        gs = GridSpec(2, 3, figure=fig, hspace=0.3, wspace=0.25)

        for idx, t in enumerate(times):
            ax = fig.add_subplot(gs[idx // 3, idx % 3])

            # Evolve harmonics
            state = genesis_harmonics.evolve(t)
            frequencies = genesis_harmonics.layer_frequencies
            amplitudes = np.abs(state['harmonic_amplitudes'])

            # Plot with glow effect
            if self.config.use_glow_effect:
                for color, alpha, width in ColorPalettes.create_glow_effect(self.colors[0]):
                    ax.plot(frequencies/1e14, amplitudes,
                           color=color, alpha=alpha, linewidth=width)

            ax.plot(frequencies/1e14, amplitudes,
                   color=self.colors[0], linewidth=2, label='Harmonic')

            # Add ZPE envelope
            zpe_envelope = genesis_harmonics.calculate_zpe_envelope(frequencies)
            ax.fill_between(frequencies/1e14, 0, zpe_envelope,
                           color=self.colors[2], alpha=0.2, label='ZPE')

            ax.set_xlabel('Frequency (10^14 Hz)')
            ax.set_ylabel('Amplitude')
            ax.set_title(f't = {t*1e12:.2f} ps', fontsize=12)
            ax.grid(True, alpha=self.config.grid_alpha)
            ax.set_ylim([0, 1.2])

            if idx == 0:
                ax.legend(loc='upper right', fontsize=9)

        fig.suptitle('Harmonic Evolution with ZPE Envelopes',
                    fontsize=self.config.title_size, y=0.98)

        return fig

    def plot_material_response(self) -> plt.Figure:
        """Plot material response curves for Tourmaline, Quartz, and BST.

        Returns:
            Matplotlib figure
        """
        from genesis_harmonics import GenesisHarmonics, MaterialType

        materials = [MaterialType.TOURMALINE, MaterialType.QUARTZ, MaterialType.BST]

        fig, axes = plt.subplots(1, 3, figsize=self.config.get_figure_size())

        frequencies = np.logspace(10, 16, 1000)  # 10^10 to 10^16 Hz

        for idx, (ax, material) in enumerate(zip(axes, materials)):
            # Create harmonics with material
            gh = GenesisHarmonics(material=material)

            # Get material response
            response = []
            for f in frequencies:
                resp = gh.material_properties.response_function(2*np.pi*f)
                response.append(np.abs(resp))

            response = np.array(response)

            # Plot magnitude
            if self.config.use_glow_effect:
                for color, alpha, width in ColorPalettes.create_glow_effect(self.colors[idx]):
                    ax.loglog(frequencies, response,
                             color=color, alpha=alpha, linewidth=width)

            ax.loglog(frequencies, response,
                     color=self.colors[idx], linewidth=2)

            # Mark resonances
            for res_freq in gh.material_properties.resonance_frequencies:
                ax.axvline(res_freq, color=self.colors[3],
                          linestyle='--', alpha=0.5)

            ax.set_xlabel('Frequency (Hz)')
            ax.set_ylabel('Response Magnitude')
            ax.set_title(material.value.capitalize(), fontsize=14)
            ax.grid(True, alpha=self.config.grid_alpha, which='both')

        fig.suptitle('Material Response Functions',
                    fontsize=self.config.title_size, y=0.98)

        return fig

    def plot_lbm_density_field(self, density_field: Optional[np.ndarray] = None,
                               velocity_field: Optional[np.ndarray] = None) -> plt.Figure:
        """Plot LBM density and velocity fields.

        Args:
            density_field: 2D density array
            velocity_field: 2D velocity array (2 components)

        Returns:
            Matplotlib figure
        """
        # Generate sample data if not provided
        if density_field is None:
            x = np.linspace(-5, 5, 100)
            y = np.linspace(-5, 5, 100)
            X, Y = np.meshgrid(x, y)

            # Create vortex-like density field
            R = np.sqrt(X**2 + Y**2)
            density_field = 1.0 + 0.3 * np.exp(-R**2/4) * np.sin(4*np.arctan2(Y, X))

            # Create velocity field
            velocity_field = np.zeros((100, 100, 2))
            velocity_field[:, :, 0] = -Y / (R + 0.1)  # u component
            velocity_field[:, :, 1] = X / (R + 0.1)   # v component

        fig = plt.figure(figsize=self.config.get_figure_size())
        gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

        # Density field
        ax1 = fig.add_subplot(gs[0, 0])
        im1 = ax1.imshow(density_field, cmap='plasma', origin='lower')
        ax1.set_title('Density Field', fontsize=14)
        ax1.set_xlabel('x')
        ax1.set_ylabel('y')
        plt.colorbar(im1, ax=ax1, label='Density')

        # Velocity magnitude
        ax2 = fig.add_subplot(gs[0, 1])
        vel_mag = np.sqrt(velocity_field[:, :, 0]**2 + velocity_field[:, :, 1]**2)
        im2 = ax2.imshow(vel_mag, cmap='viridis', origin='lower')
        ax2.set_title('Velocity Magnitude', fontsize=14)
        ax2.set_xlabel('x')
        ax2.set_ylabel('y')
        plt.colorbar(im2, ax=ax2, label='|v|')

        # Velocity vectors
        ax3 = fig.add_subplot(gs[1, 0])
        skip = 5  # Skip for clarity
        x_idx = np.arange(0, density_field.shape[1], skip)
        y_idx = np.arange(0, density_field.shape[0], skip)
        X_grid, Y_grid = np.meshgrid(x_idx, y_idx)

        ax3.quiver(X_grid, Y_grid,
                  velocity_field[::skip, ::skip, 0],
                  velocity_field[::skip, ::skip, 1],
                  vel_mag[::skip, ::skip],
                  cmap='coolwarm', scale=20, width=0.003)
        ax3.set_title('Velocity Vectors', fontsize=14)
        ax3.set_xlabel('x')
        ax3.set_ylabel('y')
        ax3.set_aspect('equal')

        # Vorticity
        ax4 = fig.add_subplot(gs[1, 1])
        # Calculate vorticity (curl of velocity)
        dudy = np.gradient(velocity_field[:, :, 0], axis=0)
        dvdx = np.gradient(velocity_field[:, :, 1], axis=1)
        vorticity = dvdx - dudy

        im4 = ax4.imshow(vorticity, cmap='RdBu_r', origin='lower')
        ax4.set_title('Vorticity', fontsize=14)
        ax4.set_xlabel('x')
        ax4.set_ylabel('y')
        plt.colorbar(im4, ax=ax4, label='Vorticity')

        fig.suptitle('Lattice Boltzmann Method - Flow Fields',
                    fontsize=self.config.title_size, y=0.98)

        return fig

    def plot_aqgm_spectral_analysis(self) -> plt.Figure:
        """Plot AQGM spectral triple and heat kernel analysis.

        Returns:
            Matplotlib figure
        """
        # Generate sample spectral data
        eigenvalues = np.sort(np.random.gamma(2, 2, 500))

        fig = plt.figure(figsize=self.config.get_figure_size())
        gs = GridSpec(2, 2, figure=fig, hspace=0.3, wspace=0.3)

        # Eigenvalue distribution
        ax1 = fig.add_subplot(gs[0, 0])
        ax1.hist(eigenvalues, bins=50, color=self.colors[0],
                alpha=0.7, edgecolor=self.colors[1])
        ax1.set_xlabel('Eigenvalue')
        ax1.set_ylabel('Count')
        ax1.set_title('Spectral Triple Eigenvalue Distribution', fontsize=14)
        ax1.grid(True, alpha=self.config.grid_alpha)

        # Weyl law plot
        ax2 = fig.add_subplot(gs[0, 1])
        n_vals = np.arange(1, len(eigenvalues) + 1)
        theoretical = 2 * np.sqrt(n_vals)  # Weyl law approximation

        ax2.loglog(n_vals, eigenvalues, color=self.colors[0],
                  label='Actual', linewidth=2)
        ax2.loglog(n_vals, theoretical, '--', color=self.colors[2],
                  label='Weyl law', linewidth=2)
        ax2.set_xlabel('n')
        ax2.set_ylabel('λ_n')
        ax2.set_title('Eigenvalue Growth (Weyl Law)', fontsize=14)
        ax2.legend()
        ax2.grid(True, alpha=self.config.grid_alpha, which='both')

        # Heat kernel trace
        ax3 = fig.add_subplot(gs[1, 0])
        t_values = np.logspace(-3, 1, 100)
        heat_trace = []

        for t in t_values:
            trace = np.sum(np.exp(-eigenvalues * t))
            heat_trace.append(trace)

        if self.config.use_glow_effect:
            for color, alpha, width in ColorPalettes.create_glow_effect(self.colors[0]):
                ax3.loglog(t_values, heat_trace,
                          color=color, alpha=alpha, linewidth=width)

        ax3.loglog(t_values, heat_trace, color=self.colors[0], linewidth=2)
        ax3.set_xlabel('t')
        ax3.set_ylabel('Tr(e^{-tD^2})')
        ax3.set_title('Heat Kernel Trace', fontsize=14)
        ax3.grid(True, alpha=self.config.grid_alpha, which='both')

        # Dimension estimation
        ax4 = fig.add_subplot(gs[1, 1])
        # Use heat kernel for dimension estimation
        log_t = np.log(t_values[20:60])
        log_trace = np.log(heat_trace[20:60])

        # Fit line
        coef = np.polyfit(log_t, log_trace, 1)
        dimension_est = -2 * coef[0]

        ax4.scatter(log_t, log_trace, color=self.colors[1], alpha=0.6)
        ax4.plot(log_t, np.polyval(coef, log_t),
                color=self.colors[2], linewidth=2,
                label=f'Dim ≈ {dimension_est:.2f}')
        ax4.set_xlabel('log(t)')
        ax4.set_ylabel('log(Trace)')
        ax4.set_title('Dimension Estimation', fontsize=14)
        ax4.legend()
        ax4.grid(True, alpha=self.config.grid_alpha)

        fig.suptitle('AQGM Framework - Spectral Analysis',
                    fontsize=self.config.title_size, y=0.98)

        return fig

    def plot_projective_geometry(self) -> plt.Figure:
        """Plot Fano plane and projective geometry structures.

        Returns:
            Matplotlib figure
        """
        fig = plt.figure(figsize=self.config.get_figure_size())
        gs = GridSpec(1, 2, figure=fig, wspace=0.3)

        # Fano plane
        ax1 = fig.add_subplot(gs[0, 0])
        self._draw_fano_plane(ax1)
        ax1.set_title('Fano Plane (PG(2,2))', fontsize=14)
        ax1.set_aspect('equal')
        ax1.axis('off')

        # PG(6,2) structure visualization
        ax2 = fig.add_subplot(gs[0, 1], projection='3d')
        self._draw_pg62_structure(ax2)
        ax2.set_title('PG(6,2) Structure - E7 Correspondence', fontsize=14)

        fig.suptitle('Projective Geometry Structures',
                    fontsize=self.config.title_size, y=0.98)

        return fig

    def _draw_fano_plane(self, ax: plt.Axes) -> None:
        """Draw the Fano plane with 7 points and 7 lines."""
        # Define Fano plane coordinates
        angle = 2 * np.pi / 7
        outer_radius = 2
        inner_radius = 0.8

        # 6 outer points in hexagon
        outer_points = []
        for i in range(6):
            x = outer_radius * np.cos(i * np.pi / 3)
            y = outer_radius * np.sin(i * np.pi / 3)
            outer_points.append((x, y))

        # 1 center point
        center_point = (0, 0)

        # All 7 points
        all_points = outer_points + [center_point]

        # Draw points with glow
        for i, (x, y) in enumerate(all_points):
            if self.config.use_glow_effect:
                for color, alpha, width in ColorPalettes.create_glow_effect(self.colors[i % len(self.colors)]):
                    ax.scatter(x, y, s=300*width, c=color, alpha=alpha)

            ax.scatter(x, y, s=300, c=self.colors[i % len(self.colors)],
                      edgecolor='white', linewidth=2, zorder=10)
            ax.text(x, y, str(i+1), ha='center', va='center',
                   fontsize=12, fontweight='bold', color='white', zorder=11)

        # Define Fano plane lines (each line contains exactly 3 points)
        lines = [
            [0, 1, 6],  # Line 1
            [1, 2, 6],  # Line 2
            [2, 3, 6],  # Line 3
            [3, 4, 6],  # Line 4
            [4, 5, 6],  # Line 5
            [5, 0, 6],  # Line 6
            [0, 2, 4],  # Line 7 (inscribed triangle)
        ]

        # Draw lines
        for line_idx, point_indices in enumerate(lines):
            points = [all_points[i] for i in point_indices]

            if 6 in point_indices:  # Lines through center
                for i in range(len(points)-1):
                    if points[i] != center_point:
                        ax.plot([center_point[0], points[i][0]],
                               [center_point[1], points[i][1]],
                               color=self.colors[(line_idx+3) % len(self.colors)],
                               linewidth=2, alpha=0.7)
            else:  # Inscribed triangle
                for i in range(3):
                    ax.plot([points[i][0], points[(i+1)%3][0]],
                           [points[i][1], points[(i+1)%3][1]],
                           color=self.colors[6 % len(self.colors)],
                           linewidth=2, alpha=0.7)

        # Add circle for outer points
        circle = plt.Circle((0, 0), outer_radius, fill=False,
                           edgecolor=self.config.grid_color,
                           linestyle='--', alpha=0.3)
        ax.add_patch(circle)

        ax.set_xlim(-3, 3)
        ax.set_ylim(-3, 3)

    def _draw_pg62_structure(self, ax: Axes3D) -> None:
        """Draw simplified PG(6,2) structure in 3D."""
        # Generate 127 points (2^7 - 1) / (2 - 1) = 127
        # Use binary representation for simplicity
        points = []

        for i in range(1, 128):  # Exclude zero
            binary = format(i, '07b')
            coords = [int(b) for b in binary]

            # Map to 3D using projection
            x = coords[0] + 0.5*coords[3] + 0.3*coords[6]
            y = coords[1] + 0.5*coords[4]
            z = coords[2] + 0.5*coords[5]

            points.append((x, y, z))

        points = np.array(points)

        # Classify points by Hamming weight
        weights = [bin(i).count('1') for i in range(1, 128)]
        unique_weights = sorted(set(weights))

        # Plot points colored by Hamming weight
        for w_idx, weight in enumerate(unique_weights):
            mask = np.array(weights) == weight
            ax.scatter(points[mask, 0], points[mask, 1], points[mask, 2],
                      c=self.colors[w_idx % len(self.colors)],
                      s=20, alpha=0.6, label=f'Weight {weight}')

        # Add some structure lines
        for i in range(0, 10, 3):
            ax.plot([points[i, 0], points[i+63, 0]],
                   [points[i, 1], points[i+63, 1]],
                   [points[i, 2], points[i+63, 2]],
                   color=self.config.grid_color, alpha=0.3)

        ax.set_xlabel('X')
        ax.set_ylabel('Y')
        ax.set_zlabel('Z')
        ax.legend(loc='upper left', fontsize=8)

        # Set viewing angle
        ax.view_init(elev=20, azim=45)

        # Style
        ax.xaxis.pane.fill = False
        ax.yaxis.pane.fill = False
        ax.zaxis.pane.fill = False
        ax.grid(True, alpha=self.config.grid_alpha)

    def create_comprehensive_figure_set(self) -> Dict[str, plt.Figure]:
        """Generate all figure types in the compendium.

        Returns:
            Dictionary mapping figure names to matplotlib figures
        """
        figures = {}

        print("Generating comprehensive figure set...")

        # E7/E8 Root Systems
        print("  - E7 2D projection...")
        figures['e7_2d'] = self.plot_e7_root_system_2d()

        print("  - E8 3D projections...")
        figures['e8_3d'] = self.plot_e8_root_system_3d()

        # Quantum Circuits
        if QISKIT_AVAILABLE:
            print("  - Quantum circuits...")
            figures['circuit_e7'] = self.plot_quantum_circuit('e7_oracle')
            figures['circuit_grover'] = self.plot_quantum_circuit('grover')

        # Harmonic Evolution
        print("  - Harmonic evolution...")
        figures['harmonics'] = self.plot_harmonic_evolution()

        print("  - Material responses...")
        figures['materials'] = self.plot_material_response()

        # LBM Fields
        print("  - LBM density fields...")
        figures['lbm'] = self.plot_lbm_density_field()

        # AQGM Spectral
        print("  - AQGM spectral analysis...")
        figures['aqgm'] = self.plot_aqgm_spectral_analysis()

        # Projective Geometry
        print("  - Projective geometry...")
        figures['projective'] = self.plot_projective_geometry()

        print(f"Generated {len(figures)} figures successfully!")

        return figures

    def batch_export(self, figures: Dict[str, plt.Figure],
                    formats: List[ExportFormat] = None) -> Dict[str, List[Path]]:
        """Export all figures in multiple formats.

        Args:
            figures: Dictionary of figure names to matplotlib figures
            formats: List of export formats (default: PNG, SVG, PDF)

        Returns:
            Dictionary mapping figure names to list of exported file paths
        """
        if formats is None:
            formats = [ExportFormat.PNG, ExportFormat.SVG, ExportFormat.PDF]

        exported = {}

        for name, fig in figures.items():
            exported[name] = []

            for fmt in formats:
                # Update config format temporarily
                orig_format = self.config.export_format
                self.config.export_format = fmt

                # Save figure
                path = self.save_figure(fig, name)
                exported[name].append(path)

                # Restore format
                self.config.export_format = orig_format

        return exported


def create_demo_visualization():
    """Create demonstration of all visualization capabilities."""

    # Setup configuration for dark mode with neon colors
    config = VisualizationConfig(
        width_pixels=3160,
        height_pixels=2820,
        dpi=300,
        color_scheme=ColorScheme.CYBERPUNK,
        use_dark_mode=True,
        use_glow_effect=True,
        output_dir=Path("figures"),
    )

    # Create visualizer
    viz = AdvancedVisualizer(config)

    # Generate all figures
    figures = viz.create_comprehensive_figure_set()

    # Export in multiple formats
    exported = viz.batch_export(figures,
                               [ExportFormat.PNG, ExportFormat.PDF])

    # Report
    print("\n" + "="*60)
    print("VISUALIZATION GENERATION COMPLETE")
    print("="*60)

    for name, paths in exported.items():
        print(f"\n{name}:")
        for path in paths:
            print(f"  - {path}")

    # Close all figures to free memory
    for fig in figures.values():
        plt.close(fig)

    return exported


# Module exports
__all__ = [
    'AdvancedVisualizer',
    'VisualizationConfig',
    'ColorScheme',
    'ExportFormat',
    'ColorPalettes',
    'create_demo_visualization'
]