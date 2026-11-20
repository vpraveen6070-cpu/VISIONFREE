"""
sampling.py — Discrete FFT Sampling Grids & Phase Nyquist Criteria
Part of VISIONFREE Phase 5.2: Diffraction and Fourier Optics Engine.

Provides:
- FFT-compatible periodic DFT pupil coordinate generation (dx = L / N).
- Explicit coordinate centering: x[k] = (k - N/2)*dx for even N, (k - (N-1)/2)*dx for odd N.
- Spatial phase gradient and Nyquist aliasing boundary calculations.
- Dynamic FFT grid size selection based on refractive power, pupil size, and wavelength.
- Comprehensive sampling diagnostics and safety factor evaluations.

Distinction from Visualization Grid:
    The existing visualization grid in pupil.py uses an endpoint-inclusive grid
    np.linspace(-half_span, half_span, N, endpoint=True) with pitch dx = L / (N - 1).
    This module implements the non-redundant periodic DFT grid dx = L / N required
    for discrete Fourier transformation without boundary endpoint duplication.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Tuple, Union

import numpy as np

# Standard photopic reference wavelength: 555 nm
DEFAULT_WAVELENGTH_PHOTOPIC: float = 5.55e-7  # meters
# Default computational window span relative to pupil diameter (2 * r_p)
DEFAULT_SPAN_FACTOR: float = 1.2
# Default engineering safety factor beyond the strict Nyquist sampling limit
DEFAULT_SAFETY_FACTOR: float = 1.5


def _validate_finite_positive(val: float, name: str) -> None:
    """Validate that a numeric parameter is finite and strictly positive."""
    if not isinstance(val, (int, float, np.floating, np.integer)):
        raise TypeError(f"Parameter '{name}' must be numeric, got {type(val).__name__}")
    if not math.isfinite(float(val)):
        raise ValueError(f"Parameter '{name}' must be finite, got {val}")
    if float(val) <= 0.0:
        raise ValueError(f"Parameter '{name}' must be strictly positive (> 0), got {val}")


@dataclass(frozen=True)
class FFTPupilGrid:
    """
    Two-dimensional FFT-compatible periodic DFT pupil coordinate grid.

    All spatial coordinates follow discrete periodic DFT conventions:
        - Grid pitch: dx = dy = window_width / samples
        - Even N: x[k] = (k - N/2) * dx. The origin (0, 0) is an exact sample at index N/2.
        - Odd N: x[k] = (k - (N-1)/2) * dx. The origin (0, 0) is an exact sample at index (N-1)/2.

    Attributes:
        radius (float): Physical entrance pupil radius r_p in meters.
        samples (int): Discrete sample count N along each axis (total N x N grid).
        span_factor (float): Ratio of window width L to pupil diameter (2 * r_p).
        window_width (float): Total physical window span L = 2 * r_p * span_factor in meters.
        dx (float): Physical sampling pitch along x in meters (window_width / samples).
        dy (float): Physical sampling pitch along y in meters (window_width / samples).
        x (np.ndarray): 2D physical x-coordinate array in meters, shape (samples, samples).
        y (np.ndarray): 2D physical y-coordinate array in meters, shape (samples, samples).
        u (np.ndarray): 2D normalized dimensionless horizontal coordinate u = x / r_p.
        v (np.ndarray): 2D normalized dimensionless vertical coordinate v = y / r_p.
        rho (np.ndarray): 2D normalized radial coordinate rho = sqrt(u^2 + v^2).
        theta (np.ndarray): 2D azimuthal angle array in radians [-pi, pi], theta = atan2(y, x).
        mask (np.ndarray): 2D boolean circular aperture mask (True inside or on pupil margin).
        has_exact_center_sample (bool): True (always True under this DFT coordinate definition).
        center_index (Tuple[int, int]): Tuple (row, col) corresponding to the exact (0, 0) sample.
    """

    radius: float
    samples: int
    span_factor: float
    window_width: float
    dx: float
    dy: float
    x: np.ndarray
    y: np.ndarray
    u: np.ndarray
    v: np.ndarray
    rho: np.ndarray
    theta: np.ndarray
    mask: np.ndarray
    has_exact_center_sample: bool
    center_index: Tuple[int, int]

    @property
    def diameter(self) -> float:
        """Physical pupil diameter in meters (2 * r_p)."""
        return 2.0 * self.radius

    @property
    def pupil_area_pixels(self) -> int:
        """Total number of sampled pixels residing within the circular aperture."""
        return int(np.count_nonzero(self.mask))


def compute_max_phase_gradient(
    radius: float,
    max_dioptric_power: float,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
) -> float:
    """
    Calculate the maximum spatial phase gradient magnitude at the pupil margin (rad/m).

    Formula:
        ||grad phi||_max = (2 * pi / lambda) * D_max * r_p
    where D_max is the maximum absolute eigenvalue of the power matrix (abs(M) + B).

    Args:
        radius: Pupil radius r_p in meters.
        max_dioptric_power: Maximum dioptric refractive error magnitude (abs(M) + B) in diopters.
        wavelength: Optical wavelength in meters (> 0).

    Returns:
        Maximum phase gradient in radians per meter.
    """
    _validate_finite_positive(radius, "radius")
    _validate_finite_positive(wavelength, "wavelength")
    if not isinstance(max_dioptric_power, (int, float, np.floating, np.integer)):
        raise TypeError(f"max_dioptric_power must be numeric, got {type(max_dioptric_power).__name__}")
    if not math.isfinite(float(max_dioptric_power)):
        raise ValueError(f"max_dioptric_power must be finite, got {max_dioptric_power}")
    if float(max_dioptric_power) < 0.0:
        raise ValueError(f"max_dioptric_power must be non-negative, got {max_dioptric_power}")

    k = (2.0 * math.pi) / float(wavelength)
    grad_max = k * float(max_dioptric_power) * float(radius)
    return float(grad_max)


def compute_nyquist_grid_size(
    radius: float,
    max_dioptric_power: float,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
    span_factor: float = DEFAULT_SPAN_FACTOR,
) -> float:
    """
    Compute the theoretical continuous minimum Nyquist sample count N_nyquist.

    Derivation:
        Phase increment condition: ||grad phi||_max * dx <= pi
        With dx = L / N and L = 2 * r_p * span_factor:
            (2 * pi / lambda) * D_max * r_p * (2 * r_p * span_factor / N) <= pi
        Solving for N:
            N >= (4 * r_p^2 * span_factor * D_max) / lambda

    Args:
        radius: Pupil radius r_p in meters.
        max_dioptric_power: Maximum dioptric power magnitude (abs(M) + B) in diopters.
        wavelength: Optical wavelength in meters.
        span_factor: Window span ratio (L / (2 * r_p)). Must be >= 1.0.

    Returns:
        Continuous floating-point Nyquist threshold N_nyquist.
    """
    _validate_finite_positive(radius, "radius")
    _validate_finite_positive(wavelength, "wavelength")
    _validate_finite_positive(span_factor, "span_factor")
    if span_factor < 1.0:
        raise ValueError(f"span_factor must be >= 1.0, got {span_factor}")

    d_max = max(0.0, float(max_dioptric_power))
    r_p = float(radius)
    wl = float(wavelength)
    sf = float(span_factor)

    n_nyquist = (4.0 * (r_p ** 2) * sf * d_max) / wl
    return float(n_nyquist)


def select_fft_grid_size(
    radius: float,
    max_dioptric_power: float,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
    span_factor: float = DEFAULT_SPAN_FACTOR,
    safety_factor: float = DEFAULT_SAFETY_FACTOR,
    power_of_two: bool = True,
    min_samples: int = 64,
) -> int:
    """
    Dynamically select an FFT sample count satisfying the phase Nyquist criterion
    with a configurable engineering safety factor.

    Formula:
        N_target = ceil(safety_factor * N_nyquist)
        If power_of_two: N_selected = 2^(ceil(log2(max(min_samples, N_target))))

    Args:
        radius: Pupil radius in meters (> 0).
        max_dioptric_power: Maximum dioptric power magnitude (abs(M) + B) in diopters (>= 0).
        wavelength: Optical wavelength in meters (> 0).
        span_factor: Ratio of computational window width to pupil diameter (>= 1.0).
        safety_factor: Multiplier applied to strict Nyquist threshold (>= 1.0, default 1.5).
        power_of_two: If True, round up to the next power of two for optimal FFT radix-2 execution.
        min_samples: Lower bound on grid samples (default 64).

    Returns:
        Selected integer grid sample count N.
    """
    _validate_finite_positive(safety_factor, "safety_factor")
    if safety_factor < 1.0:
        raise ValueError(f"safety_factor must be >= 1.0, got {safety_factor}")
    if not isinstance(min_samples, (int, np.integer)) or min_samples < 8:
        raise ValueError(f"min_samples must be integer >= 8, got {min_samples}")

    n_nyquist = compute_nyquist_grid_size(
        radius=radius,
        max_dioptric_power=max_dioptric_power,
        wavelength=wavelength,
        span_factor=span_factor,
    )

    n_target = max(int(min_samples), math.ceil(float(safety_factor) * n_nyquist))

    if power_of_two:
        # Find next power of two >= n_target
        power = math.ceil(math.log2(n_target))
        return int(2 ** power)

    # Return even integer if not strictly power of two
    return n_target if n_target % 2 == 0 else n_target + 1


def evaluate_phase_sampling(
    radius: float,
    max_dioptric_power: float,
    wavelength: float,
    grid_samples: int,
    span_factor: float = DEFAULT_SPAN_FACTOR,
) -> Dict[str, Any]:
    """
    Evaluate and report phase sampling status for a given optical configuration and grid.

    Args:
        radius: Pupil radius in meters.
        max_dioptric_power: abs(M) + B in diopters.
        wavelength: Wavelength in meters.
        grid_samples: Discrete sample count N.
        span_factor: Window span ratio (L / (2 * r_p)).

    Returns:
        Dictionary containing:
            - nyquist_samples: Minimum theoretical sample count.
            - selected_samples: Current grid sample count N.
            - dx_meters: Sampling pitch in pupil plane.
            - max_phase_gradient_rad_per_m: Peak phase gradient.
            - max_phase_increment_rad: Peak phase step between adjacent samples.
            - is_nyquist_satisfied: True if max_phase_increment_rad <= pi.
            - safety_margin_ratio: Ratio of selected samples to Nyquist minimum.
    """
    _validate_finite_positive(radius, "radius")
    _validate_finite_positive(wavelength, "wavelength")
    if not isinstance(grid_samples, (int, np.integer)) or grid_samples < 2:
        raise ValueError(f"grid_samples must be integer >= 2, got {grid_samples}")

    r_p = float(radius)
    n = int(grid_samples)
    sf = float(span_factor)
    wl = float(wavelength)
    d_max = max(0.0, float(max_dioptric_power))

    window_width = 2.0 * r_p * sf
    dx = window_width / n

    grad_max = compute_max_phase_gradient(radius=r_p, max_dioptric_power=d_max, wavelength=wl)
    phase_inc = grad_max * dx
    n_nyquist = compute_nyquist_grid_size(radius=r_p, max_dioptric_power=d_max, wavelength=wl, span_factor=sf)

    is_satisfied = bool(phase_inc <= (math.pi + 1e-12))
    safety_ratio = float(n / n_nyquist) if n_nyquist > 1e-12 else float("inf")

    return {
        "nyquist_samples": float(n_nyquist),
        "selected_samples": n,
        "window_width_meters": float(window_width),
        "dx_meters": float(dx),
        "max_phase_gradient_rad_per_m": float(grad_max),
        "max_phase_increment_rad": float(phase_inc),
        "is_nyquist_satisfied": is_satisfied,
        "safety_margin_ratio": safety_ratio,
    }


def create_fft_pupil_grid(
    radius: float,
    samples: int,
    span_factor: float = DEFAULT_SPAN_FACTOR,
) -> FFTPupilGrid:
    """
    Generate an FFT-compatible periodic DFT pupil coordinate grid.

    Coordinate rules:
        - window_width L = 2 * radius * span_factor
        - dx = dy = L / samples
        - For even samples N: x[k] = (k - N / 2) * dx  (index N/2 is exact 0.0)
        - For odd samples N: x[k] = (k - (N - 1) / 2) * dx (index (N-1)/2 is exact 0.0)

    Args:
        radius: Physical pupil radius in meters (> 0).
        samples: Grid sample count N (integer >= 2).
        span_factor: Ratio of window width to pupil diameter (>= 1.0, default 1.2).

    Returns:
        FFTPupilGrid dataclass with physical coordinates, normalized coordinates, and mask.
    """
    _validate_finite_positive(radius, "radius")
    if not isinstance(samples, (int, np.integer)) or samples < 2:
        raise ValueError(f"samples must be an integer >= 2, got {samples}")
    _validate_finite_positive(span_factor, "span_factor")
    if span_factor < 1.0:
        raise ValueError(f"span_factor must be >= 1.0, got {span_factor}")

    r = float(radius)
    n = int(samples)
    sf = float(span_factor)

    window_width = 2.0 * r * sf
    dx = window_width / float(n)
    dy = dx

    # 1D coordinates following periodic DFT origin convention
    k_indices = np.arange(n, dtype=np.float64)
    if n % 2 == 0:
        center_k = n // 2
        coords_1d = (k_indices - float(center_k)) * dx
    else:
        center_k = (n - 1) // 2
        coords_1d = (k_indices - float(center_k)) * dx

    # Exact zero validation at the designated center index
    coords_1d[center_k] = 0.0

    x_2d, y_2d = np.meshgrid(coords_1d, coords_1d)

    # Normalized dimensionless coordinates
    u_2d = x_2d / r
    v_2d = y_2d / r
    rho_2d = np.sqrt(u_2d ** 2 + v_2d ** 2)
    theta_2d = np.arctan2(y_2d, x_2d)

    # Circular aperture mask
    mask_2d = rho_2d <= (1.0 + 1e-12)

    return FFTPupilGrid(
        radius=r,
        samples=n,
        span_factor=sf,
        window_width=window_width,
        dx=dx,
        dy=dy,
        x=x_2d,
        y=y_2d,
        u=u_2d,
        v=v_2d,
        rho=rho_2d,
        theta=theta_2d,
        mask=mask_2d,
        has_exact_center_sample=True,
        center_index=(center_k, center_k),
    )
