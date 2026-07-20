#!/usr/bin/env python3
"""Execute the canonical acceptance and rejection gate for every framework claim."""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, cast

import networkx as nx
import numpy as np


REPO_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = REPO_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from mathphysics.algebras.cayley_dickson import (  # noqa: E402
    Complex,
    Octonion,
    Quaternion,
    Real,
    Sedenion,
)
from mathphysics.algebras.roots import (  # noqa: E402
    E7RootSystem,
    E9RootSystem,
    E10RootSystem,
    E11RootSystem,
)
from mathphysics.fourier_quotient import build_fourier_quotient_audit  # noqa: E402
from mathphysics.quantum_lattice_boltzmann import (  # noqa: E402
    BoundaryType,
    LBMParameters,
    QuantumLatticeBoltzmann,
)


CLAIM_LEDGER_PATH = REPO_ROOT / "data" / "registry" / "unified_framework_claims.json"
GATE_REGISTRY_PATH = REPO_ROOT / "data" / "registry" / "claim_gate_registry.json"
DEFAULT_OUTPUT = REPO_ROOT / "data" / "registry" / "claim_gate_results.json"
ADMISSION_PACKAGE_PATH = REPO_ROOT / "data" / "registry" / "experimental_admission_packages.json"


@dataclass(frozen=True)
class CheckResult:
    outcome: str
    summary: str
    metrics: dict[str, Any]


def check_cayley_dickson_boundary() -> CheckResult:
    declared = {
        algebra.properties().name: algebra.properties().is_division_algebra
        for algebra in (Real, Complex, Quaternion, Octonion, Sedenion)
    }
    left_factor = Sedenion.basis_element(3) + Sedenion.basis_element(10)
    right_factor = Sedenion.basis_element(6) - Sedenion.basis_element(15)
    product_norm_squared = float((left_factor * right_factor).norm_squared())
    passed = (
        all(declared[name] for name in ("Real", "Complex", "Quaternion", "Octonion"))
        and not declared["Sedenion"]
        and float(left_factor.norm_squared()) > 0.0
        and float(right_factor.norm_squared()) > 0.0
        and product_norm_squared == 0.0
    )
    return CheckResult(
        "accepted" if passed else "rejected",
        "Normed division stops at dimension eight; an exact sedenion zero divisor is reproduced.",
        {
            "declared_division_properties": declared,
            "zero_divisor_left_norm_squared": float(left_factor.norm_squared()),
            "zero_divisor_right_norm_squared": float(right_factor.norm_squared()),
            "zero_divisor_product_norm_squared": product_norm_squared,
        },
    )


def check_spin8_triality() -> CheckResult:
    diagram = nx.Graph([(1, 0), (1, 2), (1, 3)])
    automorphisms = list(
        nx.algorithms.isomorphism.GraphMatcher(diagram, diagram).isomorphisms_iter()
    )
    outer_permutations = {tuple(mapping[node] for node in (0, 2, 3)) for mapping in automorphisms}
    passed = len(automorphisms) == 6 and len(outer_permutations) == 6
    return CheckResult(
        "accepted" if passed else "rejected",
        "The D4 diagram has six automorphisms permuting its three outer nodes.",
        {
            "automorphism_count": len(automorphisms),
            "outer_permutation_count": len(outer_permutations),
        },
    )


def check_kac_moody_classification() -> CheckResult:
    metrics: dict[str, Any] = {}
    expected = {"E9": (0, 0, 1), "E10": (-1, 1, 0), "E11": (-2, 1, 0)}
    passed = True
    for root_system in (E9RootSystem(), E10RootSystem(), E11RootSystem()):
        matrix = root_system.generalized_cartan_matrix()
        eigenvalues = np.linalg.eigvalsh(matrix)
        determinant = round(float(np.linalg.det(matrix)))
        negative_count = int(np.count_nonzero(eigenvalues < -1e-10))
        null_count = int(np.count_nonzero(np.abs(eigenvalues) <= 1e-10))
        metrics[root_system.name] = {
            "determinant": determinant,
            "negative_eigenvalue_count": negative_count,
            "null_eigenvalue_count": null_count,
        }
        passed = passed and (determinant, negative_count, null_count) == expected[root_system.name]
    return CheckResult(
        "corrected" if passed else "rejected",
        "The matrices classify E9 as affine and E10-E11 as indefinite Kac-Moody extensions.",
        metrics,
    )


