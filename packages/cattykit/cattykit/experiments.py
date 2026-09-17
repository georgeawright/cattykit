import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from shutil import get_terminal_size

import pandas as pd

from .logging import CattycamLogger, NullLogger
from .models import load_model


@dataclass
class ExperimentResult:
    distributions: dict[str, Counter[str]]
    summaries: dict[str, pd.DataFrame]
    logging_db: str


def run_experiment(
    model_name: str,
    problems: list[str],
    iterations: int,
    logging_db: str | Path | None = None,
    verbose: bool = True,
) -> ExperimentResult:
    """Runs the model on each problem for the required number of iterations.
    The iteration count is used as the random seed given to the model.
    The same random seeds are used for each problem.
    If logging_db is not set, the model name and run date/time are used.
    Counters of answers, per-problem summary DataFrames, and the logging_db are
    returned in ExperimentResult. Each summary includes a totals row.
    If verbose, problems and solutions will print to stdout."""
    interactive = verbose and sys.stdout.isatty()
    distributions: dict[str, Counter[str]] = {}
    summaries: dict[str, pd.DataFrame] = {}
    logger = (
        CattycamLogger(logging_db, model_name)
        if logging_db is not None
        else NullLogger(model_name)
    )
    try:
        for problem_number, problem in enumerate(problems):
            if interactive:
                if problem_number:
                    print(_terminal_rule("="))
                print(problem)
                print(_terminal_rule("-"))
                display = RunningAnswerDisplay()
            answers: Counter[str] = Counter()
            runs: list[dict[str, str | float | int | None]] = []
            for seed in range(iterations):
                model = load_model(
                    model_name,
                    config={"seed": seed},
                    logger=logger,
                )
                try:
                    answer = model.solve(problem)
                    answers[answer] += 1
                    runs.append(
                        {
                            "solution": answer,
                            "codelets_run": model.coderack.number_of_codelets_run,
                            "temperature": model.temperature,
                        }
                    )
                    if interactive:
                        display.update(runs)
                finally:
                    model.close()
            distributions[problem] = answers
            summaries[problem] = summarize_runs(runs)
    finally:
        logger.close()
    return ExperimentResult(
        distributions=distributions,
        summaries=summaries,
        logging_db=str(logging_db),
    )


def total_variation_distance(
    observed: dict[str, int], expected: dict[str, int]
) -> float:
    observed_total = sum(observed.values())
    expected_total = sum(expected.values())
    answers = observed.keys() | expected.keys()
    return 0.5 * sum(
        abs(
            observed.get(answer, 0) / observed_total
            - expected.get(answer, 0) / expected_total
        )
        for answer in answers
    )


def _terminal_rule(character: str) -> str:
    """Return a full-width terminal separator."""
    return character * get_terminal_size(fallback=(80, 24)).columns


class RunningAnswerDisplay:
    def __init__(self):
        self.lines_printed = 0

    def update(self, runs: list[dict[str, str | float | int | None]]) -> None:
        summary = summarize_runs(runs)

        if self.lines_printed:
            # Clear every physical terminal line from the prior table before
            # returning to its top-left corner. This prevents remnants when a
            # table row wraps at a narrow terminal width.
            print(f"\033[{self.lines_printed}A", end="")
            for _ in range(self.lines_printed):
                print("\033[2K")
            print(f"\033[{self.lines_printed}A", end="")

        table = summary.rename(
            columns={
                "solution": "Solution",
                "frequency": "Runs",
                "mean_codelets_run": "Mean codelets",
                "codelets_standard_error": "Codelets SE",
                "mean_temperature": "Mean temp",
                "temperature_standard_error": "Temp SE",
            }
        ).to_string(
            index=False,
            formatters={
                "Mean codelets": "{:.0f}".format,
                "Codelets SE": "{:.1f}".format,
                "Mean temp": "{:.2f}".format,
                "Temp SE": "{:.4f}".format,
            },
        )
        lines = table.splitlines()
        for line in lines:
            print(f"\033[2K{line}")

        terminal_width = get_terminal_size(fallback=(80, 24)).columns
        self.lines_printed = sum(
            max(1, (len(line) + terminal_width - 1) // terminal_width) for line in lines
        )


def summarize_runs(runs: list[dict[str, str | float | int | None]]) -> pd.DataFrame:
    """Summarize the individual model runs, including an overall totals row."""
    data = pd.DataFrame(runs)
    columns = [
        "solution",
        "frequency",
        "mean_codelets_run",
        "codelets_standard_error",
        "mean_temperature",
        "temperature_standard_error",
    ]
    if data.empty:
        return pd.DataFrame(columns=columns)

    grouped = data.groupby("solution", sort=False)
    summary = grouped.agg(
        frequency=("solution", "size"),
        mean_codelets_run=("codelets_run", "mean"),
        codelets_standard_error=("codelets_run", "sem"),
        mean_temperature=("temperature", "mean"),
        temperature_standard_error=("temperature", "sem"),
    ).reset_index()
    summary = summary.sort_values("frequency", ascending=False, kind="stable")
    summary[["codelets_standard_error", "temperature_standard_error"]] = summary[
        ["codelets_standard_error", "temperature_standard_error"]
    ].fillna(0.0)

    totals = pd.DataFrame(
        [
            {
                "solution": "Total",
                "frequency": len(data),
                "mean_codelets_run": data["codelets_run"].mean(),
                "codelets_standard_error": data["codelets_run"].sem() or 0.0,
                "mean_temperature": data["temperature"].mean(),
                "temperature_standard_error": data["temperature"].sem() or 0.0,
            }
        ]
    )
    totals[["codelets_standard_error", "temperature_standard_error"]] = totals[
        ["codelets_standard_error", "temperature_standard_error"]
    ].fillna(0.0)
    return pd.concat([summary, totals], ignore_index=True)
