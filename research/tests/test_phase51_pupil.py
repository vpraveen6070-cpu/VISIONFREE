"""
test_phase51_pupil.py — Unit Tests for Module E & F: Pupil Grid, Phase & Pupil Function
Part of VISIONFREE Phase 5.1 Test Suite.

Tests:
- Circular pupil aperture mask geometry and symmetry around (0, 0)
- Physical and normalized coordinate relationships (u, v, rho, theta)
- Spatial resolution and pixel pitch dx == dy
- Error handling on invalid radius, sample count, span factor, and wavelength
- Analytical optical phase calculation: phi = 2 * pi * W / lambda
- Generalized complex pupil function boundary conditions:
    * Strictly zero amplitude and zero complex value outside the aperture
    * Unit amplitude inside aperture for uniform transmission
    * Complex angle matches optical phase mod 2*pi
    * Custom amplitude (apodization) support and validation
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from visionfree_research.optics.power_vectors import PowerVector
from visionfree_research.optics.pupil import (
    DEFAULT_WAVELENGTH_PHOTOPIC,
    PupilGrid,
    compute_wavefront_phase,
    create_pupil_grid,
    generalized_pupil_function,
)
from visionfree_research.optics.wavefront import quadratic_wavefront


class TestModuleEPupilGrid:
    """Tests for Module E: Circular Pupil Coordinates."""

    def test_pupil_grid_geometry_and_centering(self) -> None:
        """
        Verify pupil grid centering, boundary dimensions, and circular mask.
        Tested with radius = 0.002 m (4 mm pupil diameter) and samples = 101 (odd, exact center).
        """
        r_p = 0.002
        samples = 101
        grid = create_pupil_grid(radius=r_p, samples=samples, span_factor=1.0)

        # Confirm shape
        assert grid.x.shape == (samples, samples)
        assert grid.y.shape == (samples, samples)
        assert grid.mask.shape == (samples, samples)

        # Center point at index [50, 50] must be exactly (0.0, 0.0)
        center_idx = samples // 2
        assert math.isclose(grid.x[center_idx, center_idx], 0.0, abs_tol=1e-15)
        assert math.isclose(grid.y[center_idx, center_idx], 0.0, abs_tol=1e-15)
        assert grid.mask[center_idx, center_idx] is np.True_ or grid.mask[center_idx, center_idx] == True

        # Check grid boundaries
        assert math.isclose(grid.x[0, 0], -r_p, abs_tol=1e-15)
        assert math.isclose(grid.x[0, -1], +r_p, abs_tol=1e-15)
        assert math.isclose(grid.y[0, 0], -r_p, abs_tol=1e-15)
        assert math.isclose(grid.y[-1, 0], +r_p, abs_tol=1e-15)

        # Check pitch
        expected_dx = (2.0 * r_p) / (samples - 1)
        assert math.isclose(grid.dx, expected_dx, abs_tol=1e-15)
        assert math.isclose(grid.dy, expected_dx, abs_tol=1e-15)

        # Audit check: Odd grid must have exact center sample
        assert grid.has_exact_center_sample is True
        assert grid.center_offset_fraction == 0.0

    def test_even_grid_half_pixel_offset_audit(self) -> None:
        """
        Audit verification for even sample counts (e.g., N = 256 as used in visualization):
        - Confirms that (0, 0) is NOT an exact sampled coordinate.
        - Confirms the grid exhibits a precise half-pixel offset (+/- 0.5 * dx) around the origin.
        - Confirms the two central coordinates straddle zero at -0.5*dx and +0.5*dx.
        """
        r_p = 0.002
        samples = 256
        grid = create_pupil_grid(radius=r_p, samples=samples, span_factor=1.0)

        # Audit check: Even grid must NOT claim an exact center sample
        assert grid.has_exact_center_sample is False
        assert grid.center_offset_fraction == 0.5

        # Check central samples
        idx_left = samples // 2 - 1  # 127
        idx_right = samples // 2      # 128

        x_left = grid.x[idx_left, idx_left]
        x_right = grid.x[idx_right, idx_right]

        # Must be anti-symmetric half-pixel offsets
        assert math.isclose(x_left, -0.5 * grid.dx, abs_tol=1e-15)
        assert math.isclose(x_right, +0.5 * grid.dx, abs_tol=1e-15)

        # Verify no sample in the 256x256 grid is exactly zero
        assert not np.any(grid.x == 0.0)
        assert not np.any(grid.y == 0.0)

    def test_circular_mask_and_fractional_area(self) -> None:
        """
        Verify mask is True if and only if rho <= 1.0 (within tolerance).
        For span_factor=1.0, the fraction of True pixels should approximate pi/4 ~ 0.7854.
        """
        grid = create_pupil_grid(radius=0.0025, samples=256, span_factor=1.0)

        # Mask condition
        assert np.all(grid.mask[grid.rho <= 1.0])
        assert not np.any(grid.mask[grid.rho > 1.0001])

        # Fractional area of circle inscribed in square = pi / 4
        fraction = grid.pupil_area_pixels / (grid.samples ** 2)
        expected_fraction = math.pi / 4.0
        assert math.isclose(fraction, expected_fraction, rel_tol=0.01)

    def test_normalized_coordinates(self) -> None:
        """Verify u = x / r_p, v = y / r_p, rho = sqrt(u^2 + v^2), theta = atan2(y, x)."""
        r_p = 0.0018
        grid = create_pupil_grid(radius=r_p, samples=50, span_factor=1.5)

        assert np.allclose(grid.u, grid.x / r_p, atol=1e-15)
        assert np.allclose(grid.v, grid.y / r_p, atol=1e-15)
        assert np.allclose(grid.rho, np.sqrt(grid.u ** 2 + grid.v ** 2), atol=1e-15)
        assert np.allclose(grid.theta, np.arctan2(grid.y, grid.x), atol=1e-15)

    def test_invalid_pupil_inputs(self) -> None:
        """Verify error handling on non-physical pupil inputs."""
        # Non-positive radius
        with pytest.raises(ValueError, match="strictly positive"):
            create_pupil_grid(radius=0.0, samples=64)

        with pytest.raises(ValueError, match="strictly positive"):
            create_pupil_grid(radius=-0.002, samples=64)

        # Non-finite radius
        with pytest.raises(ValueError, match="must be finite"):
            create_pupil_grid(radius=float("nan"), samples=64)

        # Invalid samples
        with pytest.raises(ValueError, match="samples must be an integer >= 2"):
            create_pupil_grid(radius=0.002, samples=1)

        with pytest.raises(TypeError, match="must be an integer"):
            create_pupil_grid(radius=0.002, samples=64.5)  # type: ignore

        # Invalid span factor
        with pytest.raises(ValueError, match="span_factor must be >= 1.0"):
            create_pupil_grid(radius=0.002, samples=64, span_factor=0.9)


class TestModuleFPhaseAndGeneralizedPupil:
    """Tests for Module F: Phase and Generalized Complex Pupil Function."""

    def test_analytical_optical_phase_calculation(self) -> None:
        """
        Verify optical phase phi = (2 * pi / lambda) * W.
        Analytical test:
            W = -4.0e-6 m (-4.0 micrometers)
            lambda = 5.55e-7 m (555 nm photopic peak)
            k = 2 * pi / 5.55e-7 = 11321054.498 rad/m
            phi = 11321054.498 * (-4.0e-6) = -45.28421799 rad.
        """
        w_val = -4.0e-6
        wavelength = 5.55e-7

        opd_arr = np.array([[w_val, 0.0], [w_val / 2.0, -w_val]])
        phase = compute_wavefront_phase(opd_arr, wavelength=wavelength)

        expected_phi_00 = (2.0 * math.pi / wavelength) * w_val
        assert math.isclose(phase[0, 0], expected_phi_00, rel_tol=1e-12)
        assert math.isclose(phase[0, 1], 0.0, abs_tol=1e-15)

    def test_invalid_wavelength_rejection(self) -> None:
        """Verify non-physical wavelength inputs are rejected."""
        opd = np.zeros((10, 10))
        for bad_wl in [0.0, -500e-9, float("nan"), float("inf")]:
            with pytest.raises(ValueError, match="(strictly positive|must be finite)"):
                compute_wavefront_phase(opd, wavelength=bad_wl)

    def test_generalized_pupil_function_boundary_conditions(self) -> None:
        """
        Verify complex generalized pupil function:
        P(x, y) = A(x, y) * exp(i * phi(x, y))
        - Points outside circular pupil must be STRICTLY 0.0 + 0.0j.
        - Points inside circular pupil must have modulus |P| == 1.0 (for uniform amplitude).
        - Complex angle inside pupil must match phase mod 2*pi.
        """
        r_p = 0.002
        samples = 64
        grid = create_pupil_grid(radius=r_p, samples=samples, span_factor=1.2)

        pv = PowerVector(M=-1.5, J0=0.5, J45=-0.5)
        opd = quadratic_wavefront(pv, grid.x, grid.y)

        pupil_func = generalized_pupil_function(
            opd=opd,
            pupil_grid=grid,
            wavelength=DEFAULT_WAVELENGTH_PHOTOPIC,
        )

        assert pupil_func.shape == (samples, samples)
        assert pupil_func.dtype == np.complex128

        # 1. Outside the circular mask: complex value must be identically zero
        outside_mask = ~grid.mask
        assert np.all(pupil_func[outside_mask] == 0.0 + 0.0j)
        assert np.all(np.abs(pupil_func[outside_mask]) == 0.0)

        # 2. Inside circular mask: modulus must be 1.0 (uniform transmission)
        inside_mask = grid.mask
        moduli_inside = np.abs(pupil_func[inside_mask])
        assert np.allclose(moduli_inside, 1.0, atol=1e-12)

        # 3. Phase check inside mask: angle(P) == (phi + pi) % (2*pi) - pi
        phase_raw = compute_wavefront_phase(opd, wavelength=DEFAULT_WAVELENGTH_PHOTOPIC)
        wrapped_phase_expected = (phase_raw[inside_mask] + math.pi) % (2.0 * math.pi) - math.pi
        measured_angles = np.angle(pupil_func[inside_mask])
        assert np.allclose(measured_angles, wrapped_phase_expected, atol=1e-12)

    def test_custom_amplitude_apodization(self) -> None:
        """Verify custom scalar or 2D array amplitude inside aperture."""
        r_p = 0.002
        grid = create_pupil_grid(radius=r_p, samples=32, span_factor=1.0)
        opd = np.zeros((32, 32))

        # Scalar transmission = 0.75
        p_scalar = generalized_pupil_function(opd, grid, amplitude=0.75)
        assert np.allclose(np.abs(p_scalar[grid.mask]), 0.75, atol=1e-12)
        assert np.all(p_scalar[~grid.mask] == 0.0j)

        # Negative amplitude rejected
        with pytest.raises(ValueError, match="cannot be negative"):
            generalized_pupil_function(opd, grid, amplitude=-0.1)
