# VISIONFREE Phase 5.1: Ophthalmic Power Vector & Wavefront Mathematics Engine
## Scientific Foundations, Coordinate Systems, and Mathematical Derivations

**Document Version:** `1.0.0`  
**Date:** November 2026  
**Status:** Completed & Empirically Verified (50/50 tests passing in Python 3.14 & Python 3.9)  
**Author:** VISIONFREE Computational Optics & Scientific Computing Research Group  
**Parent Workspace:** `VISIONFREE/research/`

---

## 1. Introduction and Architectural Scope

This document provides the theoretical framework, mathematical derivations, coordinate conventions, and analytical validations for **Phase 5.1** of the VISIONFREE project.

Phase 5.1 establishes the lower-order paraxial mathematical engine for refractive error modeling, bridging classical clinical sphero-cylindrical prescriptions with modern physical wavefront optics.

```
Clinical Prescription (S, C, α)
               │
               ▼  [Thibos Decomposition]
     Power Vector (M, J0, J45)
               │
               ▼  [2D Quadratic Tensor Form]
       Power Matrix F (2x2)
               │
               ▼  [Physical Pupil Coordinates]
  Quadratic Wavefront OPD: W(x, y) [meters]
               │
               ▼  [Wavelength Scaling]
     Optical Phase Map: φ(x, y) [radians]
               │
               ▼  [Aperture Boundary Conditions]
 Complex Generalized Pupil Function: P(x, y)
```

> [!IMPORTANT]
> **Strict Phase 5.1 Boundaries:**  
> This module provides the **mathematical foundation only**. It does **not** compute Fourier propagation, point spread functions (PSF), optical transfer functions (OTF), modulation transfer functions (MTF), forward blur simulations, inverse filtering (Wiener, Tikhonov, Richardson–Lucy), or browser extension integrations. Those capabilities are deferred to Phase 5.2 and subsequent phases.

---

## 2. Clinical Prescription Notation & Ophthalmic Transposition

A conventional clinical refraction describes the paraxial refractive correction of an eye using three parameters:

1. **Sphere ($S$ or $\text{SPH}$):** Spherical refractive power in diopters ($\text{D} = \text{m}^{-1}$). Represents symmetric focal power across all meridians.
2. **Cylinder ($C$ or $\text{CYL}$):** Astigmatic refractive power difference between the two principal orthogonal meridians in diopters ($\text{D}$).
3. **Axis ($\alpha$):** Meridian angle of the cylinder axis in degrees, traditionally oriented between $0^\circ$ and $180^\circ$. By optical convention, the cylinder provides **zero refractive power along its axis** ($\theta = \alpha$) and **maximum cylinder power along the perpendicular meridian** ($\theta = \alpha + 90^\circ$).

### 2.1 Minus-Cylinder vs. Plus-Cylinder Conventions

Optometry and ophthalmology employ two alternative representations for the exact same physical lens:

- **Minus-Cylinder Convention ($C \le 0$):** Standard in modern optometric practice and spectacle dispensing:
  $$\text{Power along } \alpha = S, \quad \text{Power along } (\alpha + 90^\circ) = S + C$$
- **Plus-Cylinder Convention ($C \ge 0$):** Historically common in ophthalmic surgery and anterior segment topography.

### 2.2 Exact Ophthalmic Transposition

The mathematical conversion between plus-cylinder and minus-cylinder representations is given by:

$$\begin{aligned}
S_{\text{trans}} &= S + C \\
C_{\text{trans}} &= -C \\
\alpha_{\text{trans}} &= (\alpha + 90^\circ) \pmod{180^\circ}
\end{aligned}$$

*Invariance Property:* Although the numerical parameters change drastically (e.g., $-1.00\text{ DS} / -2.00\text{ DC} \times 30^\circ$ transposes to $-3.00\text{ DS} / +2.00\text{ DC} \times 120^\circ$), the physical dioptric lens power across every spatial meridian is identical.

---

## 3. Thibos Power-Vector Representation

