import pytest


BASIC_PROBLEMS = {
    "abc -> abd ==> ijk -> ?",
    "abc -> abd ==> kji -> ?",
}


ORIGINAL_COPYCAT_RESULTS = [
    (
        "abc -> abd ==> ijk -> ?",
        {
            "ijl": {
                "frequency": 969,
                "temperature_mean": 0.17,
                "temperature_standard_error": 0.003,
            },
            "ijd": {
                "frequency": 27,
                "temperature_mean": 0.23,
                "temperature_standard_error": 0.021,
            },
            "ijk": {
                "frequency": 2,
                "temperature_mean": 0.72,
                "temperature_standard_error": 0.035,
            },
            "hjk": {
                "frequency": 1,
                "temperature_mean": 0.16,
                "temperature_standard_error": 0.0,
            },
            "ijj": {
                "frequency": 1,
                "temperature_mean": 0.32,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 293, "standard_error": 3.0},
    ),
    (
        "abc -> abd ==> iijjkk -> ?",
        {
            "iijjll": {
                "frequency": 810,
                "temperature_mean": 0.27,
                "temperature_standard_error": 0.003,
            },
            "iijjkl": {
                "frequency": 165,
                "temperature_mean": 0.47,
                "temperature_standard_error": 0.007,
            },
            "iijjdd": {
                "frequency": 9,
                "temperature_mean": 0.32,
                "temperature_standard_error": 0.033,
            },
            "iikkll": {
                "frequency": 9,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.016,
            },
            "iijkll": {
                "frequency": 3,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.0,
            },
            "iijjkd": {
                "frequency": 3,
                "temperature_mean": 0.65,
                "temperature_standard_error": 0.062,
            },
            "ijkkll": {
                "frequency": 1,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 585, "standard_error": 7.5},
    ),
    (
        "abc -> abd ==> kji -> ?",
        {
            "kjh": {
                "frequency": 561,
                "temperature_mean": 0.14,
                "temperature_standard_error": 0.002,
            },
            "kjj": {
                "frequency": 238,
                "temperature_mean": 0.44,
                "temperature_standard_error": 0.006,
            },
            "lji": {
                "frequency": 186,
                "temperature_mean": 0.18,
                "temperature_standard_error": 0.003,
            },
            "kjd": {
                "frequency": 11,
                "temperature_mean": 0.37,
                "temperature_standard_error": 0.063,
            },
            "kkj": {
                "frequency": 3,
                "temperature_mean": 0.5,
                "temperature_standard_error": 0.027,
            },
            "kji": {
                "frequency": 1,
                "temperature_mean": 0.73,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 395, "standard_error": 5.0},
    ),
    (
        "abc -> abd ==> mrrjjj -> ?",
        {
            "mrrkkk": {
                "frequency": 705,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.002,
            },
            "mrrjjk": {
                "frequency": 197,
                "temperature_mean": 0.49,
                "temperature_standard_error": 0.006,
            },
            "mrrjkk": {
                "frequency": 48,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.006,
            },
            "mrrjjjj": {
                "frequency": 42,
                "temperature_mean": 0.21,
                "temperature_standard_error": 0.006,
            },
            "mrrjjd": {
                "frequency": 6,
                "temperature_mean": 0.62,
                "temperature_standard_error": 0.031,
            },
            "mrrjjj": {
                "frequency": 2,
                "temperature_mean": 0.82,
                "temperature_standard_error": 0.025,
            },
        },
        {"mean": 829, "standard_error": 15.7},
    ),
    (
        "abc -> abd ==> xyz -> ?",
        {
            "xyd": {
                "frequency": 811,
                "temperature_mean": 0.22,
                "temperature_standard_error": 0.005,
            },
            "wyz": {
                "frequency": 114,
                "temperature_mean": 0.14,
                "temperature_standard_error": 0.003,
            },
            "yyz": {
                "frequency": 60,
                "temperature_mean": 0.44,
                "temperature_standard_error": 0.012,
            },
            "dyz": {
                "frequency": 7,
                "temperature_mean": 0.33,
                "temperature_standard_error": 0.073,
            },
            "xyz": {
                "frequency": 4,
                "temperature_mean": 0.64,
                "temperature_standard_error": 0.103,
            },
            "xyy": {
                "frequency": 3,
                "temperature_mean": 0.36,
                "temperature_standard_error": 0.015,
            },
            "xxyz": {
                "frequency": 1,
                "temperature_mean": 0.25,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 3208, "standard_error": 88.3},
    ),
]


def pytest_configure(config):
    if config.getoption("--basic") and config.getoption("--full"):
        raise pytest.UsageError("--basic and --full cannot be used together")


def pytest_generate_tests(metafunc):
    parameter_names = ("problem", "gold_solutions", "gold_codelets")
    if not set(parameter_names).issubset(metafunc.fixturenames):
        return

    full_run = metafunc.config.getoption("--full")
    cases = (
        ORIGINAL_COPYCAT_RESULTS
        if full_run
        else [case for case in ORIGINAL_COPYCAT_RESULTS if case[0] in BASIC_PROBLEMS]
    )
    metafunc.parametrize(parameter_names, cases, ids=[case[0] for case in cases])
