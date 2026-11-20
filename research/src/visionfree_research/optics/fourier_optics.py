"""
fourier_optics.py — Monochromatic Diffraction & Fourier Propagation Engine
Part of VISIONFREE Phase 5.2: Diffraction and Fourier Optics Engine.

Implements:
- 2D Fraunhofer diffraction propagation from generalized complex pupil function.
- Amplitude Point Spread Function (APSF) and Intensity Point Spread Function (PSF).
- Multiple PSF normalization conventions (integrated energy, discrete sum, physical irradiance).
- Two-dimensional Optical Transfer Function (OTF), Modulation Transfer Function (MTF),
  and Phase Transfer Function (PTF).
- Analytical diffraction-limited Airy disk reference (Bessel functions J1, J0).
- Analytical circular aperture MTF reference (Duffieux overlap equation).
- Pupil autocorrelation cross-check for incoherent optical transfer.

Foundational References:
    Goodman JW. (2005). Introduction to Fourier Optics (3rd ed.). Roberts & Company.
    Thibos LN, et al. (1997). Optometry and Vision Science, 74(6), 367-375.
    Born M, Wolf E. (1999). Principles of Optics (7th ed.). Cambridge University Press.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, Union

import numpy as np
from scipy.fft import fft2, fftshift, ifft2, ifftshift
from scipy.special import j0, j1

from .sampling import (
    DEFAULT_SAFETY_FACTOR,
    DEFAULT_SPAN_FACTOR,
    DEFAULT_WAVELENGTH_PHOTOPIC,
    FFTPupilGrid,
    create_fft_pupil_grid,
)

# Standard human reduced-eye posterior focal length in vitreous humor (17 mm)
DEFAULT_FOCAL_LENGTH_EYE: float = 0.017  # meters


def _validate_positive_finite(val: float, name: str) -> None:
    """Validate that a numeric parameter is finite and strictly positive."""
    if not isinstance(val, (int, float, np.floating, np.integer)):
        raise TypeError(f"Parameter '{name}' must be numeric, got {type(val).__name__}")
    if not math.isfinite(float(val)):
        raise ValueError(f"Parameter '{name}' must be finite, got {val}")
    if float(val) <= 0.0:
        raise ValueError(f"Parameter '{name}' must be strictly positive (> 0), got {val}")


@dataclass(frozen=True)
class PSFResult:
    """
    Result container for Point Spread Function (PSF) computation.

    Attributes:
        psf (np.ndarray): 2D float64 array of intensity PSF.
        amplitude_psf (np.ndarray): 2D complex128 array of amplitude PSF (coherent field).
        x (np.ndarray): 1D float64 array of image-plane x coordinates (meters).
        y (np.ndarray): 1D float64 array of image-plane y coordinates (meters).
        dx (float): Sampling pitch in image plane along x (meters).
        dy (float): Sampling pitch in image plane along y (meters).
        angular_pitch_rad (float): Angular visual pitch along x in radians (dx / focal_length).
        angular_pitch_arcmin (float): Angular visual pitch in arcminutes.
        total_integrated_energy (float): Discrete integral sum(PSF) * dx * dy.
        discrete_sum (float): Raw sum of PSF array elements sum(PSF).
        centroid (Tuple[float, float]): Geometric center of mass (x_c, y_c) in meters.
        peak_intensity (float): Maximum intensity value in the PSF array.
        normalization (str): Normalization convention used ('integrated', 'probability', 'physical').
        scale_factor_applied (float): Multiplier applied to raw irradiance to achieve normalization.
        focal_length (float): Focal length f used in propagation (meters).
        wavelength (float): Optical wavelength lambda used in propagation (meters).
        pupil_samples (int): Original sample count of the pupil grid.
        fft_samples (int): Total FFT grid size (including zero-padding).
    """

    psf: np.ndarray
    amplitude_psf: np.ndarray
    x: np.ndarray
    y: np.ndarray
    dx: float
    dy: float
    angular_pitch_rad: float
    angular_pitch_arcmin: float
    total_integrated_energy: float
    discrete_sum: float
    centroid: Tuple[float, float]
    peak_intensity: float
    normalization: str
    scale_factor_applied: float
    focal_length: float
    wavelength: float
    pupil_samples: int
    fft_samples: int

    @property
    def field_of_view_x(self) -> float:
        """Total image-plane window width along x (meters)."""
        return float(self.dx * len(self.x))

    @property
    def field_of_view_y(self) -> float:
        """Total image-plane window width along y (meters)."""
        return float(self.dy * len(self.y))


@dataclass(frozen=True)
class OTFResult:
    """
    Result container for Optical Transfer Function (OTF) computation.

    Attributes:
        otf (np.ndarray): 2D complex128 array of Optical Transfer Function.
        mtf (np.ndarray): 2D float64 array of Modulation Transfer Function (|OTF| >= 0).
        ptf (np.ndarray): 2D float64 array of Phase Transfer Function in radians [-pi, pi].
        fx (np.ndarray): 1D float64 array of spatial frequencies along x (cycles/meter).
        fy (np.ndarray): 1D float64 array of spatial frequencies along y (cycles/meter).
        dfx (float): Spatial frequency sampling pitch along x (cycles/meter).
        dfy (float): Spatial frequency sampling pitch along y (cycles/meter).
        cutoff_frequency_cycles_per_m (float): Theoretical diffraction cutoff D / (lambda * f).
        cutoff_frequency_cpd (float): Theoretical diffraction cutoff in cycles per degree.
        dc_value (complex): OTF value at zero spatial frequency (fx=0, fy=0). Should be 1.0 + 0.0j.
        frequency_units (str): Text description of units ("cycles/meter").
    """

    otf: np.ndarray
    mtf: np.ndarray
    ptf: np.ndarray
    fx: np.ndarray
    fy: np.ndarray
    dfx: float
    dfy: float
    cutoff_frequency_cycles_per_m: float
    cutoff_frequency_cpd: float
    dc_value: complex
    frequency_units: str = "cycles/meter"

    @property
    def real(self) -> np.ndarray:
        """Real component of the complex OTF array."""
        return self.otf.real

    @property
    def imag(self) -> np.ndarray:
        """Imaginary component of the complex OTF array."""
        return self.otf.imag

    @property
    def fx_cpd(self) -> np.ndarray:
        """Spatial frequency axis converted to visual cycles per degree (cpd)."""
        # fx [cycles/m] * focal_length [m/rad] * (pi / 180) [rad/deg]
        # Since cutoff_cpd = cutoff_cycles_per_m * focal_length * (pi / 180):
        scale = (self.cutoff_frequency_cpd / self.cutoff_frequency_cycles_per_m)
        return self.fx * scale

    @property
    def fy_cpd(self) -> np.ndarray:
        """Spatial frequency axis converted to visual cycles per degree (cpd)."""
        scale = (self.cutoff_frequency_cpd / self.cutoff_frequency_cycles_per_m)
        return self.fy * scale


def fraunhofer_propagation(
    complex_pupil: np.ndarray,
    pupil_grid: FFTPupilGrid,
    focal_length: float = DEFAULT_FOCAL_LENGTH_EYE,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
    pad_samples: Optional[int] = None,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray, float, float]:
    """
    Perform 2D scalar Fraunhofer diffraction propagation from pupil to focal plane.

    Theoretical Continuous Integral (Goodman, 2005):
        h(x_i, y_i) = (1 / (lambda * f)) * iint P(x_p, y_p) * exp(-i * 2*pi / (lambda*f) * (x_p*x_i + y_p*y_i)) dx_p dy_p

    Phase Factor Note:
        The paraxial quadratic phase factor exp(i * k / (2*f) * (x_i^2 + y_i^2))
        is omitted because for intensity PSF computation (|h|^2), its modulus is
        identically 1.0, having zero physical impact on incoherent retinal irradiance.

    Discrete Fourier Formulation:
        Let pupil pitch be dx_p. If zero-padded to N_fft x N_fft:
            Window L_pad = N_fft * dx_p
            Retinal pitch dx_i = (lambda * f) / (N_fft * dx_p) = (lambda * f) / L_pad
            h[u, v] = (dx_p * dy_p / (lambda * f)) * fftshift(fft2(ifftshift(P_padded)))

    Args:
        complex_pupil: 2D complex array of generalized pupil function P(x_p, y_p).
        pupil_grid: FFTPupilGrid defining physical pupil coordinates and sampling pitch.
        focal_length: Effective focal length f in meters (> 0, default 17 mm).
        wavelength: Optical wavelength lambda in meters (> 0, default 555 nm).
        pad_samples: Optional total FFT sample count >= pupil_grid.samples for zero-padding.
                     Zero-padding interpolates the focal plane (denser sampling pitch dx_i)
                     without modifying the physical pupil aperture.

    Returns:
        (amplitude_psf, x_image, y_image, dx_image, dy_image)
    """
    _validate_positive_finite(focal_length, "focal_length")
    _validate_positive_finite(wavelength, "wavelength")

    p_arr = np.asarray(complex_pupil, dtype=np.complex128)
    n_pupil = pupil_grid.samples
    if p_arr.shape != (n_pupil, n_pupil):
        raise ValueError(
            f"complex_pupil shape {p_arr.shape} does not match pupil_grid samples ({n_pupil}, {n_pupil})"
        )

    dx_p = pupil_grid.dx
    dy_p = pupil_grid.dy

    # Determine zero-padding
    if pad_samples is None or pad_samples == n_pupil:
        n_fft = n_pupil
        p_padded = p_arr
    else:
        if not isinstance(pad_samples, (int, np.integer)) or pad_samples < n_pupil:
            raise ValueError(
                f"pad_samples must be integer >= pupil samples ({n_pupil}), got {pad_samples}"
            )
        n_fft = int(pad_samples)
        pad_total = n_fft - n_pupil
        pad_before = pad_total // 2
        pad_after = pad_total - pad_before
        p_padded = np.pad(p_arr, ((pad_before, pad_after), (pad_before, pad_after)), mode="constant", constant_values=0.0)

    # Focal plane sampling pitch: dx_i = (lambda * f) / (n_fft * dx_p)
    dx_i = (float(wavelength) * float(focal_length)) / (float(n_fft) * dx_p)
    dy_i = dx_i

    # Image plane 1D coordinates following DFT origin convention
    k_indices = np.arange(n_fft, dtype=np.float64)
    if n_fft % 2 == 0:
        center_k = n_fft // 2
        x_image = (k_indices - float(center_k)) * dx_i
    else:
        center_k = (n_fft - 1) // 2
        x_image = (k_indices - float(center_k)) * dx_i
    x_image[center_k] = 0.0
    y_image = x_image.copy()

    # Discrete 2D FFT propagation with ifftshift/fftshift centering
    # Scaling factor dx_p * dy_p / (lambda * f) ensures dimensional physical field scaling
    scale = (dx_p * dy_p) / (float(wavelength) * float(focal_length))
    fft_raw = fftshift(fft2(ifftshift(p_padded)))
    amplitude_psf = scale * fft_raw

    return amplitude_psf, x_image, y_image, float(dx_i), float(dy_i)


def compute_psf(
    complex_pupil: np.ndarray,
    pupil_grid: FFTPupilGrid,
    focal_length: float = DEFAULT_FOCAL_LENGTH_EYE,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
    pad_samples: Optional[int] = None,
    normalization: str = "integrated",
) -> PSFResult:
    """
    Compute the monochromatic incoherent Point Spread Function (PSF).

    Equations:
        Intensity PSF: PSF(x_i, y_i) = |h(x_i, y_i)|^2

    Normalization Conventions:
        - "integrated" (Default): Total integrated energy equals 1.0.
            iint PSF(x_i, y_i) dx_i dy_i = sum(PSF) * dx_i * dy_i = 1.0
        - "probability": Discrete sum across all array elements equals 1.0.
            sum(PSF) = 1.0
        - "physical": Unnormalized physical irradiance [W / m^2] for unit incident pupil field.

    Args:
        complex_pupil: 2D complex array of generalized pupil function.
        pupil_grid: FFTPupilGrid instance.
        focal_length: Focal length in meters (default 0.017 m).
        wavelength: Optical wavelength in meters (default 555 nm).
        pad_samples: Optional zero-padding sample count (>= pupil_grid.samples).
        normalization: "integrated", "probability", or "physical".

    Returns:
        PSFResult dataclass with intensity PSF, coordinates, and energy metrics.
    """
    valid_norms = {"integrated", "probability", "physical"}
    if normalization not in valid_norms:
        raise ValueError(f"normalization must be one of {valid_norms}, got '{normalization}'")

    amp_psf, x_i, y_i, dx_i, dy_i = fraunhofer_propagation(
        complex_pupil=complex_pupil,
        pupil_grid=pupil_grid,
        focal_length=focal_length,
        wavelength=wavelength,
        pad_samples=pad_samples,
    )

    # Raw intensity: |h|^2
    raw_intensity = np.abs(amp_psf) ** 2

    # Discrete metrics before normalization
    raw_discrete_sum = float(np.sum(raw_intensity))
    raw_integrated_energy = raw_discrete_sum * dx_i * dy_i

    if raw_discrete_sum <= 0.0 or not math.isfinite(raw_discrete_sum):
        raise ValueError("Computed pupil field has zero or non-finite total energy.")

    if normalization == "integrated":
        scale_factor = 1.0 / raw_integrated_energy
    elif normalization == "probability":
        scale_factor = 1.0 / raw_discrete_sum
    else:  # "physical"
        scale_factor = 1.0

    psf_normalized = raw_intensity * scale_factor

    # Recompute metrics on normalized PSF
    total_energy = float(np.sum(psf_normalized) * dx_i * dy_i)
    discrete_sum = float(np.sum(psf_normalized))
    peak_val = float(np.max(psf_normalized))

    # Centroid calculation: center of mass
    xg, yg = np.meshgrid(x_i, y_i)
    denom = discrete_sum if discrete_sum > 0 else 1.0
    centroid_x = float(np.sum(xg * psf_normalized) / denom)
    centroid_y = float(np.sum(yg * psf_normalized) / denom)

    # Angular pitches
    ang_rad = dx_i / float(focal_length)
    ang_arcmin = ang_rad * (180.0 * 60.0 / math.pi)

    n_fft = len(x_i)

    return PSFResult(
        psf=psf_normalized,
        amplitude_psf=amp_psf,
        x=x_i,
        y=y_i,
        dx=dx_i,
        dy=dy_i,
        angular_pitch_rad=ang_rad,
        angular_pitch_arcmin=ang_arcmin,
        total_integrated_energy=total_energy,
        discrete_sum=discrete_sum,
        centroid=(centroid_x, centroid_y),
        peak_intensity=peak_val,
        normalization=normalization,
        scale_factor_applied=scale_factor,
        focal_length=float(focal_length),
        wavelength=float(wavelength),
        pupil_samples=pupil_grid.samples,
        fft_samples=n_fft,
    )


def compute_otf(
    psf_result: PSFResult,
) -> OTFResult:
    """
    Compute the two-dimensional Optical Transfer Function (OTF) from a normalized PSF.

    Theoretical Formulation:
        OTF(f_x, f_y) = iint PSF_norm(x_i, y_i) * exp(-i * 2*pi * (f_x*x_i + f_y*y_i)) dx_i dy_i
        Normalized such that OTF(0, 0) == 1.0 + 0.0j.

    Components:
        MTF(f_x, f_y) = |OTF(f_x, f_y)| >= 0   (Modulation Transfer Function)
        PTF(f_x, f_y) = arg(OTF(f_x, f_y))     (Phase Transfer Function, radians [-pi, pi])

    Args:
        psf_result: PSFResult dataclass containing normalized intensity PSF.

    Returns:
        OTFResult dataclass with complex OTF, MTF, PTF, and spatial frequency axes.
    """
    psf_arr = psf_result.psf
    dx_i = psf_result.dx
    dy_i = psf_result.dy
    n = len(psf_result.x)

    # Spatial frequency pitch in cycles/meter: df = 1 / (N * dx_i)
    df_x = 1.0 / (float(n) * dx_i)
    df_y = 1.0 / (float(n) * dy_i)

    k_indices = np.arange(n, dtype=np.float64)
    if n % 2 == 0:
        center_k = n // 2
        fx = (k_indices - float(center_k)) * df_x
    else:
        center_k = (n - 1) // 2
        fx = (k_indices - float(center_k)) * df_x
    fx[center_k] = 0.0
    fy = fx.copy()

    # Discrete 2D Fourier transform of the PSF:
    # Integral = sum(PSF) * dx_i * dy_i * exp(-i * 2*pi * ...)
    # If psf was normalized with integrated energy = 1.0, then sum(PSF)*dx*dy == 1.0,
    # meaning fft_raw at (0, 0) * dx_i * dy_i equals 1.0!
    fft_raw = fftshift(fft2(ifftshift(psf_arr)))
    otf_unscaled = fft_raw * (dx_i * dy_i)

    # Find DC coordinate at the designated center index
    dc_raw = otf_unscaled[center_k, center_k]
    if abs(dc_raw) <= 0.0 or not math.isfinite(abs(dc_raw)):
        raise ValueError("OTF DC component is zero or non-finite.")

    # Strictly enforce OTF(0, 0) == 1.0 + 0.0j
    otf_norm = otf_unscaled / dc_raw
    otf_norm[center_k, center_k] = 1.0 + 0.0j

    # Modulation and Phase transfer functions
    mtf = np.abs(otf_norm)
    ptf = np.angle(otf_norm)

    # Theoretical diffraction cutoff: f_cutoff = D / (lambda * f)
    # where D is entrance pupil diameter = 2 * r_p
    # Note: pupil diameter can be deduced from cutoff frequency or passed through
    # For a general focal length and wavelength:
    # Retinal field of view = N * dx_i. Pupil window L_p = (lambda * f) / dx_i.
    pupil_window = (psf_result.wavelength * psf_result.focal_length) / dx_i
    # Actual pupil diameter is approximately (pupil_samples / fft_samples) * pupil_window / span_factor
    # More directly, cutoff in cycles/meter is 2 * r_p / (lambda * f)
    # We estimate cutoff using the maximum frequency in the grid or physical parameters:
    cutoff_cycles_per_m = (pupil_window / DEFAULT_SPAN_FACTOR) / (psf_result.wavelength * psf_result.focal_length)
    cutoff_cpd = cutoff_cycles_per_m * psf_result.focal_length * (math.pi / 180.0)

    return OTFResult(
        otf=otf_norm,
        mtf=mtf,
        ptf=ptf,
        fx=fx,
        fy=fy,
        dfx=float(df_x),
        dfy=float(df_y),
        cutoff_frequency_cycles_per_m=float(cutoff_cycles_per_m),
        cutoff_frequency_cpd=float(cutoff_cpd),
        dc_value=complex(otf_norm[center_k, center_k]),
        frequency_units="cycles/meter",
    )


def analytical_airy_psf(
    radius_or_diameter: float,
    focal_length: float,
    wavelength: float,
    r_image: Union[float, np.ndarray],
    diameter_passed: bool = False,
    peak_normalized: bool = True,
) -> Union[float, np.ndarray]:
    """
    Compute the analytical diffraction-limited Airy pattern for an unaberrated clear circular aperture.

    Formula (Airy, 1835; Goodman, 2005):
        u = pi * D * r_image / (lambda * f)
        I(u) = I_0 * [ 2 * J1(u) / u ]^2

    Limiting Behavior:
        lim_{u -> 0} [ 2 * J1(u) / u ] = 1.0

    Args:
        radius_or_diameter: Pupil radius r_p (if diameter_passed=False) or diameter D (if True) in meters.
        focal_length: Focal length f in meters (> 0).
        wavelength: Wavelength lambda in meters (> 0).
        r_image: Radial distance from the optical axis in the focal plane (meters, scalar or array).
        diameter_passed: If True, input is diameter D; if False, input is radius r_p.
        peak_normalized: If True, intensity is normalized to 1.0 at r_image=0.
                         If False, normalized such that the spatial integral equals 1.0.

    Returns:
        Airy intensity (scalar float or NumPy array).
    """
    _validate_positive_finite(radius_or_diameter, "radius_or_diameter")
    _validate_positive_finite(focal_length, "focal_length")
    _validate_positive_finite(wavelength, "wavelength")

    d = float(radius_or_diameter) if diameter_passed else 2.0 * float(radius_or_diameter)
    r_arr = np.asarray(r_image, dtype=np.float64)

    # Compute dimensionless argument u = pi * D * r / (lambda * f)
    factor = (math.pi * d) / (float(wavelength) * float(focal_length))
    u = factor * np.abs(r_arr)

    # Numerical evaluation of 2 * J1(u) / u avoiding division by zero
    # Near u=0, use Maclaurin series: 2*J1(u)/u = 1 - u^2/8 + u^4/192 - ...
    with np.errstate(divide="ignore", invalid="ignore"):
        airy_field = np.where(u < 1e-7, 1.0 - (u ** 2) / 8.0, 2.0 * j1(u) / u)

    intensity = airy_field ** 2

    if not peak_normalized:
        # For integrated normalization iint I(r) r dr dtheta = 1.0:
        # Peak of integrated Airy is (pi * D^2) / (4 * lambda^2 * f^2)
        peak_scale = (math.pi * (d ** 2)) / (4.0 * (float(wavelength) ** 2) * (float(focal_length) ** 2))
        intensity = intensity * peak_scale

    if np.ndim(r_image) == 0:
        return float(intensity)
    return intensity


def analytical_airy_zeros(
    radius_or_diameter: float,
    focal_length: float,
    wavelength: float,
    diameter_passed: bool = False,
) -> Dict[str, float]:
    """
    Compute exact radial positions of the first three dark rings (Airy minima) in meters.

    Analytical Zero Coordinates (Bessel function J1 zeros):
        - 1st dark ring: u_1 = 3.831705970207512 => r_1 = 1.21966989 * lambda * f / D
        - 2nd dark ring: u_2 = 7.015586669815619 => r_2 = 2.23313059 * lambda * f / D
        - 3rd dark ring: u_3 = 10.17346813506272 => r_3 = 3.23831548 * lambda * f / D

    Args:
        radius_or_diameter: Pupil radius or diameter in meters.
        focal_length: Focal length f in meters.
        wavelength: Wavelength lambda in meters.
        diameter_passed: True if input is diameter, False if radius.

    Returns:
        Dict with keys 'r_first_zero_m', 'r_second_zero_m', 'r_third_zero_m', 'encircled_energy_first_ring'.
    """
    _validate_positive_finite(radius_or_diameter, "radius_or_diameter")
    _validate_positive_finite(focal_length, "focal_length")
    _validate_positive_finite(wavelength, "wavelength")

    d = float(radius_or_diameter) if diameter_passed else 2.0 * float(radius_or_diameter)
    scale = (float(wavelength) * float(focal_length)) / (math.pi * d)

    u1 = 3.831705970207512
    u2 = 7.015586669815619
    u3 = 10.173468135062722

    # Encircled energy inside first dark ring: E(u1) = 1 - J0(u1)^2 - J1(u1)^2
    # Since J1(u1) = 0, E(u1) = 1 - J0(u1)^2
    ee_first_ring = float(1.0 - (j0(u1) ** 2))

    return {
        "r_first_zero_m": float(u1 * scale),
        "r_second_zero_m": float(u2 * scale),
        "r_third_zero_m": float(u3 * scale),
        "angular_first_zero_rad": float(u1 * float(wavelength) / (math.pi * d)),
        "encircled_energy_first_ring": ee_first_ring,
    }


def analytical_diffraction_limited_mtf(
    spatial_frequency_cycles_per_m: Union[float, np.ndarray],
    pupil_diameter: float,
    focal_length: float,
    wavelength: float,
) -> Union[float, np.ndarray]:
    """
    Compute the exact closed-form Modulation Transfer Function (MTF) for an unaberrated circular aperture.

    Formula (Duffieux overlap area of two displaced circles):
        nu = f_r / f_cutoff
        where f_cutoff = D / (lambda * f)
        MTF(nu) = (2 / pi) * [ arccos(nu) - nu * sqrt(1 - nu^2) ] for nu <= 1, else 0.

    Args:
        spatial_frequency_cycles_per_m: Radial spatial frequency in cycles/meter.
        pupil_diameter: Entrance pupil diameter D in meters.
        focal_length: Focal length f in meters.
        wavelength: Optical wavelength lambda in meters.

    Returns:
        MTF values in range [0.0, 1.0].
    """
    _validate_positive_finite(pupil_diameter, "pupil_diameter")
    _validate_positive_finite(focal_length, "focal_length")
    _validate_positive_finite(wavelength, "wavelength")

    f_cutoff = float(pupil_diameter) / (float(wavelength) * float(focal_length))
    f_arr = np.abs(np.asarray(spatial_frequency_cycles_per_m, dtype=np.float64))

    nu = f_arr / f_cutoff

    with np.errstate(invalid="ignore"):
        mtf_vals = np.where(
            nu >= 1.0,
            0.0,
            (2.0 / math.pi) * (np.arccos(np.clip(nu, 0.0, 1.0)) - nu * np.sqrt(np.clip(1.0 - nu ** 2, 0.0, 1.0))),
        )

    if np.ndim(spatial_frequency_cycles_per_m) == 0:
        return float(mtf_vals)
    return mtf_vals


def pupil_autocorrelation_otf(
    complex_pupil: np.ndarray,
    pupil_grid: FFTPupilGrid,
    focal_length: float = DEFAULT_FOCAL_LENGTH_EYE,
    wavelength: float = DEFAULT_WAVELENGTH_PHOTOPIC,
) -> np.ndarray:
    """
    Compute the Optical Transfer Function directly via normalized pupil autocorrelation.

    Autocorrelation Theorem:
        In discrete Fourier analysis, the Fourier transform of the intensity PSF
        (|h|^2 proportional to |FFT(P)|^2) is mathematically identical to the
        discrete autocorrelation of P:
            OTF(f_x, f_y) = ifft2(|fft2(ifftshift(P))|^2)
        When span_factor >= 2.0 (pupil diameter <= window_width / 2), circular
        autocorrelation equals continuous linear autocorrelation without periodic wrap-around.

    Args:
        complex_pupil: 2D complex generalized pupil function array.
        pupil_grid: FFTPupilGrid defining spatial dimensions.
        focal_length: Focal length in meters.
        wavelength: Optical wavelength in meters.

    Returns:
        2D complex array of OTF computed via autocorrelation.
    """
    p_arr = np.asarray(complex_pupil, dtype=np.complex128)
    n = pupil_grid.samples
    center_k = n // 2 if n % 2 == 0 else (n - 1) // 2

    # Discrete autocorrelation via Fourier power spectrum
    p_centered = ifftshift(p_arr)
    p_spec = fft2(p_centered)
    autocorr = fftshift(ifft2(np.abs(p_spec) ** 2))

    dc_val = autocorr[center_k, center_k]
    if abs(dc_val) > 0:
        autocorr = autocorr / dc_val

    return autocorr
