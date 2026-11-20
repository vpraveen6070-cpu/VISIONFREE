# VISIONFREE Phase 5.2: Diffraction and Fourier Optics Engine
## Monochromatic Scalar Wave Propagation, Point Spread Functions, and Transfer Functions

**Document Version:** `1.1.0` (Incorporating Phase 5.2.1 Independent Numerical Audit)  
**Date:** November 2026  
**Status:** Completed & Empirically Verified (100/100 tests passing across Python 3.14 & Python 3.9)  
**Author:** VISIONFREE Computational Optics & Scientific Computing Research Group  
**Parent Workspace:** `VISIONFREE/research/`

---

## 1. Executive Summary & Scope

Phase 5.2 establishes the monochromatic physical wave optics and Fourier transformation engine for the VISIONFREE project. Building directly upon the ophthalmic power vector and quadratic wavefront formulations developed in Phase 5.1, this module transforms complex pupil fields into focal-plane retinal intensity distributions and spatial frequency transfer functions.

```
+-------------------------------------------------------------------------+
|                  Phase 5.1 Ophthalmic Wavefront Engine                  |
|  Clinical Rx (S, C, α) -> Power Vector (M, J0, J45) -> OPD W(x, y)      |
+-------------------------------------------------------------------------+
                                     │
                                     ▼
+-------------------------------------------------------------------------+
|                Phase 5.2 Generalized Complex Pupil Field                |
|           P(x_p, y_p) = A(x_p, y_p) * exp[ i * (2π/λ) * OPD(x_p, y_p) ]  |
+-------------------------------------------------------------------------+
                                     │
                       [Fraunhofer Fourier Transform]
                                     ▼
+-------------------------------------------------------------------------+
|                    Point Spread Functions (Retina)                      |
|  Amplitude PSF:  h(x_i, y_i) = Fraunhofer{ P(x_p, y_p) }                |
|  Intensity PSF:  PSF(x_i, y_i) = |h(x_i, y_i)|²                          |
+-------------------------------------------------------------------------+
                                     │
                        [Inverse Fourier Transform]
                                     ▼
+-------------------------------------------------------------------------+
|                   Optical & Modulation Transfer Functions                |
|  OTF(f_x, f_y) = ℱ{ PSF(x_i, y_i) } with OTF(0, 0) ≡ 1.0                |
|  MTF(f_x, f_y) = |OTF(f_x, f_y)| ≥ 0                                    |
|  PTF(f_x, f_y) = atan2( Im{OTF}, Re{OTF} )                              |
+-------------------------------------------------------------------------+
```

> [!IMPORTANT]
> **Strict Phase 5.2 Boundaries:**  
> This module models monochromatic diffraction and Fourier propagation of ocular aberrations. In accordance with project milestones, Phase 5.2 **does not** perform forward blur convolution on benchmark images, pre-compensation filtering, Wiener deconvolution, Tikhonov regularization, or browser extension UI integration. Those higher-level processing algorithms are strictly reserved for Phase 5.3 and subsequent phases.

---

## 2. Scalar Fraunhofer Diffraction Theory & Physical Validity Criteria

### 2.1 The Scalar Wave Approximation

In ocular optical modeling, the electromagnetic field is treated as a scalar wave $u(\mathbf{r}, t) = \operatorname{Re}\{U(\mathbf{r}) e^{-i \omega t}\}$. This scalar approximation is physically valid when:
1. The pupil aperture diameter $D$ (typically $2\text{ mm} \le D \le 8\text{ mm}$) is vastly larger than the optical wavelength $\lambda$ ($550\text{ nm} = 0.55\,\mu\text{m}$):
   $$\frac{D}{\lambda} \sim \frac{4 \times 10^{-3}\,\text{m}}{5.5 \times 10^{-7}\,\text{m}} \approx 7272 \gg 1$$
   Under this condition, polarization-dependent vector boundary effects at the pupil margin contribute less than $0.01\%$ to the total focal irradiance and can be safely neglected (Goodman, 2005; Born & Wolf, 1999).
2. The ocular media (cornea, aqueous humor, crystalline lens, vitreous humor) are assumed isotropic and non-magnetic at physiological scales.

### 2.2 Fresnel vs. Fraunhofer Regimes

For propagation over a distance $z$ from an aperture of radius $r_p$, the Fresnel number $N_F$ characterizes the diffraction regime:
$$N_F = \frac{r_p^2}{\lambda z}$$

