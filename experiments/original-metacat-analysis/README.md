# Original Metacat Analysis

Run James B. Marshall’s Metacat 1.2 in Docker with its original Scheme source.
The image uses Chez Scheme 9.5.4, the author’s patched Linux SWL 1.3, and
Tcl/Tk 8.6. The snapshot of installed Debian package versions for each build
stage is stored in `/opt/metacat-batch/{build,runtime}-packages.txt`.
The base image digest is in the package [Dockerfile](original_metacat/Dockerfile),
and upstream downloads are verified against
[archives.sha256](original_metacat/archives.sha256). [Upstream Metacat
instructions](https://science.slc.edu/~jmarshall/metacat/)

## Build and run

To build the image manually, run this from the repository root. For Python
usage, `Metacat.start()` builds the image automatically.

```sh
make -C experiments/original-metacat-analysis/original_metacat build
```

To transfer the image to another machine, use
`docker save -o original-metacat-1.2.tar original-metacat:1.2` and then
`docker load -i original-metacat-1.2.tar` on the destination machine.

### Single trial

The container accepts the initial, modified, and target strings followed by
the seed. It prints one JSON object with `answer`, `temperature`,
`codelets_run`, `snag_count`, and an `error` field that is null on success.

```sh
docker run --rm --platform linux/amd64 original-metacat:1.2 abc abd ijk 1
```

The entry point uses the [`original_metacat` package](original_metacat) to
prepare the trial and send it to SWL. Each trial stops at the
first answer, when Metacat gives up, or after 100,000 codelets. Chez Scheme 9.5.4
accepts integer RNG seeds from `1` through `4294967295`.

### Bulk experiment

Run the numbered script with `uv`.

```sh
cd experiments/original-metacat-analysis
uv sync --locked
uv run 00_run_metacat_with_copycat_inputs.py
```

The script calls `Metacat.start()` once to build the Docker image and start a
container with one SWL worker. It calls `run_once` for each pending trial and
automatically closes the worker when the batch ends or is interrupted. The script reads
all 29 Copycat problems from [original-copycat-problems.json](../../datasets/original-metacat-analysis/original-copycat-problems.json)
and passes each problem string directly to `Metacat.run_once`.
It uses seeds **1 through 10** and a limit of **100,000 codelets per trial**,
both set in the script, for a total of 290 trials. It writes
`datasets/original-metacat-analysis/original_metacat_raw_results.csv`.
It uses the columns from the [Copycat raw results CSV](../../datasets/copycat-replication/replication/reproduction_raw_results.csv)
and adds `error` as the final column. Scheme errors during a trial are returned
in that column, along with any codelet count and temperature the model reported.
Docker, worker, and communication failures raise an exception and stop the
batch; after fixing the underlying issue, rerun to resume. Unavailable
measurements for a Scheme error are blank.
Temperature is a proportion
from 0 to 1. When a trial reaches the limit or gives up, its `answer` is blank
and its temperature is the workspace temperature at the stop. The count
includes the codelet that finds the answer or gives up.

The script appends and flushes each trial row as it finishes. To resume, run
the same command again. It skips problem–seed pairs with a complete row,
including rows with a recorded Scheme error. Pass `--overwrite` to clear the CSV
and rerun every trial.
If the worker itself exits, the batch stops and can be resumed with a new
worker.

Use the same lifecycle for Python callers.

```python
from original_metacat import Metacat

with Metacat.start() as metacat:
    result = metacat.run_once("abc -> abd ==> ijk -> ?", 1)
```

The single-trial Docker command accepts `--codelet-limit` and `--timeout`
to override the codelet limit or set a wall-clock timeout in seconds.

## How the worker runs

The image generates a configured loader outside the unpacked Metacat source.
The [SWL patch](original_metacat/swl-repl-load.patch) adds a command-line option
that loads the adapter in the SWL REPL thread. The runner starts SWL under
`xvfb-run -a`.
The adapter calls `setup` once per worker. For each request it clears
Episodic Memory, resets the problem and seed, and uses a temporary
`reset-handler` to return from a normal Metacat stop.
It reads the first answer and its temperature from the Temporal Trace and
counts all `snag` events.

For a GUI comparison using this image's runtime, start SWL with the
configured loader and call `(setup)` in the REPL. Start from empty Episodic
Memory and enter `abc abd ijk 1` in the control panel. Compare the first
answer, its trace temperature, the codelet count, and the trace snag count
with the corresponding batch record. Historical CSV rows labeled with seed
`0` used `4294967295` in Chez Scheme.

The GUI and batch checks for `abc abd ijk 1` both returned `ijd` after 396
codelets with zero snags. The GUI showed temperature 21, which is 0.21 in the
CSV. A one-codelet limit produced a blank answer in the CSV.
