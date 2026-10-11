"""Public experiment-running and statistical-analysis API."""

from .reproduction import reproduction_summary, run_reproduction
from .runner import ExperimentResult, run_experiment
from .statistics import (
    chi_square_survival_function,
    mean_absolute_error,
    summarize_runs,
    total_variation_distance,
    two_sided_p_value,
    z_statistic,
)

__all__ = [
    "ExperimentResult",
    "chi_square_survival_function",
    "mean_absolute_error",
    "run_experiment",
    "run_reproduction",
    "reproduction_summary",
    "summarize_runs",
    "total_variation_distance",
    "two_sided_p_value",
    "z_statistic",
]
