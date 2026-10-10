"""Run the 29 baseline Copycat problems and save raw runs plus summary JSON."""

from __future__ import annotations

import argparse
import json

from cattykit.experiments import run_experiment, summarize_runs
from copycat_reproduction.experiment_helpers import result_case
from copycat_reproduction.paths import (
    REPRODUCTION_DATASETS,
    TEMPLATE_PATH,
)

RAW_RESULTS_PATH = REPRODUCTION_DATASETS / "reproduction_raw_results.csv"
RESULTS_PATH = REPRODUCTION_DATASETS / "reproduction_copycat_results.json"


def main(iterations: int = 1000) -> None:
    """Run every source problem once per seed; do not perform analysis or plotting."""
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    REPRODUCTION_DATASETS.mkdir(parents=True, exist_ok=True)
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    cases_by_problem = {case["problem"]: case for case in template["results"]}
    result = run_experiment(
        "copycat",
        list(cases_by_problem),
        iterations,
        verbose=False,
        record_attributes=["snag_count"],
        summary_function=summarize_runs,
        progress_callback=lambda number, total, problem: print(
            f"[{number}/{total}] {problem}"
        ),
    )
    result.save_raw_runs_csv(RAW_RESULTS_PATH)
    reproduced_cases = []
    for problem, case in cases_by_problem.items():
        reproduced_cases.append(
            result_case(
                problem,
                result.summary.loc[result.summary["problem"] == problem],
                case["source"],
                case["id"],
            )
        )
    RESULTS_PATH.write_text(
        json.dumps(
            {
                "schema_version": template["schema_version"],
                "source_work": template["source_work"],
                "basic_problems": template["basic_problems"],
                "results": reproduced_cases,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1000)
    main(parser.parse_args().iterations)
