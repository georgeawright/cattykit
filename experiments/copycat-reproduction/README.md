# Reproduction Experiments for Copycat

This directory contains scripts for running experiments and generating tables and figures
as part of a reproduction study of the model Copycat. The scripts go hand in had with data
stored in [datasets/copycat-reproduction](../../datasets/copycat-reproduction/) and output
artefacts in [papers/copycat-reproduction](../../papers/copycat-reproduction/).

## Running the scripts

Scripts produce outputs which are consumed by subsequent scripts according to the dependency graph:

```text
00_run_baseline.py ─────> 10_analyse_baseline.py ─────> 21_plot_basic_problems.py
  │
  │
  └──> 01_run_removal_methods.py ──> 11_analyse_removal_methods.py
```

Scripts beginning with `0` run Copycat or altered versions of Copycat and generate raw CSV outputs
saved in [datasets/copycat-reproduction](../../datasets/copycat-reproduction/).

Scripts beginning with `1` use these CSV files to generate tables of summary statistics saved in
[datasets/copycat-reproduction](../../datasets/copycat-reproduction/) and
[papers/copycat-reproduction/tables](../../papers/copycat-reproduction/tables/).

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
