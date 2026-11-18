"""Generate baseline comparison CSVs and Markdown table."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from copycat_reproduction.paths import GOLD_PATH, REPRODUCTION_DATASETS, TABLES
from copycat_reproduction.table_helpers import (
    comparison_markdown,
    comparison_table,
)

RESULTS_PATH = REPRODUCTION_DATASETS / "reproduction_copycat_results.json"
COMPARISON_CSV_PATH = REPRODUCTION_DATASETS / "reproduction_comparison.csv"
MARKDOWN_PATH = TABLES / "baseline-comparison-statistics.md"


def main(gold_path: Path = GOLD_PATH) -> None:
    """Analyse the baseline summary produced by stage 00."""
    if not RESULTS_PATH.is_file():
        raise FileNotFoundError(f"Run 00 first; missing {RESULTS_PATH}")
    if not gold_path.is_file():
        raise FileNotFoundError(f"Missing original result data: {gold_path}")
    TABLES.mkdir(parents=True, exist_ok=True)
    observed = json.loads(RESULTS_PATH.read_text(encoding="utf-8"))
    original = json.loads(gold_path.read_text(encoding="utf-8"))
    comparison = comparison_table(observed, original)
    comparison.to_csv(COMPARISON_CSV_PATH, index=False)
    MARKDOWN_PATH.write_text(
        comparison_markdown(comparison),
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--gold-path", type=Path, default=GOLD_PATH)
    main(parser.parse_args().gold_path)
