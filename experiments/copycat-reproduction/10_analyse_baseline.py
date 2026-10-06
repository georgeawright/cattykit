"""Generate baseline comparison CSVs and a paper-ready Markdown table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from copycat_reproduction.experiment_helpers import reproduction_from_raw_results
from copycat_reproduction.paths import DATASETS, GOLD_PATH, TABLES
from copycat_reproduction.table_helpers import (
    comparison_markdown,
    comparison_table,
    error_summary,
)

RAW_RESULTS_PATH = DATASETS / "reproduction_raw_results.csv"
RESULTS_PATH = DATASETS / "reproduction_copycat_results.json"
COMPARISON_CSV_PATH = DATASETS / "reproduction_comparison.csv"
ERROR_SUMMARY_CSV_PATH = DATASETS / "reproduction_comparison_error_summary.csv"
MARKDOWN_PATH = TABLES / "baseline-comparison-statistics.md"


def main(gold_path: Path = GOLD_PATH) -> None:
    """Analyse existing baseline raw data; this stage never runs Copycat."""
    if not RAW_RESULTS_PATH.is_file():
        raise FileNotFoundError(f"Run 00 first; missing {RAW_RESULTS_PATH}")
    if not gold_path.is_file():
        raise FileNotFoundError(f"Missing original result data: {gold_path}")
    TABLES.mkdir(parents=True, exist_ok=True)
    reproduction = reproduction_from_raw_results(pd.read_csv(RAW_RESULTS_PATH))
    RESULTS_PATH.write_text(json.dumps(reproduction, indent=2) + "\n", encoding="utf-8")
    original = json.loads(gold_path.read_text(encoding="utf-8"))
    comparison = comparison_table(reproduction, original)
    error = error_summary(comparison)
    comparison.to_csv(COMPARISON_CSV_PATH, index=False)
    error.to_csv(ERROR_SUMMARY_CSV_PATH, index=False)
    MARKDOWN_PATH.write_text(
        comparison_markdown(comparison, error),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold-path", type=Path, default=GOLD_PATH)
    main(parser.parse_args().gold_path)
