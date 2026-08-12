from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import tempfile
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass
from pathlib import Path
from typing import Sequence


REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_MAX_WORKERS = 8
WORKER_ENVIRONMENT = "NA228_TEST_WORKERS"
POWERSHELL_ENVIRONMENT = "NA228_TEST_POWERSHELL"
UNITTEST_COUNT = re.compile(r"Ran (\d+) tests? in [0-9.]+s")


@dataclass(frozen=True)
class ProcessShard:
    name: str
    command: tuple[str, ...]


@dataclass(frozen=True)
class ProcessResult:
    name: str
    returncode: int
    output: str
    duration_seconds: float


def resolve_worker_count(
    value: str | None,
    processor_count: int | None = None,
) -> int:
    if value is not None and value.strip():
        try:
            workers = int(value)
        except ValueError as error:
            raise ValueError(
                f"{WORKER_ENVIRONMENT} must be a positive integer; got {value!r}"
            ) from error
        if workers < 1:
            raise ValueError(
                f"{WORKER_ENVIRONMENT} must be a positive integer; got {value!r}"
            )
        return workers

    available = os.cpu_count() if processor_count is None else processor_count
    return max(1, min(DEFAULT_MAX_WORKERS, available or 1))


def _is_importable_test(path: Path, repository: Path) -> bool:
    relative = path.relative_to(repository)
    current = repository
    for part in relative.parts[:-1]:
        current /= part
        if not (current / "__init__.py").is_file():
            return False
    return True


def discover_python_test_modules(repository: Path = REPOSITORY) -> tuple[str, ...]:
    tests = repository / "tests"
    modules = {
        ".".join(path.relative_to(repository).with_suffix("").parts)
        for path in tests.rglob("test_*.py")
        if _is_importable_test(path, repository)
    }
    return tuple(sorted(modules))


def discover_powershell_tests(repository: Path = REPOSITORY) -> tuple[Path, ...]:
    tests = repository / "tests"
    return tuple(
        sorted(
            tests.rglob("test_*.ps1"),
            key=lambda path: path.relative_to(repository).as_posix(),
        )
    )


