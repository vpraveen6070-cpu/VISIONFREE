"""
dataset_generator.py — Deterministic Synthetic Benchmark Dataset Generator
Part of VISIONFREE Phase 5.0 Research Environment.

Generates controlled, reproducible synthetic visual targets for:
- Text targets (black-on-white, white-on-black, multiple fonts, sizes, weights)
- Line patterns (horizontal, vertical, diagonal, multiple stroke widths and spacings)
- Geometric patterns (checkerboards, concentric rings, Siemens star, repeating shapes)
- Contrast targets (grayscale step wedges, uniform patches, calibrated Michelson contrast bars)
- Edge targets (knife-edges, ISO 12233 slanted edge, disc and square boundaries)

Zero optical blur or pre-compensation is applied. Images represent pristine ground-truth targets.
"""

from __future__ import annotations

import math
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
from PIL import Image, ImageDraw, ImageFont

try:
    from .dataset_manifest import compute_sha256, save_manifest
except (ImportError, ValueError):
    from visionfree_research.dataset_manifest import compute_sha256, save_manifest

# Standard benchmark image resolution
DEFAULT_WIDTH = 512
DEFAULT_HEIGHT = 512
DEFAULT_SEED = 42


def linear_to_srgb(l: np.ndarray | float | list) -> np.ndarray:
    """
    Convert linear relative luminance L in [0.0, 1.0] to 8-bit sRGB code values in [0, 255]
    per IEC 61966-2-1 standard transfer function.
    """
    l_arr = np.asarray(l, dtype=np.float64)
    s = np.where(
        l_arr <= 0.0031308,
        12.92 * l_arr,
        1.055 * np.power(np.maximum(l_arr, 1e-12), 1.0 / 2.4) - 0.055
    )
    return np.clip(np.round(s * 255.0), 0, 255).astype(np.uint8)


def srgb_to_linear(s8: np.ndarray | int | list) -> np.ndarray:
    """
    Convert 8-bit sRGB code values in [0, 255] to linear relative luminance L in [0.0, 1.0]
    per IEC 61966-2-1 standard transfer function.
    """
    s = np.asarray(s8, dtype=np.float64) / 255.0
    return np.where(
        s <= 0.04045,
        s / 12.92,
        np.power((s + 0.055) / 1.055, 2.4)
    )


