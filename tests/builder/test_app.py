from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from na228_builder.scripts.app import (
    ReleaseError,
    ReleaseManifest,
    SupportedImage,
    _runtime_configuration_validator,
    application_directory,
    identify_supported_images,
    main,
    parse_release_manifest,
    run_release,
)


class ReleaseAppTests(unittest.TestCase):
    def image(self, image_id: str, label: str, data: bytes) -> SupportedImage:
        return SupportedImage(
            image_id,
            label,
            len(data),
            hashlib.sha256(data).hexdigest().upper(),
        )

    def manifest(self, na2: bytes, nun5: bytes) -> ReleaseManifest:
        return ReleaseManifest(
            schema_version=1,
            product_name="Narutimate Accel v2.28",
            product_version="v-test",
            executable_name="Narutimate Accel v2.28_test.exe",
            output_name="Narutimate Accel v2.28.iso",
            configuration="na228_builder/configurations/release.json",
            configuration_name="config.json",
            images=(
                self.image("na2", "original NA2 ISO", na2),
                self.image("nun5", "original NUN5 ISO", nun5),
            ),
        )

    def write_configuration(self, root: Path, value: object | None = None) -> Path:
        path = root / "config.json"
        path.write_text(json.dumps({} if value is None else value), encoding="utf-8")
        return path

    def test_release_toolchain_references_live_inputs(self) -> None:
        repository = Path(__file__).resolve().parents[2]
        toolchain = json.loads(
            (repository / "scripts" / "release" / "toolchain.json").read_text(
                encoding="utf-8"
            )
        )
        for field in (
            "requirements",
            "entry_point",
            "release_manifest",
            "icon",
            "instructions",
        ):
            with self.subTest(field=field):
                self.assertTrue((repository / toolchain[field]).is_file())

        manifest = json.loads(
            (repository / toolchain["release_manifest"]).read_text(encoding="utf-8")
        )
        self.assertTrue((repository / manifest["configuration"]).is_file())

    def test_application_directory_uses_explicit_executable_parent(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            executable = Path(directory) / "folder" / "Narutimate Accel v2.28.exe"
            self.assertEqual(
                application_directory(executable=executable),
                executable.resolve().parent,
            )

    def test_manifest_parser_normalizes_and_validates_image_identities(self) -> None:
        data = {
            "schema_version": 1,
            "product_name": "Narutimate Accel v2.28",
            "product_version": "1.0.0",
            "executable_name": "Narutimate Accel v2.28.exe",
            "output_name": "Narutimate Accel v2.28.iso",
            "configuration": "na228_builder/configurations/release.json",
            "configuration_name": "config.json",
            "images": [
                {
                    "id": "NA2",
                    "label": "original NA2 ISO",
                    "size": 10,
                    "sha256": "ab" * 32,
                },
                {
                    "id": "nun5",
                    "label": "original NUN5 ISO",
                    "size": 11,
                    "sha256": "cd" * 32,
                },
            ],
        }

        manifest = parse_release_manifest(json.dumps(data))

        self.assertEqual(manifest.images[0].image_id, "na2")
        self.assertEqual(manifest.images[0].sha256, "AB" * 32)
        self.assertEqual(manifest.output_name, "Narutimate Accel v2.28.iso")
        self.assertEqual(
            manifest.configuration_name,
            "config.json",
        )

    def test_manifest_parser_rejects_unsafe_output_name(self) -> None:
        data = {
            "schema_version": 1,
            "product_name": "Narutimate Accel v2.28",
            "product_version": "1.0.0",
            "executable_name": "Narutimate Accel v2.28.exe",
            "output_name": "build/Narutimate Accel v2.28.iso",
            "configuration": "na228_builder/configurations/release.json",
            "configuration_name": "config.json",
            "images": [
                {
                    "id": "na2",
                    "label": "NA2",
                    "size": 1,
                    "sha256": "11" * 32,
                },
                {
                    "id": "nun5",
                    "label": "NUN5",
                    "size": 2,
                    "sha256": "22" * 32,
                },
            ],
        }
        with self.assertRaisesRegex(ReleaseError, "one filename"):
            parse_release_manifest(json.dumps(data))

    def test_discovery_is_nonrecursive_case_insensitive_and_hash_pinned(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "renamed.ISO").write_bytes(na2)
            (root / "donor.iSo").write_bytes(nun5)
            (root / "unrelated.iso").write_bytes(b"wrong size")
            nested = root / "nested"
            nested.mkdir()
            (nested / "duplicate.iso").write_bytes(na2)

            messages: list[str] = []
            selected = identify_supported_images(
                root,
                self.manifest(na2, nun5).images,
                emit=messages.append,
            )

            self.assertEqual(selected["na2"].name, "renamed.ISO")
            self.assertEqual(selected["nun5"].name, "donor.iSo")
            self.assertTrue(any("[OK] original NA2 ISO" in line for line in messages))

    def test_same_size_wrong_hash_is_rejected(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(b"dirty-na2")
            (root / "NUN5.iso").write_bytes(nun5)

            with self.assertRaisesRegex(ReleaseError, "supported original NA2 ISO"):
                identify_supported_images(
                    root,
                    self.manifest(na2, nun5).images,
                    emit=lambda _message: None,
                )

    def test_duplicate_supported_iso_is_rejected(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2 A.iso").write_bytes(na2)
            (root / "NA2 B.ISO").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)

            with self.assertRaisesRegex(ReleaseError, "multiple copies"):
                identify_supported_images(
                    root,
                    self.manifest(na2, nun5).images,
                    emit=lambda _message: None,
                )

    def test_configuration_failures_happen_before_iso_hashing(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)
            manifest = self.manifest(na2, nun5)

            with mock.patch("na228_builder.scripts.app.file_sha256") as hash_file:
                with self.assertRaisesRegex(ReleaseError, "Configuration is missing"):
                    run_release(
                        root,
                        manifest,
                        lambda *_args: None,
                        emit=lambda _message: None,
                    )
                hash_file.assert_not_called()

            (root / manifest.configuration_name).write_text("not json", encoding="utf-8")
            with mock.patch("na228_builder.scripts.app.file_sha256") as hash_file:
                with self.assertRaisesRegex(ReleaseError, "not valid JSON"):
                    run_release(
                        root,
                        manifest,
                        lambda *_args: None,
                        emit=lambda _message: None,
                    )
                hash_file.assert_not_called()

            self.write_configuration(root)

            def reject_configuration(_path: Path) -> None:
                raise ValueError("structure mismatch")

            with mock.patch("na228_builder.scripts.app.file_sha256") as hash_file:
                with self.assertRaisesRegex(ValueError, "structure mismatch"):
                    run_release(
                        root,
                        manifest,
                        lambda *_args: None,
                        configuration_validator=reject_configuration,
                        emit=lambda _message: None,
                    )
                hash_file.assert_not_called()

    def test_runtime_config_validation_wraps_internal_details_for_users(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            configuration = Path(directory) / "config.json"
            self.write_configuration(configuration.parent)
            with mock.patch(
                "na228_builder.scripts.release_runtime.validate_release_configuration",
                side_effect=ValueError(
                    "Invalid config value at features.battle_logic.substitution_cost: "
                    "got 0.1; expected decimal & 0..15 & step 0.25, or false to disable it"
                ),
            ):
                with self.assertRaisesRegex(
                    ReleaseError,
                    "Invalid config.json: Invalid config value at "
                    "features.battle_logic.substitution_cost",
                ):
                    _runtime_configuration_validator(configuration)

    def test_success_promotes_building_iso_and_preserves_inputs(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            na2_path = root / "anything.iso"
            nun5_path = root / "something.ISO"
            na2_path.write_bytes(na2)
            nun5_path.write_bytes(nun5)
            configuration_path = self.write_configuration(root)
            calls: list[tuple[Path, Path, Path, Path]] = []

            def builder(
                source_na2: Path,
                source_nun5: Path,
                configuration: Path,
                building: Path,
                _emit,
            ) -> None:
                calls.append((source_na2, source_nun5, configuration, building))
                building.write_bytes(na2)

            output = run_release(
                root,
                self.manifest(na2, nun5),
                builder,
                emit=lambda _message: None,
            )

            self.assertEqual(
                output,
                root.resolve() / "Narutimate Accel v2.28.iso",
            )
            self.assertEqual(output.read_bytes(), na2)
            self.assertFalse(
                (root / "Narutimate Accel v2.28.iso.building").exists()
            )
            self.assertEqual(na2_path.read_bytes(), na2)
            self.assertEqual(nun5_path.read_bytes(), nun5)
            self.assertEqual(
                calls[0][:2],
                (na2_path.resolve(), nun5_path.resolve()),
            )
            self.assertEqual(calls[0][2], configuration_path.resolve())

    def test_existing_output_is_replaced_and_ignored_during_source_discovery(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        replacement = b"built-na2"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)
            output = root / "Narutimate Accel v2.28.iso"
            output.write_bytes(na2)
            self.write_configuration(root)

            def builder(
                _na2: Path,
                _nun5: Path,
                _configuration: Path,
                building: Path,
                _emit,
            ) -> None:
                building.write_bytes(replacement)

            result = run_release(
                root,
                self.manifest(na2, nun5),
                builder,
                emit=lambda _message: None,
            )

            self.assertEqual(result.read_bytes(), replacement)
            self.assertFalse(
                (root / "Narutimate Accel v2.28.iso.building").exists()
            )

    def test_existing_building_path_is_refused_before_builder(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)
            building = root / "Narutimate Accel v2.28.iso.building"
            building.write_bytes(b"keep")
            self.write_configuration(root)
            called = False

            def builder(*_args) -> None:
                nonlocal called
                called = True

            with self.assertRaisesRegex(ReleaseError, "already exists"):
                run_release(
                    root,
                    self.manifest(na2, nun5),
                    builder,
                    emit=lambda _message: None,
                )
            self.assertFalse(called)
            self.assertEqual(building.read_bytes(), b"keep")

    def test_builder_failure_removes_only_new_temporary_output(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)
            output = root / "Narutimate Accel v2.28.iso"
            output.write_bytes(b"previous")
            self.write_configuration(root)

            def builder(
                _na2: Path,
                _nun5: Path,
                _configuration: Path,
                building: Path,
                _emit,
            ) -> None:
                building.write_bytes(b"partial")
                raise RuntimeError("synthetic failure")

            with self.assertRaisesRegex(RuntimeError, "synthetic failure"):
                run_release(
                    root,
                    self.manifest(na2, nun5),
                    builder,
                    emit=lambda _message: None,
                )

            self.assertEqual(output.read_bytes(), b"previous")
            self.assertFalse(
                (root / "Narutimate Accel v2.28.iso.building").exists()
            )

    def test_selected_inputs_are_rechecked_after_locking(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)
            self.write_configuration(root)
            real_identify = identify_supported_images
            called = False

            def identify_then_change(*args, **kwargs):
                selected = real_identify(*args, **kwargs)
                selected["na2"].write_bytes(b"dirty-na2")
                return selected

            def builder(*_args) -> None:
                nonlocal called
                called = True

            with mock.patch(
                "na228_builder.scripts.app.identify_supported_images",
                side_effect=identify_then_change,
            ):
                with self.assertRaisesRegex(ReleaseError, "changed after identification"):
                    run_release(
                        root,
                        self.manifest(na2, nun5),
                        builder,
                        emit=lambda _message: None,
                    )
            self.assertFalse(called)

    def test_wrong_size_build_is_rejected_and_cleaned(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)
            self.write_configuration(root)

            def builder(
                _na2: Path,
                _nun5: Path,
                _configuration: Path,
                building: Path,
                _emit,
            ) -> None:
                building.write_bytes(b"wrong")

            with self.assertRaisesRegex(ReleaseError, "wrong size"):
                run_release(
                    root,
                    self.manifest(na2, nun5),
                    builder,
                    emit=lambda _message: None,
                )

            self.assertFalse(
                (root / "Narutimate Accel v2.28.iso.building").exists()
            )

    def test_missing_build_output_is_reported(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "NA2.iso").write_bytes(na2)
            (root / "NUN5.iso").write_bytes(nun5)
            self.write_configuration(root)

            with self.assertRaisesRegex(ReleaseError, "did not produce"):
                run_release(
                    root,
                    self.manifest(na2, nun5),
                    lambda *_args: None,
                    emit=lambda _message: None,
                )

    def test_main_writes_failure_log_and_keeps_traceback_out_of_console(self) -> None:
        na2 = b"clean-na2"
        nun5 = b"clean-nun5"
        for should_fail in (False, True):
            with self.subTest(should_fail=should_fail):
                with tempfile.TemporaryDirectory() as directory:
                    root = Path(directory)
                    (root / "NA2.iso").write_bytes(na2)
                    (root / "NUN5.iso").write_bytes(nun5)
                    self.write_configuration(root)
                    prompts: list[str] = []
                    messages: list[str] = []

                    def builder(
                        _na2: Path,
                        _nun5: Path,
                        _configuration: Path,
                        building: Path,
                        _emit,
                    ) -> None:
                        if should_fail:
                            raise RuntimeError("boom")
                        building.write_bytes(na2)

                    code = main(
                        directory=root,
                        manifest=self.manifest(na2, nun5),
                        builder=builder,
                        emit=messages.append,
                        read=lambda prompt: prompts.append(prompt) or "",
                    )

                    self.assertEqual(code, 1 if should_fail else 0)
                    self.assertEqual(prompts, ["Press Enter to close."])
                    expected = "Build failed" if should_fail else "Build completed"
                    self.assertTrue(any(expected in message for message in messages))
                    self.assertNotIn("Traceback", "\n".join(messages))
                    if should_fail:
                        log = (root / "builder-error.log").read_text(encoding="utf-8")
                        self.assertIn("Technical details: builder-error.log", messages)
                        self.assertIn("Outcome: failed", log)
                        self.assertIn("Traceback", log)
                        self.assertIn("RuntimeError: boom", log)
                    else:
                        self.assertFalse(any(path.suffix == ".log" for path in root.iterdir()))


if __name__ == "__main__":
    unittest.main()
