"""Run only the two alternative coderack-removal methods."""

from __future__ import annotations

import argparse
import json
import random
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from typing import Any

from cattykit.experiments import run_experiment, summarize_runs
from copycat.coderack import Coderack
from copycat_reproduction.experiment_helpers import result_case
from copycat_reproduction.paths import (
    DATASETS,
    TEMPLATE_PATH,
)

RemovalMethod = Callable[[Coderack, int, float], None]


def faithful_original_removal(
    coderack: Coderack, count: int, temperature: float
) -> None:
    """Translate the original Lisp removal loop, including its stale weights."""
    codelets = coderack.codelets
    weights = coderack.get_urgency_bin_weights(temperature)
    probabilities = [
        (coderack.number_of_codelets_run - codelet.birth_time)
        * (1 + weights[-1] - weights[codelet.urgency_bin])
        for codelet in codelets
    ]
    removed = 0
    while removed < count and codelets:
        total = sum(probabilities)
        if total <= 0:
            index = random.randrange(len(probabilities))
        else:
            selected = random.randrange(total)
            cumulative = 0
            for candidate, probability in enumerate(probabilities):
                cumulative += probability
                if cumulative > selected:
                    index = candidate
                    break
        if index >= len(codelets):
            continue
        coderack._remove(codelets.pop(index))
        removed += 1


@contextmanager
def patched_removal(method: RemovalMethod) -> Iterator[None]:
    """Install one alternative removal method only for the enclosed work."""
    original = Coderack.remove_codelets
    Coderack.remove_codelets = method
    try:
        yield
    finally:
        Coderack.remove_codelets = original


def run_method(name: str, method: RemovalMethod, iterations: int) -> None:
    """Run one alternative and save its raw CSV and summary JSON."""
    template = json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))
    with patched_removal(method):
        result = run_experiment(
            "copycat",
            [case["problem"] for case in template["results"]],
            iterations,
            verbose=False,
            record_attributes=["snag_count"],
            summary_function=summarize_runs,
            progress_callback=lambda number, total, problem: print(
                f"[{name} {number}/{total}] {problem}"
            ),
        )
    cases = [
        result_case(
            case["problem"],
            result.summary.loc[result.summary["problem"] == case["problem"]],
            case["source"],
            case["id"],
        )
        for case in template["results"]
    ]
    reproduction: dict[str, Any] = {
        "schema_version": template["schema_version"],
        "source_work": template["source_work"],
        "basic_problems": template["basic_problems"],
        "results": cases,
    }
    raw_runs = result.raw_runs.assign(method=name)
    raw_runs.to_csv(DATASETS / f"coderack_removal_{name}_raw_results.csv", index=False)
    (DATASETS / f"coderack_removal_{name}_results.json").write_text(
        json.dumps(reproduction, indent=2) + "\n", encoding="utf-8"
    )


def main(iterations: int = 1000) -> None:
    """Run alternatives only; script 00 exclusively owns the baseline run."""
    if iterations < 1:
        raise ValueError("iterations must be at least 1")
    DATASETS.mkdir(parents=True, exist_ok=True)
    run_method("faithful_original_removal", faithful_original_removal, iterations)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=1000)
    main(parser.parse_args().iterations)
