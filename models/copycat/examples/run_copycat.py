from pathlib import Path
import random

from cattykit.logging import PrintLogger
from copycat import Copycat

_CONFIG_DIRECTORY = Path(__file__).parent.parent / "configs"


def main() -> None:
    random.seed(1)
    logger = PrintLogger()
    copycat = Copycat.from_json(
        str(_CONFIG_DIRECTORY / "slipnet.json"),
        str(_CONFIG_DIRECTORY / "coderack.json"),
        str(_CONFIG_DIRECTORY / "hyperparameters.json"),
        logger=logger,
    )
    copycat.solve("abc -> abd ==> ijk -> ?")
    logger.close()


if __name__ == "__main__":
    main()
