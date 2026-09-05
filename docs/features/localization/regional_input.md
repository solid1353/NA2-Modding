# Regional input

`features.localization.regional_input` selects the guarded menu-input ports that
make the imported English interface use its intended confirm and cancel buttons.
The catalog and localization patch store own selection and exact writes.

## Save/Load handlers

The accepted behavior combines the shared selectable-modal decoder with the
Save/Load parent, confirmation, and acknowledgment handler groups. The three
Save/Load groups were ineffective in isolation but corrected the title/load/save
matrix together. They must not be treated as independently runtime-proven.

The visible first-record wrapper reads the effective accept mask from the live
comparison instruction at `0x001E451C`; it does not embed a second Circle or
Cross constant. Changing regional input therefore updates the wrapper without
a separate setting.

BTL complete-file offset `0x00066210` is an NA2-specific Cross correction
(`20006330` to `40006330`). The corresponding NUN5 offset `0x000692B0` still
checks Circle, so this site is established by NA2 runtime behavior rather than
copied from NUN5.

Clean function relationships remain in
[`../../knowledge/runtime/menu_input/function_map.tsv`](../../knowledge/runtime/menu_input/function_map.tsv).
