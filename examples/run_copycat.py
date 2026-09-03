import random
from pathlib import Path

from cattykit.logging import SQLiteLogger
from copycat import Copycat

_CONFIG_DIRECTORY = (
    Path(__file__).parent.parent / "models" / "copycat" / "copycat" / "configs"
)


def main() -> None:
    random.seed(2)
    logger = SQLiteLogger("history.sqlite")
    copycat = Copycat.from_json(
        str(_CONFIG_DIRECTORY / "slipnet.json"),
        str(_CONFIG_DIRECTORY / "coderack.json"),
        str(_CONFIG_DIRECTORY / "hyperparameters.json"),
        logger=logger,
    )
    result = copycat.solve("abc -> abd ==> xyz -> ?")
    print(result)
    logger.close()


if __name__ == "__main__":
    main()