def load_exceptional_scope_audit() -> dict[str, Any]:
    audit_path = REPO_ROOT / "data" / "registry" / "exceptional_group_scope_audit.json"
    return cast("dict[str, Any]", json.loads(audit_path.read_text(encoding="ascii")))


def check_albert_group_scope() -> CheckResult:
    audit = load_exceptional_scope_audit()
    ladder = {entry["group"]: entry for entry in audit["albert_ladder"]}
    implementation = audit["albert_implementation"]
    passed = (
        ladder["F4"]["role"] == "automorphism group of the Albert algebra h3(O)"
        and ladder["E6(-26)"]["status"] == "established"
        and "not its automorphism group" in ladder["E7(-25)"]["role"]
        and ladder["E7 as Aut(J3(S))"]["status"] == "rejected"
        and implementation["coordinate_dimension"] == 27
        and implementation["inputs_are_hermitian"]
        and implementation["nonzero_product_norm"] > 0.0
        and implementation["identity_residual_maximum_absolute"] <= 1e-6
        and implementation["commutativity_residual_maximum_absolute"] <= 1e-6
        and implementation["jordan_identity_residual_maximum_absolute"] <= 1e-6
    )
    return CheckResult(
        "corrected" if passed else "rejected",
        "The executable Albert product is nontrivial and unital; F4, E6(-26), and E7(-25) occupy automorphism, reduced-structure, and conformal roles.",
        {
            "coordinate_dimension": implementation["coordinate_dimension"],
            "nonzero_product_norm": implementation["nonzero_product_norm"],
            "identity_residual_maximum_absolute": implementation[
                "identity_residual_maximum_absolute"
            ],
            "commutativity_residual_maximum_absolute": implementation[
                "commutativity_residual_maximum_absolute"
            ],
            "jordan_identity_residual_maximum_absolute": implementation[
                "jordan_identity_residual_maximum_absolute"
            ],
            "rejected_source_ladder": ladder["E7 as Aut(J3(S))"]["status"],
        },
    )


def check_moonshine_stability_scope() -> CheckResult:
    audit = load_exceptional_scope_audit()
    scope = audit["moonshine_scope"]
    source_paths = [REPO_ROOT / item["relpath"] for item in audit["source_evidence"]]
    passed = (
        scope["physical_stability_claim_status"] == "rejected"
        and "defines no Monster representation" in scope["repository_implementation"]
        and all(path.is_file() and path.stat().st_size > 0 for path in source_paths)
    )
    return CheckResult(
        "rejected" if passed else "open",
        "The retained code has neither a Monster representation nor a physical evolution operator, so moonshine cannot supply a stability theorem here.",
        {
            "source_count": len(source_paths),
            "monster_order": scope["monster_order"],
            "physical_stability_claim_status": scope["physical_stability_claim_status"],
            "source_files_present": all(path.is_file() for path in source_paths),
        },
    )


def check_e7_root_quotient() -> CheckResult:
    root_system = E7RootSystem()
    simple_roots = root_system.generate_simple_roots()
    generated_roots = root_system.generate_roots()
    maximum_residual = 0.0
    maximum_integrality_error = 0.0
    for root in generated_roots:
        coefficients, _, _, _ = np.linalg.lstsq(simple_roots.T, root, rcond=None)
        residual = float(np.linalg.norm(simple_roots.T @ coefficients - root))
        integrality_error = float(np.max(np.abs(coefficients - np.rint(coefficients))))
        maximum_residual = max(maximum_residual, residual)
        maximum_integrality_error = max(maximum_integrality_error, integrality_error)
    passed = maximum_residual < 1e-9 and maximum_integrality_error < 1e-9
    return CheckResult(
        "falsified" if passed else "rejected",
        "Every generated E7 root is an integral combination of simple roots and has zero P/Q class.",
        {
            "root_count": len(generated_roots),
            "maximum_basis_residual": maximum_residual,
            "maximum_integrality_error": maximum_integrality_error,
        },
    )