Sphero-cylindrical notation cannot be directly manipulated using standard linear algebra because the cylindrical axis $\alpha$ is a circular directional variable with non-linear periodicity ($180^\circ$), introducing coordinate singularities at $C = 0$.

In their seminal work, **Thibos, Wheeler, and Horner (1997)** applied Fourier analysis to directional refractive power, decomposing any sphero-cylindrical prescription into an orthonormal 3D power vector $\mathbf{v} = [M, J_0, J_{45}]^T$:

$$\begin{aligned}
M &= S + \frac{C}{2} &&\text{[Mean Spherical Equivalent power, Diopters]} \\
J_0 &= -\frac{C}{2} \cos(2\alpha) &&\text{[Jackson Cross-Cylinder at } 0^\circ/90^\circ\text{, Diopters]} \\
J_{45} &= -\frac{C}{2} \sin(2\alpha) &&\text{[Jackson Cross-Cylinder at } 45^\circ/135^\circ\text{, Diopters]}
\end{aligned}$$

where the angle $\alpha$ is converted to radians ($\alpha_{\text{rad}} = \alpha \times \frac{\pi}{180}$) before evaluating the trigonometric functions.

### 3.1 Astigmatic Vector Invariants

1. **Overall Astigmatic Vector Magnitude ($B$):**
   $$B = \sqrt{J_0^2 + J_{45}^2} = \frac{|C|}{2} \quad [\text{Diopters}]$$
2. **Total Dioptric Vector Length ($\|\mathbf{v}\|$):**
   $$\|\mathbf{v}\| = \sqrt{M^2 + J_0^2 + J_{45}^2} \quad [\text{Diopters}]$$
3. **Transposition Invariance:**
   Both $(S, C, \alpha)$ and its transposed counterpart $(S+C, -C, \alpha \pm 90^\circ)$ yield **identical** $[M, J_0, J_{45}]^T$ vectors. This eliminates the artificial ambiguity between plus and minus cylinder notations.

---

## 4. Meridional Power & 2D Refractive Power Matrix

### 4.1 Meridional Power Equation

The refractive power $F(\theta)$ along an arbitrary spatial meridian at angle $\theta$ (measured counter-clockwise from the horizontal $x$-axis) is given by the exact Fourier expansion:

$$F(\theta) = M + J_0 \cos(2\theta) + J_{45} \sin(2\theta) \quad [\text{Diopters}]$$

### 4.2 The Symmetric 2D Dioptric Power Matrix ($\mathbf{F}$)

In Cartesian pupil coordinates, refraction behaves as a symmetric second-order 2D tensor represented by the dioptric power matrix $\mathbf{F}$:

$$\mathbf{F} = \begin{bmatrix} M + J_0 & J_{45} \\ J_{45} & M - J_0 \end{bmatrix} \quad [\text{Diopters}]$$

### 4.3 Quadratic Form Equivalence

Let $\mathbf{e}(\theta) = [\cos\theta, \sin\theta]^T$ denote a unit direction vector along meridian $\theta$. The meridional refractive power is given identically by the quadratic form:

$$F(\theta) = \mathbf{e}(\theta)^T \mathbf{F} \, \mathbf{e}(\theta)$$

*Proof:*
$$\begin{aligned}
\mathbf{e}(\theta)^T \mathbf{F} \, \mathbf{e}(\theta) &= \begin{bmatrix} \cos\theta & \sin\theta \end{bmatrix} \begin{bmatrix} M + J_0 & J_{45} \\ J_{45} & M - J_0 \end{bmatrix} \begin{bmatrix} \cos\theta \\ \sin\theta \end{bmatrix} \\
&= (M + J_0)\cos^2\theta + 2 J_{45}\cos\theta\sin\theta + (M - J_0)\sin^2\theta \\
&= M(\cos^2\theta + \sin^2\theta) + J_0(\cos^2\theta - \sin^2\theta) + J_{45}(2\sin\theta\cos\theta) \\
&= M + J_0 \cos(2\theta) + J_{45} \sin(2\theta) = F(\theta). \quad \blacksquare
\end{aligned}$$

