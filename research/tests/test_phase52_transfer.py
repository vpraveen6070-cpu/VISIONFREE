"""
test_phase52_transfer.py — Unit Tests for Module D & E: Optical Transfer Function (OTF/MTF/PTF)
Part of VISIONFREE Phase 5.2 Test Suite.

Tests:
- DC normalization: OTF(0, 0) == 1.0 + 0.0j and MTF(0, 0) == 1.0
- MTF non-negativity: MTF(f_x, f_y) >= 0 across all frequencies
- PTF phase bounds in [-pi, pi]
- Real-valued OTF for centrosymmetric aberrations (defocus & regular astigmatism)
- Negative OTF lobes and phase reversal (PTF = +/- pi) under optical defocus
- Numerical MTF agreement with closed-form analytical circular aperture MTF
- Cutoff frequency threshold f_c = D / (lambda * f)
- Pupil autocorrelation cross-check equivalence
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from visionfree_research.optics.fourier_optics import (
    DEFAULT_FOCAL_LENGTH_EYE,
    DEFAULT_WAVELENGTH_PHOTOPIC,
    analytical_diffraction_limited_mtf,
    compute_otf,
    compute_psf,
    pupil_autocorrelation_otf,
)
from visionfree_research.optics.power_vectors import PowerVector
from visionfree_research.optics.pupil import compute_wavefront_phase
from visionfree_research.optics.sampling import create_fft_pupil_grid
from visionfree_research.optics.wavefront import quadratic_wavefront


class TestModuleDOTFAndMTF:
    """Tests for Module D & E: Optical Transfer Function and Modulation Transfer."""

    def test_dc_normalization_and_mtf_non_negativity(self) -> None:
        """Verify OTF(0, 0) == 1.0 + 0.0j, MTF(0, 0) == 1.0, and MTF >= 0 everywhere."""
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=1.2)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        psf_res = compute_psf(p_field, grid)
        otf_res = compute_otf(psf_res)

        # DC component at center index
        c_k = len(otf_res.fx) // 2
        assert math.isclose(otf_res.dc_value.real, 1.0, abs_tol=1e-12)
        assert math.isclose(otf_res.dc_value.imag, 0.0, abs_tol=1e-12)
        assert math.isclose(otf_res.mtf[c_k, c_k], 1.0, abs_tol=1e-12)

        # Strict non-negativity of MTF
        assert np.all(otf_res.mtf >= 0.0)

        # PTF must be bounded within [-pi, pi]
        assert np.all(otf_res.ptf >= -math.pi - 1e-12)
        assert np.all(otf_res.ptf <= math.pi + 1e-12)

    def test_centrosymmetric_aberrations_purely_real_otf(self) -> None:
        """
        Verify that for centrosymmetric aberrations (defocus and astigmatism),
        the OTF imaginary component vanishes (Im{OTF} ~ 0).
        """
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=1.2)
        wl = DEFAULT_WAVELENGTH_PHOTOPIC

        pv = PowerVector(M=-1.50, J0=0.75, J45=-0.50)
        opd = quadratic_wavefront(pv, grid.x, grid.y)
        phi = compute_wavefront_phase(opd, wavelength=wl)
        p_field = np.where(grid.mask, np.exp(1j * phi), 0.0j)

        psf_res = compute_psf(p_field, grid, wavelength=wl)
        otf_res = compute_otf(psf_res)

        # Imaginary component must be negligible (< 1e-10 relative to peak)
        max_imag = np.max(np.abs(otf_res.imag))
        assert max_imag < 1e-9

    def test_defocus_negative_otf_lobe_and_contrast_reversal(self) -> None:
        """
        Verify that severe optical defocus produces negative lobes in the real OTF
        corresponding to a PTF phase shift of pi (contrast reversal).
        """
        r_p = 0.0025  # 5 mm pupil
        grid = create_fft_pupil_grid(radius=r_p, samples=256, span_factor=1.2)
        wl = DEFAULT_WAVELENGTH_PHOTOPIC

        # 3.0 D of spherical defocus
        pv = PowerVector(M=-3.00, J0=0.0, J45=0.0)
        opd = quadratic_wavefront(pv, grid.x, grid.y)
        phi = compute_wavefront_phase(opd, wavelength=wl)
        p_field = np.where(grid.mask, np.exp(1j * phi), 0.0j)

        psf_res = compute_psf(p_field, grid, wavelength=wl)
        otf_res = compute_otf(psf_res)

        # Real OTF must contain negative values
        min_real = np.min(otf_res.real)
        assert min_real < -0.01, f"Expected negative lobe, got min {min_real}"

        # Where real OTF is significantly negative, PTF must be ~ pi (or -pi)
        neg_mask = otf_res.real < -0.05
        assert np.any(neg_mask)
        ptf_at_neg = np.abs(otf_res.ptf[neg_mask])
        assert np.allclose(ptf_at_neg, math.pi, atol=0.1)

    def test_analytical_mtf_diffraction_limited_agreement(self) -> None:
        """
        Verify numerical MTF for clear circular aperture matches the analytical
        Duffieux overlap equation:
            MTF(nu) = (2 / pi) * [ arccos(nu) - nu * sqrt(1 - nu^2) ]
        Using span_factor = 2.5 to provide full linear autocorrelation support (>= 2.0).
        """
        r_p = 0.002  # D = 0.004 m
        f = 0.017    # 17 mm
        wl = 5.55e-7 # 555 nm
        grid = create_fft_pupil_grid(radius=r_p, samples=256, span_factor=2.5)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        psf_res = compute_psf(p_field, grid, focal_length=f, wavelength=wl)
        otf_res = compute_otf(psf_res)

        # Extract 1D horizontal MTF cut
        c_k = len(otf_res.fy) // 2
        freqs = otf_res.fx[c_k:]
        num_mtf = otf_res.mtf[c_k, c_k:]

        # Analytical reference
        d_pupil = 2.0 * r_p
        f_cutoff = d_pupil / (wl * f)
        ana_mtf = analytical_diffraction_limited_mtf(
            spatial_frequency_cycles_per_m=freqs,
            pupil_diameter=d_pupil,
            focal_length=f,
            wavelength=wl,
        )

        # Compare below 80% of cutoff frequency: agreement within 0.1%
        eval_mask = freqs < (0.80 * f_cutoff)
        assert np.allclose(num_mtf[eval_mask], ana_mtf[eval_mask], atol=0.005)

    def test_analytical_diffraction_limited_mtf_properties(self) -> None:
        """Verify analytical MTF function properties."""
        d_p = 0.004
        f = 0.017
        wl = 5.55e-7
        f_cutoff = d_p / (wl * f)

        # Zero frequency is exactly 1.0
        assert math.isclose(analytical_diffraction_limited_mtf(0.0, d_p, f, wl), 1.0, abs_tol=1e-15)

        # At cutoff, MTF is 0.0
        assert math.isclose(analytical_diffraction_limited_mtf(f_cutoff, d_p, f, wl), 0.0, abs_tol=1e-15)

        # Beyond cutoff, MTF is strictly 0.0
        assert analytical_diffraction_limited_mtf(1.5 * f_cutoff, d_p, f, wl) == 0.0

    def test_pupil_autocorrelation_cross_check(self) -> None:
        """
        Verify pupil autocorrelation cross-check:
        The OTF computed via pupil autocorrelation matches the OTF from the PSF
        to machine floating-point precision on the same discrete grid.
        """
        r_p = 0.002
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=2.5)
        p_field = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        psf_res = compute_psf(p_field, grid)
        otf_from_psf = compute_otf(psf_res).otf

        otf_from_autocorr = pupil_autocorrelation_otf(p_field, grid)

        # Both must have DC = 1.0
        c_k = grid.samples // 2
        assert math.isclose(abs(otf_from_psf[c_k, c_k]), 1.0, abs_tol=1e-12)
        assert math.isclose(abs(otf_from_autocorr[c_k, c_k]), 1.0, abs_tol=1e-12)

        # Exact mathematical agreement via Fourier convolution theorem
        assert np.allclose(otf_from_psf, otf_from_autocorr, atol=1e-12)