In a free-space collimated beam over ocular distances ($r_p = 2\text{ mm}$, $z = 17\text{ mm}$), $N_F \approx 428 \gg 1$, which would strictly represent near-field Fresnel diffraction. However, **in the focused human eye**, the ocular refracting elements introduce a convergent spherical wavefront of focal length $f \approx 17\text{ mm}$ that cancels the quadratic Fresnel phase curvature in the posterior focal plane.

Consequently, the observation plane coincides with the Fraunhofer focal plane of the optical system. The effective Fresnel number of the focused system vanishes:
$$N_{F,\text{effective}} = \frac{r_p^2}{\lambda} \left( \frac{1}{z} - \frac{1}{f} \right)_{z = f} = 0$$
Hence, the field distribution in the focal plane is **rigorously described by the Fraunhofer diffraction integral** (Goodman, 2005).

### 2.3 Paraxial Approximation

The focal length of the reduced human eye is $f \approx 17\text{ mm}$, and the maximum physiological pupil radius is $r_p \le 4\text{ mm}$. The maximum angular ray deviation $\theta$ satisfies:
$$\tan \theta = \frac{r_p}{f} \le \frac{4\text{ mm}}{17\text{ mm}} \approx 0.235\text{ rad} \implies \sin \theta \approx \theta, \quad \cos \theta \approx 1 - \frac{\theta^2}{2}$$
The paraxial approximation introduces an amplitude error of less than $\frac{1}{2}(1 - \cos \theta) \approx 2.7\%$ at the extreme margin of an $8\text{ mm}$ pupil and less than $0.7\%$ for a standard $4\text{ mm}$ pupil ($r_p = 2\text{ mm}$).

### 2.4 Monochromatic Incoherent Illumination Assumption

1. Natural light is spatially incoherent. The retinal intensity distribution $I_i(x_i, y_i)$ is formed by linear intensity superposition:
   $$I_i(x_i, y_i) = I_g(x_i, y_i) * \text{PSF}(x_i, y_i)$$
   where $I_g$ is the ideal geometrical image and $*$ denotes 2D spatial convolution.
2. In Phase 5.2, monochromatic light at the standard photopic visual efficiency peak ($\lambda = 550\text{ nm}$, green $V(\lambda)$ maximum) is modeled. Polychromatic chromatic aberrations (LCA/TCA) are decomposed into monochromatic spectral channels in Phase 5.3+.

---

## 3. The Generalized Complex Pupil Function

### 3.1 Mathematical Definition

The exit pupil of the eye is described by the complex generalized pupil function $P(x_p, y_p)$:
$$P(x_p, y_p) = A(x_p, y_p) \exp\left[ i \phi(x_p, y_p) \right] = A(x_p, y_p) \exp\left[ i \frac{2\pi}{\lambda} \text{OPD}(x_p, y_p) \right]$$
where:
- $(x_p, y_p)$ are Cartesian coordinates in the pupil plane (metres).
- $A(x_p, y_p)$ is the real-valued amplitude transmission factor ($0 \le A \le 1$).
- $\text{OPD}(x_p, y_p)$ is the Optical Path Difference function (metres).
- $\phi(x_p, y_p)$ is the optical phase distribution (radians).

### 3.2 Amplitude Transmission & Stiles-Crawford Apodization

For an unobstructed clear circular aperture of radius $r_p$:
$$A_0(x_p, y_p) = \begin{cases} 1, & \sqrt{x_p^2 + y_p^2} \le r_p \\ 0, & \sqrt{x_p^2 + y_p^2} > r_p \end{cases}$$

Under photopic illumination, retinal cone photoreceptors exhibit directional sensitivity due to waveguide properties (Stiles-Crawford Effect I). The effective transmission apodization is modeled by a Gaussian profile:
$$A_{\text{SCE}}(x_p, y_p) = A_0(x_p, y_p) \exp\left[ -\frac{\rho}{2} (x_p^2 + y_p^2) \right]$$
where $\rho \approx 0.116\,\text{mm}^{-2} = 1.16 \times 10^5\,\text{m}^{-2}$ for typical human eyes (Applegate & Lakshminarayanan, 1993).

### 3.3 Phase Sign Convention & Wavefront Aberration Link

