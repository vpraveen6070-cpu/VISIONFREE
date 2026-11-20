"""
test_dataset.py — Test Suite for Synthetic Benchmark Dataset and Manifest
Part of VISIONFREE Phase 5.0 / 5.0.1 Research Environment.
"""

import json
import tempfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from visionfree_research.dataset_generator import (
    BenchmarkDatasetGenerator,
    generate_benchmark_dataset,
    linear_to_srgb,
    resolve_font,
    srgb_to_linear,
)
from visionfree_research.dataset_manifest import (
    compute_sha256,
    load_manifest,
    validate_manifest_integrity,
)


@pytest.fixture(scope="session")
def benchmark_dir():
    """Return the path to the canonical benchmark data directory."""
    pkg_root = Path(__file__).resolve().parents[1]
    return pkg_root / "data" / "benchmarks"


@pytest.fixture(scope="session")
def canonical_manifest(benchmark_dir):
    """Ensure benchmark dataset is generated and return parsed manifest."""
    manifest_path = benchmark_dir / "dataset_manifest.json"
    generate_benchmark_dataset(benchmark_dir, seed=42)
    return load_manifest(manifest_path)


# -----------------------------------------------------------------------------
# 1. Dataset Integrity Tests
# -----------------------------------------------------------------------------
def test_manifest_file_exists(benchmark_dir):
    manifest_path = benchmark_dir / "dataset_manifest.json"
    assert manifest_path.is_file(), f"Manifest missing at {manifest_path}"


def test_manifest_validation_function(benchmark_dir):
    manifest_path = benchmark_dir / "dataset_manifest.json"
    is_valid, errors = validate_manifest_integrity(manifest_path)
    assert is_valid, f"Manifest validation failed with errors: {errors}"
    assert len(errors) == 0


def test_all_images_exist_and_match_manifest(benchmark_dir, canonical_manifest):
    targets_dir = benchmark_dir / "targets"
    assert targets_dir.is_dir()

    images = canonical_manifest["images"]
    assert len(images) == canonical_manifest["total_image_count"]
    assert len(images) > 0

    for entry in images:
        filepath = targets_dir / entry["filename"]
        assert filepath.is_file(), f"Image file {entry['filename']} does not exist"
        assert filepath.stat().st_size > 0, f"Image {entry['filename']} is empty (0 bytes)"

        # Verify SHA-256
        actual_hash = compute_sha256(filepath)
        assert actual_hash == entry["sha256"], f"Checksum mismatch on {entry['filename']}"

        # Verify image dimensions and format via Pillow
        with Image.open(filepath) as im:
            assert im.format == "PNG", f"Expected PNG format for {entry['filename']}, got {im.format}"
            assert im.size == (entry["width"], entry["height"]), (
                f"Dimension mismatch for {entry['filename']}: expected {entry['width']}x{entry['height']}, "
                f"got {im.size}"
            )
            assert im.mode == entry["color_mode"], (
                f"Color mode mismatch for {entry['filename']}: expected {entry['color_mode']}, got {im.mode}"
            )


# -----------------------------------------------------------------------------
# 2. Reproducibility Tests
# -----------------------------------------------------------------------------
def test_dataset_generation_reproducibility():
    """Verify that generating dataset twice with the same seed produces byte-identical files."""
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        dir1 = Path(tmp1)
        dir2 = Path(tmp2)

        m1 = generate_benchmark_dataset(dir1, seed=42)
        m2 = generate_benchmark_dataset(dir2, seed=42)

        assert m1["total_image_count"] == m2["total_image_count"]
        assert len(m1["images"]) == len(m2["images"])

        for img1, img2 in zip(m1["images"], m2["images"]):
            assert img1["filename"] == img2["filename"]
            assert img1["sha256"] == img2["sha256"], (
                f"Non-deterministic generation for {img1['filename']}: {img1['sha256']} != {img2['sha256']}"
            )

            # Check byte-for-byte identity
            b1 = (dir1 / "targets" / img1["filename"]).read_bytes()
            b2 = (dir2 / "targets" / img2["filename"]).read_bytes()
            assert b1 == b2, f"Byte content mismatch for {img1['filename']}"


