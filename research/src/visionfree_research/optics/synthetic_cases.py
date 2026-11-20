"""
synthetic_cases.py — Canonical Synthetic Test Cases with Analytical Solutions
Part of VISIONFREE Phase 5.1: Mathematical Foundation.

Provides hand-calculated, mathematically verified synthetic ophthalmic prescriptions
and their corresponding Thibos power vectors, power matrices, and principal powers.
Used across test suites and visualization benchmarks.

Strict Scope Notice:
    These cases are synthetic illustrative benchmarks only. They are not derived from
    any human patient records, clinical trials, or Chrome extension user profiles.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

import numpy as np

from .power_vectors import PowerVector, Prescription


@dataclass(frozen=True)
class AnalyticalCase:
    """A synthetic test case with pre-calculated exact analytical values."""

    case_id: str
    description: str
    sphere: float
    cylinder: float
    axis: Optional[float]
    expected_M: float
    expected_J0: float
    expected_J45: float
    expected_B: float
    expected_F: np.ndarray
    expected_eigenvalues: Tuple[float, float]
    expected_principal_axes: Tuple[Optional[float], Optional[float]]
    equivalent_plus_cylinder: Optional[Tuple[float, float, float]] = None


def get_canonical_synthetic_cases() -> Dict[str, AnalyticalCase]:
    """
    Return dictionary of 8 canonical synthetic numerical examples.

    Cases covered:
        1. Pure spherical power (myopia)
        2. Pure cylinder at 0 deg (with-the-rule)
        3. Pure cylinder at 45 deg (oblique)
        4. Pure cylinder at 90 deg (against-the-rule)
        5. Oblique astigmatism at 30 deg
        6. Mixed sphere and cylinder at 75 deg
        7. Transposition pair (minus/plus cylinder equivalence)
        8. Zero refractive power (emmetropia)
    """
    cases: Dict[str, AnalyticalCase] = {}

    # Case 1: Pure spherical myopia (-2.00 D)
    # M = -2.00, J0 = 0, J45 = 0, B = 0
    # F = [[-2.0, 0], [0, -2.0]], eigenvalues = (-2.0, -2.0), axes = (None, None)
    cases["case1_pure_sphere"] = AnalyticalCase(
        case_id="case1_pure_sphere",
        description="Pure spherical myopia: S = -2.00 D, C = 0.00 D",
        sphere=-2.00,
        cylinder=0.00,
        axis=None,
        expected_M=-2.00,
        expected_J0=0.00,
        expected_J45=0.00,
        expected_B=0.00,
        expected_F=np.array([[-2.00, 0.00], [0.00, -2.00]], dtype=np.float64),
        expected_eigenvalues=(-2.00, -2.00),
        expected_principal_axes=(None, None),
    )

    # Case 2: Pure cylinder at 0 deg (S = 0.00, C = -1.50, alpha = 0.0 deg)
    # M = -0.75, J0 = -(-0.75)*cos(0) = +0.75, J45 = 0, B = 0.75
    # F = [[-0.75 + 0.75, 0], [0, -0.75 - 0.75]] = [[0.0, 0.0], [0.0, -1.50]]
    # Principal powers: lambda_1 = M + B = 0.0, lambda_2 = M - B = -1.50
    # Principal axes: alpha_1 = 0.0 deg, alpha_2 = 90.0 deg
    cases["case2_pure_cyl_0"] = AnalyticalCase(
        case_id="case2_pure_cyl_0",
        description="Pure cylinder at 0 deg: S = 0.00 D, C = -1.50 D, Axis = 0 deg",
        sphere=0.00,
        cylinder=-1.50,
        axis=0.0,
        expected_M=-0.75,
        expected_J0=0.75,
        expected_J45=0.00,
        expected_B=0.75,
        expected_F=np.array([[0.00, 0.00], [0.00, -1.50]], dtype=np.float64),
        expected_eigenvalues=(0.00, -1.50),
        expected_principal_axes=(0.0, 90.0),
    )

    # Case 3: Pure cylinder at 45 deg (S = 0.00, C = -2.00, alpha = 45.0 deg)
    # 2*alpha = 90 deg. cos(90) = 0, sin(90) = 1
    # M = -1.00, J0 = 0, J45 = -(-1.00)*1 = +1.00, B = 1.00
    # F = [[-1.00, +1.00], [+1.00, -1.00]]
    # Principal powers: lambda_1 = -1.0 + 1.0 = 0.0, lambda_2 = -1.0 - 1.0 = -2.00
    # Principal axes: alpha_1 = 45.0 deg, alpha_2 = 135.0 deg
    cases["case3_pure_cyl_45"] = AnalyticalCase(
        case_id="case3_pure_cyl_45",
        description="Pure cylinder at 45 deg: S = 0.00 D, C = -2.00 D, Axis = 45 deg",
        sphere=0.00,
        cylinder=-2.00,
        axis=45.0,
        expected_M=-1.00,
        expected_J0=0.00,
        expected_J45=1.00,
        expected_B=1.00,
        expected_F=np.array([[-1.00, 1.00], [1.00, -1.00]], dtype=np.float64),
        expected_eigenvalues=(0.00, -2.00),
        expected_principal_axes=(45.0, 135.0),
    )

    # Case 4: Pure cylinder at 90 deg (S = 0.00, C = -1.50, alpha = 90.0 deg)
    # 2*alpha = 180 deg. cos(180) = -1, sin(180) = 0
    # M = -0.75, J0 = -(-0.75)*(-1) = -0.75, J45 = 0, B = 0.75
    # F = [[-0.75 - 0.75, 0], [0, -0.75 + 0.75]] = [[-1.50, 0.0], [0.0, 0.0]]
    # Principal powers: lambda_1 = 0.0, lambda_2 = -1.50
    # Principal axes: alpha_1 = 90.0 deg, alpha_2 = 0.0 deg
    cases["case4_pure_cyl_90"] = AnalyticalCase(
        case_id="case4_pure_cyl_90",
        description="Pure cylinder at 90 deg: S = 0.00 D, C = -1.50 D, Axis = 90 deg",
        sphere=0.00,
        cylinder=-1.50,
        axis=90.0,
        expected_M=-0.75,
        expected_J0=-0.75,
        expected_J45=0.00,
        expected_B=0.75,
        expected_F=np.array([[-1.50, 0.00], [0.00, 0.00]], dtype=np.float64),
        expected_eigenvalues=(0.00, -1.50),
        expected_principal_axes=(90.0, 0.0),
    )

    # Case 5: Oblique astigmatism at 30 deg (S = -1.00, C = -2.00, alpha = 30.0 deg)
    # 2*alpha = 60 deg. cos(60) = 0.5, sin(60) = sqrt(3)/2 = 0.8660254037844386
    # M = -1.00 + (-1.00) = -2.00
    # J0 = -(-1.00)*0.5 = +0.50
    # J45 = -(-1.00)*(sqrt(3)/2) = +sqrt(3)/2
    # B = sqrt(0.25 + 0.75) = 1.00
    # F_00 = -2.00 + 0.50 = -1.50
    # F_11 = -2.00 - 0.50 = -2.50
    # F_01 = F_10 = sqrt(3)/2
    # Principal powers: lambda_1 = -2.00 + 1.00 = -1.00 (= S), lambda_2 = -2.00 - 1.00 = -3.00 (= S + C)
    # Principal axes: alpha_1 = 30.0 deg, alpha_2 = 120.0 deg
    sqrt3_over_2 = math.sqrt(3.0) / 2.0
    cases["case5_oblique_30"] = AnalyticalCase(
        case_id="case5_oblique_30",
        description="Oblique astigmatism: S = -1.00 D, C = -2.00 D, Axis = 30 deg",
        sphere=-1.00,
        cylinder=-2.00,
        axis=30.0,
        expected_M=-2.00,
        expected_J0=0.50,
        expected_J45=sqrt3_over_2,
        expected_B=1.00,
        expected_F=np.array([[-1.50, sqrt3_over_2], [sqrt3_over_2, -2.50]], dtype=np.float64),
        expected_eigenvalues=(-1.00, -3.00),
        expected_principal_axes=(30.0, 120.0),
        equivalent_plus_cylinder=(-3.00, +2.00, 120.0),
    )

    # Case 6: Mixed sphere and cylinder at 75 deg (S = +1.50 D, C = -3.00 D, alpha = 75.0 deg)
    # 2*alpha = 150 deg. cos(150) = -sqrt(3)/2, sin(150) = 0.5
    # M = +1.50 - 1.50 = 0.00
    # J0 = -(-1.50)*(-sqrt(3)/2) = -1.50 * sqrt(3)/2 = -0.75 * sqrt(3) ~ -1.299038105676658
    # J45 = -(-1.50)*(0.5) = +0.75
    # B = sqrt( (1.5*sqrt(3)/2)^2 + (0.75)^2 ) = sqrt( 1.6875 + 0.5625 ) = sqrt(2.25) = 1.50
    # F_00 = 0.0 + J0 = -1.299038105676658
    # F_11 = 0.0 - J0 = +1.299038105676658
    # F_01 = F_10 = 0.75
    # Principal powers: lambda_1 = M + B = +1.50 (= S), lambda_2 = M - B = -1.50 (= S + C)
    # Principal axes: alpha_1 = 75.0 deg, alpha_2 = 165.0 deg
    j0_c6 = -1.50 * sqrt3_over_2
    cases["case6_mixed_75"] = AnalyticalCase(
        case_id="case6_mixed_75",
        description="Mixed sphere and cylinder: S = +1.50 D, C = -3.00 D, Axis = 75 deg",
        sphere=1.50,
        cylinder=-3.00,
        axis=75.0,
        expected_M=0.00,
        expected_J0=j0_c6,
        expected_J45=0.75,
        expected_B=1.50,
        expected_F=np.array([[j0_c6, 0.75], [0.75, -j0_c6]], dtype=np.float64),
        expected_eigenvalues=(1.50, -1.50),
        expected_principal_axes=(75.0, 165.0),
        equivalent_plus_cylinder=(-1.50, +3.00, 165.0),
    )

    # Case 7: Transposition pair verification
    # Minus cylinder: S = -2.50 D, C = -1.00 D, alpha = 15.0 deg
    # Plus cylinder transposition: S' = -3.50 D, C' = +1.00 D, alpha' = 105.0 deg
    # 2*alpha_minus = 30 deg. cos(30) = sqrt(3)/2, sin(30) = 0.5
    # M = -2.50 - 0.50 = -3.00
    # J0 = -(-0.50)*sqrt(3)/2 = +0.25*sqrt(3) ~ 0.4330127018922193
    # J45 = -(-0.50)*0.5 = +0.25
    # B = 0.50
    j0_c7 = 0.50 * sqrt3_over_2
    cases["case7_transposition_pair"] = AnalyticalCase(
        case_id="case7_transposition_pair",
        description="Transposition pair: (-2.50/-1.00x15) <-> (-3.50/+1.00x105)",
        sphere=-2.50,
        cylinder=-1.00,
        axis=15.0,
        expected_M=-3.00,
        expected_J0=j0_c7,
        expected_J45=0.25,
        expected_B=0.50,
        expected_F=np.array([[-3.00 + j0_c7, 0.25], [0.25, -3.00 - j0_c7]], dtype=np.float64),
        expected_eigenvalues=(-2.50, -3.50),
        expected_principal_axes=(15.0, 105.0),
        equivalent_plus_cylinder=(-3.50, +1.00, 105.0),
    )

    # Case 8: Zero refractive power (Emmetropia)
    # S = 0.00, C = 0.00, axis = None
    # M = 0.0, J0 = 0.0, J45 = 0.0, B = 0.0
    # F = [[0, 0], [0, 0]]
    # Principal powers: (0.0, 0.0), principal axes: (None, None)
    cases["case8_emmetropia"] = AnalyticalCase(
        case_id="case8_emmetropia",
        description="Zero refractive power: S = 0.00 D, C = 0.00 D, Axis = None",
        sphere=0.00,
        cylinder=0.00,
        axis=None,
        expected_M=0.00,
        expected_J0=0.00,
        expected_J45=0.00,
        expected_B=0.00,
        expected_F=np.array([[0.00, 0.00], [0.00, 0.00]], dtype=np.float64),
        expected_eigenvalues=(0.00, 0.00),
        expected_principal_axes=(None, None),
    )

    return cases
