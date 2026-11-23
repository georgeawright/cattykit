"""Compare baseline and alternative coderack-removal results."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd
from copycat_replication.paths import (
    CODERACK_REMOVAL_DATASETS,
    GOLD_PATH,
    REPLICATION_DATASETS,
    TABLES,
)
from copycat_replication.table_helpers import (
    comparison_table,
    method_comparison_markdown,
    method_summary_row,
)

SUMMARY_CSV_PATH = CODERACK_REMOVAL_DATASETS / "coderack_removal_method_comparison.csv"
SUMMARY_MARKDOWN_PATH = TABLES / "coderack-removal-method-comparison.md"


def main(gold_path: Path = GOLD_PATH) -> None:
    """Generate three-way tables exclusively from saved baseline/alternative runs."""
    if not gold_path.is_file():
        raise FileNotFoundError(f"Missing original result data: {gold_path}")
    TABLES.mkdir(parents=True, exist_ok=True)
    original = json.loads(gold_path.read_text(encoding="utf-8"))
    baseline_runs = pd.read_csv(
        REPLICATION_DATASETS / "reproduction_raw_results.csv"
    )
    snaggable_problems = set(
        baseline_runs.loc[baseline_runs["snag_count"] > 0, "problem"]
    )
    result_paths = (
        (
            "fixed_weighted_removal",
            REPLICATION_DATASETS / "reproduction_raw_results.csv",
            REPLICATION_DATASETS / "reproduction_copycat_results.json",
        ),
        (
            "faithful_original_removal",
            CODERACK_REMOVAL_DATASETS
            / "coderack_removal_faithful_original_removal_raw_results.csv",
            CODERACK_REMOVAL_DATASETS
            / "coderack_removal_faithful_original_removal_results.json",
        ),
    )
    summary_rows = []
    for name, raw_path, summary_path in result_paths:
        if not raw_path.is_file():
            raise FileNotFoundError(f"Required raw results are missing: {raw_path}")
        raw_runs = pd.read_csv(raw_path)
        if not summary_path.is_file():
            raise FileNotFoundError(f"Required summary results are missing: {summary_path}")
        reproduction = json.loads(summary_path.read_text(encoding="utf-8"))
        comparison = comparison_table(reproduction, original)
        comparison.to_csv(
            CODERACK_REMOVAL_DATASETS / f"coderack_removal_{name}_comparison.csv",
            index=False,
        )
        summary_rows.append(
            method_summary_row(name, comparison, raw_runs, snaggable_problems)
        )
    summary = pd.DataFrame(summary_rows)
    summary.to_csv(SUMMARY_CSV_PATH, index=False)
    SUMMARY_MARKDOWN_PATH.write_text(
        method_comparison_markdown(
            summary,
            {
                "fixed_weighted_removal": "Fixed weighted removal",
                "faithful_original_removal": "Faithful original removal",
            },
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold-path", type=Path, default=GOLD_PATH)
    main(parser.parse_args().gold_path)
