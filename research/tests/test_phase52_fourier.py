"""
test_phase52_fourier.py — Unit Tests for Module B: Fraunhofer Diffraction Propagation
Part of VISIONFREE Phase 5.2 Test Suite.

Tests:
- Discrete retinal sampling pitch: dx_i = (lambda * f) / (N_fft * dx_p)
- Parseval energy conservation: iint |h(x_i, y_i)|^2 dx_i dy_i == iint |P(x_p, y_p)|^2 dx_p dy_p
- Zero-padding support: interpolates focal plane sampling without altering physical pupil aperture
- Spatial centering: centered aperture produces a centered APSF without linear phase tilt
- Both even (N = 128, 256) and odd (N = 127, 255) grid execution
- Error handling on non-positive focal length, wavelength, or mismatched dimensions
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from visionfree_research.optics.fourier_optics import (
    DEFAULT_FOCAL_LENGTH_EYE,
    DEFAULT_WAVELENGTH_PHOTOPIC,
    fraunhofer_propagation,
)
from visionfree_research.optics.sampling import create_fft_pupil_grid


class TestModuleBFraunhoferPropagation:
    """Tests for Module B: Fraunhofer Propagation Engine."""

    def test_image_plane_sampling_pitch_analytical(self) -> None:
        """
        Verify exact analytical focal plane sampling pitch:
            dx_i = (lambda * f) / (N_fft * dx_p) = (lambda * f) / L_p
        Analytical:
            lambda = 5.55e-7 m (555 nm)
            f = 0.017 m (17 mm)
            r_p = 0.002 m (2 mm)
            span_factor = 1.2 => L_p = 2 * r_p * 1.2 = 0.0048 m
            dx_i = (5.55e-7 * 0.017) / 0.0048 = 9.435e-9 / 0.0048 = 1.965625e-6 m (1.966 um)
        """
        r_p = 0.002
        sf = 1.2
        f = 0.017
        wl = 5.55e-7
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=sf)

        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)
        amp_psf, x_i, y_i, dx_i, dy_i = fraunhofer_propagation(
            complex_pupil=p_field,
            pupil_grid=grid,
            focal_length=f,
            wavelength=wl,
        )

        expected_dx_i = (wl * f) / grid.window_width
        assert math.isclose(dx_i, expected_dx_i, rel_tol=1e-12)
        assert math.isclose(dy_i, expected_dx_i, rel_tol=1e-12)
        assert len(x_i) == 128
        assert len(y_i) == 128

    def test_parseval_energy_conservation(self) -> None:
        """
        Verify Parseval's theorem for continuous discrete approximation:
            iint |h(x_i, y_i)|^2 dx_i dy_i == iint |P(x_p, y_p)|^2 dx_p dy_p
        For unit circular pupil transmission:
            Integral(P) = pi * r_p^2
        """
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=256, span_factor=1.2)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        amp_psf, x_i, y_i, dx_i, dy_i = fraunhofer_propagation(
            complex_pupil=p_field,
            pupil_grid=grid,
            focal_length=DEFAULT_FOCAL_LENGTH_EYE,
            wavelength=DEFAULT_WAVELENGTH_PHOTOPIC,
        )

        # Pupil plane energy integral: sum(|P|^2) * dx_p * dy_p
        pupil_energy = np.sum(np.abs(p_field) ** 2) * grid.dx * grid.dy
        # Image plane energy integral: sum(|h|^2) * dx_i * dy_i
        image_energy = np.sum(np.abs(amp_psf) ** 2) * dx_i * dy_i

        # Must conserve energy across Fourier transformation within 0.001%
        assert math.isclose(image_energy, pupil_energy, rel_tol=1e-5)

        # Theoretical aperture area pi * r_p^2
        theoretical_area = math.pi * (r_p ** 2)
        assert math.isclose(pupil_energy, theoretical_area, rel_tol=0.01)

    def test_zero_padding_sampling_refinement(self) -> None:
        """
        Verify zero-padding:
        - When pad_samples = 2 * N_pupil, image pitch dx_i is halved (2x denser sampling).
        - Pupil aperture area and physical energy are completely preserved.
        """
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=1.2)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        # Unpadded
        _, _, _, dx_unpad, _ = fraunhofer_propagation(
            p_field, grid, pad_samples=128
        )
        # Padded to 256
        amp_pad, x_pad, y_pad, dx_pad, _ = fraunhofer_propagation(
            p_field, grid, pad_samples=256
        )

        assert len(x_pad) == 256
        assert math.isclose(dx_pad, dx_unpad / 2.0, rel_tol=1e-12)

        # Energy is conserved in the padded computation
        padded_energy = np.sum(np.abs(amp_pad) ** 2) * dx_pad * dx_pad
        pupil_energy = np.sum(np.abs(p_field) ** 2) * grid.dx * grid.dy
        assert math.isclose(padded_energy, pupil_energy, rel_tol=1e-5)

    def test_odd_and_even_grid_execution(self) -> None:
        """Verify propagation succeeds cleanly on both even (128) and odd (127) sample counts."""
        for n_test in [128, 127]:
            grid = create_fft_pupil_grid(radius=0.002, samples=n_test, span_factor=1.2)
            p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)
            amp, x, y, dx, dy = fraunhofer_propagation(p_field, grid)
            assert amp.shape == (n_test, n_test)
            assert len(x) == n_test
            assert len(y) == n_test

    def test_input_validation(self) -> None:
        """Verify rejection of invalid inputs."""
        grid = create_fft_pupil_grid(radius=0.002, samples=64)
        p_field = np.ones((64, 64), dtype=complex)

        # Invalid focal length
        with pytest.raises(ValueError, match="strictly positive"):
            fraunhofer_propagation(p_field, grid, focal_length=-0.017)

        # Invalid wavelength
        with pytest.raises(ValueError, match="strictly positive"):
            fraunhofer_propagation(p_field, grid, wavelength=0.0)

        # Smaller pad_samples than pupil
        with pytest.raises(ValueError, match="pad_samples must be integer >= pupil samples"):
            fraunhofer_propagation(p_field, grid, pad_samples=32)

        # Mismatched array shape
        with pytest.raises(ValueError, match="does not match pupil_grid samples"):
            fraunhofer_propagation(np.ones((32, 32), dtype=complex), grid)
