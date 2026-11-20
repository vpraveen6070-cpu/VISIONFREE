"""
test_phase51_power_vectors.py — Unit Tests for Module A, B, and C
Part of VISIONFREE Phase 5.1 Test Suite.

Tests:
- Analytical correctness against 8 canonical synthetic benchmarks
- Input validation (NaN, inf, invalid axis ranges)
- Cylinder axis periodicity (0 deg == 180 deg, alpha == alpha + 180 deg)
- Missing axis handling (allowed for C=0, rejected for C!=0)
- Prescription transposition invariance (plus <-> minus cylinder)
- Round-trip reconstruction (Prescription -> PowerVector -> Prescription)
- Power matrix symmetry, trace, determinant, and eigenvalue invariants
- Meridional power formula F(theta) consistency with e(theta)^T * F * e(theta)
- Zero cylinder handling with undefined/null axis
"""

from __future__ import annotations

import math
import numpy as np
import pytest

from visionfree_research.optics.power_vectors import (
    DEFAULT_TOLERANCE,
    PowerVector,
    Prescription,
    construct_power_matrix,
    decompose_power_matrix,
    meridional_power,
    power_matrix_meridional_power,
    power_vector_to_prescription,
    prescription_to_power_vector,
)
from visionfree_research.optics.synthetic_cases import get_canonical_synthetic_cases


