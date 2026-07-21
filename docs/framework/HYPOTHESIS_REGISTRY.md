# Hypothesis Registry

This is the human-readable view of `data/registry/hypothesis_registry.json`.
The JSON registry is canonical. Contract consistency is not scientific admission.
A supported or negative result remains out of the paper until its locked decision
rule is evaluated and a cache-isolated clean-environment rerun is retained.

## Coverage

- Registered hypotheses: 14
- Canonical source claims covered: 16
- Active: 1
- Blocked: 9
- Excluded: 2
- Falsified: 1
- Not supported: 1
- Explicit archival conjectures and predictions dispositioned: 54
- Programs: beta_plane_jets=1, e7_fourier_selector=1, foundational_backlog=6, physical_admission=6

## Promotion policy

- A computational or empirical hypothesis result may enter the manuscript only when its locked decision rule is evaluated and paper_promotion is eligible or promoted.
- Every supported or negative computational or empirical result requires a cache-isolated rerun in a pinned clean environment, with separate runner and reviewer roles, before promotion. This gate establishes computational repeatability, not external replication or an independent implementation.
- Literature is admitted only when it directly defines, constrains, tests, or falsifies a registered hypothesis; literature cannot substitute for repository evidence.

## hyp_higher_cayley_dickson_observable: Higher Cayley-Dickson zero-divisor observable

- Program: `foundational_backlog`
- Source claims: `higher_cayley_dickson_physical_mapping`
- Research status: `blocked`
- Implementation status: `design_only`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

For declared state spaces X_ZD and X_0, dynamics Phi_t, and measurement Y, an intervention that changes only zero-divisor structure produces a nonzero preregistered contrast E[Y(Phi_t(X_ZD)) - Y(Phi_t(X_0))].

Observable predictions:

- `zero_divisor_contrast`: Matched difference in the declared response Y Prediction: The confidence interval excludes zero and exceeds the preregistered minimum effect. Method: Run identical dynamics on algebraic and algebra-free states matched for spectrum, energy, dimension, parameter count, and conditioning.

Controls:

- Algebra-free state with matched spectrum and energy
- Basis-scrambled multiplication table
- Parameter-count- and conditioning-matched surrogate

Falsification thresholds:

- Falsify the physical mapping if the corrected 95 percent confidence interval contains zero.
- Falsify specificity if any matched surrogate reproduces the effect within the preregistered equivalence margin.

Required evidence:

- `definition` / `missing`: Typed physical state map, intervention, dynamics, observable, units, and nuisance parameters.
- `derivation` / `missing`: Algebra-to-observable mechanism with dimensional consistency.
- `control` / `planned`: Matched algebra-free and scrambled-label controls.
- `literature` / `present`: Algebraic boundary and zero-divisor foundations. Artifacts: `data/external/sources.toml`.
- `replication` / `external_required`: Independent reproduction after a primary result exists.

Aligned literature: `arxiv_baez_math_0105155`, `arxiv_moreno_math_0512517`

## hyp_e10_e11_truncation_dictionary: Finite E10 or E11 supergravity dictionary

- Program: `foundational_backlog`
- Source claims: `e10_e11_supergravity_scope`
- Research status: `blocked`
- Implementation status: `design_only`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

For a fixed algebra, level or height cutoff L, and explicit dictionary phi_L, every declared algebraic equation maps to the named supergravity equation through L, with the first unmatched term recorded.

Observable predictions:

- `truncation_residual`: Symbolic residual of each mapped equation through cutoff L Prediction: Every in-scope residual simplifies exactly to zero and the first out-of-scope mismatch is identified. Method: Evaluate the locked dictionary symbolically and compare term-by-term with the declared supergravity truncation.

Controls:

- Label-shuffled dictionary
- Competing dictionary with the same number of free correspondences

Falsification thresholds:

- One nonzero exact residual within the declared cutoff falsifies the stated dictionary.
- Instability of previously matched terms when L is increased falsifies truncation stability.

Required evidence:

- `definition` / `missing`: Explicit algebra, real form, truncation, variables, and typed dictionary.
- `derivation` / `missing`: Term-by-term symbolic equation map.
- `literature` / `present`: Foundational E10 and E11 supergravity proposals. Artifacts: `data/external/sources.toml`.
- `control` / `planned`: Dictionary specificity controls.
- `replication` / `external_required`: Independent symbolic reproduction.

Aligned literature: `arxiv_damour_e10_0207267`, `arxiv_west_e11_0104081`

## hyp_moonshine_stability_operator: Moonshine-specific stability operator

- Program: `foundational_backlog`
- Source claims: `monstrous_moonshine_stability`
- Research status: `blocked`
- Implementation status: `design_only`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

