import importlib

import pandas as pd
import pytest
from cattykit.experiments import ExperimentResult, run_reproduction


def test_run_reproduction_compares_standard_summary_rows(monkeypatch, tmp_path):
    observed = pd.DataFrame(
        [
            {
                "problem": "abc",
                "solution": "abd",
                "frequency": 5,
                "mean_codelets_run": 10.0,
                "codelets_standard_error": 1.0,
                "mean_temperature": 0.4,
                "temperature_standard_error": 0.1,
            },
            {
                "problem": "abc",
                "solution": "abe",
                "frequency": 0,
                "mean_codelets_run": 10.0,
                "codelets_standard_error": 1.0,
                "mean_temperature": 0.4,
                "temperature_standard_error": 0.1,
            },
            {
                "problem": "abc",
                "solution": "Total",
                "frequency": 5,
                "mean_codelets_run": 10.0,
                "codelets_standard_error": 1.0,
                "mean_temperature": None,
                "temperature_standard_error": None,
            },
        ]
    )
    module = importlib.import_module("cattykit.experiments.reproduction")
    monkeypatch.setattr(
        module,
        "run_experiment",
        lambda *args, **kwargs: ExperimentResult(observed, pd.DataFrame()),
    )
    gold = {
        "abc": [
            {
                "solution": "abd",
                "frequency": 4,
                "mean_codelets_run": None,
                "codelets_standard_error": None,
                "mean_temperature": 0.5,
                "temperature_standard_error": 0.1,
            },
            {
                "solution": "abe",
                "frequency": 1,
                "mean_codelets_run": None,
                "codelets_standard_error": None,
                "mean_temperature": 0.2,
                "temperature_standard_error": 0.1,
            },
            {
                "solution": "Total",
                "frequency": 5,
                "mean_codelets_run": 8.0,
                "codelets_standard_error": 1.0,
                "mean_temperature": None,
                "temperature_standard_error": None,
            },
        ]
    }

    output_path = tmp_path / "comparison.csv"
    comparison, summary = run_reproduction("model", gold, 5, output_path)

    assert comparison["solution"].tolist() == ["Total", "abd", "abe"]
    assert comparison.loc[2, "observed_frequency"] == 0
    assert comparison.loc[0, "tv_distance"] == pytest.approx(0.2)
    assert summary["mean_codelets_relative_error_magnitude"] == 0.25
    assert summary["mean_temperature_absolute_error_magnitude"] == pytest.approx(0.12)
    assert summary["max_temperature_absolute_error_magnitude"] == pytest.approx(0.12)
    assert summary["temperature_absolute_error_magnitude_by_problem"] == {
        "abc": pytest.approx(0.12)
    }
    assert output_path.is_file()
