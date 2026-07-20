# Experiments Portfolio Shortlist

This shortlist separates structural falsifiers, numerical regressions, and
physical experiments. Each artifact has one figure or table target and one
gate that must pass before the result enters the paper.

## 1. Quotient-charge triad inventory

- Method: define a typed map from integer Fourier modes to `P/Q`, enumerate all
  triads in a fixed spectral domain, and compare admitted sets under basis
  changes and charge-label shuffles.
- Paper target: a table of total, admitted, rejected, and orbit-equivalent
  triads, plus a shell-by-shell admission plot.
- Validation: exhaustive closure checks and invariance tests. The mechanism is
  rejected before simulation if every mode has zero charge or the filter equals
  its shuffled control.
- Status: complete. The unique nontrivial D4-invariant map exists but admits
  all 3,721 ordered exact triads in the radius-four audit, so the homomorphic
  filter mechanism is falsified.

## 2. Beta-plane matched ablation

- Method: implement an independently specified beta term and compare quotient-
  filtered forcing with a control matched in radial spectrum, total power,
  anisotropy, resolution, time step, boundary condition, and random seed.
- Paper target: effect sizes with confidence intervals for zonal energy
  fraction, jet count, enstrophy flux, and spectral anisotropy.
- Validation: mass and momentum budgets, grid and time-step refinement, multiple
  seeds, and a rejection threshold fixed before execution.
- Status: complete as a preregistered negative-control experiment. Across 36
  arm runs, beta changes every matched trajectory, the quotient and identity
  fields are bit-identical, budgets close, time-step refinement passes, and no
  persistent-jet claim is admitted.

## 3. Retained LBM evidence audit

- Method: read every Parquet state and generate mass, speed, zonal-profile, and
  vorticity anisotropy diagnostics with fixed coordinate conventions.
- Paper target: time series for relative mass drift and zonal-to-total RMS,
  accompanied by a final-state diagnostic table.
- Validation: unit tests on synthetic isotropic and prescribed-zonal fields,
  schema inspection, and source SHA-256 capture.
- Status: implemented in `scripts/analyze_retained_lbm.py`; the retained run is
  nearly isotropic and does not reproduce the published four-jet claim.

## 4. CPU D2Q9 conservation regression

- Method: run the corrected periodic solver from a root-indexed density
  scaffold and record measured mass and kinetic energy.
- Paper target: conservation error by step and a compact equilibrium-identity
  table.
- Validation: the equilibrium populations sum to density at nonzero velocity;
  injected mass causes the validator to fail.
- Status: implemented and passing. This validates the solver prerequisite, not
  a quantum or exceptional-algebra mechanism.

## 5. Tourmaline novelty boundary

- Method: extract the conventional electrical, thermal, and vibration evidence
  separately from proposed enhancement claims. Define the latter with a full
  energy balance and matched material controls before laboratory work.
- Paper target: a claim-source-measurement matrix distinguishing known material
  response from novel excess-energy observables.
- Validation: calibrated raw data, blinded controls, uncertainty propagation,
  and independent replication.
- Status: conventional evidence exists in the corpus; novel coupling evidence
  does not.

## 6. Scientific-document decomposition

- Method: retain native PDF text, run MinerU 3.4.4 high-effort hybrid parsing on
  CUDA, and use 400 DPI Tesseract as an independent fallback.
- Paper target: a page-level extraction ledger with source hash, engine version,
  selected representation, and reason for selection.
- Validation: visual comparison of equations, reading order, tables, diagrams,
  and representative sparse pages. Text length is never treated as accuracy.
- Status: all 878 pages are routed and decomposed; the sparse Superforce
  commentary selects MinerU as primary and Tesseract as fallback.
