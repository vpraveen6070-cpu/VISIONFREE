"""
test_phase52_sampling.py — Unit Tests for Module A: FFT-Compatible Pupil Grids & Nyquist Criteria
Part of VISIONFREE Phase 5.2 Test Suite.

Tests:
- Non-redundant periodic DFT coordinate grid definition (dx = L / N)
- Explicit coordinate origins:
    * Even N: x[k] = (k - N/2)*dx, exact (0, 0) at index (N/2, N/2)
    * Odd N: x[k] = (k - (N-1)/2)*dx, exact (0, 0) at index ((N-1)/2, (N-1)/2)
- Analytical spatial phase gradient calculation
- Continuous Nyquist sample count threshold
- Dynamic FFT grid size selection with configurable safety factors
- Undersampling detection and diagnostic reporting
- Input validation (negative radius, zero wavelength, non-physical samples)
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from visionfree_research.optics.sampling import (
    DEFAULT_SAFETY_FACTOR,
    DEFAULT_SPAN_FACTOR,
    DEFAULT_WAVELENGTH_PHOTOPIC,
    FFTPupilGrid,
    compute_max_phase_gradient,
    compute_nyquist_grid_size,
    create_fft_pupil_grid,
    evaluate_phase_sampling,
    select_fft_grid_size,
)


class TestModuleASamplingGrid:
    """Tests for Module A: FFT Sampling Grid and Nyquist Criteria."""

    def test_even_grid_coordinate_geometry(self) -> None:
        """
        Verify that for even N, the periodic DFT grid has dx = L / N,
        and (0, 0) is an exact sampled coordinate at index (N/2, N/2).
        """
        r_p = 0.002  # 2 mm
        n = 256
        span_factor = 1.2
        grid = create_fft_pupil_grid(radius=r_p, samples=n, span_factor=span_factor)

        assert grid.samples == n
        assert grid.has_exact_center_sample is True
        assert grid.center_index == (128, 128)

        expected_window = 2.0 * r_p * span_factor  # 0.0048 m
        assert math.isclose(grid.window_width, expected_window, abs_tol=1e-15)

        expected_dx = expected_window / float(n)  # L / N
        assert math.isclose(grid.dx, expected_dx, abs_tol=1e-15)
        assert math.isclose(grid.dy, expected_dx, abs_tol=1e-15)

        # Coordinate at center index (128, 128) must be analytically 0.0
        assert grid.x[128, 128] == 0.0
        assert grid.y[128, 128] == 0.0

        # Boundary coordinate at index 0 must be -L / 2
        assert math.isclose(grid.x[0, 0], -expected_window / 2.0, abs_tol=1e-15)
        assert math.isclose(grid.y[0, 0], -expected_window / 2.0, abs_tol=1e-15)

        # Non-redundant boundary: index N-1 must be L/2 - dx (not +L/2)
        assert math.isclose(grid.x[0, -1], (expected_window / 2.0) - expected_dx, abs_tol=1e-15)

    def test_odd_grid_coordinate_geometry(self) -> None:
        """
        Verify that for odd N, the grid has dx = L / N,
        and (0, 0) is an exact sampled coordinate at index ((N-1)/2, (N-1)/2).
        """
        r_p = 0.002
        n = 255
        span_factor = 1.0
        grid = create_fft_pupil_grid(radius=r_p, samples=n, span_factor=span_factor)

        center_idx = (n - 1) // 2  # 127
        assert grid.center_index == (center_idx, center_idx)
        assert grid.x[center_idx, center_idx] == 0.0
        assert grid.y[center_idx, center_idx] == 0.0

        expected_window = 2.0 * r_p * span_factor
        expected_dx = expected_window / float(n)
        assert math.isclose(grid.dx, expected_dx, abs_tol=1e-15)

        # Symmetric endpoints for odd N: [- (N-1)/2 * dx, + (N-1)/2 * dx]
        max_coord = float(center_idx) * expected_dx
        assert math.isclose(grid.x[0, 0], -max_coord, abs_tol=1e-15)
        assert math.isclose(grid.x[0, -1], +max_coord, abs_tol=1e-15)

    def test_max_phase_gradient_analytical(self) -> None:
        """
        Verify maximum spatial phase gradient calculation:
            ||grad phi||_max = (2 * pi / lambda) * D_max * r_p
        Analytical:
            r_p = 0.002 m (2 mm)
            D_max = 2.50 D
            lambda = 5.55e-7 m (555 nm)
            k = 2 * pi / 5.55e-7 ~ 11321054.498 rad/m
            ||grad phi||_max = 11321054.498 * 2.50 * 0.002 = 56605.272 rad/m
        """
        r_p = 0.002
        d_max = 2.50
        wl = 5.55e-7

        grad_calc = compute_max_phase_gradient(radius=r_p, max_dioptric_power=d_max, wavelength=wl)
        expected_grad = (2.0 * math.pi / wl) * d_max * r_p

        assert math.isclose(grad_calc, expected_grad, rel_tol=1e-12)

    def test_nyquist_grid_size_analytical(self) -> None:
        """
        Verify theoretical continuous Nyquist threshold:
            N_nyquist = (4 * r_p^2 * span_factor * D_max) / lambda
        Analytical:
            r_p = 0.002 m
            span_factor = 1.2
            D_max = 3.0 D
            lambda = 5.55e-7 m
            Numerator = 4 * (0.002)^2 * 1.2 * 3.0 = 5.76e-5
            N_nyquist = 5.76e-5 / 5.55e-7 = 103.78378
        """
        r_p = 0.002
        sf = 1.2
        d_max = 3.0
        wl = 5.55e-7

        n_nyquist = compute_nyquist_grid_size(radius=r_p, max_dioptric_power=d_max, wavelength=wl, span_factor=sf)
        expected_n = (4.0 * (r_p ** 2) * sf * d_max) / wl

        assert math.isclose(n_nyquist, expected_n, rel_tol=1e-12)

    def test_dynamic_grid_selection_power_of_two(self) -> None:
        """
        Verify dynamic power-of-two grid selection with safety factor 1.5:
        N_nyquist ~ 103.78 => target = ceil(1.5 * 103.78) = 156
        Next power of two: 256.
        """
        n_selected = select_fft_grid_size(
            radius=0.002,
            max_dioptric_power=3.0,
            wavelength=5.55e-7,
            span_factor=1.2,
            safety_factor=1.5,
            power_of_two=True,
        )
        assert n_selected == 256

        # For large pupil and high power, verify scaling up
        # r_p = 0.004 (8 mm pupil), D_max = 8.0 D => N_nyquist ~ 1108 => N_selected = 2048
        n_high = select_fft_grid_size(
            radius=0.004,
            max_dioptric_power=8.0,
            wavelength=5.55e-7,
            span_factor=1.2,
            safety_factor=1.5,
            power_of_two=True,
        )
        assert n_high == 2048

    def test_evaluate_phase_sampling_diagnostics(self) -> None:
        """Verify diagnostic evaluation reports correct satisfaction and increments."""
        # Adequately sampled case: N = 256 for 2.0 D with 4 mm pupil
        diag_ok = evaluate_phase_sampling(
            radius=0.002,
            max_dioptric_power=2.0,
            wavelength=5.55e-7,
            grid_samples=256,
            span_factor=1.2,
        )
        assert diag_ok["is_nyquist_satisfied"] is True
        assert diag_ok["max_phase_increment_rad"] < math.pi
        assert diag_ok["safety_margin_ratio"] > 1.0

        # Deliberately undersampled case: N = 32 for 6.0 D with 4 mm pupil
        diag_under = evaluate_phase_sampling(
            radius=0.002,
            max_dioptric_power=6.0,
            wavelength=5.55e-7,
            grid_samples=32,
            span_factor=1.2,
        )
        assert diag_under["is_nyquist_satisfied"] is False
        assert diag_under["max_phase_increment_rad"] > math.pi
        assert diag_under["safety_margin_ratio"] < 1.0

    def test_input_validation(self) -> None:
        """Verify non-physical inputs raise ValueError or TypeError."""
        with pytest.raises(ValueError, match="strictly positive"):
            create_fft_pupil_grid(radius=-0.002, samples=128)

        with pytest.raises(ValueError, match="must be an integer >= 2"):
            create_fft_pupil_grid(radius=0.002, samples=1)

        with pytest.raises(ValueError, match="span_factor must be >= 1.0"):
            create_fft_pupil_grid(radius=0.002, samples=128, span_factor=0.8)

        with pytest.raises(ValueError, match="safety_factor must be >= 1.0"):
            select_fft_grid_size(radius=0.002, max_dioptric_power=2.0, safety_factor=0.5)
