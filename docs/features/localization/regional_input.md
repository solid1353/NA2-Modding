# Regional input

`features.localization: "en"` includes the `localization.regional_input` patch
to make the imported English interface use its intended confirm and cancel buttons.
The `"jp"` choice retains native regional input. Button labels and input behavior
are selected together.
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

## Observed menu buttons

A development image with English localization was navigated through Mode
Select, Free Battle and Practice setup, both pause menus, Options, and
Collection. Cross confirmed and Triangle backed out on every visited menu;
Screen Settings labels Triangle as Cancel. Circle selected Random on Character
Select and Stage Select and opened Customize Jutsu on the Free Battle versus
screen. The retail menus are mapped in
[Modes and menu navigation](../../knowledge/game/modes_and_navigation.md).
