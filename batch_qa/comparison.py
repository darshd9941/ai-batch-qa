"""A/B comparison and parameter grid analysis."""
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from .analyzer import QualityReport, analyze_image, natural_sort_key


@dataclass
class ComparisonResult:
    image_a: QualityReport
    image_b: QualityReport
    winner: str  # "a", "b", "tie"
    score_diff: float
    metric_comparison: dict  # {metric: {"a": val, "b": val, "winner": "a"/"b"}}


def compare_two(image_a: str, image_b: str) -> ComparisonResult:
    """Compare two images side by side."""
    report_a = analyze_image(image_a)
    report_b = analyze_image(image_b)

    metrics = {}
    a_wins = 0
    b_wins = 0

    for metric in ["sharpness", "brightness", "contrast", "overall_score"]:
        val_a = getattr(report_a, metric)
        val_b = getattr(report_b, metric)

        # For brightness, closer to 128 is better
        if metric == "brightness":
            diff_a = abs(val_a - 128)
            diff_b = abs(val_b - 128)
            winner = "a" if diff_a < diff_b else "b" if diff_b < diff_a else "tie"
        else:
            winner = "a" if val_a > val_b else "b" if val_b > val_a else "tie"

        if winner == "a":
            a_wins += 1
        elif winner == "b":
            b_wins += 1

        metrics[metric] = {"a": val_a, "b": val_b, "winner": winner}

    # For noise/artifacts, lower is better
    for metric in ["noise_level", "artifact_score"]:
        val_a = getattr(report_a, metric)
        val_b = getattr(report_b, metric)
        winner = "a" if val_a < val_b else "b" if val_b < val_a else "tie"
        if winner == "a":
            a_wins += 1
        elif winner == "b":
            b_wins += 1
        metrics[metric] = {"a": val_a, "b": val_b, "winner": winner}

    overall_winner = "a" if a_wins > b_wins else "b" if b_wins > a_wins else "tie"
    score_diff = abs(report_a.overall_score - report_b.overall_score)

    return ComparisonResult(
        image_a=report_a,
        image_b=report_b,
        winner=overall_winner,
        score_diff=round(score_diff, 1),
        metric_comparison=metrics,
    )


def compare_directory(
    directory: str,
    extensions: tuple = (".png", ".jpg", ".jpeg", ".webp"),
) -> list[ComparisonResult]:
    """Compare all images in a directory pairwise."""
    dir_path = Path(directory)
    files = sorted(
        [f for f in dir_path.iterdir() if f.suffix.lower() in extensions],
        key=lambda p: natural_sort_key(p.name),
    )

    results = []
    for i in range(len(files)):
        for j in range(i + 1, min(i + 2, len(files))):
            try:
                result = compare_two(str(files[i]), str(files[j]))
                results.append(result)
            except Exception as e:
                print(f"  Warning: Could not compare {files[i].name} vs {files[j].name}: {e}")

    return results


def build_parameter_grid(
    directory: str,
    pattern: str = r"(.+)_s(\d+)_c([\d.]+)",
    extensions: tuple = (".png", ".jpg", ".jpeg", ".webp"),
) -> dict:
    """
    Parse filenames to extract parameters and build a grid.
    Expected pattern: {name}_s{seed}_c{cfg}.{ext}
    """
    import re
    dir_path = Path(directory)
    grid = {}

    files = sorted(
        [f for f in dir_path.iterdir() if f.suffix.lower() in extensions],
        key=lambda p: natural_sort_key(p.name),
    )

    for f in files:
        match = re.match(pattern, f.stem)
        if match:
            groups = match.groups()
            name = groups[0] if len(groups) > 0 else "default"
            seed = groups[1] if len(groups) > 1 else "unknown"
            cfg = groups[2] if len(groups) > 2 else "unknown"

            key = f"prompt={name}"
            if key not in grid:
                grid[key] = {}
            grid[key][f"seed={seed}_cfg={cfg}"] = {
                "file": f.name,
                "path": str(f),
                "seed": seed,
                "cfg": cfg,
            }

    return grid


def find_best_in_grid(
    directory: str,
    pattern: str = r"(.+)_s(\d+)_c([\d.]+]",
) -> Optional[str]:
    """Find the highest-quality image in a parameter grid."""
    grid = build_parameter_grid(directory, pattern)
    best_file = None
    best_score = -1

    for prompt_group in grid.values():
        for params, info in prompt_group.items():
            try:
                report = analyze_image(info["path"])
                if report.overall_score > best_score:
                    best_score = report.overall_score
                    best_file = info["file"]
            except Exception:
                continue

    return best_file
