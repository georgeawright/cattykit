import random

from copycat import Copycat

random.seed(0)

SLIPNET_JSON_FILE = "configs/slipnet.json"
CODERACK_JSON_FILE = "configs/coderack.json"
HYPERPARAMETERS_FILE = "configs/hyperparameters.json"


def main():
    copycat = Copycat.from_json(
        SLIPNET_JSON_FILE, CODERACK_JSON_FILE, HYPERPARAMETERS_FILE
    )
    copycat.solve("abc -> abd ==> ijk -> ?")


if __name__ == "__main__":
    main()
