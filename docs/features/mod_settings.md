# Mod Settings

`features.settings.mod_settings` defines the initial values and Return to
Defaults values for the session-wide Mod Settings menu:

| Field | Menu row | Values |
| --- | --- | --- |
| `battle_mechanics_submenu` | Battle Mechanics | `true` includes the submenu launcher; `false` omits it |
| `new_controls` | Control Scheme | `false` = Classic, `true` = Updated |
| `simple_display` | Simple Display | `off`, `on` |
| `character_overrides` | Character Balance | `false` = Original, `true` = Overrides |
| `balance_overlay` | Balance Overlay | `false` = Off, `true` = On |
| `support_selection` | Support Selection | `none`, `relevant`, `all` |

The builder always includes the five runtime implementations. Their configured
values initialize one writable runtime state when the game starts; changes made
through the menu last until the game process ends and are not written to the
memory card.

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
transaction and closes. Select stages the configured defaults, and Square
opens a configured submenu. Opening plays the same sound as native Practice
Settings.

`battle_mechanics_submenu` is the first configured row and opens
`features.settings.submenus.battle_mechanics_submenu`, the same generated
submenu used by Battle Settings and Practice Settings.

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
block source at runtime. Simple Display updates the three live settings packs
when changed. Character Balance selects the original data or generated
character-override table. Balance Overlay gates its Character Select renderer
and shows substitution cost only with Character Balance set to Overrides.
Support Selection applies its three-state filter to the always-present
Character Select hooks.
