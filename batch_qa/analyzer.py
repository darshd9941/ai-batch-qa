"""Core image quality analysis engine."""
import os
import math
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field

try:
    from PIL import Image, ImageFilter, ImageStat
    import numpy as np
except ImportError:
    raise ImportError("Install Pillow and numpy: pip install Pillow numpy")


@dataclass
class QualityReport:
    filename: str
    path: str
    width: int
    height: int
    file_size_kb: float
    # Quality scores (0-100)
    sharpness: float = 0.0
    brightness: float = 0.0
    contrast: float = 0.0
    noise_level: float = 0.0
    artifact_score: float = 0.0
    overall_score: float = 0.0
    # Flags
    is_blurry: bool = False
    is_overexposed: bool = False
    is_underexposed: bool = False
    has_artifacts: bool = False
    has_text: bool = False
    # Metadata
    aspect_ratio: str = ""
    megapixels: float = 0.0
    format: str = ""
    mode: str = ""
    # Issues
    issues: list = field(default_factory=list)


def analyze_image(
    image_path: str,
    blur_threshold: float = 50.0,
    brightness_range: tuple = (40, 220),
) -> QualityReport:
    """Analyze a single image for quality issues."""
    path = Path(image_path)
    img = Image.open(str(path))
    arr = np.array(img.convert("RGB"))

    stat = ImageStat.Stat(img.convert("L"))

    # Basic metrics
    width, height = img.size
    file_size_kb = path.stat().st_size / 1024
    megapixels = (width * height) / 1_000_000
    aspect_ratio = f"{width}:{height}"
    if width > 0 and height > 0:
        from math import gcd
        g = gcd(width, height)
        aspect_ratio = f"{width // g}:{height // g}"

    # Sharpness (Laplacian variance)
    gray = img.convert("L")
    laplacian = gray.filter(ImageFilter.Kernel(
        size=(3, 3),
        kernel=[-1, -1, -1, -1, 8, -1, -1, -1, -1],
        scale=1,
        offset=0,
    ))
    lap_stat = ImageStat.Stat(laplacian)
    sharpness_var = lap_stat.var[0] if lap_stat.var[0] else 0
    sharpness = min(100, sharpness_var / 5.0)
    is_blurry = sharpness_var < blur_threshold

    # Brightness
    brightness = stat.mean[0]
    is_overexposed = brightness > brightness_range[1]
    is_underexposed = brightness < brightness_range[0]

    # Contrast (std dev of grayscale)
    contrast = stat.stddev[0] * 2  # Scale to ~0-100

    # Noise estimation (high-frequency content)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    noise_level = min(100, edge_stat.mean[0] * 2)

    # Basic artifact detection (blocky patterns, banding)
    artifact_score = _detect_artifacts(arr)

    # Overall score
    overall = (
        sharpness * 0.3
        + (100 - abs(brightness - 128) * 0.8) * 0.2
        + min(100, contrast) * 0.2
        + (100 - noise_level) * 0.15
        + (100 - artifact_score) * 0.15
    )

    # Issues list
    issues = []
    if is_blurry:
        issues.append(f"BLURRY (sharpness: {sharpness:.1f})")
    if is_overexposed:
        issues.append(f"OVEREXPOSED (brightness: {brightness:.0f})")
    if is_underexposed:
        issues.append(f"UNDEREXPOSED (brightness: {brightness:.0f})")
    if artifact_score > 30:
        issues.append(f"ARTIFACTS DETECTED (score: {artifact_score:.0f})")
    if noise_level > 60:
        issues.append(f"NOISY (level: {noise_level:.0f})")
    if width < 512 or height < 512:
        issues.append(f"LOW RESOLUTION ({width}x{height})")

    return QualityReport(
        filename=path.name,
        path=str(path.absolute()),
        width=width,
        height=height,
        file_size_kb=round(file_size_kb, 1),
        sharpness=round(sharpness, 1),
        brightness=round(brightness, 1),
        contrast=round(contrast, 1),
        noise_level=round(noise_level, 1),
        artifact_score=round(artifact_score, 1),
        overall_score=round(overall, 1),
        is_blurry=is_blurry,
        is_overexposed=is_overexposed,
        is_underexposed=is_underexposed,
        has_artifacts=artifact_score > 30,
        aspect_ratio=aspect_ratio,
        megapixels=round(megapixels, 2),
        format=img.format or path.suffix.upper().strip("."),
        mode=img.mode,
        issues=issues,
    )


def _detect_artifacts(arr: np.ndarray) -> float:
    """Detect compression artifacts and banding."""
    # Check for blocky patterns (JPEG artifacts)
    h, w, _ = arr.shape
    if h < 8 or w < 8:
        return 0.0

    # Block difference analysis
    block_size = 8
    diffs = []
    for y in range(0, h - block_size, block_size):
        for x in range(0, w - block_size, block_size):
            block = arr[y : y + block_size, x : x + block_size].astype(float)
            # Horizontal edge difference
            h_diff = abs(block[-1, :].mean() - block[0, :].mean())
            diffs.append(h_diff)

    if not diffs:
        return 0.0

    # Banding: many blocks with similar small differences
    avg_diff = sum(diffs) / len(diffs)
    banding = sum(1 for d in diffs if 2 < d < 15) / len(diffs) * 100

    return min(100, banding + avg_diff)


def analyze_batch(
    directory: str,
    extensions: tuple = (".png", ".jpg", ".jpeg", ".webp", ".bmp"),
) -> list[QualityReport]:
    """Analyze all images in a directory."""
    dir_path = Path(directory)
    if not dir_path.exists():
        raise FileNotFoundError(f"Directory not found: {directory}")

    reports = []
    files = sorted(dir_path.iterdir(), key=lambda p: natural_sort_key(p.name))
    for f in files:
        if f.suffix.lower() in extensions:
            try:
                report = analyze_image(str(f))
                reports.append(report)
            except Exception as e:
                print(f"  Warning: Could not analyze {f.name}: {e}")

    return reports


def natural_sort_key(s: str):
    """Sort strings with embedded numbers naturally."""
    return [
        int(text) if text.isdigit() else text.lower()
        for text in __import__("re").split(r"(\d+)", s)
    ]
