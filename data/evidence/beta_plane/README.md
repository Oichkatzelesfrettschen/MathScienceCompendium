# Locked beta-plane primary execution

The primary beta-plane evidence is the first fresh execution of the pinned
container after canonicalizing every seed reduction. The execution is bound to
source commit `144de09947f20a07c4a4da1dd0d649c41d8ba151`.
The image identity is
`sha256:e8689f8912510d5f1f93b1966b89a4e854177d1e474193eb598ff20de6631a6b`.
Its environment report records Python 3.11.13, NumPy 2.4.2, and SciPy 1.17.1.
The production receipt records 540 pending runs and zero resumed runs. The
refinement receipt records 48 pending runs and zero resumed runs.

The earlier host-generated primary artifacts carried source commit
`2164f4fc43223565f172a64052ef169a72d2b23b` but lacked a clean-environment
report. Comparison with the pinned execution preserved the registered
decisions but changed thousands of last-bit floating-point values and every
raw-array digest. The host reports NumPy 2.5.1 and SciPy 1.18.0. The verifier
therefore rejected those artifacts instead of applying a numerical tolerance.
They remain recoverable from Git history and are summarized by
`host_primary_rejection_report.json`.

The next clean execution exposed a separate aggregation defect in the primary
at source commit `ea42a163487dcee01b6e2c785c21ffd65ab4d99c`. All three raw
array archives were byte-identical, the refinement and control JSON outputs
were identical after source-commit normalization, and the scientific decision
remained `not_supported`. One production `effect_estimate` nevertheless
changed by approximately 7e-18 because completed seed records entered a
floating-point mean in worker completion order. The verifier rejected that
primary without a numerical tolerance. Commit `144de09947f20a07c4a4da1dd0d649c41d8ba151`
sorts the reduction by drag, viscosity, and seed before aggregation and adds an
adversarial permutation-invariance test. The complete failed comparison is
retained in `completion_order_rejection_report.json`.

The locked primary artifacts are:

- `production_run_arrays.tar`: `b96bb6ac46a823c5a74d25a895406a8b9b6d78db5a3f49d01262ce44e9f3d61b`
- `refinement_run_arrays.tar`: `6714b6a581b259d96aa9633fbbe1fd016c26459753f6f643a9783868a2bd322d`
- `control_final_states.tar`: `2e6dfe14f80ca19529a910ebcc52582418fa799561ae3127118a4a3c22c95d66`
- `locked_primary_environment_report.json`: `099385f0c935e78e7aea7cf361c3116303a49b5f9ad0dd44405c2175004fc2da`
- `locked_primary_docker_compose_run.tar`: `e399e6b240a865b273474778f4051a6054a2accd2caeebc9a443a437242a5b71`
- `locked_primary_image_identity.json`: `1f4d90841ecf5a2710fc8a9df61cc2ac3143849a5251f144529d0f198fc6a03e`
- `completion_order_rejection_report.json`: `fae4d76addae451204a0b3a9fd514441f625322e5a82d1e2f22a5063ae70c72e`

A second fresh execution from the next committed source tree is required before
any beta result can enter the manuscript result registry.