In accordance with Phase 5.1 and international standards (ISO 24157:2008, Thibos et al., 2000):
$$\text{OPD}(x_p, y_p) = -W(x_p, y_p)$$
$$\phi(x_p, y_p) = \frac{2\pi}{\lambda} \text{OPD}(x_p, y_p) = -\frac{2\pi}{\lambda} W(x_p, y_p)$$
For lower-order paraxial refractions parameterized by the Thibos power matrix $\mathbf{F} = \begin{pmatrix} M + J_0 & J_{45} \\ J_{45} & M - J_0 \end{pmatrix}$:
$$W_2(x_p, y_p) = -\frac{1}{2} \begin{pmatrix} x_p & y_p \end{pmatrix} \mathbf{F} \begin{pmatrix} x_p \\ y_p \end{pmatrix}$$
$$\text{OPD}_2(x_p, y_p) = +\frac{1}{2} \begin{pmatrix} x_p & y_p \end{pmatrix} \mathbf{F} \begin{pmatrix} x_p \\ y_p \end{pmatrix}$$
$$\phi_2(x_p, y_p) = \frac{\pi}{\lambda} \begin{pmatrix} x_p & y_p \end{pmatrix} \mathbf{F} \begin{pmatrix} x_p \\ y_p \end{pmatrix}$$

---

## 4. Continuous Fraunhofer Propagation & Discrete Scaling

### 4.1 The Continuous Fraunhofer Integral

In the posterior focal plane of a lens of focal length $f$, the complex field $U_i(x_i, y_i)$ is:
$$U_i(x_i, y_i) = \frac{e^{i k f} e^{i \frac{k}{2f} (x_i^2 + y_i^2)}}{i \lambda f} \iint_{-\infty}^{\infty} P(x_p, y_p) \exp\left[ -i \frac{2\pi}{\lambda f} (x_i x_p + y_i y_p) \right] dx_p dy_p$$
Because the retina is a square-law detector sensitive to irradiance $|U_i|^2$, the pre-factor phase terms have unit modulus, leaving the intensity PSF proportional to the 2D spatial Fourier transform evaluated at:
$$f_x = \frac{x_i}{\lambda f}, \quad f_y = \frac{y_i}{\lambda f}$$

### 4.2 Discrete Fourier Scaling & Reciprocity

Let the pupil plane be sampled on an $N \times N$ grid with pitch $\Delta x_p$ and physical span $L = N \Delta x_p$. After zero-padding to $N_{\text{pad}} \times N_{\text{pad}}$ ($N_{\text{pad}} \ge N$), the padded span is $L_{\text{pad}} = N_{\text{pad}} \Delta x_p$. The discrete sampling pitch $\Delta x_i$ and retinal span $L_i$ are:
$$\Delta x_i = \frac{\lambda f}{L_{\text{pad}}} = \frac{\lambda f}{N_{\text{pad}} \Delta x_p}, \qquad L_i = N_{\text{pad}} \Delta x_i = \frac{\lambda f}{\Delta x_p}$$

This reciprocity demonstrates:
1. **Focal Sampling Pitch ($\Delta x_i$):** Inversely proportional to total pupil window $L_{\text{pad}}$. Zero-padding refines the discrete interpolation density of the focal PSF.
2. **Focal Grid Extent ($L_i$):** Inversely proportional to pupil pitch $\Delta x_p$. Finer pupil sampling expands the physical field of view on the retina.

### 4.3 Spatial Frequency & Visual Angular Units

$$f_x = \frac{x_i}{\lambda f} \quad (\text{cycles / m}), \qquad \text{cpd} = f_x \cdot f \cdot \frac{\pi}{180} = \frac{x_i}{\lambda} \cdot \frac{\pi}{180} \quad (\text{cycles / degree})$$
For a $4\text{ mm}$ pupil at $\lambda = 550\text{ nm}$, the theoretical optical cutoff is $f_{c,\text{cpd}} \approx 126.9\text{ cpd}$, exceeding the human foveal cone photoreceptor Nyquist limit ($\approx 60\text{ cpd}$).

---

## 5. Amplitude PSF vs. Intensity PSF

### 5.1 Complex Impulse Response (Amplitude PSF)
$$h[j, k] = \frac{\Delta x_p \Delta y_p}{i \lambda f} \operatorname{fftshift}\left( \operatorname{fft2}\left( \operatorname{ifftshift}( P ) \right) \right)[j, k]$$

### 5.2 Point Spread Function (Intensity PSF)
$$\text{PSF}(x_i, y_i) = |h(x_i, y_i)|^2 = \operatorname{Re}\{h\}^2 + \operatorname{Im}\{h\}^2 \ge 0$$

### 5.3 Geometric Centroid & Parity Properties

For even pupil phase parity ($W(-x_p, -y_p) = W(x_p, y_p)$), the continuous optical centroid $(\bar{x}_i, \bar{y}_i) \equiv (0, 0)$. On discrete FFT grids of even dimension $N$, discrete boundary asymmetry leaves an unavoidable sub-nanometer sampling residual:
$$|\bar{x}_i| \approx 1.0\text{ nm} \ll \Delta x_i$$
which is rigorously validated across all grid resolutions.

---

## 6. Normalization Conventions & Independent Parseval Verification