def check_fourier_quotient_filter() -> CheckResult:
    audit = build_fourier_quotient_audit(radius=4)
    return CheckResult(
        str(audit["triad_filter_outcome"]),
        str(audit["proof"]),
        {
            "mode_count": audit["mode_count"],
            "ordered_exact_triad_count": audit["ordered_exact_triad_count"],
            "nontrivial_square_symmetry_map_exists": audit["nontrivial_square_symmetry_map_exists"],
            "maximum_rejected_exact_triad_count": audit["maximum_rejected_exact_triad_count"],
        },
    )


def check_fractal_convergence() -> CheckResult:
    results_path = REPO_ROOT / "experiments" / "results" / "fractal_dimensions.json"
    results = json.loads(results_path.read_text(encoding="ascii"))
    exact_dimensions = {
        "cantor_set": float(np.log(2.0) / np.log(3.0)),
        "sierpinski_triangle": float(np.log(3.0) / np.log(2.0)),
        "koch_snowflake": float(np.log(4.0) / np.log(3.0)),
    }
    absolute_errors = {
        name: abs(float(results[name]["dimension"]) - exact)
        for name, exact in exact_dimensions.items()
    }
    has_refinement_series = all("resolution_series" in results[name] for name in exact_dimensions)
    outcome = (
        "accepted" if has_refinement_series and max(absolute_errors.values()) < 0.02 else "bounded"
    )
    return CheckResult(
        outcome,
        "Exact controls have visible error and no retained multi-resolution convergence series.",
        {
            "absolute_control_errors": absolute_errors,
            "maximum_absolute_control_error": max(absolute_errors.values()),
            "has_refinement_series": has_refinement_series,
        },
    )


def check_retained_lbm_beta_jets() -> CheckResult:
    source = (REPO_ROOT / "src" / "mathphysics" / "quantum_lattice_boltzmann.py").read_text(
        encoding="utf-8"
    )
    audit = json.loads(
        (REPO_ROOT / "data" / "registry" / "lbm_evidence_audit.json").read_text(encoding="ascii")
    )
    final_snapshot = audit["snapshots"][-1]
    beta_enters_source = re.search(r"\bbeta\b", source.lower()) is not None
    zonal_ratio = float(final_snapshot["zonal_to_total_rms_ratio"])
    anisotropy = float(final_snapshot["vorticity_spectral_second_moment_ratio_x_to_y"])
    falsified = not beta_enters_source and zonal_ratio < 0.01 and abs(anisotropy - 1.0) < 0.05
    return CheckResult(
        "falsified" if falsified else "open",
        "The retained solver has no beta term and the final state is nearly isotropic with negligible zonal mean energy.",
        {
            "beta_enters_source": beta_enters_source,
            "final_zonal_to_total_rms_ratio": zonal_ratio,
            "final_vorticity_anisotropy_ratio": anisotropy,
        },
    )


