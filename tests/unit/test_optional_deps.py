"""Tests for optional_deps.py.

Covers:
- Module-level boolean flags (HAS_JAX, HAS_QISKIT, HAS_GUDHI, HAS_LIESYM,
  HAS_JAXLIE, HAS_PLOTLY) exist and are bool
- require_dependency raises ValueError for unknown names
- require_dependency raises ImportError for unavailable deps
- require_dependency does NOT raise for a dep that is actually installed
- safe_import returns a module object for a stdlib module
- safe_import returns None for a module that does not exist
- __all__ contains the public names
"""

from __future__ import annotations

import importlib
import sys
import types
from unittest.mock import patch

import pytest

from mathphysics.optional_deps import (
    HAS_GUDHI,
    HAS_JAX,
    HAS_JAXLIE,
    HAS_LIESYM,
    HAS_PLOTLY,
    HAS_QISKIT,
    require_dependency,
    safe_import,
)
import mathphysics.optional_deps as optional_deps_module


# ---------------------------------------------------------------------------
# Boolean flags exist and have correct type
# ---------------------------------------------------------------------------


def test_has_jax_is_bool():
    assert isinstance(HAS_JAX, bool)


def test_has_qiskit_is_bool():
    assert isinstance(HAS_QISKIT, bool)


def test_has_gudhi_is_bool():
    assert isinstance(HAS_GUDHI, bool)


def test_has_liesym_is_bool():
    assert isinstance(HAS_LIESYM, bool)


def test_has_jaxlie_is_bool():
    assert isinstance(HAS_JAXLIE, bool)


def test_has_plotly_is_bool():
    assert isinstance(HAS_PLOTLY, bool)


# ---------------------------------------------------------------------------
# __all__ completeness
# ---------------------------------------------------------------------------


def test_all_contains_public_flags():
    import mathphysics.optional_deps as m  # noqa: PLC0415

    for name in ("HAS_JAX", "HAS_QISKIT", "HAS_GUDHI", "HAS_LIESYM",
                 "HAS_JAXLIE", "HAS_PLOTLY"):
        assert name in m.__all__, f"{name} missing from __all__"


def test_all_contains_require_dependency():
    import mathphysics.optional_deps as m  # noqa: PLC0415

    assert "require_dependency" in m.__all__


def test_all_contains_safe_import():
    import mathphysics.optional_deps as m  # noqa: PLC0415

    assert "safe_import" in m.__all__


# ---------------------------------------------------------------------------
# require_dependency - invalid name
# ---------------------------------------------------------------------------


def test_require_dependency_unknown_raises_value_error():
    with pytest.raises(ValueError, match="Unknown dependency"):
        require_dependency("nonexistent_package_xyz")


def test_require_dependency_empty_string_raises_value_error():
    with pytest.raises(ValueError):
        require_dependency("")


# ---------------------------------------------------------------------------
# require_dependency - unavailable dependency
# ---------------------------------------------------------------------------


def _patch_flag_false(flag_name: str, dep_name: str):
    """Context manager: patch HAS_<flag> to False and clear dep from sys.modules."""
    return patch.object(optional_deps_module, flag_name, False)


def test_require_dependency_unavailable_raises_import_error():
    # Temporarily mark jax as unavailable regardless of actual installation
    with patch.dict(
        vars(optional_deps_module),
        {"HAS_JAX": False},
    ):
        with pytest.raises(ImportError, match="jax"):
            require_dependency("jax")


def test_require_dependency_import_error_message_has_install_hint():
    with patch.dict(vars(optional_deps_module), {"HAS_QISKIT": False}):
        with pytest.raises(ImportError) as exc_info:
            require_dependency("qiskit")
        assert "pip install" in str(exc_info.value)


def test_require_dependency_gudhi_unavailable_raises():
    with patch.dict(vars(optional_deps_module), {"HAS_GUDHI": False}):
        with pytest.raises(ImportError):
            require_dependency("gudhi")


def test_require_dependency_plotly_unavailable_raises():
    with patch.dict(vars(optional_deps_module), {"HAS_PLOTLY": False}):
        with pytest.raises(ImportError):
            require_dependency("plotly")


# ---------------------------------------------------------------------------
# require_dependency - available dependency (patched as available)
# ---------------------------------------------------------------------------


def test_require_dependency_available_does_not_raise():
    # Patch HAS_JAX = True; the function should return without error
    with patch.dict(vars(optional_deps_module), {"HAS_JAX": True}):
        # Should not raise anything
        require_dependency("jax")


def test_require_dependency_qiskit_available_does_not_raise():
    with patch.dict(vars(optional_deps_module), {"HAS_QISKIT": True}):
        require_dependency("qiskit")


# ---------------------------------------------------------------------------
# safe_import - stdlib module succeeds
# ---------------------------------------------------------------------------


def test_safe_import_stdlib_returns_module():
    result = safe_import("json")
    assert result is not None
    import json  # noqa: PLC0415

    assert result is json


def test_safe_import_os_returns_module():
    result = safe_import("os")
    assert result is not None
    import os  # noqa: PLC0415

    assert result is os


def test_safe_import_math_returns_module():
    mod = safe_import("math")
    assert mod is not None
    assert hasattr(mod, "pi")


def test_safe_import_nonexistent_returns_none():
    result = safe_import("_this_package_does_not_exist_abc123")
    assert result is None


def test_safe_import_deeply_nested_nonexistent_returns_none():
    result = safe_import("_fake.nested.module.xyz")
    assert result is None


# ---------------------------------------------------------------------------
# Conditional coverage: if JAX is installed, require_dependency works end-to-end
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not HAS_JAX, reason="JAX not installed in this environment")
def test_require_dependency_jax_installed_no_exception():
    # JAX is actually present; calling require_dependency should be a no-op
    require_dependency("jax")


@pytest.mark.skipif(not HAS_QISKIT, reason="Qiskit not installed in this environment")
def test_require_dependency_qiskit_installed_no_exception():
    require_dependency("qiskit")
