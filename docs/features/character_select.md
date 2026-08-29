# Character Select

## Balance overlay

`features.character_select.balance_overlay` is independently selectable from
`features.general.character_overrides`. Its guarded hook replaces the first
native player-panel draw call with a wrapper that preserves that draw, resolves
the selected character ID, and reads the same complete generated character
table used by battle.

When enabled, the overlay always displays each selected character's `TIER` in
the corresponding top-screen block. It additionally displays the resolved
`SUB x%` value only when `features.general.character_overrides` is enabled. If
Character Overrides is disabled, the table still supplies tier metadata to the
overlay but is not applied to gameplay. The builder links the complete table
once whenever either consumer needs it; it does not generate a partial or
alternate table.

## Support selection rework

`features.character_select.support_selection_rework` is an accepted runtime
patch that builds one compact support roster per player. Every roster begins with **No Support**;
native supports are retained only for the declared directional relationships:
Naruto-Sakura, Sakura-Chiyo, Itachi-Kisame, Sasori-Deidara, and
Sasuke-Orochimaru in both directions, plus Naruto to Sai, Naruto to Gaara,
Sasuke to Naruto, Tsunade to Jiraiya, and Shikamaru to Choji. A fighter with no
declared relationship therefore receives No Support as the sole selectable
entry.

Both native population call sites are routed through one C injection. It
copies the complete `0x454`-byte selector-data block for each player, preserving
the fighter and support portrait-object tables while allowing simultaneous
different rosters. It retains each permitted native ID and availability state,
prepends the entries declared in `ADDITIONAL_SUPPORT_ENTRIES`, and clears the
unused list slots. The current special declaration adds native no-support ID
`0x25` as an available entry, maps it to display record `0x5F`, and supplies
the name `NO SUPPORT`.

The first runtime test proved that the inserted icon rendered and that the
cursor could reach it, but pressing OK did not accept it. NA2's separate BTL
compatibility helper rejects every support ID at or above `0x24`; NUN6 extends
that gate through `0x25`. The implementation routes all six Character
Select consumers of the helper through a second table-aware C entry point.
IDs declared in `ADDITIONAL_SUPPORT_ENTRIES` are accepted globally, while
native IDs are accepted only for the same directional roster table. This keeps
confirmation, navigation, and draw eligibility aligned with the compact lists
instead of showing rejected cells with red-X overlays.

Runtime testing then confirmed that OK accepts the new entry, but established
that NA2's unextended support-to-display map resolves ID `0x25` to record zero,
visibly reusing Classic Naruto. The localization pipeline's imported official
NUN5 `CHARSEL1.CCS` already contains a Leaf sprite at display record `0x5F`;
the patch routes Character Select's list and selected-portrait lookups
through the table-defined record. NUN6 artwork is not imported or reused.

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
label width without editing the executable list. The native renderer always
visits 13 carousel positions and wraps them modulo the roster count; an
additional guarded draw hook suppresses those wrapped repetitions so every
compact entry is rendered once at its native position. The selector defaults to
No Support and initializes the carousel anchor from the compact count so the
complete row opens centered. Left and right retain native movement between
entries, while input past the first or last entry is ignored instead of
wrapping. A one-entry roster thus shows one centered, highlighted Leaf cell and
remains there. Clean call sites, both native list producers, all six
compatibility consumers, both horizontal-navigation calls, and all six render
hooks are statically guarded. The user accepted the fitted-and-centered label
in runtime on 2026-08-14, the compact per-character roster behavior on
2026-08-15, and the centered default plus bounded navigation on 2026-08-23.

For a fighter whose compact roster contains only No Support, both native
fighter-confirmation calls now retain the native confirmation work and then
advance directly from fighter selection to the finalized state with support
index zero and Linked Mode disabled. The support-selection and Linked Mode
screens are never rendered. Back from that finalized state returns directly to
fighter selection; rosters with selectable partners retain the complete native
forward and backward flow. A retained replay confirmed that Naruto's four
recorded menu markers remain unchanged while the
No-Support-only fighter moves directly from marker 5 to marker 8. A derivative
replay confirmed the reverse marker-8-to-marker-5 transition. The user accepted
both directions on 2026-08-15.

The setting does not change field-support calls or the native battle support
gauge. Those are controlled independently by
`features.settings.shared.support`; selected native supports and linked Jutsu
remain intact in every combination. The Character Select record is in
[`../knowledge/game/character_select.md`](../knowledge/game/character_select.md),
and the battle-path evidence is in
[`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).