def check_lbm_conservation() -> CheckResult:
    parameters = LBMParameters(
        nx=16,
        ny=16,
        tau=1.5,
        harmonic_amplitude=1e-4,
        num_harmonics=3,
        boundary_type=BoundaryType.PERIODIC,
    )
    simulation = QuantumLatticeBoltzmann(parameters)
    simulation.state.velocity[..., 0] = 0.1
    simulation.state.velocity[..., 1] = 0.05
    simulation._compute_equilibrium()
    equilibrium_error = float(
        np.max(np.abs(np.sum(simulation.state.f_eq, axis=2) - simulation.state.density))
    )
    simulation = QuantumLatticeBoltzmann(parameters)
    simulation.run_simulation(timesteps=50)
    conservation = simulation.validate_conservation(relative_tolerance=1e-10)
    passed = equilibrium_error <= 1e-12 and bool(conservation["mass_conserved"])
    return CheckResult(
        "repaired" if passed else "rejected",
        "The corrected D2Q9 equilibrium and periodic evolution pass mass-conservation regressions.",
        {
            "maximum_equilibrium_density_error": equilibrium_error,
            "periodic_relative_mass_error": conservation["relative_mass_error"],
        },
    )


def check_matched_beta_ablation() -> CheckResult:
    results = json.loads(
        (REPO_ROOT / "data" / "registry" / "beta_plane_ablation_results.json").read_text(
            encoding="ascii"
        )
    )
    criteria = results["aggregate_criteria"]
    maximum_filter_error = max(
        record["comparisons"]["quotient_to_identity_maximum_vorticity_error"]
        for record in results["records"]
    )
    minimum_beta_difference = min(
        record["comparisons"]["beta_to_f_plane_relative_vorticity_l2"]
        for record in results["records"]
    )
    passed = (
        criteria["all_preregistered_implementation_criteria_passed"]
        and maximum_filter_error <= 1e-12
        and minimum_beta_difference > 1e-6
    )
    return CheckResult(
        "falsified" if passed else "rejected",
        "Beta changes every matched trajectory while the homomorphic quotient filter remains exactly identical to its control.",
        {
            "arm_run_count": results["arm_run_count"],
            "minimum_beta_to_f_plane_relative_l2": minimum_beta_difference,
            "maximum_filter_to_identity_error": maximum_filter_error,
            "jet_claim_admitted": criteria["jet_claim_admitted"],
        },
    )


def check_planck_force_identity() -> CheckResult:
    return CheckResult(
        "rejected",
        "Dividing Planck energy by Planck length cancels hbar algebraically and yields c^4/G; this is not a field-theory unification gate.",
        {"hbar_exponent_after_simplification": 0, "result": "c^4/G"},
    )


def check_higher_cayley_physical_mapping() -> CheckResult:
    audit = cast(
        "dict[str, Any]",
        json.loads(
            (REPO_ROOT / "data" / "registry" / "cayley_dickson_property_audit.json").read_text(
                encoding="ascii"
            )
        ),
    )
    validation_report = (
        REPO_ROOT / "research" / "fact_checks" / "mathematical_validation_report.txt"
    ).read_text(encoding="utf-8")
    algebra_names = [str(entry["name"]) for entry in audit["algebras"]]
    serialized_audit = json.dumps(audit, sort_keys=True).lower()
    required_experimental_fields = (
        "dimensional_state_map",
        "measured_observable",
        "matched_algebra_free_control",
        "retained_raw_data",
    )
    present_experimental_fields = [
        field for field in required_experimental_fields if field in serialized_audit
    ]
    report_bounds_physical_scope = (
        "No known physical applications beyond sedenions" in validation_report
    )
    passed = (
        {"Octonion", "Sedenion", "Pathion"}.issubset(algebra_names)
        and not present_experimental_fields
        and report_bounds_physical_scope
    )
    return CheckResult(
        "rejected" if passed else "open",
        "The retained audit reaches higher Cayley-Dickson algebras algebraically but defines no state map, observable, raw dataset, or matched algebra-free control.",
        {
            "audited_algebra_count": len(algebra_names),
            "highest_audited_dimension": max(
                int(entry["dimension"]) for entry in audit["algebras"]
            ),
            "present_experimental_fields": present_experimental_fields,
            "validation_report_bounds_physical_scope": report_bounds_physical_scope,
        },
    )


