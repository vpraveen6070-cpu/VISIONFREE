# VISIONFREE Research Workspace
## Phase 5: Computational Optics, Image Processing & Reproducible Benchmarks

**Workspace Version:** `0.1.1` (Phase 5.0.1 Readiness Audit)  
**Parent Project:** VISIONFREE (`0.4.1`)  
**Base Git Checkpoint:** `bc0a5ee` (`main`)  
**Directory:** `VISIONFREE/research/`  

---

## 1. Purpose of the Research Workspace

This isolated workspace hosts offline computational optics, mathematical modeling, and digital image processing research for the VISIONFREE project. 

Its primary objective in Phase 5 is to evaluate whether digital image pre-compensation on standard 2D displays can improve retinal contrast for uncorrected defocus and astigmatism, and to establish the physical and perceptual limits of 2D screen pre-filtering.

### Key Architectural Boundaries:
- **Strictly Offline & Decoupled:** This environment does not depend on or modify the Chrome extension runtime (`manifest.json`, background service workers, content scripts, styler, or options UI).
- **Zero In-Browser WebGL Canvas Injections:** All optical modeling is prototyped in Python to prevent destructive DOM rasterization on live web pages.
- **Reproducible Science:** All experiments use deterministic synthetic visual targets generated on the fly with no external dataset downloads or patient clinical data.

---

## 2. Python Environment & Upgrade Status

### Dual Research Environments:
VISIONFREE maintains two isolated scientific research environments to ensure backward compatibility and modern forward-looking research:

