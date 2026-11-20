"""
visionfree_research.optics — Ophthalmic Power Vector, Wavefront & Fourier Optics Engine
Part of VISIONFREE Phase 5: Computational Optics Research Workspace.

Provides:
- Thibos power-vector conversion (S, C, alpha <-> M, J0, J45)
- Symmetric 2D refractive power matrices and eigenvalue analysis
- Quadratic wavefront optical path difference (OPD) modeling
- Circular entrance pupil coordinate grids and aperture masking
- Optical phase calculation and complex generalized pupil functions
- Discrete FFT-compatible sampling grids and Nyquist criteria
- 2D Fraunhofer diffraction propagation
- Monochromatic Amplitude and Intensity Point Spread Functions (PSF)
- Optical Transfer Function (OTF), MTF, and PTF computation
- Analytical Airy disk and circular aperture MTF references
"""

from .fourier_optics import (
    DEFAULT_FOCAL_LENGTH_EYE,
    OTFResult,
    PSFResult,
    analytical_airy_psf,
    analytical_airy_zeros,
    analytical_diffraction_limited_mtf,
    compute_otf,
    compute_psf,
    fraunhofer_propagation,
    pupil_autocorrelation_otf,
)
from .power_vectors import (
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
from .pupil import (
    DEFAULT_WAVELENGTH_PHOTOPIC,
    PupilGrid,
    compute_wavefront_phase,
    create_pupil_grid,
    generalized_pupil_function,
)
from .sampling import (
    DEFAULT_SAFETY_FACTOR,
    DEFAULT_SPAN_FACTOR,
    FFTPupilGrid,
    compute_max_phase_gradient,
    compute_nyquist_grid_size,
    create_fft_pupil_grid,
    evaluate_phase_sampling,
    select_fft_grid_size,
)
from .synthetic_cases import (
    AnalyticalCase,
    get_canonical_synthetic_cases,
)
from .wavefront import (
    DEFAULT_SIGMA,
    quadratic_wavefront,
    seidel_wavefront_coefficients,
)

__all__ = [
    "DEFAULT_TOLERANCE",
    "DEFAULT_SIGMA",
    "DEFAULT_WAVELENGTH_PHOTOPIC",
    "DEFAULT_FOCAL_LENGTH_EYE",
    "DEFAULT_SPAN_FACTOR",
    "DEFAULT_SAFETY_FACTOR",
    "Prescription",
    "PowerVector",
    "prescription_to_power_vector",
    "power_vector_to_prescription",
    "construct_power_matrix",
    "meridional_power",
    "power_matrix_meridional_power",
    "decompose_power_matrix",
    "quadratic_wavefront",
    "seidel_wavefront_coefficients",
    "PupilGrid",
    "create_pupil_grid",
    "compute_wavefront_phase",
    "generalized_pupil_function",
    "AnalyticalCase",
    "get_canonical_synthetic_cases",
    "FFTPupilGrid",
    "create_fft_pupil_grid",
    "compute_max_phase_gradient",
    "compute_nyquist_grid_size",
    "select_fft_grid_size",
    "evaluate_phase_sampling",
    "PSFResult",
    "OTFResult",
    "fraunhofer_propagation",
    "compute_psf",
    "compute_otf",
    "analytical_airy_psf",
    "analytical_airy_zeros",
    "analytical_diffraction_limited_mtf",
    "pupil_autocorrelation_otf",
]
