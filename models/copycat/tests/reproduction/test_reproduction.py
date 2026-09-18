from cattykit.experiments import (
    run_experiment,
    total_variation_distance,
    z_statistic,
)


def test_matches_copycat_answers(problem, gold_solutions, gold_codelets):
    iterations = sum(solution["frequency"] for solution in gold_solutions.values())
    result = run_experiment("copycat", [problem], iterations)
    answer_distribution = result.distributions[problem]
    gold_distribution = {
        solution: statistics["frequency"]
        for solution, statistics in gold_solutions.items()
    }

    distance = total_variation_distance(gold_distribution, answer_distribution)
    assert distance <= 0.05

    summary = result.summaries[problem]

    for solution, gold_temperature in gold_solutions.items():
        if gold_temperature["frequency"] <= 10:
            continue
        observed = summary.loc[summary["solution"] == solution]
        assert not observed.empty
        temperature_z_score = z_statistic(
            observed.iloc[0]["mean_temperature"],
            gold_temperature["temperature_mean"],
            observed.iloc[0]["temperature_standard_error"],
            gold_temperature["temperature_standard_error"],
        )
        assert abs(temperature_z_score) < 2.0
        # lower z statistics indicate less discrepancy between
        # the behaviour of the implementations

    total = summary.loc[summary["solution"] == "Total"].iloc[0]
    codelets_z_score = z_statistic(
        total["mean_codelets_run"],
        gold_codelets["mean"],
        total["codelets_standard_error"],
        gold_codelets["standard_error"],
    )
    assert abs(codelets_z_score) < 2.5
    # the maximum z-statistic is less stringent for codelet count
    # as it is a measure of search path or stopping time.
    # This is more sensitive to the program's stochasticity than
    # final temperature and has a heavier tailed distribution.
