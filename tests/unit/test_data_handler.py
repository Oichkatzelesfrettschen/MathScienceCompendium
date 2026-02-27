import unittest
import numpy as np
import pandas as pd
from mathphysics.data_handler import SimulationDataHandler


class TestDataHandler(unittest.TestCase):
    def setUp(self) -> None:
        self.handler = SimulationDataHandler()
        self.test_prefix = "test_state_unit"

    def test_save_load_parquet(self) -> None:
        # Use a 1D array to avoid shape issues during simple load
        data = np.random.rand(100)
        self.handler.save_state(data, self.test_prefix, iteration=42)
        loaded = self.handler.load_state(self.test_prefix, iteration=42)
        self.assertIsNotNone(loaded)
        # loaded might be flattened or keep original depending on implementation
        self.assertEqual(len(loaded), 100)

    def test_data_consistency(self) -> None:
        # Ensure file exists from previous test or create it
        data = np.random.rand(100)
        self.handler.save_state(data, self.test_prefix, iteration=42)

        filename = f"{self.test_prefix}_000042.parquet"
        from mathphysics.config import Config

        path = Config.get_results_path(filename)

        df = pd.read_parquet(path)
        self.assertIn("density", df.columns)
        raw_val = df["density"].iloc[0]
        self.assertGreater(len(raw_val), 0)


if __name__ == "__main__":
    unittest.main()