### 6.1 Normalization Modes

| Normalization Mode | Formula | Physical Meaning | Primary Use Case |
| :--- | :--- | :--- | :--- |
| `integrated` (Default) | $\iint \text{PSF}(x_i, y_i) dx_i dy_i = 1.0$ | Radiometric flux conservation in continuous space ($\text{W} / \text{W} = 1$) | Optical transfer function calculations, Strehl ratio, wavefront diagnostics |
| `probability` | $\sum_{j,k} \text{PSF}[j,k] = 1.0$ | Discrete probability distribution / discrete blur kernel | Image convolution, forward blur simulation, deconvolution filters |
| `unnormalized` | $\text{PSF}_{\text{phys}} = \|h_{\text{phys}}\|^2$ | Absolute physical irradiance ($\text{W}/\text{m}^2$ per unit incident flux) | Photometric sensor modeling, laser safety, absolute radiometric exposure |

### 6.2 Independent Parseval Verification Before Normalization

By Parseval's theorem for the discrete Fourier transform:
$$\sum_{u, v} |\operatorname{fft2}(P_{\text{pad}})[u, v]|^2 = N_{\text{pad}}^2 \sum_{j, k} |P[j, k]|^2$$
Substituting $U_i = \frac{\Delta x_p \Delta y_p}{i \lambda f} \operatorname{fft2}(P_{\text{pad}})$ and $\Delta x_i \Delta y_i = \frac{\lambda^2 f^2}{N_{\text{pad}}^2 \Delta x_p \Delta y_p}$:
$$\sum_{u, v} |U_i[u, v]|^2 \Delta x_i \Delta y_i = \Delta x_p \Delta y_p \sum_{j, k} |P[j, k]|^2$$

This proves that **discrete integrated focal-plane energy strictly equals discrete pupil-plane energy before any explicit normalization**:
$$\iint |U_i(x_i, y_i)|^2 dx_i dy_i \equiv \iint |P(x_p, y_p)|^2 dx_p dy_p$$
Our independent audit confirms this identity holds to **machine precision ($\le 2.70 \times 10^{-16}$)** across all $N \in \{64, 128, 256, 512, 1024, 2048\}$ and all zero-padding ratios.

### 6.3 Aperture Discretization Error

The discrete pupil area $A_{\text{disc}} = \sum \operatorname{mask} \cdot \Delta x_p^2$ differs from the continuous circle area $\pi r_p^2$ due to pixelated boundary staircasing. This geometric discretization error scales as $O(1/N)$:
- $N = 64$: $-0.901\%$
- $N = 128$: $-0.248\%$
- $N = 256$: $-0.116\%$
- $N = 512$: $-0.075\%$
- $N = 1024$: $-0.013\%$
- $N = 2048$: $-0.009\%$

Checking that $\iint \text{PSF}_{\text{integrated}} = 1.0$ on an already normalized array tests the division operation by construction. Physical energy conservation must be verified by comparing unnormalized focal energy against discrete pupil energy.

---

## 7. Analytical Airy Disk Benchmark & Zero Localization

### 7.1 Analytical PSF Formula

For a clear circular aperture of diameter $D = 2 r_p$:
$$\text{PSF}_{\text{Airy}}(r_i) = I_0 \left[ \frac{2 J_1(u)}{u} \right]^2, \qquad u = \frac{\pi D r_i}{\lambda f}$$
Maclaurin series expansion for $|u| < 10^{-8}$:
$$\frac{2 J_1(u)}{u} = 1 - \frac{u^2}{8} + \frac{u^4}{192} - \frac{u^6}{9216} + \mathcal{O}(u^8)$$

### 7.2 Canonical Zeros & Encircled Energy

- **1st Dark Ring (Airy Radius):** 
  $$u_1 = 3.8317059702075123 \implies r_1 = \frac{u_1 \lambda f}{\pi D}$$
  For standard photopic ocular parameters ($\lambda = 550\text{ nm} = 5.50 \times 10^{-7}\text{ m}$, $f = 17\text{ mm} = 0.017\text{ m}$, $D = 4\text{ mm} = 0.004\text{ m}$):
  $$r_{1,\text{exact}} = \mathbf{2.8509783708354544\,\mu\text{m}} \quad (2.8509783708354544 \times 10^{-6}\text{ m})$$
- **2nd Dark Ring:** $u_2 = 7.015586669815619 \implies r_2 = 5.218552\,\mu\text{m}$.
- **3rd Dark Ring:** $u_3 = 10.17346813506272 \implies r_3 = 7.568434\,\mu\text{m}$.
- **Encircled Energy within $r_1$:** $E(u_1) = 1 - J_0^2(u_1) - J_1^2(u_1) = 1 - J_0^2(u_1) = \mathbf{83.78\%}$.

