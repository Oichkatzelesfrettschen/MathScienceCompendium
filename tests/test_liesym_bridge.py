import numpy as np
import pytest

from mathphysics.algebras.liesym_bridge import LiesymBridge


def test_liesym_bridge():
    print("Testing LiesymBridge...")
    roots = LiesymBridge.get_roots("E", 8)
    print(f"E8 Roots count: {len(roots)}")
    assert len(roots) == 240

    roots7 = LiesymBridge.get_roots("E", 7)
    print(f"E7 Roots count: {len(roots7)}")
    assert len(roots7) == 126

    print("Bridge functional.")


def test_f4_fallback_and_orbit_are_available():
    roots = LiesymBridge.get_roots("F", 4)
    assert len(roots) == 48
    orbit = LiesymBridge.get_weyl_orbit(roots[0], "F", 4)
    assert len(orbit) in {24, 48}


def test_weyl_orbit_rejects_nonroot_vector():
    with pytest.raises(ValueError, match="not a root"):
        LiesymBridge.get_weyl_orbit(np.zeros(8), "E", 8)


if __name__ == "__main__":
    test_liesym_bridge()