# -----------------------------------------------------------------------------
# 3. Dataset Diversity Tests
# -----------------------------------------------------------------------------
def test_dataset_categories_diversity(canonical_manifest):
    categories = set(canonical_manifest["categories"])
    expected_categories = {"text", "line", "geometric", "contrast", "edge"}
    assert expected_categories.issubset(categories)

    present_categories = {img["category"] for img in canonical_manifest["images"]}
    assert expected_categories == present_categories


def test_text_target_diversity(canonical_manifest):
    text_images = [img for img in canonical_manifest["images"] if img["category"] == "text"]
    assert len(text_images) >= 10, "Expected at least 10 text targets"

    # Polarity check
    polarities = {img["parameters"].get("polarity") for img in text_images}
    assert "bow" in polarities, "Missing black-on-white text"
    assert "wob" in polarities, "Missing white-on-black text"

    # Font size check
    sizes = {img["parameters"].get("size_pt") for img in text_images}
    assert {10, 14, 18, 24, 32}.issubset(sizes), f"Missing expected text font sizes: {sizes}"

    # Weights check
    weights = {img["parameters"].get("weight") for img in text_images}
    assert "regular" in weights
    assert "bold" in weights

    # Font info check
    for img in text_images:
        assert img["font_info"] is not None, f"Missing font_info in {img['filename']}"
        assert "family" in img["font_info"]
        assert "font_name" in img["font_info"]


def test_line_pattern_diversity(canonical_manifest):
    line_images = [img for img in canonical_manifest["images"] if img["category"] == "line"]
    assert len(line_images) >= 8

    orientations = {img["parameters"].get("orientation") for img in line_images}
    assert {"horizontal", "vertical", "diagonal_45", "diagonal_135", "crosshatch"}.issubset(orientations)

    widths = {img["parameters"].get("stroke_width_px") for img in line_images}
    assert {1, 2, 4}.issubset(widths), f"Missing stroke widths: {widths}"


def test_geometric_pattern_diversity(canonical_manifest):
    geom_images = [img for img in canonical_manifest["images"] if img["category"] == "geometric"]
    patterns = {img["parameters"].get("pattern") for img in geom_images}
    assert {"checkerboard", "concentric_rings", "siemens_star", "grid", "repeating_shapes"}.issubset(patterns)


def test_contrast_target_diversity(canonical_manifest):
    contrast_images = [img for img in canonical_manifest["images"] if img["category"] == "contrast"]
    types = {img["parameters"].get("type") for img in contrast_images}
    assert {"step_wedge", "uniform_patches", "michelson_contrast_grating"}.issubset(types)

    # Check varying Michelson contrast levels
    michelson_images = [
        img for img in contrast_images if img["parameters"].get("type") == "michelson_contrast_grating"
    ]
    c_values = {img["parameters"].get("target_linear_michelson_contrast") for img in michelson_images}
    assert {1.0, 0.5, 0.25, 0.1, 0.05}.issubset(c_values)


def test_edge_target_diversity(canonical_manifest):
    edge_images = [img for img in canonical_manifest["images"] if img["category"] == "edge"]
    types = {img["parameters"].get("type") for img in edge_images}
    assert {
        "vertical_knife_edge",
        "horizontal_knife_edge",
        "illustrative_slanted_edge",
        "disc_boundary",
        "square_boundary"
    }.issubset(types)


# -----------------------------------------------------------------------------
# 4. Photometric Calibration & sRGB Tests
# -----------------------------------------------------------------------------
def test_photometric_srgb_linear_roundtrip():
    """Verify that linear_to_srgb and srgb_to_linear accurately invert within 8-bit quantization limits."""
    # Test linear levels from 0 to 1
    lin = np.linspace(0.0, 1.0, 256)
    s8 = linear_to_srgb(lin)
    lin_rec = srgb_to_linear(s8)

    # Reconstructed linear luminance should match within 8-bit quantization resolution (max step ~0.004)
    max_err = np.max(np.abs(lin - lin_rec))
    assert max_err < 0.005, f"Linear roundtrip error too large: {max_err}"

    # Test all 8-bit integer codes round-trip identically
    codes = np.arange(256, dtype=np.uint8)
    lin_codes = srgb_to_linear(codes)
    codes_rec = linear_to_srgb(lin_codes)
    assert np.array_equal(codes, codes_rec), "Integer sRGB codes failed round-trip conservation"


