"""Data Handling module for experimental results.

Provides high-performance storage using Parquet and TFRecords.
"""

from __future__ import annotations

from typing import Any, cast

import numpy as np
import pandas as pd


try:
    import pyarrow as pa
    import pyarrow.parquet as pq

    HAS_PYARROW = True
except ImportError:
    pa = None
    pq = None
    HAS_PYARROW = False


from .config import Config


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

        processed_data = {
            key: [value.tolist() if hasattr(value, "tolist") else value]
            for key, value in data_dict.items()
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
        return cast("np.ndarray", np.asarray(df["density"].iloc[0]))
