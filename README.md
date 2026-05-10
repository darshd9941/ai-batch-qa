# ai-batch-qa

# ðŸ“Š AI Batch QA

> Auto-detect quality issues in batch AI image generation â€” blur, artifacts, overexposure, noise. CLIP-based scoring, A/B comparison, parameter grids.

![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![Pillow](https://img.shields.io/badge/Pillow-10+-blue)
![License](https://img.shields.io/badge/License-MIT-green)

## The Problem

When generating batches of AI images (8, 20, 100+), reviewing each one manually is tedious. You miss artifacts, keep blurry shots, and can't systematically compare parameter variations. Batch captioning breaks due to file naming mismatches. There's no way to know which seed/cfg/prompt combination produced the best result without eyeballing every file.

## The Solution

```bash
# Analyze an entire folder
ai-batch-qa analyze ./generated_images/

# Quick check a single image
ai-batch-qa check image.png

# Compare two images
ai-batch-qa compare good.png bad.png

# Build parameter grid from filenames
ai-batch-qa grid ./batch_output/ --pattern "(.+)_s(\d+)_c([\d.]+)"
```

## Quick Start

```bash
# Clone
git clone https://github.com/darshd9941/ai-batch-qa.git
cd ai-batch-qa

# Install
pip install -e .

# Or from requirements
pip install -r requirements.txt
python -m batch_qa.cli analyze ./my_images/
```

## Features

### Quality Analysis
- **Sharpness** â€” Laplacian variance detection for blur
- **Brightness** â€” Over/underexposure detection
- **Contrast** â€” Dynamic range analysis
- **Noise** â€” High-frequency content estimation
- **Artifact detection** â€” JPEG compression artifacts, banding patterns
- **Resolution check** â€” Flags images under 512px

### A/B Comparison
- Side-by-side metric comparison
- Per-metric winner determination
- Overall score differential
- HTML report generation

### Parameter Grid
- Parse filenames to extract seed, CFG, prompt parameters
- Build searchable grid of variations
- Auto-find highest-quality image in grid

### Batch Reporting
- Dark-themed HTML reports
- Image thumbnails (if accessible)
- Sortable table with all metrics
- Pass/fail status per image
- Top issues summary

## CLI Commands

| Command | Description |
|---------|-------------|
| `analyze` | Scan a directory, analyze all images, generate HTML report |
| `check` | Quick quality check on a single image |
| `compare` | Compare two images side by side |
| `grid` | Build parameter grid from filenames |
| `ab` | Generate A/B comparison HTML report |

## Filename Patterns for Grid

The grid command expects filenames like:
```
my_prompt_s42_c7.5.png
my_prompt_s123_c8.0.png
```

Pattern: `{name}_s{seed}_c{cfg}.{ext}`

## Quality Scoring

Each image gets an overall score (0-100) based on:
- Sharpness (30%)
- Brightness accuracy (20%)
- Contrast (20%)
- Noise level (15%)
- Artifact score (15%)

## Python API

```python
from batch_qa import analyze_image, analyze_batch, compare_two

# Single image
report = analyze_image("photo.png")
print(f"Score: {report.overall_score}")
print(f"Issues: {report.issues}")

# Batch
reports = analyze_batch("./generated/")
for r in sorted(reports, key=lambda x: x.overall_score, reverse=True):
    print(f"{r.filename}: {r.overall_score}")

# Compare
result = compare_two("a.png", "b.png")
print(f"Winner: {result.winner}")
```

## Contributing

Contributions welcome! Especially:
- CLIP-based semantic quality scoring
- More artifact detection patterns
- Integration with ComfyUI as a custom node
- Support for video frame analysis

## License

MIT License â€” see [LICENSE](LICENSE) for details.


## Installation

### Prerequisites

- Python 3.8 or higher
- pip (Python package manager)

### Clone the Repository

```bash
git clone https://github.com/darshd9941/ai-batch-qa.git
cd ai-batch-qa
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

### Environment Setup

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Edit .env and add your API keys:
   ```bash
   # Required for Claude vision features
   ANTHROPIC_API_KEY=your-api-key-here
   ```

## Usage

### Web App (if applicable)

```bash
streamlit run app.py
```

### CLI Usage

```bash
python main.py --help
```

### Python API

```python
from module import MainClass

# Initialize the tool
tool = MainClass()

# Use the tool
result = tool.process("input")
print(result)
```

## Configuration

- .env - Environment variables (API keys, settings)
- config.yaml - Configuration file (if applicable)

## Examples

See the examples/ directory for detailed usage examples.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

See LICENSE file for details.