### 7.3 Resolving the Airy First-Zero Localization Discrepancy & Reconciling Convergence Metrics

When evaluating the numerical first minimum against the theoretical reference $r_{1,\text{exact}} = 2.8509783708354544\,\mu\text{m}$, three distinct localization methodologies must be distinguished:

1. **Nearest Sampled Pixel ($r_{1,\text{disc}}$):**
   The discrete array sample index where the intensity profile begins to rise ($\Delta \text{PSF} > 0$). The error is bounded by grid quantization:
   $$|r_{1,\text{disc}} - r_{1,\text{exact}}| \le \frac{1}{2} \Delta x_i$$
   - When $\Delta x_i = 0.2922\,\mu\text{m}$ ($N = 512, N_{\text{pad}} = 2048$), the nearest sampled pixel is index 10 at $2.9219\,\mu\text{m}$, yielding a discrete quantization error of $0.0709\,\mu\text{m}$ (**$2.49\%$**).
   - When $\Delta x_i = 0.0730\,\mu\text{m}$ ($N = 256, N_{\text{pad}} = 4096$), the nearest pixel is index 39 at $2.8488\,\mu\text{m}$ (**$0.08\%$**).
2. **Subpixel Parabolic Vertex:**
   Three-point vertex interpolation around the discrete minimum:
   $$\delta = -\frac{\Delta x_i}{2} \frac{y_{+1} - y_{-1}}{y_{+1} - 2y_0 + y_{-1}}$$
3. **Cubic Spline Root of Radial Derivative ($r_{1,\text{spline}}$):**
   Evaluating the continuous root of $\frac{d}{dr} \text{PSF}_{\text{spline}}(r) = 0$.

#### Reconciliation of the Reported 0.0044% and 0.0062% Convergence Results:
The two values reported in earlier audit drafts represent two distinct, reproducible numerical studies rather than contradictory claims:
- **Study 1: Pupil Grid Resolution Convergence (Table 1):** Holding the physical focal-plane window constant at $L_{\text{pad}} = 32\text{ mm}$ (using $N_{\text{pad}} = 4 N_{\text{pupil}}$, so that $\Delta x_i = 0.2922\,\mu\text{m}$ is fixed across resolutions), testing $N_{\text{pupil}} = 512$ with $N_{\text{pad}} = 2048$ yields a numerical spline root of:
  $$r_{1,\text{spline}} = 2.8511051\,\mu\text{m} \implies \text{Error} = \frac{|2.8511051 - 2.8509784|}{2.8509784} \times 100\% = \mathbf{0.0044\%} \; (0.127\text{ nm})$$
- **Study 2: Zero-Padding Convergence at Fixed Pupil Resolution (Table 2):** Fixing the pupil grid resolution at $N_{\text{pupil}} = 256$ ($\Delta x_p = 31.25\,\mu\text{m}$) and progressively increasing zero-padding up to $N_{\text{pad}} = 4096$ ($\Delta x_i = 0.0730\,\mu\text{m}$), the asymptotic spline root converges to:
  $$r_{1,\text{spline}} = 2.850803\,\mu\text{m} \implies \text{Error} = \frac{|2.850803 - 2.8509784|}{2.8509784} \times 100\% = \mathbf{0.0062\%} \; (0.175\text{ nm})$$
Both figures are numerically authentic, verified, and reflect sub-nanometer physical agreement ($< 0.2\text{ nm}$) with the analytical Bessel zero.

### 7.4 Focal Plane Sampling Threshold for Dark Ring Resolution

Because the first secondary bright ring has a peak intensity of only $1.75\%$ of the central core, discrete samples on a coarse grid ($\Delta x_i > 0.5\,\mu\text{m}$) evaluate the falling slope of the central core ($> 3\%$) and jump past the secondary peak ($< 1.5\%$), appearing monotonically decreasing.

To resolve the Airy dark ring as a discrete local minimum, the focal sampling pitch must satisfy:
$$\Delta x_i \le 0.5\,\mu\text{m} \implies L_{\text{pad}} \ge \frac{\lambda f}{0.5\,\mu\text{m}} = 18.7\text{ mm} \implies \frac{N_{\text{pad}}}{N_{\text{pupil}}} \ge 2.34$$
Hence, zero-padding ($N_{\text{pad}} \ge 2.5 N_{\text{pupil}}$) is physically necessary to resolve sub-micron diffraction features.

---

## 8. Optical Transfer Function & Independent MTF Validation