### 4.4 Matrix Invariants and Eigenvalue Analysis

The 2D power matrix $\mathbf{F}$ possesses fundamental linear algebraic invariants:

1. **Trace:** $\operatorname{Tr}(\mathbf{F}) = (M + J_0) + (M - J_0) = 2M$ (Twice the spherical equivalent).
2. **Determinant:** $\det(\mathbf{F}) = (M + J_0)(M - J_0) - J_{45}^2 = M^2 - (J_0^2 + J_{45}^2) = M^2 - B^2$.
3. **Characteristic Equation:**
   $$\lambda^2 - \operatorname{Tr}(\mathbf{F})\lambda + \det(\mathbf{F}) = \lambda^2 - 2M\lambda + (M^2 - B^2) = 0$$
4. **Eigenvalues (Principal Meridional Powers):**
   $$\lambda_1 = M + B = M + \frac{|C|}{2}, \qquad \lambda_2 = M - B = M - \frac{|C|}{2}$$

In canonical minus-cylinder notation ($C \le 0$, where $B = -C/2$):
$$\lambda_1 = S, \qquad \lambda_2 = S + C$$
The two eigenvalues of the matrix $\mathbf{F}$ correspond **exactly** to the powers along the two principal orthogonal meridians of the eye!

---

## 5. Quadratic Wavefront and Optical Path Difference (OPD)

### 5.1 Physical Pupil Plane Coordinates

Let $(x, y)$ denote physical Cartesian coordinates in the ocular entrance pupil plane measured in **meters** ($m$), with $(0, 0)$ located strictly at the pupil center:
- $+x$: Horizontal axis (nasal/temporal depending on eye).
- $+y$: Vertical axis (superior).

### 5.2 Wavefront OPD Formulation

The Optical Path Difference $W(x, y)$ represents the optical distance deviation between the aberrated ocular wavefront and a paraxial spherical reference wave converging on the retinal fovea:

$$W(x, y) = \frac{\sigma}{2} \begin{bmatrix} x & y \end{bmatrix} \mathbf{F} \begin{bmatrix} x \\ y \end{bmatrix} \quad [\text{meters}]$$

Expanding using the components of $\mathbf{F}$:

$$W(x, y) = \frac{\sigma}{2} \left[ (M + J_0)x^2 + 2 J_{45}xy + (M - J_0)y^2 \right] \quad [\text{meters}]$$

In polar coordinates ($x = r\cos\theta, y = r\sin\theta$):
$$W(r, \theta) = \frac{\sigma}{2} r^2 F(\theta) \quad [\text{meters}]$$

### 5.3 Dimensional Verification

- $[x] = [y] = \text{meters}$ ($\text{m}$)
- $[M] = [J_0] = [J_{45}] = \text{diopters} = \text{m}^{-1}$
- $[W(x, y)] = \text{m}^{-1} \cdot \text{m}^2 = \text{meters}$ ($\text{m}$). Dimensionally exact.

### 5.4 Sign Convention Parameter ($\sigma$)

In optical literature, the sign of wavefront error versus optical path difference depends on whether the wavefront is referenced to phase advance or phase delay:

- **$\sigma = +1.0$ (Default in VISIONFREE):** Optical Path Difference (OPD) lead convention. Consistent with Section 5.3 of `PHASE5_RESEARCH_PLAN.md`. Under this convention, positive dioptric power ($M > 0$, hyperopic defocus where ray vergence is convergent) causes positive optical path length ($W > 0$).
- **$\sigma = -1.0$:** Wavefront aberration delay convention (wavefront lagging behind the reference sphere).

Our implementation explicitly parameterizes $\sigma$, defaults to $+1.0$, and verifies that $W(x, y; \sigma=-1.0) = -W(x, y; \sigma=+1.0)$.

### 5.5 Classical Seidel Aberration Coefficients

