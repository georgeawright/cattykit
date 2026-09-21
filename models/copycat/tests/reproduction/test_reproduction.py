from cattykit.experiments import run_reproduction


def test_matches_copycat_answers(gold_behaviour):
    _, summary = run_reproduction(
        "copycat", gold_behaviour, iterations=1000, output_file="reproductions.csv"
    )

    assert summary["mean_total_variation_distance"] <= 0.05
    assert summary["max_total_variation_distance"] <= 0.10
    assert summary["temperature_rms_z_score"] <= 1.5
    assert summary["temperature_max_absolute_z_score"] <= 4
    assert summary["codelets_rms_z_score"] <= 1.5
    assert summary["codelets_max_absolute_z_score"] <= 4
