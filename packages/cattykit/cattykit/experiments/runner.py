"""Execution of repeatable model experiments."""

from __future__ import annotations

import sys
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from shutil import get_terminal_size
from typing import Any

import pandas as pd

from ..logging import CattycamLogger, NullLogger
from ..models import load_model
from .statistics import SUMMARY_COLUMNS, summarize_runs

RAW_RESULT_COLUMNS = ["problem", "random_seed", "answer", "codelets_run", "temperature"]
SummaryFunction = Callable[[list[dict[str, Any]], str], pd.DataFrame]
ProgressCallback = Callable[[int, int, str], None]


class RunningAnswerDisplay:
    """Render an updating terminal view of a running experiment summary."""

    def __init__(self) -> None:
        self.lines_printed = 0

    def update(self, results: pd.DataFrame) -> None:
        table = results.drop(columns="problem").to_string(index=False)
        if self.lines_printed:
            print(f"\033[{self.lines_printed}A", end="")
            for _ in range(self.lines_printed):
                print("\033[2K")
            print(f"\033[{self.lines_printed}A", end="")
        lines = table.splitlines()
        for line in lines:
            print(f"\033[2K{line}")
        width = get_terminal_size(fallback=(80, 24)).columns
        self.lines_printed = sum(max(1, (len(line) + width - 1) // width) for line in lines)


@dataclass
class ExperimentResult:
    """Aggregate statistics and the individual runs that produced them."""

    summary: pd.DataFrame
    raw_runs: pd.DataFrame

    def save_summary_csv(self, path: str | Path) -> None:
        self.summary.to_csv(path, index=False)

    def save_raw_runs_csv(self, path: str | Path) -> None:
        self.raw_runs.to_csv(path, index=False)


def run_experiment(
    model_name: str,
    problems: list[str],
    iterations: int,
    logging_db: str | Path | None = None,
    verbose: bool = True,
    record_attributes: list[str] | None = None,
    summary_function: SummaryFunction = summarize_runs,
    progress_callback: ProgressCallback | None = None,
) -> ExperimentResult:
    """Run every problem once per seed with configurable recordings and summaries."""
    record_attributes = record_attributes or []
    reserved = set(RAW_RESULT_COLUMNS)
    duplicates = reserved.intersection(record_attributes)
    if duplicates:
        raise ValueError(
            f"record_attributes duplicate standard fields: {sorted(duplicates)}"
        )
    interactive = verbose and sys.stdout.isatty()
    summaries, raw_runs = [], []
    logger = (
        CattycamLogger(logging_db, model_name) if logging_db else NullLogger(model_name)
    )
    try:
        for problem_number, problem in enumerate(problems, start=1):
            display = RunningAnswerDisplay() if interactive else None
            runs = []
            for seed in range(iterations):
                model = load_model(model_name, config={"seed": seed}, logger=logger)
                try:
                    answer = model.solve(problem)
                    run: dict[str, Any] = {
                        "solution": answer,
                        "codelets_run": model.coderack.number_of_codelets_run,
                        "temperature": model.temperature,
                    }
                    run.update(
                        {
                            attribute: getattr(model, attribute)
                            for attribute in record_attributes
                        }
                    )
                    runs.append(run)
                    raw_runs.append(
                        {
                            "problem": problem,
                            "random_seed": seed,
                            "answer": answer,
                            **{key: run[key] for key in run if key != "solution"},
                        }
                    )
                    if display:
                        display.update(summary_function(runs, problem))
                finally:
                    model.close()
            summaries.append(summary_function(runs, problem))
            if progress_callback is not None:
                progress_callback(problem_number, len(problems), problem)
    finally:
        logger.close()
    return ExperimentResult(
        pd.concat(summaries, ignore_index=True)
        if summaries
        else pd.DataFrame(columns=SUMMARY_COLUMNS),
        pd.DataFrame(raw_runs, columns=[*RAW_RESULT_COLUMNS, *record_attributes]),
    )
