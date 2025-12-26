"""Anchor Diagram Generation: Visualizing High-Dimensional Mechanics.

Generates Voronoi cells for E8 root systems and simulated persistence barcodes
to ground the algebraic-topological synthesis roadmap.
"""

from __future__ import annotations
import numpy as np
from mathphysics.viz import Visualizer
from mathphysics.algebras.roots import E8RootSystem
from mathphysics.topology_bridge import TopologyBridge
from mathphysics.config import Config

def generate_anchor_diagrams():
    viz = Visualizer()
    print("[VIZ] Generating geometric and topological anchors...")

    # 1. E8 Voronoi Tesselation (Visualizing the Lattice Gaps)
    e8 = E8RootSystem()
    roots = e8.generate_roots()
    fig = viz.plot_voronoi_2d(roots, "E8 Root System: Voronoi Partition (Spectral Grating)")
    viz.save(fig, "e8_voronoi_grating")
    
    # 2. Real/Simulated Persistence Barcode (Visualizing Homology)
    # Use the bridge to calculate persistence (will use Gudhi if installed)
    persistence_data = TopologyBridge.calculate_persistence(roots)
    fig = viz.plot_persistence_barcode(persistence_data, "Topological Signature: Persistent Homology (Sugawara Consistency)")
    viz.save(fig, "vorticity_homology_barcode")

    print("[VIZ] Anchor diagrams complete.")

if __name__ == "__main__":
    generate_anchor_diagrams()