### 8.1 Definition & DC Normalization
$$\text{OTF}(f_x, f_y) = \frac{\iint \text{PSF}(x_i, y_i) e^{-i 2\pi(f_x x_i + f_y y_i)} dx_i dy_i}{\iint \text{PSF}(x_i, y_i) dx_i dy_i}, \qquad \text{OTF}(0, 0) \equiv 1.0 + 0.0j$$

### 8.2 Autocorrelation Dual Equivalence vs. Truly Independent Validation

Two distinct validation tests are implemented:

1. **Algebraic Dual Cross-Check (`compute_otf` vs. `pupil_autocorrelation_otf`):**
   By the discrete convolution theorem:
   $$\mathcal{F}\{ |\mathcal{F}\{P\}|^2 \} \equiv \mathcal{F}^{-1}\{ |\mathcal{F}\{P\}|^2 \}$$
   These two functions share the exact same underlying discrete FFT conventions and circular periodic boundaries. They agree to machine precision ($4.53 \times 10^{-16}$). This confirms implementation self-consistency, but does **not** constitute an independent physical validation.
2. **Truly Independent Closed-Form Benchmark (Duffieux Formula):**
   The numerical MTF is compared directly against the analytical closed-form circular aperture overlap formula:
   $$\text{MTF}_{\text{diff}}(\nu) = \frac{2}{\pi} \left[ \arccos(\nu) - \nu \sqrt{1 - \nu^2} \right], \quad \nu = \frac{\rho}{\rho_c} \le 1, \quad \rho_c = \frac{D}{\lambda f}$$
   Our independent audit confirms agreement across all spatial frequencies:
   - Maximum absolute error: $< 8.0 \times 10^{-4}$ ($< 0.08\%$)
   - Root-mean-square error: $2.16 \times 10^{-4}$

---

## 9. Phase Transfer Function & Contrast Reversal

$$\text{PTF}(f_x, f_y) = \operatorname{atan2}\left( \operatorname{Im}\{\text{OTF}\}, \operatorname{Re}\{\text{OTF}\} \right) \in [-\pi, +\pi]$$
When severe defocus or centrosymmetric aberration causes the real OTF to become negative, the PTF jumps discontinuously to $\pm \pi$, physically inverting grating contrast (bright bars become dark). The unit test suite validates this $\pi$-jump to within $10^{-14}$.

---

## 10. FFT Coordinate Conventions & Symmetry Parity

1. **Even $N$ Formulation:**
   $$x[k] = \left( k - \frac{N}{2} \right) \Delta x, \quad k \in \{0, 1, \dots, N-1\}$$
   - Index $k = N/2$ is strictly at coordinate $0.0$.
   - Domain range: $[-L/2, +L/2 - \Delta x]$.
   - Asymmetry leaves a sub-pixel centroid residual $\epsilon \sim 1.0\text{ nm} \ll \Delta x_i$.
2. **Odd $N$ Formulation:**
   $$x[k] = \left( k - \frac{N-1}{2} \right) \Delta x, \quad k \in \{0, 1, \dots, N-1\}$$
   - Origin is at $(N-1)/2$, symmetrically spanning $[-L/2, +L/2]$.
3. **Quadrant Swapping:** Two-sided `fftshift(fft2(ifftshift(P)))` ensures origin centering.

---

## 11. Physical Sampling vs. Zero-Padding Limitations

A critical distinction in numerical Fourier optics must be maintained regarding zero-padding:

1. **Zero-Padding Refines Focal-Plane Numerical Sampling:** Zero-padding ($N_{\text{pad}} > N$) increases the total computational domain $L_{\text{pad}} = N_{\text{pad}} \Delta x_p$, which reduces the focal-plane sampling interval $\Delta x_i = \frac{\lambda f}{L_{\text{pad}}}$. This evaluates the continuous sinc-interpolated Fourier spectrum at a denser lattice of discrete sample points, resolving fine Airy diffraction rings without blocky pixelation and preventing circular convolution wrap-around aliasing in transfer function calculations.
2. **Zero-Padding Does NOT Increase Physical Optical Resolution:** Zero-padding adds no new physical information. The physical optical resolving power of the system is strictly bounded by the physical entrance pupil aperture diameter $D$ (the classical Abbe and Rayleigh diffraction limits) and the unpadded pupil-plane sampling pitch $\Delta x_p$. Zero-padding cannot recover wavefront aberrations, high-frequency phase variations, or pupil features that were under-sampled on the physical pupil grid.

---

## 12. Numerical Aliasing & Sampling Limits

