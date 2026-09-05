# Character Select

## Balance overlay

`features.character_select.balance_overlay` is independently selectable from
`features.settings.character_overrides`. Its guarded hook replaces the first
native player-panel draw call with a wrapper that preserves that draw, resolves
the selected character ID, and reads the same complete generated character
table used by battle.

When enabled, the overlay always displays each selected character's `TIER` in
the corresponding top-screen block. It additionally displays the resolved
`SUB x%` value only when `features.settings.character_overrides` is enabled. If
Character Overrides is disabled, the table still supplies tier metadata to the
overlay but is not applied to gameplay. The builder links the complete table
once whenever either consumer needs it; it does not generate a partial or
alternate table.

## Support selection

`features.character_select.support_selection` accepts `"all"`, `"relevant"`,
or `"none"`. Each mode builds one support roster per player, beginning with
**No Support**:

- `"all"` appends only supports selectable by the chosen fighter, in native
  order, using native unlock, recommendation, and compatibility checks. It retains native
  carousel wrapping, repeated cells, and positioning, initially selecting No
  Support through the native support-ID selector. Confirmation skips Linked
  Mode and finalizes in Auto mode; Back returns to support selection with
  the current cursor and scroll position preserved.
- `"relevant"` appends only the declared directional relationships below.
- `"none"` keeps only No Support and skips support selection.

The relevant relationships are:
Naruto-Sakura, Sakura-Chiyo, Itachi-Kisame, Sasori-Deidara, and
Sasuke-Orochimaru in both directions, plus Naruto to Sai, Naruto to Gaara,
Sasuke to Naruto, Tsunade to Jiraiya, and Shikamaru to Choji. A fighter with no
retained relationship therefore receives No Support as the sole selectable
entry. The base configuration uses `"all"`; release uses `"relevant"`.
As with other catalog settings, `false` disables the patch and retains native
selection without the added No Support entry.

The comparative implementation evidence for prepending No Support is recorded
in [NUN6 Character Select](nun6/gameplay/character_select.md).

Both native population call sites use one C entry point. In `"all"`, the
wrapper filters the native roster separately for each player and prepends No
Support. Its filter calls the native compatibility predicate behind the red
unavailable marker and preserves the recommendation exception for locked
entries. This excludes both Sasori and Hiruko when either is the main fighter,
including Sasori's puppet form, through the native rule rather than a special
case. The filtering change is pending runtime validation and acceptance.
After fighter confirmation, the shared confirmation hook
selects No Support through native `0x003B49C0`, which initializes the native
cursor and scroll anchor. The compact modes instead center their complete row.

All modes copy the complete `0x454`-byte selector-data block for each player, preserving
the fighter and support portrait-object tables while allowing simultaneous
different rosters. It retains each permitted native ID and availability state,
prepends the entries declared in `ADDITIONAL_SUPPORT_ENTRIES`, and clears the
unused list slots. The current special declaration adds native no-support ID
`0x25` as an available entry, maps it to display record `0x5F`, and supplies
the name `NO SUPPORT`.

The first runtime test proved that the inserted icon rendered and that the
cursor could reach it, but pressing OK did not accept it. NA2's separate BTL
compatibility helper rejects every support ID at or above `0x24`. The linked
comparison establishes an extended gate through `0x25`. The implementation routes all six Character
Select consumers of the helper through a second table-aware C entry point.
IDs declared in `ADDITIONAL_SUPPORT_ENTRIES` are accepted globally. In
`"relevant"`, native IDs use the same directional roster table; in `"none"`,
they are rejected. The `"all"` candidate delegates native IDs to the original
compatibility helper; excluded entries are absent from the filtered list. This
keeps confirmation, navigation, and draw eligibility consistent with the chosen
mode. The corrected `"all"` mode has not yet been validated in game.

The support-selection builder adapter selects the hook set before composition.
All modes share the fighter-confirmation, support-finalization, and finalized
Back hooks for the No Support default and Linked Mode bypass. Linked Mode is
fixed to Auto for both players in Battle and Practice, including secondary
fighter confirmation and No Support; the modal stays skipped. This Auto change
is pending runtime validation and acceptance. In `"all"`, the
Back handler preserves the selected support and carousel position instead of
reapplying the initial default. The adapter omits the compact cell-draw and
horizontal-navigation hooks from `"all"`, together with their code. Per-player
list storage is shared by all modes, while `"all"` retains native carousel
drawing, scrolling, and wrapping.