def check_e10_e11_supergravity_scope() -> CheckResult:
    e10_source = (
        REPO_ROOT / "source_materials" / "pdfs" / "extracted" / "hep-th_0207267.txt"
    ).read_text(encoding="utf-8")
    e11_source = (
        REPO_ROOT / "source_materials" / "pdfs" / "extracted" / "hep-th_0104081.txt"
    ).read_text(encoding="utf-8")
    scope_audit = (REPO_ROOT / "research" / "kac_moody_deep_analysis.txt").read_text(
        encoding="utf-8"
    )
    evidence_flags = {
        "e10_formal_expansion": "A formal" in e10_source and "small tension" in e10_source,
        "e10_finite_height_match": "at least up to 30th order in height" in e10_source,
        "e10_first_four_rungs": "first four rungs" in e10_source,
        "e11_is_conjectural": re.search(
            r"\bwe\s+conjecture\b", e11_source, flags=re.IGNORECASE
        )
        is not None,
        "specific_truncations": "specific truncations" in scope_audit,
        "not_full_quantum_m_theory": "not full quantum M-theory" in scope_audit,
    }
    passed = all(evidence_flags.values())
    return CheckResult(
        "bounded" if passed else "open",
        "The retained E10 result is a finite-height formal supergravity correspondence, while the E11 source states a conjectural nonlinear realization; neither establishes complete M-theory unification.",
        evidence_flags,
    )


def check_dimension_definition_scope() -> CheckResult:
    implementation = (
        REPO_ROOT / "src" / "mathphysics" / "fractal_analysis.py"
    ).read_text(encoding="utf-8")
    validation_report = (
        REPO_ROOT / "research" / "fact_checks" / "mathematical_validation_report.txt"
    ).read_text(encoding="utf-8")
    estimator_names = (
        "box_counting_dimension",
        "hausdorff_dimension",
        "correlation_dimension",
        "information_dimension",
    )
    implemented_estimators = [
        name
        for name in estimator_names
        if re.search(rf"^\s+def {name}\(", implementation, flags=re.MULTILINE)
    ]
    negative_dimension_is_multifractal = (
        "Negative dimensions appear only in multifractal formalism" in validation_report
    )
    rejects_literal_spatial_dimension = (
        "not literal spatial dimensions" in validation_report
    )
    passed = (
        len(implemented_estimators) == len(estimator_names)
        and negative_dimension_is_multifractal
        and rejects_literal_spatial_dimension
    )
    return CheckResult(
        "corrected" if passed else "open",
        "The implementation exposes named nonnegative fractal estimators, while the retained review confines negative values to multifractal spectra rather than spatial axes.",
        {
            "implemented_estimators": implemented_estimators,
            "negative_dimension_is_multifractal": negative_dimension_is_multifractal,
            "rejects_literal_spatial_dimension": rejects_literal_spatial_dimension,
        },
    )


def check_kac_moody_fluid_scope() -> CheckResult:
    implementation = (
        REPO_ROOT / "src" / "mathphysics" / "algebras" / "loop_algebras.py"
    ).read_text(encoding="utf-8")
    missing_bridge_terms = [
        term
        for term in ("ward_identity", "fluid_variable", "vorticity", "dispersion_relation")
        if term not in implementation.lower()
    ]
    not_implemented_count = implementation.count("raise NotImplementedError()")
    algebraic_surface_present = all(
        term in implementation
        for term in ("class AffineLieAlgebra", "level", "get_generalized_cartan_matrix")
    )
    passed = (
        algebraic_surface_present
        and not_implemented_count >= 4
        and len(missing_bridge_terms) == 4
    )
    return CheckResult(
        "rejected" if passed else "open",
        "The retained module exposes an incomplete affine-algebra surface and no Ward-identity, fluid-variable, vorticity, or dispersion bridge.",
        {
            "algebraic_surface_present": algebraic_surface_present,
            "not_implemented_method_count": not_implemented_count,
            "missing_bridge_terms": missing_bridge_terms,
        },
    )


