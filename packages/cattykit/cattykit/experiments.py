from pathlib import Path
from datetime import datetime

from .logging import SQLiteLogger
from .models import load_model


def run_experiment(
    model_name: str,
    problems: list[str],
    iterations: int,
    logging_db: str | Path | None = None,
    verbose: bool = True,
) -> str:
    """Runs the model on each problem for the required number of iterations.
    The iteration count is used as the random seed given to the model.
    The same random seeds are used for each problem.
    If logging_db is not set, the model name and run date/time are used.
    The logging_db is returned as a string.
    If verbose, problems and solutions will print to stdout."""
    if logging_db is None:
        now = datetime.now().strftime("%Y%m%d-%H%M%S")
        logging_db = f"{model_name}-experiments-{now}.sqlite"
    logger = SQLiteLogger(logging_db)
    try:
        for problem in problems:
            if verbose:
                print(problem)
            for seed in range(iterations):
                model = load_model(
                    model_name,
                    config={"seed": seed},
                    logger=logger,
                )
                try:
                    result = model.solve(problem)
                    if verbose:
                        print(result)
                finally:
                    model.close()
    finally:
        logger.close()
    return str(logging_db)
