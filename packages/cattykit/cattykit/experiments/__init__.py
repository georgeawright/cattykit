"""Public experiment-running and statistical-analysis API."""

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
    "summarize_runs",
    "total_variation_distance",
    "two_sided_p_value",
    "z_statistic",
]
