import numpy as np
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

if __name__ == "__main__":
    test_liesym_bridge()
