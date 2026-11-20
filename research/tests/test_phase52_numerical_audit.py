"""
test_phase52_numerical_audit.py — Independent Numerical & Physical Optics Audit Tests
Part of VISIONFREE Phase 5.2.1: Independent Fourier Optics Numerical Audit.

Validates:
1. Parseval energy conservation BEFORE any PSF normalization (machine-precision agreement).
2. Airy first zero localization: distinguishing nearest discrete pixel, parabolic fit, and spline root.
3. Independent closed-form Duffieux MTF verification vs. numerical OTF.
4. Algebraic dual equivalence of PSF-derived OTF and pupil autocorrelation OTF.
5. Mathematical consistency of sampling safety ratios and classification thresholds.
6. Sub-pixel centroid parity behavior across grid resolutions.
"""

from __future__ import annotations

import math
import numpy as np
import pytest
from scipy.interpolate import CubicSpline
from scipy.optimize import root_scalar

from visionfree_research.optics.sampling import (
    create_fft_pupil_grid,
    compute_nyquist_grid_size,
    compute_max_phase_gradient,
    select_fft_grid_size,
    evaluate_phase_sampling,
)
from visionfree_research.optics.fourier_optics import (
    fraunhofer_propagation,
    compute_psf,
    compute_otf,
    analytical_airy_zeros,
    analytical_airy_psf,
    analytical_diffraction_limited_mtf,
    pupil_autocorrelation_otf,
)


class TestModuleENumericalParsevalAudit:
    """Verify energy conservation and Parseval relation before any explicit normalization."""

    @pytest.mark.parametrize("n_samples", [64, 128, 256, 512])
    @pytest.mark.parametrize("pad_samples", [None, 512, 1024])
    def test_unnormalized_parseval_machine_precision(
        self, n_samples: int, pad_samples: int | None
    ) -> None:
        """
        Verify that discrete focal plane integrated energy:
            iint |U_i(x_i, y_i)|^2 dx_i dy_i
        agrees with discrete pupil plane energy:
            iint |P(x_p, y_p)|^2 dx_p dy_p
        to machine precision (relative error < 1e-14) BEFORE any normalization.
        """
        r_p = 0.002
        f = 0.017
        wl = 5.50e-7
        grid = create_fft_pupil_grid(radius=r_p, samples=n_samples, span_factor=1.8)

        # Complex aberrated & apodized pupil field
        r = grid.rho
        p_field = np.where(grid.mask, np.exp(-1.16e5 * r**2) * np.exp(1j * 3.5e5 * r**2), 0.0j)

        dx_p = grid.dx
        dy_p = grid.dy
        discrete_pupil_energy = float(np.sum(np.abs(p_field) ** 2) * (dx_p * dy_p))

        pad = pad_samples if (pad_samples is not None and pad_samples >= n_samples) else n_samples
        field, x_i, y_i, dx_i, dy_i = fraunhofer_propagation(
            p_field, grid, pad_samples=pad, wavelength=wl, focal_length=f
        )
        focal_energy_unnorm = float(np.sum(np.abs(field) ** 2) * (dx_i * dy_i))

        rel_diff = abs(focal_energy_unnorm - discrete_pupil_energy) / discrete_pupil_energy
        assert rel_diff < 1e-14, f"Parseval violated! RelDiff={rel_diff}"

    def test_discrete_pupil_area_convergence_to_pi_r_squared(self) -> None:
        """
        Verify that discrete pupil area sum(mask) * dx_p^2 converges monotonically
        to the continuous analytical circle area pi * r_p^2 as O(1/N).
        """
        r_p = 0.002
        analytical_area = math.pi * (r_p ** 2)

        errors_pct = []
        for n in [64, 128, 256, 512, 1024]:
            grid = create_fft_pupil_grid(radius=r_p, samples=n, span_factor=2.0)
            p_clear = np.where(grid.mask, 1.0, 0.0)
            discrete_area = float(np.sum(p_clear) * (grid.dx * grid.dy))
            err_pct = abs(discrete_area - analytical_area) / analytical_area * 100.0
            errors_pct.append(err_pct)

        # Error must decrease monotonically
        for k in range(len(errors_pct) - 1):
            assert errors_pct[k + 1] <= errors_pct[k]
        # By N=1024, error must be under 0.05%
        assert errors_pct[-1] < 0.05


class TestModuleFAiryLocalizationAudit:
    """Verify Airy zero localization distinguishing discrete, parabolic, and spline methods."""

    def test_distinguish_discrete_vs_spline_airy_zeros(self) -> None:
        """
        Verify that:
        1. Nearest discrete pixel coordinate has a quantization error ~ 0.5 * dx_i.
        2. Subpixel spline root achieves < 0.05% relative error against analytical r1.
        """
        r_p = 0.002
        f = 0.017
        wl = 5.50e-7
        grid = create_fft_pupil_grid(radius=r_p, samples=256, span_factor=2.0)
        p_clear = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        # Pad to 2048 for dx_i = 0.146 um
        field, x_i, y_i, dx_i, dy_i = fraunhofer_propagation(
            p_clear, grid, pad_samples=2048, wavelength=wl, focal_length=f
        )
        c_k = len(x_i) // 2
        cut = np.abs(field[c_k, c_k:]) ** 2
        r_coords = x_i[c_k:]

        # Theoretical exact value: u1 * lambda * f / (pi * D)
        exact_r1_target = 2.8509783708354544e-6
        zeros = analytical_airy_zeros(r_p, f, wl)
        r1_analytical = zeros["r_first_zero_m"]
        assert math.isclose(r1_analytical, exact_r1_target, abs_tol=1e-15)

        diffs = np.diff(cut)
        first_min_idx = np.where(diffs > 0)[0][0]
        r1_discrete = r_coords[first_min_idx]

        # Discrete pixel error is bound by dx_i
        disc_abs_err = abs(r1_discrete - r1_analytical)
        assert disc_abs_err <= dx_i

        # Cubic spline subpixel root
        cs = CubicSpline(r_coords[:first_min_idx + 5], cut[:first_min_idx + 5])
        sol = root_scalar(
            cs.derivative(),
            bracket=[r_coords[first_min_idx - 1], r_coords[first_min_idx + 1]],
        )
        r1_spline = sol.root

        spline_rel_err_pct = abs(r1_spline - r1_analytical) / r1_analytical * 100.0
        # Spline root must be significantly more accurate than discrete quantization
        assert spline_rel_err_pct < 0.05, f"Spline error {spline_rel_err_pct}% exceeds 0.05%"
        assert abs(r1_spline - r1_analytical) < 0.1 * disc_abs_err


