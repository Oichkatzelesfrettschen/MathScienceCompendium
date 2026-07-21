# Locked beta-plane primary execution

The primary beta-plane evidence is the first fresh execution of the pinned
container at source commit `ea42a163487dcee01b6e2c785c21ffd65ab4d99c`.
The image identity is
`sha256:a2afc408cf5d1320a8501bbaa564cdfac4f53d2f6c5e6a9e442c073e041e36ba`.
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

The locked primary artifacts are:

- `production_run_arrays.tar`: `b96bb6ac46a823c5a74d25a895406a8b9b6d78db5a3f49d01262ce44e9f3d61b`
- `refinement_run_arrays.tar`: `6714b6a581b259d96aa9633fbbe1fd016c26459753f6f643a9783868a2bd322d`
- `control_final_states.tar`: `2e6dfe14f80ca19529a910ebcc52582418fa799561ae3127118a4a3c22c95d66`
- `locked_primary_environment_report.json`: `b8a0047b9ddf53c4b2eca29073b8ff1c4b1ebff87dfc7145b0dc17c3f140f4e3`
- `locked_primary_docker_compose_run.tar`: `ee363430a366aad689cf2877dde4a703e07f04b77fec939f3c58c1d2a58ceb36`
- `locked_primary_image_identity.json`: `2e24529847c8a5b6d27174f04c085905a45d4d1bc9fba9511642e134f0145d50`

A second fresh execution from the next committed source tree is required before
any beta result can enter the manuscript result registry.
