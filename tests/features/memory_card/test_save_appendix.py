"""Save-schema checks that prevent ambiguous or incomplete stored settings."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from na228_builder.patches.memory_card import save_appendix


class SaveAppendixTests(unittest.TestCase):
    def setUp(self) -> None:
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.path = Path(temporary.name) / "save_appendix.tsv"

    def write_rows(self, rows: list[str]) -> None:
        self.path.write_text(
            "# schema_version: 1\nid\tkey\tlabel\tvalues\n"
            + "\n".join(rows)
            + "\n",
            encoding="utf-8",
        )

    def test_duplicate_identity_is_rejected(self) -> None:
        for second in (
            "0101\tsecond\tSecond\tOff | On",
            "0102\tfirst\tSecond\tOff | On",
        ):
            with self.subTest(second=second):
                self.write_rows(["0101\tfirst\tFirst\tOff | On", second])
                with self.assertRaisesRegex(ValueError, "Duplicate"):
                    save_appendix.load_save_appendix(self.path)

    def test_fixed_appendix_capacity_is_enforced(self) -> None:
        rows = [
            f"{index:04X}\tsetting{index}\tSetting {index}\tOff | On"
            for index in range(1, 126)
        ]
        self.write_rows(rows[:124])
        self.assertEqual(124, len(save_appendix.load_save_appendix(self.path)[1]))
        self.write_rows(rows)
        with self.assertRaisesRegex(ValueError, "capacity"):
            save_appendix.load_save_appendix(self.path)

    def test_fractional_ranges_have_exact_endpoints(self) -> None:
        self.write_rows(["0101\tdelay\tDelay\t0.1s to 0.3s by 0.1s | Off"])
        _, rows = save_appendix.load_save_appendix(self.path)
        self.assertEqual(4, rows[0].option_count)
        self.write_rows(["0101\tdelay\tDelay\t0.1s to 0.35s by 0.1s"])
        with self.assertRaisesRegex(ValueError, "does not end on its step"):
            save_appendix.load_save_appendix(self.path)

    def test_missing_setting_and_invalid_default_stop_schema_generation(self) -> None:
        self.write_rows(["0101\tfirst\tFirst\tOff | On"])
        binding = save_appendix.SettingBinding("get", "set", 0, 0, 0)
        with patch.object(save_appendix, "_bindings", return_value={
            "first": binding, "second": binding,
        }):
            with self.assertRaisesRegex(ValueError, "omits settings: second"):
                save_appendix.save_appendix_schema_fragment(
                    None, owner="memory_card", path=self.path,
                )
        invalid = save_appendix.SettingBinding("get", "set", 0, 0, 2)
        with patch.object(save_appendix, "_bindings", return_value={"first": invalid}):
            with self.assertRaisesRegex(ValueError, "default for first"):
                save_appendix.save_appendix_schema_fragment(
                    None, owner="memory_card", path=self.path,
                )


if __name__ == "__main__":
    unittest.main()
