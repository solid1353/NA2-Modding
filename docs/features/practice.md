# Practice

## Practice bootstrap PNACH

Practice bootstrap is runtime-only and has no builder catalog node, builder
configuration field, resident fragment, or ISO rebuild input. The launch
profile invocation is `na228 <game> [game] -l practice <case-id>`; `practice`
selects a stable `case_id` case-insensitively from
`@repository/launch_profiles/practice/movesets.tsv`. It works with NUN5,
NA2.28 build selectors, build-and-launch tokens, and input playback. It reads
only that case; it neither reads
`character_data.tsv` nor expands character, support, or awakening combinations.
The table's spelling is canonical and is returned regardless of input casing.
Empty `support_id` and `awakening_id` cells select No Support `0x25` and the
`FFFFFFFF` no-effect awakening sentinel. A nonempty hexadecimal support or
awakening ID overrides its default. A `-rev` case adds a fourth, game-specific
inline PNACH line that selects the native Half starting-HP mode; all other cases
retain normal starting HP. Every case has an authoritative E2E
`capture_policy`: an empty cell means no capture; populated values are `base`,
`specials`, `base, specials`, or `base, parent-specials`. The last value records
a second form in its own Base grid and appends it to the preceding primary
form's Specials grid. ID suffixes do not implicitly select a capture family.

`@repository/launch_profiles/practice/NA228.pnach` and
`@repository/launch_profiles/practice/NUN5.pnach` contain the
complete game-specific bootstraps. Each selected game receives its own file and
three ordinary inline PNACH lines at that game's character, support, and
awakening configuration addresses. Those process-local lines are the sole case
values and do not modify or regenerate either file. The normal
PNACHs at `@pcsx2_files/games/NA228/NA228.pnach` and
`@pcsx2_files/games/NUN5/NUN5.pnach` contain no Practice bootstrap.
Clean NA2 is not supported yet.

The bootstrap writes both current and match-start Player 1 fields, fixes Player
2 to Naruto with Sakura support and the Practice stage to `6`, skips Character
Select and Practice Settings, and retains the native battle-loading states.
Its battle wrapper first runs the native update, then applies the requested
awakening once after Player 1 exists. Every nonempty awakening ID reaches the
native awakening function's exact-effect transition, so the requested effect,
awakened controller state, transition actions, and sound are applied together.
Deidara `0x41` retains the complete native entry. Taijutsu Chiyo `0x4E` first
enters her separate native moveset state, then uses the complete native entry to
remove her constructor-owned `0x4D` effect and apply `0x4E`. Gaara's regular
`0x3B` first enters his separate native moveset state, then reaches the shared
transition; his item awakening `0x3C` deliberately does not enter that moveset
state. There is no raw-effect fallback.

The NA2 guards are runtime `0x001E9AF8` for the post-Continue route,
`0x001ECA2C` for the unchanged state-`7` call into the replaced native
`FUN_001ED450` range, and `0x001ECACC` for the state-`15` battle-update call.
The reverse-engineering evidence, PNACH layout, and native field contract are
in [`../knowledge/gameplay/battle.md`](../knowledge/gameplay/battle.md).

## Practice Settings rework

`features.settings.practice` maps a compact
Practice Settings row list onto the native menu and accepts four optional
native defaults:

- `health`: `full`, `half`, or `critical`;
- `commands`: `off` or `on`;
- `guide_ninja_sound`: `off` or `on`;
- `linked_attack`: `off`, `on`, or `random`.

An omitted field preserves the game's native initializer value. The base
configuration explicitly selects `full`, `off`, `off`, and `off` in the order
above. Health reaches the native normalized live-HP targets `1.0`, `0.5`, and
`0.1`; Linked Attack maps to the native dummy values Don't use, Normal, and
`乱発`.

The implementation builds the feature-aware row list. When
`features.settings.shared` is enabled, it adds the same `Substitution: Chakra |
Gauge | Free`, `Sub Active Frames: 0..16`, `X-dash Chakra Cost: 0% | 5% | ... |
100%`, and `Support: Off | On` rows used by Battle Settings. `Chakra` uses
native chakra and hides the gauge, `Gauge` uses and displays the independent
resource, and `Free` consumes nothing and hides the gauge. Both menus stage and
commit the same runtime values, and the shared configuration controls both
reset actions directly.

The row list always retains Ultimate Jutsu. With the shared setting enabled,
that row exposes its six
native values plus `No Contest` and `No HUD`, stages and commits the same shared
runtime enum as Battle Settings, and uses the Battle setting's configured value
for its reset action. The row's underlying native slot receives the selected
native value, or `Command` for either custom value. The same feature also adds
ordinary `Shadowblur Extra Hit: Off | On` and `Extra Hit: Off | On` rows to the
player section. They snapshot and commit the same shared runtime toggles as
Battle Settings, and their reset values come from `features.settings.shared`.

The native support-related Practice rows remain present because Support can be
changed at runtime. The native Extra Hit Counter row remains independent of the
shared Extra Hit selector. The intended presentation retains the native row
widgets, localization, selection, scrolling, animation, and clipping paths.
Runtime confirmation is pending.

The implementation uses one guarded tail hook in clean `SLPS_258.37` at ELF offset
`0xE7C7C` (runtime `0x001E7B7C`) to replace the initializer's final
store-and-return pair. The leaf first reproduces the displaced native Linked
Attack default, then applies only configured fields from the resident Practice
schema. The former standalone starting-HP, Commands, Guide Ninja Sound, and
Linked Attack edit patches are not retained.

Practice `-rev` cases override the initializer process-locally with
`0x001E7AE8 = 0xA0850001` for NA228 or
`0x001ED8D8 = 0xA0850001` for NUN5. Other cases do not add either write.