A declared Monster representation rho and evolution U_t preserve a named invariant and improve a preregistered stability functional relative to equal-dimensional non-Monster controls.

Observable predictions:

- `stability_margin`: Difference in the declared Lyapunov or norm-growth bound Prediction: The Monster construction improves the bound beyond the locked minimum margin. Method: Evaluate the same evolution and perturbation ensemble under Monster, non-Monster, and label-shuffled representations.

Controls:

- Equal-dimensional non-Monster representation
- Label-shuffled representation
- Invariant-disabled ablation

Falsification thresholds:

- Failure of the claimed commutation or invariant relation falsifies the mechanism.
- A corrected confidence interval overlapping the locked equivalence margin falsifies a stability advantage.

Required evidence:

- `definition` / `missing`: Representation, evolution, invariant, perturbation ensemble, and stability functional.
- `derivation` / `missing`: Proof linking the representation to the stability inequality.
- `literature` / `present`: Moonshine theorem and modern representation foundations. Artifacts: `data/external/sources.toml`.
- `control` / `planned`: Equal-capacity alternative representation controls.
- `replication` / `external_required`: Independent computational reproduction.

Aligned literature: `borcherds_monstrous_moonshine_1992`, `arxiv_duncan_griffin_ono_1411_6571`

## hyp_fractal_estimator_convergence: Fractal estimator convergence under refinement

- Program: `foundational_backlog`
- Source claims: `fractal_estimator_convergence`
- Research status: `active`
- Implementation status: `implemented_inconclusive`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

For exact-dimension controls and declared estimators, absolute error decreases under resolution refinement and remains stable under adjacent scale-window choices.

Observable predictions:

- `maximum_dimension_error`: Maximum absolute dimension error across locked exact controls Prediction: The retained refinement series reaches error below 0.02 without a worsening terminal trend. Method: Run box-counting and comparison estimators on Cantor, Sierpinski, Koch, and nonfractal controls at preregistered resolutions and scale windows.

Controls:

- Cantor set
- Sierpinski triangle
- Koch curve
- Nonfractal line and plane

Falsification thresholds:

- Falsify convergence if maximum absolute error remains at or above 0.02 at the terminal preregistered resolution.
- Falsify scale stability if adjacent admissible windows shift the estimate by 0.02 or more.

Required evidence:

- `simulation` / `present`: Retained baseline estimator outputs. Artifacts: `experiments/results/fractal_dimensions.json`.
- `control` / `missing`: Exact-dimension refinement series and scale-window sensitivity.
- `replication` / `external_required`: Independent clean-environment estimator run.

Aligned literature: none admitted

## hyp_scalar_curvature_action: Covariant scalar-curvature mechanism

- Program: `physical_admission`
- Source claims: `scalar_field_curvature_mechanism`
- Research status: `blocked`
- Implementation status: `blocked_external_evidence`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

A frozen covariant action with declared fields, units, gauge, background, and boundary data yields ghost-free field equations and a dimensioned observable that differs from GR and minimally coupled scalar controls.

Observable predictions:

- `held_out_curvature_observable`: Named dimensioned curvature or propagation observable on held-out data Prediction: The corrected 95 percent confidence interval excludes both matched controls by the preregistered minimum effect. Method: Derive and solve all arms at matched resolution, then evaluate the locked observable on held-out cases.

Controls:

- General relativity
- Minimally coupled scalar field
- Null-source evolution

Falsification thresholds:

- Reject if a ghost, gradient instability, or tachyonic physical mode exists in the declared regime.
- Reject if normalized constraints exceed 1e-8 or fail refinement.
- Reject if the multiplicity-corrected distinguishing test fails at alpha 0.05.

Required evidence:

- `definition` / `missing`: Covariant action, units, fields, gauge, background, and boundaries.
- `derivation` / `missing`: Field equations, stress tensor, constraints, and perturbation spectrum.
- `control` / `planned`: Matched GR, minimal-scalar, and null-source simulations.
- `measurement` / `external_required`: Held-out dimensioned observable with uncertainty.
- `replication` / `external_required`: Independent reproduction of derivation and observable.

Aligned literature: none admitted

## hyp_zpe_closed_cycle_work: Positive closed-cycle vacuum-device work

- Program: `physical_admission`
- Source claims: `zpe_energy_harvesting`
- Research status: `blocked`
- Implementation status: `blocked_external_evidence`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

A physical device produces positive net useful work over a complete return cycle after electrical, pump, boundary-control, environmental heat, radiative, dissipative, and stored-energy channels are included.

Observable predictions:

- `net_cycle_work`: Net useful cycle work with propagated uncertainty Prediction: The multiplicity-corrected lower 95 percent confidence bound is above zero after three-sigma energy closure. Method: Calibrate and integrate every energy channel over blinded complete cycles and compare with disabled, classical, and sham controls.

