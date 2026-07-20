"""Interactive Explorer Generation for Exceptional Algebras.

Exports root system data and generates a high-performance 3D visualization
site using Three.js and Vue.js.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from sklearn.decomposition import PCA

from mathphysics.algebras.roots import (
    BaseRootSystem,
    E4RootSystem,
    E5RootSystem,
    E6RootSystem,
    E7RootSystem,
    E8RootSystem,
    E9RootSystem,
    E10RootSystem,
    E11RootSystem,
    F4RootSystem,
    KacMoodyAlgebra,
)
from mathphysics.config import Config
from mathphysics.interactive_explorer_template import HTML_TEMPLATE


def generate_explorer_data() -> list[dict[str, Any]]:
    """Generate all root system data for the interactive explorer."""
    systems: list[BaseRootSystem | KacMoodyAlgebra] = [
        E4RootSystem(),
        E5RootSystem(),  # D5
        F4RootSystem(),
        E6RootSystem(),
        E7RootSystem(),
        E8RootSystem(),
        E9RootSystem(),
        E10RootSystem(),
        E11RootSystem(),
    ]

    data = []
    pca = PCA(n_components=3)

    for system in systems:
        if isinstance(system, BaseRootSystem):
            system_name = system.properties.name
            system_rank = system.properties.rank
        else:
            system_name = system.name
            system_rank = system.rank

        print(f"[EXPLORER] Processing {system_name}...")

        # Handle finite vs Kac-Moody
        if isinstance(system, BaseRootSystem):
            roots = system.generate_roots()
            if isinstance(system, E7RootSystem):
                roots = system.generate_roots(include_zero=False)

            # Perform PCA to 3D
            if len(roots) > 3:
                roots_3d = pca.fit_transform(roots)
            else:
                # Pad with zeros if too few roots
                roots_3d = np.pad(roots, ((0, 0), (0, 3 - roots.shape[1])), mode="constant")

            # Get Cartan matrix and determinant
            try:
                cartan = system.compute_cartan_matrix()
                det = float(np.linalg.det(cartan))
            except (AttributeError, ValueError, np.linalg.LinAlgError):
                det = 0.0

            # Get root types and mappings
            root_types = []
            bit_patterns = []
            for r in roots:
                # Type classification
                non_zero = r[np.abs(r) > 1e-10]
                is_type1 = len(non_zero) > 0 and np.allclose(np.abs(non_zero), 1.0)
                root_types.append("Type 1: Integer" if is_type1 else "Type 2: Half-integer")

                # Bit pattern proxy (sign bits + magnitude bits)
                pattern = 0
                for val in r:
                    pattern = (pattern << 2) | (1 if val > 0 else (2 if val < 0 else 0))
                bit_patterns.append(pattern)

            data.append(
                {
                    "name": system_name,
                    "rank": system_rank,
                    "dim": system.properties.dimension,
                    "roots": roots.tolist(),
                    "roots3d": roots_3d.tolist(),
                    "det": round(det, 2),
                    "types": root_types,
                    "bitPatterns": bit_patterns,
                }
            )
        # Handle Kac-Moody (E9-E11) - generate a finite subset of roots
        elif isinstance(system, E9RootSystem):
            e8 = E8RootSystem()
            e8_roots = e8.generate_roots()
            # Create shells for n = -1, 0, 1
            roots_list = []
            for n in [-1, 0, 1]:
                for r in e8_roots:
                    # Append n and a zero for consistent rank mapping if needed
                    # Here we just want a 3D cloud
                    roots_list.append(np.append(r, [n]))

            roots = np.array(roots_list)
            roots_3d = pca.fit_transform(roots)

            data.append(
                {
                    "name": system_name,
                    "rank": 9,
                    "dim": "Infinite",
                    "roots": roots.tolist()[:240],  # Sample for tooltip
                    "roots3d": roots_3d.tolist(),
                    "det": 0.0,
                }
            )
        else:
            # E10, E11 placeholders - empty for now or generate small sample
            data.append(
                {
                    "name": system_name,
                    "rank": system_rank,
                    "dim": "Infinite",
                    "roots": [],
                    "roots3d": [],
                    "det": "N/A",
                }
            )

    return data


def build_explorer_site() -> None:
    """Assemble the HTML template with data and save to figures."""
    data = generate_explorer_data()
    json_data = json.dumps(data)

    html_content = HTML_TEMPLATE.replace("{data_placeholder}", json_data)

    output_path = Config.FIGURES_DIR / "lie_algebras_explorer.html"
    with output_path.open("w") as f:
        f.write(html_content)

    print(f"[EXPLORER] Site generated: {output_path}")


if __name__ == "__main__":
    build_explorer_site()
