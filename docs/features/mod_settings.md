# Mod Settings

`features.default_settings.mod_settings` defines the initial values and Return to
Defaults values for the session-wide Mod Settings menu:

| Field | Menu row | Values |
| --- | --- | --- |
| `controls` | Control Scheme | `classic`, `updated` |
| `character_balance` | Character Balance | `original`, `overrides` |
| `balance_overlay` | Balance Overlay | `off`, `on` |
| `simple_display` | Simple Display | `off`, `on` |
| `support_selection` | Support Selection | `none`, `relevant`, `all` |

The builder always includes the five runtime implementations. Their configured
values initialize one writable runtime state when the game starts. With
`features.memory_card.dedicated_save_namespace` enabled, the existing save flow
writes these values and every other runtime-editable value below
`features.default_settings` to the dedicated record appendix. A valid loaded record
overrides configured defaults; a setting absent from an older record keeps its
configured default. With the dedicated namespace disabled, the retail save
format does not store these values.

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

Mode Select input is routed through the child while the menu is open and is
cleared before native Mode Select handling continues. The child retains the
native Practice Settings input, sound, defaults, submenu, and backing behavior
while using the shared generated pages and rows. Cross applies the staged
values and closes. Triangle returns from a submenu or discards the root
transaction and closes. Select stages the configured defaults and shows
**Settings returned to defaults.** Square opens a configured submenu.
Opening plays the same sound as native Practice Settings.

`features.menu_composition.mod_settings` controls the Battle Mechanics, Battle
Settings, and Practice Settings launchers. Each Boolean includes or omits its
launcher, and their config order determines their order before the five Mod
Settings values. The value rows follow `features.default_settings.mod_settings`
order. `menu_composition` is omitted from release config and catalog exports;
the packaged builder retains its resolved release values. Battle Mechanics opens
`features.default_settings.battle_mechanics`. The Battle Settings and
Practice Settings pages expose their existing stored values without repeating
Battle Mechanics. Changes made through these pages also appear in the existing
in-game Battle Settings and Practice Settings menus.

Battle Difficulty and Options Difficulty share the same selected value.
Changing either control updates the native Options mirror and the persisted
Battle Difficulty value.

Both pages use the generated Practice-style submenu renderer. Their labels,
selector values, and help messages reference the same translated resources as
the original Battle Settings and Practice Settings menus. Handicap remains a
normal text-value row in this shared presentation.

Before publishing the child, the runtime acquires `option.ccs` through the
native archive helper and constructs only its `ANM_option_ca` camera and
`ANM_option_back` backdrop resources. It records whether the helper loaded the
archive or returned an existing one, and destroys the archive only when the
menu owns it. The context and animation instances are always released with
Mode Select or after failed construction. The Mod Settings child then loads its
own `PRAC.CCS` instance. Its native full-screen Practice backdrop tint is
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

Control Scheme selects the held-input guard, action-history lookup, and logical
block source at runtime. Simple Display has one shared value for Mod Settings,
the battle/Practice pause menu, and the save appendix. The native Simple Display
getter and setter use the same Mod Settings getter and setter as the menu and
save flow. The shared setter updates the three native settings packs, which
carry the value for native gameplay. Character Balance selects the original
data or generated character-override table. Balance Overlay gates its Character Select renderer
and shows substitution cost only with Character Balance set to Overrides.
Support Selection applies its three-state filter to the always-present
Character Select hooks.