For a circular pupil of radius $r_p$ (meters), the quadratic wavefront relates to Seidel lower-order aberrations:
$$\begin{aligned}
W_{20} &= \frac{\sigma}{2} r_p^2 M \quad &&\text{[Defocus coefficient, meters]} \\
W_{22} &= \frac{\sigma}{2} r_p^2 B = \frac{\sigma}{4} r_p^2 |C| \quad &&\text{[Astigmatism coefficient, meters]}
\end{aligned}$$

---

## 6. Circular Pupil Coordinate Systems

### 6.1 Coordinate Normalization

For an entrance pupil of physical radius $r_p = D_p / 2$ meters:

- Normalized dimensionless Cartesian coordinates:
  $$u = \frac{x}{r_p}, \quad v = \frac{y}{r_p}$$
- Normalized radial coordinate:
  $$\rho = \sqrt{u^2 + v^2} = \frac{\sqrt{x^2 + y^2}}{r_p}$$
- Azimuthal coordinate:
  $$\theta = \operatorname{atan2}(y, x) \quad [-\pi, \pi]$$

### 6.2 Circular Aperture Mask

The pupil transmission boundary is defined by the sharp step function:
$$\operatorname{Mask}(x, y) = \begin{cases} 
1 & \text{if } \rho \le 1.0 \quad (\sqrt{x^2 + y^2} \le r_p) \\
0 & \text{if } \rho > 1.0 \quad (\text{outside pupil aperture})
\end{cases}$$

### 6.3 Grid Discretization: Odd vs. Even Sampling & FFT Phase-Tilt Trade-offs

A critical nuance in discrete computational optics is the choice of sample count $N$:

1. **Odd Grid Samples ($N$ is odd, e.g., $N = 255, 257, 513$):**
   - **Exact Center Vertex:** Index $(N-1)/2$ evaluates analytically to $(x, y) = (0.0, 0.0)$.
   - **Perfect Origin Symmetry:** Positive and negative coordinate intervals are strictly mirrored ($[-K \cdot dx, \dots, 0, \dots, +K \cdot dx]$).
   - **Zero Phase Tilt:** The optical axis falls on an exact sampled vertex, preventing sub-pixel interpolation phase tilts in optical transfer functions.
   - **FFT Overhead:** Non-power-of-two odd sizes do not exploit radix-2 Cooley–Tukey FFT shortcuts (though mixed-radix or Chirp-Z transforms handle composite odds efficiently).

2. **Even Grid Samples ($N$ is even, e.g., $N = 256, 512, 1024$):**
   - **Half-Pixel Origin Offset:** For symmetric span $[-L/2, +L/2]$, the sampled coordinates straddle the origin at $-0.5\,dx$ and $+0.5\,dx$. The origin $(0, 0)$ is **never** an explicit sampled vertex!
   - **Radix-2 FFT Efficiency:** Powers of two provide maximum throughput for hardware FFT libraries (FFTW, cuFFT, WebGPU compute shaders).
   - **Phase Ramp Consequence:** In Phase 5.2 Fourier propagation, an even grid either requires centered coordinates with a half-pixel offset (introducing a linear phase ramp across Fourier space) or standard FFT-asymmetric coordinates ($x_k = (k - N/2) \cdot dx$) where $(0, 0)$ sits at index $N/2$, resulting in asymmetric spatial boundaries.

---

## 7. Wavefront Phase & Complex Generalized Pupil Function

### 7.1 Optical Phase Calculation

Given an Optical Path Difference $W(x, y)$ in meters and an optical wavelength $\lambda$ in meters (e.g., standard photopic peak $\lambda_0 = 555\text{ nm} = 5.55 \times 10^{-7}\text{ m}$), the optical phase advance $\phi(x, y)$ in radians is:

$$\phi(x, y) = \frac{2\pi}{\lambda} W(x, y) = k \cdot W(x, y) \quad [\text{radians}]$$

where $k = 2\pi / \lambda$ is the optical wavenumber in vacuum/air.

### 7.2 Complex Generalized Pupil Function

Following Goodman (2005), the generalized complex pupil function $P(x, y)$ describes both the transmission amplitude and phase delay across the aperture:

$$P(x, y) = A(x, y) \exp\left( i \phi(x, y) \right) = A(x, y) \exp\left( i \frac{2\pi}{\lambda} W(x, y) \right)$$

### 7.3 Aperture Boundary Conditions

1. **Inside Aperture ($\rho \le 1.0$):**  
   $A(x, y) = 1.0$ for uniform transmission (or $A(x, y) = \exp(-\rho_{\text{SCE}} r^2)$ for Stiles-Crawford apodization).  
   $|P(x, y)| = A(x, y)$, and $\arg(P(x, y)) = \phi(x, y) \pmod{2\pi}$.
2. **Outside Aperture ($\rho > 1.0$):**  
   $A(x, y) \equiv 0.0$, which enforces $P(x, y) \equiv 0.0 + 0.0j$.  
   No light passes outside the physical entrance pupil.

---

## 8. Hand-Calculated Analytical Benchmark Examples

To ensure test validity without circular self-referential assertions, the following 8 canonical cases were hand-calculated from first principles:

| Case ID | Prescription ($S / C \times \alpha$) | $M$ (D) | $J_0$ (D) | $J_{45}$ (D) | $B$ (D) | Power Matrix $\mathbf{F}$ | Eigenvalues $(\lambda_1, \lambda_2)$ | Principal Axes |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| **Case 1** | $-2.00 / 0.00 \times \text{None}$ | $-2.00$ | $0.00$ | $0.00$ | $0.00$ | $\begin{bmatrix} -2.0 & 0.0 \\ 0.0 & -2.0 \end{bmatrix}$ | $(-2.00, -2.00)$ | $(\text{None}, \text{None})$ |
| **Case 2** | $0.00 / -1.50 \times 0^\circ$ | $-0.75$ | $+0.75$ | $0.00$ | $0.75$ | $\begin{bmatrix} 0.0 & 0.0 \\ 0.0 & -1.5 \end{bmatrix}$ | $(0.00, -1.50)$ | $(0^\circ, 90^\circ)$ |
| **Case 3** | $0.00 / -2.00 \times 45^\circ$ | $-1.00$ | $0.00$ | $+1.00$ | $1.00$ | $\begin{bmatrix} -1.0 & +1.0 \\ +1.0 & -1.0 \end{bmatrix}$ | $(0.00, -2.00)$ | $(45^\circ, 135^\circ)$ |
| **Case 4** | $0.00 / -1.50 \times 90^\circ$ | $-0.75$ | $-0.75$ | $0.00$ | $0.75$ | $\begin{bmatrix} -1.5 & 0.0 \\ 0.0 & 0.0 \end{bmatrix}$ | $(0.00, -1.50)$ | $(90^\circ, 0^\circ)$ |
| **Case 5** | $-1.00 / -2.00 \times 30^\circ$ | $-2.00$ | $+0.50$ | $+\frac{\sqrt{3}}{2} \approx 0.866$ | $1.00$ | $\begin{bmatrix} -1.5 & 0.866 \\ 0.866 & -2.5 \end{bmatrix}$ | $(-1.00, -3.00)$ | $(30^\circ, 120^\circ)$ |
| **Case 6** | $+1.50 / -3.00 \times 75^\circ$ | $0.00$ | $-1.5\frac{\sqrt{3}}{2} \approx -1.299$ | $+0.75$ | $1.50$ | $\begin{bmatrix} -1.299 & 0.75 \\ 0.75 & +1.299 \end{bmatrix}$ | $(+1.50, -1.50)$ | $(75^\circ, 165^\circ)$ |
| **Case 7** | $-2.50 / -1.00 \times 15^\circ$ | $-3.00$ | $+0.433$ | $+0.25$ | $0.50$ | $\begin{bmatrix} -2.567 & 0.25 \\ 0.25 & -3.433 \end{bmatrix}$ | $(-2.50, -3.50)$ | $(15^\circ, 105^\circ)$ |
| **Case 8** | $0.00 / 0.00 \times \text{None}$ | $0.00$ | $0.00$ | $0.00$ | $0.00$ | $\begin{bmatrix} 0.0 & 0.0 \\ 0.0 & 0.0 \end{bmatrix}$ | $(0.00, 0.00)$ | $(\text{None}, \text{None})$ |

