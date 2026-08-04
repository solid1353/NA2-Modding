from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from na228_builder.build_preflight import (
    check_preflight,
    collect_build_state,
    builder_tree_entry,
    state_fingerprint,
    write_receipt,
)
from na228_builder.profile import feature_content_sha256


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
        builder = workspace / "na228_builder"
        profile = builder / "profiles" / "default.tsv"
        profile.parent.mkdir(parents=True)
        (builder / "engine.py").write_text("ENGINE = 1\n", encoding="utf-8")
        (builder / "schema.tsv").write_text("schema\t1\n", encoding="utf-8")
        feature = builder / "features" / "feature"
        module = feature / "string_patcher"
        module.mkdir(parents=True)
        (feature / "README.md").write_text("# Feature\n", encoding="utf-8")
        (module / "strings.tsv").write_text("string_id\n", encoding="utf-8")
        source_roots = workspace / "source_roots"
        source_roots.mkdir(parents=True)
        (source_roots / "NA2.iso.files").mkdir()
        (source_roots / "NUN5.iso.files").mkdir()
        shared = workspace / "shared"
        for name in (
            "cheats",
            "game_settings",
            "input_profiles",
            "memory_cards",
        ):
            (shared / name).mkdir(parents=True)
        (workspace / "build").mkdir()
        (workspace / "paths.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "roots": {
                        "repository": ".",
                        "builder": "na228_builder",
                        "features": "@builder/features",
                        "source": "source_roots",
                        "build": "build",
                        "pcsx2_cheats": "shared/cheats",
                        "pcsx2_game_settings": "shared/game_settings",
                        "pcsx2_input_profiles": "shared/input_profiles",
                        "pcsx2_memory_cards": "shared/memory_cards",
                    },
                    "files": {
                        "product_config": "@repository/product.json",
                        "game_catalog": "@repository/games.json",
                    },
                }
            ),
            encoding="utf-8",
        )
        (workspace / "games.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "sources": {
                        "NA2": {"serial": "SLPS-25837", "crc": "C0659AD1"},
                        "NUN5": {"serial": "SLES-55605", "crc": "C071D4C1"},
                    },
                }
            ),
            encoding="utf-8",
        )
        (workspace / "product.json").write_text(
            json.dumps(
                {
                    "schema_version": 1,
                    "title": "Test Product",
                    "serial": "TEST-00000",
                    "inputs": {"na2": "@source_na2", "nun5": "@source_nun5"},
                    "identity": {
                        "image": {
                            "source_boot_path": "SLPS_258.37",
                            "output_boot_path": "SLOP_NA2.28",
                            "system_cnf_path": "SYSTEM.CNF",
                        },
                        "memory_card": {
                            "title_offset": 4,
                            "title_capacity": 16,
                            "title_encoding": "ascii",
                            "source_title": "Original",
                            "output_title": "Output",
                        },
                        "game_title": {
                            "imported": "Imported",
                            "output": "Output",
                            "expected_mapping_count": 1,
                            "expected_occurrence_count": 1,
                        },
                    },
                    "builds": {"latest": {"postfix": "Latest"}},
                }
            ),
            encoding="utf-8",
        )
        profile.write_text(
            "feature_id\tenabled\texpected_sha256\tbypass_check\n"
            "feature\t1\t" + feature_content_sha256(feature) + "\t1\n",
            encoding="utf-8",
        )
        na2_iso = root / "source" / "NA2.iso"
        nun5_iso = root / "source" / "NUN5.iso"
        na2_iso.parent.mkdir()
        na2_iso.write_bytes(b"clean na2")
        nun5_iso.write_bytes(b"clean nun5")
        latest_iso = workspace / "build" / "NA2.28 - Latest.iso"
        latest_iso.parent.mkdir(exist_ok=True)
        latest_iso.write_bytes(b"verified latest")
        return {
            "workspace": workspace,
            "builder": builder,
            "profile": profile,
            "na2_iso": na2_iso,
            "nun5_iso": nun5_iso,
            "latest_iso": latest_iso,
            "receipt": workspace / "logs" / "na228" / "preflight" / "latest.json",
        }

    def state(self, paths: dict[str, Path], **overrides: object) -> dict[str, object]:
        arguments: dict[str, object] = {
            "workspace": paths["workspace"],
            "na2_iso": paths["na2_iso"],
            "nun5_iso": paths["nun5_iso"],
            "profile_path": paths["profile"],
            "dependencies": DEPENDENCIES,
        }
        arguments.update(overrides)
        return collect_build_state(**arguments)  # type: ignore[arg-type]

    def check(self, paths: dict[str, Path]) -> dict[str, object]:
        return check_preflight(
            workspace=paths["workspace"],
            na2_iso=paths["na2_iso"],
            nun5_iso=paths["nun5_iso"],
            output_iso=paths["latest_iso"],
            profile_path=paths["profile"],
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
            output_iso=paths["latest_iso"],
            profile_path=paths["profile"],
            receipt_path=paths["receipt"],
            expected_fingerprint=expected_fingerprint,
            dependencies=DEPENDENCIES,
        )

    def test_fingerprint_is_deterministic_and_invalidates_every_declared_input(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = state_fingerprint(self.state(paths))
            self.assertEqual(initial, state_fingerprint(self.state(paths)))

            self.assertNotEqual(
                initial,
                state_fingerprint(self.state(paths, payload_shift=32)),
            )
            (paths["builder"] / "engine.py").write_text(
                "ENGINE = 2\n", encoding="utf-8"
            )
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))
            (paths["builder"] / "engine.py").write_text(
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

    def test_builder_hash_excludes_non_composing_files_and_python_cache(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = builder_tree_entry(paths["builder"])
            documentation = paths["builder"] / "README.md"
            documentation.write_text("documentation\n", encoding="utf-8")
            with_documentation = builder_tree_entry(paths["builder"])
            self.assertEqual(initial["sha256"], with_documentation["sha256"])

            (paths["builder"] / "release_runtime.py").write_text(
                "RELEASE_ONLY = True\n", encoding="utf-8"
            )
            self.assertEqual(
                with_documentation["sha256"],
                builder_tree_entry(paths["builder"])["sha256"],
            )

            cache = paths["builder"] / "__pycache__"
            cache.mkdir()
            (cache / "engine.cpython-999.pyc").write_bytes(b"generated")
            self.assertEqual(
                with_documentation["sha256"],
                builder_tree_entry(paths["builder"])["sha256"],
            )

    def test_profile_resources_invalidate_but_documentation_content_does_not(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = state_fingerprint(self.state(paths))
            feature = paths["builder"] / "features" / "feature"

            (feature / "README.md").write_text(
                "# Updated documentation only\n", encoding="utf-8"
            )
            self.assertEqual(initial, state_fingerprint(self.state(paths)))

            (feature / "string_patcher" / "strings.tsv").write_text(
                "string_id\nchanged\n", encoding="utf-8"
            )
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))

    def test_product_configuration_invalidates_fingerprint(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            initial = state_fingerprint(self.state(paths))
            product = paths["workspace"] / "product.json"
            document = json.loads(product.read_text(encoding="utf-8"))
            document["title"] = "Changed Product"
            product.write_text(json.dumps(document), encoding="utf-8")
            self.assertNotEqual(initial, state_fingerprint(self.state(paths)))

    def test_receipt_hit_requires_matching_fingerprint_and_output_hash(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            paths = self.create_workspace(Path(directory))
            fingerprint = state_fingerprint(self.state(paths))
            self.assertEqual(self.check(paths)["reason"], "receipt-missing")
            written = self.record(paths, fingerprint)
            self.assertEqual(written["status"], "written")
            self.assertEqual(self.check(paths)["status"], "hit")

            original = paths["latest_iso"].read_bytes()
            paths["latest_iso"].write_bytes(b"X" * len(original))
            self.assertEqual(self.check(paths)["reason"], "output-iso-hash-mismatch")
            paths["latest_iso"].write_bytes(original)

            paths["builder"].joinpath("engine.py").write_text(
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
            paths["builder"].joinpath("engine.py").write_text(
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
            self.assertIn('"profile": "profiles/default.tsv"', text)


if __name__ == "__main__":
    unittest.main()
