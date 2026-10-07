"""Plot basic-problem results from Copycat's two-decimal quantisation run."""

from __future__ import annotations

from copycat_reproduction.figure_helpers import save_basic_problem_figures
from copycat_reproduction.paths import DATASETS, FIGURES

RAW_RESULTS_PATH = DATASETS / "quantized_raw_results.csv"


def main() -> None:
    """Generate quantised figures from saved runs; this stage never solves."""
    if not RAW_RESULTS_PATH.is_file():
        raise FileNotFoundError(f"Run 02 first; missing {RAW_RESULTS_PATH}")
    FIGURES.mkdir(parents=True, exist_ok=True)
    save_basic_problem_figures(RAW_RESULTS_PATH, filename_prefix="quantized-")


if __name__ == "__main__":
    main()
