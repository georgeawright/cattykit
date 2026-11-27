"""Run one original Metacat trial and print its result as JSON."""

import argparse
import json
import os
import signal
import subprocess
import sys
from contextlib import contextmanager, suppress
from dataclasses import asdict
from pathlib import Path
from tempfile import TemporaryDirectory

from .metacat import _DEFAULT_CODELET_LIMIT, _read_reply, _trial_request, _trial_result

HERE = Path(__file__).resolve().parent


@contextmanager
def _swl_session():
    with TemporaryDirectory(prefix="metacat-") as temp_dir:
        # SWL uses stdout for startup messages. Give the adapter a separate pipe.
        read_fd, write_fd = os.pipe()
        with os.fdopen(read_fd, encoding="utf-8") as responses:
            environment = dict(
                os.environ,
                SWL_PREFS_DIR=temp_dir,
                XDG_CACHE_HOME=temp_dir,
                METACAT_REQUESTS="/proc/self/fd/0",
                METACAT_RESPONSES=f"/proc/self/fd/{write_fd}",
            )
            try:
                worker = subprocess.Popen(
                    [
                        "xvfb-run",
                        "-a",
                        "-e",
                        "/dev/stderr",
                        "swl",
                        "--repl-load",
                        str(HERE / "adapter.ss"),
                    ],
                    cwd=HERE,
                    env=environment,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.DEVNULL,
                    encoding="utf-8",
                    pass_fds=(write_fd,),
                    start_new_session=True,
                )
            finally:
                os.close(write_fd)
            with worker:
                try:
                    ready = _read_reply(responses, timeout=120)
                    if not ready.get("ready"):
                        raise RuntimeError(ready.get("error") or "SWL did not start")
                    yield worker.stdin, responses
                finally:
                    with suppress(BrokenPipeError):
                        worker.stdin.close()
                    try:
                        worker.wait(timeout=5)
                    except subprocess.TimeoutExpired:
                        with suppress(ProcessLookupError):
                            os.killpg(worker.pid, signal.SIGKILL)


def _send_request(requests, responses, request: str, timeout: int | None = None):
    """Send a prepared Scheme request and return the adapter's reply."""
    requests.write(request + "\n")
    requests.flush()
    return _read_reply(responses, timeout=timeout)


def serve(timeout: int | None) -> None:
    with _swl_session() as (requests, responses):
        print(json.dumps({"ready": True}), flush=True)
        for line in sys.stdin:
            request = json.loads(line)
            reply = _send_request(requests, responses, request, timeout)
            print(json.dumps(reply), flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("initial", nargs="?")
    parser.add_argument("modified", nargs="?")
    parser.add_argument("target", nargs="?")
    parser.add_argument("random_seed", nargs="?", type=int)
    parser.add_argument(
        "--worker", action="store_true", help="Serve trial requests on stdin"
    )
    parser.add_argument("--codelet-limit", type=int, default=_DEFAULT_CODELET_LIMIT)
    parser.add_argument("--timeout", type=int, help="Worker timeout in seconds")
    args = parser.parse_args()
    if not args.worker and None in (
        args.initial,
        args.modified,
        args.target,
        args.random_seed,
    ):
        parser.error(
            "provide the initial, modified, and target strings and random seed"
        )

    try:
        if args.timeout is not None and args.timeout < 1:
            raise ValueError("timeout must be positive")
        if args.worker:
            serve(args.timeout)
            return
        request = _trial_request(
            (args.initial, args.modified, args.target),
            args.random_seed,
            args.codelet_limit,
        )
        with _swl_session() as (requests, responses):
            reply = _send_request(requests, responses, request, args.timeout)
        result = _trial_result(reply)
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError) as exc:
        parser.exit(1, f"{exc}\n")
    print(json.dumps(asdict(result)))
    if result.error is not None:
        parser.exit(1)


if __name__ == "__main__":
    main()
