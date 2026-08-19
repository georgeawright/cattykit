from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime

from .logging import SQLiteLogger
from .models import load_model


@dataclass
class ExperimentResult:
    distributions: dict[str, Counter[str]]
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
    Counters of answers and the logging_db are returned in ExperimentResult.
    If verbose, problems and solutions will print to stdout."""
    if logging_db is None:
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        logging_db = f"{model_name}-experiments-{now}.sqlite"
    distributions: dict[str, Counter[str]] = {}
    logger = SQLiteLogger(logging_db)
    try:
        for problem in problems:
            if verbose:
                print(problem)
            answers: Counter[str] = Counter()
            for seed in range(iterations):
                model = load_model(
                    model_name,
                    config={"seed": seed},
                    logger=logger,
                )
                try:
                    answer = model.solve(problem)
                    answers[answer] += 1
                    if verbose:
                        print(f"{seed}: {answer}")
                finally:
                    model.close()
            distributions[problem] = answers
    finally:
        logger.close()
    return ExperimentResult(
        distributions=distributions,
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
