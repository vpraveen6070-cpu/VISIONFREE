"""
test_phase51_wavefront.py — Unit Tests for Module D: Quadratic Wavefront & OPD Model
Part of VISIONFREE Phase 5.1 Test Suite.

Tests:
- Dimensional consistency and physical units (W in meters)
- Zero wavefront condition at pupil center W(0, 0) == 0
- Quadratic radial scaling property W(k*x, k*y) == k^2 * W(x, y)
- Astigmatic cross-term isolation (J45 pure shear term)
- Circular symmetry of pure spherical defocus
- Sign convention parameter behavior (sigma = +1.0 vs -1.0)
- Classical Seidel coefficients W20 and W22
- Input validation (NaN, inf, zero sigma, matrix shape/symmetry)
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from visionfree_research.optics.power_vectors import PowerVector
from visionfree_research.optics.wavefront import (
    DEFAULT_SIGMA,
    quadratic_wavefront,
    seidel_wavefront_coefficients,
)


class TestModuleDWavefront:
    """Tests for Module D: Quadratic Wavefront and OPD Model."""

    def test_dimensional_units_and_hand_calculated_opd(self) -> None:
        """
        Verify exact hand-calculated optical path difference:
        For pure myopia M = -2.00 D (S = -2.00, C = 0.00), sigma = +1.0:
        At pupil margin r = 2.0 mm (0.002 m):
            W = 0.5 * sigma * M * r^2
            W = 0.5 * (+1.0) * (-2.00 m^-1) * (0.002 m)^2
            W = -1.0 * 4.0e-6 m = -4.0e-6 m = -4.0 micrometers.
        """
        pv = PowerVector(M=-2.00, J0=0.00, J45=0.00)
        r_p = 0.002  # 2 mm

        # Margin points along axes
        w_right = quadratic_wavefront(pv, x=r_p, y=0.0, sigma=1.0)
        w_top = quadratic_wavefront(pv, x=0.0, y=r_p, sigma=1.0)
        w_diag = quadratic_wavefront(pv, x=r_p / math.sqrt(2.0), y=r_p / math.sqrt(2.0), sigma=1.0)

        expected_w = -4.0e-6  # -4.0 micrometers
        assert math.isclose(w_right, expected_w, abs_tol=1e-15)
        assert math.isclose(w_top, expected_w, abs_tol=1e-15)
        assert math.isclose(w_diag, expected_w, abs_tol=1e-15)

    def test_zero_wavefront_at_pupil_center(self) -> None:
        """Verify W(0, 0) == 0.0 for arbitrary power vectors and matrices."""
        test_vectors = [
            PowerVector(M=-3.0, J0=1.5, J45=-0.8),
            PowerVector(M=0.0, J0=0.0, J45=0.0),
            PowerVector(M=+2.5, J0=-1.0, J45=2.0),
        ]

        for pv in test_vectors:
            w_center = quadratic_wavefront(pv, x=0.0, y=0.0)
            assert w_center == 0.0

            # Also verify via power matrix
            w_matrix_center = quadratic_wavefront(pv.to_matrix(), x=0.0, y=0.0)
            assert w_matrix_center == 0.0

    def test_quadratic_scaling_property(self) -> None:
        """
        Verify quadratic scaling: W(k*x, k*y) = k^2 * W(x, y).
        Tested for k = 2.0, 0.5, and -1.0.
        """
        pv = PowerVector(M=-1.50, J0=0.75, J45=-0.50)
        x = 0.0012
        y = -0.0008

        w_base = quadratic_wavefront(pv, x=x, y=y)

        for k in [2.0, 0.5, -1.0, 3.5]:
            w_scaled = quadratic_wavefront(pv, x=k * x, y=k * y)
            expected_scaled = (k ** 2) * w_base
            assert math.isclose(w_scaled, expected_scaled, rel_tol=1e-12)

    def test_pure_astigmatic_cross_term(self) -> None:
        """
        Verify that for pure J45 (M=0, J0=0), the wavefront is a pure hyperbolic saddle:
            W(x, y) = sigma * J45 * x * y
        """
        j45_val = 1.50
        pv = PowerVector(M=0.0, J0=0.0, J45=j45_val)

        x = 0.001
        y = 0.001
        w_pp = quadratic_wavefront(pv, x=x, y=y, sigma=1.0)
        assert math.isclose(w_pp, j45_val * x * y, abs_tol=1e-15)

        # Opposite sign in diagonal quadrant
        w_pn = quadratic_wavefront(pv, x=x, y=-y, sigma=1.0)
        assert math.isclose(w_pn, -j45_val * x * y, abs_tol=1e-15)

        # On the principal coordinate axes x=0 or y=0, W must be exactly 0
        assert quadratic_wavefront(pv, x=x, y=0.0) == 0.0
        assert quadratic_wavefront(pv, x=0.0, y=y) == 0.0

    def test_pure_spherical_circular_symmetry(self) -> None:
        """Verify that pure defocus M produces rotational symmetry across all azimuths."""
        pv = PowerVector(M=-2.50, J0=0.0, J45=0.0)
        r = 0.0015

        angles = np.linspace(0.0, 2.0 * math.pi, 36, endpoint=False)
        w_values = [
            quadratic_wavefront(pv, x=r * math.cos(theta), y=r * math.sin(theta))
            for theta in angles
        ]

        expected_w = 0.5 * (-2.50) * (r ** 2)
        for w_val in w_values:
            assert math.isclose(w_val, expected_w, abs_tol=1e-15)

    def test_sign_convention_parameter(self) -> None:
        """
        Verify that sigma parameter reverses sign exactly:
            W(x, y; sigma=-1.0) == -W(x, y; sigma=+1.0)
        """
        pv = PowerVector(M=+1.75, J0=-0.80, J45=0.60)
        x_grid = np.linspace(-0.002, 0.002, 25)
        y_grid = np.linspace(-0.002, 0.002, 25)
        xg, yg = np.meshgrid(x_grid, y_grid)

        w_plus = quadratic_wavefront(pv, xg, yg, sigma=+1.0)
        w_minus = quadratic_wavefront(pv, xg, yg, sigma=-1.0)

        assert np.allclose(w_plus, -w_minus, atol=1e-15)

    def test_seidel_coefficients_analytical(self) -> None:
        """
        Verify Seidel coefficients against analytical formulas:
            W20 = (sigma / 2) * r_p^2 * M
            W22 = (sigma / 2) * r_p^2 * B = (sigma / 4) * r_p^2 * |CYL|
        """
        # S = -1.00 D, C = -2.00 D => M = -2.00 D, B = 1.00 D
        pv = PowerVector(M=-2.00, J0=0.60, J45=0.80)  # B = sqrt(0.36 + 0.64) = 1.00
        r_p = 0.0025  # 2.5 mm

        coeffs = seidel_wavefront_coefficients(pv, pupil_radius=r_p, sigma=1.0)

        expected_w20 = 0.5 * (r_p ** 2) * (-2.00)  # -6.25e-6 m
        expected_w22 = 0.5 * (r_p ** 2) * (1.00)   # +3.125e-6 m

        assert math.isclose(coeffs["W20_meters"], expected_w20, abs_tol=1e-15)
        assert math.isclose(coeffs["W22_meters"], expected_w22, abs_tol=1e-15)

    def test_oblique_astigmatism_opd_at_principal_coordinates(self) -> None:
        """
        Audit test: Independently verify OPD values at principal meridian coordinates
        for oblique astigmatism (Case 5: S = -1.00 D, C = -2.00 D, alpha = 30 deg).
        Analytical invariant:
            At r = r_p along meridian theta: W(r_p, theta) = (sigma / 2) * r_p^2 * F(theta)
            - Along theta = alpha = 30 deg: F(30 deg) = S = -1.00 D
              W(r_p, 30 deg) = 0.5 * (+1.0) * (0.002)^2 * (-1.00) = -2.0e-6 m
            - Along theta = alpha + 90 deg = 120 deg: F(120 deg) = S + C = -3.00 D
              W(r_p, 120 deg) = 0.5 * (+1.0) * (0.002)^2 * (-3.00) = -6.0e-6 m
            - Along Circle of Least Confusion (theta = 75 deg): F(75 deg) = M = -2.00 D
              W(r_p, 75 deg) = 0.5 * (+1.0) * (0.002)^2 * (-2.00) = -4.0e-6 m
        """
        r_p = 0.002  # 2 mm
        sqrt3_2 = math.sqrt(3.0) / 2.0
        pv = PowerVector(M=-2.00, J0=0.50, J45=sqrt3_2)

        # 1. Principal meridian at 30 deg
        x_30 = r_p * math.cos(math.radians(30.0))
        y_30 = r_p * math.sin(math.radians(30.0))
        w_30 = quadratic_wavefront(pv, x=x_30, y=y_30, sigma=1.0)
        expected_w_30 = 0.5 * (r_p ** 2) * (-1.00)  # -2.0e-6 m
        assert math.isclose(w_30, expected_w_30, abs_tol=1e-15)

        # 2. Orthogonal principal meridian at 120 deg
        x_120 = r_p * math.cos(math.radians(120.0))
        y_120 = r_p * math.sin(math.radians(120.0))
        w_120 = quadratic_wavefront(pv, x=x_120, y=y_120, sigma=1.0)
        expected_w_120 = 0.5 * (r_p ** 2) * (-3.00)  # -6.0e-6 m
        assert math.isclose(w_120, expected_w_120, abs_tol=1e-15)

        # 3. Intermediate Circle of Least Confusion at 75 deg (45 deg away from axis)
        x_75 = r_p * math.cos(math.radians(75.0))
        y_75 = r_p * math.sin(math.radians(75.0))
        w_75 = quadratic_wavefront(pv, x=x_75, y=y_75, sigma=1.0)
        expected_w_75 = 0.5 * (r_p ** 2) * (-2.00)  # -4.0e-6 m
        assert math.isclose(w_75, expected_w_75, abs_tol=1e-15)

    def test_input_validation(self) -> None:
        """Verify invalid inputs raise appropriate exceptions."""
        pv = PowerVector(M=-1.0, J0=0.0, J45=0.0)

        # Zero sigma is forbidden
        with pytest.raises(ValueError, match="cannot be zero"):
            quadratic_wavefront(pv, x=0.001, y=0.001, sigma=0.0)

        # NaN coordinates
        with pytest.raises(ValueError, match="non-finite or NaN"):
            quadratic_wavefront(pv, x=float("nan"), y=0.001)

        # Asymmetric power matrix
        asym_mat = np.array([[1.0, 2.0], [3.0, 4.0]])
        with pytest.raises(ValueError, match="must be symmetric"):
            quadratic_wavefront(asym_mat, x=0.001, y=0.001)

        # Invalid radius in seidel
        with pytest.raises(ValueError, match="strictly positive"):
            seidel_wavefront_coefficients(pv, pupil_radius=-0.002)