class TestModuleGTransferFunctionIndependentAudit:
    """Verify OTF/MTF against analytical Duffieux formula and verify autocorrelation equivalence."""

    def test_independent_duffieux_mtf_agreement(self) -> None:
        """
        Verify that numerical MTF derived from PSF matches the independent
        closed-form circular Duffieux MTF to within 0.001 across all frequencies.
        """
        r_p = 0.002
        f = 0.017
        wl = 5.50e-7
        grid = create_fft_pupil_grid(radius=r_p, samples=256, span_factor=2.5)
        p_clear = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        psf_res = compute_psf(p_clear, grid, pad_samples=512, wavelength=wl, focal_length=f)
        otf_res = compute_otf(psf_res)

        c_y = len(otf_res.fy) // 2
        c_x = len(otf_res.fx) // 2
        fx_cut = otf_res.fx[c_x:]
        mtf_num = otf_res.mtf[c_y, c_x:]

        mtf_duffieux = analytical_diffraction_limited_mtf(
            spatial_frequency_cycles_per_m=fx_cut,
            pupil_diameter=2.0 * r_p,
            focal_length=f,
            wavelength=wl,
        )

        abs_diff = np.abs(mtf_num - mtf_duffieux)
        max_err = float(np.max(abs_diff))
        rms_err = float(np.sqrt(np.mean(abs_diff ** 2)))

        assert max_err < 1.0e-3, f"Max MTF error vs Duffieux {max_err} exceeds 1e-3"
        assert rms_err < 3.0e-4, f"RMS MTF error vs Duffieux {rms_err} exceeds 3e-4"

    def test_autocorrelation_algebraic_dual_equivalence(self) -> None:
        """
        Verify that compute_otf (from PSF) and pupil_autocorrelation_otf
        are algebraically identical in the discrete domain (difference < 1e-15).
        """
        r_p = 0.002
        f = 0.017
        wl = 5.50e-7
        grid = create_fft_pupil_grid(radius=r_p, samples=128, span_factor=2.2)
        p_clear = np.where(grid.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        psf_res = compute_psf(p_clear, grid, pad_samples=128, wavelength=wl, focal_length=f)
        otf_from_psf = compute_otf(psf_res).otf

        otf_from_auto = pupil_autocorrelation_otf(p_clear, grid, focal_length=f, wavelength=wl)

        max_diff = float(np.max(np.abs(otf_from_psf - otf_from_auto)))
        assert max_diff < 1e-15, f"Dual equivalence violated: {max_diff}"


class TestModuleHSamplingConsistencyAudit:
    """Verify Nyquist sampling criteria and mathematical consistency of classifications."""

    @pytest.mark.parametrize(
        "d_max, expected_status",
        [
            (0.25, "COMPLIANT_OVERSAMPLED"),
            (1.50, "COMPLIANT_OVERSAMPLED"),
            (3.00, "COMPLIANT_ADEQUATE"),
            (3.50, "COMPLIANT_ADEQUATE"),
            (7.00, "ALIASED"),
            (11.00, "ALIASED"),
        ],
    )
    def test_static_grid_256_mathematical_consistency(
        self, d_max: float, expected_status: str
    ) -> None:
        """
        Verify consistent classification of N=256 against strict Nyquist and safety factor:
        - Ratio >= 2.0: COMPLIANT_OVERSAMPLED
        - 1.5 <= Ratio < 2.0: COMPLIANT_ADEQUATE (satisfies S=1.5)
        - 1.0 <= Ratio < 1.5: MARGINAL (satisfies strict Nyquist, but below S=1.5)
        - Ratio < 1.0: ALIASED (Nyquist violated)
        """
        r_p = 0.002
        wl = 5.50e-7
        span_factor = 1.5
        n_static = 256

        n_nyquist = compute_nyquist_grid_size(
            radius=r_p, max_dioptric_power=d_max, wavelength=wl, span_factor=span_factor
        )
        ratio = n_static / n_nyquist

        if ratio >= 2.0:
            status = "COMPLIANT_OVERSAMPLED"
        elif ratio >= 1.5:
            status = "COMPLIANT_ADEQUATE"
        elif ratio >= 1.0:
            status = "MARGINAL"
        else:
            status = "ALIASED"

        assert status == expected_status, f"D_max={d_max}: ratio={ratio:.2f}, got {status}, expected {expected_status}"