Controls:

- Modulation-disabled cycles
- Matched classical parametric source
- Blind sham cycles

Falsification thresholds:

- Reject if any declared energy channel is omitted.
- Reject if the closure residual exceeds three propagated standard uncertainties.
- Reject if the corrected lower 95 percent confidence bound for net work is not above zero in either primary or independent replication.

Required evidence:

- `definition` / `missing`: Physical device, return cycle, measurement operators, and complete energy ledger.
- `measurement` / `external_required`: Calibrated blinded raw cycle data and uncertainty covariance.
- `control` / `external_required`: Disabled, classical, and sham control cycles.
- `literature` / `present`: Casimir, dynamical-Casimir, and quantum inequality constraints. Artifacts: `data/external/sources.toml`.
- `replication` / `external_required`: Independent device and analysis replication.

Aligned literature: `arxiv_jaffe_hep_th_0503158`, `arxiv_wilson_1105_4714`, `arxiv_fewster_1208_5399`

## hyp_time_crystal_net_period_work: Time-crystalline order separated from net energy gain

- Program: `physical_admission`
- Source claims: `time_crystal_energy_amplification`
- Research status: `blocked`
- Implementation status: `blocked_external_evidence`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

A specified driven many-body system exhibits locked subharmonic order, while a separate complete period-resolved ledger determines whether net useful work remains positive after drive, heat, storage, and loss terms.

Observable predictions:

- `subharmonic_order`: Subharmonic order parameter and lifetime Prediction: The response remains locked over the preregistered perturbation range and exceeds all phase-destroying controls. Method: Measure the locked Fourier component and lifetime for interacting, noninteracting, localization-disabled, off-resonant, and sham-drive arms.
- `net_period_work`: Net useful work over integer drive periods Prediction: The corrected lower 95 percent confidence bound is above zero after three-sigma energy closure. Method: Integrate all work, heat, storage, and loss channels over complete periods.

Controls:

- Noninteracting system
- Localization-disabled system
- Off-resonant drive
- Sham drive

Falsification thresholds:

- Reject time-crystalline order if the subharmonic response is not locked or is reproduced by phase-destroying controls.
- Reject energy amplification if closure exceeds three uncertainties or the corrected lower bound for net period work is not positive.

Required evidence:

- `definition` / `missing`: Hamiltonian or open-system generator and period-resolved energy operators.
- `measurement` / `external_required`: Raw order-parameter and complete energy-channel time series.
- `control` / `external_required`: Interacting and phase-destroying control arms.
- `literature` / `present`: No-go theorem and discrete time-crystal foundations. Artifacts: `data/external/sources.toml`.
- `replication` / `external_required`: Independent order and energy replication.

Aligned literature: `arxiv_watanabe_oshikawa_1410_2143`, `arxiv_else_bauer_nayak_1603_08001`, `arxiv_zhang_1609_08684`, `arxiv_camacho_fauseweh_2605_27211`

## hyp_planck_force_unification_action: Planck-force unification action

- Program: `foundational_backlog`
- Source claims: `planck_force_unification`
- Research status: `blocked`
- Implementation status: `design_only`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

A common action containing explicit field content reproduces declared Standard Model and general-relativistic low-energy limits and predicts an observable not implied by their uncoupled combination.

Observable predictions:

- `distinguishing_low_energy_observable`: Preregistered low-energy observable unique to the common action Prediction: The result differs from Standard Model plus general relativity and equal-parameter effective-field-theory controls by the locked minimum effect. Method: Derive all limits and evaluate the observable under the common action and matched alternatives.

Controls:

- Standard Model plus general relativity
- Equal-parameter effective field theories

Falsification thresholds:

- Failure to recover any declared low-energy limit falsifies the model.
- Absence of a distinguishing observable leaves c^4/G as dimensional analysis rather than unification evidence.

Required evidence:

- `definition` / `missing`: Common action, fields, symmetries, units, and coupling constants.
- `derivation` / `missing`: Standard Model and general-relativistic limits plus distinguishing prediction.
- `control` / `planned`: Equal-capacity alternative theories.
- `replication` / `external_required`: Independent analytic and numerical reproduction.

Aligned literature: `pais_superforce_2023`, `brandenburg_comment_superforce`

## hyp_origami_typed_operator: Typed fold-merge operator

- Program: `physical_admission`
- Source claims: `origami_fold_merge_operator`
- Research status: `excluded`
- Implementation status: `excluded_undefined`
- Independent reproduction: `not_applicable`
- Paper promotion: `prohibited`

Formal statement:

