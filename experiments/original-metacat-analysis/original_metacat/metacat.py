"""Call the original Metacat runtime from the host through Docker."""

import json
import re
import select
import subprocess
from contextlib import suppress
from dataclasses import dataclass
from pathlib import Path
from typing import Self
from uuid import uuid4

IMAGE = "original-metacat:1.2"
BUILD_CONTEXT = Path(__file__).resolve().parent
_DEFAULT_CODELET_LIMIT = 100_000
_MAX_SEED = 2**32 - 1


def _read_reply(stream, timeout=None):
    if not select.select([stream], [], [], timeout)[0]:
        raise TimeoutError("Timed out waiting for the Metacat worker")
    if not (reply := stream.readline()):
        raise RuntimeError("Metacat worker exited before sending a reply")
    try:
        return json.loads(reply)
    except json.JSONDecodeError as exc:
        raise RuntimeError("Metacat worker sent an invalid reply") from exc


@dataclass(frozen=True)
class _RunResult:
    """One trial's measurements, with temperature on the 0–1 scale."""

    answer: str | None
    temperature: float | None
    codelets_run: int | None
    snag_count: int | None
    error: str | None = None


def _trial_request(problem: tuple[str, str, str], random_seed: int, limit: int) -> str:
    if not all(
        isinstance(word, str) and re.fullmatch("[a-z]+", word) for word in problem
    ):
        raise ValueError(f"Expected three lowercase letter strings, got {problem!r}")
    if type(random_seed) is not int or not 1 <= random_seed <= _MAX_SEED:
        raise ValueError(f"seed must be an integer between 1 and {_MAX_SEED}")
    if type(limit) is not int or limit < 1:
        raise ValueError("codelet limit must be a positive integer")

    initial, modified, target = problem
    return f"({initial} {modified} {target} {random_seed} {limit})"


def _trial_result(reply: dict) -> _RunResult:
    temperature = reply["final_temperature"]
    return _RunResult(
        answer=reply["answer"],
        temperature=temperature / 100 if temperature is not None else None,
        codelets_run=reply["codelets_run"],
        snag_count=reply["snags"],
        error=reply["error"],
    )


class Metacat:
    """Run successive trials through one container and SWL worker."""

    def __init__(
        self, codelet_limit: int | None = None, timeout: int | None = None
    ) -> None:
        self.codelet_limit = (
            _DEFAULT_CODELET_LIMIT if codelet_limit is None else codelet_limit
        )
        self.timeout = timeout
        self._container = None

    @classmethod
    def start(
        cls, codelet_limit: int | None = None, timeout: int | None = None
    ) -> Self:
        """Build the image, start the worker, and return a running client."""
        metacat = cls(codelet_limit=codelet_limit, timeout=timeout)
        metacat._start()
        return metacat

    def _start(self) -> None:
        subprocess.run(
            [
                "docker",
                "build",
                "--platform",
                "linux/amd64",
                "-t",
                IMAGE,
                str(BUILD_CONTEXT),
            ],
            check=True,
        )
        self._name = f"original-metacat-{uuid4().hex}"
        command = [
            "docker",
            "run",
            "--rm",
            "-i",
            "--pull",
            "never",
            "--platform",
            "linux/amd64",
            "--name",
            self._name,
            IMAGE,
            "--worker",
        ]
        if self.timeout is not None:
            command.extend(["--timeout", str(self.timeout)])
        self._container = subprocess.Popen(
            command,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            encoding="utf-8",
            start_new_session=True,
        )
        try:
            if not _read_reply(self._container.stdout, timeout=150).get("ready"):
                raise RuntimeError("Metacat container did not start its worker")
        except BaseException:
            self.close()
            raise

    def __enter__(self) -> Self:
        if self._container is None:
            raise RuntimeError("Use Metacat.start() to create a running client")
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def close(self) -> None:
        """Stop the worker and remove the container."""
        container, self._container = self._container, None
        if container is None:
            return
        with container:
            with suppress(BrokenPipeError):
                container.stdin.close()
            try:
                container.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # A trial may still be running when the caller is interrupted.
                with suppress(subprocess.TimeoutExpired):
                    subprocess.run(
                        ["docker", "rm", "-f", self._name],
                        stdout=subprocess.DEVNULL,
                        check=False,
                        timeout=10,
                    )
                try:
                    container.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    container.kill()

    def run_once(self, problem: str, random_seed: int) -> _RunResult:
        """Run a problem written as `initial -> modified ==> target -> ?`."""
        container = self._container
        if container is None:
            raise RuntimeError("Use Metacat.start() before running a trial")
        source, question = problem.split(" ==> ")
        initial, modified = source.split(" -> ")
        target = question.removesuffix(" -> ?")

        request = _trial_request(
            (initial, modified, target), random_seed, self.codelet_limit
        )
        container.stdin.write(json.dumps(request) + "\n")
        container.stdin.flush()
        return _trial_result(_read_reply(container.stdout))