class TestModuleAPowerVectors:
    """Tests for Module A: Power Vector Conversion."""

    def test_canonical_cases_exact_analytical_match(self) -> None:
        """Verify all 8 canonical synthetic benchmarks against hand-calculated values."""
        cases = get_canonical_synthetic_cases()
        assert len(cases) == 8

        for case_id, case in cases.items():
            pv = prescription_to_power_vector(
                sphere=case.sphere,
                cylinder=case.cylinder,
                axis=case.axis,
                tolerance=1e-9,
            )

            # Check Thibos power vector components
            assert math.isclose(pv.M, case.expected_M, abs_tol=1e-9), f"Failed M in {case_id}"
            assert math.isclose(pv.J0, case.expected_J0, abs_tol=1e-9), f"Failed J0 in {case_id}"
            assert math.isclose(pv.J45, case.expected_J45, abs_tol=1e-9), f"Failed J45 in {case_id}"
            assert math.isclose(pv.astigmatic_magnitude, case.expected_B, abs_tol=1e-9), f"Failed B in {case_id}"

            # Check power matrix
            f_mat = pv.to_matrix()
            assert np.allclose(f_mat, case.expected_F, atol=1e-9), f"Failed F matrix in {case_id}"

            # Check principal powers (eigenvalues)
            p1, p2 = pv.principal_powers()
            exp_p1, exp_p2 = case.expected_eigenvalues
            assert math.isclose(p1, exp_p1, abs_tol=1e-9), f"Failed lambda_1 in {case_id}"
            assert math.isclose(p2, exp_p2, abs_tol=1e-9), f"Failed lambda_2 in {case_id}"

            # Check principal axes
            ax1, ax2 = pv.principal_axes()
            exp_ax1, exp_ax2 = case.expected_principal_axes
            if exp_ax1 is None:
                assert ax1 is None and ax2 is None, f"Expected None axes for {case_id}"
            else:
                assert ax1 is not None and ax2 is not None
                assert math.isclose(ax1, exp_ax1, abs_tol=1e-9), f"Failed axis_1 in {case_id}"
                assert math.isclose(ax2, exp_ax2, abs_tol=1e-9), f"Failed axis_2 in {case_id}"

    def test_axis_periodicity_and_normalization(self) -> None:
        """Verify that axis = 0 deg and axis = 180 deg produce identical power vectors."""
        pv_0 = prescription_to_power_vector(sphere=-1.0, cylinder=-2.0, axis=0.0)
        pv_180 = prescription_to_power_vector(sphere=-1.0, cylinder=-2.0, axis=180.0)

        assert math.isclose(pv_0.M, pv_180.M, abs_tol=1e-12)
        assert math.isclose(pv_0.J0, pv_180.J0, abs_tol=1e-12)
        assert math.isclose(pv_0.J45, pv_180.J45, abs_tol=1e-12)
        assert np.allclose(pv_0.to_matrix(), pv_180.to_matrix(), atol=1e-12)

    def test_missing_axis_when_cylinder_is_zero(self) -> None:
        """Verify missing axis is cleanly accepted when cylinder is zero."""
        pv1 = prescription_to_power_vector(sphere=-3.5, cylinder=0.0, axis=None)
        pv2 = prescription_to_power_vector(sphere=-3.5, cylinder=0.0, axis=0.0)
        pv3 = prescription_to_power_vector(sphere=-3.5, cylinder=0.0, axis=90.0)

        assert pv1.M == -3.5 and pv1.J0 == 0.0 and pv1.J45 == 0.0
        assert pv1 == pv2 == pv3

        # Reconstructed prescription must have axis=None
        p = pv1.to_prescription()
        assert p.sphere == -3.5
        assert p.cylinder == 0.0
        assert p.axis is None

    def test_missing_axis_when_cylinder_nonzero_raises(self) -> None:
        """Verify that omitting axis for non-zero cylinder raises ValueError."""
        with pytest.raises(ValueError, match="requires a defined axis"):
            prescription_to_power_vector(sphere=-2.0, cylinder=-1.0, axis=None)

        with pytest.raises(ValueError, match="requires a defined axis"):
            Prescription(sphere=-2.0, cylinder=-1.0, axis=None)

    def test_invalid_axis_range_rejection(self) -> None:
        """Verify axis outside [0, 180] deg is rejected."""
        with pytest.raises(ValueError, match="must lie in \\[0, 180\\]"):
            prescription_to_power_vector(sphere=0.0, cylinder=-1.0, axis=-0.1)

        with pytest.raises(ValueError, match="must lie in \\[0, 180\\]"):
            prescription_to_power_vector(sphere=0.0, cylinder=-1.0, axis=180.1)

    def test_nan_and_inf_rejection(self) -> None:
        """Verify NaN and infinity are rejected across all numerical parameters."""
        for bad_val in [float("nan"), float("inf"), float("-inf")]:
            with pytest.raises(ValueError, match="must be finite"):
                prescription_to_power_vector(sphere=bad_val, cylinder=-1.0, axis=45.0)

            with pytest.raises(ValueError, match="must be finite"):
                prescription_to_power_vector(sphere=-1.0, cylinder=bad_val, axis=45.0)

            with pytest.raises(ValueError, match="must be finite"):
                prescription_to_power_vector(sphere=-1.0, cylinder=-1.0, axis=bad_val)

            with pytest.raises(ValueError, match="must be finite"):
                PowerVector(M=bad_val, J0=0.0, J45=0.0)