A declared operator F from state space X to state space Y is closed on its domain, has stated regularity and invariants, and produces an observable not equivalent to a coordinate transformation.

Observable predictions:

- `noncoordinate_effect`: Invariant physical contrast between F and an equivalent coordinate transformation Prediction: The contrast exceeds a preregistered nonzero minimum effect. Method: Evaluate the same states under F and the matched coordinate-only control.

Controls:

- Equivalent coordinate transformation
- Identity operator

Falsification thresholds:

- An undefined domain, codomain, operator law, or observable excludes the claim from testing.
- Observational equivalence to the coordinate control falsifies the proposed physical effect.

Required evidence:

- `definition` / `missing`: Domain, codomain, topology, measure, operator law, regularity, and invariants.
- `measurement` / `missing`: Operational physical state map and observable.
- `control` / `planned`: Coordinate-equivalence control.

Aligned literature: none admitted

## hyp_e7_nonhomomorphic_fourier_selector: E7 specificity of a nonhomomorphic Fourier triad selector

- Program: `e7_fourier_selector`
- Source claims: `e7_root_quotient_charge`, `external_fourier_quotient_map`
- Research status: `falsified`
- Implementation status: `implemented_negative`
- Independent reproduction: `passed`
- Paper promotion: `promoted`

Formal statement:

The E7 discriminant quadratic-defect mask uses epsilon(k)=(kx+ky) mod 2 and D4=3*(epsilon(k)+epsilon(p)+epsilon(q)) mod 4. E7 specificity requires this mask to differ on at least one locked exact triad from the generic even-checkerboard kernel.

Observable predictions:

- `checkerboard_specificity_difference`: Mismatch count between the quadratic-defect and generic checkerboard masks Prediction: At least one exact triad differs on each locked square Fourier domain. Method: Exhaustively enumerate integer triads k+p+q=0 at radii 2, 4, and 8 and compare both masks exactly.
- `controlled_dynamical_effect`: Paired change in locked flow diagnostics Prediction: Only a selector that survives the exact checkerboard control may proceed to matched dynamical controls. Method: Run paired simulations with identical initial fields and matched triad-retention rates.

Controls:

- Identity selector
- Failed homomorphic parity selector
- Generic even-checkerboard sublattice
- Alternative parity maps
- Label-shuffled selector with identical triad-retention rate
- Equal-density orbit-closed random masks
- Matched radial-spectrum, power, and anisotropy controls
- Square-symmetry-breaking selector ablation

Falsification thresholds:

- Reject E7 specificity if the quadratic-defect mask is exactly the generic checkerboard kernel.
- Reject the replacement if it accepts all or no exact triads on any locked evaluation domain.
- Reject the claimed symmetry if any exact rotation or reflection test fails.
- Reject a dynamical advantage unless corrected paired confidence bounds exceed the preregistered minimum effect against every matched control.

Required evidence:

- `definition` / `present`: Typed nonhomomorphic selector and explicit statement that it is not an E7 root charge. Artifacts: `src/mathphysics/triad_selectors.py`, `data/registry/e7_selector_preregistration.json`.
- `derivation` / `present`: Exact Cartan inverse, discriminant value, selector counts, and declared lattice symmetries. Artifacts: `data/registry/triad_selector_audit.json`, `tests/unit/test_triad_selectors.py`.
- `simulation` / `planned`: Generic parity-kernel dynamics only after conservation gates.
- `control` / `present`: Exact generic-checkerboard equivalence control. Artifacts: `data/registry/triad_selector_audit.json`, `tests/unit/test_triad_selectors.py`.
- `control` / `planned`: Identity, homomorphism, alternative parity, and equal-rate shuffled controls.
- `replication` / `present`: Cache-isolated clean-environment rerun. Artifacts: `data/registry/independent_reproduction_registry.json`, `data/reproduction/verification_report.json`, `data/reproduction/triad_selector_audit.json`.

Aligned literature: `arxiv_kartashov_kartashova_1307_8272`, `arxiv_hayat_amanullah_walsh_bustamante_1804_03092`

## hyp_kac_moody_fluid_dictionary: Kac-Moody current-to-fluid dictionary

- Program: `foundational_backlog`
- Source claims: `kac_moody_fluid_transfer`
- Research status: `blocked`
- Implementation status: `design_only`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

A typed map from declared Kac-Moody currents and a Sugawara stress tensor to dimensioned fluid variables satisfies the Ward identities and yields a dispersion relation that outperforms a spectrum- and power-matched label-shuffled forcing control.

Observable predictions:

- `dispersion_residual`: Residual of the derived dispersion relation and paired flow diagnostic effect Prediction: Ward and dispersion residuals pass exact or locked numerical tolerances and the flow effect exceeds the matched control. Method: Evaluate the typed dictionary symbolically, then run paired forcing with identical spectra and injected power.

