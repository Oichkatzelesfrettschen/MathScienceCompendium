"""Deterministic barotropic beta-plane dynamics for matched ablations.

The solver evolves relative vorticity on a doubly periodic square using a
dealiased Fourier pseudospectral discretization and fourth-order Runge-Kutta
time integration. The E7 quotient arm is intentionally a negative control:
the homomorphism admits every exact triad, so it must be bit-identical to the
identity arm.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING

import numpy as np
from scipy.signal import find_peaks


if TYPE_CHECKING:
    from numpy.typing import NDArray


class NonlinearFilter(str, Enum):
    IDENTITY = "identity"
    E7_PQ_HOMOMORPHISM = "e7_pq_homomorphism"


@dataclass(frozen=True)
class BetaPlaneConfig:
    grid_size: int = 32
    time_step: float = 0.005
    steps: int = 100
    beta: float = 5.0
    linear_drag: float = 0.02
    viscosity: float = 5e-4
    initial_wavenumber_minimum: float = 4.0
    initial_wavenumber_maximum: float = 6.0
    initial_energy: float = 0.01
    seed: int = 11
    nonlinear_filter: NonlinearFilter = NonlinearFilter.IDENTITY

    def __post_init__(self) -> None:
        if self.grid_size < 8 or self.grid_size % 2 != 0:
            raise ValueError("grid_size must be an even integer of at least eight")
        if self.time_step <= 0.0 or self.steps <= 0:
            raise ValueError("time_step and steps must be positive")
        if self.linear_drag < 0.0 or self.viscosity < 0.0:
            raise ValueError("linear_drag and viscosity must be nonnegative")
        if not 0.0 < self.initial_wavenumber_minimum < self.initial_wavenumber_maximum:
            raise ValueError("initial wavenumber bounds must be positive and ordered")
        if self.initial_energy <= 0.0:
            raise ValueError("initial_energy must be positive")


@dataclass(frozen=True)
class BetaPlaneRun:
    config: BetaPlaneConfig
    initial_vorticity: NDArray[np.float64]
    final_vorticity: NDArray[np.float64]
    initial_energy: float
    final_energy: float
    initial_enstrophy: float
    final_enstrophy: float
    energy_budget_residual: float
    enstrophy_budget_residual: float
    zonal_kinetic_energy_fraction: float
    spectral_zonal_energy_fraction: float
    jet_count: int
    jet_prominence_threshold: float
    final_window_sample_count: int
    final_window_minimum_zonal_fraction: float
    final_window_jet_counts: tuple[int, ...]
    jet_claim_admitted: bool


class BarotropicBetaPlane:
    """Dealiased pseudospectral barotropic vorticity solver."""

    def __init__(self, config: BetaPlaneConfig) -> None:
        self.config = config
        grid_size = config.grid_size
        domain_spacing = 2.0 * np.pi / grid_size
        wavenumbers = 2.0 * np.pi * np.fft.fftfreq(grid_size, d=domain_spacing)
        self.wavenumber_x, self.wavenumber_y = np.meshgrid(wavenumbers, wavenumbers, indexing="ij")
        self.wavenumber_squared = self.wavenumber_x**2 + self.wavenumber_y**2
        self.inverse_wavenumber_squared = np.zeros_like(self.wavenumber_squared)
        nonzero_modes = self.wavenumber_squared > 0.0
        self.inverse_wavenumber_squared[nonzero_modes] = (
            1.0 / self.wavenumber_squared[nonzero_modes]
        )
        cutoff = grid_size // 3
        self.dealias_mask = (np.abs(self.wavenumber_x) <= cutoff) & (
            np.abs(self.wavenumber_y) <= cutoff
        )

    def initial_vorticity(self) -> NDArray[np.complex128]:
        """Create a seeded, band-limited field normalized by kinetic energy."""
        generator = np.random.default_rng(self.config.seed)
        physical_noise = generator.standard_normal((self.config.grid_size, self.config.grid_size))
        vorticity_hat = np.fft.fft2(physical_noise)
        radial_wavenumber = np.sqrt(self.wavenumber_squared)
        shell = (
            (radial_wavenumber >= self.config.initial_wavenumber_minimum)
            & (radial_wavenumber <= self.config.initial_wavenumber_maximum)
            & self.dealias_mask
        )
        vorticity_hat *= shell
        vorticity_hat[0, 0] = 0.0
        current_energy = self.kinetic_energy(vorticity_hat)
        if current_energy <= 0.0:
            raise ValueError("initial spectral shell contains no active modes")
        vorticity_hat *= np.sqrt(self.config.initial_energy / current_energy)
        return np.asarray(vorticity_hat, dtype=np.complex128)

    def streamfunction_hat(self, vorticity_hat: NDArray[np.complex128]) -> NDArray[np.complex128]:
        return -vorticity_hat * self.inverse_wavenumber_squared

    def physical_fields(
        self, vorticity_hat: NDArray[np.complex128]
    ) -> tuple[
        NDArray[np.float64],
        NDArray[np.float64],
        NDArray[np.float64],
        NDArray[np.float64],
    ]:
        streamfunction_hat = self.streamfunction_hat(vorticity_hat)
        streamfunction = np.fft.ifft2(streamfunction_hat).real
        vorticity = np.fft.ifft2(vorticity_hat).real
        velocity_x = np.fft.ifft2(-1j * self.wavenumber_y * streamfunction_hat).real
        velocity_y = np.fft.ifft2(1j * self.wavenumber_x * streamfunction_hat).real
        return streamfunction, vorticity, velocity_x, velocity_y

    def nonlinear_tendency_hat(
        self, vorticity_hat: NDArray[np.complex128]
    ) -> NDArray[np.complex128]:
        streamfunction_hat = self.streamfunction_hat(vorticity_hat)
        streamfunction_x = np.fft.ifft2(1j * self.wavenumber_x * streamfunction_hat).real
        streamfunction_y = np.fft.ifft2(1j * self.wavenumber_y * streamfunction_hat).real
        vorticity_x = np.fft.ifft2(1j * self.wavenumber_x * vorticity_hat).real
        vorticity_y = np.fft.ifft2(1j * self.wavenumber_y * vorticity_hat).real
        jacobian = streamfunction_x * vorticity_y - streamfunction_y * vorticity_x
        tendency_hat = -np.fft.fft2(jacobian) * self.dealias_mask
        if self.config.nonlinear_filter is NonlinearFilter.E7_PQ_HOMOMORPHISM:
            # Exact convolution triads conserve every homomorphic Z/2 charge.
            # The filter therefore admits the complete tendency without edits.
            return tendency_hat
        return tendency_hat

    def tendency_hat(self, vorticity_hat: NDArray[np.complex128]) -> NDArray[np.complex128]:
        streamfunction_hat = self.streamfunction_hat(vorticity_hat)
        beta_tendency = -self.config.beta * (1j * self.wavenumber_x * streamfunction_hat)
        drag_tendency = -self.config.linear_drag * vorticity_hat
        viscous_tendency = -self.config.viscosity * self.wavenumber_squared * vorticity_hat
        tendency = (
            self.nonlinear_tendency_hat(vorticity_hat)
            + beta_tendency
            + drag_tendency
            + viscous_tendency
        )
        tendency *= self.dealias_mask
        tendency[0, 0] = 0.0
        return np.asarray(tendency, dtype=np.complex128)

    def step(self, vorticity_hat: NDArray[np.complex128]) -> NDArray[np.complex128]:
        time_step = self.config.time_step
        first = self.tendency_hat(vorticity_hat)
        second = self.tendency_hat(vorticity_hat + 0.5 * time_step * first)
        third = self.tendency_hat(vorticity_hat + 0.5 * time_step * second)
        fourth = self.tendency_hat(vorticity_hat + time_step * third)
        updated = vorticity_hat + time_step * (first + 2.0 * second + 2.0 * third + fourth) / 6.0
        updated *= self.dealias_mask
        updated[0, 0] = 0.0
        return np.asarray(updated, dtype=np.complex128)

    def kinetic_energy(self, vorticity_hat: NDArray[np.complex128]) -> float:
        _, _, velocity_x, velocity_y = self.physical_fields(vorticity_hat)
        return float(0.5 * np.mean(velocity_x**2 + velocity_y**2))

    def enstrophy(self, vorticity_hat: NDArray[np.complex128]) -> float:
        vorticity = np.fft.ifft2(vorticity_hat).real
        return float(0.5 * np.mean(vorticity**2))

    def budget_rates(self, vorticity_hat: NDArray[np.complex128]) -> tuple[float, float]:
        streamfunction = np.fft.ifft2(self.streamfunction_hat(vorticity_hat)).real
        vorticity = np.fft.ifft2(vorticity_hat).real
        tendency = np.fft.ifft2(self.tendency_hat(vorticity_hat)).real
        energy_rate = float(-np.mean(streamfunction * tendency))
        enstrophy_rate = float(np.mean(vorticity * tendency))
        return energy_rate, enstrophy_rate

    def zonal_diagnostics(
        self, vorticity_hat: NDArray[np.complex128]
    ) -> tuple[float, float, int, float]:
        _, _, velocity_x, velocity_y = self.physical_fields(vorticity_hat)
        zonal_profile = np.mean(velocity_x, axis=0)
        zonal_profile -= np.mean(zonal_profile)
        total_speed_squared = float(np.mean(velocity_x**2 + velocity_y**2))
        zonal_fraction = (
            float(np.mean(zonal_profile**2)) / total_speed_squared
            if total_speed_squared > 0.0
            else 0.0
        )
        streamfunction_hat = self.streamfunction_hat(vorticity_hat)
        velocity_x_hat = -1j * self.wavenumber_y * streamfunction_hat
        velocity_y_hat = 1j * self.wavenumber_x * streamfunction_hat
        spectral_energy = np.abs(velocity_x_hat) ** 2 + np.abs(velocity_y_hat) ** 2
        spectral_total = float(np.sum(spectral_energy))
        spectral_zonal = float(np.sum(spectral_energy[self.wavenumber_x == 0.0]))
        spectral_fraction = spectral_zonal / spectral_total if spectral_total > 0.0 else 0.0
        zonal_rms = float(np.sqrt(np.mean(zonal_profile**2)))
        prominence = 0.05 * zonal_rms
        if prominence == 0.0:
            jet_count = 0
        else:
            eastward, _ = find_peaks(zonal_profile, prominence=prominence)
            westward, _ = find_peaks(-zonal_profile, prominence=prominence)
            jet_count = len(eastward) + len(westward)
        return zonal_fraction, spectral_fraction, jet_count, prominence

    def run(self) -> BetaPlaneRun:
        vorticity_hat = self.initial_vorticity()
        initial_vorticity = np.fft.ifft2(vorticity_hat).real
        initial_energy = self.kinetic_energy(vorticity_hat)
        initial_enstrophy = self.enstrophy(vorticity_hat)
        prior_energy_rate, prior_enstrophy_rate = self.budget_rates(vorticity_hat)
        integrated_energy_rate = 0.0
        integrated_enstrophy_rate = 0.0
        final_window_start = max(1, int(np.ceil(0.8 * self.config.steps)))
        final_window_zonal_fractions: list[float] = []
        final_window_jet_counts: list[int] = []
        for step_index in range(1, self.config.steps + 1):
            vorticity_hat = self.step(vorticity_hat)
            energy_rate, enstrophy_rate = self.budget_rates(vorticity_hat)
            integrated_energy_rate += (
                0.5 * self.config.time_step * (prior_energy_rate + energy_rate)
            )
            integrated_enstrophy_rate += (
                0.5 * self.config.time_step * (prior_enstrophy_rate + enstrophy_rate)
            )
            prior_energy_rate = energy_rate
            prior_enstrophy_rate = enstrophy_rate
            if step_index >= final_window_start:
                window_zonal_fraction, _, window_jet_count, _ = self.zonal_diagnostics(
                    vorticity_hat
                )
                final_window_zonal_fractions.append(window_zonal_fraction)
                final_window_jet_counts.append(window_jet_count)
        final_energy = self.kinetic_energy(vorticity_hat)
        final_enstrophy = self.enstrophy(vorticity_hat)
        zonal_fraction, spectral_fraction, jet_count, prominence = self.zonal_diagnostics(
            vorticity_hat
        )
        minimum_window_zonal_fraction = min(final_window_zonal_fractions)
        jet_claim_admitted = (
            minimum_window_zonal_fraction > 0.1
            and jet_count > 0
            and set(final_window_jet_counts) == {jet_count}
        )
        return BetaPlaneRun(
            config=self.config,
            initial_vorticity=np.asarray(initial_vorticity, dtype=np.float64),
            final_vorticity=np.asarray(np.fft.ifft2(vorticity_hat).real, dtype=np.float64),
            initial_energy=initial_energy,
            final_energy=final_energy,
            initial_enstrophy=initial_enstrophy,
            final_enstrophy=final_enstrophy,
            energy_budget_residual=(final_energy - initial_energy - integrated_energy_rate),
            enstrophy_budget_residual=(
                final_enstrophy - initial_enstrophy - integrated_enstrophy_rate
            ),
            zonal_kinetic_energy_fraction=zonal_fraction,
            spectral_zonal_energy_fraction=spectral_fraction,
            jet_count=jet_count,
            jet_prominence_threshold=prominence,
            final_window_sample_count=len(final_window_zonal_fractions),
            final_window_minimum_zonal_fraction=minimum_window_zonal_fraction,
            final_window_jet_counts=tuple(final_window_jet_counts),
            jet_claim_admitted=jet_claim_admitted,
        )
