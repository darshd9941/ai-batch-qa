"""AI Batch QA — quality analysis for AI-generated images."""
__version__ = "1.0.0"

from .analyzer import analyze_image, analyze_batch, QualityReport, natural_sort_key
from .comparison import compare_two, compare_directory, build_parameter_grid
from .report import generate_report, generate_comparison_report
