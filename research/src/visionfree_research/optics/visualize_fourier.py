"""
visualize_fourier.py — Publication-Quality Visualization of Diffraction & Fourier Engine
Part of VISIONFREE Phase 5.2: Diffraction and Fourier Optics Engine.

Generates an 8-panel comprehensive scientific visualization:
1. Circular pupil transmission amplitude A(x_p, y_p).
2. Wavefront phase map phi(x_p, y_p) for an astigmatic eye (+1.50 DS / -3.00 DC x 75 deg).
3. Two-dimensional retinal Intensity Point Spread Function (PSF).
4. Logarithmic PSF image (log10(PSF / peak)), resolving diffraction rings.
5. Radial cross-section of the numerical Airy disk with analytical Bessel overlay.
6. Two-dimensional Optical Transfer Function (real component) showing contrast reversal lobes.
7. Modulation Transfer Function (MTF) radial cuts vs. spatial frequency in cycles/mm and cpd.
8. Numerical convergence study across grid resolutions (N = 64, 128, 256, 512).

Output:
    research/results/phase52/phase52_fourier_optics_demo.png (Git-ignored)

Scientific Notice:
    These plots represent numerical simulations of paraxial physical optics models
    under monochromatic Fraunhofer diffraction. They do NOT represent in-vivo
    human retinal measurements or clinical visual acuity.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Headless backend
import matplotlib.pyplot as plt
import numpy as np

from visionfree_research.optics.fourier_optics import (
    DEFAULT_FOCAL_LENGTH_EYE,
    DEFAULT_WAVELENGTH_PHOTOPIC,
    analytical_airy_psf,
    analytical_airy_zeros,
    analytical_diffraction_limited_mtf,
    compute_otf,
    compute_psf,
    fraunhofer_propagation,
)
from visionfree_research.optics.power_vectors import prescription_to_power_vector
from visionfree_research.optics.pupil import compute_wavefront_phase
from visionfree_research.optics.sampling import create_fft_pupil_grid
from visionfree_research.optics.wavefront import DEFAULT_SIGMA, quadratic_wavefront


def run_fourier_visualization(
    output_dir: str | Path = "research/results/phase52",
    dpi: int = 200,
) -> Path:
    """
    Generate and save the 8-panel Fourier optics demonstration figure.

    Args:
        output_dir: Target directory path.
        dpi: Export image resolution.

    Returns:
        Path to the saved figure file.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    fig_file = out_path / "phase52_fourier_optics_demo.png"

    # Base parameters
    r_p = 0.002           # 2.0 mm radius (4.0 mm pupil diameter)
    f_eye = DEFAULT_FOCAL_LENGTH_EYE  # 17 mm reduced eye focal length
    wl = DEFAULT_WAVELENGTH_PHOTOPIC  # 555 nm photopic peak
    n_samples = 256
    span_factor = 2.5     # Adequate linear autocorrelation support

    # 1. Setup clear unaberrated circular pupil for Airy disk evaluation
    grid_airy = create_fft_pupil_grid(radius=r_p, samples=n_samples, span_factor=span_factor)
    p_airy = np.where(grid_airy.mask, 1.0 + 0.0j, 0.0 + 0.0j)
    psf_airy_res = compute_psf(p_airy, grid_airy, focal_length=f_eye, wavelength=wl, pad_samples=512)
    otf_airy_res = compute_otf(psf_airy_res)

    # 2. Setup astigmatic pupil: +1.50 DS / -3.00 DC x 75 deg (Mixed Astigmatism)
    pv_astig = prescription_to_power_vector(sphere=1.50, cylinder=-3.00, axis=75.0)
    opd_astig = quadratic_wavefront(pv_astig, grid_airy.x, grid_airy.y, sigma=DEFAULT_SIGMA)
    phi_astig = compute_wavefront_phase(opd_astig, wavelength=wl)
    p_astig = np.where(grid_airy.mask, np.exp(1j * phi_astig), 0.0j)
    psf_astig_res = compute_psf(p_astig, grid_airy, focal_length=f_eye, wavelength=wl, pad_samples=512)
    otf_astig_res = compute_otf(psf_astig_res)

    # Create 4x2 subplot layout
    fig, axes = plt.subplots(4, 2, figsize=(14, 18), constrained_layout=True)

    # -------------------------------------------------------------
    # Panel 1: Circular Pupil Amplitude A(x_p, y_p)
    # -------------------------------------------------------------
    ax1 = axes[0, 0]
    extent_pupil_mm = [
        grid_airy.x[0, 0] * 1e3,
        grid_airy.x[0, -1] * 1e3,
        grid_airy.y[0, 0] * 1e3,
        grid_airy.y[-1, 0] * 1e3,
    ]
    im1 = ax1.imshow(
        np.abs(p_airy),
        extent=extent_pupil_mm,
        origin="lower",
        cmap="Blues_r",
        vmin=0.0,
        vmax=1.0,
    )
    circ1 = plt.Circle((0, 0), r_p * 1e3, color="navy", fill=False, linewidth=2, linestyle="--")
    ax1.add_patch(circ1)
    ax1.set_title(
        f"(1) Circular Pupil Transmission Amplitude $A(x_p, y_p)$\n"
        f"Dia: {2*r_p*1e3:.1f} mm, Window: {grid_airy.window_width*1e3:.1f} mm, $N={n_samples}$",
        fontsize=11,
        fontweight="bold",
    )
    ax1.set_xlabel("Pupil $x_p$ (mm)", fontsize=10)
    ax1.set_ylabel("Pupil $y_p$ (mm)", fontsize=10)
    cbar1 = fig.colorbar(im1, ax=ax1, fraction=0.046, pad=0.04)
    cbar1.set_label("Amplitude $A$", fontsize=9)

    # -------------------------------------------------------------
    # Panel 2: Wavefront Phase Map phi(x_p, y_p)
    # -------------------------------------------------------------
    ax2 = axes[0, 1]
    phi_wrapped = np.where(grid_airy.mask, (phi_astig + math.pi) % (2.0 * math.pi) - math.pi, np.nan)
    im2 = ax2.imshow(
        phi_wrapped,
        extent=extent_pupil_mm,
        origin="lower",
        cmap="twilight",
        vmin=-math.pi,
        vmax=+math.pi,
    )
    ax2.add_patch(plt.Circle((0, 0), r_p * 1e3, color="black", fill=False, linewidth=1.5, linestyle="--"))
    ax2.set_title(
        f"(2) Pupil Optical Phase Map $\\phi(x_p, y_p)$ (Wrapped $[-\\pi, +\\pi]$)\n"
        f"Mixed Astigmatism: $+1.50$ DS / $-3.00$ DC $\\times 75^\\circ$ ($\\lambda = {wl*1e9:.0f}$ nm)",
        fontsize=11,
        fontweight="bold",
    )
    ax2.set_xlabel("Pupil $x_p$ (mm)", fontsize=10)
    ax2.set_ylabel("Pupil $y_p$ (mm)", fontsize=10)
    cbar2 = fig.colorbar(im2, ax=ax2, fraction=0.046, pad=0.04)
    cbar2.set_label("Phase (rad)", fontsize=9)

    # -------------------------------------------------------------
    # Panel 3: 2D Retinal Intensity PSF
    # -------------------------------------------------------------
    ax3 = axes[1, 0]
    # Zoom into central +/- 30 micrometers
    crop_um = 30.0
    x_um = psf_astig_res.x * 1e6
    y_um = psf_astig_res.y * 1e6
    crop_mask_x = np.abs(x_um) <= crop_um
    crop_mask_y = np.abs(y_um) <= crop_um
    psf_astig_crop = psf_astig_res.psf[np.ix_(crop_mask_y, crop_mask_x)]
    extent_psf_um = [-crop_um, crop_um, -crop_um, crop_um]

    im3 = ax3.imshow(
        psf_astig_crop / np.max(psf_astig_crop),
        extent=extent_psf_um,
        origin="lower",
        cmap="inferno",
        vmin=0.0,
        vmax=1.0,
    )
    ax3.set_title(
        f"(3) 2D Retinal Intensity PSF (Normalized)\n"
        f"Astigmatic Focal Blur ($f = {f_eye*1e3:.0f}$ mm, $\\Delta x_i = {psf_astig_res.dx*1e6:.2f}\\,\\mu$m)",
        fontsize=11,
        fontweight="bold",
    )
    ax3.set_xlabel("Retinal $x_i$ ($\\mu$m)", fontsize=10)
    ax3.set_ylabel("Retinal $y_i$ ($\\mu$m)", fontsize=10)
    cbar3 = fig.colorbar(im3, ax=ax3, fraction=0.046, pad=0.04)
    cbar3.set_label("Relative Irradiance", fontsize=9)

    # -------------------------------------------------------------
    # Panel 4: Logarithmic PSF Image (Airy Rings)
    # -------------------------------------------------------------
    ax4 = axes[1, 1]
    x_airy_um = psf_airy_res.x * 1e6
    crop_airy_mask = np.abs(x_airy_um) <= 25.0
    psf_airy_crop = psf_airy_res.psf[np.ix_(crop_airy_mask, crop_airy_mask)]
    extent_airy_um = [-25.0, 25.0, -25.0, 25.0]

    # Log10 scale down to 4 decades (-4.0)
    log_psf = np.log10(np.clip(psf_airy_crop / np.max(psf_airy_crop), 1e-4, 1.0))
    im4 = ax4.imshow(
        log_psf,
        extent=extent_airy_um,
        origin="lower",
        cmap="magma",
        vmin=-4.0,
        vmax=0.0,
    )
    ax4.set_title(
        f"(4) Logarithmic PSF Image: $\\log_{{10}}(\\mathrm{{PSF}} / \\mathrm{{PSF}}_{{\\max}})$\n"
        f"Diffraction-Limited Airy Pattern (4 Decades Dynamic Range)",
        fontsize=11,
        fontweight="bold",
    )
    ax4.set_xlabel("Retinal $x_i$ ($\\mu$m)", fontsize=10)
    ax4.set_ylabel("Retinal $y_i$ ($\\mu$m)", fontsize=10)
    cbar4 = fig.colorbar(im4, ax=ax4, fraction=0.046, pad=0.04)
    cbar4.set_label("$\\log_{10}$ Relative Intensity", fontsize=9)

    # -------------------------------------------------------------
    # Panel 5: Airy Radial Cross-Section vs. Analytical Bessel Overlay
    # -------------------------------------------------------------
    ax5 = axes[2, 0]
    c_idx = len(psf_airy_res.y) // 2
    r_pts_um = psf_airy_res.x[c_idx:] * 1e6
    line_num = psf_airy_res.psf[c_idx, c_idx:] / psf_airy_res.peak_intensity

    # Analytical Bessel curve
    r_dense_m = np.linspace(0, 20e-6, 500)
    r_dense_um = r_dense_m * 1e6
    line_ana = analytical_airy_psf(radius_or_diameter=r_p, focal_length=f_eye, wavelength=wl, r_image=r_dense_m)

    zeros = analytical_airy_zeros(r_p, f_eye, wl)
    r1_um = zeros["r_first_zero_m"] * 1e6

    ax5.plot(r_dense_um, line_ana, "k-", linewidth=2.0, label="Analytical Bessel $[2 J_1(u)/u]^2$")
    ax5.plot(r_pts_um[:45], line_num[:45], "ro", markersize=3.5, alpha=0.8, label="Numerical Fraunhofer FFT")
    ax5.axvline(r1_um, color="blue", linestyle="--", linewidth=1.2, label=f"1st Dark Ring ($r_1 = {r1_um:.2f}\\,\\mu$m)")
    ax5.set_xlim(0, 15.0)
    ax5.set_ylim(-0.02, 1.05)
    ax5.set_title(
        "(5) Airy Radial Cross-Section vs. Analytical Bessel Reference\n"
        f"First Dark Ring Zero: $1.22 \\lambda f / D = {r1_um:.2f}\\,\\mu$m",
        fontsize=11,
        fontweight="bold",
    )
    ax5.set_xlabel("Radial Distance from Axis $r_i$ ($\\mu$m)", fontsize=10)
    ax5.set_ylabel("Normalized Intensity $I(r) / I_0$", fontsize=10)
    ax5.legend(loc="upper right", fontsize=8.5)
    ax5.grid(True, linestyle=":", alpha=0.6)

    # -------------------------------------------------------------
    # Panel 6: 2D Optical Transfer Function (Real Part)
    # -------------------------------------------------------------
    ax6 = axes[2, 1]
    # Spatial frequency in cycles/mm
    fx_cpmm = otf_astig_res.fx * 1e-3
    fy_cpmm = otf_astig_res.fy * 1e-3
    extent_otf_cpmm = [fx_cpmm[0], fx_cpmm[-1], fy_cpmm[0], fy_cpmm[-1]]

    im6 = ax6.imshow(
        otf_astig_res.real,
        extent=extent_otf_cpmm,
        origin="lower",
        cmap="coolwarm",
        vmin=-0.2,
        vmax=1.0,
    )
    ax6.set_title(
        f"(6) 2D Optical Transfer Function $\\mathrm{{Re}}\\{{\\mathrm{{OTF}}(f_x, f_y)\\}}$\n"
        f"Shows Contrast Reversal Lobes (Blue Negative Regions)",
        fontsize=11,
        fontweight="bold",
    )
    ax6.set_xlabel("Spatial Frequency $f_x$ (cycles/mm)", fontsize=10)
    ax6.set_ylabel("Spatial Frequency $f_y$ (cycles/mm)", fontsize=10)
    cbar6 = fig.colorbar(im6, ax=ax6, fraction=0.046, pad=0.04)
    cbar6.set_label("$\\mathrm{Re}\\{\\mathrm{OTF}\\}$", fontsize=9)

    # -------------------------------------------------------------
    # Panel 7: MTF Frequency Response vs. Spatial Frequency
    # -------------------------------------------------------------
    ax7 = axes[3, 0]
    c_otf = len(otf_airy_res.fy) // 2
    freq_cpd = otf_airy_res.fx_cpd[c_otf:]
    mtf_airy_cut = otf_airy_res.mtf[c_otf, c_otf:]
    mtf_astig_cut_x = otf_astig_res.mtf[c_otf, c_otf:]
    mtf_astig_cut_y = otf_astig_res.mtf[c_otf:, c_otf]

    f_cut_cpd = otf_airy_res.cutoff_frequency_cpd

    ax7.plot(freq_cpd, mtf_airy_cut, "k-", linewidth=2.0, label="Diffraction-Limited (Analytical)")
    ax7.plot(freq_cpd, mtf_astig_cut_x, "b-", linewidth=1.5, label="Astigmatic $+1.50/-3.00\\times 75^\\circ$ ($f_x$)")
    ax7.plot(freq_cpd, mtf_astig_cut_y, "r--", linewidth=1.5, label="Astigmatic $+1.50/-3.00\\times 75^\\circ$ ($f_y$)")
    ax7.axvline(60.0, color="gray", linestyle=":", label="Human Foveal Nyquist (~60 cpd)")
    ax7.set_xlim(0, min(120.0, f_cut_cpd))
    ax7.set_ylim(-0.02, 1.05)
    ax7.set_title(
        f"(7) Modulation Transfer Function (MTF) Frequency Response\n"
        f"Diffraction Cutoff: $f_c = {f_cut_cpd:.1f}$ cpd ($D/\\lambda = {r_p*2/wl*math.pi/180:.1f}$ cpd)",
        fontsize=11,
        fontweight="bold",
    )
    ax7.set_xlabel("Visual Spatial Frequency (cycles / degree)", fontsize=10)
    ax7.set_ylabel(r"Modulation Transfer $|\mathrm{OTF}| \geq 0$", fontsize=10)
    ax7.legend(loc="upper right", fontsize=8.5)
    ax7.grid(True, linestyle=":", alpha=0.6)

    # -------------------------------------------------------------
    # Panel 8: Numerical Sampling Convergence Study
    # -------------------------------------------------------------
    ax8 = axes[3, 1]
    resolutions = [64, 128, 256, 512, 1024]
    errors_discrete_r1_pct = []
    errors_spline_r1_pct = []
    area_errors_pct = []
    a_cont = math.pi * (r_p ** 2)

    from scipy.interpolate import CubicSpline
    from scipy.optimize import root_scalar

    for n_res in resolutions:
        # Physical pupil window L = 8 mm; use 4x zero-padding (L_pad = 32 mm)
        # to ensure uniform focal plane sampling pitch dx_i = 0.292 um across all N
        n_pad = n_res * 4
        grid_conv = create_fft_pupil_grid(radius=r_p, samples=n_res, span_factor=2.0)
        p_conv = np.where(grid_conv.mask, 1.0 + 0.0j, 0.0 + 0.0j)

        # Discrete pupil area error before normalization
        disc_area = float(np.sum(np.abs(p_conv) ** 2) * (grid_conv.dx ** 2))
        area_err = abs(disc_area - a_cont) / a_cont * 100.0
        area_errors_pct.append(area_err)

        field_conv, x_c, y_c, dx_c, dy_c = fraunhofer_propagation(
            p_conv, grid_conv, pad_samples=n_pad, wavelength=wl, focal_length=f_eye
        )
        c_k = n_pad // 2
        cut_conv = np.abs(field_conv[c_k, c_k:]) ** 2
        r_c = x_c[c_k:]

        diffs = np.diff(cut_conv)
        first_min_indices = np.where(diffs > 0)[0]
        if len(first_min_indices) > 0:
            idx = first_min_indices[0]
            r1_disc = r_c[idx]
            err_disc = abs(r1_disc - zeros["r_first_zero_m"]) / zeros["r_first_zero_m"] * 100.0

            # Subpixel cubic spline root of derivative
            cs = CubicSpline(r_c[:idx + 5], cut_conv[:idx + 5])
            try:
                sol = root_scalar(cs.derivative(), bracket=[r_c[max(0, idx - 1)], r_c[min(len(r_c) - 1, idx + 1)]])
                r1_spline = sol.root
                err_spline = abs(r1_spline - zeros["r_first_zero_m"]) / zeros["r_first_zero_m"] * 100.0
            except Exception:
                err_spline = err_disc
        else:
            err_disc = 0.0
            err_spline = 0.0

        errors_discrete_r1_pct.append(err_disc)
        errors_spline_r1_pct.append(err_spline)

    ax8.plot(resolutions, area_errors_pct, "g^--", linewidth=1.5, markersize=5, label=r"Aperture Area Error vs $\pi r_p^2$ (%)")
    ax8.plot(resolutions, errors_discrete_r1_pct, "rs:", linewidth=1.5, markersize=5, label=r"Airy 1st Zero Nearest Pixel (%)")
    ax8.plot(resolutions, errors_spline_r1_pct, "bo-", linewidth=2.0, markersize=6, label=r"Airy 1st Zero Spline Root (%)")
    ax8.set_xscale("log", base=2)
    ax8.set_yscale("log")
    ax8.set_xticks(resolutions)
    ax8.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
    ax8.set_title(
        "(8) Numerical Convergence & Discretization Audit\n"
        r"Discretization Quantization vs. Subpixel Wave Convergence",
        fontsize=11,
        fontweight="bold",
    )
    ax8.set_xlabel("Pupil Grid Resolution $N$ (samples / axis)", fontsize=10)
    ax8.set_ylabel("Relative Error (%) [Log Scale]", fontsize=10)
    ax8.legend(loc="upper right", fontsize=8.0)
    ax8.grid(True, which="both", linestyle=":", alpha=0.6)

    # Super-title with scientific disclaimer
    fig.suptitle(
        "VISIONFREE Phase 5.2 — Monochromatic Diffraction & Fourier Optics Engine\n"
        "Scalar Fraunhofer Diffraction, Point Spread Function & Optical Transfer Function Modeling",
        fontsize=13,
        fontweight="bold",
    )

    fig.savefig(fig_file, dpi=dpi)
    plt.close(fig)
    return fig_file


if __name__ == "__main__":
    saved_path = run_fourier_visualization()
    print(f"Phase 5.2 Fourier optics visualization saved successfully at: {saved_path}")
