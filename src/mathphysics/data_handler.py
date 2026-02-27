"""Data Handling module for experimental results.

Provides high-performance storage using Parquet and TFRecords.
"""

from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd


try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    pa = None  # type: ignore
    pq = None  # type: ignore
    HAS_PYARROW = False


from .config import Config
from .optional_deps import HAS_JAX


class DataHandler:
    """Handles simulation data export and ingestion."""

    @staticmethod
    def save_to_parquet(data_dict: dict[str, Any], filename: str) -> None:
        """Save a dictionary of arrays to a Parquet file as a single snapshot row.

        Raises:
            ImportError: If pyarrow is not installed
        """
        if not HAS_PYARROW:
            raise ImportError(
                "pyarrow is required for parquet operations. Install with: pip install pyarrow"
            )

        if HAS_JAX:
            import jax.numpy as jnp  # noqa: PLC0415

            _array_types: tuple[type, ...] = (np.ndarray, jnp.ndarray)
        else:
            _array_types = (np.ndarray,)

        processed_data = {
            k: [v.tolist() if isinstance(v, _array_types) else v]
            for k, v in data_dict.items()
        }

        df = pd.DataFrame(processed_data)
        table = pa.Table.from_pandas(df)

        output_path = Config.get_results_path(filename)
        pq.write_table(table, output_path)
        print(f"Data saved to Parquet: {output_path}")

    @staticmethod
    def save_simulation_state(
        density: np.ndarray,
        velocity: np.ndarray,
        iteration: int,
        filename_prefix: str = "lbm_state",
    ) -> None:
        """Save full simulation state."""
        data = {
            "iteration": iteration,
            "density": density,
            "velocity_x": velocity[..., 0],
            "velocity_y": velocity[..., 1],
        }
        DataHandler.save_to_parquet(data, f"{filename_prefix}_{iteration:06d}.parquet")


class SimulationDataHandler:
    """Wrapper for simulation state persistence compatible with existing tests."""

    def __init__(self) -> None:
        self.config = Config()

    def save_state(self, density: np.ndarray, filename_prefix: str, iteration: int) -> None:
        """Save density field to parquet."""
        data = {"iteration": iteration, "density": density}
        DataHandler.save_to_parquet(data, f"{filename_prefix}_{iteration:06d}.parquet")

    def load_state(self, filename_prefix: str, iteration: int) -> np.ndarray | None:
        """Load density field from parquet."""
        filename = f"{filename_prefix}_{iteration:06d}.parquet"
        path = Config.get_results_path(filename)
        if not path.exists():
            return None
        df = pd.read_parquet(path)
        return np.array(df["density"].iloc[0])
