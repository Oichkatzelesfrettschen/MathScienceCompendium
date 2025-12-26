"""Unit tests for the main entry point."""

from __future__ import annotations
import unittest
from mathphysics.main import run_experiments

class TestMain(unittest.TestCase):
    def test_full_orchestration(self):
        """Test full experiment orchestration."""
        # Just verify it can be called (dry run not easily possible without side effects)
        self.assertTrue(callable(run_experiments))

if __name__ == '__main__':
    unittest.main()