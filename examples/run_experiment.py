import cattykit


def main() -> None:
    results = cattykit.run_experiment(
        model_name="copycat",
        problems=[
            "abc -> abd ==> ijk -> ?",
            "abc -> abd ==> iijjkk -> ?",
            "abc -> abd ==> kji -> ?",
            "abc -> abd ==> mrrjjj -> ?",
            "abc -> abd ==> xyz -> ?",
        ],
        iterations=1000,
    )


if __name__ == "__main__":
    main()
