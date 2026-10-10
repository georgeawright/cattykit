"""Compare baseline and two-decimal-quantised Copycat results from raw CSVs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from copycat_reproduction.experiment_helpers import reproduction_from_raw_results
from copycat_reproduction.paths import (
    GOLD_PATH,
    QUANTIZATION_DATASETS,
    REPRODUCTION_DATASETS,
    TABLES,
)
from copycat_reproduction.table_helpers import (
    comparison_table,
    method_comparison_markdown,
    method_summary_row,
)

SUMMARY_CSV_PATH = QUANTIZATION_DATASETS / "quantisation_comparison.csv"
SUMMARY_MARKDOWN_PATH = TABLES / "quantisation-comparison.md"


def main(gold_path: Path = GOLD_PATH) -> None:
    """Generate comparison tables exclusively from completed experiment runs."""
    if not gold_path.is_file():
        raise FileNotFoundError(f"Missing original result data: {gold_path}")
    TABLES.mkdir(parents=True, exist_ok=True)
    original = json.loads(gold_path.read_text(encoding="utf-8"))
    baseline_runs = pd.read_csv(
        REPRODUCTION_DATASETS / "reproduction_raw_results.csv"
    )
    snaggable_problems = set(
        baseline_runs.loc[baseline_runs["snag_count"] > 0, "problem"]
    )
    raw_paths = (
        (
            "full_precision",
            REPRODUCTION_DATASETS / "reproduction_raw_results.csv",
        ),
        (
            "two_decimal_quantisation",
            QUANTIZATION_DATASETS / "quantized_raw_results.csv",
        ),
    )
    summary_rows = []
    for name, raw_path in raw_paths:
        if not raw_path.is_file():
            raise FileNotFoundError(f"Required raw results are missing: {raw_path}")
        raw_runs = pd.read_csv(raw_path)
        reproduction = reproduction_from_raw_results(raw_runs)
        comparison = comparison_table(reproduction, original)
        comparison.to_csv(
            QUANTIZATION_DATASETS / f"quantisation_{name}_comparison.csv",
            index=False,
        )
        summary_rows.append(
            method_summary_row(name, comparison, raw_runs, snaggable_problems)
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SUMMARY_CSV_PATH, index=False)
    SUMMARY_MARKDOWN_PATH.write_text(
        method_comparison_markdown(
            "Numeric quantisation comparison",
            summary,
            {
                "full_precision": "Full precision",
                "two_decimal_quantisation": "Two-decimal quantisation",
            },
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold-path", type=Path, default=GOLD_PATH)
    main(parser.parse_args().gold_path)
