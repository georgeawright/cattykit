import cattykit


def main() -> None:
    results_db = cattykit.run_experiment(
        model_name="copycat",
        problems=[
            "abc -> abd ==> ijk -> ?",
            "abc -> abc ==> iijjkk -> ?",
            "abc -> abc ==> kji -> ?",
            "abc -> abc ==> mrrjjj -> ?",
            "abc -> abc ==> xyz -> ?",
        ],
        iterations=10,
    )
    print(f"Results saved to {results_db}")


if __name__ == "__main__":
    main()
