# Reproduction Experiments for Copycat

This directory contains scripts for running experiments and generating tables and figures
as part of a reproduction study of the model Copycat. The scripts go hand in had with data
stored in [datasets/copycat-replication](../../datasets/copycat-replication/) and output
artefacts in [papers/copycat-replication](../../papers/copycat-replication/).

The experiments pin Cattykit 0.1.4 from PyPI and the Copycat 0.1.2 wheel
from its GitHub release. The lockfile records the complete dependency resolution;
use `uv sync --locked` to install it. Local changes to the model and library
do not affect experiment runs. Record the experiment repository revision as well.

The baseline and coderack-removal runs use Copycat's default two-decimal
precision policy. The unquantized runs explicitly select `FullPrecision()`.
Changing these settings requires rerunning the affected experiments and their
downstream analyses before interpreting existing datasets, tables, or figures.

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
 ├─> 02_run_without_quantization.py ─> 12_analyse_quantization.py ─> 22_plot_unquantized_basic_problems.py
 │
 ├──────────────────────> 15_analyse_frequency_sampling_variation.py
 │
 └──────────────────────> 16_analyse_transcription_precision.py
```

Scripts beginning with `0` run Copycat or altered versions of Copycat and generate raw CSV outputs
saved under [datasets/copycat-replication](../../datasets/copycat-replication/):

- `replication/` for baseline runs and baseline-derived analysis;
- `coderack_removal/` for coderack-removal runs and comparisons; and
- `quantization/` for unquantized runs and comparisons.

Scripts beginning with `1` use these CSV files to generate tables of summary statistics saved in
[the matching dataset subdirectory](../../datasets/copycat-replication/) and
[papers/copycat-replication/tables](../../papers/copycat-replication/tables/).

The original Copycat reference data is input only and lives in
[`datasets/copycat-replication/original/`](../../datasets/copycat-replication/original/).
The snag-correlation analysis reads baseline runs from `replication/` and writes its
result to `snags/`.

Stage 20 also requires the baseline TV reference ranges from stage 15; rerun stage 15
when the baseline comparison changes. Use `--baseline-only` to generate only the baseline ranges.

Scripts beginning with `2` use previously generated tables to draw PNG figures saved in
[papers/copycat-replication/figures](../../papers/copycat-replication/figures/).

To run all experiment scripts, run:

``` bash
make all
```

For the baseline analysis, run:

``` bash
make baseline
```
