from __future__ import annotations

import struct
from dataclasses import replace
from typing import TYPE_CHECKING

from ..payload_builder.operations import PayloadFragment

if TYPE_CHECKING:
    from .catalog import CatalogSelection
    from ..modules.runtime_injector.engine import RuntimeInjectionPackage


SUPPORT_SELECTION_PATH = (
    "features",
    "character_select",
    "support_selection",
)
SUPPORT_SELECTION_MODES = {
    "all": 2,
    "relevant": 1,
    "none": 0,
}
COMPACT_SUPPORT_SYMBOLS = frozenset({
    "character_select_support_selection_draw_support_cell",
    "character_select_support_selection_bounded_support_navigation",
})


def support_selection_runtime_package(
    selection: CatalogSelection,
    package: RuntimeInjectionPackage,
) -> RuntimeInjectionPackage:
    matches = [
        node for node in selection.nodes if node.path == SUPPORT_SELECTION_PATH
    ]
    if len(matches) != 1:
        raise ValueError("Catalog selection has no unique support_selection node")
    node = matches[0]
    if not node.enabled:
        return package
    if (
        not node.has_configured_value
        or node.configured_value not in SUPPORT_SELECTION_MODES
    ):
        raise ValueError("Support selection must be 'all', 'relevant', or 'none'")
    mode_fragment = PayloadFragment(
        owner=package.owner,
        symbol="character_select_support_selection_mode",
        kind="rodata",
        alignment=4,
        payload=struct.pack("<I", SUPPORT_SELECTION_MODES[node.configured_value]),
    )
    if node.configured_value == "all":
        omitted = COMPACT_SUPPORT_SYMBOLS
        edits = tuple(
            edit
            for edit in package.edits
            if edit.symbolic_patch.symbol not in COMPACT_SUPPORT_SYMBOLS
        )
    else:
        omitted = frozenset()
        edits = package.edits
    return replace(
        package,
        edits=edits,
        fragments=(mode_fragment, *(
            fragment for fragment in package.fragments
            if fragment.symbol not in omitted
        )),
    )
