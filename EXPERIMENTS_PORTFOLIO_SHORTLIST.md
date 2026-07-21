# Experiments Portfolio Shortlist

This shortlist separates structural falsifiers, numerical regressions, and
physical experiments. Each artifact has one figure or table target and one
gate that must pass before the result enters the paper.

## Theme A: Exact algebraic and operator-support tests

### 1. Quotient-charge triad inventory

- Method: define a typed map from integer Fourier modes to `P/Q`, enumerate all
  triads in a fixed spectral domain, and compare admitted sets under basis
  changes and charge-label shuffles.
- Paper target: a `pgfplots` shell-by-shell table of exact triads and rejected
  channels, with zero modes and PDE-zero channels reported separately.
- Validation: exhaustive closure checks and invariance tests. The mechanism is
  rejected before simulation if every mode has zero charge or the filter equals
  its shuffled control.
- Status: complete. The unique nontrivial D4-invariant map exists but admits
  all 3,721 ordered exact triads in the original radius-four audit, so the
  homomorphic filter mechanism is falsified. Of these, 3,480 contain no zero
  modes and 3,120 have nonzero barotropic interaction coefficients.

### 2. Nonhomomorphic triad-selector audit

- Method: compare identity, exact barotropic operator support, exact Rossby
  resonance, preregistered resonance broadening, the E7 discriminant
  quadratic-defect selector, and equal-density orbit-closed random masks.
- Paper target: a `pgfplots` grouped bar chart of active-channel retention by
  selector family and shell radius.
- Validation: exact arithmetic, source-exchange and cyclic closure, reality
  closure, declared lattice covariance, and instantaneous inviscid energy and
  enstrophy conservation before any trajectory is run.
- Status: radius-two, radius-four, and radius-eight enumeration is complete,
  but conservation and dynamical-control gates remain pending. At radius four
  the quadratic defect admits 656 and rejects 2,464 active channels. Exact
  comparison proves that it is the generic even-checkerboard kernel, so E7
  specificity is falsified before dynamics.

## Theme B: Controlled fluid dynamics

### 3. Beta-plane matched ablation

- Method: implement an independently specified beta term and compare quotient-
  filtered forcing with a control matched in radial spectrum, total power,
  anisotropy, resolution, time step, boundary condition, and random seed.
- Paper target: a `pgfplots` forest plot of paired zonal-fraction and
  persistent-jet-prevalence effects with multiplicity-corrected intervals.
- Validation: mass and momentum budgets, grid and time-step refinement, multiple
  seeds, and a rejection threshold fixed before execution.
- Status: the short implementation ablation and 540-run production sweep are
  complete. The numerical gate passes, but all eight Holm-adjusted primary
  contrasts fail and the registered transient-zonalization claim is falsified.
  An amended 48-run refinement with shared Fourier initial conditions passes
  its time-step, grid, and jet-count gates. No result is paper-promoted without
  independent clean-environment reproduction.

### 4. Retained LBM evidence audit

- Method: read every Parquet state and generate mass, speed, zonal-profile, and
  vorticity anisotropy diagnostics with fixed coordinate conventions.
- Paper target: time series for relative mass drift and zonal-to-total RMS,
  accompanied by a final-state diagnostic table.
- Validation: unit tests on synthetic isotropic and prescribed-zonal fields,
  schema inspection, and source SHA-256 capture.
- Status: implemented in `scripts/analyze_retained_lbm.py`; the retained run is
  nearly isotropic and does not reproduce the published four-jet claim.

### 5. CPU D2Q9 conservation regression

- Method: run the corrected periodic solver from a root-indexed density
  scaffold and record measured mass and kinetic energy.
- Paper target: conservation error by step and a compact equilibrium-identity
  table.
- Validation: the equilibrium populations sum to density at nonzero velocity;
  injected mass causes the validator to fail.
- Status: implemented and passing. This validates the solver prerequisite, not
  a quantum or exceptional-algebra mechanism.

## Theme C: Physical admission and evidence provenance

### 6. Measurable physical-claim admission

- Method: extract the conventional electrical, thermal, and vibration evidence
  separately from proposed enhancement claims. Define the latter with a full
  energy balance and matched material controls before laboratory work.
- Paper target: a claim-source-operator matrix distinguishing conventional
  baselines from novel residuals for tourmaline, driven time crystals,
  scalar-curvature models, and closed-cycle vacuum-work devices.
- Validation: calibrated raw data, blinded controls, uncertainty propagation,
  and independent replication.
- Status: operator packages and promotion states are specified. All four remain
  blocked before calibration because no admissible raw measurements, complete
  channel ledger, or independent replication is retained.

### 7. Scientific-document decomposition

- Method: retain native PDF text, run MinerU 3.4.4 high-effort hybrid parsing on
  CUDA, and use 400 DPI Tesseract as an independent fallback.
- Paper target: a `pgfplots` source-by-source page and extraction-role summary
  backed by the page-level ledger, source hashes, and engine version.
- Validation: visual comparison of equations, reading order, tables, diagrams,
  and representative sparse pages. Text length is never treated as accuracy.
- Status: complete. The 42-PDF, 1,076-page corpus passes through MinerU 3.4.4
  high-effort CUDA decomposition with zero failed sources. The native-text
  audit routes sparse pages to the separate 400 DPI Tesseract comparison.

### 8. Independent promotion reproduction

- Method: reproduce a supported primary result from a fresh source checkout and
  pinned environment without retained run caches. Record the source commit,
  environment image digest, preregistration and result hashes, command, outcome,
  and independent reviewer.
- Paper target: a compact primary-versus-reproduction digest and outcome table.
- Validation: `scripts/validate_hypothesis_promotions.py` rejects eligible or
  promoted claims without a passing clean-environment record and live evidence.
- Status: gate implemented. No new research-program result is eligible for
  positive paper promotion.