---

## 9. Assumptions and Scientific Limitations

The Phase 5.1 mathematics engine implements a rigorous lower-order paraxial model. The following simplifying assumptions and limitations must be explicitly noted:

1. **Paraxial Assumption:**  
   Wavefront curvature is modeled up to second order (quadratic terms $x^2, xy, y^2$). This corresponds to paraxial defocus ($W_{20}$) and regular astigmatism ($W_{22}$).
2. **Absence of Higher-Order Aberrations (HOAs):**  
   Real human ocular wavefronts contain monochromatic higher-order aberrations, including spherical aberration ($Z_4^0$), coma ($Z_3^{\pm 1}$), and trefoil ($Z_3^{\pm 3}$). These require Hartmann–Shack or aberrometric Zernike expansions and are not captured by a 3-parameter $(S, C, \alpha)$ refraction.
3. **Absence of Chromatic Dispersion:**  
   The human eye exhibits approximately $2.0\text{ D}$ of longitudinal chromatic aberration (LCA) across the visible spectrum ($400\text{--}700\text{ nm}$). This module computes monochromatic phase at a single specified wavelength $\lambda$ (defaulting to photopic $\lambda_0 = 555\text{ nm}$).
4. **Spectacle Vertex Distance ($d_{\text{vd}}$):**  
   The dioptric powers $S$ and $C$ are assumed to be referenced at the entrance pupil plane (corneal vertex). Clinical spectacle prescriptions measured at $12\text{--}14\text{ mm}$ vertex distance require corneal transposition before insertion if $|S| > 4.0\text{ D}$.
5. **Viewing Distance Vergence & Accommodation:**  
   Object distance vergence ($L = -1/d$) and dynamic crystalline lens accommodation ($A_{\text{acc}}$) are not embedded in this lower-order module and must be supplied by the caller as net defocus $\Delta D = M + (1/d - A_{\text{acc}})$.
6. **No ISO Certification Claim:**  
   While coordinate systems and terminology align with the principles of ISO 24157, this software is an independent research simulation tool and makes no claim of ISO certification or regulatory medical device compliance.

---

## 10. Phase Sampling Readiness & Numerical Aliasing Criteria for Phase 5.2

In discrete optical propagation (Phase 5.2), discrete Fourier transforms will be applied to the generalized complex pupil function $P(x, y) = A(x, y) \exp(i\phi(x, y))$. To ensure reliable discrete modeling without numerical phase wrapping or high-frequency aliasing, the phase gradient must satisfy the spatial Nyquist limit.

### 10.1 Maximum Phase Gradient Derivation

The spatial phase gradient vector in the entrance pupil plane is:
$$\nabla \phi(x, y) = \frac{2\pi}{\lambda} \nabla W(x, y) = \frac{2\pi \sigma}{\lambda} \mathbf{F} \begin{bmatrix} x \\ y \end{bmatrix} \quad [\text{rad} / \text{m}]$$

The maximum gradient magnitude occurs at the pupil perimeter ($r = r_p$) along the principal meridian corresponding to the largest absolute eigenvalue $\lambda_{\max} = \max(|\lambda_1|, |\lambda_2|) = |M| + B$:
$$\|\nabla \phi\|_{\max} = \frac{2\pi}{\lambda} (|M| + B) r_p \quad [\text{rad} / \text{m}]$$

### 10.2 Spatial Nyquist Sampling Condition

To prevent spatial phase aliasing across discrete samples separated by pitch $\Delta x$:
$$|\Delta \phi| = \|\nabla \phi\|_{\max} \Delta x \le \pi \implies \Delta x \le \frac{\lambda}{2 r_p (|M| + B)}$$

