"""Plot baseline answers, temperature, codelets, and snags for five targets."""

from __future__ import annotations

from copycat_replication.comparison_figures import save_comparison_figures
from copycat_replication.figure_helpers import (
    save_basic_problem_figures,
    save_problem_5_xyd_scatter,
)
from copycat_replication.paths import FIGURES, REPLICATION_DATASETS

RAW_RESULTS_PATH = REPLICATION_DATASETS / "reproduction_raw_results.csv"


def main() -> None:
    """Generate figures from saved baseline raw data; this stage never solves."""
    if not RAW_RESULTS_PATH.is_file():
        raise FileNotFoundError(f"Run 00 first; missing {RAW_RESULTS_PATH}")
    FIGURES.mkdir(parents=True, exist_ok=True)
    save_basic_problem_figures(RAW_RESULTS_PATH)
    save_problem_5_xyd_scatter(RAW_RESULTS_PATH)
    save_comparison_figures()


if __name__ == "__main__":
    main()
