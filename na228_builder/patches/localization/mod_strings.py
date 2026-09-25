"""Language-selected text authored by the mod, shared by Python and C payloads."""
from __future__ import annotations

import csv
import re
from dataclasses import dataclass, field
from pathlib import Path
from string import Formatter

from ...infrastructure.modules.payload_builder.operations import PayloadFragment


TABLE_PATH = Path(__file__).resolve().parents[2] / "resources" / "mod_strings.tsv"
NUMERIC_CHARACTERS = "0123456789%.,:/+-"
FULLWIDTH_NUMBERS = str.maketrans({char: chr(ord(char) + 0xFEE0)
                                 for char in NUMERIC_CHARACTERS})
NUMBER = re.compile(r"[+-]?[0-9]+(?:[.,:/-][0-9]+)*%?")


@dataclass(frozen=True)
class Message:
    id: str
    arguments: dict[str, object] = field(default_factory=dict)


def message(identifier: str, **arguments: object) -> Message:
    return Message(identifier, arguments)


class ModStrings:
    def __init__(self, selection):
        self.language = next(node.configured_value for node in selection.nodes
                             if node.path == ("features", "localization"))
        self.encoding = "cp932" if self.language == "jp" else "cp1252"
        with TABLE_PATH.open(encoding="utf-8-sig", newline="") as handle:
            reader = csv.DictReader(handle, delimiter="\t")
            if not reader.fieldnames or self.language not in reader.fieldnames:
                raise ValueError(f"mod_strings.tsv has no {self.language!r} column")
            self.rows = {}
            for row in reader:
                identifier = row["id"]
                value = row[self.language]
                if not identifier or identifier in self.rows or not value:
                    raise ValueError(f"Invalid or missing mod string: {identifier!r}/{self.language}")
                self.rows[identifier] = value.replace("\\n", "\n")

    def resolve(self, value: Message | str) -> str:
        if isinstance(value, str):
            return value
        template = self.rows[value.id]
        arguments = {key: self.resolve(argument) if isinstance(argument, Message) else argument
                     for key, argument in value.arguments.items()}
        fields = {name for _, name, _, _ in Formatter().parse(template) if name is not None}
        if fields != set(arguments):
            raise ValueError(f"Mod string {value.id!r} arguments differ: {fields} != {set(arguments)}")
        return template.format(**arguments)

    def encode(self, value: Message | str) -> bytes:
        text = self.resolve(value)
        if self.language == "jp":
            # Keep renderer commands such as <iconL1> byte-for-byte intact.
            text = "".join(part if part.startswith("<") else
                           NUMBER.sub(lambda match: match[0].translate(FULLWIDTH_NUMBERS), part)
                           for part in re.split(r"(<[^>]*>)", text))
        return text.encode(self.encoding)

    def native_payload(self, symbol: str) -> bytes:
        if symbol == "mod_number_glyphs":
            glyphs = []
            for code in range(128):
                char = chr(code)
                if self.language == "jp" and char in NUMERIC_CHARACTERS:
                    char = char.translate(FULLWIDTH_NUMBERS)
                glyphs.append(int.from_bytes(char.encode(self.encoding), "big").to_bytes(2, "little"))
            return b"".join(glyphs)
        if symbol == "mod_number_handicap":
            return b"".join(self.encode(f"{value}-{10 - value}") + b"\0"
                            for value in range(11))
        return self.encode(self.rows[symbol.removeprefix("mod_text_").replace("__", ".")]
                           .replace("{0}", "\x01")) + b"\0"

    def fragments(self, fragments, patches):
        """Embed only text and number glyphs referenced by selected payloads."""
        references = {}
        for fragment in fragments:
            for relocation in fragment.relocations:
                if relocation.symbol.startswith(("mod_text_", "mod_number_")):
                    references.setdefault(relocation.symbol, fragment.owner)
        for patch in patches:
            if patch.symbol.startswith(("mod_text_", "mod_number_")):
                references.setdefault(patch.symbol, patch.owner)
        return tuple(PayloadFragment(
            owner=owner, symbol=symbol, kind="rodata", alignment=4,
            payload=self.native_payload(symbol),
        ) for symbol, owner in sorted(references.items()))
