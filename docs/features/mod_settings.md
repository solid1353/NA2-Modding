# Mod Settings

`features.defaults.mod_settings` defines the initial values and Return to
Defaults values for the session-wide Mod Settings menu. The Match Setup
submenu holds settings that apply from the next battle:

| Field | Menu row | Values |
| --- | --- | --- |
| `support_selection` | Support Selection | `none`, `relevant`, `all` |
| `character_balance` | Character Balance | `original`, `overrides` |
| `balance_overlay` | Balance Overlay | `off`, `on` |
| `extended_items` | Extended Items | `off`, `on`; see [Extended Items](battle.md#extended-items) |

`simple_display` (`off` or `on`) remains on the Mod Settings root.

The builder always includes the runtime implementations of Simple Display and
the first three Match Setup rows. Their configured
values initialize one writable runtime state when the game starts. The menu,
save flow, and C consumers use `mod_settings_option_get` and
`mod_settings_option_set` with the setting's index: Simple Display `0`,
Character Balance `1`, Balance Overlay `2`, and Support Selection `3`. Each
value is its position in the table's value list. The setter ignores an
out-of-range value, and the getter returns the configured value for an
out-of-range stored value. The Simple Display assembly bridges read the first
state word directly. With
`features.memory_card.extended_save_data` enabled, the existing save flow
writes these values and every other runtime-editable value below
`features.defaults` to the dedicated record appendix. A valid loaded record
overrides configured defaults; a missing setting keeps its configured default.
When the appendix schema changes, all mod settings return to configured defaults
while native progress and controls load. With extended save data disabled, the
retail save format does not store these values.

Square on Mode Select opens an existing Practice Settings child as a modal
surface. Each Mode Select controller prepares the Options backdrop, Practice
child, replacement title, and footer prompt during its native entrance
transition, before its first draw. The footer adds a pink Square badge followed
by **Mod** between the native START and OK prompts. Square therefore only resets
and opens the prepared child. While the child completes its native opening
phase invisibly, Mode Select continues drawing. The active menu then replaces
Mode Select drawing with the Options backdrop followed by the Mod Settings
surface. The child and the menu-owned backdrop resources are released with
Mode Select; a newly constructed Mode Select controller prepares a new set.

`defaults.mod_settings` hooks these main-ELF call sites: Mode Select
construction (`0xEA528`), the
[pre-decoder no-op](../knowledge/game/mode_flow.md#resident-pre-dispatch-hook-seam)
(`0x284AD0`), Mode Select draw (`0xEA69C`), the START prompt draw
(`0x285F40`), and the cleanup calls after accept and back (`0xEA628`,
`0xEA66C`). It calls the BTL Practice child entries from Mode Select, which
relies on BTL being
[selected before Mode Select is constructed](../knowledge/game/mode_flow.md#overlay-state-across-return-routing).

While the menu is open, each child update temporarily receives Mode Select's
[combined new and held masks](../knowledge/game/mode_flow.md#input-actions)
in the active side's input record, which is restored afterward. Either player
can therefore operate the menu, and manager `+0x18` is unchanged. Mode
Select's sampled input fields `+0x30`, `+0x38`, `+0x3C`, and `+0x40` are then
cleared before native Mode Select handling continues, including on the frame
Square opens the menu and the frame Cross or Triangle closes it. The child
retains the native Practice Settings input, sound, submenu, and backing behavior
while using the shared generated pages and rows. Cross applies the staged
values and closes. Triangle returns from a submenu or discards the root
transaction and closes. Select stages configured defaults for every setting on
the current page, including rows outside the visible scroll window, and names
that page in the reset notice. On the root page, this resets Simple Display;
child pages retain their own values until reset separately. Square opens a
configured submenu. Opening plays the same sound as native Practice Settings.

`features.defaults.mod_settings` holds the `match_setup_submenu`,
`battle_mechanics_submenu`, `battle_settings_submenu`,
`practice_settings_submenu`, and `control_settings_submenu` launcher switches
with its Simple Display row; Match Setup's settings live in
`features.defaults.match_setup`. Their config order places Match Setup
first and Control Settings after Practice Settings in the base menu, before
Simple Display. Match Setup's settings read their runtime values through Mod
Settings, so they require `mod_settings` to stay enabled. The release configuration exposes these switches with
the other default settings.
Battle Mechanics opens
`features.defaults.battle_mechanics`. The Battle Settings and
Practice Settings pages expose their existing stored values without repeating
Battle Mechanics. Changes made through these pages also appear in the existing
in-game Battle Settings and Practice Settings menus.

Control Settings opens the native Options Controls screen and controller over
the Mod Settings menu. Both players can edit it, as in Options; the native reset
otherwise leaves only the last battle's human side active outside the Options
mode. Each player's side reads that player's own pad. Its binding and
vibration edits, defaults, confirmation, and cancellation use the native
Controls behavior. Mod Settings keeps its
selected row and staged values while Controls is open. Closing Controls returns
to its launcher; confirmed control changes are independent of the Mod Settings
transaction. The Mod Settings handoff clears the native Options white
transition when Controls opens and closes; opening Options normally retains
its native transition.

Battle Difficulty and Options Difficulty share the same selected value.
Changing either control updates the native Options mirror and the persisted
Battle Difficulty value.

The settings pages use the generated Practice-style submenu renderer. Their labels,
selector values, and help messages reference the same translated resources as
the original Battle Settings and Practice Settings menus. The Practice Settings
hooks recognize the Mod Settings child by comparing it with the child pointer
Mode Select prepared. For that child they use the Mod Settings pages, skip the
native Practice snapshot and apply, and add the Handicap panel and Control
Settings launcher; every other child keeps Practice Settings' pages and native
behavior.

Handicap uses the native Battle Settings presentation from
[Battle rows and Handicap](../knowledge/localization/ui/battle/settings_presentation.md#battle-rows-and-handicap).
Its row draws the native double-height panel in place of its Practice strip,
aligned to the ordinary strip it replaces. The ten-segment gauge sits 38 units
below the label at scale `0.9`; the selected count is red and the rest blue.
While Handicap is selected, the label-only cursor replaces the Practice cursor
and no value arrows are shown. Handicap must be the last row on its page
because the panel's second line has no room for a following row; the builder
rejects any other placement.

Before publishing the child, the runtime acquires `option.ccs` through the
native archive helper and constructs only its `ANM_option_ca` camera and
`ANM_option_back` backdrop resources. It records whether the helper loaded the
archive or returned an existing one, and destroys the archive only when the
menu owns it. The context and animation instances are always released with
Mode Select or after failed construction. The Mod Settings child then loads its
own `PRAC.CCS` instance. After the child is constructed, the runtime acquires
`setting.ccs` the same way and creates the Handicap panel animation, cursor,
and a `TEX_s_menu` gauge sprite in the child's text context. They are released
before the child. If the backdrop, footer sprite, child, or any of these
Handicap resources cannot be created, everything already prepared is released
and that Mode Select runs without the Mod prompt or menu. The
runtime replaces the panel's yellow label cap in `TEX_s_menu` with the olive cap
the Practice rows use from the child's `TEX_prac_t01`, then re-uploads the
texture and palette. The palette is full, so the cap's most frequent colors
take the entries only the old cap used and the rest use the nearest existing
color. The archive can already be resident and shared, so the original cap
pixels and palette are saved first and restored and re-uploaded before release. Its native full-screen Practice backdrop tint is
disabled so the Options artwork supplies the complete background. After
construction, the runtime replaces only the title strip of that instance's
`TEX_prac_t01` pixels with the bundled 128-by-32 indexed
`mod_settings_title.png` texture and re-uploads the native texture. The title
artwork is centered without changing its aspect ratio. The native title model
then draws **Mod Settings**; ordinary Practice Settings retains its original
archive, title, and rendering path.

The footer prompt stays inside Mode Select's prompt render context at controller
`+0x6C`. **Mod** is installed in a transparent, unused part of the Mode Select
label atlas and is submitted with its native label sprite. A menu-owned sprite
loads `TEX_vs_t01` from `vs.ccs` and draws only the retail Practice launcher's
Square badge rectangle `(5, 281, 22, 22)`. That sprite is finalized immediately
after its draw, so no pending
geometry is left on a Practice-owned or shared sprite. The native START draw
call is wrapped to append both pieces before the existing Mode Select prompt
batches are finalized; other menus and shared prompt textures are unchanged.
The Square badge is centered at `(294, 362)` and the Mod label at `(327, 362)`,
using the same vertical anchor as the native footer prompts.

Simple Display has one shared value for Mod Settings,
the battle/Practice pause menu, and the save appendix. The 1P, 2P, and COM
[markers above fighters](../knowledge/localization/ui/battle/selectors_and_prompts.md#player-markers)
are drawn only while it is on. The native Simple Display
getter and setter use the same Mod Settings getter and setter as the menu and
save flow. The shared setter updates the three native settings packs, which
carry the value for native gameplay. Character Balance selects the original
data or generated character-override table. Balance Overlay gates its Character Select renderer
and shows substitution cost only with Character Balance set to Overrides.
Support Selection applies its three-state filter to the always-present
Character Select hooks.
