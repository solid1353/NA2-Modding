from __future__ import annotations

import json
from collections.abc import Callable
from typing import Any


def _normalized(text: str) -> str:
    characters = list(text)
    index = 0
    in_string = False
    escaped = False

    while index < len(characters):
        character = characters[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            index += 1
            continue
        if character != "/" or index + 1 >= len(characters):
            index += 1
            continue

        following = characters[index + 1]
        if following == "/":
            characters[index] = " "
            characters[index + 1] = " "
            index += 2
            while index < len(characters) and characters[index] not in "\r\n":
                characters[index] = " "
                index += 1
            continue
        if following == "*":
            start = index
            characters[index] = " "
            characters[index + 1] = " "
            index += 2
            while index + 1 < len(characters):
                if characters[index] == "*" and characters[index + 1] == "/":
                    characters[index] = " "
                    characters[index + 1] = " "
                    index += 2
                    break
                if characters[index] not in "\r\n":
                    characters[index] = " "
                index += 1
            else:
                raise json.JSONDecodeError("Unterminated block comment", text, start)
            continue
        index += 1

    index = 0
    in_string = False
    escaped = False
    while index < len(characters):
        character = characters[index]
        if in_string:
            if escaped:
                escaped = False
            elif character == "\\":
                escaped = True
            elif character == '"':
                in_string = False
            index += 1
            continue
        if character == '"':
            in_string = True
            index += 1
            continue
        if character != ",":
            index += 1
            continue
        following = index + 1
        while following < len(characters) and characters[following].isspace():
            following += 1
        if following < len(characters) and characters[following] in "}]":
            characters[index] = " "
        index += 1

    return "".join(characters)


def loads(
    text: str,
    *,
    object_pairs_hook: Callable[[list[tuple[str, Any]]], Any] | None = None,
) -> Any:
    return json.loads(
        _normalized(text),
        object_pairs_hook=object_pairs_hook,
    )
