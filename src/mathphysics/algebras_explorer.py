"""Interactive Lie Algebra Root System Explorer.

Generates a high-resolution interactive HTML dashboard using Plotly to explore
the geometry of E4-E11 and F4 root systems with selectable overlays.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from sklearn.decomposition import PCA

from mathphysics.algebras.roots import (
    E4RootSystem,
    E5RootSystem,
    E6RootSystem,
    E7RootSystem,
    E8RootSystem,
    F4RootSystem,
)
from mathphysics.config import Config


def generate_explorer_dashboard():
    print("[EXPLORER] Generating multi-algebra root dashboard...")

    systems = {
        "E4 (A4)": E4RootSystem(),
        "E5 (D5)": E5RootSystem(),
        "F4": F4RootSystem(),
        "E6": E6RootSystem(),
        "E7": E7RootSystem(),
        "E8": E8RootSystem(),
    }

    fig = go.Figure()

    # We use a 3D PCA projection that encompasses all systems
    # For consistent projection, we'll fit the PCA on the largest system (E8)
    e8_roots = systems["E8"].generate_roots()
    pca = PCA(n_components=3)
    pca.fit(e8_roots)

    colors = ["cyan", "magenta", "yellow", "lime", "orange", "red"]

    for (name, sys), color in zip(systems.items(), colors):
        roots = sys.generate_roots()
        # Project to 3D
        # Pad with zeros if roots have fewer than 8 dims (e.g. F4, E4)
        padded_roots = np.zeros((roots.shape[0], 8))
        padded_roots[:, : roots.shape[1]] = roots
        r3d = pca.transform(padded_roots)

        df = pd.DataFrame(r3d, columns=["PC1", "PC2", "PC3"])
        df["Norm"] = np.linalg.norm(roots, axis=1)

        fig.add_trace(
            go.Scatter3d(
                x=df["PC1"],
                y=df["PC2"],
                z=df["PC3"],
                mode="markers",
                name=name,
                marker={
                    "size": 5,
                    "color": color,
                    "opacity": 0.7,
                    "line": {"width": 0.5, "color": "white"},
                },
                hovertemplate=f"<b>{name} Root</b><br>"
                + "PC1: %{x:.2f}<br>"
                + "PC2: %{y:.2f}<br>"
                + "PC3: %{z:.2f}<br>"
                + "Norm: %{customdata:.2f}<extra></extra>",
                customdata=df["Norm"],
            )
        )

    # Add selectability/overlays through UI buttons
    fig.update_layout(
        template="plotly_dark",
        title="Lie Algebra Root System Explorer (SM89 Projective Synthesis)",
        scene={
            "xaxis_title": "Principal Component 1",
            "yaxis_title": "Principal Component 2",
            "zaxis_title": "Principal Component 3",
        },
        legend={"title": "Select Systems", "itemsizing": "constant"},
        margin={"l": 0, "r": 0, "b": 0, "t": 40},
    )

    output_path = Config.FIGURES_DIR / "lie_algebras_explorer.html"
    fig.write_html(str(output_path))
    print(f"[EXPLORER] Dashboard saved to {output_path}")
    return output_path


if __name__ == "__main__":
    generate_explorer_dashboard()