Controls:

- Label-shuffled forcing with identical spectrum and power
- Current-disabled evolution

Falsification thresholds:

- Any failed type, unit, or Ward-identity check falsifies the declared dictionary.
- A paired effect interval overlapping the equivalence margin falsifies transfer specificity.

Required evidence:

- `definition` / `missing`: Currents, representation level, stress tensor, fluid variables, units, and map.
- `derivation` / `missing`: Ward identities and fluid dispersion relation.
- `simulation` / `missing`: Matched forcing experiment.
- `replication` / `external_required`: Independent symbolic and numerical reproduction.

Aligned literature: none admitted

## hyp_beta_plane_transient_zonalization: Transient beta-dependent zonalization of freely decaying turbulence

- Program: `beta_plane_jets`
- Source claims: `lbm_beta_plane_and_jets`, `matched_beta_plane_algebraic_ablation`
- Research status: `not_supported`
- Implementation status: `implemented_negative`
- Independent reproduction: `passed`
- Paper promotion: `promoted`

Formal statement:

In the declared dealiased barotropic beta-plane solver without sustained forcing, beta equal to 5 and 10 increases final-window zonal energy fraction and persistent-jet prevalence relative to paired beta-zero controls across preregistered drag, viscosity, and seed cells.

Observable predictions:

- `zonal_fraction_contrast`: Paired final-window mean zonal energy fraction difference versus beta zero Prediction: For beta 5 and 10, the Holm-adjusted exact sign-flip p-value is below 0.05, the simultaneous lower 95 percent confidence bound is above zero, and the estimated difference is at least 0.05. Method: Use seed-paired, drag-paired, and viscosity-paired production runs with exact seed-cluster sign flips and Bonferroni-simultaneous bootstrap intervals.
- `persistent_jet_prevalence`: Paired persistent-jet prevalence difference versus beta zero Prediction: For beta 5 and 10, the Holm-adjusted exact sign-flip p-value is below 0.05, the simultaneous lower 95 percent confidence bound is above zero, and the estimated difference is at least 0.50. Method: Apply fixed circular peak diagnostics over the final 25 percent of every run.

Controls:

- Paired beta-zero f-plane runs
- Transposed-initial-field f-plane runs
- Failed E7 homomorphic-selector sentinels
- Synthetic prescribed-zonal positive controls
- Retained high-resolution LBM null corpus

Falsification thresholds:

- A run is persistent only when final-window mean and 10th-percentile zonal fractions are at least 0.10, modal jet count is at least 2, and modal-count occupancy is at least 0.80.
- Reject numerical admission if normalized energy or enstrophy residual exceeds 1e-6, time-step change is at least 2 percent, grid change is at least 5 percent, or refined jet count differs by more than one.
- Reject the primary claim unless both beta 5 and beta 10 pass the Holm-adjusted sign-flip tests, simultaneous confidence bounds, and minimum effects for both endpoints.

Required evidence:

- `definition` / `present`: Locked decaying-turbulence protocol, parameter matrix, diagnostics, and multiplicity plan. Artifacts: `data/registry/beta_plane_sweep_preregistration.json`, `scripts/run_beta_plane_sweep.py`.
- `simulation` / `present`: Existing short beta-response and homomorphic-filter negative-control ablation. Artifacts: `data/registry/beta_plane_ablation_results.json`.
- `simulation` / `present`: Production sweep, refinement runs, tracked time series, profiles, and normalized budget residuals. Artifacts: `data/registry/beta_plane_sweep_results.json`, `data/registry/beta_plane_refinement_results.json`, `data/registry/beta_plane_refinement_protocol_amendment.json`, `data/evidence/beta_plane/production_run_arrays.tar`, `data/evidence/beta_plane/refinement_run_arrays.tar`.
- `control` / `present`: F-plane, transpose, synthetic-positive, LBM-null, and quotient-sentinel controls. Artifacts: `data/registry/beta_plane_control_results.json`, `data/registry/lbm_evidence_audit.json`.
- `replication` / `present`: Cache-isolated clean-environment rerun. Artifacts: `data/registry/independent_reproduction_registry.json`, `data/reproduction/verification_report.json`, `data/reproduction/beta_plane_sweep_results.json`.

Aligned literature: `arxiv_bakas_constantinou_ioannou_1407_3354`, `arxiv_bakas_constantinou_ioannou_1708_03031`, `arxiv_kartashov_kartashova_1307_8272`, `arxiv_hayat_amanullah_walsh_bustamante_1804_03092`, `arxiv_sahoo_ray_2507_23493`

## hyp_tourmaline_excess_cycle_energy: Tourmaline response beyond conventional constitutive models

