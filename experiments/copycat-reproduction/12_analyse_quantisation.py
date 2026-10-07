"""Compare baseline and two-decimal-quantised Copycat results from raw CSVs."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from copycat_reproduction.experiment_helpers import reproduction_from_raw_results
from copycat_reproduction.paths import DATASETS, GOLD_PATH, TABLES
from copycat_reproduction.table_helpers import (
    comparison_table,
    method_comparison_markdown,
    method_summary_row,
)

SUMMARY_CSV_PATH = DATASETS / "quantisation_comparison.csv"
SUMMARY_MARKDOWN_PATH = TABLES / "quantisation-comparison.md"


def main(gold_path: Path = GOLD_PATH) -> None:
    """Generate comparison tables exclusively from completed experiment runs."""
    if not gold_path.is_file():
        raise FileNotFoundError(f"Missing original result data: {gold_path}")
    TABLES.mkdir(parents=True, exist_ok=True)
    original = json.loads(gold_path.read_text(encoding="utf-8"))
    raw_paths = (
        ("full_precision", DATASETS / "reproduction_raw_results.csv"),
        ("two_decimal_quantisation", DATASETS / "quantized_raw_results.csv"),
    )
    summary_rows = []
    for name, raw_path in raw_paths:
        if not raw_path.is_file():
            raise FileNotFoundError(f"Required raw results are missing: {raw_path}")
        reproduction = reproduction_from_raw_results(pd.read_csv(raw_path))
        comparison = comparison_table(reproduction, original)
        comparison.to_csv(DATASETS / f"quantisation_{name}_comparison.csv", index=False)
        summary_rows.append(method_summary_row(name, comparison))
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