class TestModuleBMeridionalPowerAndMatrix:
    """Tests for Module B: Meridional Power and Power Matrix."""

    def test_matrix_quadratic_form_matches_fourier_meridional_power(self) -> None:
        """
        Verify that F(theta) = e(theta)^T * F * e(theta)
        matches F(theta) = M + J0*cos(2*theta) + J45*sin(2*theta)
        across a fine angular meridian grid from 0 to 360 deg.
        """
        pv = PowerVector(M=-2.0, J0=0.75, J45=-1.25)
        f_mat = pv.to_matrix()

        theta_angles = np.linspace(0.0, 360.0, 73, endpoint=True)

        for theta in theta_angles:
            f_fourier = pv.meridional_power(theta)
            f_quadratic = power_matrix_meridional_power(f_mat, theta)

            assert math.isclose(f_fourier, f_quadratic, abs_tol=1e-12), (
                f"Mismatch at theta={theta}: fourier={f_fourier}, quadratic={f_quadratic}"
            )

    def test_principal_meridians_match_sphere_and_cylinder(self) -> None:
        """
        For a minus-cylinder prescription (S, C, alpha), verify:
        - Power along meridian theta = alpha is exactly S.
        - Power along meridian theta = alpha + 90 deg is exactly S + C.
        """
        s = -1.75
        c = -2.50
        alpha = 35.0

        pv = prescription_to_power_vector(sphere=s, cylinder=c, axis=alpha)

        f_axis = pv.meridional_power(alpha)
        f_perp = pv.meridional_power(alpha + 90.0)

        assert math.isclose(f_axis, s, abs_tol=1e-12), f"Power at axis should be {s}, got {f_axis}"
        assert math.isclose(f_perp, s + c, abs_tol=1e-12), f"Power at axis+90 should be {s+c}, got {f_perp}"

    def test_matrix_eigenvalue_and_trace_invariants(self) -> None:
        """
        Verify fundamental linear algebraic invariants of the 2D power matrix:
        - Trace(F) == 2 * M
        - Det(F) == M^2 - B^2
        - Matrix eigenvalues match lambda_1 = M + B and lambda_2 = M - B
        """
        pv = PowerVector(M=+0.50, J0=-1.25, J45=+0.80)
        f_mat = pv.to_matrix()

        # Matrix symmetry
        assert np.allclose(f_mat, f_mat.T, atol=1e-14)

        # Trace
        assert math.isclose(np.trace(f_mat), 2.0 * pv.M, abs_tol=1e-14)

        # Determinant
        b_sq = pv.J0**2 + pv.J45**2
        expected_det = pv.M**2 - b_sq
        assert math.isclose(np.linalg.det(f_mat), expected_det, abs_tol=1e-14)

        # NumPy numerical eigenvalues vs analytical principal powers
        numerical_eigs = np.sort(np.linalg.eigvalsh(f_mat))[::-1]  # descending
        analytical_eigs = np.array(pv.principal_powers())  # (M+B, M-B)
        assert np.allclose(numerical_eigs, analytical_eigs, atol=1e-12)

    def test_decompose_power_matrix_round_trip(self) -> None:
        """Verify decompose_power_matrix extracts original vector and eigenvalues."""
        pv_orig = PowerVector(M=-3.25, J0=1.10, J45=-0.65)
        f_mat = pv_orig.to_matrix()

        pv_extracted, eigenvalues, axes = decompose_power_matrix(f_mat)

        assert math.isclose(pv_extracted.M, pv_orig.M, abs_tol=1e-14)
        assert math.isclose(pv_extracted.J0, pv_orig.J0, abs_tol=1e-14)
        assert math.isclose(pv_extracted.J45, pv_orig.J45, abs_tol=1e-14)
        assert np.allclose(eigenvalues, pv_orig.principal_powers(), atol=1e-14)


