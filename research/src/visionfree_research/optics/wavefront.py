"""
wavefront.py — Quadratic Wavefront & Optical Path Difference (OPD) Engine
Part of VISIONFREE Phase 5.1: Mathematical Foundation.

Implements paraxial quadratic wavefront error and optical path difference (OPD)
modeling from refractive power matrices and Thibos power vectors.

Equations:
    W(x, y) = (sigma / 2) * [x, y] * F * [x, y]^T
    W(x, y) = (sigma / 2) * [(M + J0) * x^2 + 2 * J45 * x * y + (M - J0) * y^2]

Sign Conventions:
    sigma = +1.0 (Default): Optical Path Difference (OPD) convention as
        formulated in VISIONFREE Research Plan Section 5.3. Under this convention,
        hyperopic / positive dioptric defocus (M > 0) produces positive optical
        path lead (W > 0) relative to a reference sphere converging on the retina.
    sigma = -1.0: Wavefront error / optical path delay convention where convergent
        wavefronts advance ahead of the paraxial reference plane.

Phase Convention:
    The complex generalized pupil function is defined as:
        P(x, y) = A(x, y) * exp(i * 2 * pi * W(x, y) / lambda)
    where lambda is the optical wavelength in meters.

Scientific Limitations & Model Boundaries:
    1. Paraxial Lower-Order Approximation: This quadratic surface models only paraxial
       defocus and regular astigmatism (Seidel W20 and W22). It does NOT capture
       monochromatic higher-order ocular aberrations (e.g., spherical aberration Z_4^0,
       trefoil Z_3^{+/-3}, coma Z_3^{+/-1}).
    2. Exclusions: Viewing distance vergence (L = -1/d), dynamic accommodation (A_acc),
       spectacle vertex-distance transposition (d_vd), and ocular chromatic dispersion
       are not embedded into this low-level model and must be parameterized at higher tiers.
"""

from __future__ import annotations

import math
from typing import Dict, Union

import numpy as np

from .power_vectors import PowerVector, construct_power_matrix

# Default sign convention parameter: +1.0 represents OPD lead (consistent with Research Plan 5.3)
DEFAULT_SIGMA: float = 1.0


def _validate_finite_scalar(val: float, name: str) -> None:
    """Validate that a scalar float is finite and non-NaN."""
    if not isinstance(val, (int, float, np.floating, np.integer)):
        raise TypeError(f"Parameter '{name}' must be numeric, got {type(val).__name__}")
    if not math.isfinite(float(val)):
        raise ValueError(f"Parameter '{name}' must be finite, got {val}")


def quadratic_wavefront(
    power: Union[PowerVector, np.ndarray],
    x: Union[float, np.ndarray],
    y: Union[float, np.ndarray],
    sigma: float = DEFAULT_SIGMA,
) -> Union[float, np.ndarray]:
    """
    Compute quadratic wavefront Optical Path Difference (OPD) W(x, y) in meters.

    Formula:
        W(x, y) = (sigma / 2) * [ (M + J0) * x^2 + 2 * J45 * x * y + (M - J0) * y^2 ]

    Dimensional Analysis:
        - M, J0, J45 are in diopters (m^-1).
        - x, y are physical pupil coordinates in meters (m).
        - W(x, y) = m^-1 * m^2 = meters (m).

    Args:
        power: PowerVector instance, or a 2x2 symmetric refractive power matrix F (diopters).
        x: Physical horizontal pupil coordinate(s) in meters (scalar or array).
        y: Physical vertical pupil coordinate(s) in meters (scalar or array).
        sigma: Sign convention parameter (+1.0 for OPD lead, -1.0 for delay).

    Returns:
        Optical path difference W in meters (scalar float or NumPy array).
    """
    _validate_finite_scalar(sigma, "sigma")
    if abs(sigma) < 1e-12:
        raise ValueError("Sign parameter 'sigma' cannot be zero.")

    if isinstance(power, PowerVector):
        m_val = float(power.M)
        j0_val = float(power.J0)
        j45_val = float(power.J45)
    elif isinstance(power, np.ndarray):
        if power.shape != (2, 2):
            raise ValueError(f"Expected 2x2 power matrix, got shape {power.shape}")
        if not np.allclose(power, power.T, atol=1e-9):
            raise ValueError("Power matrix must be symmetric (F == F.T)")
        m_val = float((power[0, 0] + power[1, 1]) / 2.0)
        j0_val = float((power[0, 0] - power[1, 1]) / 2.0)
        j45_val = float((power[0, 1] + power[1, 0]) / 2.0)
    else:
        raise TypeError(
            f"Parameter 'power' must be PowerVector or 2x2 ndarray, got {type(power).__name__}"
        )

    x_arr = np.asarray(x, dtype=np.float64)
    y_arr = np.asarray(y, dtype=np.float64)

    if not np.all(np.isfinite(x_arr)):
        raise ValueError("Pupil x coordinates contain non-finite or NaN values.")
    if not np.all(np.isfinite(y_arr)):
        raise ValueError("Pupil y coordinates contain non-finite or NaN values.")

    # Quadratic OPD expansion
    half_sigma = 0.5 * float(sigma)
    f_xx = m_val + j0_val
    f_yy = m_val - j0_val
    two_f_xy = 2.0 * j45_val

    w = half_sigma * (f_xx * (x_arr ** 2) + two_f_xy * (x_arr * y_arr) + f_yy * (y_arr ** 2))

    if np.ndim(x) == 0 and np.ndim(y) == 0:
        return float(w)
    return w


def seidel_wavefront_coefficients(
    power: PowerVector,
    pupil_radius: float,
    sigma: float = DEFAULT_SIGMA,
) -> Dict[str, float]:
    """
    Compute classical Seidel lower-order aberration coefficients (meters)
    for a circular pupil of radius r_p.

    Formulas (from Research Plan Section 5.3):
        W_20 = (sigma / 2) * r_p^2 * M           [Defocus coefficient, meters]
        W_22 = (sigma / 2) * r_p^2 * B           [Astigmatism coefficient, meters]
             = (sigma / 4) * r_p^2 * |CYL|

    Args:
        power: PowerVector containing M, J0, J45.
        pupil_radius: Pupil radius r_p in meters.
        sigma: Sign convention parameter (default +1.0).

    Returns:
        Dict with keys 'W20_meters', 'W22_meters', 'pupil_radius_meters'.
    """
    _validate_finite_scalar(pupil_radius, "pupil_radius")
    if pupil_radius <= 0.0:
        raise ValueError(f"Pupil radius must be strictly positive, got {pupil_radius} m")
    _validate_finite_scalar(sigma, "sigma")

    r_sq = float(pupil_radius) ** 2
    w20 = 0.5 * float(sigma) * r_sq * float(power.M)
    w22 = 0.5 * float(sigma) * r_sq * float(power.astigmatic_magnitude)

    return {
        "W20_meters": float(w20),
        "W22_meters": float(w22),
        "pupil_radius_meters": float(pupil_radius),
        "sigma": float(sigma),
    }
