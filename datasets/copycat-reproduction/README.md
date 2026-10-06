# Copycat reproduction data

`original_copycat_results.template.json` defines the reference-data format used
by the Copycat reproduction tests. It lists every problem and the book page on
which its reported solutions appear, but in order to avoid copyright infringement,
contains no numerical results.

## Recreate the local dataset

The source is:

> Mitchell, M. (1993). *Analogy-Making as Perception: A Computer Model*.
> MIT Press. https://doi.org/10.5555/152203

1. Obtain lawful access to the source.
2. Copy `original_copycat_results.template.json` to
   `original_copycat_results.json`.
3. For each problem, transcribe the labelled values on its `source.page` into
   `solutions` and `codelets`.

The local dataset is ignored by Git. The test fixture looks for it at that
default path, or at the path supplied in `COPYCAT_GOLD_DATA_PATH`.

## Generated reproduction outputs

The reproduction script writes complete per-problem outputs here:

- `reproduction_copycat_results.json` contains the summarized reproduction
  results.
- `reproduction_raw_results.csv` contains every run and its seed, answer,
  temperature, and codelets-run count.
- `reproduction_comparison.csv` contains all 29 per-problem comparison
  statistics.
- `reproduction_comparison_error_summary.csv` summarizes the comparison-error
  distributions.

For example:

```sh
cd models/copycat
COPYCAT_GOLD_DATA_PATH=/path/to/original_copycat_results.json \
  uv run python -m pytest tests/reproduction --basic
```

## Data format

Each problem has a stable string `id`, mirroring Mitchell's grouping of
problems into five targets and their variants.
Each `solutions` key is a reported answer string. Its value contains its
`frequency`, `temperature_mean`, and `temperature_standard_error`. `codelets`
contains the reported `mean` and `standard_error` for the problem.

Temperatures are reported in the source as integer percentages from 0 to 100.
Store them as decimal proportions from 0 to 1:

```text
stored_value = source_value / 100
```

This allows direct comparison with this repositories Python re-implementation
which uses floating point numbers for temperature and other values.
