from pathlib import Path

import cattykit

_REPOSITORY_ROOT = Path(__file__).parent.parent


def main() -> None:
    cattykit.install_model(_REPOSITORY_ROOT / "models" / "copycat")

    results_db = cattykit.run_experiment(
        model_name="copycat",
        problems=[
            "abc -> abd ==> ijk -> ?",
            "abc -> abc ==> iijjkk -> ?",
            "abc -> abc ==> kji -> ?",
            "abc -> abc ==> mrrjjj -> ?",
            "abc -> abc ==> xyz -> ?",
        ],
        iterations=1_000,
    )
    print(f"Results saved to {results_db}")


if __name__ == "__main__":
    main()