- Program: `physical_admission`
- Source claims: `tourmaline_novel_energy_effect`
- Research status: `blocked`
- Implementation status: `blocked_external_evidence`
- Independent reproduction: `pending`
- Paper promotion: `prohibited`

Formal statement:

After fitting conventional pyroelectric, piezoelectric, dielectric, thermal, triboelectric, vibrational, and electromagnetic responses on calibration data, blinded tourmaline cycles retain a positive novelty residual and closed excess-energy balance.

Observable predictions:

- `novelty_residual`: Held-out residual charge, voltage, current, or work beyond the conventional constitutive model Prediction: The Holm-corrected lower 95 percent confidence bound exceeds the preregistered minimum effect while energy closure remains within three uncertainties. Method: Calibrate stress, temperature, charge, voltage, current, and vibration; lock the model; then evaluate blind material and orientation arms.

Controls:

- Rotated crystal axis
- Nonpolar matched material
- Conventional reference material
- Dummy fixture

Falsification thresholds:

- Reject novelty if the conventional model explains the held-out response within the locked equivalence margin.
- Reject an energy claim if any channel is omitted or closure exceeds three propagated standard uncertainties.
- Reject promotion unless the corrected effect survives independent replication.

Required evidence:

- `definition` / `missing`: Composition, orientation, geometry, electrodes, cycle, operators, and conventional constitutive model.
- `measurement` / `external_required`: Calibrated blinded raw cycles and complete energy ledger.
- `control` / `external_required`: Axis, nonpolar, reference-material, and dummy-fixture arms.
- `replication` / `external_required`: Independent material, apparatus, and analysis replication.

Aligned literature: none admitted

## hyp_consciousness_operational_endpoint: Operational biological endpoint for consciousness resonance

- Program: `physical_admission`
- Source claims: `consciousness_resonance`
- Research status: `excluded`
- Implementation status: `excluded_undefined`
- Independent reproduction: `not_applicable`
- Paper promotion: `prohibited`

Formal statement:

A declared intervention and dose produce a preregistered change in an operational biological endpoint under a causal model and blinded matched comparator.

Observable predictions:

- `blinded_biological_effect`: Preregistered operational biological endpoint Prediction: The corrected effect exceeds the locked minimum effect and replicates independently. Method: Apply randomized blinded intervention and comparator assignments under a declared causal model.

Controls:

- Blinded sham intervention
- Dose-zero arm
- Matched nonspecific stimulation

Falsification thresholds:

- An undefined intervention, dose, endpoint, or causal model excludes the claim from testing.
- A preregistered null or control-equivalent response falsifies the declared effect.

Required evidence:

- `definition` / `missing`: Intervention, dose, endpoint, causal model, comparator, and minimum effect.
- `measurement` / `external_required`: Ethically approved blinded raw data.
- `control` / `external_required`: Sham, dose-zero, and nonspecific controls.
- `replication` / `external_required`: Independent preregistered replication.

Aligned literature: none admitted

## Archival conjecture dispositions

These dormant legacy items are not manuscript claims. Each remains traceable
so it cannot silently re-enter the active authority surface.

### `papers/sections/vol4_ch12_unresolved.tex`

