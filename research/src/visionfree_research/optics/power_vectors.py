"""
power_vectors.py — Ophthalmic Power Vector & Refractive Matrix Engine
Part of VISIONFREE Phase 5.1: Mathematical Foundation.

Provides:
- Thibos et al. (1997) power-vector decomposition (S, C, alpha -> M, J0, J45).
- Symmetric 2D dioptric power matrix formulation and eigenvalue analysis.
- Meridional refractive power computation along arbitrary angles.
- Principal meridian identification and astigmatic vector magnitude.
- Reconstruction to canonical minus-cylinder clinical notation.
- Exact ophthalmic transposition (plus-cylinder <-> minus-cylinder).

Reference:
    Thibos LN, Wheeler W, Horner D. (1997). "Power Vectors: An Application
    of Fourier Analysis to the Description and Statistical Analysis of
    Refractive Error." Optometry and Vision Science, 74(6), 367-375.
    DOI: 10.1002/j.1538-9235.1997.tb04707.x
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Tuple, Union

import numpy as np

# Default numerical threshold for dioptric equivalence and zero-cylinder detection
DEFAULT_TOLERANCE: float = 1e-9


def _validate_finite(value: float, name: str) -> None:
    """Validate that a numerical value is finite (neither NaN nor infinite)."""
    if not isinstance(value, (int, float, np.floating, np.integer)):
        raise TypeError(f"Parameter '{name}' must be numeric, got {type(value).__name__}")
    if not math.isfinite(float(value)):
        raise ValueError(f"Parameter '{name}' must be finite, got {value}")


@dataclass(frozen=True)
class Prescription:
    """
    Ophthalmic sphero-cylindrical prescription representation.

    Attributes:
        sphere (float): Spherical power in diopters (D).
        cylinder (float): Cylindrical power in diopters (D).
        axis (Optional[float]): Cylinder axis in degrees [0, 180].
            Treated as None or ignored when abs(cylinder) < tolerance.
            Axes of 0.0 deg and 180.0 deg are physically and optically equivalent.
    """

    sphere: float
    cylinder: float
    axis: Optional[float] = None
    tolerance: float = DEFAULT_TOLERANCE

    def __post_init__(self) -> None:
        _validate_finite(self.sphere, "sphere")
        _validate_finite(self.cylinder, "cylinder")
        _validate_finite(self.tolerance, "tolerance")

        if self.tolerance <= 0:
            raise ValueError(f"Tolerance must be strictly positive, got {self.tolerance}")

        is_cylindrical = abs(self.cylinder) >= self.tolerance

        if is_cylindrical:
            if self.axis is None:
                raise ValueError(
                    f"Non-zero cylinder ({self.cylinder:+.4f} D) requires a defined axis in [0, 180] deg."
                )
            _validate_finite(self.axis, "axis")
            if not (0.0 <= self.axis <= 180.0):
                raise ValueError(
                    f"Cylinder axis must lie in [0, 180] deg, got {self.axis} deg."
                )
        else:
            if self.axis is not None:
                _validate_finite(self.axis, "axis")
                if not (0.0 <= self.axis <= 180.0):
                    raise ValueError(
                        f"Cylinder axis must lie in [0, 180] deg, got {self.axis} deg."
                    )

    @property
    def is_astigmatic(self) -> bool:
        """Return True if cylinder magnitude meets or exceeds tolerance threshold."""
        return abs(self.cylinder) >= self.tolerance

    @property
    def normalized_axis(self) -> Optional[float]:
        """
        Return the canonical axis in [0, 180) degrees.
        If axis is 180 deg, it is normalized to 0 deg.
        Returns None for purely spherical prescriptions.
        """
        if not self.is_astigmatic:
            return None
        assert self.axis is not None
        axis_val = float(self.axis)
        if abs(axis_val - 180.0) < self.tolerance or axis_val < self.tolerance:
            return 0.0
        return axis_val

    def transpose(self) -> Prescription:
        """
        Perform standard ophthalmic prescription transposition between
        plus-cylinder and minus-cylinder conventions.

        Formulas:
            S' = S + C
            C' = -C
            alpha' = (alpha + 90 deg) mod 180 deg
        """
        if not self.is_astigmatic:
            return Prescription(
                sphere=float(self.sphere),
                cylinder=0.0,
                axis=None,
                tolerance=self.tolerance,
            )

        assert self.axis is not None
        s_trans = float(self.sphere + self.cylinder)
        c_trans = float(-self.cylinder)
        raw_axis = (float(self.axis) + 90.0) % 180.0
        if abs(raw_axis - 180.0) < self.tolerance or raw_axis < self.tolerance:
            axis_trans = 0.0
        else:
            axis_trans = raw_axis

        return Prescription(
            sphere=s_trans,
            cylinder=c_trans,
            axis=axis_trans,
            tolerance=self.tolerance,
        )

    def to_power_vector(self) -> PowerVector:
        """Convert this prescription to a Thibos PowerVector."""
        return prescription_to_power_vector(
            sphere=self.sphere,
            cylinder=self.cylinder,
            axis=self.axis,
            tolerance=self.tolerance,
        )


@dataclass(frozen=True)
class PowerVector:
    """
    Thibos 3D orthonormal power-vector representation of refractive error.

    Decomposes an ophthalmic prescription into:
        M (float): Spherical equivalent power (D). M = S + C/2
        J0 (float): Horizontal/vertical Jackson cross-cylinder power (D) at 0/90 deg.
        J45 (float): Oblique Jackson cross-cylinder power (D) at 45/135 deg.

    Reference:
        Thibos et al. (1997), Optom Vis Sci 74(6):367-375.
    """

    M: float
    J0: float
    J45: float
    tolerance: float = DEFAULT_TOLERANCE

    def __post_init__(self) -> None:
        _validate_finite(self.M, "M")
        _validate_finite(self.J0, "J0")
        _validate_finite(self.J45, "J45")
        _validate_finite(self.tolerance, "tolerance")

        if self.tolerance <= 0:
            raise ValueError(f"Tolerance must be strictly positive, got {self.tolerance}")

    @property
    def astigmatic_magnitude(self) -> float:
        """
        Overall astigmatic vector magnitude B (diopters).
        B = sqrt(J0^2 + J45^2) = |CYL| / 2.
        """
        return float(math.hypot(self.J0, self.J45))

    @property
    def power_length(self) -> float:
        """
        Total dioptric vector length in 3D power space (diopters).
        ||v|| = sqrt(M^2 + J0^2 + J45^2).
        """
        return float(math.sqrt(self.M * self.M + self.J0 * self.J0 + self.J45 * self.J45))

    @property
    def is_astigmatic(self) -> bool:
        """Return True if astigmatic vector magnitude B >= tolerance."""
        return self.astigmatic_magnitude >= self.tolerance

    def as_array(self) -> np.ndarray:
        """Return 1D NumPy array [M, J0, J45] of dtype float64."""
        return np.array([self.M, self.J0, self.J45], dtype=np.float64)

    def to_matrix(self) -> np.ndarray:
        """
        Construct the symmetric 2D refractive power matrix F (diopters):
            F = [[M + J0,   J45  ],
                 [  J45 , M - J0 ]]
        """
        return construct_power_matrix(self)

    def meridional_power(self, theta_deg: Union[float, np.ndarray]) -> Union[float, np.ndarray]:
        """
        Compute refractive power along arbitrary meridian angle theta (in degrees):
            F(theta) = M + J0 * cos(2*theta) + J45 * sin(2*theta)
        """
        return meridional_power(self.M, self.J0, self.J45, theta_deg)

    def principal_powers(self) -> Tuple[float, float]:
        """
        Return the analytical principal meridional powers (lambda_1, lambda_2) in diopters.

        Eigenvalues of F:
            lambda_1 = M + B = M + sqrt(J0^2 + J45^2)
            lambda_2 = M - B = M - sqrt(J0^2 + J45^2)

        In canonical minus-cylinder notation:
            lambda_1 = Sphere
            lambda_2 = Sphere + Cylinder
        """
        b = self.astigmatic_magnitude
        return (float(self.M + b), float(self.M - b))

    def principal_axes(self) -> Tuple[Optional[float], Optional[float]]:
        """
        Return principal meridian orientations (alpha_1, alpha_2) in degrees [0, 180).
        alpha_1 corresponds to the principal power lambda_1 (Sphere in minus-cylinder).
        alpha_2 corresponds to lambda_2 (Sphere + Cylinder, at alpha_1 + 90 deg).

        For purely spherical prescriptions (B < tolerance), the cylinder axis is
        physically undefined, returning (None, None).
        """
        b = self.astigmatic_magnitude
        if b < self.tolerance:
            return (None, None)

        # In minus cylinder: J0 = B * cos(2*alpha), J45 = B * sin(2*alpha)
        # 2*alpha = atan2(J45, J0)
        two_alpha_rad = math.atan2(self.J45, self.J0)
        two_alpha_deg = math.degrees(two_alpha_rad) % 360.0
        alpha_1 = (two_alpha_deg / 2.0) % 180.0
        if abs(alpha_1 - 180.0) < self.tolerance or alpha_1 < self.tolerance:
            alpha_1 = 0.0

        alpha_2 = (alpha_1 + 90.0) % 180.0
        if abs(alpha_2 - 180.0) < self.tolerance or alpha_2 < self.tolerance:
            alpha_2 = 0.0

        return (float(alpha_1), float(alpha_2))

    def to_prescription(self) -> Prescription:
        """
        Reconstruct the canonical minus-cylinder prescription (S, C, alpha).

        Note: Mathematical prescription reconstruction is a linear algebraic operation
        and does NOT constitute subjective or clinical refraction.
        """
        return power_vector_to_prescription(self, tolerance=self.tolerance)


def prescription_to_power_vector(
    sphere: float,
    cylinder: float,
    axis: Optional[float] = None,
    tolerance: float = DEFAULT_TOLERANCE,
) -> PowerVector:
    """
    Convert a sphero-cylindrical prescription to a Thibos PowerVector.

    Equations:
        M = S + C / 2
        J0 = -(C / 2) * cos(2 * alpha_rad)
        J45 = -(C / 2) * sin(2 * alpha_rad)

    Args:
        sphere: Spherical power in diopters.
        cylinder: Cylindrical power in diopters.
        axis: Cylinder axis in degrees [0, 180]. May be None if abs(cylinder) < tolerance.
        tolerance: Numerical threshold for astigmatism detection.

    Returns:
        PowerVector instance with (M, J0, J45).
    """
    _validate_finite(sphere, "sphere")
    _validate_finite(cylinder, "cylinder")
    _validate_finite(tolerance, "tolerance")

    s = float(sphere)
    c = float(cylinder)

    if abs(c) < tolerance:
        # Pure spherical power: J0 = 0, J45 = 0, axis unconstrained
        if axis is not None:
            _validate_finite(axis, "axis")
            if not (0.0 <= axis <= 180.0):
                raise ValueError(f"Cylinder axis must lie in [0, 180] deg, got {axis} deg.")
        return PowerVector(M=s, J0=0.0, J45=0.0, tolerance=tolerance)

    if axis is None:
        raise ValueError(
            f"Non-zero cylinder ({c:+.4f} D) requires a defined axis in [0, 180] deg."
        )

    _validate_finite(axis, "axis")
    ax = float(axis)
    if not (0.0 <= ax <= 180.0):
        raise ValueError(f"Cylinder axis must lie in [0, 180] deg, got {ax} deg.")

    # Periodic identity: 180 deg is identical to 0 deg
    if abs(ax - 180.0) < tolerance:
        ax = 0.0

    alpha_rad = math.radians(ax)
    two_alpha = 2.0 * alpha_rad

    m = s + (c / 2.0)
    j0 = -(c / 2.0) * math.cos(two_alpha)
    j45 = -(c / 2.0) * math.sin(two_alpha)

    # Clean near-zero floating precision artifacts
    if abs(j0) < tolerance:
        j0 = 0.0
    if abs(j45) < tolerance:
        j45 = 0.0

    return PowerVector(M=m, J0=j0, J45=j45, tolerance=tolerance)


def power_vector_to_prescription(
    pv: PowerVector,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Prescription:
    """
    Reconstruct canonical minus-cylinder prescription from a Thibos PowerVector.

    In canonical minus-cylinder notation (C <= 0):
        B = sqrt(J0^2 + J45^2)
        C = -2 * B
        S = M - C / 2 = M + B
        2 * alpha = atan2(J45, J0)

    Args:
        pv: PowerVector instance.
        tolerance: Numerical threshold for astigmatism detection.

    Returns:
        Prescription instance with canonical minus-cylinder notation.
    """
    b = pv.astigmatic_magnitude

    if b < tolerance:
        return Prescription(
            sphere=float(pv.M),
            cylinder=0.0,
            axis=None,
            tolerance=tolerance,
        )

    cyl = -2.0 * b
    sph = float(pv.M + b)

    two_alpha_rad = math.atan2(pv.J45, pv.J0)
    two_alpha_deg = math.degrees(two_alpha_rad) % 360.0
    alpha = (two_alpha_deg / 2.0) % 180.0

    if abs(alpha - 180.0) < tolerance or alpha < tolerance:
        alpha = 0.0

    return Prescription(
        sphere=sph,
        cylinder=cyl,
        axis=alpha,
        tolerance=tolerance,
    )


def construct_power_matrix(
    pv_or_m: Union[PowerVector, float],
    j0: Optional[float] = None,
    j45: Optional[float] = None,
) -> np.ndarray:
    """
    Construct the symmetric 2D refractive power matrix F (diopters).

    Matrix form:
        F = [[M + J0,   J45  ],
             [  J45 , M - J0 ]]

    Args:
        pv_or_m: PowerVector object, or scalar M (diopters).
        j0: Jackson cross-cylinder J0 (diopters), if scalar M is passed.
        j45: Jackson cross-cylinder J45 (diopters), if scalar M is passed.

    Returns:
        2x2 symmetric NumPy array of dtype float64.
    """
    if isinstance(pv_or_m, PowerVector):
        m_val = float(pv_or_m.M)
        j0_val = float(pv_or_m.J0)
        j45_val = float(pv_or_m.J45)
    else:
        _validate_finite(pv_or_m, "M")
        if j0 is None or j45 is None:
            raise ValueError("When passing scalar M, j0 and j45 must also be provided.")
        _validate_finite(j0, "J0")
        _validate_finite(j45, "J45")
        m_val = float(pv_or_m)
        j0_val = float(j0)
        j45_val = float(j45)

    f_mat = np.array(
        [
            [m_val + j0_val, j45_val],
            [j45_val, m_val - j0_val],
        ],
        dtype=np.float64,
    )
    return f_mat


def meridional_power(
    m: float,
    j0: float,
    j45: float,
    theta_deg: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """
    Compute meridional refractive power F(theta) at angle theta (degrees).

    Formula:
        F(theta) = M + J0 * cos(2 * theta) + J45 * sin(2 * theta)

    Args:
        m: Spherical equivalent power (D).
        j0: Jackson cross-cylinder power at 0/90 deg (D).
        j45: Jackson cross-cylinder power at 45/135 deg (D).
        theta_deg: Meridian angle in degrees (scalar or array).

    Returns:
        Refractive power in diopters (scalar or array).
    """
    _validate_finite(m, "M")
    _validate_finite(j0, "J0")
    _validate_finite(j45, "J45")

    theta_rad = np.radians(theta_deg)
    two_theta = 2.0 * theta_rad

    return m + j0 * np.cos(two_theta) + j45 * np.sin(two_theta)


def power_matrix_meridional_power(
    f_matrix: np.ndarray,
    theta_deg: Union[float, np.ndarray],
) -> Union[float, np.ndarray]:
    """
    Calculate meridional power via matrix quadratic form:
        F(theta) = e(theta)^T * F * e(theta)
    where e(theta) = [cos(theta), sin(theta)]^T.

    Args:
        f_matrix: 2x2 symmetric refractive power matrix.
        theta_deg: Meridian angle in degrees (scalar or array).

    Returns:
        Refractive power in diopters (scalar or array).
    """
    f_arr = np.asarray(f_matrix, dtype=np.float64)
    if f_arr.shape != (2, 2):
        raise ValueError(f"Power matrix must have shape (2, 2), got {f_arr.shape}")
    if not np.allclose(f_arr, f_arr.T, atol=DEFAULT_TOLERANCE):
        raise ValueError("Power matrix must be symmetric (F == F.T)")

    theta_arr = np.asarray(theta_deg, dtype=np.float64)
    theta_rad = np.radians(theta_arr)

    cos_t = np.cos(theta_rad)
    sin_t = np.sin(theta_rad)

    # e^T * F * e = F_00 * cos^2 + 2 * F_01 * cos * sin + F_11 * sin^2
    power = (
        f_arr[0, 0] * (cos_t ** 2)
        + 2.0 * f_arr[0, 1] * cos_t * sin_t
        + f_arr[1, 1] * (sin_t ** 2)
    )

    if np.ndim(theta_deg) == 0:
        return float(power)
    return power


def decompose_power_matrix(
    f_matrix: np.ndarray,
    tolerance: float = DEFAULT_TOLERANCE,
) -> Tuple[PowerVector, Tuple[float, float], Tuple[Optional[float], Optional[float]]]:
    """
    Decompose a 2x2 symmetric power matrix into its Thibos PowerVector,
    principal eigenvalues (principal powers), and principal orientations.

    Args:
        f_matrix: 2x2 symmetric power matrix.
        tolerance: Numerical tolerance for symmetry and astigmatism checks.

    Returns:
        (power_vector, (lambda_1, lambda_2), (axis_1, axis_2))
        where axis_1 and axis_2 are None if astigmatism < tolerance.
    """
    f_arr = np.asarray(f_matrix, dtype=np.float64)
    if f_arr.shape != (2, 2):
        raise ValueError(f"Expected shape (2, 2), got {f_arr.shape}")
    if not np.allclose(f_arr, f_arr.T, atol=tolerance):
        raise ValueError("Matrix is not symmetric within tolerance.")

    # Invert linear equations:
    # F_00 = M + J0, F_11 = M - J0 => M = (F_00 + F_11) / 2, J0 = (F_00 - F_11) / 2
    # F_01 = J45
    m = float((f_arr[0, 0] + f_arr[1, 1]) / 2.0)
    j0 = float((f_arr[0, 0] - f_arr[1, 1]) / 2.0)
    j45 = float((f_arr[0, 1] + f_arr[1, 0]) / 2.0)

    pv = PowerVector(M=m, J0=j0, J45=j45, tolerance=tolerance)
    eigenvalues = pv.principal_powers()
    axes = pv.principal_axes()

    return pv, eigenvalues, axes