def check_gravitoelectromagnetism_scope() -> CheckResult:
    primary_source = (
        REPO_ROOT / "source_materials" / "pdfs" / "extracted" / "gr-qc_0311030.txt"
    ).read_text(encoding="utf-8")
    paper_section = (
        REPO_ROOT / "papers" / "sections" / "review_physical_claims.tex"
    ).read_text(encoding="utf-8")
    evidence_flags = {
        "linear_perturbation_approach": "Linear Perturbation Approach to GEM" in primary_source,
        "minkowski_background": "Minkowski metric" in primary_source,
        "linear_order": "To linear order in the" in primary_source,
        "transverse_gauge": "transverse gauge condition" in primary_source,
        "paper_rejects_new_coupling": "does not create a new electromagnetic--gravitational coupling"
        in paper_section,
        "paper_preserves_nonlinear_gr": "does not replace the nonlinear Einstein equations"
        in paper_section,
    }
    passed = all(evidence_flags.values())
    return CheckResult(
        "corrected" if passed else "open",
        "The primary source derives GEM as a gauge-fixed linear perturbation of general relativity, and the paper rejects a new coupling or replacement for nonlinear Einstein dynamics.",
        evidence_flags,
    )


def load_admission_packages() -> dict[str, dict[str, Any]]:
    payload = cast(
        "dict[str, Any]",
        json.loads(ADMISSION_PACKAGE_PATH.read_text(encoding="ascii")),
    )
    return {str(package["claim_id"]): package for package in payload["packages"]}


def check_admission_package(claim_id: str, expected_outcome: str, measurable: bool) -> CheckResult:
    package = load_admission_packages()[claim_id]
    energy_accounting = package["energy_accounting"]
    observables = package["observables"]
    controls = package["controls"]
    channels = energy_accounting["channels"]
    if measurable:
        structurally_complete = (
            package["measurable"] is True
            and energy_accounting["required"] is True
            and len(observables) >= 3
            and len(controls) >= 3
            and len(channels) >= 6
            and "residual" in energy_accounting["closure_equation"]
            and len(package["acceptance_criteria"]) >= 3
            and len(package["rejection_criteria"]) >= 3
        )
    else:
        structurally_complete = (
            package["measurable"] is False
            and energy_accounting["required"] is False
            and observables == []
            and controls == []
            and channels == []
        )
    passed = (
        structurally_complete
        and package["admission_ready"] is False
        and package["current_outcome"] == expected_outcome
        and len(package["missing_required_evidence"]) > 0
    )
    return CheckResult(
        expected_outcome if passed else "open",
        "The admission package defines the measurement boundary and preserves the present rejection or scope result until its missing evidence exists.",
        {
            "admission_ready": package["admission_ready"],
            "measurable": package["measurable"],
            "observable_count": len(observables),
            "control_count": len(controls),
            "energy_channel_count": len(channels),
            "missing_evidence_count": len(package["missing_required_evidence"]),
            "structurally_complete": structurally_complete,
        },
    )


def check_scalar_gravity_admission() -> CheckResult:
    return check_admission_package("scalar_field_curvature_mechanism", "rejected", measurable=True)


def check_zpe_energy_admission() -> CheckResult:
    return check_admission_package("zpe_energy_harvesting", "rejected", measurable=True)


def check_time_crystal_energy_admission() -> CheckResult:
    return check_admission_package("time_crystal_energy_amplification", "rejected", measurable=True)


def check_tourmaline_admission() -> CheckResult:
    return check_admission_package("tourmaline_novel_energy_effect", "bounded", measurable=True)


def check_origami_measurability() -> CheckResult:
    return check_admission_package("origami_fold_merge_operator", "excluded", measurable=False)


def check_consciousness_measurability() -> CheckResult:
    return check_admission_package("consciousness_resonance", "excluded", measurable=False)


