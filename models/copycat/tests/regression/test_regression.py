from datetime import datetime
from pathlib import Path

import pytest

from cattykit.logging import SQLiteLogger
from cattykit.experiments import run_experiment, total_variation_distance

_CONFIG_DIRECTORY = (
    Path(__file__).parent.parent / "models" / "copycat" / "copycat" / "configs"
)
NOW = datetime.now().strftime("%Y%m%d-%H%M%S")


@pytest.mark.parametrize(
    "problem, gold_distribution",
    [
        (
            "abc -> abd ==> ijk -> ?",
            {
                "ijl": 969,
                "ijd": 27,
                "ijk": 2,
                "hjk": 1,
                "ijj": 1,
            },
        ),
        (
            "abc -> abd ==> iijjkk -> ?",
            {
                "iijjll": 810,
                "iijjkl": 165,
                "iijjdd": 9,
                "iikkll": 9,
                "iijkll": 3,
                "iijjkd": 3,
                "ijkkll": 1,
            },
        ),
        (
            "abc -> abd ==> kji -> ?",
            {
                "kjh": 561,
                "kjj": 238,
                "lji": 106,
                "kjd": 11,
                "kkj": 3,
                "kji": 1,
            },
        ),
        (
            "abc -> abd ==> mrrjjj -> ?",
            {
                "mrrkkk": 705,
                "mrrjjk": 197,
                "mrrjkk": 48,
                "mrrjjjj": 42,
                "mrrjjd": 6,
                "mrrjjj": 2,
            },
        ),
        (
            "abc -> abd ==> xyz -> ?",
            {
                "xyd": 811,
                "wyz": 114,
                "yyz": 60,
                "dyz": 7,
                "xyz": 4,
                "xyy": 3,
                "xxyz": 1,
            },
        ),
    ],
)
def test_matches_copycat_answers(problem, gold_distribution):
    logging_db = f"copycat-regression-{NOW}.sqlite"
    iterations = sum(count for _, count in gold_distribution.items())
    result = run_experiment("copycat", [problem], iterations, logging_db)
    answer_distribution = result.distributions[problem]
    distance = total_variation_distance(gold_distribution, answer_distribution)
    assert distance <= 0.05
