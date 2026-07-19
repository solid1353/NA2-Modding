from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na2_patcher.build_preflight import (
    check_preflight,
    collect_build_state,
    patcher_tree_entry,
    state_fingerprint,
    write_receipt,
)


DEPENDENCIES = {
    "python_implementation": "test-python",
    "python_version": "1.0",
    "zlib_compile_version": "1.0",
    "zlib_runtime_version": "1.0",
    "zopfli_version": "0.4.3",
}


class BuildPreflightTests(unittest.TestCase):
    def create_workspace(self, root: Path) -> dict[str, Path]:
        workspace = root / "repository"
        patcher = workspace / "na2_patcher"
        profile = patcher / "profiles" / "current"
        profile.mkdir(parents=True)
        (patcher / "engine.py").write_text("ENGINE = 1\n", encoding="utf-8")
        (patcher / "schema.tsv").write_text("schema\t1\n", encoding="utf-8")
        (profile / "manifest.tsv").write_text(
            "key\tvalue\nschema_version\t1\nprofile_id\tcurrent\n",
            encoding="utf-8",
        )
        na2_iso = root / "source" / "NA2.iso"
        nun5_iso = root / "source" / "NUN5.iso"
        na2_iso.parent.mkdir()
        na2_iso.write_bytes(b"clean na2")
        nun5_iso.write_bytes(b"clean nun5")
        current_iso = workspace / "build" / "NA2.28 - Current.iso"
        current_iso.parent.mkdir()
        current_iso.write_bytes(b"verified current")
        return {
            "workspace": workspace,
            "patcher": patcher,
            "profile": profile,
            "na2_iso": na2_iso,
            "nun5_iso": nun5_iso,
            "current_iso": current_iso,
            "receipt": workspace / "logs" / "na2" / "preflight" / "current.json",
        }

    def state(self, paths: dict[str, Path], **overrides: object) -> dict[str, object]:
        arguments: dict[str, object] = {
            "workspace": paths["workspace"],
            "na2_iso": paths["na2_iso"],
            "nun5_iso": paths["nun5_iso"],
            "profile_directory": paths["profile"],
            "dependencies": DEPENDENCIES,
        }
        arguments.update(overrides)
        return collect_build_state(**arguments)  # type: ignore[arg-type]

    def check(self, paths: dict[str, Path]) -> dict[str, object]:
        return check_preflight(
            workspace=paths["workspace"],
            na2_iso=paths["na2_iso"],
            nun5_iso=paths["nun5_iso"],
            current_iso=paths["current_iso"],
            profile_directory=paths["profile"],
            receipt_path=paths["receipt"],
            dependencies=DEPENDENCIES,
        )

    def record(
        self,
        paths: dict[str, Path],
        expected_fingerprint: str,
    ) -> dict[str, object]:
        return write_receipt(
            workspace=paths["workspace"],
            na2_iso=paths["na2_iso"],
            nun5_iso=paths["nun5_iso"],
            current_iso=paths["current_iso"],
            profile_directory=paths["profile"],
            receipt_path=paths["receipt"],
            expected_fingerprint=expected_fingerprint,
            dependencies=DEPENDENCIES,
        )

    def test_fingerprint_is_deterministic_and_invalidates_every_declared_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = state_fingerprint(self.state(paths))
            self.assertEqual(initial, state_fingerprint(self.state(paths)))

            (paths["patcher"] / "engine.py").write_text(
                "ENGINE = 2\n", encoding="utf-8"
            )
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            (paths["patcher"] / "engine.py").write_text(
                "ENGINE = 1\n", encoding="utf-8"
            )

            paths["na2_iso"].write_bytes(b"changed na2")
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            paths["na2_iso"].write_bytes(b"clean na2")

            paths["nun5_iso"].write_bytes(b"changed nun5")
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            paths["nun5_iso"].write_bytes(b"clean nun5")

            changed_dependencies = dict(DEPENDENCIES, zlib_runtime_version="2.0")
            self.assertNotEqual(
                initial,
                state_fingerprint(
                    self.state(paths, dependencies=changed_dependencies)
                ),
            )

    def test_patcher_hash_covers_tests_and_docs_but_ignores_python_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = patcher_tree_entry(paths["patcher"])
            documentation = paths["patcher"] / "README.md"
            documentation.write_text("documentation\n", encoding="utf-8")
            with_documentation = patcher_tree_entry(paths["patcher"])
            self.assertNotEqual(initial["sha256"], with_documentation["sha256"])

            cache = paths["patcher"] / "__pycache__"
            cache.mkdir()
            (cache / "engine.cpython-999.pyc").write_bytes(b"generated")
            self.assertEqual(
                with_documentation["sha256"],
                patcher_tree_entry(paths["patcher"])["sha256"],
            )

    def test_receipt_hit_requires_matching_fingerprint_and_current_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            self.assertEqual(self.check(paths)["reason"], "receipt-missing")
            written = self.record(paths, fingerprint)
            self.assertEqual(written["status"], "written")
            self.assertEqual(self.check(paths)["status"], "hit")

            original = paths["current_iso"].read_bytes()
            paths["current_iso"].write_bytes(b"X" * len(original))
            self.assertEqual(self.check(paths)["reason"], "current-iso-hash-mismatch")
            paths["current_iso"].write_bytes(original)

            paths["patcher"].joinpath("engine.py").write_text(
                "ENGINE = 3\n", encoding="utf-8"
            )
            self.assertEqual(self.check(paths)["reason"], "fingerprint-mismatch")

    def test_missing_corrupt_and_tampered_receipts_are_safe_misses(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            self.record(paths, fingerprint)

            paths["receipt"].write_text("not json\n", encoding="utf-8")
            self.assertEqual(self.check(paths)["reason"], "receipt-invalid")

            self.record(paths, fingerprint)
            receipt = json.loads(paths["receipt"].read_text(encoding="utf-8"))
            receipt["state"]["profile"] = "profiles/tampered"
            paths["receipt"].write_text(json.dumps(receipt), encoding="utf-8")
            self.assertEqual(self.check(paths)["reason"], "receipt-invalid")

            paths["receipt"].unlink()
            self.assertEqual(self.check(paths)["reason"], "receipt-missing")

    def test_receipt_is_not_written_if_inputs_change_during_build(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            paths["patcher"].joinpath("engine.py").write_text(
                "ENGINE = 4\n", encoding="utf-8"
            )
            result = self.record(paths, fingerprint)
            self.assertEqual(result["reason"], "inputs-changed-during-build")
            self.assertFalse(paths["receipt"].exists())

    def test_receipt_contains_no_machine_specific_absolute_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            self.record(paths, fingerprint)
            text = paths["receipt"].read_text(encoding="utf-8")
            self.assertNotIn(str(paths["workspace"]), text)
            self.assertIn('"profile": "profiles/current"', text)


if __name__ == "__main__":
    unittest.main()
