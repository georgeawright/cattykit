from cattykit.experiments import run_reproduction


def test_matches_copycat_answers(gold_behaviour):
    _, summary = run_reproduction(
        "copycat", gold_behaviour, iterations=1000, output_file="reproductions.csv"
    )

    assert summary["mean_total_variation_distance"] <= 0.05
    assert summary["max_total_variation_distance"] <= 0.10
    assert summary["mean_temperature_absolute_error_magnitude"] <= 0.05
    assert summary["max_temperature_absolute_error_magnitude"] <= 0.10
    assert summary["mean_codelets_relative_error_magnitude"] <= 0.10
    assert summary["codelets_relative_error_magnitude_quantiles"][90] <= 0.25
