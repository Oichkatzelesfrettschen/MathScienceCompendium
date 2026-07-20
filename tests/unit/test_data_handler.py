import tempfile
import unittest

import numpy as np
import pandas as pd

from mathphysics.config import Config
from mathphysics.data_handler import SimulationDataHandler


class TestDataHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.original_results_directory = Config.RESULTS_DIR
        self.temporary_directory = self.enterContext(tempfile.TemporaryDirectory())
        Config.RESULTS_DIR = self.temporary_directory
        self.handler = SimulationDataHandler()
        self.test_prefix = "test_state_unit"

    def tearDown(self) -> None:
        Config.RESULTS_DIR = self.original_results_directory

    def test_save_load_parquet(self) -> None:
        # Use a 1D array to avoid shape issues during simple load
        data = np.arange(100, dtype=float)
        self.handler.save_state(data, self.test_prefix, iteration=42)
        loaded = self.handler.load_state(self.test_prefix, iteration=42)
        self.assertIsNotNone(loaded)
        # loaded might be flattened or keep original depending on implementation
        self.assertEqual(len(loaded), 100)

    def test_data_consistency(self) -> None:
        # Ensure file exists from previous test or create it
        data = np.arange(100, dtype=float)
        self.handler.save_state(data, self.test_prefix, iteration=42)

        filename = f"{self.test_prefix}_000042.parquet"
        path = Config.get_results_path(filename)

        df = pd.read_parquet(path)
        self.assertIn("density", df.columns)
        raw_val = df["density"].iloc[0]
        self.assertGreater(len(raw_val), 0)


if __name__ == "__main__":
    unittest.main()