1. **Primary Python 3.14 Research Environment (`research/.venv314/`):**
   - **Python Version:** `Python 3.14.10` (Clang 21.0.0, native Apple Silicon `arm64`).
   - **Status:** Fully configured, verified, and passing 100% of automated tests (16/16 green).
   - **Dependency Lockfile:** [`research/requirements-py314-lock.txt`](file:///Users/vereshwarapupraveenkumar/VISION%20FREE/research/requirements-py314-lock.txt).
2. **Legacy Python 3.9 Baseline Environment (`research/.venv/`):**
   - **Python Version:** `Python 3.9.6` (Clang 21.0.0, Apple Silicon `arm64`).
   - **Status:** Fully functional, preserved for historical reproducibility and regression verification (16/16 green).
   - **Dependency Lockfile:** [`research/requirements-lock.txt`](file:///Users/vereshwarapupraveenkumar/VISION%20FREE/research/requirements-lock.txt).

### Git Exclusion:
Both environments (`research/.venv/` and `research/.venv314/`) are strictly excluded in `research/.gitignore`. Neither virtual environment is tracked in Git.

---

## 3. Environment Activation Instructions

### Python 3.14 Research Environment (`.venv314`) — RECOMMENDED
```bash
# macOS / Linux (bash / zsh):
source research/.venv314/bin/activate

# Verify Python version and architecture:
python -c "import platform, sys; print(sys.version); print(platform.machine())"

# Execute test suite:
PYTHONPATH=research/src pytest research/tests/ -v
```

### Windows Python 3.14 Setup (PowerShell / Command Prompt):
```powershell
# 1. Install Python 3.14 from python.org or via winget:
# winget install Python.Python.3.14

# 2. Create environment using Python Launcher:
py -3.14 -m venv research\.venv314

# 3. Activate:
.\research\.venv314\Scripts\Activate.ps1

# 4. Install dependencies from py314 lockfile:
pip install -r research\requirements-py314-lock.txt

# 5. Run test suite:
$env:PYTHONPATH="research\src"
pytest research\tests\ -v
```

### Legacy Python 3.9 Environment (`.venv`)
```bash
# macOS / Linux:
source research/.venv/bin/activate
PYTHONPATH=research/src pytest research/tests/ -v

# Windows (PowerShell):
.\research\.venv\Scripts\Activate.ps1
```

To deactivate any active virtual environment:
```bash
deactivate
```

---

## 4. Required Scientific Packages

### Python 3.14 Dependency Stack (`research/requirements-py314-lock.txt`):

| Package | Pinned Version in `.venv314` | Primary Role in Research Stack |
| :--- | :---: | :--- |
| **NumPy** | `2.5.5` | N-dimensional array processing and complex pupil matrix math |
| **SciPy** | `1.18.1` | Fast Fourier Transforms (`scipy.fft`) and optimization (`scipy.optimize`) |
| **Matplotlib** | `3.11.2` | Cross-sectional luminance profile plotting and MTF visualization |
| **Pillow** | `13.0.0` | Synthetic optotype drawing, format conversion, and image I/O |
| **scikit-image** | `0.26.0` | Structural Similarity (`ssim`), PSNR, and image quality metrics |
| **pytest** | `9.2.0` | Automated testing of dataset integrity, diversity, and reproducibility |

### Legacy Python 3.9 Dependency Stack (`research/requirements-lock.txt`):
- `numpy==2.0.2`, `scipy==1.13.1`, `matplotlib==3.9.4`, `pillow==11.3.0`, `scikit-image==0.24.0`, `pytest==8.4.2`.

| Package | Installed Version | Primary Role in Research Stack |
| :--- | :---: | :--- |
| **numpy** | `2.0.2` | N-dimensional array processing and complex pupil matrix math |
| **scipy** | `1.13.1` | Fast Fourier Transforms (`scipy.fft`) and optimization (`scipy.optimize`) |
| **matplotlib** | `3.9.4` | Cross-sectional luminance profile plotting and MTF visualization |
| **pillow** | `11.3.0` | Synthetic optotype drawing, format conversion, and image I/O |
| **scikit-image** | `0.24.0` | Structural Similarity (`ssim`), PSNR, and image quality metrics |
| **pytest** | `8.4.2` | Automated testing of dataset integrity, diversity, and reproducibility |

- **Pillow & FreeType:** Pillow `11.3.0` compiled with FreeType `2.13.3`.
- **OpenCV:** Omitted intentionally to keep the scientific stack lightweight and deterministic.

---

## 5. Photometric Calibration: Linear-Light Luminance vs. sRGB

A critical requirement in computational optics is distinguishing **physical linear-light luminance** from **gamma-encoded display code values**.

### Transfer Functions (IEC 61966-2-1):
- **Linear Relative Luminance ($L \in [0.0, 1.0]$) to 8-Bit sRGB Code ($S_8 \in [0, 255]$):**
  $$S = \begin{cases} 12.92 L, & L \le 0.0031308 \\ 1.055 L^{1/2.4} - 0.055, & L > 0.0031308 \end{cases}, \qquad S_8 = \text{round}(255 \times S)$$
- **sRGB Code ($S_8 \in [0, 255]$) to Linear Relative Luminance ($L \in [0.0, 1.0]$):**
  $$S = \frac{S_8}{255.0}, \qquad L = \begin{cases} \frac{S}{12.92}, & S \le 0.04045 \\ \left(\frac{S + 0.055}{1.055}\right)^{2.4}, & S > 0.04045 \end{cases}$$

### Michelson Contrast in Linear Luminance:
Michelson contrast is physically defined in **linear-light luminance**, never raw gamma-compressed sRGB code values:
$$C = \frac{L_{\max} - L_{\min}}{L_{\max} + L_{\min}}$$

All contrast targets (step wedges, uniform patches, and bar gratings) are defined first in linear relative luminance around $L_{\text{mean}} = 0.50$, and then converted to sRGB for PNG serialization. The manifest records both target linear values, encoded sRGB integer bytes, and reconstructed linear luminance values.

---

## 6. Dataset Structure & Manifest Schema

All benchmark targets are stored in `research/data/benchmarks/`:

```
research/data/benchmarks/
├── targets/                             # 42 canonical PNG targets (512x512)
│   ├── text_sans_10pt_regular_bow.png
│   ├── text_sans_14pt_regular_bow.png
│   ├── text_sans_14pt_bold_bow.png
│   ├── text_sans_18pt_regular_bow.png
│   ├── text_sans_24pt_bold_bow.png
│   ├── text_sans_32pt_bold_bow.png
│   ├── text_sans_14pt_regular_wob.png
│   ├── text_serif_14pt_regular_bow.png
│   ├── text_mono_14pt_regular_bow.png
│   ├── line_horizontal_w1_s4.png
│   ├── line_vertical_w2_s8.png
│   ├── line_diagonal_45deg_w2_s8.png
│   ├── geom_checkerboard_med_16px.png
│   ├── geom_radial_siemens_star.png
│   ├── contrast_stepwedge_8step.png
│   ├── contrast_bars_michelson_100.png
│   ├── edge_vertical_knife.png
│   ├── edge_slanted_iso12233.png
│   └── ...
└── dataset_manifest.json               # Auto-generated JSON manifest
```

### Slanted-Edge Compliance Disclaimer:
The slanted-edge target (`edge_slanted_iso12233.png`) carries the explicit metadata disclaimer:
> *"Illustrative slanted-edge target based on the slanted-edge measurement principle; not claimed to be ISO 12233 compliant."*

---

## 7. Cross-Platform Font Reproducibility

### Exact Font Provenance on Reference Host (macOS Apple Silicon):

| Font Face | Canonical Host File Path | SHA-256 Hash (Prefix) |
| :--- | :--- | :--- |
| **Arial Regular** | `/System/Library/Fonts/Supplemental/Arial.ttf` | `525979822591a344...` |
| **Arial Bold** | `/System/Library/Fonts/Supplemental/Arial Bold.ttf` | `d72db21f9242aedd...` |
| **Times New Roman Regular** | `/System/Library/Fonts/Supplemental/Times New Roman.ttf` | `f3b4ffff71c2a0c7...` |
| **Times New Roman Bold** | `/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf` | `50f5b1f27b7d3462...` |
| **Courier New Regular** | `/System/Library/Fonts/Supplemental/Courier New.ttf` | `c886ca3172d8ce91...` |
| **Courier New Bold** | `/System/Library/Fonts/Supplemental/Courier New Bold.ttf` | `500df4e46b554ae7...` |

### Same-Machine vs. Cross-Platform Reproducibility:
- **Same-Machine Bit-for-Bit Reproducibility:** Generating the dataset on the reference machine with seed `42` yields bit-for-bit identical files with matching SHA-256 hashes (verified by `test_dataset_generation_reproducibility`).
- **Cross-Platform Reproducibility:** Different operating systems (macOS, Windows, Linux) bundle distinct vendor versions of TrueType fonts and use different rasterizer raster hintings (FreeType vs. DirectWrite vs. CoreText). Therefore, cross-platform generation produces identical typographic parameters and identical layout geometry, but subtle subpixel antialiasing differences may alter raw file hashes.
- **No Silent Fallbacks:** If a requested font family cannot be located on the host, the generator throws an explicit `FileNotFoundError` rather than silently substituting a fallback font.

---

## 8. How to Regenerate Benchmark Images

To regenerate all 42 synthetic benchmark targets and update `dataset_manifest.json`:

```bash
# Ensure virtual environment is activated
source research/.venv/bin/activate

# Execute generator module
PYTHONPATH=research/src python -m visionfree_research.dataset_generator
```

---

## 9. How to Run Automated Tests

The test suite validates dataset integrity, photometric accuracy, SHA-256 hashes, dimensional accuracy, reproducibility, diversity across all categories, and absence of clinical prescription data:

```bash
# Run full pytest suite with verbose output
PYTHONPATH=research/src pytest research/tests/ -v
```

Expected result:
```
============================== 16 passed in 0.42s ==============================
```

---

## 10. Current Scientific Limitations

1. **Monocular Paraxial Assumption:** Phase 5.0 benchmarks represent planar 2D targets. Real viewing involves binocular convergence and accommodations that vary dynamically.
2. **Lower-Order Model Boundary:** As detailed in `PHASE5_RESEARCH_PLAN.md`, spherocylindrical prescriptions do not capture corneal higher-order aberrations or ocular media scatter.
3. **Display Clipping:** 2D screens cannot emit negative luminance or exceed maximum display white ($L \in [0, 1]$), which limits optical deconvolution.
