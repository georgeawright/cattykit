import json
import os
from pathlib import Path

import pandas as pd
import pytest

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_DATASET_PATH = (
    REPOSITORY_ROOT / "datasets/copycat/original_copycat_results.json"
)

def pytest_configure(config):
    if config.getoption("--basic") and config.getoption("--full"):
        raise pytest.UsageError("--basic and --full cannot be used together")


@pytest.fixture
def gold_behaviour(request) -> dict[str, pd.DataFrame]:
    """Return the published behaviour for every problem in the selected run."""
    dataset_path = Path(os.environ.get("COPYCAT_GOLD_DATA_PATH", DEFAULT_DATASET_PATH))
    if not dataset_path.is_file():
        pytest.skip(
            "Copycat gold data is not available. Recreate it from "
            "datasets/copycat/original_copycat_results.template.json."
        )
    dataset = json.loads(dataset_path.read_text(encoding="utf-8"))
    full_run = request.config.getoption("--full")
    cases = (
        dataset["results"]
        if full_run
        else [
            case
            for case in dataset["results"]
            if case["problem"] in dataset["basic_problems"]
        ]
    )
    return {
        case["problem"]: gold_behaviour_dataframe(
            case["solutions"], case["codelets"]
        )
        for case in cases
    }


def gold_behaviour_dataframe(
    gold_solutions: dict[str, dict[str, float | int]],
    gold_codelets: dict[str, float],
) -> pd.DataFrame:
    """Convert Copycat's published data to the experiment summary schema."""
    solutions = pd.DataFrame.from_dict(gold_solutions, orient="index")
    solutions.index.name = "solution"
    solutions = solutions.reset_index().rename(
        columns={"temperature_mean": "mean_temperature"},
    )
    solutions["mean_codelets_run"] = None
    solutions["codelets_standard_error"] = None
    totals = pd.DataFrame(
        [
            {
                "solution": "Total",
                "frequency": int(solutions["frequency"].sum()),
                "mean_codelets_run": gold_codelets["mean"],
                "codelets_standard_error": gold_codelets["standard_error"],
                "mean_temperature": None,
                "temperature_standard_error": None,
            }
        ]
    )
    return pd.concat([solutions, totals], ignore_index=True)[
        [
            "solution",
            "frequency",
            "mean_codelets_run",
            "codelets_standard_error",
            "mean_temperature",
            "temperature_standard_error",
        ]
    ]
