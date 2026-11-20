"""
dataset_manifest.py — Manifest Management and Integrity Verification
Part of VISIONFREE Phase 5.0 Research Environment.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def compute_sha256(filepath: str | Path) -> str:
    """Compute the SHA-256 hexadecimal digest of a file."""
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def save_manifest(manifest_data: Dict[str, Any], filepath: str | Path) -> None:
    """Save manifest dictionary to JSON with standardized indentation and encoding."""
    path = Path(filepath)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest_data, f, indent=2, ensure_ascii=False)


def load_manifest(filepath: str | Path) -> Dict[str, Any]:
    """Load and parse manifest JSON file."""
    path = Path(filepath)
    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found at {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_manifest_integrity(
    manifest_path: str | Path,
    targets_dir: Optional[str | Path] = None
) -> Tuple[bool, List[str]]:
    """
    Validate the integrity of a dataset manifest and its referenced target files.
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors: List[str] = []
    m_path = Path(manifest_path)
    if not m_path.is_file():
        return False, [f"Manifest file does not exist: {m_path}"]

    try:
        manifest = load_manifest(m_path)
    except Exception as e:
        return False, [f"Failed to parse manifest JSON: {e}"]

    # Required top-level keys
    required_keys = [
        "dataset_name",
        "dataset_version",
        "generation_date",
        "generator_version",
        "random_seed",
        "total_image_count",
        "categories",
        "images"
    ]
    for key in required_keys:
        if key not in manifest:
            errors.append(f"Missing required top-level manifest key: '{key}'")

    if errors:
        return False, errors

    images = manifest.get("images", [])
    if len(images) != manifest.get("total_image_count"):
        errors.append(
            f"Image count mismatch: total_image_count={manifest.get('total_image_count')} "
            f"but found {len(images)} entries in 'images' array."
        )

    t_dir = Path(targets_dir) if targets_dir else m_path.parent / "targets"
    if not t_dir.is_dir():
        errors.append(f"Targets directory does not exist: {t_dir}")
        return False, errors

    for idx, entry in enumerate(images):
        fname = entry.get("filename")
        if not fname:
            errors.append(f"Entry at index {idx} has missing or empty 'filename'.")
            continue

        img_path = t_dir / fname
        if not img_path.is_file():
            errors.append(f"Referenced file not found on disk: {img_path}")
            continue

        # File size check
        if img_path.stat().st_size == 0:
            errors.append(f"Image file is empty (0 bytes): {img_path}")

        # Hash check
        expected_hash = entry.get("sha256")
        if not expected_hash:
            errors.append(f"Entry {fname} is missing 'sha256' hash in manifest.")
        else:
            actual_hash = compute_sha256(img_path)
            if actual_hash != expected_hash:
                errors.append(
                    f"Checksum mismatch for {fname}: expected {expected_hash}, computed {actual_hash}"
                )

        # Dimension and format check via Pillow if available
        try:
            from PIL import Image
            with Image.open(img_path) as im:
                if im.format != "PNG":
                    errors.append(f"File {fname} is not in PNG format (got {im.format}).")
                w, h = im.size
                if entry.get("width") != w or entry.get("height") != h:
                    errors.append(
                        f"Dimension mismatch for {fname}: manifest specifies ({entry.get('width')}, {entry.get('height')}) "
                        f"but actual image is ({w}, {h})."
                    )
                if entry.get("color_mode") and entry.get("color_mode") != im.mode:
                    errors.append(
                        f"Color mode mismatch for {fname}: manifest specifies {entry.get('color_mode')}, image is {im.mode}."
                    )
        except Exception as ex:
            errors.append(f"Failed to inspect image file {fname}: {ex}")

    is_valid = len(errors) == 0
    return is_valid, errors
