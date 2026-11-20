"""
visualize_wavefront.py — Scientific Visualization of Phase 5.1 Optics Engine
Part of VISIONFREE Phase 5.1: Mathematical Foundation.

Generates a 4-panel demonstration plot:
1. Circular entrance pupil aperture grid with physical dimensions.
2. Pure spherical defocus quadratic wavefront OPD map (W in micrometers).
3. Astigmatic quadratic wavefront OPD map (hyperbolic saddle in micrometers).
4. Optical phase map (phi in radians at lambda = 555 nm).

Output is saved to:
    research/results/phase51/phase51_wavefront_demo.png

Scientific Disclaimer:
    This is an offline visualization of mathematical wavefront models.
    It does NOT simulate retinal image formation or actual human visual perception.
"""

from __future__ import annotations

import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # Headless backend for batch/automated execution
import matplotlib.pyplot as plt
import numpy as np

from visionfree_research.optics.power_vectors import prescription_to_power_vector
from visionfree_research.optics.pupil import (
    DEFAULT_WAVELENGTH_PHOTOPIC,
    compute_wavefront_phase,
    create_pupil_grid,
)
from visionfree_research.optics.wavefront import DEFAULT_SIGMA, quadratic_wavefront


def run_visualization(
    output_dir: str | Path = "research/results/phase51",
    dpi: int = 200,
) -> Path:
    """
    Generate and save the 4-panel mathematical visualization figure.

    Args:
        output_dir: Destination directory (created if non-existent).
        dpi: Resolution of exported PNG figure.

    Returns:
        Path to the saved figure file.
    """
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    fig_file = out_path / "phase51_wavefront_demo.png"

    # Setup 4.0 mm entrance pupil (radius = 2.0 mm = 0.002 m) on a 256x256 grid
    pupil_radius = 0.002  # meters (2 mm)
    grid_samples = 256
    pupil = create_pupil_grid(radius=pupil_radius, samples=grid_samples, span_factor=1.2)

    # Convert coordinates to millimeters for plotting
    x_mm = pupil.x * 1e3
    y_mm = pupil.y * 1e3

    # 1. Pure Spherical Myopia: S = -2.00 D, C = 0.00 D
    pv_sphere = prescription_to_power_vector(sphere=-2.00, cylinder=0.00)
    opd_sphere = quadratic_wavefront(pv_sphere, pupil.x, pupil.y, sigma=DEFAULT_SIGMA)
    # Mask outside pupil for clean aperture visualization
    opd_sphere_masked = np.where(pupil.mask, opd_sphere * 1e6, np.nan)  # micrometers

    # 2. Astigmatic Case: S = +1.50 D, C = -3.00 D, Axis = 75 deg (Mixed Astigmatism)
    pv_astig = prescription_to_power_vector(sphere=1.50, cylinder=-3.00, axis=75.0)
    opd_astig = quadratic_wavefront(pv_astig, pupil.x, pupil.y, sigma=DEFAULT_SIGMA)
    opd_astig_masked = np.where(pupil.mask, opd_astig * 1e6, np.nan)  # micrometers

    # 3. Phase Map for Astigmatic Wavefront (lambda = 555 nm)
    phase_astig = compute_wavefront_phase(opd_astig, wavelength=DEFAULT_WAVELENGTH_PHOTOPIC)
    # Wrap to [-pi, pi] for fringe visualization
    phase_astig_wrapped = (phase_astig + math.pi) % (2.0 * math.pi) - math.pi
    phase_astig_masked = np.where(pupil.mask, phase_astig_wrapped, np.nan)

    # Create 2x2 subplot figure
    fig, axes = plt.subplots(2, 2, figsize=(12, 11), constrained_layout=True)

    # -------------------------------------------------------------
    # Panel (a): Circular Pupil Aperture
    # -------------------------------------------------------------
    ax_a = axes[0, 0]
    extent_mm = [x_mm[0, 0], x_mm[0, -1], y_mm[0, 0], y_mm[-1, 0]]
    im_a = ax_a.imshow(
        pupil.mask.astype(float),
        extent=extent_mm,
        origin="lower",
        cmap="Blues",
        vmin=0.0,
        vmax=1.0,
    )
    # Draw pupil perimeter
    circle = plt.Circle((0, 0), pupil_radius * 1e3, color="navy", fill=False, linewidth=2, linestyle="--")
    ax_a.add_patch(circle)
    ax_a.axhline(0, color="gray", linestyle=":", alpha=0.6)
    ax_a.axvline(0, color="gray", linestyle=":", alpha=0.6)
    ax_a.set_title(
        f"(a) Circular Entrance Pupil Aperture\n"
        f"Radius $r_p = {pupil_radius*1e3:.1f}$ mm (Dia: {2*pupil_radius*1e3:.1f} mm), $N={grid_samples}$",
        fontsize=11,
        fontweight="bold",
    )
    ax_a.set_xlabel("Pupil $x$ (mm)", fontsize=10)
    ax_a.set_ylabel("Pupil $y$ (mm)", fontsize=10)
    cbar_a = fig.colorbar(im_a, ax=ax_a, fraction=0.046, pad=0.04)
    cbar_a.set_label("Pupil Transmission $A(x, y)$", fontsize=9)

    # -------------------------------------------------------------
    # Panel (b): Pure Defocus Wavefront OPD (S = -2.00 D)
    # -------------------------------------------------------------
    ax_b = axes[0, 1]
    im_b = ax_b.imshow(
        opd_sphere_masked,
        extent=extent_mm,
        origin="lower",
        cmap="coolwarm",
    )
    ax_b.add_patch(plt.Circle((0, 0), pupil_radius * 1e3, color="black", fill=False, linewidth=1.5, linestyle="--"))
    ax_b.axhline(0, color="gray", linestyle=":", alpha=0.6)
    ax_b.axvline(0, color="gray", linestyle=":", alpha=0.6)
    ax_b.set_title(
        f"(b) Pure Spherical Defocus OPD ($W$)\n"
        f"Prescription: $-2.00$ DS / $0.00$ DC (Sign $\\sigma = {DEFAULT_SIGMA:+.1f}$)",
        fontsize=11,
        fontweight="bold",
    )
    ax_b.set_xlabel("Pupil $x$ (mm)", fontsize=10)
    ax_b.set_ylabel("Pupil $y$ (mm)", fontsize=10)
    cbar_b = fig.colorbar(im_b, ax=ax_b, fraction=0.046, pad=0.04)
    cbar_b.set_label("Wavefront OPD $W$ ($\\mu$m)", fontsize=9)

    # -------------------------------------------------------------
    # Panel (c): Astigmatic Wavefront OPD (+1.50 / -3.00 x 75)
    # -------------------------------------------------------------
    ax_c = axes[1, 0]
    im_c = ax_c.imshow(
        opd_astig_masked,
        extent=extent_mm,
        origin="lower",
        cmap="viridis",
    )
    ax_c.add_patch(plt.Circle((0, 0), pupil_radius * 1e3, color="black", fill=False, linewidth=1.5, linestyle="--"))
    # Plot principal meridian axes (75 deg and 165 deg)
    ax_len = pupil_radius * 1e3
    ax_c.plot(
        [-ax_len * math.cos(math.radians(75)), ax_len * math.cos(math.radians(75))],
        [-ax_len * math.sin(math.radians(75)), ax_len * math.sin(math.radians(75))],
        color="white",
        linestyle="-",
        linewidth=1.5,
        label="Axis $75^\\circ$ ($+1.50$ D)",
    )
    ax_c.plot(
        [-ax_len * math.cos(math.radians(165)), ax_len * math.cos(math.radians(165))],
        [-ax_len * math.sin(math.radians(165)), ax_len * math.sin(math.radians(165))],
        color="red",
        linestyle="-",
        linewidth=1.5,
        label="Axis $165^\\circ$ ($-1.50$ D)",
    )
    ax_c.legend(loc="upper right", fontsize=8)
    ax_c.set_title(
        f"(c) Astigmatic Wavefront OPD ($W$)\n"
        f"Prescription: $+1.50$ DS / $-3.00$ DC $\\times 75^\\circ$ (Toric Saddle)",
        fontsize=11,
        fontweight="bold",
    )
    ax_c.set_xlabel("Pupil $x$ (mm)", fontsize=10)
    ax_c.set_ylabel("Pupil $y$ (mm)", fontsize=10)
    cbar_c = fig.colorbar(im_c, ax=ax_c, fraction=0.046, pad=0.04)
    cbar_c.set_label("Wavefront OPD $W$ ($\\mu$m)", fontsize=9)

    # -------------------------------------------------------------
    # Panel (d): Optical Phase Map (Wrapped at lambda = 555 nm)
    # -------------------------------------------------------------
    ax_d = axes[1, 1]
    im_d = ax_d.imshow(
        phase_astig_masked,
        extent=extent_mm,
        origin="lower",
        cmap="twilight",
        vmin=-math.pi,
        vmax=+math.pi,
    )
    ax_d.add_patch(plt.Circle((0, 0), pupil_radius * 1e3, color="black", fill=False, linewidth=1.5, linestyle="--"))
    ax_d.set_title(
        f"(d) Optical Phase Map $\\phi(x, y) \\,(\\mathrm{{mod}}\\,2\\pi)$\n"
        f"Photopic $\\lambda = {DEFAULT_WAVELENGTH_PHOTOPIC*1e9:.0f}$ nm, $\\phi = 2\\pi W / \\lambda$",
        fontsize=11,
        fontweight="bold",
    )
    ax_d.set_xlabel("Pupil $x$ (mm)", fontsize=10)
    ax_d.set_ylabel("Pupil $y$ (mm)", fontsize=10)
    cbar_d = fig.colorbar(im_d, ax=ax_d, fraction=0.046, pad=0.04)
    cbar_d.set_label("Wrapped Phase $\\phi$ (radians)", fontsize=9)

    # Super-title with scientific disclaimer
    fig.suptitle(
        "VISIONFREE Phase 5.1 — Ophthalmic Power Vector & Wavefront Mathematics Engine\n"
        "Mathematical Model Demonstration (Not a Simulation of Retinal Visual Perception)",
        fontsize=13,
        fontweight="bold",
    )

    fig.savefig(fig_file, dpi=dpi)
    plt.close(fig)
    return fig_file


if __name__ == "__main__":
    saved_file = run_visualization()
    print(f"Phase 5.1 visualization generated successfully at: {saved_file}")