- `legacy_op_12_1` (12.1): Physical Relevance of Sedenions - `mapped`. The active hypothesis replaces false algebraic premises with a typed observable contrast. Maps to `hyp_higher_cayley_dickson_observable`.
- `legacy_op_12_2` (12.2): Alternativity Beyond Octonions - `superseded`. The retained Cayley-Dickson audit supplies exact counterexamples beyond octonions.
- `legacy_op_12_3` (12.3): Cayley-Dickson to 2048 Dimensions - `mapped`. Dimension alone is not a physical hypothesis; only the typed observable replacement remains active. Maps to `hyp_higher_cayley_dickson_observable`.
- `legacy_op_12_4` (12.4): E10 Role in M-Theory - `mapped`. The active record requires a finite truncation and exact dictionary. Maps to `hyp_e10_e11_truncation_dictionary`.
- `legacy_op_12_5` (12.5): E11 Mathematical Consistency - `mapped`. The active record bounds the claim to an explicit truncation and first mismatch. Maps to `hyp_e10_e11_truncation_dictionary`.
- `legacy_op_12_6` (12.6): Umbral Moonshine Classification - `field_open_problem`. This literature-level classification problem is not a claim contributed by the framework.
- `legacy_op_12_7` (12.7): Physical Meaning of Negative Dimensions - `superseded`. The active review distinguishes formal dimension estimators from literal negative spatial axes.
- `legacy_op_12_8` (12.8): Correct Quantum Gravity Theory - `field_open_problem`. This is a field-wide question rather than a testable framework claim.
- `legacy_op_12_9` (12.9): Planck Force Physical Meaning - `mapped`. The active record requires a common action and distinguishing observable. Maps to `hyp_planck_force_unification_action`.
- `legacy_op_12_10` (12.10): GUT Scale Unification - `field_open_problem`. The broad field problem is not a specific framework prediction.
- `legacy_op_12_11` (12.11): Role of Exceptional Groups in Unification - `mapped`. A physical role requires an explicit common action and low-energy limits. Maps to `hyp_planck_force_unification_action`.
- `legacy_op_12_12` (12.12): Vacuum Energy Catastrophe - `field_open_problem`. The cosmological-constant problem is not solved or newly posed by this framework.
- `legacy_op_12_13` (12.13): Casimir Effect Engineering - `mapped`. Any extraction extension is governed by the complete-cycle energy ledger. Maps to `hyp_zpe_closed_cycle_work`.
- `legacy_op_12_14` (12.14): String Landscape vs. Swampland - `field_open_problem`. This is a literature-level problem outside the framework's admitted contributions.
- `legacy_op_12_15` (12.15): Fractal String Theory - `excluded_undefined`. No action, state space, or observable is defined.
- `legacy_op_12_16` (12.16): Lorentz Invariance Violation - `field_open_problem`. No framework-specific coefficient or dispersion relation is declared.
- `legacy_op_12_17` (12.17): Gravitational Wave Modifications - `mapped`. A distinguishing propagation observable belongs under the covariant scalar-curvature model. Maps to `hyp_scalar_curvature_action`.
- `legacy_op_12_18` (12.18): Tourmaline Zero-Point Energy Extraction - `mapped`. Material novelty and closed-cycle vacuum work are tested separately. Maps to `hyp_tourmaline_excess_cycle_energy`, `hyp_zpe_closed_cycle_work`.
- `legacy_op_12_19` (12.19): Metamaterial Applications - `field_open_problem`. Applications require device-specific operators and are not one scientific claim.
- `legacy_op_12_20` (12.20): Framework Mathematical Consistency - `superseded`. The active claim ledger replaces the monolithic consistency prompt with atomic checks.
- `legacy_op_12_21` (12.21): Framework Completeness - `excluded_undefined`. Completeness is undefined without a target theory class and adequacy criterion.
- `legacy_op_12_22` (12.22): Pre-paradigmatic vs. Paradigmatic Science - `excluded_undefined`. This is an epistemic classification prompt, not an observable scientific hypothesis.

### `papers/sections/vol2_ch6_string_theory.tex`

- `legacy_op_6_1` (OP-6.1): Landscape Selection - `field_open_problem`. The string landscape is a field-wide issue rather than a framework result.
- `legacy_op_6_2` (OP-6.2): Moduli Stabilisation - `field_open_problem`. No framework-specific compactification or moduli potential is supplied.
- `legacy_op_6_3` (OP-6.3): E11 Full Proof - `mapped`. The active record tests finite declared correspondences without claiming a full proof. Maps to `hyp_e10_e11_truncation_dictionary`.
- `legacy_op_6_4` (OP-6.4): Experimental Testability - `field_open_problem`. Planck-scale access is a broad field constraint, not a repository hypothesis.

### `papers/sections/vol2_ch7_quantum_gravity.tex`

- `legacy_op_7_1` (OP-7.1): Semiclassical Limit of LQG - `field_open_problem`. This is a field-wide LQG question and not a framework contribution.
- `legacy_op_7_2` (OP-7.2): Truncation Convergence in Asymptotic Safety - `field_open_problem`. This is a field-wide asymptotic-safety question.
- `legacy_op_7_3` (OP-7.3): Experimental Signatures - `field_open_problem`. No framework-specific signature or minimum effect is supplied.
- `legacy_op_7_4` (OP-7.4): Unification of Approaches - `field_open_problem`. Shared dimensional reduction is not itself a typed unification mechanism.

### `papers/sections/vol2_ch6_quantum_encoding.tex`

- `legacy_quantum_encoding_optimality` (Open Problems item 1): Universal optimal E7 encoding - `excluded_undefined`. Optimality lacks a workload, cost model, hardware target, and comparison class.
- `legacy_quantum_encoding_error_correction` (Open Problems item 2): E7-native error-correcting codes - `excluded_undefined`. No code family, noise model, distance, or decoder is defined.
- `legacy_quantum_encoding_advantage` (Open Problems item 3): E7 quantum advantage - `excluded_undefined`. No problem family, oracle model, complexity bound, or classical baseline is defined.

### `papers/sections/vol3_ch10_predictions.tex`

