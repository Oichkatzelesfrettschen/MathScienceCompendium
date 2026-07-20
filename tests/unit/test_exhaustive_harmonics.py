"""Exhaustive tests for genesis_harmonics.py.

Covers:
- GenesisHarmonics construction with defaults and custom parameters
- MaterialType enum values
- _initialize_layers frequency ratios (golden ratio scaling)
- layer_frequencies length matches num_layers
- evolve returns required keys with correct shapes
- evolve harmonic_amplitudes are unit-magnitude complex numbers
- evolve zpe_modulation is a scalar float
- calculate_zpe_envelope shape, positivity, and decay
- MaterialProperties dataclass fields
- Different material types produce different frequencies
"""

from __future__ import annotations

import numpy as np

from mathphysics.genesis_harmonics import (
    GenesisHarmonics,
    MaterialType,
)
from mathphysics.topology_bridge import TopologyBridge


# ---------------------------------------------------------------------------
# MaterialType
# ---------------------------------------------------------------------------


def test_material_type_tourmaline_value():
    assert MaterialType.TOURMALINE.value == "tourmaline"


def test_material_type_quartz_value():
    assert MaterialType.QUARTZ.value == "quartz"


def test_material_type_bst_value():
    assert MaterialType.BST.value == "bst"


def test_material_type_enum_members():
    members = list(MaterialType)
    assert len(members) == 3


# ---------------------------------------------------------------------------
# GenesisHarmonics construction
# ---------------------------------------------------------------------------


def test_genesis_harmonics_default_num_layers():
    gh = GenesisHarmonics()
    assert gh.num_layers == 7


def test_genesis_harmonics_default_base_frequency():
    gh = GenesisHarmonics()
    assert gh.base_frequency == 1e12


def test_genesis_harmonics_default_material():
    gh = GenesisHarmonics()
    assert gh.material == MaterialType.TOURMALINE


def test_genesis_harmonics_default_fractal_alpha():
    gh = GenesisHarmonics()
    assert gh.fractal_alpha == 1.5


def test_genesis_harmonics_default_zpe_beta():
    gh = GenesisHarmonics()
    assert gh.zpe_beta == 0.1


def test_genesis_harmonics_custom_num_layers():
    gh = GenesisHarmonics(num_layers=12)
    assert gh.num_layers == 12


def test_genesis_harmonics_custom_material():
    gh = GenesisHarmonics(material=MaterialType.QUARTZ)
    assert gh.material == MaterialType.QUARTZ


def test_genesis_harmonics_custom_zpe_beta():
    gh = GenesisHarmonics(zpe_beta=0.05)
    assert gh.zpe_beta == 0.05


# ---------------------------------------------------------------------------
# layer_frequencies
# ---------------------------------------------------------------------------


def test_layer_frequencies_length_matches_num_layers():
    gh = GenesisHarmonics(num_layers=5)
    assert len(gh.layer_frequencies) == 5


def test_layer_frequencies_first_equals_base():
    gh = GenesisHarmonics(num_layers=4, base_frequency=1e10)
    # phi^0 = 1 so first frequency == base
    assert abs(gh.layer_frequencies[0] - 1e10) < 1.0


def test_layer_frequencies_golden_ratio_scaling():
    phi = (1 + np.sqrt(5)) / 2
    gh = GenesisHarmonics(num_layers=4, base_frequency=1.0)
    for k in range(4):
        expected = phi**k
        assert abs(gh.layer_frequencies[k] - expected) < 1e-6


def test_layer_frequencies_monotonically_increasing():
    gh = GenesisHarmonics(num_layers=6)
    freqs = gh.layer_frequencies
    assert np.all(np.diff(freqs) > 0)


def test_layer_frequencies_all_positive():
    gh = GenesisHarmonics(num_layers=7)
    assert np.all(gh.layer_frequencies > 0)


# ---------------------------------------------------------------------------
# evolve
# ---------------------------------------------------------------------------


def test_evolve_returns_dict():
    gh = GenesisHarmonics(num_layers=5)
    result = gh.evolve(0.0)
    assert isinstance(result, dict)


def test_evolve_has_harmonic_amplitudes_key():
    gh = GenesisHarmonics(num_layers=5)
    result = gh.evolve(0.0)
    assert "harmonic_amplitudes" in result


def test_evolve_has_zpe_modulation_key():
    gh = GenesisHarmonics(num_layers=5)
    result = gh.evolve(0.0)
    assert "zpe_modulation" in result


def test_evolve_harmonic_amplitudes_shape():
    n = 8
    gh = GenesisHarmonics(num_layers=n)
    result = gh.evolve(1.0)
    assert result["harmonic_amplitudes"].shape == (n,)


def test_evolve_harmonic_amplitudes_unit_magnitude():
    gh = GenesisHarmonics(num_layers=7)
    result = gh.evolve(0.5)
    mags = np.abs(result["harmonic_amplitudes"])
    np.testing.assert_allclose(mags, np.ones(7), atol=1e-10)


def test_evolve_zpe_modulation_is_scalar():
    gh = GenesisHarmonics(num_layers=5)
    result = gh.evolve(1.0)
    # Should be a plain Python float or 0-dimensional numpy value
    zpe = result["zpe_modulation"]
    assert np.ndim(zpe) == 0


def test_evolve_zpe_modulation_bounded():
    gh = GenesisHarmonics(num_layers=5, zpe_beta=0.1)
    result = gh.evolve(1.0)
    # |sin(x)| <= 1, so |zpe_modulation| <= zpe_beta
    assert abs(result["zpe_modulation"]) <= gh.zpe_beta + 1e-12