Runtime testing then confirmed that OK accepts the new entry, but established
that NA2's unextended support-to-display map resolves ID `0x25` to record zero,
visibly reusing Classic Naruto. The localization pipeline's imported official
NUN5 `CHARSEL1.CCS` already contains a Leaf sprite at display record `0x5F`;
the patch routes Character Select's list and selected-portrait lookups
through the table-defined record. No donor artwork is imported or reused.

The NUN5 character-name atlas has no suitable No Support label. For the added
entry only, the selected-name path therefore skips the unrelated character
sprite and draws `NO SUPPORT` with the resident font, centered in the existing
nameplate. Every native support delegates to the complete original name path.
Runtime testing confirmed the Leaf and label both render, while the initial
full-width label intruded beneath the **Linked Character** badge. Two rejected
candidates wrote `0.80` to the shared scale word without activating Font v2's
geometry hooks; runtime pixels proved that the label remained full-width and
offsetting it merely moved the problem. The accepted implementation uses the
existing Font v2 adapter to fit the measured 112-unit label into the row's
84-unit maximum width and center its actually scaled glyph geometry in the
nameplate. There is no manual draw offset. The injection remains table-driven
so later special entries can supply their own display record, name, and maximum
label width without editing the executable list. In the compact modes, the
native renderer always
visits 13 carousel positions and wraps them modulo the roster count; an
additional guarded draw hook suppresses those wrapped repetitions so every
compact entry is rendered once at its native position. The selector defaults to
No Support and initializes the carousel anchor from the compact count so the
complete row opens centered. Left and right retain native movement between
entries, while input past the first or last entry is ignored instead of
wrapping. A one-entry roster thus shows one centered, highlighted Leaf cell and
remains there. Clean call sites, both native list producers, all six
compatibility consumers, both horizontal-navigation calls, and all six render
hooks are statically guarded. Runtime validation confirmed the
fitted-and-centered label, compact per-character roster behavior, centered
default, and bounded navigation.

In the compact modes, for a fighter whose roster contains only No Support, both native
fighter-confirmation calls now retain the native confirmation work and then
advance directly from fighter selection to the finalized state with support
index zero and Linked Mode set to Auto. The support-selection and Linked Mode
screens are never rendered. Back from that finalized state returns directly to
fighter selection; rosters with selectable partners retain the complete native
forward and backward flow. A retained replay confirmed that Naruto's four
recorded menu markers remain unchanged while the
No-Support-only fighter moves directly from marker 5 to marker 8. A derivative
replay confirmed the reverse marker-8-to-marker-5 transition. Runtime validation
confirmed both directions.

The setting does not change field-support calls or the native battle support
gauge. Those are controlled independently by
`features.settings.ingame.battle_mechanics.support`; selected native supports and linked Jutsu
remain intact in every combination. The Character Select record is in
[`../knowledge/game/character_select.md`](../knowledge/game/character_select.md),
and the battle-path evidence is in
[Battle support mechanics](../knowledge/gameplay/support_mechanics.md).

## NUN5 PNACH

The active
[`NUN5.pnach`](../../pcsx2_files/games/NUN5/NUN5.pnach)
section `[+Select No Support on Character Select]` ports this support-selection
behavior to NUN5.

The PNACH reserves `0x2000` bytes from the game allocator tail by moving its
heap end to `0x01FF3FF0`. Immutable code and data occupy
`0x01FF4000..0x01FF4A5F`; mutable selector buffers occupy
`0x01FF4A60..0x01FF5307` and are never written by the PNACH. Payload and hook
writes require allocator global `0x00617A84` to contain the reserved heap end,
so hot-loading the PNACH into a process that still uses the native heap cannot
overwrite it.

The apparent space after the loaded NUN5 `BTL.BIN` belongs to the live overlay
reservation and may contain battle state. It is not safe resident payload
storage.