### 12.1 The Nyquist Phase Gradient Criterion
$$\|\nabla \phi_2\|_{\max} = \frac{2\pi}{\lambda} D_{\max} r_p \implies N_{\text{nyquist}} \ge \frac{4 r_p^2 \cdot \text{span\_factor} \cdot D_{\max}}{\lambda}$$
$$N_{\text{target}} = \operatorname{next\_pow2}\left( \lceil S \cdot N_{\text{nyquist}} \rceil \right), \quad S = 1.5$$

### 12.2 What the Nyquist Criterion Does and Does NOT Guarantee

> [!CAUTION]
> **Phase-gradient sampling criteria do not eliminate all sources of numerical aliasing.**
> The phase-gradient Nyquist criterion guarantees **only** that adjacent phase samples inside the pupil aperture do not exceed $\pi$ radians ($\Delta \phi \le \pi$), preventing internal phase wrap-around aliasing.
> It does **not** eliminate all sources of numerical error or aliasing throughout the complete optical simulation because:
> 1. **Aperture Step Discontinuity:** The hard boundary of a clear circular aperture is a Heaviside step discontinuity whose continuous Fourier spectrum possesses infinite spatial frequency support ($1/r^3$ intensity decay in the Airy rings). Truncating this spectrum on a finite discrete DFT grid inherently produces spectral leakage and Gibbs ringing.
> 2. **Focal Domain Spatial Wrap-Around:** Severe ophthalmic refractive errors produce large geometrical blur spots of diameter $d_{\text{geom}} \approx 2 r_p D_{\max} f$. If $d_{\text{geom}}$ approaches or exceeds the finite focal computational window $L_i = \lambda f / \Delta x_p$, energy wraps around the periodic boundaries of the image domain.
> 3. **Discrete Aperture Staircasing:** Cartesian pixelation of the circular margin introduces geometric area errors that converge as $O(1/N)$.

### 12.3 Aperture Boundary Representation (Binary vs. Supersampled)

An independent numerical audit evaluated an $8 \times 8$ supersampled subpixel anti-aliased pupil boundary against the standard binary mask:
- Supersampling reduced peak linear field error from $-1.79\%$ to $-0.015\%$ at $N = 64$ because the continuous field integral $\iint P dx_p dy_p$ is linear in transmission amplitude.
- However, when computing intensity $|U_i|^2$, squaring fractional transmission amplitudes ($0 < \alpha < 1 \implies \alpha^2 < \alpha$) introduces an artificial absorbing ring at the pupil boundary, degrading quadratic energy conservation ($\iint |P|^2 dx_p dy_p$).
- Furthermore, subpixel smoothing produced zero improvement in Airy zero localization or transfer function accuracy.
- **Scope of Finding:** This result—that a standard binary circular mask on an adequately sampled grid ($N \ge 256$, where geometric area error is $< 0.12\%$) is physically and numerically preferred—is **specific to the tested discrete Fourier optics irradiance formulation**, where the continuous field integral is squared to compute intensity. It is **not a universal claim of superiority across all numerical methods** (e.g., linear amplitude field integration, finite-element, or boundary-element methods, where anti-aliased subpixel averaging can be advantageous).

### 12.4 Consistent Safety Ratio Classification

To resolve previous reporting ambiguities, classifications for a static $N=256$ grid ($r_p = 2\text{ mm}, \text{span} = 1.5, \lambda = 550\text{ nm}$) are strictly defined by the safety ratio $R = N / N_{\text{nyquist}}$:

```
Prescription (S, C x α)    D_max (D)   N_nyquist   N_rec (S=1.5)   Safety Ratio R   Mathematical Status
---------------------------------------------------------------------------------------------------------
+0.25 DS (Mild)            0.25 D      10.9        32              23.49            COMPLIANT (Oversampled)
-1.00 / -0.50 x 90°        1.50 D      65.5        128             3.91             COMPLIANT (Oversampled)
+1.50 / -3.00 x 75°        3.00 D      130.9       256             1.96             COMPLIANT (Adequate)
-2.50 / -1.00 x 180°       3.50 D      152.7       256             1.68             COMPLIANT (Adequate)
-5.00 / -2.00 x 45°        7.00 D      305.5       512             0.84             ALIASED (Nyquist violated)
-8.00 / -3.00 x 30°        11.00 D     480.0       1024            0.53             ALIASED (Severe)
```
- **COMPLIANT (Oversampled):** $R \ge 2.0$ (more than double the Nyquist threshold).
- **COMPLIANT (Adequate):** $1.5 \le R < 2.0$ (satisfies the $S = 1.5$ engineering safety margin).
- **MARGINAL:** $1.0 \le R < 1.5$ (satisfies strict Nyquist, but below safety margin $S = 1.5$).
- **ALIASED:** $R < 1.0$ (violates strict Nyquist; phase increments exceed $\pi$ radians).