SPECIAL_CHECKERS: dict[str, Callable[[], CheckResult]] = {
    "cayley_dickson_boundary": check_cayley_dickson_boundary,
    "physical_mapping_admission": check_higher_cayley_physical_mapping,
    "albert_group_scope": check_albert_group_scope,
    "spin8_triality": check_spin8_triality,
    "kac_moody_classification": check_kac_moody_classification,
    "bounded_correspondence_scope": check_e10_e11_supergravity_scope,
    "moonshine_stability_scope": check_moonshine_stability_scope,
    "dimension_definition_scope": check_dimension_definition_scope,
    "e7_root_quotient": check_e7_root_quotient,
    "fourier_quotient_filter": check_fourier_quotient_filter,
    "fractal_convergence": check_fractal_convergence,
    "retained_lbm_beta_jets": check_retained_lbm_beta_jets,
    "lbm_conservation": check_lbm_conservation,
    "matched_beta_ablation": check_matched_beta_ablation,
    "kac_moody_fluid_scope": check_kac_moody_fluid_scope,
    "planck_force_identity": check_planck_force_identity,
    "scalar_gravity_admission": check_scalar_gravity_admission,
    "zpe_energy_admission": check_zpe_energy_admission,
    "time_crystal_energy_admission": check_time_crystal_energy_admission,
    "tourmaline_admission": check_tourmaline_admission,
    "gravitoelectromagnetism_scope": check_gravitoelectromagnetism_scope,
    "operator_measurability": check_origami_measurability,
    "consciousness_measurability": check_consciousness_measurability,
}


def execute_claim_gates() -> dict[str, Any]:
    claims_payload = json.loads(CLAIM_LEDGER_PATH.read_text(encoding="ascii"))
    gates_payload = json.loads(GATE_REGISTRY_PATH.read_text(encoding="ascii"))
    claims = {claim["id"]: claim for claim in claims_payload["claims"]}
    results: list[dict[str, Any]] = []
    for gate in gates_payload["gates"]:
        claim_id = str(gate["claim_id"])
        claim = claims[claim_id]
        missing_evidence = [
            path for path in gate["evidence_paths"] if not (REPO_ROOT / path).exists()
        ]
        checker_name = str(gate["checker"])
        if checker_name not in SPECIAL_CHECKERS:
            raise KeyError(f"No executable checker registered for {checker_name!r}")
        check_result = SPECIAL_CHECKERS[checker_name]()
        status_matches = claim["status"] == gate["expected_claim_status"]
        outcome_matches = check_result.outcome == gate["expected_gate_outcome"]
        gate_passed = status_matches and outcome_matches and not missing_evidence
        results.append(
            {
                "claim_id": claim_id,
                "checker": gate["checker"],
                "gate_kind": gate["gate_kind"],
                "expected_claim_status": gate["expected_claim_status"],
                "actual_claim_status": claim["status"],
                "expected_gate_outcome": gate["expected_gate_outcome"],
                "actual_gate_outcome": check_result.outcome,
                "passed": gate_passed,
                "missing_evidence_paths": missing_evidence,
                "summary": check_result.summary,
                "metrics": check_result.metrics,
            }
        )
    return {
        "schema_version": 1,
        "generator": "scripts/run_claim_gates.py",
        "claim_count": len(claims),
        "gate_count": len(results),
        "passed_count": sum(result["passed"] for result in results),
        "failed_count": sum(not result["passed"] for result in results),
        "all_gates_passed": all(result["passed"] for result in results),
        "results": results,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = parser.parse_args()
    output_path = arguments.output
    if not output_path.is_absolute():
        output_path = REPO_ROOT / output_path
    payload = execute_claim_gates()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(
        json.dumps(payload, indent=2, sort_keys=True, allow_nan=False) + "\n",
        encoding="ascii",
    )
    print(
        f"Wrote {output_path.relative_to(REPO_ROOT)}: "
        f"{payload['passed_count']}/{payload['gate_count']} gates passed"
    )
    return 0 if payload["all_gates_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