def resolve_font(
    family: str = "sans",
    size_pt: int = 14,
    weight: str = "regular"
) -> Tuple[ImageFont.ImageFont, Dict[str, Any]]:
    """
    Resolve a true-type font based on family and weight across macOS, Windows, and Linux.
    Fails explicitly with FileNotFoundError if the requested font cannot be located,
    preventing silent font substitution that would compromise research reproducibility.
    
    Returns:
        Tuple of (ImageFont instance, font_metadata dict)
    """
    family = family.lower()
    weight = weight.lower()
    is_bold = "bold" in weight

    if family == "default":
        return ImageFont.load_default(), {
            "family": "default",
            "weight": weight,
            "size_pt": size_pt,
            "font_name": "Pillow_load_default",
            "font_file": "builtin",
            "is_system_font": False
        }

    candidates: List[str] = []

    if family in ("sans", "sans-serif", "arial"):
        # macOS
        candidates.append(
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if is_bold
            else "/System/Library/Fonts/Supplemental/Arial.ttf"
        )
        candidates.append("/System/Library/Fonts/Helvetica.ttc")
        # Windows
        candidates.append(r"C:\Windows\Fonts\arialbd.ttf" if is_bold else r"C:\Windows\Fonts\arial.ttf")
        # Linux
        candidates.append(
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if is_bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
        )

    elif family in ("serif", "times"):
        # macOS
        candidates.append(
            "/System/Library/Fonts/Supplemental/Times New Roman Bold.ttf" if is_bold
            else "/System/Library/Fonts/Supplemental/Times New Roman.ttf"
        )
        # Windows
        candidates.append(r"C:\Windows\Fonts\timesbd.ttf" if is_bold else r"C:\Windows\Fonts\times.ttf")
        # Linux
        candidates.append(
            "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf" if is_bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"
        )

    elif family in ("mono", "monospace", "courier"):
        # macOS
        candidates.append(
            "/System/Library/Fonts/Supplemental/Courier New Bold.ttf" if is_bold
            else "/System/Library/Fonts/Supplemental/Courier New.ttf"
        )
        candidates.append("/System/Library/Fonts/Menlo.ttc")
        # Windows
        candidates.append(r"C:\Windows\Fonts\courbd.ttf" if is_bold else r"C:\Windows\Fonts\cour.ttf")
        # Linux
        candidates.append(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf" if is_bold
            else "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
        )
    else:
        raise ValueError(f"Unknown font family request: '{family}'. Supported: 'sans', 'serif', 'mono', 'default'")

    selected_font: Optional[ImageFont.ImageFont] = None
    selected_path: Optional[str] = None

    for c in candidates:
        if os.path.exists(c):
            try:
                selected_font = ImageFont.truetype(c, size=size_pt)
                selected_path = c
                break
            except Exception:
                continue

    if selected_font is None:
        raise FileNotFoundError(
            f"Could not locate required system font for family='{family}', weight='{weight}'. "
            f"Searched candidate paths: {candidates}. "
            "Silent font substitution is prohibited to preserve reproducible rendering. "
            "Please install the requested system font or specify an explicit font path."
        )

    font_info = {
        "family": family,
        "weight": weight,
        "size_pt": size_pt,
        "font_name": Path(selected_path).stem if selected_path else "unknown",
        "font_file": selected_path,
        "is_system_font": True
    }

    return selected_font, font_info