class TestModuleCInvariantsAndTransposition:
    """Tests for Module C: Mathematical Invariants & Prescription Transposition."""

    def test_pure_sphere_invariants(self) -> None:
        """For C = 0: M = S, J0 = 0, J45 = 0, F = S * Identity."""
        sphere_val = -4.25
        pv = prescription_to_power_vector(sphere=sphere_val, cylinder=0.0)

        assert pv.M == sphere_val
        assert pv.J0 == 0.0
        assert pv.J45 == 0.0
        assert pv.astigmatic_magnitude == 0.0

        expected_matrix = sphere_val * np.eye(2, dtype=np.float64)
        assert np.allclose(pv.to_matrix(), expected_matrix, atol=1e-14)

    @pytest.mark.parametrize(
        "s_minus, c_minus, a_minus",
        [
            (-1.00, -2.00, 30.0),
            (+1.50, -3.00, 75.0),
            (-2.50, -1.00, 15.0),
            (0.00, -1.50, 0.0),
            (0.00, -1.50, 90.0),
            (-0.50, -0.75, 135.0),
        ],
    )
    def test_prescription_transposition_power_vector_invariance(
        self, s_minus: float, c_minus: float, a_minus: float
    ) -> None:
        """
        Verify that a minus-cylinder prescription and its plus-cylinder transposed
        counterpart map to the EXACT same Thibos power vector and power matrix.
        """
        rx_minus = Prescription(sphere=s_minus, cylinder=c_minus, axis=a_minus)
        rx_plus = rx_minus.transpose()

        # Confirm transposition produced plus cylinder
        assert rx_plus.cylinder > 0, f"Expected positive cylinder, got {rx_plus.cylinder}"

        pv_minus = rx_minus.to_power_vector()
        pv_plus = rx_plus.to_power_vector()

        assert math.isclose(pv_minus.M, pv_plus.M, abs_tol=1e-12)
        assert math.isclose(pv_minus.J0, pv_plus.J0, abs_tol=1e-12)
        assert math.isclose(pv_minus.J45, pv_plus.J45, abs_tol=1e-12)
        assert np.allclose(pv_minus.to_matrix(), pv_plus.to_matrix(), atol=1e-12)

    def test_round_trip_minus_cylinder_reconstruction(self) -> None:
        """Verify Prescription -> PowerVector -> Prescription reproduces original inputs."""
        test_rxs = [
            Prescription(sphere=-2.0, cylinder=-1.5, axis=40.0),
            Prescription(sphere=+1.0, cylinder=-2.0, axis=90.0),
            Prescription(sphere=0.0, cylinder=-0.5, axis=0.0),
            Prescription(sphere=-3.0, cylinder=-2.5, axis=165.0),
            Prescription(sphere=-1.25, cylinder=0.0, axis=None),
            Prescription(sphere=0.0, cylinder=0.0, axis=None),
        ]

        for orig in test_rxs:
            pv = orig.to_power_vector()
            reconstructed = pv.to_prescription()

            assert math.isclose(reconstructed.sphere, orig.sphere, abs_tol=1e-12)
            assert math.isclose(reconstructed.cylinder, orig.cylinder, abs_tol=1e-12)

            if orig.axis is None:
                assert reconstructed.axis is None
            else:
                assert reconstructed.axis is not None
                assert math.isclose(reconstructed.axis, orig.normalized_axis, abs_tol=1e-12)

    def test_direct_positive_cylinder_thibos_and_reconstruction(self) -> None:
        """
        Audit test: Independently verify positive cylinder passed directly to
        prescription_to_power_vector and reconstructed to canonical minus cylinder.
        Prescription: S = -3.00 D, C = +2.00 D, Axis = 120 deg
        Thibos analytical:
            M = -3.00 + 1.00 = -2.00 D
            2*alpha = 240 deg => cos(240) = -0.5, sin(240) = -sqrt(3)/2
            J0 = -(+1.00)*(-0.5) = +0.50 D
            J45 = -(+1.00)*(-sqrt(3)/2) = +sqrt(3)/2 ~ 0.8660254 D
            B = 1.00 D
        Reconstructed canonical minus cylinder:
            C_minus = -2*B = -2.00 D
            S_minus = M + B = -1.00 D
            alpha_minus = 30 deg
        """
        sqrt3_2 = math.sqrt(3.0) / 2.0
        pv_pos = prescription_to_power_vector(sphere=-3.00, cylinder=+2.00, axis=120.0)

        assert math.isclose(pv_pos.M, -2.00, abs_tol=1e-12)
        assert math.isclose(pv_pos.J0, 0.50, abs_tol=1e-12)
        assert math.isclose(pv_pos.J45, sqrt3_2, abs_tol=1e-12)
        assert math.isclose(pv_pos.astigmatic_magnitude, 1.00, abs_tol=1e-12)

        # Eigenvalues must match principal powers (-1.00 D, -3.00 D)
        p1, p2 = pv_pos.principal_powers()
        assert math.isclose(p1, -1.00, abs_tol=1e-12)
        assert math.isclose(p2, -3.00, abs_tol=1e-12)

        # Reconstruction to canonical minus cylinder
        rx_recon = pv_pos.to_prescription()
        assert math.isclose(rx_recon.sphere, -1.00, abs_tol=1e-12)
        assert math.isclose(rx_recon.cylinder, -2.00, abs_tol=1e-12)
        assert math.isclose(rx_recon.axis, 30.0, abs_tol=1e-12)
