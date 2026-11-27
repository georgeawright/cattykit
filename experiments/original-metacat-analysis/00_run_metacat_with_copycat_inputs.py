"""Run a grid of original Metacat trials and save the raw results."""

import argparse
import csv
import fcntl
import json
from contextlib import nullcontext
from pathlib import Path

from original_metacat import Metacat

DATASETS = Path(__file__).resolve().parents[2] / "datasets/original-metacat-analysis"
PROBLEMS_PATH = DATASETS / "original-copycat-problems.json"
RESULTS_PATH = DATASETS / "original_metacat_raw_results.csv"
SEEDS = range(1, 2)
CODELET_LIMIT = 100_000
RESULT_COLUMNS = [
    "problem",
    "random_seed",
    "answer",
    "codelets_run",
    "temperature",
    "snag_count",
    "error",
]


def completed_trials(stream) -> set[tuple[str, int]]:
    stream.seek(0)
    last_line = ""

    def read_line():
        nonlocal last_line
        last_line = stream.readline()
        return last_line

    # Using readline keeps tell() usable, including for quoted multiline errors.
    reader = csv.reader(iter(read_line, ""), strict=True)
    completed = set()
    while True:
        offset = stream.tell()
        try:
            row = next(reader, None)
        except csv.Error:
            if last_line:
                raise
            row = []
        if row is None:
            break
        if not last_line.endswith("\n"):
            # A stopped writer may have left an unfinished final record.
            stream.seek(offset)
            stream.truncate()
            break
        if offset == 0:
            if row != RESULT_COLUMNS:
                raise ValueError("Unexpected results CSV header")
        else:
            if len(row) != len(RESULT_COLUMNS):
                raise ValueError(
                    f"Incomplete results CSV record at line {reader.line_num}"
                )
            completed.add((row[0], int(row[1])))
    return completed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--overwrite", action="store_true", help="Start a fresh results CSV"
    )
    args = parser.parse_args()

    problems = json.loads(PROBLEMS_PATH.read_text(encoding="utf-8"))
    RESULTS_PATH.parent.mkdir(parents=True, exist_ok=True)
    written = 0
    with RESULTS_PATH.open(
        "a+", encoding="utf-8", errors="surrogateescape", newline=""
    ) as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            parser.exit(1, f"Another run is writing to {RESULTS_PATH}\n")

        completed = set() if args.overwrite else completed_trials(stream)
        has_pending_trials = any(
            (problem, seed) not in completed for problem in problems for seed in SEEDS
        )
        metacat_context = (
            Metacat.start(codelet_limit=CODELET_LIMIT)
            if has_pending_trials
            else nullcontext()
        )
        with metacat_context as metacat:
            if args.overwrite:
                stream.seek(0)
                stream.truncate()

            writer = csv.writer(stream, lineterminator="\n")
            if stream.tell() == 0:
                writer.writerow(RESULT_COLUMNS)
                stream.flush()
            for problem in problems:
                pending = [seed for seed in SEEDS if (problem, seed) not in completed]
                if pending:
                    print(problem, flush=True)
                for seed in pending:
                    result = metacat.run_once(problem, seed)
                    writer.writerow(
                        [
                            problem,
                            seed,
                            result.answer,
                            result.codelets_run,
                            result.temperature,
                            result.snag_count,
                            result.error,
                        ]
                    )
                    stream.flush()
                    completed.add((problem, seed))
                    written += 1
    print(f"Wrote {written} CSV rows to {RESULTS_PATH}")


if __name__ == "__main__":
    main()
