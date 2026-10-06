"""Plot baseline answer frequencies, temperatures, and codelets for five targets."""

from __future__ import annotations

from copycat_reproduction.figure_helpers import save_basic_problem_figures
from copycat_reproduction.paths import DATASETS, FIGURES

RAW_RESULTS_PATH = DATASETS / "reproduction_raw_results.csv"


def main() -> None:
    """Generate figures from saved baseline raw data; this stage never solves."""
    if not RAW_RESULTS_PATH.is_file():
        raise FileNotFoundError(f"Run 00 first; missing {RAW_RESULTS_PATH}")
    FIGURES.mkdir(parents=True, exist_ok=True)
    save_basic_problem_figures(RAW_RESULTS_PATH)


if __name__ == "__main__":
    main()