For a square computational window spanning $L_p = 2 r_p \cdot \text{span\_factor}$, the minimum discrete sample count $N_{\min}$ is:
$$N_{\min} \ge \frac{4 r_p^2 \cdot \text{span\_factor} \cdot (|M| + B)}{\lambda}$$

### 10.3 Numerical Case Analysis

For standard photopic peak wavelength $\lambda = 555\text{ nm}$ ($5.55 \times 10^{-7}\text{ m}$) with tight span ($\text{span\_factor} = 1.0$):

| Net Power $(\|M\| + B)$ | Pupil Radius $r_p = 1.5\text{ mm}$ (3 mm dia) | Pupil Radius $r_p = 2.0\text{ mm}$ (4 mm dia) | Pupil Radius $r_p = 3.0\text{ mm}$ (6 mm dia) | Pupil Radius $r_p = 4.0\text{ mm}$ (8 mm dia) |
| :---: | :---: | :---: | :---: | :---: |
| **0.50 D** (Mild) | $N \ge 8$ | $N \ge 15$ | $N \ge 33$ | $N \ge 58$ |
| **2.00 D** (Moderate) | $N \ge 33$ | $N \ge 58$ | $N \ge 130$ | $N \ge 231$ |
| **4.00 D** (High) | $N \ge 65$ | $N \ge 116$ | $N \ge 260$ | $N \ge 462$ |
| **8.00 D** (Severe) | $N \ge 130$ | $N \ge 231$ | $N \ge 520$ | $N \ge 923$ |
| **12.00 D** (Extreme) | $N \ge 195$ | $N \ge 346$ | $N \ge 779$ | $N \ge 1384$ |

### 10.4 Key Scientific Findings & Recommendations for Phase 5.2

1. **No Fixed Grid is Universally Sufficient:** A fixed grid of $N = 256$ is fully adequate for a 4 mm pupil up to $\approx 8.8\text{ D}$. However, for dilated pupils (e.g., $r_p = 3.0\text{ mm}$ or $4.0\text{ mm}$), $N = 256$ aliases above $3.9\text{ D}$ and $2.2\text{ D}$, respectively.
2. **Dynamic Sampling Strategy:** In Phase 5.2, grid resolution $N$ must be dynamically computed based on the specific $(r_p, |M|+B, \lambda)$ triplet, choosing the nearest power-of-two (e.g. $256, 512, 1024, 2048$) that satisfies $N \ge 1.5 \times N_{\min}$ (providing a $50\%$ safety margin against fringe compression).
3. **Wavelength Scaling:** Shorter blue wavelengths ($\lambda = 450\text{ nm}$) experience $23\%$ higher phase gradients than green ($555\text{ nm}$), requiring correspondingly denser spatial sampling.

---

## 11. Foundational Scientific References

1. **Thibos, L. N., Wheeler, W., & Horner, D. (1997).**  
   *"Power Vectors: An Application of Fourier Analysis to the Description and Statistical Analysis of Refractive Error."*  
   **Optometry and Vision Science**, 74(6), 367–375.  
   DOI: [10.1002/j.1538-9235.1997.tb04707.x](https://doi.org/10.1002/j.1538-9235.1997.tb04707.x)

2. **International Organization for Standardization (ISO). (2008 / 2015).**  
   *ISO 24157: Ophthalmic optics and instruments — Reporting aberrations of the human eye.*  
   Defines standard Cartesian coordinate axes, pupil normalization, and Zernike polynomial conventions for ocular wavefront representation.

3. **Goodman, J. W. (2005).**  
   *Introduction to Fourier Optics* (3rd ed.).  
   Roberts & Company Publishers, Englewood, Colorado.  
   (Chapters 5 & 6: Generalized pupil functions, monochromatic aberration polynomials, and coherent vs. incoherent impulse responses).

4. **Atchison, D. A., & Smith, G. (2000).**  
   *Optics of the Human Eye.*  
   Butterworth-Heinemann, Oxford.  
   (Chapters 3, 4 & 18: Paraxial schematic eyes, astigmatism of oblique incidence, and Jackson cross-cylinder principles).
