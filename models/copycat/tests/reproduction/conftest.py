import pandas as pd
import pytest


BASIC_PROBLEMS = {
    "abc -> abd ==> ijk -> ?",
    "abc -> abd ==> iijjkk -> ?",
    "abc -> abd ==> kji -> ?",
    "abc -> abd ==> mrrjjj -> ?",
    "abc -> abd ==> xyz -> ?",
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
    (
        "abc -> abd ==> ijklmnop -> ?",
        {
            "ijklmnoq": {
                "frequency": 913,
                "temperature_mean": 0.29,
                "temperature_standard_error": 0.005,
            },
            "ijklnopq": {
                "frequency": 25,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.006,
            },
            "ijklmnod": {
                "frequency": 16,
                "temperature_mean": 0.53,
                "temperature_standard_error": 0.054,
            },
            "ijklmnopq": {
                "frequency": 13,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.013,
            },
            "ijklmnpq": {
                "frequency": 11,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.012,
            },
            "ijkmnopq": {
                "frequency": 11,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.007,
            },
            "ijlmnopq": {
                "frequency": 5,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.006,
            },
            "iklmnopq": {
                "frequency": 3,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.006,
            },
            "iklmnop": {
                "frequency": 3,
                "temperature_mean": 0.65,
                "temperature_standard_error": 0.032,
            },
        },
        {"mean": 581, "standard_error": 8.9},
    ),
    (
        "abc -> abd ==> xlg -> ?",
        {
            "xlh": {
                "frequency": 985,
                "temperature_mean": 0.42,
                "temperature_standard_error": 0.001,
            },
            "xld": {
                "frequency": 14,
                "temperature_mean": 0.52,
                "temperature_standard_error": 0.017,
            },
            "xlg": {
                "frequency": 1,
                "temperature_mean": 0.90,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 323, "standard_error": 5.3},
    ),
    (
        "abc -> abd ==> xcg -> ?",
        {
            "xch": {
                "frequency": 974,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.001,
            },
            "xdg": {
                "frequency": 14,
                "temperature_mean": 0.56,
                "temperature_standard_error": 0.018,
            },
            "xcd": {
                "frequency": 12,
                "temperature_mean": 0.51,
                "temperature_standard_error": 0.015,
            },
        },
        {"mean": 498, "standard_error": 10.5},
    ),
    (
        "abc -> abd ==> abcd -> ?",
        {
            "abce": {
                "frequency": 913,
                "temperature_mean": 0.18,
                "temperature_standard_error": 0.003,
            },
            "abdd": {
                "frequency": 63,
                "temperature_mean": 0.26,
                "temperature_standard_error": 0.015,
            },
            "abcd": {
                "frequency": 21,
                "temperature_mean": 0.23,
                "temperature_standard_error": 0.033,
            },
            "abde": {
                "frequency": 2,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.0,
            },
            "acde": {
                "frequency": 1,
                "temperature_mean": 0.41,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 333, "standard_error": 4.1},
    ),
    (
        "abc -> abd ==> cde -> ?",
        {
            "cdf": {
                "frequency": 835,
                "temperature_mean": 0.17,
                "temperature_standard_error": 0.003,
            },
            "bde": {
                "frequency": 109,
                "temperature_mean": 0.16,
                "temperature_standard_error": 0.003,
            },
            "dde": {
                "frequency": 37,
                "temperature_mean": 0.41,
                "temperature_standard_error": 0.014,
            },
            "cdd": {
                "frequency": 17,
                "temperature_mean": 0.19,
                "temperature_standard_error": 0.019,
            },
            "cef": {
                "frequency": 2,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.010,
            },
        },
        {"mean": 304, "standard_error": 3.1},
    ),
    (
        "abc -> abd ==> cab -> ?",
        {
            "dab": {
                "frequency": 491,
                "temperature_mean": 0.41,
                "temperature_standard_error": 0.003,
            },
            "cac": {
                "frequency": 364,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.004,
            },
            "cbc": {
                "frequency": 137,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.003,
            },
            "cabc": {
                "frequency": 3,
                "temperature_mean": 0.27,
                "temperature_standard_error": 0.010,
            },
            "cad": {
                "frequency": 3,
                "temperature_mean": 0.44,
                "temperature_standard_error": 0.022,
            },
            "cab": {
                "frequency": 1,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.0,
            },
            "cdd": {
                "frequency": 1,
                "temperature_mean": 0.48,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 712, "standard_error": 16.7},
    ),
    (
        "abc -> abd ==> cmg -> ?",
        {
            "cmh": {
                "frequency": 699,
                "temperature_mean": 0.42,
                "temperature_standard_error": 0.001,
            },
            "dmg": {
                "frequency": 296,
                "temperature_mean": 0.41,
                "temperature_standard_error": 0.003,
            },
            "cmd": {
                "frequency": 5,
                "temperature_mean": 0.49,
                "temperature_standard_error": 0.043,
            },
        },
        {"mean": 307, "standard_error": 5.1},
    ),
    (
        "abc -> qbc ==> ijk -> ?",
        {
            "qjk": {
                "frequency": 999,
                "temperature_mean": 0.19,
                "temperature_standard_error": 0.002,
            },
            "ijk": {
                "frequency": 1,
                "temperature_mean": 0.30,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 306, "standard_error": 3.0},
    ),
    (
        "aabc -> aabd ==> ijkk -> ?",
        {
            "ijll": {
                "frequency": 612,
                "temperature_mean": 0.29,
                "temperature_standard_error": 0.004,
            },
            "ijkl": {
                "frequency": 198,
                "temperature_mean": 0.49,
                "temperature_standard_error": 0.007,
            },
            "jjkk": {
                "frequency": 121,
                "temperature_mean": 0.47,
                "temperature_standard_error": 0.009,
            },
            "hjkk": {
                "frequency": 47,
                "temperature_mean": 0.19,
                "temperature_standard_error": 0.005,
            },
            "jkkk": {
                "frequency": 9,
                "temperature_mean": 0.42,
                "temperature_standard_error": 0.023,
            },
            "ijkd": {
                "frequency": 6,
                "temperature_mean": 0.57,
                "temperature_standard_error": 0.040,
            },
            "ijdd": {
                "frequency": 3,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.059,
            },
            "ijkk": {
                "frequency": 3,
                "temperature_mean": 0.69,
                "temperature_standard_error": 0.098,
            },
            "djkk": {
                "frequency": 1,
                "temperature_mean": 0.58,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 750, "standard_error": 11.5},
    ),
    (
        "abcm -> abcn ==> rijk -> ?",
        {
            "sijk": {
                "frequency": 398,
                "temperature_mean": 0.68,
                "temperature_standard_error": 0.002,
            },
            "rijl": {
                "frequency": 391,
                "temperature_mean": 0.64,
                "temperature_standard_error": 0.005,
            },
            "rjkl": {
                "frequency": 168,
                "temperature_mean": 0.59,
                "temperature_standard_error": 0.004,
            },
            "rijn": {
                "frequency": 19,
                "temperature_mean": 0.67,
                "temperature_standard_error": 0.020,
            },
            "nijk": {
                "frequency": 6,
                "temperature_mean": 0.74,
                "temperature_standard_error": 0.014,
            },
            "rikl": {
                "frequency": 5,
                "temperature_mean": 0.65,
                "temperature_standard_error": 0.040,
            },
            "rijk": {
                "frequency": 5,
                "temperature_mean": 0.83,
                "temperature_standard_error": 0.016,
            },
            "qijk": {
                "frequency": 4,
                "temperature_mean": 0.59,
                "temperature_standard_error": 0.044,
            },
            "rnnn": {
                "frequency": 3,
                "temperature_mean": 0.66,
                "temperature_standard_error": 0.036,
            },
            "rhij": {
                "frequency": 1,
                "temperature_mean": 0.55,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 1777, "standard_error": 52.6},
    ),
    (
        "abc -> abd ==> hhwwqq -> ?",
        {
            "hhwwrr": {
                "frequency": 703,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.002,
            },
            "hhwwqr": {
                "frequency": 261,
                "temperature_mean": 0.47,
                "temperature_standard_error": 0.005,
            },
            "hhxxrr": {
                "frequency": 18,
                "temperature_mean": 0.39,
                "temperature_standard_error": 0.007,
            },
            "hhwwqd": {
                "frequency": 11,
                "temperature_mean": 0.62,
                "temperature_standard_error": 0.035,
            },
            "hhwwdd": {
                "frequency": 4,
                "temperature_mean": 0.50,
                "temperature_standard_error": 0.049,
            },
            "hhwwqq": {
                "frequency": 2,
                "temperature_mean": 0.59,
                "temperature_standard_error": 0.0,
            },
            "ihwwqq": {
                "frequency": 1,
                "temperature_mean": 0.52,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 794, "standard_error": 14.0},
    ),
    (
        "abc -> abd ==> lmfgop -> ?",
        {
            "lmfgoq": {
                "frequency": 530,
                "temperature_mean": 0.51,
                "temperature_standard_error": 0.003,
            },
            "lmfgpq": {
                "frequency": 443,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.003,
            },
            "lmfgod": {
                "frequency": 14,
                "temperature_mean": 0.56,
                "temperature_standard_error": 0.030,
            },
            "lmfgop": {
                "frequency": 9,
                "temperature_mean": 0.66,
                "temperature_standard_error": 0.031,
            },
            "lmfgdd": {
                "frequency": 4,
                "temperature_mean": 0.54,
                "temperature_standard_error": 0.033,
            },
        },
        {"mean": 1023, "standard_error": 21.9},
    ),
    (
        "abc -> abd ==> lmnfghopq -> ?",
        {
            "lmnfghpqr": {
                "frequency": 479,
                "temperature_mean": 0.47,
                "temperature_standard_error": 0.003,
            },
            "lmnfghopr": {
                "frequency": 462,
                "temperature_mean": 0.53,
                "temperature_standard_error": 0.003,
            },
            "lmnfghoqr": {
                "frequency": 26,
                "temperature_mean": 0.50,
                "temperature_standard_error": 0.010,
            },
            "lmnfghopd": {
                "frequency": 21,
                "temperature_mean": 0.59,
                "temperature_standard_error": 0.017,
            },
            "lmnfghopq": {
                "frequency": 6,
                "temperature_mean": 0.61,
                "temperature_standard_error": 0.014,
            },
            "lmnfghddd": {
                "frequency": 6,
                "temperature_mean": 0.51,
                "temperature_standard_error": 0.019,
            },
        },
        {"mean": 1067, "standard_error": 22.2},
    ),
    (
        "aabbcc -> aabbcd ==> iijjkk -> ?",
        {
            "iijjkl": {
                "frequency": 879,
                "temperature_mean": 0.32,
                "temperature_standard_error": 0.004,
            },
            "iijjll": {
                "frequency": 103,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.009,
            },
            "iijjkkk": {
                "frequency": 6,
                "temperature_mean": 0.39,
                "temperature_standard_error": 0.016,
            },
            "iijjkd": {
                "frequency": 4,
                "temperature_mean": 0.51,
                "temperature_standard_error": 0.105,
            },
            "ijjkk": {
                "frequency": 3,
                "temperature_mean": 0.56,
                "temperature_standard_error": 0.027,
            },
            "iijjdd": {
                "frequency": 2,
                "temperature_mean": 0.62,
                "temperature_standard_error": 0.015,
            },
            "iikkll": {
                "frequency": 1,
                "temperature_mean": 0.50,
                "temperature_standard_error": 0.0,
            },
            "jijjkk": {
                "frequency": 1,
                "temperature_mean": 0.60,
                "temperature_standard_error": 0.0,
            },
            "iijkll": {
                "frequency": 1,
                "temperature_mean": 0.48,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 725, "standard_error": 8.3},
    ),
    (
        "abc -> abd ==> edc -> ?",
        {
            "edb": {
                "frequency": 645,
                "temperature_mean": 0.13,
                "temperature_standard_error": 0.001,
            },
            "edd": {
                "frequency": 328,
                "temperature_mean": 0.38,
                "temperature_standard_error": 0.005,
            },
            "fdc": {
                "frequency": 26,
                "temperature_mean": 0.20,
                "temperature_standard_error": 0.010,
            },
            "eed": {
                "frequency": 1,
                "temperature_mean": 0.51,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 348, "standard_error": 4.6},
    ),
    (
        "abc -> abd ==> cba -> ?",
        {
            "dba": {
                "frequency": 885,
                "temperature_mean": 0.16,
                "temperature_standard_error": 0.004,
            },
            "cbb": {
                "frequency": 88,
                "temperature_mean": 0.48,
                "temperature_standard_error": 0.023,
            },
            "cbd": {
                "frequency": 26,
                "temperature_mean": 0.22,
                "temperature_standard_error": 0.034,
            },
            "ccb": {
                "frequency": 1,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 404, "standard_error": 9.8},
    ),
    (
        "abc -> abd ==> mrr -> ?",
        {
            "mss": {
                "frequency": 640,
                "temperature_mean": 0.42,
                "temperature_standard_error": 0.001,
            },
            "mrs": {
                "frequency": 338,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.003,
            },
            "mrrr": {
                "frequency": 14,
                "temperature_mean": 0.21,
                "temperature_standard_error": 0.01,
            },
            "mrd": {
                "frequency": 5,
                "temperature_mean": 0.52,
                "temperature_standard_error": 0.013,
            },
            "mdd": {
                "frequency": 2,
                "temperature_mean": 0.44,
                "temperature_standard_error": 0.005,
            },
            "mrr": {
                "frequency": 1,
                "temperature_mean": 0.77,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 721, "standard_error": 15.5},
    ),
    (
        "abc -> abd ==> mmrrrjjjj -> ?",
        {
            "mmrrrkkkk": {
                "frequency": 688,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.002,
            },
            "mmrrrjjjk": {
                "frequency": 201,
                "temperature_mean": 0.50,
                "temperature_standard_error": 0.005,
            },
            "mmrrrjkkk": {
                "frequency": 53,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.06,
            },
            "mmrrrjjkk": {
                "frequency": 39,
                "temperature_mean": 0.44,
                "temperature_standard_error": 0.06,
            },
            "mmrrrjjjjj": {
                "frequency": 10,
                "temperature_mean": 0.22,
                "temperature_standard_error": 0.01,
            },
            "mmrrrjjjd": {
                "frequency": 4,
                "temperature_mean": 0.62,
                "temperature_standard_error": 0.06,
            },
            "mmrrrdddd": {
                "frequency": 2,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.025,
            },
            "mmrrrjjjj": {
                "frequency": 2,
                "temperature_mean": 0.64,
                "temperature_standard_error": 0.065,
            },
            "mmrrrjjdd": {
                "frequency": 1,
                "temperature_mean": 0.47,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 829, "standard_error": 14.5},
    ),
    (
        "abc -> abd ==> rssttt -> ?",
        {
            "rssuuu": {
                "frequency": 704,
                "temperature_mean": 0.29,
                "temperature_standard_error": 0.004,
            },
            "rssttu": {
                "frequency": 176,
                "temperature_mean": 0.48,
                "temperature_standard_error": 0.006,
            },
            "rsstuu": {
                "frequency": 46,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.07,
            },
            "rttuuu": {
                "frequency": 45,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.03,
            },
            "rstuuu": {
                "frequency": 15,
                "temperature_mean": 0.45,
                "temperature_standard_error": 0.017,
            },
            "rssddd": {
                "frequency": 8,
                "temperature_mean": 0.48,
                "temperature_standard_error": 0.017,
            },
            "rssttd": {
                "frequency": 3,
                "temperature_mean": 0.58,
                "temperature_standard_error": 0.017,
            },
            "rsstttt": {
                "frequency": 2,
                "temperature_mean": 0.30,
                "temperature_standard_error": 0.030,
            },
            "rsstdd": {
                "frequency": 1,
                "temperature_mean": 0.54,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 666, "standard_error": 11.7},
    ),
    (
        "abc -> abd ==> xpqdef -> ?",
        {
            "xpqefg": {
                "frequency": 504,
                "temperature_mean": 0.46,
                "temperature_standard_error": 0.002,
            },
            "xpqdeg": {
                "frequency": 434,
                "temperature_mean": 0.53,
                "temperature_standard_error": 0.004,
            },
            "xpqdfg": {
                "frequency": 20,
                "temperature_mean": 0.49,
                "temperature_standard_error": 0.011,
            },
            "xpqcdef": {
                "frequency": 13,
                "temperature_mean": 0.23,
                "temperature_standard_error": 0.017,
            },
            "xpqded": {
                "frequency": 11,
                "temperature_mean": 0.59,
                "temperature_standard_error": 0.028,
            },
            "xpqdefg": {
                "frequency": 9,
                "temperature_mean": 0.22,
                "temperature_standard_error": 0.012,
            },
            "xpqdef": {
                "frequency": 5,
                "temperature_mean": 0.62,
                "temperature_standard_error": 0.010,
            },
            "xpqddd": {
                "frequency": 4,
                "temperature_mean": 0.54,
                "temperature_standard_error": 0.033,
            },
        },
        {"mean": 989, "standard_error": 21.5},
    ),
    (
        "abc -> qbc ==> xyz -> ?",
        {
            "qyz": {
                "frequency": 996,
                "temperature_mean": 0.19,
                "temperature_standard_error": 0.003,
            },
            "xyz": {
                "frequency": 3,
                "temperature_mean": 0.73,
                "temperature_standard_error": 0.09,
            },
            "qqz": {
                "frequency": 1,
                "temperature_mean": 0.56,
                "temperature_standard_error": 0.0,
            },
        },
        {"mean": 302, "standard_error": 3.1},
    ),
    (
        "rst -> rsu ==> xyz -> ?",
        {
            "xyu": {
                "frequency": 988,
                "temperature_mean": 0.22,
                "temperature_standard_error": 0.004,
            },
            "wyz": {
                "frequency": 8,
                "temperature_mean": 0.16,
                "temperature_standard_error": 0.012,
            },
            "xyz": {
                "frequency": 4,
                "temperature_mean": 0.65,
                "temperature_standard_error": 0.124,
            },
        },
        {"mean": 3658, "standard_error": 107.2},
    ),
    (
        "abc -> abd ==> glz -> ?",
        {
            "hlz": {
                "frequency": 646,
                "temperature_mean": 0.43,
                "temperature_standard_error": 0.003,
            },
            "gld": {
                "frequency": 338,
                "temperature_mean": 0.49,
                "temperature_standard_error": 0.005,
            },
            "dlz": {
                "frequency": 14,
                "temperature_mean": 0.52,
                "temperature_standard_error": 0.019,
            },
            "glz": {
                "frequency": 2,
                "temperature_mean": 0.69,
                "temperature_standard_error": 0.04,
            },
        },
        {"mean": 5823, "standard_error": 143.1},
    ),
    (
        "abc -> abd ==> cmz -> ?",
        {
            "dmz": {
                "frequency": 904,
                "temperature_mean": 0.40,
                "temperature_standard_error": 0.002,
            },
            "cmd": {
                "frequency": 96,
                "temperature_mean": 0.48,
                "temperature_standard_error": 0.008,
            },
        },
        {"mean": 1779, "standard_error": 50.9},
    ),
]


def pytest_configure(config):
    if config.getoption("--basic") and config.getoption("--full"):
        raise pytest.UsageError("--basic and --full cannot be used together")


@pytest.fixture
def gold_behaviour(request) -> dict[str, pd.DataFrame]:
    """Return the published behaviour for every problem in the selected run."""
    full_run = request.config.getoption("--full")
    cases = (
        ORIGINAL_COPYCAT_RESULTS
        if full_run
        else [case for case in ORIGINAL_COPYCAT_RESULTS if case[0] in BASIC_PROBLEMS]
    )
    return {
        problem: gold_behaviour_dataframe(solutions, codelets)
        for problem, solutions, codelets in cases
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
