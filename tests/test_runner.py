from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

from tests import run


class ParallelRunnerTests(unittest.TestCase):
    def test_worker_count_defaults_to_eight_and_validates_overrides(self) -> None:
        self.assertEqual(run.resolve_worker_count(None, processor_count=8), 8)
        self.assertEqual(run.resolve_worker_count(None, processor_count=16), 8)
        self.assertEqual(run.resolve_worker_count(None, processor_count=32), 8)
        self.assertEqual(run.resolve_worker_count("1", processor_count=16), 1)
        self.assertEqual(run.resolve_worker_count("24", processor_count=16), 24)
        for value in ("0", "-1", "abc", "1.5"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                run.resolve_worker_count(value, processor_count=16)

    def test_discovers_supported_shards_once_in_deterministic_order(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            repository = Path(temporary)
            tests = repository / "tests"
            nested = tests / "nested"
            nested.mkdir(parents=True)
            for package in (tests, nested):
                (package / "__init__.py").write_text("", encoding="utf-8")
            for path in (
                tests / "test_beta.py",
                nested / "test_alpha.py",
                tests / "test_beta.ps1",
                nested / "test_alpha.ps1",
                nested / "helper.py",
            ):
                path.write_text("", encoding="utf-8")

            self.assertEqual(
                run.discover_python_test_modules(repository),
                ("tests.nested.test_alpha", "tests.test_beta"),
            )
            self.assertEqual(
                tuple(
                    path.relative_to(repository).as_posix()
                    for path in run.discover_powershell_tests(repository)
                ),
                ("tests/nested/test_alpha.ps1", "tests/test_beta.ps1"),
            )

    def test_process_shards_overlap_and_preserve_input_order(self) -> None:
        barrier = "\n".join(
            (
                "import sys, time",
                "from pathlib import Path",
                "root, name, expected = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])",
                "root.mkdir(parents=True, exist_ok=True)",
                "(root / f'{name}.ready').write_text('', encoding='utf-8')",
                "deadline = time.monotonic() + 5",
                "while len(tuple(root.glob('*.ready'))) < expected "
                "and time.monotonic() < deadline:",
                "    time.sleep(0.02)",
                "if len(tuple(root.glob('*.ready'))) < expected:",
                "    raise SystemExit(7)",
                "print(f'ready-{name}')",
            )
        )
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            marker_root = root / "markers"
            shards = tuple(
                run.ProcessShard(
                    name=name,
                    command=(
                        sys.executable,
                        "-B",
                        "-c",
                        barrier,
                        str(marker_root),
                        name,
                        "2",
                    ),
                )
                for name in ("second", "first")
            )
            results = run.run_process_shards(
                shards,
                worker_count=2,
                working_directory=root,
                temp_root=root / "temp",
            )

            self.assertEqual(tuple(result.name for result in results), ("second", "first"))
            self.assertEqual(tuple(result.returncode for result in results), (0, 0))
            self.assertIn("ready-second", results[0].output)
            self.assertIn("ready-first", results[1].output)

    def test_process_shards_capture_output_and_failure_codes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            shards = (
                run.ProcessShard(
                    name="passing",
                    command=(
                        sys.executable,
                        "-B",
                        "-c",
                        "import sys; print('pass-out'); print('pass-err', file=sys.stderr)",
                    ),
                ),
                run.ProcessShard(
                    name="failing",
                    command=(
                        sys.executable,
                        "-B",
                        "-c",
                        "import sys; print('fail-out'); "
                        "print('fail-err', file=sys.stderr); raise SystemExit(9)",
                    ),
                ),
            )
            results = run.run_process_shards(
                shards,
                worker_count=2,
                working_directory=root,
                temp_root=root / "temp",
            )

            self.assertEqual(tuple(result.returncode for result in results), (0, 9))
            self.assertIn("pass-out", results[0].output)
            self.assertIn("pass-err", results[0].output)
            self.assertIn("fail-out", results[1].output)
            self.assertIn("fail-err", results[1].output)


if __name__ == "__main__":
    unittest.main()