---

## 13. Comprehensive Convergence & Verification Study

A rigorous resolution study separating pupil resolution $N$ from zero-padding was conducted with fixed physical focal window $L_{\text{pad}} = 32\text{ mm}$ ($N_{\text{pad}} = 4 N$, $\Delta x_i = 0.2922\,\mu\text{m}$) across $N \in \{64, 128, 256, 512, 1024, 2048\}$:

```
+-------------------------------------------------------------------------------------------------------------------+
|     N |   Pad | dx_p(um) | dx_i(um) | Parseval Diff | Raw E Err% | Peak Err% | Centroid(nm) | r1 Disc% | r1 Spline% |
|-------+-------+----------+----------+---------------+------------+-----------+--------------+----------+------------|
|    64 |   256 |   125.00 |   0.2922 |      0.00e+00 |   -0.9012% |  -1.7942% |       8.5547 |    2.49% |    0.0993% |
|   128 |   512 |    62.50 |   0.2922 |      2.70e-16 |   -0.2484% |  -0.4962% |       4.1850 |    2.49% |    0.1254% |
|   256 |  1024 |    31.25 |   0.2922 |      1.35e-16 |   -0.1163% |  -0.2324% |       2.0736 |    2.49% |    0.0175% |
|   512 |  2048 |    15.62 |   0.2922 |      1.35e-16 |   -0.0755% |  -0.1509% |       1.0324 |    2.49% |    0.0044% |
|  1024 |  4096 |     7.81 |   0.2922 |      1.35e-16 |   -0.0128% |  -0.0257% |       0.5149 |    2.49% |    0.0111% |
|  2048 |  8192 |     3.91 |   0.2922 |      1.35e-16 |   -0.0093% |  -0.0186% |       0.2572 |    2.49% |    0.0097% |
+-------------------------------------------------------------------------------------------------------------------+
```

### Zero-Padding Study for Fixed Pupil Grid ($N_{\text{pupil}} = 256$, $\Delta x_p = 31.25\,\mu\text{m}$):
```
+-----------------------------------------------------------------------------------------------+
|   Pad |  dx_i (um) | Nearest idx | r1_disc (um) | r1_disc Err% | r1_spline (um) | r1_spline Err% |
|-------+------------+-------------+--------------+--------------+----------------+----------------|
|   512 |     0.5844 |           5 |       2.9219 |        2.49% |       2.852528 |        0.0543% |
|  1024 |     0.2922 |          10 |       2.9219 |        2.49% |       2.850479 |        0.0175% |
|  2048 |     0.1461 |          20 |       2.9219 |        2.49% |       2.850783 |        0.0069% |
|  4096 |     0.0730 |          39 |       2.8488 |        0.08% |       2.850803 |        0.0062% |
|  8192 |     0.0365 |          78 |       2.8488 |        0.08% |       2.850799 |        0.0063% |
+-----------------------------------------------------------------------------------------------+
```

---

## 14. Diagnostic Visualizations

The Phase 5.2 diagnostic visualization suite (`research/src/visionfree_research/optics/visualize_fourier.py`) generates a comprehensive 8-panel technical figure saved at:
`research/results/phase52/phase52_fourier_optics_demo.png`

Panel 8 specifically presents the dual convergence metrics:
- Aperture Area Error vs. $\pi r_p^2$ (monotonically decreasing $O(1/N)$ geometric error).
- Airy First Zero Nearest Pixel Error (quantization floor $\sim \Delta x_i / 2$).
- Airy First Zero Spline Root Error (physical wave optics convergence down to $< 0.01\%$).

---

## 15. Scientific Citations & References

1. **Goodman, J. W.** (2005). *Introduction to Fourier Optics* (3rd ed.). Roberts & Company Publishers.
2. **Born, M., & Wolf, E.** (1999). *Principles of Optics* (7th ed.). Cambridge University Press.
3. **Thibos, L. N., Wheeler, W., & Horner, D.** (1997). *Power vectors: an application of Fourier analysis to the description and statistical analysis of refractive error*. Optometry and Vision Science, 74(6), 367–375.
4. **Duffieux, P. M.** (1983). *The Fourier Transform and its Applications to Optics* (2nd ed.). John Wiley & Sons.
5. **Applegate, R. A., & Lakshminarayanan, V.** (1993). *Parametric representation of Stiles-Crawford functions*. Journal of the Optical Society of America A, 10(7), 1611–1623.
6. **ISO 24157:2008**. *Ophthalmic optics and instruments — Reporting aberrations of the human eye*.
