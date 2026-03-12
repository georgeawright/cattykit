from copycat import Copycat

SLIPNET_JSON_FILE = "slipnet.json"
CODERACK_JSON_FILE = "coderack.json"


def main():
    copycat = Copycat.from_json(SLIPNET_JSON_FILE, CODERACK_JSON_FILE)


if __name__ == "__main__":
    main()
