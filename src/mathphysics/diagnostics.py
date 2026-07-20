"""Shared diagnostics for numerical physics artifacts."""

from __future__ import annotations

import numpy as np


def calculate_vorticity(velocity: np.ndarray) -> np.ndarray:
    """Return scalar vorticity under the repository coordinate convention.

    Array axis 0 is x, array axis 1 is y, and the final component axis stores
    (velocity_x, velocity_y). Therefore omega_z = d(velocity_y)/dx -
    d(velocity_x)/dy.
    """
    if velocity.ndim != 3 or velocity.shape[-1] != 2:
        raise ValueError("velocity must have shape (x, y, 2)")
    return np.gradient(velocity[..., 1], axis=0) - np.gradient(
        velocity[..., 0],
        axis=1,
    )
