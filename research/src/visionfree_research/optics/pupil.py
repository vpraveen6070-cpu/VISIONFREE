"""
pupil.py — Circular Pupil Coordinates, Wavefront Phase & Generalized Pupil Function
Part of VISIONFREE Phase 5.1: Mathematical Foundation.

Provides:
- 2D circular entrance pupil coordinate grid generation (physical and normalized).
- Circular aperture masking with center at (0, 0).
- Optical phase calculation phi(x, y) = 2 * pi * W(x, y) / lambda in radians.
- Complex generalized pupil function construction: P(x, y) = A(x, y) * exp(i * phi(x, y)).

Note:
    In accordance with Phase 5.1 specifications, this module does NOT compute
    Fourier transforms, point spread functions (PSF), optical transfer functions (OTF),
    or image deconvolution.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Optional, Union

import numpy as np

# Standard photopic reference wavelength: 555 nm (CIE photopic peak, V(lambda))
DEFAULT_WAVELENGTH_PHOTOPIC: float = 5.55e-7  # 555 nm in meters


def _validate_finite_float(val: float, name: str) -> None:
    """Validate that a value is a finite numeric float."""
    if not isinstance(val, (int, float, np.floating, np.integer)):
        raise TypeError(f"Parameter '{name}' must be numeric, got {type(val).__name__}")
    if not math.isfinite(float(val)):
        raise ValueError(f"Parameter '{name}' must be finite, got {val}")


@dataclass(frozen=True)
class PupilGrid:
    """
    Two-dimensional circular entrance pupil grid and coordinate system.

    The grid window is centered symmetrically around the origin (x, y) = (0, 0).

    Sampling note:
        - When samples N is odd: (0, 0) is an exact sampled grid coordinate at index (N-1)//2.
        - When samples N is even: (0, 0) lies at the geometric center between indices
          (N//2 - 1) and (N//2), with each central sample having a half-pixel offset of
          +/-0.5 * dx from the origin. The point (0, 0) is not an explicit sampled vertex.

    Attributes:
        radius (float): Physical pupil radius r_p in meters.
        samples (int): Grid sample count N along each axis (total N x N grid points).
        dx (float): Grid sampling pitch along horizontal x-axis in meters.
        dy (float): Grid sampling pitch along vertical y-axis in meters.
        x (np.ndarray): 2D physical x-coordinate array in meters, shape (samples, samples).
        y (np.ndarray): 2D physical y-coordinate array in meters, shape (samples, samples).
        u (np.ndarray): 2D normalized dimensionless horizontal coordinate u = x / r_p.
        v (np.ndarray): 2D normalized dimensionless vertical coordinate v = y / r_p.
        rho (np.ndarray): 2D normalized radial coordinate rho = sqrt(u^2 + v^2).
        theta (np.ndarray): 2D azimuthal angle array in radians [-pi, pi], theta = atan2(y, x).
        mask (np.ndarray): 2D boolean circular aperture mask (True inside or on pupil margin).
    """

    radius: float
    samples: int
    dx: float
    dy: float
    x: np.ndarray
    y: np.ndarray
    u: np.ndarray
    v: np.ndarray
    rho: np.ndarray
    theta: np.ndarray
    mask: np.ndarray

    @property
    def has_exact_center_sample(self) -> bool:
        """True if grid sample count N is odd, containing an exact (0, 0) sample point."""
        return (self.samples % 2) == 1

    @property
    def center_offset_fraction(self) -> float:
        """
        Offset of the nearest central grid sample from the origin (0, 0)
        as a fraction of pixel pitch dx. Returns 0.0 for odd N, 0.5 for even N.
        """
        return 0.0 if (self.samples % 2) == 1 else 0.5

    @property
    def diameter(self) -> float:
        """Physical pupil diameter in meters (2 * r_p)."""
        return 2.0 * self.radius

    @property
    def physical_extent(self) -> float:
        """Total span of the grid window in meters."""
        return float(self.dx * (self.samples - 1))

    @property
    def pupil_area_pixels(self) -> int:
        """Total number of sampled pixels residing within the circular pupil aperture."""
        return int(np.count_nonzero(self.mask))


def create_pupil_grid(
    radius: float,
    samples: int,
    span_factor: float = 1.0,
) -> PupilGrid:
    """
    Generate a 2D Cartesian and normalized polar coordinate grid for a circular pupil.

    The grid window is centered symmetrically at physical coordinates (x, y) = (0, 0).
    When samples N is odd, (0, 0) is an exact grid vertex at index (N-1)//2.
    When samples N is even, the grid has a half-pixel offset (+/-0.5 * dx) relative to (0, 0).

    Args:
        radius: Physical entrance pupil radius r_p in meters (e.g., 0.002 m for 4 mm pupil).
                Must be strictly positive and finite.
        samples: Number of discrete grid sample points N along each axis (integer >= 2).
        span_factor: Ratio of total grid window width to pupil diameter (2 * r_p).
                     Default is 1.0 (tight bounding box from -r_p to +r_p).
                     Must be >= 1.0.

    Returns:
        PupilGrid dataclass with physical coordinates, normalized coordinates, and circular mask.

    Raises:
        TypeError: If radius, samples, or span_factor have incorrect types.
        ValueError: If radius <= 0, samples < 2, or span_factor < 1.0.
    """
    _validate_finite_float(radius, "radius")
    if radius <= 0.0:
        raise ValueError(f"Pupil radius must be strictly positive (> 0), got {radius} m.")

    if not isinstance(samples, (int, np.integer)):
        raise TypeError(f"Grid samples must be an integer, got {type(samples).__name__}")
    if samples < 2:
        raise ValueError(f"Grid samples must be an integer >= 2, got {samples}")

    _validate_finite_float(span_factor, "span_factor")
    if span_factor < 1.0:
        raise ValueError(f"span_factor must be >= 1.0 to contain the pupil, got {span_factor}")

    r = float(radius)
    n = int(samples)
    half_span = r * float(span_factor)

    # Linearly spaced 1D coordinates spanning [-half_span, +half_span]
    coords_1d = np.linspace(-half_span, half_span, n, endpoint=True, dtype=np.float64)

    # For odd n, the middle index is analytically 0.0.
    # For even n, the grid is strictly anti-symmetric around 0.0.
    dx = float(coords_1d[1] - coords_1d[0])
    dy = dx

    x_2d, y_2d = np.meshgrid(coords_1d, coords_1d)

    # Normalized pupil coordinates
    u_2d = x_2d / r
    v_2d = y_2d / r
    rho_2d = np.sqrt(u_2d ** 2 + v_2d ** 2)
    theta_2d = np.arctan2(y_2d, x_2d)

    # Circular pupil aperture mask: points inside or on pupil margin (rho <= 1.0)
    # Using a tiny numerical tolerance (1e-12) to ensure boundary points on the circle
    # at exactly r are reliably captured.
    mask_2d = rho_2d <= (1.0 + 1e-12)

    return PupilGrid(
        radius=r,
        samples=n,
        dx=dx,
        dy=dy,
        x=x_2d,
        y=y_2d,
        u=u_2d,
        v=v_2d,
        rho=rho_2d,
        theta=theta_2d,
        mask=mask_2d,
    )


def compute_wavefront_phase(
    opd: np.ndarray,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
) -> np.ndarray:
    """
    Convert an Optical Path Difference (OPD) wavefront map into optical phase in radians.

    Formula:
        phi(x, y) = (2 * pi / lambda) * W(x, y)

    Args:
        opd: 2D array of optical path differences W(x, y) in meters.
        wavelength: Optical wavelength lambda in meters (must be > 0 and finite).
                    Default is 555 nm (5.55e-7 m).

    Returns:
        2D NumPy array of unwrapped phase values in radians (float64).

    Raises:
        ValueError: If wavelength <= 0 or non-finite, or opd contains NaN/inf.
    """
    _validate_finite_float(wavelength, "wavelength")
    if wavelength <= 0.0:
        raise ValueError(f"Wavelength must be strictly positive (> 0), got {wavelength} m.")

    opd_arr = np.asarray(opd, dtype=np.float64)
    if not np.all(np.isfinite(opd_arr)):
        raise ValueError("OPD array contains non-finite or NaN values.")

    k = (2.0 * math.pi) / float(wavelength)
    phase = k * opd_arr
    return phase


def generalized_pupil_function(
    opd: np.ndarray,
    pupil_grid: PupilGrid,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
    amplitude: Optional[Union[float, np.ndarray]] = None,
) -> np.ndarray:
    """
    Construct the complex generalized pupil function P(x, y).

    Equation:
        P(x, y) = A(x, y) * exp(i * phi(x, y))
    where:
        phi(x, y) = (2 * pi / lambda) * W(x, y)
        A(x, y) is the pupil transmission amplitude (0 outside the circular aperture).

    Boundary Conditions:
        - Inside circular pupil (mask == True): P(x, y) has magnitude A(x, y) and phase phi(x, y).
        - Outside circular pupil (mask == False): P(x, y) is identically 0.0 + 0.0j.

    Args:
        opd: Optical path difference array W(x, y) in meters, shape (samples, samples).
        pupil_grid: PupilGrid instance defining spatial coordinates and circular mask.
        wavelength: Optical wavelength in meters (> 0).
        amplitude: Pupil amplitude function inside the aperture. If None, defaults to uniform 1.0.
                   Can also be a custom 2D float array (e.g., Stiles-Crawford apodization).

    Returns:
        Complex 2D NumPy array of dtype complex128, shape (samples, samples).

    Raises:
        ValueError: If array shapes mismatch, or wavelength is non-physical.
    """
    opd_arr = np.asarray(opd, dtype=np.float64)
    if opd_arr.shape != (pupil_grid.samples, pupil_grid.samples):
        raise ValueError(
            f"OPD shape {opd_arr.shape} does not match pupil grid shape "
            f"({pupil_grid.samples}, {pupil_grid.samples})"
        )

    # Compute unwrapped phase
    phase = compute_wavefront_phase(opd_arr, wavelength=wavelength)

    # Setup amplitude array inside aperture
    if amplitude is None:
        amp_arr = np.where(pupil_grid.mask, 1.0, 0.0).astype(np.float64)
    elif isinstance(amplitude, (int, float, np.floating, np.integer)):
        _validate_finite_float(amplitude, "amplitude")
        if amplitude < 0.0:
            raise ValueError(f"Amplitude cannot be negative, got {amplitude}")
        amp_arr = np.where(pupil_grid.mask, float(amplitude), 0.0).astype(np.float64)
    else:
        amp_raw = np.asarray(amplitude, dtype=np.float64)
        if amp_raw.shape != opd_arr.shape:
            raise ValueError(
                f"Amplitude array shape {amp_raw.shape} does not match grid shape {opd_arr.shape}"
            )
        if np.any(amp_raw < 0.0):
            raise ValueError("Amplitude cannot contain negative values.")
        amp_arr = np.where(pupil_grid.mask, amp_raw, 0.0)

    # Construct complex generalized pupil: P = A * exp(i * phi)
    # Outside mask, amp_arr is 0.0, so result is strictly 0.0 + 0.0j
    complex_pupil = amp_arr * np.exp(1j * phase)

    # Ensure numerical zero outside mask
    complex_pupil[~pupil_grid.mask] = 0.0 + 0.0j

    return complex_pupil
