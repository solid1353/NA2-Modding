from __future__ import annotations

import struct

from na228_builder.infrastructure.modules.payload_builder.operations import (
    PayloadFragment,
    PayloadRelocation,
)


def save_load_continuation_fragments(selection, *, owner: str) -> tuple[PayloadFragment, ...]:
    enabled = {
        node.path[-1]
        for node in selection.nodes
        if node.path[:-1] == ("features", "memory_card") and node.enabled
    }
    next_update = "display_only_first_save_update" if "auto_loading" in enabled else None
    fragments = []
    for setting, symbol in (
        ("dialogs_rework", "dialogs_rework"),
        ("dedicated_save_namespace", "save_appendix"),
    ):
        if setting not in enabled:
            continue
        fragments.append(PayloadFragment(
            owner=owner,
            symbol=f"{symbol}_next_update",
            kind="rodata",
            alignment=4,
            payload=struct.pack("<I", 0 if next_update else 0x001E3F20),
            relocations=(
                PayloadRelocation(offset=0, kind="abs32", symbol=next_update),
            ) if next_update else (),
        ))
        next_update = f"{symbol}_update"
    return tuple(fragments)
