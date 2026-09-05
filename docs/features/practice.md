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
Its battle wrapper first runs the native update, then applies the configured
Practice Status once after the dummy fighter exists and applies the requested
awakening once after Player 1 exists. Status activation calls the native
Practice bridge, including its dummy-control flag, fighter-controller state,
and AI/Strength initialization side effects. Every nonempty awakening ID
reaches the native awakening function's exact-effect transition, so the
requested effect, awakened controller state, transition actions, and sound are
applied together.
Deidara `0x41` retains the complete native entry. Taijutsu Chiyo `0x4E` first
enters her separate native moveset state, then uses the complete native entry to
remove her constructor-owned `0x4D` effect and apply `0x4E`. Gaara's regular
`0x3B` first enters his separate native moveset state, then reaches the shared
transition; his item awakening `0x3C` deliberately does not enter that moveset
state. There is no raw-effect fallback.

The native starting-HP enum is settings byte `+1` in `FUN_001E7A80`. At
runtime `0x001E7AE8` (ELF offset `0xE7BE8`), the full-HP form retains the clean
eight bytes, the half-HP form stores the existing `a1 == 1`, and the critical
form reorders the existing `li t1,2` before storing `t1`. Every form preserves
the following native store of `2` to settings byte `+2` and requires the exact
clean eight-byte guard.

The NA2 guards are runtime `0x001E9AF8` for the post-Continue route,
`0x001ECA2C` for the unchanged state-`7` call into the replaced native
`FUN_001ED450` range, and `0x001ECACC` for the state-`15` battle-update call.
The native Practice architecture and starting-HP evidence are in
[Practice-mode knowledge](../knowledge/gameplay/practice_mode.md). Native
effect-entry behavior is in [Awakening](../knowledge/gameplay/awakening.md).

## Practice Settings rework

`features.settings.ingame.practice_mode` maps a generated, paged Practice Settings
schema onto the native menu. Its root options and `opponent_settings` submenu
retain the native value handlers. The complete base configuration
defines every retained native default:

| Section | Field | Values |
| --- | --- | --- |
| Root | `health` | `normal`, `half`, `almost` |
| Root | `commands`, `damage` | `off`, `on` |
| `opponent_settings` | `status` | `manual`, `com`, `stand`, `jump`, `double_jump` |
| `opponent_settings` | `strength` | `simple`, `easy`, `normal`, `hard`, `insane`, `ultimate` |
| `opponent_settings` | `attack` | `no`, `single`, `combo`, `projectile`, `high_speed_move`, `ultimate_jutsu`, `jutsu` |
| `opponent_settings` | `guard` | `no`, `yes` |
| `opponent_settings` | `move` | `stay`, `follow` |
| `opponent_settings` | `substitution_jutsu` | `normal`, `no` |
| `opponent_settings` | `linked_attack` | `dont_use`, `normal`, `random` |
| `opponent_settings` | `extra_hit_counter` | `normal`, `return` |

Field-support availability and Unlimited are configured through the shared
[Support row](battle.md#battle-support) in Battle Mechanics.

Configured fields initialize the Practice manager and replace the corresponding
local values when Return to Defaults is used. Health reaches normalized live-HP
targets `1.0`, `0.5`, and `0.1`; opponent Linked Attack maps to Don't use,
Normal, and `乱発`. Every retained Practice option has a concrete configured
value and appears in its menu section. Linked Mode and Guide Ninja Sound are not
configuration fields: both rows are always omitted, Linked Mode is fixed to
Auto, and Guide Ninja Sound is fixed to Off.

The base config orders the root page as `Battle Mechanics`, `Opponent Settings`,
then the retained native General Settings rows. Config key order controls the
root and every child page; moving entries within an object reorders its rows.
Square on a
launcher opens its child page; Confirm applies and closes from launcher rows as
it does from every ordinary row. Launcher rows retain the native row geometry,
recolor only their label panel to the child-heading orange, and display
`Open <iconSQUARE>` without native value arrows. `Battle Mechanics` contains every enabled leaf under
`features.settings.ingame.battle_mechanics`, in config key order. `Opponent
Settings` likewise follows its config object's key order.
Both child pages use the native orange section heading and opponent-style row
backing, with their own page title. The count-derived backing and launcher-label
renderer is shared with Battle Settings.
Cancel returns to the selected launcher's root row; Cancel on the root retains
the native close behavior. With regional input enabled, Cancel is Triangle.
Mod rows use the same runtime values as Battle Settings, so both menus stage,
reset, and commit the same state. Entering or leaving either child page restarts
the selected row's help-text animation.

Chakra is no longer a native General Settings row. The base config places it
first in Battle Mechanics. It shares `normal`, `unlimited`, or a
`0.1..10.0%/s` regeneration rate with
Battle Settings. Numeric values appear as `Regen N.N%/s`. The generated native
default pack fixes the underlying Practice Chakra key to Normal; the shared
runtime setting alone owns refilling.

Confirm on any ordinary row still applies and closes the complete Practice
transaction. Return to Defaults resets every configured row, including rows on
the page that is not currently visible. Closing from the root without
confirming still discards all staged changes.

Ultimate Jutsu is now an injected mod row rather than an always-retained
native row. It exposes its six native values plus `No Contest` and `No HUD`,
stages and commits the same shared runtime enum as Battle Settings, and uses
the shared configured value for its reset action. The underlying native slot
receives the selected native value, or `Command` for either custom value. The
same mod block also adds
ordinary `Shadowblur Extra Hit: Off | On` and `Extra Hit: Off | On` rows to the
player section. They snapshot and commit the same shared runtime toggles as
Battle Settings, and their reset values come from `features.settings.ingame.battle_mechanics`.

The native Extra Hit Counter row remains independent of the mod Extra Hit
selector. The presentation retains the native row widgets, localization,
selection, scrolling, animation, and clipping paths.

Each generated page records its row range, section counts, parent page, and
return row. Backing cells and selection-frame placement are derived from the
active page's section counts. Both sections retain the native first, middle,
and terminal cell roles; extra rows repeat a native middle cell and keep the
terminal cell on the actual final row. The cursor uses section-local visible
geometry, so adding or removing options does not change row height, introduce
seams, or require a new fixed-index layout patch. Runtime label and value tables
are allocated from the largest generated page rather than a fixed menu
capacity.

The implementation guards the native manager-reset call site in clean
`SLPS_258.37` at ELF offset `0xF5AD4` and applies the Practice default pack only
after the native reset and Strength-mirror write complete. Menu-local Return to
Defaults uses each feature-aware row schema, so startup and menu reset share the
same configured values. The former initializer-tail override is not retained.

Practice `-rev` cases override the initializer process-locally with
`0x001E7AE8 = 0xA0850001` for NA228 or
`0x001ED8D8 = 0xA0850001` for NUN5. Other cases do not add either write.