def test_contrast_targets_photometric_accuracy(canonical_manifest):
    """Verify that contrast targets calculate Michelson contrast in physical linear luminance."""
    contrast_images = [img for img in canonical_manifest["images"] if img["category"] == "contrast"]

    for img in contrast_images:
        params = img["parameters"]
        assert params.get("photometric_standard") == "IEC 61966-2-1", (
            f"Missing photometric standard in {img['filename']}"
        )

        if params.get("type") == "michelson_contrast_grating":
            c_target = params["target_linear_michelson_contrast"]
            c_actual = params["actual_linear_michelson_contrast"]

            # Mathematical verification of linear formula: C = (Lmax - Lmin) / (Lmax + Lmin)
            l_max = params["reconstructed_linear_luminance_max"]
            l_min = params["reconstructed_linear_luminance_min"]
            computed_c = (l_max - l_min) / (l_max + l_min) if (l_max + l_min) > 0 else 0.0

            assert abs(computed_c - c_actual) < 1e-4
            # Tolerance for 8-bit integer rounding quantization is +/- 0.005
            assert abs(c_actual - c_target) < 0.005, (
                f"Michelson contrast deviation {abs(c_actual - c_target)} exceeds 8-bit quantization tolerance for {img['filename']}"
            )


# -----------------------------------------------------------------------------
# 5. Slanted-Edge Compliance & Disclaimer Tests
# -----------------------------------------------------------------------------
def test_slanted_edge_description_disclaimer(canonical_manifest):
    """Verify that slanted-edge target contains the exact mandated disclaimer."""
    slanted = next(
        img for img in canonical_manifest["images"]
        if img["filename"] == "edge_slanted_iso12233.png"
    )
    expected_desc = (
        "Illustrative slanted-edge target based on the slanted-edge measurement principle; "
        "not claimed to be ISO 12233 compliant."
    )
    assert slanted["parameters"]["type"] == "illustrative_slanted_edge"
    assert slanted["parameters"]["description"] == expected_desc


# -----------------------------------------------------------------------------
# 6. Cross-Platform Font Resolution & Safety Tests
# -----------------------------------------------------------------------------
def test_font_resolution_no_silent_fallback():
    """Ensure font resolution fails explicitly when a requested family cannot be found."""
    # Unknown family raises ValueError
    with pytest.raises(ValueError):
        resolve_font(family="nonexistent_family_xyz")

    # Explicit default request succeeds
    font_def, meta_def = resolve_font(family="default")
    assert meta_def["family"] == "default"
    assert meta_def["is_system_font"] is False


def test_no_prescription_data_in_manifest(canonical_manifest):
    """Ensure no clinical prescription terms or personal patient data appear in metadata."""
    forbidden_keys = {"sph", "cyl", "axis", "diopters", "prescription", "patient", "user_id"}
    for img in canonical_manifest["images"]:
        params = img.get("parameters", {})
        for forbidden in forbidden_keys:
            assert forbidden not in params, f"Found clinical prescription key '{forbidden}' in {img['filename']}"


def test_images_are_pristine_unblurred(benchmark_dir, canonical_manifest):
    """Verify that knife-edge targets possess pristine step transitions with zero blur."""
    targets_dir = benchmark_dir / "targets"
    v_knife = targets_dir / "edge_vertical_knife.png"
    assert v_knife.is_file()

    with Image.open(v_knife) as im:
        arr = list(im.getdata())
        unique_vals = set(arr)
        assert unique_vals == {0, 255}, f"Knife edge contains non-binary values {unique_vals}, indicating blur"
