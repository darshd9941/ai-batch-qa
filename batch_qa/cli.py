"""CLI for batch QA analysis of AI-generated images."""
import sys
import click

# Force UTF-8 output on Windows
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from rich.console import Console
from rich.table import Table
from .analyzer import analyze_image, analyze_batch
from .comparison import compare_two, build_parameter_grid, find_best_in_grid
from .report import generate_report, generate_comparison_report

console = Console(force_terminal=True)


@click.group()
@click.version_option(package_name="ai-batch-qa")
def cli():
    """AI Batch QA - detect quality issues in AI-generated image batches."""
    pass


@cli.command()
@click.argument("path")
@click.option("--output", "-o", default="qa_report.html", help="Output HTML report path")
def analyze(path, output):
    """Analyze a single image or all images in a directory."""
    from pathlib import Path
    p = Path(path)

    if p.is_file():
        console.print(f"\nAnalyzing [cyan]{p.name}[/]...")
        report = analyze_image(str(p))
        _print_single_report(report)
        reports = [report]
    elif p.is_dir():
        console.print(f"\nScanning directory [cyan]{path}[/]...")
        console.print("  Analyzing images...")
        reports = analyze_batch(str(p))
        console.print(f"  Found {len(reports)} images.")
        _print_batch_summary(reports)
    else:
        console.print(f"[red]Error:[/] {path} not found")
        return

    report_path = generate_report(reports, output_path=output)
    console.print(f"\n[green]OK[/] Report saved to [cyan]{report_path}[/]")


@cli.command()
@click.argument("image_a")
@click.argument("image_b")
def compare(image_a, image_b):
    """Compare two images side by side."""
    console.print(f"\nComparing [cyan]{image_a}[/] vs [cyan]{image_b}[/]...")
    result = compare_two(image_a, image_b)

    table = Table(title="A/B Comparison", show_lines=True)
    table.add_column("Metric", style="bold")
    table.add_column("Image A", justify="right")
    table.add_column("Image B", justify="right")
    table.add_column("Winner", justify="center")

    for metric, data in result.metric_comparison.items():
        winner = "<<" if data["winner"] == "a" else ">>" if data["winner"] == "b" else "=="
        style_a = "green" if data["winner"] == "a" else ""
        style_b = "green" if data["winner"] == "b" else ""
        table.add_row(
            metric,
            f"[{style_a}]{data['a']:.1f}[/]",
            f"[{style_b}]{data['b']:.1f}[/]",
            winner,
        )

    console.print(table)

    winner_name = "Image A" if result.winner == "a" else "Image B" if result.winner == "b" else "Tie"
    console.print(f"\n[bold green]Winner: {winner_name}[/] (score diff: {result.score_diff})")


@cli.command()
@click.argument("directory")
@click.option("--pattern", "-p", default=r"(.+)_s(\d+)_c([\d.]+)", help="Filename pattern for parameter extraction")
def grid(directory, pattern):
    """Build a parameter grid from filenames."""
    console.print(f"\nBuilding parameter grid from [cyan]{directory}[/]...")
    parameter_grid = build_parameter_grid(directory, pattern)

    if not parameter_grid:
        console.print("[yellow]No files matched the pattern.[/]")
        console.print("Expected: {name}_s{seed}_c{cfg}.png")
        return

    for prompt, params_dict in parameter_grid.items():
        console.print(f"\n[bold]{prompt}[/]")
        for params, info in params_dict.items():
            console.print(f"  - {info['file']} (seed={info['seed']}, cfg={info['cfg']})")

    best = find_best_in_grid(directory, pattern)
    if best:
        console.print(f"\n[bold green]Best in grid: {best}[/]")


@cli.command()
@click.argument("image_path")
def check(image_path):
    """Quick quality check on a single image."""
    report = analyze_image(image_path)
    _print_single_report(report)

    if report.issues:
        console.print(f"\n[red]WARNING: {len(report.issues)} issue(s) found[/]")
    else:
        console.print(f"\n[green]OK - Image looks good![/]")


@cli.command()
@click.argument("image_a")
@click.argument("image_b")
@click.option("--output", "-o", default="ab_comparison.html", help="Output HTML report")
def ab(image_a, image_b, output):
    """Generate A/B comparison HTML report."""
    result = compare_two(image_a, image_b)
    path = generate_comparison_report([result], output_path=output)
    console.print(f"[green]OK[/] Comparison report saved to [cyan]{path}[/]")


def _print_single_report(r):
    """Print a single image report to console."""
    status = "OK" if not r.issues else "FLAGGED"
    table = Table(show_header=False, border_style="dim")
    table.add_column("Key", style="bold")
    table.add_column("Value")
    table.add_row("File", r.filename)
    table.add_row("Dimensions", f"{r.width}x{r.height} ({r.megapixels} MP)")
    table.add_row("File Size", f"{r.file_size_kb} KB")
    table.add_row("Format", f"{r.format} / {r.mode}")
    table.add_row("Aspect Ratio", r.aspect_ratio)
    table.add_row("Overall Score", f"[bold]{r.overall_score}[/] / 100")
    table.add_row("Sharpness", f"{r.sharpness} / 100")
    table.add_row("Brightness", f"{r.brightness:.0f} / 255")
    table.add_row("Contrast", f"{r.contrast:.0f} / 100")
    table.add_row("Noise Level", f"{r.noise_level:.0f} / 100")
    table.add_row("Status", status)
    if r.issues:
        table.add_row("Issues", "\n".join(f"[red]- {i}[/]" for i in r.issues))
    console.print(table)


def _print_batch_summary(reports):
    """Print batch analysis summary."""
    if not reports:
        console.print("[yellow]No images found.[/]")
        return

    total = len(reports)
    flagged = sum(1 for r in reports if r.issues)
    avg_score = sum(r.overall_score for r in reports) / total
    best = max(reports, key=lambda r: r.overall_score)
    worst = min(reports, key=lambda r: r.overall_score)

    table = Table(title=f"Batch Summary ({total} images)")
    table.add_column("Metric", style="bold")
    table.add_column("Value")
    table.add_row("Total Images", str(total))
    table.add_row("Passed", f"[green]{total - flagged}[/]")
    table.add_row("Flagged", f"[red]{flagged}[/]" if flagged else "0")
    table.add_row("Average Score", f"{avg_score:.1f}")
    table.add_row("Best", f"[green]{best.filename}[/] ({best.overall_score})")
    table.add_row("Worst", f"[red]{worst.filename}[/] ({worst.overall_score})")
    console.print(table)

    # Top issues
    issue_counts = {}
    for r in reports:
        for issue in r.issues:
            key = issue.split("(")[0].strip()
            issue_counts[key] = issue_counts.get(key, 0) + 1
    if issue_counts:
        console.print("\n[bold]Top Issues:[/]")
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            console.print(f"  [red]-[/] {issue}: {count} images")


if __name__ == "__main__":
    cli()
