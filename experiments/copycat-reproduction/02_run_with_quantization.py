"""Run Copycat with its normalized numeric state quantized to percentages.

This is an ablation experiment: the installed Copycat package is patched only
while the experiment runs.  A value such as ``0.376`` is represented as
``0.38`` (the equivalent of an integer score of 38 on Copycat's 0--100 scale).
The patch quantizes persistent floating-point state, NumPy activation arrays,
and values used as probabilities or weighted-selection weights.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from functools import wraps
from types import ModuleType
from typing import Any

import numpy as np
from cattykit.experiments import run_experiment, summarize_runs
from copycat import tools
from copycat_reproduction.experiment_helpers import result_case
from copycat_reproduction.paths import DATASETS, TEMPLATE_PATH

RAW_RESULTS_PATH = DATASETS / "quantized_raw_results.csv"
RESULTS_PATH = DATASETS / "quantized_copycat_results.json"


def quantize(value: object, decimals: int = 2) -> object:
    """Round floats and floating NumPy arrays, leaving discrete values intact."""
    if isinstance(value, float | np.floating):
        return round(float(value), decimals)
    if isinstance(value, np.ndarray) and np.issubdtype(value.dtype, np.floating):
        return np.round(value, decimals)
    if isinstance(value, list):
        return [quantize(item, decimals) for item in value]
    if isinstance(value, tuple):
        return tuple(quantize(item, decimals) for item in value)
    return value


def _quantized_setattr(
    decimals: int, original: Callable[..., None]
) -> Callable[..., None]:
    @wraps(original)
    def patched(self: object, name: str, value: object) -> None:
        original(self, name, quantize(value, decimals))

    return patched


def _quantized_function(
    decimals: int, original: Callable[..., Any]
) -> Callable[..., Any]:
    @wraps(original)
    def patched(*args: object, **kwargs: object) -> Any:
        return quantize(original(*args, **kwargs), decimals)

    return patched


def _quantized_selection(
    decimals: int, original: Callable[..., Any]
) -> Callable[..., Any]:
    """Round sampling weights before Python's random module consumes them."""
    @wraps(original)
    def patched(items: object, weights: object, k: object) -> Any:
        return original(items, quantize(weights, decimals), k)

    return patched


def _copycat_modules() -> Iterator[ModuleType]:
    """Yield loaded Copycat modules, including modules with imported helpers."""
    for name, module in tuple(sys.modules.items()):
        if name == "copycat" or name.startswith("copycat."):
            if module is not None:
                yield module


@contextmanager
def quantized_copycat(decimals: int = 2) -> Iterator[None]:
    """Temporarily quantize Copycat's numeric state and stochastic inputs.

    Copycat imports selection helpers into many modules.  Replacing each loaded
    reference ensures probabilities are rounded immediately before comparisons
    with the random stream, rather than merely when values are logged.
    """
    changes: list[tuple[object, str, object, bool]] = []

    def replace(owner: object, name: str, replacement: object) -> None:
        owner_dict = vars(owner)
        changes.append((owner, name, getattr(owner, name), name in owner_dict))
        setattr(owner, name, replacement)

    # Quantize every float assigned to a Copycat-domain object.  This includes
    # strengths, salience, temperature, Slipnode fields, and NumPy activations.
    classes: set[type[object]] = set()
    for module in _copycat_modules():
        classes.update(
            value
            for value in vars(module).values()
            if isinstance(value, type) and value.__module__.startswith("copycat")
        )
    for class_ in classes:
        replace(class_, "__setattr__", _quantized_setattr(decimals, class_.__setattr__))

    # Quantize direct probability calculations and all weighted choices.  The
    # replacement is installed at every module-level imported reference.
    probability = tools.temperature_adjust_probability
    adjusted_value = tools.temperature_adjust
    adjusted_values = tools.temperature_adjust_list
    selection = tools.select_items_from_list
    for module in _copycat_modules():
        for name, value in tuple(vars(module).items()):
            if value is probability:
                replace(module, name, _quantized_function(decimals, probability))
            elif value is adjusted_value:
                replace(module, name, _quantized_function(decimals, adjusted_value))
            elif value is adjusted_values:
                replace(module, name, _quantized_function(decimals, adjusted_values))
            elif value is selection:
                replace(module, name, _quantized_selection(decimals, selection))
    try:
        yield
    finally:
        for owner, name, original, was_defined in reversed(changes):
            if was_defined:
                setattr(owner, name, original)
            else:
                delattr(owner, name)


def main(iterations: int = 1000, decimals: int = 2) -> None:
    """Run every source problem once per seed with quantized Copycat values."""
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    if decimals < 0:
        raise ValueError("decimals must not be negative")
    DATASETS.mkdir(parents=True, exist_ok=True)
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    cases_by_problem = {case["problem"]: case for case in template["results"]}
    with quantized_copycat(decimals):
        result = run_experiment(
            "copycat",
            list(cases_by_problem),
            iterations,
            verbose=False,
            record_attributes=["snag_count"],
            summary_function=summarize_runs,
            progress_callback=lambda number, total, problem: print(
                f"[quantized {number}/{total}] {problem}"
            ),
        )
    result.save_raw_runs_csv(RAW_RESULTS_PATH)
    reproduced_cases = [
        result_case(
            problem,
            result.summary.loc[result.summary["problem"] == problem],
            case["source"],
            case["id"],
        )
        for problem, case in cases_by_problem.items()
    ]
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
    parser.add_argument("--decimals", type=int, default=2)
    arguments = parser.parse_args()
    main(arguments.iterations, arguments.decimals)
