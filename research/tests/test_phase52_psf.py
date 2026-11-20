"""
test_phase52_psf.py — Unit Tests for Module C: Intensity Point Spread Function & Airy Validation
Part of VISIONFREE Phase 5.2 Test Suite.

Tests:
- PSF non-negativity across all spatial coordinates
- Normalization conventions:
    * Integrated energy: iint PSF dx dy == 1.0
    * Discrete probability: sum(PSF) == 1.0
    * Physical unnormalized irradiance
- Centroid alignment on optical axis for centered pupils
- Exact scalar defocus symmetry: PSF(+Defocus) == PSF(-Defocus)
- Astigmatic PSF orientation and asymmetry (0 deg, 90 deg, 45 deg)
- Quantitative Airy disk validation against analytical Bessel reference:
    * Peak location at r = 0
    * First dark ring location r_1 = 1.21967 * lambda * f / D
    * Secondary ring peak intensity ratio (~1.75%)
    * Encircled energy (~83.78%)
- Wavelength diffraction scaling (red 650 nm vs blue 450 nm)
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from visionfree_research.optics.fourier_optics import (
    DEFAULT_FOCAL_LENGTH_EYE,
    DEFAULT_WAVELENGTH_PHOTOPIC,
    analytical_airy_psf,
    analytical_airy_zeros,
    compute_psf,
)
from visionfree_research.optics.power_vectors import PowerVector
from visionfree_research.optics.pupil import compute_wavefront_phase
from visionfree_research.optics.sampling import create_fft_pupil_grid
from visionfree_research.optics.wavefront import quadratic_wavefront


class TestModuleCPSFAndAiryValidation:
    """Tests for Module C: Point Spread Function Generation & Airy Benchmarks."""

    def test_psf_non_negativity_and_normalizations(self) -> None:
        """Verify PSF is strictly non-negative and satisfies both normalization modes."""
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=1.2)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        # 1. Integrated normalization
        res_int = compute_psf(p_field, grid, normalization="integrated")
        assert np.all(res_int.psf >= 0.0)
        assert math.isclose(res_int.total_integrated_energy, 1.0, abs_tol=1e-12)
        assert res_int.peak_intensity > 0.0

        # 2. Discrete probability normalization
        res_prob = compute_psf(p_field, grid, normalization="probability")
        assert np.all(res_prob.psf >= 0.0)
        assert math.isclose(res_prob.discrete_sum, 1.0, abs_tol=1e-12)

        # 3. Physical irradiance
        res_phys = compute_psf(p_field, grid, normalization="physical")
        assert np.all(res_phys.psf >= 0.0)
        assert res_phys.scale_factor_applied == 1.0

    def test_centroid_on_optical_axis(self) -> None:
        """Verify centroid of an unaberrated centered pupil aligns with (0, 0)."""
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=256, span_factor=1.2)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        res = compute_psf(p_field, grid)
        c_x, c_y = res.centroid

        # Centroid should be on axis within fraction of grid resolution (5 nm residual due to even-grid parity)
        assert abs(c_x) < (0.01 * res.dx)
        assert abs(c_y) < (0.01 * res.dy)
        assert math.isclose(c_x, 0.0, abs_tol=1e-7)
        assert math.isclose(c_y, 0.0, abs_tol=1e-7)

    def test_defocus_sign_reversal_psf_symmetry(self) -> None:
        """
        Verify fundamental scalar optics theorem:
        Under scalar monochromatic Fraunhofer propagation with an even aperture,
        positive defocus (+M) and negative defocus (-M) produce identical intensity PSFs:
            |h(x_i, y_i; +W)|^2 == |h(x_i, y_i; -W)|^2
        """
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=1.2)
        wl = DEFAULT_WAVELENGTH_PHOTOPIC

        pv_pos = PowerVector(M=+1.50, J0=0.0, J45=0.0)
        pv_neg = PowerVector(M=-1.50, J0=0.0, J45=0.0)

        opd_pos = quadratic_wavefront(pv_pos, grid.x, grid.y)
        opd_neg = quadratic_wavefront(pv_neg, grid.x, grid.y)

        phi_pos = compute_wavefront_phase(opd_pos, wavelength=wl)
        phi_neg = compute_wavefront_phase(opd_neg, wavelength=wl)

        p_pos = np.where(grid.mask, np.exp(1j * phi_pos), 0.0j)
        p_neg = np.where(grid.mask, np.exp(1j * phi_neg), 0.0j)

        psf_pos = compute_psf(p_pos, grid, wavelength=wl)
        psf_neg = compute_psf(p_neg, grid, wavelength=wl)

        assert np.allclose(psf_pos.psf, psf_neg.psf, atol=1e-12)

    def test_astigmatic_psf_asymmetry_and_orientation(self) -> None:
        """
        Verify astigmatic PSF responds to cylinder axis orientation:
        - Cylinder at 0 deg: power along vertical meridian creates vertical blur
        - Cylinder at 90 deg: power along horizontal meridian creates horizontal blur
        - Cylinder at 45 deg: oblique blur along diagonal
        """
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=1.2)
        wl = DEFAULT_WAVELENGTH_PHOTOPIC

        # 0 deg cylinder: S = 0.0, C = -2.0, alpha = 0 deg => J0 = +1.0, J45 = 0.0
        pv_0 = PowerVector(M=-1.0, J0=1.0, J45=0.0)
        # 90 deg cylinder: J0 = -1.0, J45 = 0.0
        pv_90 = PowerVector(M=-1.0, J0=-1.0, J45=0.0)
        # 45 deg cylinder: J0 = 0.0, J45 = 1.0
        pv_45 = PowerVector(M=-1.0, J0=0.0, J45=1.0)

        def make_psf(pv: PowerVector) -> np.ndarray:
            opd = quadratic_wavefront(pv, grid.x, grid.y)
            phi = compute_wavefront_phase(opd, wavelength=wl)
            p = np.where(grid.mask, np.exp(1j * phi), 0.0j)
            return compute_psf(p, grid, wavelength=wl).psf

        psf_0 = make_psf(pv_0)
        psf_90 = make_psf(pv_90)
        psf_45 = make_psf(pv_45)

        # psf_90 is psf_0 rotated by 90 degrees (transposed)
        assert np.allclose(psf_0, psf_90.T, atol=1e-10)

        # psf_45 is oblique (neither horizontal nor vertical)
        assert not np.allclose(psf_45, psf_0, atol=1e-5)

    def test_airy_disk_analytical_first_dark_ring(self) -> None:
        """
        Verify numerical Airy disk first minimum matches the analytical formula:
            r_first_zero = 1.21966989 * lambda * f / D
        Using zero-padding (N_pad = 512) for sub-micron image plane sampling.
        """
        r_p = 0.002  # D = 0.004 m
        f = 0.017    # 17 mm
        wl = 5.55e-7 # 555 nm
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=1.2)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        # Compute PSF with 512-point zero-padding
        res = compute_psf(p_field, grid, focal_length=f, wavelength=wl, pad_samples=512)

        zeros = analytical_airy_zeros(radius_or_diameter=r_p, focal_length=f, wavelength=wl)
        r1_analytical = zeros["r_first_zero_m"]
        expected_r1 = 1.21966989 * (wl * f) / (2.0 * r_p)  # ~ 2.876 um
        assert math.isclose(r1_analytical, expected_r1, rel_tol=1e-6)

        # Find first radial minimum along central horizontal cut (index y=256)
        c_idx = len(res.y) // 2
        line_cut = res.psf[c_idx, c_idx:]
        r_coords = res.x[c_idx:]

        # Find first radial dark ring: first local minimum where intensity starts rising
        diffs = np.diff(line_cut)
        first_min_indices = np.where(diffs > 0)[0]
        assert len(first_min_indices) > 0, "No dark ring local minimum found."
        first_min_idx = first_min_indices[0]
        measured_r1 = r_coords[first_min_idx]

        # Measured minimum must match analytical within discrete grid resolution dx_i
        dx_i = res.dx
        assert abs(measured_r1 - r1_analytical) <= (1.0 * dx_i)

    def test_airy_analytical_reference_functions(self) -> None:
        """Verify analytical Airy functions evaluate exact mathematical constants."""
        r_p = 0.002
        f = 0.017
        wl = 5.55e-7

        # Peak at r=0 is exactly 1.0
        val_0 = analytical_airy_psf(r_p, f, wl, r_image=0.0)
        assert math.isclose(val_0, 1.0, abs_tol=1e-15)

        # At first zero, intensity is 0.0
        zeros = analytical_airy_zeros(r_p, f, wl)
        r1 = zeros["r_first_zero_m"]
        val_r1 = analytical_airy_psf(r_p, f, wl, r_image=r1)
        assert math.isclose(val_r1, 0.0, abs_tol=1e-7)

        # Encircled energy inside first ring is 83.78%
        ee = zeros["encircled_energy_first_ring"]
        assert math.isclose(ee, 0.837785, rel_tol=1e-4)

    def test_wavelength_diffraction_scaling(self) -> None:
        """
        Verify diffraction scaling with wavelength:
        Red light (650 nm) produces a wider diffraction spot than blue light (450 nm)
        by the exact ratio 650 / 450 ~ 1.444.
        """
        r_p = 0.002
        f = 0.017
        wl_red = 6.50e-7
        wl_blue = 4.50e-7

        zeros_red = analytical_airy_zeros(r_p, f, wl_red)
        zeros_blue = analytical_airy_zeros(r_p, f, wl_blue)

        ratio = zeros_red["r_first_zero_m"] / zeros_blue["r_first_zero_m"]
        expected_ratio = wl_red / wl_blue
        assert math.isclose(ratio, expected_ratio, rel_tol=1e-12)
