# Reproduction Experiments for Copycat

This directory contains scripts for running experiments and generating tables and figures
as part of a reproduction study of the model Copycat. The scripts go hand in had with data
stored in [datasets/copycat-reproduction](../../datasets/copycat-reproduction/) and output
artefacts in [papers/copycat-reproduction](../../papers/copycat-reproduction/).

## Running the scripts

Scripts produce outputs which are consumed by subsequent scripts according to the dependency graph:

```text
00_run_baseline.py ─────> 10_analyse_baseline.py ─────> 20_plot_basic_problems.py
 │
 ├──────────────────────> 13_analyse_codelets_vs_temperature.py
 │
 ├──────────────────────> 14_analyse_codelets_vs_snags.py
 │
 ├─> 01_run_removal_methods.py ─> 11_analyse_removal_methods.py
 │
 ├─> 02_run_with_quantization.py ─> 12_analyse_quantisation.py ─> 22_plot_quantized_basic_problems.py
 │
 ├──────────────────────> 15_analyse_frequence_sampling_variation.py
 │
 └──────────────────────> 16_analyse_transcription_precision.py
```

Scripts beginning with `0` run Copycat or altered versions of Copycat and generate raw CSV outputs
saved under [datasets/copycat-reproduction](../../datasets/copycat-reproduction/):

- `reproduction/` for baseline runs and baseline-derived analysis;
- `coderack_removal/` for coderack-removal runs and comparisons; and
- `quantization/` for quantized runs and comparisons.

Scripts beginning with `1` use these CSV files to generate tables of summary statistics saved in
[the matching dataset subdirectory](../../datasets/copycat-reproduction/) and
[papers/copycat-reproduction/tables](../../papers/copycat-reproduction/tables/).

The original Copycat reference data is input only and lives in
[`datasets/copycat-reproduction/original/`](../../datasets/copycat-reproduction/original/).
The snag-correlation analysis reads baseline runs from `reproduction/` and writes its
result to `snags/`.

Scripts beginning with `2` use previously generated tables to draw PNG figures saved in
[papers/copycat-reproduction/figures](../../papers/copycat-reproduction/figures/).

To run all experiment scripts, run:

``` bash
make all
```

For the baseline analysis, run:

``` bash
make baseline
```