class BenchmarkDatasetGenerator:
    """
    Deterministic synthetic benchmark image generator for computational optics research.
    """

    def __init__(
        self,
        output_dir: str | Path,
        seed: int = DEFAULT_SEED,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT
    ):
        self.output_dir = Path(output_dir)
        self.targets_dir = self.output_dir / "targets"
        self.targets_dir.mkdir(parents=True, exist_ok=True)
        self.seed = seed
        self.width = width
        self.height = height
        self.rng = np.random.default_rng(seed)
        self.image_entries: List[Dict[str, Any]] = []

    def _save_image(
        self,
        img: Image.Image,
        filename: str,
        category: str,
        parameters: Dict[str, Any],
        font_info: Optional[Dict[str, Any]] = None,
        color_mode: str = "L"
    ) -> Dict[str, Any]:
        """Save image to disk, compute hash, and record manifest entry."""
        if img.mode != color_mode:
            img = img.convert(color_mode)

        filepath = self.targets_dir / filename
        img.save(filepath, format="PNG")

        sha = compute_sha256(filepath)
        entry = {
            "filename": filename,
            "rel_path": f"targets/{filename}",
            "category": category,
            "width": img.width,
            "height": img.height,
            "color_mode": color_mode,
            "font_info": font_info,
            "parameters": parameters,
            "sha256": sha
        }
        self.image_entries.append(entry)
        return entry

    # -------------------------------------------------------------------------
    # Category A: Text Targets
    # -------------------------------------------------------------------------
    def generate_text_targets(self) -> None:
        """Generate text targets with varying polarity, families, sizes, weights, and spacing."""
        text_configs = [
            # Standard pangram + optotype lines
            ("sans", 10, "regular", "bow", 1.2, "text_sans_10pt_regular_bow.png"),
            ("sans", 14, "regular", "bow", 1.4, "text_sans_14pt_regular_bow.png"),
            ("sans", 14, "bold", "bow", 1.4, "text_sans_14pt_bold_bow.png"),
            ("sans", 18, "regular", "bow", 1.4, "text_sans_18pt_regular_bow.png"),
            ("sans", 24, "bold", "bow", 1.5, "text_sans_24pt_bold_bow.png"),
            ("sans", 32, "bold", "bow", 1.5, "text_sans_32pt_bold_bow.png"),
            # Reverse polarity (white on black)
            ("sans", 14, "regular", "wob", 1.4, "text_sans_14pt_regular_wob.png"),
            ("sans", 18, "bold", "wob", 1.4, "text_sans_18pt_bold_wob.png"),
            # Serif
            ("serif", 14, "regular", "bow", 1.4, "text_serif_14pt_regular_bow.png"),
            ("serif", 14, "bold", "bow", 1.4, "text_serif_14pt_bold_bow.png"),
            # Monospace
            ("mono", 14, "regular", "bow", 1.4, "text_mono_14pt_regular_bow.png"),
            # Line spacing variations
            ("sans", 14, "regular", "bow", 1.1, "text_spacing_tight_bow.png"),
            ("sans", 14, "regular", "bow", 2.0, "text_spacing_loose_bow.png"),
        ]

        text_lines = [
            "VISIONFREE RESEARCH BENCHMARK",
            "The quick brown fox jumps over the lazy dog.",
            "Pack my box with five dozen liquor jugs.",
            "E C O D Z N   4 8 2 9 3 7 5 1",
            "Spherical Defocus & Astigmatic Optical Transfer Function",
            "High contrast typography legibility evaluation target."
        ]

        for family, size_pt, weight, polarity, line_spacing, filename in text_configs:
            bg_color = 255 if polarity == "bow" else 0
            fg_color = 0 if polarity == "bow" else 255

            im = Image.new("L", (self.width, self.height), color=bg_color)
            draw = ImageDraw.Draw(im)
            font, font_info = resolve_font(family, size_pt, weight)

            y_pos = 40
            line_step = int(size_pt * 1.33 * line_spacing)

            for line in text_lines:
                if y_pos + line_step > self.height - 20:
                    break
                draw.text((40, y_pos), line, font=font, fill=fg_color)
                y_pos += line_step

            params = {
                "font_family": family,
                "size_pt": size_pt,
                "weight": weight,
                "polarity": polarity,
                "line_spacing_factor": line_spacing,
                "bg_luminance": bg_color,
                "fg_luminance": fg_color
            }
            self._save_image(im, filename, "text", params, font_info=font_info, color_mode="L")

    # -------------------------------------------------------------------------
    # Category B: Line Patterns
    # -------------------------------------------------------------------------
    def generate_line_patterns(self) -> None:
        """Generate horizontal, vertical, diagonal, and crosshatch patterns."""
        line_configs = [
            ("horizontal", 1, 4, "line_horizontal_w1_s4.png"),
            ("horizontal", 2, 8, "line_horizontal_w2_s8.png"),
            ("horizontal", 4, 16, "line_horizontal_w4_s16.png"),
            ("vertical", 1, 4, "line_vertical_w1_s4.png"),
            ("vertical", 2, 8, "line_vertical_w2_s8.png"),
            ("vertical", 4, 16, "line_vertical_w4_s16.png"),
            ("diagonal_45", 2, 8, "line_diagonal_45deg_w2_s8.png"),
            ("diagonal_135", 2, 8, "line_diagonal_135deg_w2_s8.png"),
            ("crosshatch", 1, 8, "line_crosshatch_w1_s8.png"),
        ]

        for orientation, stroke_w, spacing, filename in line_configs:
            arr = np.ones((self.height, self.width), dtype=np.uint8) * 255

            if orientation == "horizontal":
                period = stroke_w + spacing
                for y in range(0, self.height, period):
                    arr[y : min(y + stroke_w, self.height), :] = 0

            elif orientation == "vertical":
                period = stroke_w + spacing
                for x in range(0, self.width, period):
                    arr[:, x : min(x + stroke_w, self.width)] = 0

            elif orientation == "diagonal_45":
                period = stroke_w + spacing
                Y, X = np.indices((self.height, self.width))
                diag = (X + Y) % period
                arr[diag < stroke_w] = 0

            elif orientation == "diagonal_135":
                period = stroke_w + spacing
                Y, X = np.indices((self.height, self.width))
                diag = (X - Y) % period
                arr[diag < stroke_w] = 0

            elif orientation == "crosshatch":
                period = stroke_w + spacing
                for y in range(0, self.height, period):
                    arr[y : min(y + stroke_w, self.height), :] = 0
                for x in range(0, self.width, period):
                    arr[:, x : min(x + stroke_w, self.width)] = 0

            im = Image.fromarray(arr)
            params = {
                "orientation": orientation,
                "stroke_width_px": stroke_w,
                "spacing_px": spacing,
                "spatial_period_px": stroke_w + spacing
            }
            self._save_image(im, filename, "line", params, color_mode="L")

    # -------------------------------------------------------------------------
    # Category C: Geometric Patterns
    # -------------------------------------------------------------------------
    def generate_geometric_patterns(self) -> None:
        """Generate checkerboards, concentric rings, Siemens star, and fine repeating structures."""
        # 1. Checkerboards
        for block_size, name in [(4, "fine_4px"), (16, "med_16px"), (64, "coarse_64px")]:
            Y, X = np.indices((self.height, self.width))
            cb = ((X // block_size) + (Y // block_size)) % 2
            arr = (cb * 255).astype(np.uint8)
            im = Image.fromarray(arr)
            self._save_image(
                im,
                f"geom_checkerboard_{name}.png",
                "geometric",
                {"pattern": "checkerboard", "block_size_px": block_size},
                color_mode="L"
            )

        # 2. Concentric circular rings
        Y, X = np.indices((self.height, self.width))
        cx, cy = self.width / 2.0, self.height / 2.0
        R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        rings = (np.sin(R * 0.15) > 0).astype(np.uint8) * 255
        im_rings = Image.fromarray(rings)
        self._save_image(
            im_rings,
            "geom_concentric_circles.png",
            "geometric",
            {"pattern": "concentric_rings", "radial_frequency_factor": 0.15},
            color_mode="L"
        )

        # 3. Radial Siemens Star (Spoke target: 36 spokes / 72 sectors)
        num_spokes = 36
        Theta = np.arctan2(Y - cy, X - cx)
        star = ((np.sin(num_spokes * Theta) > 0)).astype(np.uint8) * 255
        im_star = Image.fromarray(star)
        self._save_image(
            im_star,
            "geom_radial_siemens_star.png",
            "geometric",
            {"pattern": "siemens_star", "spokes": num_spokes, "sectors": num_spokes * 2},
            color_mode="L"
        )

        # 4. Orthogonal Fine Grid (8px grid)
        grid_arr = np.ones((self.height, self.width), dtype=np.uint8) * 255
        grid_arr[::8, :] = 0
        grid_arr[:, ::8] = 0
        im_grid = Image.fromarray(grid_arr)
        self._save_image(
            im_grid,
            "geom_grid_fine_8px.png",
            "geometric",
            {"pattern": "grid", "pitch_px": 8, "line_width_px": 1},
            color_mode="L"
        )

        # 5. Repeating Shapes (Array of triangles, circles, and diamonds)
        im_shapes = Image.new("L", (self.width, self.height), color=255)
        draw = ImageDraw.Draw(im_shapes)
        cell = 64
        for r in range(2, 6):
            for c in range(2, 6):
                x0 = c * cell + 16
                y0 = r * cell + 16
                x1 = x0 + 32
                y1 = y0 + 32
                shape_type = (r + c) % 3
                if shape_type == 0:
                    draw.ellipse([x0, y0, x1, y1], fill=0)
                elif shape_type == 1:
                    draw.rectangle([x0, y0, x1, y1], fill=0)
                else:
                    mid_x = (x0 + x1) // 2
                    mid_y = (y0 + y1) // 2
                    draw.polygon([(mid_x, y0), (x1, mid_y), (mid_x, y1), (x0, mid_y)], fill=0)

        self._save_image(
            im_shapes,
            "geom_repeating_shapes.png",
            "geometric",
            {"pattern": "repeating_shapes", "cell_size": cell},
            color_mode="L"
        )

    # -------------------------------------------------------------------------
    # Category D: Contrast Targets (Photometrically Calibrated in Linear Luminance)
    # -------------------------------------------------------------------------
    def generate_contrast_targets(self) -> None:
        """
        Generate step wedges, flat calibration patches, and Michelson contrast gratings
        calibrated in physical linear-light relative luminance L in [0, 1] and encoded to sRGB.
        """
        # 1. 8-step linear luminance wedge
        arr_8 = np.zeros((self.height, self.width), dtype=np.uint8)
        step_w8 = self.width // 8
        levels_linear_8 = np.linspace(0.0, 1.0, 8, dtype=np.float64)
        levels_srgb_8 = linear_to_srgb(levels_linear_8)
        for i in range(8):
            arr_8[:, i * step_w8 : (i + 1) * step_w8] = levels_srgb_8[i]
        im_8 = Image.fromarray(arr_8)
        self._save_image(
            im_8,
            "contrast_stepwedge_8step.png",
            "contrast",
            {
                "type": "step_wedge",
                "num_steps": 8,
                "target_linear_luminance_levels": [round(float(v), 5) for v in levels_linear_8],
                "encoded_srgb_levels": levels_srgb_8.tolist(),
                "photometric_standard": "IEC 61966-2-1"
            },
            color_mode="L"
        )

        # 2. 16-step linear luminance wedge
        arr_16 = np.zeros((self.height, self.width), dtype=np.uint8)
        step_w16 = self.width // 16
        levels_linear_16 = np.linspace(0.0, 1.0, 16, dtype=np.float64)
        levels_srgb_16 = linear_to_srgb(levels_linear_16)
        for i in range(16):
            arr_16[:, i * step_w16 : (i + 1) * step_w16] = levels_srgb_16[i]
        im_16 = Image.fromarray(arr_16)
        self._save_image(
            im_16,
            "contrast_stepwedge_16step.png",
            "contrast",
            {
                "type": "step_wedge",
                "num_steps": 16,
                "target_linear_luminance_levels": [round(float(v), 5) for v in levels_linear_16],
                "encoded_srgb_levels": levels_srgb_16.tolist(),
                "photometric_standard": "IEC 61966-2-1"
            },
            color_mode="L"
        )

        # 3. Uniform Calibrated Linear Patches (5 square patches at 5%, 25%, 50%, 75%, 95% linear luminance)
        patch_linear = [0.05, 0.25, 0.50, 0.75, 0.95]
        patch_srgb = linear_to_srgb(patch_linear)
        reconstructed_linear = srgb_to_linear(patch_srgb)

        im_patches = Image.new("L", (self.width, self.height), color=int(linear_to_srgb(0.50)))
        draw = ImageDraw.Draw(im_patches)
        px_coords = [(64, 64), (320, 64), (192, 192), (64, 320), (320, 320)]
        for (px, py), lvl_srgb in zip(px_coords, patch_srgb):
            draw.rectangle([px, py, px + 128, py + 128], fill=int(lvl_srgb), outline=0)
        self._save_image(
            im_patches,
            "contrast_uniform_patches.png",
            "contrast",
            {
                "type": "uniform_patches",
                "target_linear_luminances": patch_linear,
                "encoded_srgb_levels": patch_srgb.tolist(),
                "reconstructed_linear_luminances": [round(float(v), 5) for v in reconstructed_linear],
                "photometric_standard": "IEC 61966-2-1"
            },
            color_mode="L"
        )

        # 4. Calibrated Michelson Contrast Bar Gratings in Linear Luminance
        # Michelson Contrast C = (L_max - L_min) / (L_max + L_min)
        # Using mean linear luminance L_mean = 0.50:
        # L_max = L_mean * (1 + C), L_min = L_mean * (1 - C)
        contrast_specs = [
            (1.00, "contrast_bars_michelson_100.png"),
            (0.50, "contrast_bars_michelson_50.png"),
            (0.25, "contrast_bars_michelson_25.png"),
            (0.10, "contrast_bars_michelson_10.png"),
            (0.05, "contrast_bars_michelson_05.png"),
        ]

        bar_period = 32  # 16px high, 16px low
        l_mean = 0.50
        for c_val, fname in contrast_specs:
            l_max = l_mean * (1.0 + c_val)
            l_min = l_mean * (1.0 - c_val)
            s_max = int(linear_to_srgb(l_max))
            s_min = int(linear_to_srgb(l_min))
            l_rec_max = float(srgb_to_linear(s_max))
            l_rec_min = float(srgb_to_linear(s_min))
            c_actual_linear = (
                (l_rec_max - l_rec_min) / (l_rec_max + l_rec_min)
                if (l_rec_max + l_rec_min) > 0 else 0.0
            )

            arr_bars = np.zeros((self.height, self.width), dtype=np.uint8)
            X = np.arange(self.width)
            bars = (X % bar_period < bar_period // 2)
            arr_bars[:, bars] = s_max
            arr_bars[:, ~bars] = s_min
            im_bar = Image.fromarray(arr_bars)
            self._save_image(
                im_bar,
                fname,
                "contrast",
                {
                    "type": "michelson_contrast_grating",
                    "target_linear_michelson_contrast": c_val,
                    "target_linear_luminance_max": round(l_max, 5),
                    "target_linear_luminance_min": round(l_min, 5),
                    "encoded_srgb_max": s_max,
                    "encoded_srgb_min": s_min,
                    "reconstructed_linear_luminance_max": round(l_rec_max, 5),
                    "reconstructed_linear_luminance_min": round(l_rec_min, 5),
                    "actual_linear_michelson_contrast": round(c_actual_linear, 5),
                    "bar_period_px": bar_period,
                    "photometric_standard": "IEC 61966-2-1"
                },
                color_mode="L"
            )

    # -------------------------------------------------------------------------
    # Category E: Edge Targets
    # -------------------------------------------------------------------------
    def generate_edge_targets(self) -> None:
        """Generate vertical knife-edge, horizontal knife-edge, illustrative slanted edge, and shape boundaries."""
        # 1. Vertical Knife-Edge (step transition at x = 256)
        arr_v = np.zeros((self.height, self.width), dtype=np.uint8)
        arr_v[:, self.width // 2 :] = 255
        im_v = Image.fromarray(arr_v)
        self._save_image(
            im_v,
            "edge_vertical_knife.png",
            "edge",
            {"type": "vertical_knife_edge", "transition_x": self.width // 2},
            color_mode="L"
        )

        # 2. Horizontal Knife-Edge (step transition at y = 256)
        arr_h = np.zeros((self.height, self.width), dtype=np.uint8)
        arr_h[self.height // 2 :, :] = 255
        im_h = Image.fromarray(arr_h)
        self._save_image(
            im_h,
            "edge_horizontal_knife.png",
            "edge",
            {"type": "horizontal_knife_edge", "transition_y": self.height // 2},
            color_mode="L"
        )

        # 3. Illustrative Slanted Edge (5.0 degrees tilt from vertical)
        # Equation of edge line: (X - cx) - tan(5 deg) * (Y - cy) >= 0
        tilt_deg = 5.0
        tilt_rad = math.radians(tilt_deg)
        cx, cy = self.width / 2.0, self.height / 2.0
        Y, X = np.indices((self.height, self.width))
        slanted_edge = ((X - cx) - math.tan(tilt_rad) * (Y - cy)) >= 0
        arr_slant = (slanted_edge * 255).astype(np.uint8)
        im_slant = Image.fromarray(arr_slant)
        self._save_image(
            im_slant,
            "edge_slanted_iso12233.png",
            "edge",
            {
                "type": "illustrative_slanted_edge",
                "description": "Illustrative slanted-edge target based on the slanted-edge measurement principle; not claimed to be ISO 12233 compliant.",
                "tilt_angle_degrees": tilt_deg,
                "center_x": cx,
                "center_y": cy
            },
            color_mode="L"
        )

        # 4. Centered Solid Disc Boundary (radius = 120 px)
        R = np.sqrt((X - cx) ** 2 + (Y - cy) ** 2)
        disc_arr = ((R <= 120.0) * 255).astype(np.uint8)
        im_disc = Image.fromarray(disc_arr)
        self._save_image(
            im_disc,
            "edge_disc_boundary.png",
            "edge",
            {"type": "disc_boundary", "radius_px": 120, "center": [cx, cy]},
            color_mode="L"
        )

        # 5. Centered Solid Square Boundary (200x200 px)
        sq_arr = np.zeros((self.height, self.width), dtype=np.uint8)
        sq_half = 100
        sq_arr[int(cy - sq_half) : int(cy + sq_half), int(cx - sq_half) : int(cx + sq_half)] = 255
        im_sq = Image.fromarray(sq_arr)
        self._save_image(
            im_sq,
            "edge_square_boundary.png",
            "edge",
            {"type": "square_boundary", "side_px": 200, "center": [cx, cy]},
            color_mode="L"
        )

    # -------------------------------------------------------------------------
    # Generator Orchestration & Manifest Writing
    # -------------------------------------------------------------------------
    def generate_all(self) -> Dict[str, Any]:
        """Generate the full benchmark dataset and write dataset_manifest.json."""
        self.image_entries.clear()

        self.generate_text_targets()
        self.generate_line_patterns()
        self.generate_geometric_patterns()
        self.generate_contrast_targets()
        self.generate_edge_targets()

        manifest = {
            "dataset_name": "VISIONFREE-Synthetic-Benchmarks",
            "dataset_version": "1.0.0",
            "generation_date": datetime.now(timezone.utc).isoformat(),
            "generator_version": "0.1.0",
            "random_seed": self.seed,
            "total_image_count": len(self.image_entries),
            "categories": ["text", "line", "geometric", "contrast", "edge"],
            "standard_dimensions": {"width": self.width, "height": self.height},
            "color_encoding": "sRGB_8bit_gamma_encoded",
            "photometric_transfer_standard": "IEC 61966-2-1",
            "photometric_interpretation": "Contrast and step targets are defined in physical linear relative luminance L in [0, 1] and encoded to sRGB code values in [0, 255]. Text targets are defined with standard digital black/white endpoints.",
            "disclaimer": "Synthetic computational vision research targets. Not clinically calibrated optotypes.",
            "images": self.image_entries
        }

        manifest_path = self.output_dir / "dataset_manifest.json"
        save_manifest(manifest, manifest_path)
        return manifest


def generate_benchmark_dataset(
    output_dir: str | Path,
    seed: int = DEFAULT_SEED,
    width: int = DEFAULT_WIDTH,
    height: int = DEFAULT_HEIGHT
) -> Dict[str, Any]:
    """Convenience functional interface to generate the dataset."""
    gen = BenchmarkDatasetGenerator(output_dir, seed=seed, width=width, height=height)
    return gen.generate_all()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Generate VISIONFREE Synthetic Benchmark Dataset")
    parser.add_argument(
        "--output-dir",
        type=str,
        default=str(Path(__file__).resolve().parents[2] / "data" / "benchmarks"),
        help="Directory where targets/ and dataset_manifest.json will be saved"
    )
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED, help="Deterministic random seed")
    args = parser.parse_args()

    manifest = generate_benchmark_dataset(args.output_dir, seed=args.seed)
    print(f"Generated {manifest['total_image_count']} benchmark images in {args.output_dir}")