def _terminate_process_tree(process: subprocess.Popen[str]) -> None:
    if process.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
                timeout=5,
            )
        else:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
    except (OSError, subprocess.SubprocessError):
        process.kill()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def run_process_shards(
    shards: Sequence[ProcessShard],
    *,
    worker_count: int,
    working_directory: Path,
    temp_root: Path,
) -> tuple[ProcessResult, ...]:
    if worker_count < 1:
        raise ValueError("worker_count must be positive")
    if not shards:
        return ()

    temp_root.mkdir(parents=True, exist_ok=True)
    active: set[subprocess.Popen[str]] = set()
    active_lock = threading.Lock()
    results: list[ProcessResult | None] = [None] * len(shards)

    def execute(shard: ProcessShard) -> ProcessResult:
        environment = os.environ.copy()
        environment["TEMP"] = str(temp_root)
        environment["TMP"] = str(temp_root)
        environment["PYTHONDONTWRITEBYTECODE"] = "1"
        process_options: dict[str, object] = {}
        if os.name == "nt":
            process_options["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP
        else:
            process_options["start_new_session"] = True

        started = time.perf_counter()
        process = subprocess.Popen(
            shard.command,
            cwd=working_directory,
            env=environment,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            encoding="utf-8",
            errors="replace",
            **process_options,
        )
        with active_lock:
            active.add(process)
        try:
            output, _ = process.communicate()
        finally:
            with active_lock:
                active.discard(process)
        return ProcessResult(
            name=shard.name,
            returncode=process.returncode,
            output=output,
            duration_seconds=time.perf_counter() - started,
        )

    executor = ThreadPoolExecutor(max_workers=min(worker_count, len(shards)))
    futures: dict[Future[ProcessResult], int] = {
        executor.submit(execute, shard): index
        for index, shard in enumerate(shards)
    }
    try:
        for future in as_completed(futures):
            results[futures[future]] = future.result()
    except BaseException:
        with active_lock:
            processes = tuple(active)
        for process in processes:
            _terminate_process_tree(process)
        for future in futures:
            future.cancel()
        executor.shutdown(wait=True, cancel_futures=True)
        raise
    else:
        executor.shutdown(wait=True)

    completed = tuple(result for result in results if result is not None)
    if len(completed) != len(shards):
        raise RuntimeError("A test shard completed without a result")
    return completed


def _print_results(label: str, results: Sequence[ProcessResult]) -> None:
    stream = sys.stdout
    for result in results:
        outcome = "passed" if result.returncode == 0 else f"failed: {result.returncode}"
        print(
            f"[{label}] {result.name} ({outcome}, {result.duration_seconds:.2f}s)",
            file=stream,
        )
        if result.output:
            stream.write(result.output)
            if not result.output.endswith("\n"):
                stream.write("\n")
    stream.flush()


def _failed_names(results: Sequence[ProcessResult]) -> tuple[str, ...]:
    return tuple(result.name for result in results if result.returncode != 0)


def _python_test_count(results: Sequence[ProcessResult]) -> int:
    total = 0
    for result in results:
        matches = UNITTEST_COUNT.findall(result.output)
        if matches:
            total += int(matches[-1])
    return total


def _run_phase(
    label: str,
    shards: Sequence[ProcessShard],
    *,
    worker_count: int,
    temp_root: Path,
) -> tuple[ProcessResult, ...]:
    active_workers = min(worker_count, len(shards)) if shards else 0
    print(
        f"[tests] {label}: {len(shards)} shards with {active_workers} workers.",
        flush=True,
    )
    results = run_process_shards(
        shards,
        worker_count=worker_count,
        working_directory=REPOSITORY,
        temp_root=temp_root,
    )
    _print_results(label.casefold(), results)
    return results


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--powershell")
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    try:
        worker_count = resolve_worker_count(os.environ.get(WORKER_ENVIRONMENT))
    except ValueError as error:
        print(f"Test runner configuration error: {error}", file=sys.stderr)
        return 2
    powershell = args.powershell or os.environ.get(POWERSHELL_ENVIRONMENT)
    if not powershell:
        print(
            f"Test runner configuration error: {POWERSHELL_ENVIRONMENT} is unset",
            file=sys.stderr,
        )
        return 2

    temp_parent = Path(os.environ.get("TEMP") or tempfile.gettempdir())
    python_modules = discover_python_test_modules()
    python_shards = tuple(
        ProcessShard(
            name=module,
            command=(sys.executable, "-B", "-m", "unittest", module),
        )
        for module in python_modules
    )
    try:
        python_results = _run_phase(
            "Python",
            python_shards,
            worker_count=worker_count,
            temp_root=temp_parent,
        )
    except KeyboardInterrupt:
        print("Unit-test run interrupted.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError) as error:
        print(f"Python test runner failed: {error}", file=sys.stderr)
        return 2

    python_failures = _failed_names(python_results)
    if python_failures:
        print(
            "Python tests failed: " + ", ".join(python_failures),
            file=sys.stderr,
        )
        return 1
    print(
        f"[tests] Python passed: {len(python_results)} modules, "
        f"{_python_test_count(python_results)} tests.",
        flush=True,
    )

    powershell_paths = discover_powershell_tests()
    powershell_shards = tuple(
        ProcessShard(
            name=path.relative_to(REPOSITORY).as_posix(),
            command=(powershell, "-NoProfile", "-NonInteractive", "-File", str(path)),
        )
        for path in powershell_paths
    )
    try:
        powershell_results = _run_phase(
            "PowerShell",
            powershell_shards,
            worker_count=worker_count,
            temp_root=temp_parent,
        )
    except KeyboardInterrupt:
        print("Unit-test run interrupted.", file=sys.stderr)
        return 130
    except (OSError, RuntimeError) as error:
        print(f"PowerShell test runner failed: {error}", file=sys.stderr)
        return 2

    powershell_failures = _failed_names(powershell_results)
    if powershell_failures:
        print(
            "PowerShell tests failed: " + ", ".join(powershell_failures),
            file=sys.stderr,
        )
        return 1
    print(
        f"[tests] PowerShell passed: {len(powershell_results)} scripts.",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
