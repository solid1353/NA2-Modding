# Menu input runtime behavior

Native NA2 and NUN5 menu-input handler relationships and Save/Load control
flow.

## Research coverage

- **Assigned scope:** identify the resident menu-input handlers, their regional
  button masks, and the Save/Load row and confirmation owners.
- **Exploration depth:** matching functions and immediate masks were compared
  statically, and representative modal and Save/Load paths were exercised.
- **Confirmed coverage:** the shared selectable-modal family, Save/Load parent
  and child handlers, slot-row renderer, navigation branches, and relevant
  confirmation statuses are identified.
- **Unresolved or untested:** the minimum independently sufficient subset of
  regional Save/Load handler changes.
- **Deliberate exclusions and overlap:** NA228 selection and validation belong
  to [Regional input](../../../features/localization/regional_input.md); compact
  one-record presentation belongs to [Memory Card](../../../features/memory_card.md).
- **Evidence limitations:** combined runtime behavior does not prove that every
  participating native handler is independently necessary.

## Save/Load controller

`FUN_001E6370` draws three Save/Load record rows. Its loop ends at
`0x001E6970` with `slti v1,s2,3`. The earlier occupancy scan still examines all
three records. `FUN_001E69B0` separately owns selection and navigation; its Down
and Up branches at `0x001E6AA0` and `0x001E6AE0` change selected-slot field
`+0x10`, clear transition field `+0x18`, and play sound `0x35`.

The upper-frame constructor is `FUN_001E57B0`. Date and play-time placement is
owned by the row renderer, while the independent `MDL_xkun1` object draws the
slot cursor. These are separate presentation owners from occupancy, save data,
and save execution.

Save-mode status `0x0C` is the no-save-data confirmation. Its No branch resets
the controller to the initial save prompt after `0x001E4588`. Status `0x2C` is
unrelated. The live comparison instruction at `0x001E451C` supplies the accept
mask used by the status-`0x0B` and status-`0x0C` confirmation paths.

[`function_map.tsv`](function_map.tsv) records reusable NA2/NUN5 input-handler
functions, offsets, and button masks. Its offsets and masks were validated
against the clean regional binaries; row notes contain only handler-specific
limitations or runtime corroboration. Mod behavior and its runtime evidence are
linked from [Regional input](../../../features/localization/regional_input.md).