def test_evolve_at_t0_phases_zero():
    gh = GenesisHarmonics(num_layers=4)
    result = gh.evolve(0.0)
    # At t=0, phases = 0, so exp(i*0) = 1.0 + 0j
    expected = np.ones(4, dtype=complex)
    np.testing.assert_allclose(result["harmonic_amplitudes"], expected, atol=1e-10)


# ---------------------------------------------------------------------------
# calculate_zpe_envelope
# ---------------------------------------------------------------------------


def test_calculate_zpe_envelope_shape():
    gh = GenesisHarmonics(num_layers=7, base_frequency=1e12)
    freqs = np.linspace(1e11, 1e13, 10)
    envelope = gh.calculate_zpe_envelope(freqs)
    assert envelope.shape == (10,)


def test_calculate_zpe_envelope_all_positive():
    gh = GenesisHarmonics()
    freqs = np.array([1e11, 1e12, 1e13])
    envelope = gh.calculate_zpe_envelope(freqs)
    assert np.all(envelope > 0)


def test_calculate_zpe_envelope_decays_with_frequency():
    # Envelope should decay for large frequencies relative to base
    gh = GenesisHarmonics(base_frequency=1e12)
    freqs = np.array([1e10, 1e12, 1e14])
    envelope = gh.calculate_zpe_envelope(freqs)
    # envelope at 1e14 should be smaller than at 1e10
    assert envelope[2] < envelope[0]


def test_calculate_zpe_envelope_proportional_to_frequency_near_zero():
    # For very small frequencies << base, envelope ~ 0.5 * hbar * freq
    gh = GenesisHarmonics(base_frequency=1e15)
    h_bar = 1.054e-34
    freq = 1.0  # very small compared to base
    env = gh.calculate_zpe_envelope(np.array([freq]))[0]
    expected = 0.5 * h_bar * freq * np.exp(-freq / (10 * 1e15))
    assert abs(env - expected) < 1e-50


# ---------------------------------------------------------------------------
# MaterialProperties dataclass
# ---------------------------------------------------------------------------


def test_material_properties_has_name():
    gh = GenesisHarmonics(material=MaterialType.QUARTZ)
    assert gh.material_properties.name == "quartz"


def test_material_properties_has_resonance_frequencies():
    gh = GenesisHarmonics()
    assert len(gh.material_properties.resonance_frequencies) == 3


def test_material_properties_has_dielectric_constant():
    gh = GenesisHarmonics()
    assert gh.material_properties.dielectric_constant == 4.5


def test_material_properties_response_function_callable():
    gh = GenesisHarmonics()
    val = gh.material_properties.response_function(1e12)
    # Result should be complex
    assert isinstance(val, complex)


def test_material_properties_quartz_higher_freqs_than_tourmaline():
    gh_t = GenesisHarmonics(material=MaterialType.TOURMALINE)
    gh_q = GenesisHarmonics(material=MaterialType.QUARTZ)
    assert (
        gh_q.material_properties.resonance_frequencies[0]
        > (gh_t.material_properties.resonance_frequencies[0])
    )


# ---------------------------------------------------------------------------
# TopologyBridge behavior
# ---------------------------------------------------------------------------
# These tests keep the topology fallback beside the harmonics integration checks.


def test_topology_bridge_calculate_persistence_returns_array():
    pts = np.random.rand(10, 2).tolist()
    result = TopologyBridge.calculate_persistence(np.array(pts))
    assert isinstance(result, np.ndarray)


def test_topology_bridge_calculate_persistence_shape():
    pts = np.random.rand(8, 2)
    result = TopologyBridge.calculate_persistence(pts)
    # Each row is [dim, birth, death]
    assert result.ndim == 2
    assert result.shape[1] == 3


def test_topology_bridge_calculate_persistence_dims_non_negative():
    pts = np.random.rand(8, 2)
    result = TopologyBridge.calculate_persistence(pts)
    assert np.all(result[:, 0] >= 0)


def test_topology_bridge_calculate_persistence_death_ge_birth():
    pts = np.random.rand(8, 2)
    result = TopologyBridge.calculate_persistence(pts)
    # death >= birth for every pair
    assert np.all(result[:, 2] >= result[:, 1])


def test_topology_bridge_get_betti_numbers_returns_list():
    pts = np.random.rand(8, 2)
    betti = TopologyBridge.get_betti_numbers(pts)
    assert isinstance(betti, list)


def test_topology_bridge_get_betti_numbers_non_negative():
    pts = np.random.rand(8, 2)
    betti = TopologyBridge.get_betti_numbers(pts)
    assert all(b >= 0 for b in betti)


def test_topology_bridge_fallback_persistence_without_gudhi():
    # The fallback path (no gudhi) returns a fixed 3-row array.
    # We test the fallback by patching HAS_GUDHI in the topology_bridge module.
    from unittest.mock import patch  # noqa: PLC0415

    import mathphysics.topology_bridge as tb  # noqa: PLC0415

    with patch.object(tb, "HAS_GUDHI", False):
        pts = np.random.rand(5, 2)
        result = tb.TopologyBridge.calculate_persistence(pts)
        assert result.shape == (3, 3)


def test_topology_bridge_fallback_betti_numbers_without_gudhi():
    from unittest.mock import patch  # noqa: PLC0415

    import mathphysics.topology_bridge as tb  # noqa: PLC0415

    with patch.object(tb, "HAS_GUDHI", False):
        pts = np.random.rand(5, 2)
        betti = tb.TopologyBridge.get_betti_numbers(pts)
        assert betti == [1, 0, 0]
