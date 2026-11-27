# Original Metacat

This package provides a Python interface to the original Scheme model.

## Installation

Install `uv` and make sure Docker is running and accessible to your user.
The package requires Python 3.13 or newer.

To build the image ahead of time, run `make build` from this directory.

Alternatively, install the Python package and check that the worker starts.

```sh
uv sync
uv run python - <<'PY'
from original_metacat import Metacat

with Metacat.start():
    print("Metacat worker is ready.")
PY
```

This builds the image using Docker's build cache and waits for
the worker to start. The example stops the worker when it exits.

[`archives.sha256`](archives.sha256) records the expected
SHA-256 checksums for the Chez Scheme, SWL, and Metacat source archives.
Docker downloads the archives and verifies their checksums before
unpacking them.

## How it works

```text
HOST MACHINE
  Python caller
    |  ^
    v  |  run_once(problem, seed) down / result up
  Metacat (metacat.py)
    |  ^
    |  |  JSON-wrapped Scheme request down / raw JSON reply up
----|--|-----------------------------------------------------------
    v  |  DOCKER CONTAINER
  __main__.py --worker (SWL process and pipes)
    |  ^
    v  |  Scheme request down / JSON reply up through a separate pipe
  SWL REPL (adapter.ss), running under Xvfb
    |  ^
    v  |  Reset and run down / final state and Temporal Trace up
  Original Metacat (Scheme)
```

## Python usage

`Metacat.start()` builds the image, starts the container and worker, and waits
until the model has finished setup.

Each `run_once()` call clears Episodic Memory and resets the model with the
next problem and seed.

`close()` closes the request stream and shuts down the worker.

Alternatively, use a context manager:

```python
from original_metacat import Metacat

with Metacat.start() as metacat:
    result = metacat.run_once("abc -> abd ==> ijk -> ?", 1)
```