- `legacy_prediction_2048d_planck` (Alpha table row 1): 2048D structure affects Planck-scale physics - `mapped`. Only a typed zero-divisor observable remains testable. Maps to `hyp_higher_cayley_dickson_observable`.
- `legacy_prediction_kac_moody_scattering` (Alpha table row 2): Kac-Moody symmetries detectable in scattering - `mapped`. A specific algebra, dictionary, amplitude, and energy range are required. Maps to `hyp_e10_e11_truncation_dictionary`.
- `legacy_prediction_fractal_gr` (Alpha table row 3): Fractal dimensions modify general relativity - `mapped`. The estimator and covariant action burdens are separate. Maps to `hyp_scalar_curvature_action`, `hyp_fractal_estimator_convergence`.
- `legacy_prediction_monster_compactification` (Alpha table row 4): Monster group constrains compactification - `mapped`. A representation, operator, and matched control are missing. Maps to `hyp_moonshine_stability_operator`.
- `legacy_prediction_triality_interactions` (Alpha table row 5): Octonion triality in particle interactions - `excluded_undefined`. No process, representation action, energy scale, or observable is specified.
- `legacy_prediction_nodespace_transitions` (Unified Model table row 1): Nodespace transitions at phase boundaries - `excluded_undefined`. Nodespace and the transition operator are undefined.
- `legacy_prediction_fractal_cosmology` (Unified Model table row 2): Fractal structure in cosmological evolution - `excluded_undefined`. No estimator-to-cosmological-observable map is supplied.
- `legacy_prediction_metaprinciple_symmetry` (Unified Model table row 3): Meta-principle governs symmetry breaking - `excluded_undefined`. The meta-principle has no mathematical operator or quantitative prediction.
- `legacy_prediction_nodespace_susy` (Unified Model table row 4): Supersymmetry broken by a nodespace mechanism - `excluded_undefined`. No supermultiplet, breaking operator, scale, or spectrum is defined.
- `legacy_prediction_planck_force_fundamental` (Metaprinciple table row 1): Planck force is fundamental - `mapped`. The dimensional identity is not a mechanism; the active hypothesis requires an action. Maps to `hyp_planck_force_unification_action`.
- `legacy_prediction_macroscopic_planck_quantum` (Metaprinciple table row 2): Macroscopic quantum phenomena at Planck force - `mapped`. No dimensioned deviation exists outside the common-action hypothesis. Maps to `hyp_planck_force_unification_action`.
- `legacy_prediction_subplanck_quantum_gravity` (Metaprinciple table row 3): Quantum-gravity effects below the Planck scale - `excluded_undefined`. No model-specific deviation, energy range, or observable is declared.
- `legacy_prediction_superforce_unification` (Metaprinciple table row 4): Unification of forces by superforce - `mapped`. The active hypothesis demands field content and low-energy limits. Maps to `hyp_planck_force_unification_action`.
- `legacy_prediction_tourmaline_piezoelectric` (Tourmaline table row 1): Tourmaline piezoelectric coefficient - `superseded`. This conventional measurable property is a baseline, not a novel hypothesis.
- `legacy_prediction_tourmaline_shg` (Tourmaline table row 2): Tourmaline second-harmonic generation - `superseded`. This conventional optical response is a baseline and control variable.
- `legacy_prediction_tourmaline_thermal` (Tourmaline table row 3): Tourmaline thermal-conductivity anisotropy - `superseded`. This conventional response belongs in the constitutive baseline.
- `legacy_prediction_tourmaline_zpe` (Tourmaline table row 4): Zero-point energy couples to the tourmaline lattice - `mapped`. Novel material residuals and complete-cycle net work are tested separately. Maps to `hyp_tourmaline_excess_cycle_energy`, `hyp_zpe_closed_cycle_work`.
- `legacy_prediction_biological_coherence` (Tourmaline table row 5): Quantum coherence in biological systems - `mapped`. The claim remains excluded until intervention and endpoint are operational. Maps to `hyp_consciousness_operational_endpoint`.

### `papers/sections/vol2_ch5_superforce.tex`

- `legacy_superforce_vacuum_bernoulli` (Prediction 1): Vacuum Bernoulli gravitational perturbation - `mapped`. The relation lacks a covariant action and complete apparatus energy ledger. Maps to `hyp_scalar_curvature_action`, `hyp_zpe_closed_cycle_work`.
- `legacy_superforce_inertial_mass` (Prediction 2): Electromagnetic-field inertial mass reduction - `mapped`. A covariant mechanism and matched GR control are required. Maps to `hyp_scalar_curvature_action`.
- `legacy_superforce_material_g` (Prediction 3): Material-dependent gravitational constant - `mapped`. Changing permittivity does not alter G without a derived coupling and distinguishing measurement. Maps to `hyp_scalar_curvature_action`.
