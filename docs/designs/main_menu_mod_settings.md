# Main Menu Mod Settings modal

Status: Draft

This design adds one dedicated **Mod Settings** modal launched from Mode
Select. It uses the existing Practice Settings child, resources, input model,
transitions, sounds, row presentation, backing, cursor, arrows, help text,
staging, Defaults, Confirm, and Cancel behavior. It does not extend resident
Options, repurpose the Return to Title two-choice modal, or combine those two
controllers.

The modal edits one shared mutable runtime state. Its values control
Guard/Substitution input interpretation, Simple Display bits in the live
settings packs, substitution-cost calculation, Character Select balance-overlay
drawing, and support-list construction and navigation. The active build
configuration defines each field's initial value and Return-to-Defaults value.
Those values no longer decide whether the corresponding runtime code is
emitted. Implementation remains unauthorized until `imp`.

## Requested behavior

On Mode Select, pressing Square opens Mod Settings. Mode Select remains visible
and animated while the settings receive input. After the modal finishes its
fade-out and is destroyed, Mode Select resumes on the same selected slot.

The root page contains these rows in this order:

| Row | Values | Configuration default |
| --- | --- | --- |
| Control Scheme | Classic, Updated | `features.settings.new_controls` |
| Simple Display | Off, On | `features.settings.simple_display` |
| Character Balance | Original, Overrides | `features.settings.character_overrides` |
| Balance Overlay | Off, On | `features.character_select.balance_overlay` |
| Support Selection | All, Relevant, None | `features.character_select.support_selection` |

Reuse the existing Practice Settings interface, changing its title to **Mod
Settings** and supplying the rows above. Its controls, sounds, button prompts,
navigation, help, fades, Defaults, apply, and discard behavior remain unchanged:

- Up and Down wrap through rows; Left and Right change the selected value.
- Square opens a submenu when the selected configured row owns one.
- Cross applies all staged changes and closes from any page.
- Triangle returns from a submenu to its parent page without discarding staged
  changes. On the root page, it discards all staged changes and closes without
  applying them.
- Select stages configured defaults for every row; the values are committed
  only if the user subsequently applies them with Cross.
- Navigation, value changes, submenu entry, and submenu return use sound
  `0x35`; Confirm uses `0x34`; root Cancel and Defaults use `0x33`.
- The fade, repeat countdown, help animation, cursor, value arrows, backing,
  footer prompts, and visible-row culling remain the Practice implementation.

For now, applied choices last for the current game session and are not saved
to the memory card. Restarting the game restores the initial values from the
configuration. Existing saved control assignments remain owned by the native
profile and are never rewritten by changing Control Scheme.

## Established retail basis

The resident controller and overlay-lifetime facts are canonical in
[Resident front-end and mode flow](../knowledge/game/mode_flow.md) and
[Practice-mode architecture](../knowledge/gameplay/practice_mode.md).
Presentation facts are canonical in
[Battle and Practice settings presentation](../knowledge/localization/ui/battle/settings_presentation.md).

### Mode Select host

Clean Mode Select callback `FUN_001EA240` synchronously selects BTL before it
constructs the Mode Select controller. The BTL overlay is therefore resident
through the active Mode Select phase. While the controller remains active:

- `FUN_003854F0` updates it;
- state 2 calls `FUN_003849C0` for input;
- `FUN_003849C0` calls the clean eight-byte no-op `FUN_00384DE0` at runtime
  `0x003849D0` before decoding input and while `a0` is still the Mode Select
  controller pointer; and
- callback call site `0x001EA59C` calls `FUN_00385C00` to draw Mode Select
  whenever its update remains nonterminal.

The no-op is the input/update extension seam. The draw call is the presentation
extension seam. Neither requires a new manager callback ID or a result-table
entry, so opening and closing Mod Settings cannot dispatch another game mode.

The native Return to Title controller is Mode Select state 3. It is a nested
two-choice modal whose result is interpreted specifically as exit or resume.
Its exact selection and button behavior is documented in the linked mode-flow
record. It is not a general settings owner and must remain unchanged.

### Practice Settings child

The Practice child is a `0xB8`-byte BTL object. Its established live entry
points are:

| Role | Live address |
| --- | ---: |
| Initialize child | `0x008809E0` |
| Destroy child | `0x00880A20` |
| Construct resources | `0x00880BE0` |
| Reset/snapshot | `0x00880F30` |
| Update | `0x00881AB0` |
| Draw | `0x00882250` |

The retail standalone wrapper proves that this child can be allocated outside
the main battle-settings parent: it allocates `0xB8`, initializes the child,
constructs resources with variant 0, and calls the same update and draw
entries. That standalone wrapper itself belongs to a separate BTL selector
host whose scheduling alongside the main owner is unresolved. Mod Settings
must therefore reuse the child lifecycle, not install or invoke the standalone
host.

The main Practice parent passes backdrop variant 1; the standalone wrapper
passes variant 0. Mod Settings uses variant 1 so it remains a modal surface
over Mode Select. The separately drawn child `+0x18` object uses the
`TEX_prac_t01` rectangle `(1,1,126,30)` for panel/arrow imagery; it is not the
title and remains native.

The title is record `0` of the `ANM_prac_cel` backing at child `+0x2C`. That
record targets `OBJ_prac_title` and `MDL_prac_title`, independently of the 17
row-cell records. The Mod Settings adapter suppresses only record `0` for the
Mod Settings child and draws `Mod Settings` with the existing font in the
native title footprint. The Practice adapter leaves record `0` unchanged. All
other Practice resources remain native.

### Supplied NA2.28 savestate

The supplied slot-1 state shows Mode Select with Free Battle highlighted and
the native Return to Title modal open with its first choice selected. It
corroborates the state-3 controller interpretation but is mod-runtime evidence,
not clean-retail evidence.

The preserved EE memory contained these relevant live values:

| Address / object field | Value | Interpretation |
| --- | ---: | --- |
| `0x006045E0` | `0xFFFF` | remembered Mode Select slot cleared by the active back path |
| `0x006073FC` | `0x00950180` | input context pointer |
| `0x006075F8` | `0x00C9ED50` | live profile pointer |
| `0x00607600` | `0x00CA2600` | resident front-end manager |
| `0x0060760C` | `0x00CA6B40` | callback transient |
| `0x00607610` | `0x00CA4BD0` | Mode Select controller |
| Manager `+0x08/+0x0C/+0x10` | `4 / 1 / 0` | active callback phase, Mode Select callback, BTL selector |
| Manager `+0x14/+0x18` | `0 / 0` | no active pause owner; controller port 0 retained |
| Manager `+0x4C/+0x74` | `1 / 2` | current Player 1 and Player 2 character IDs |
| Callback transient `+0x00/+0x08/+0x10` | `4 / 0 / 0xFFFFFFFF` | active Mode Select callback phase and saved-result fields |
| Mode Select `+0x00` | `3` | native Return to Title modal state |
| Mode Select `+0x04` | `4` | four active compact slots |
| Mode Select `+0x08..+0x14` | `1, 2, 5, 6` | Free Battle, Practice, Collection, Options physical slots |
| Mode Select `+0x24` | `0` | first compact entry selected |
| Mode Select `+0x30..+0x40` | all zero | no sampled input in the preserved frame |
| Mode Select `+0xBC` | `1` | Free Battle physical slot presented |
| Mode Select `+0xC0/+0xC8/+0xCC/+0xD0` | `0x00CC4430 / 0x00CC5270 / 0x00CC6D10 / 0x00CC5FA0` | live presentation/modal child pointers |
| Mode Select `+0xCC` | `0x00CC6D10` | active nested modal wrapper |
| Modal wrapper `+0x40/+0x48/+0x7C` | `0 / 8 / 0x00CC7A40` | non-timed wrapper state, presentation field, nested child pointer |
| Nested child `+0x12` | `0` | no choice result committed |
| Nested child `+0x14` | `2` | two choices |
| Nested child `+0x18` | `0` | first choice selected |
| Nested child `+0x1C/+0x28/+0x29` | `3 / 0 / 5` | modal mode and clear event/input fields |

The three manager settings packs at `+0x9F4`, `+0xA00`, and `+0xA0C` were
identical: `31 00 02 63 02 05 02 02 00 00 00 01`. First-byte bit `0x02` was
clear, matching Simple Display Off.

The state also contained executable BTL code at `0x006BFD30`, `0x006C0F60`,
`0x006C1120`, `0x00875B20`, `0x00875B50`, `0x008809E0`, `0x00880BE0`,
`0x00881660`, `0x00881AB0`, and `0x00882250`. These cover the generic settings
parent, standalone Practice wrapper, and Practice child constructor, resource,
input, update, and draw paths. This supports the selected architecture's
residency assumption for this input; the clean resident callback independently
establishes why BTL is present.

## Current implementation inventory

The existing shared menu work already provides most of the requested system:

- `SettingsMenuOption` contains getter, setter, argument, and staged value.
- `build_menu_pages` discovers page topology from catalog/configuration order.
- generated pages contain row ranges, section counts, parent page/row, and
  heading resources.
- shared code handles page selection, model-index translation, dynamic
  backing composition, visible-row culling, label/value indirection, cursor
  geometry, help text, and window movement.
- Practice's Opponent Settings text is a generated submenu header selected by
  the active page; it is not backing animation record `0`.
- Practice snapshots runtime options on open, stages every edit, stages all
  configured defaults on Select, commits all setters on Confirm, and discards
  staged values on root Cancel.

The reusable pieces are currently mixed with Practice-only behavior:

- the C adapter directly reads the Practice child offsets and native rows;
- snapshot/apply/defaults unconditionally call native Practice handlers;
- active page and presentation tables are global Practice singletons;
- row availability contains Practice Status and difficulty rules; and
- the generated Practice row format includes native row IDs, local offsets,
  resource-slot flags, and custom battle-mechanic cases.

Mod Settings needs a second adapter over the same child and renderer, not a
copy of those functions.

### Current build-time behavior to retire

The five requested values currently influence composition independently:

- `settings.new_controls` conditionally installs editor labels/defaults and
  three gameplay changes for split Guard/Substitution behavior.
- `settings.simple_display` replaces only the initializer instruction at ELF
  offset `0xE7BAC` with either native `or v1,v1,a2` or a no-op.
- `settings.character_overrides` conditionally installs substitution-cost
  hooks and may own the generated character table.
- `character_select.balance_overlay` conditionally installs the Character
  Select draw wrapper and may own that same table.
- `character_select.support_selection` conditionally installs its hooks and
  payload; its adapter also omits compact-navigation code when the configured
  mode is `all`.

Those omissions are incompatible with changing values at runtime. The table,
hooks, and all mode-specific helper bodies must be present in every maintained
build that exposes Mod Settings.

The current base configuration resolves to these initial/default values:

| Runtime field | Base value |
| --- | --- |
| Control Scheme | Updated |
| Simple Display | Off |
| Character Balance | Overrides |
| Balance Overlay | On |
| Support Selection | None |

Other configurations keep their own values; the builder translates each
configuration independently into the same runtime enum layout.

## Shared runtime state

Emit one settings-owned writable data fragment initialized from configuration:

```c
typedef struct ModSettingsState {
    unsigned int control_scheme;       /* 0 Classic, 1 Updated */
    unsigned int simple_display;       /* 0 Off, 1 On */
    unsigned int character_balance;    /* 0 Original, 1 Overrides */
    unsigned int balance_overlay;      /* 0 Off, 1 On */
    unsigned int support_selection;    /* 0 All, 1 Relevant, 2 None */
} ModSettingsState;
```

This is the only mutable source of truth for the five runtime consumers during
the current game session. Each row uses one generic getter/setter pair with the field
index as `SettingsMenuOption.argument`. The generated row descriptor retains
the active configuration's value separately for the local Defaults transaction.

Setters validate their enum range. Invalid stored values fall back to the
configured default at the getter/consumer boundary; they must not index a text
table out of range.

## Generic menu/session split

Extract the current shared behavior into an adapter-driven session without
changing the native child layout:

```text
SettingsMenuSchema
  pages, rows, label/help/value tables, configured defaults

SettingsMenuSession
  schema, active page/index, active label/value buffers

SettingsMenuAdapter
  snapshot, apply, defaults, get/set, maximum, enabled,
  input source, title presentation
```

Controller-facing hooks resolve the adapter by child pointer. If the pointer
equals the resident Mod Settings child, they use the Mod Settings session;
otherwise they use the existing Practice adapter. This avoids a process-wide
“current menu kind” flag and cannot misroute a Practice child merely because a
previous modal was open.

The Mod Settings adapter has only runtime-option rows:

- snapshot copies all five values from `ModSettingsState` into staged fields;
- apply writes all five staged values through their setters;
- defaults replaces all five staged fields with their generated defaults;
- every row is enabled and has a fixed maximum from its value table; and
- there are no native Practice manager keys or child-local option values.

The Practice adapter retains all native snapshot/apply/defaults calls,
availability rules, custom battle-mechanic handlers, and page behavior. Its
externally visible behavior must not change.

The schema generator remains data-driven. Add a dedicated five-row root schema
using the same page/row resource generation and generic `MenuOption` bindings.
Mod Settings supports the shared submenu behavior used by Battle Settings and
Practice Settings: a configured row may open a generated child page with its
own header. Square enters that page, Triangle returns to its configured parent
row, and Cross applies and closes from any page. The five requested rows remain
on the root page; this requirement does not add an unrequested submenu. Further
rows or pages remain schema data and do not require another controller.

## Mode Select lifecycle

The resident launcher owns one pointer to the Mod Settings child.

### Open and update

The replacement for `FUN_00384DE0` receives the Mode Select controller pointer.
When no modal exists, a newly pressed Square from either controller allocates
the `0xB8` child, initializes it, constructs Practice resources with backdrop
variant 1, and activates the Mod Settings session.

When the modal exists, the launcher calls the native Practice child update.
The Mod Settings input adapter ORs the corresponding new/held masks from both
controller ports, matching Mode Select's two-port ownership while retaining
Practice repeat arbitration. It does not overwrite manager `+0x18`, which must
continue to identify the controller that confirmed a game mode.

Before returning to the native Mode Select decoder, the launcher clears the
controller's sampled action fields `+0x30`, `+0x38`, `+0x3C`, and `+0x40`.
This suppresses navigation, confirmation, Back, and Start while the modal is
open. The close-triggering frame is also cleared so Cross or Triangle cannot
fall through into Mode Select.

Once the child update reports fade-out completion, the launcher destroys and
frees the child, clears its pointer, and leaves the Mode Select controller and
selected slot untouched. An allocation failure leaves Mode Select active and
does not publish a partial modal.

### Draw and cleanup

Replace the draw call at resident call site `0x001EA59C` with a wrapper that
first calls native `FUN_00385C00` and then, if the child exists, calls native
Practice draw `0x00882250` for the child. Native Mode Select therefore remains
the background and keeps its ordinary animation.

Mode Select's destruction path also calls a cleanup wrapper. If an exceptional
or externally forced state destroys Mode Select while the modal still exists,
the wrapper destroys and frees the child before continuing native cleanup.
Clean input flow cannot normally reach that path because all Mode Select
actions are suppressed while the modal is active.

## Runtime consumers

### Control Scheme

Keep the Control Settings editor extension installed in both modes:

- action index 6 remains labelled Guard;
- action index 7 remains labelled Substitution;
- both assignment slots remain independently editable and saved;
- the one-action permutation swap remains installed; and
- the configured resident, BTL, and Select-reset binding tables remain
  installed.

Only gameplay interpretation changes:

| Existing patch point | Classic | Updated |
| --- | --- | --- |
| Held-Guard rejection at `na2_elf:0x129720` | execute native 16-frame rejection | permit a fresh Substitution press |
| First substitution-history arm at `na2_elf:0x129740` | search action 6 | search action 7 |
| Second logical-block source at `na2_btl:0x3C02C` | load action 7 as native | return zero so only action 6 blocks |

These three sites become guarded runtime branches instead of direct
configuration-selected replacements. Changing scheme never rewrites either
player's assignment array.

### Simple Display

Clean `FUN_001E7A80` clears Simple Display bit `0x02`, then sets it with:

```text
0x001E7AAC  or v1,v1,a2
0x001E7AB0  sb v1,0(a0)
```

Replace that guarded eight-byte pair with an ABI bridge that stores the bit
from `ModSettingsState.simple_display`. Because `FUN_001E7A80` initializes the
manager's three 12-byte settings packs and is reused by native reset paths,
the shared value is reapplied after every such initialization.

The setter also updates byte 0 bit `0x02` in the live manager packs at
`+0x9F4`, `+0xA00`, and `+0xA0C` when the manager exists. This makes a confirmed
change effective immediately and keeps later Battle/Practice consumers in
sync. The current `mips_simple_display_default` direct-edit adapter becomes
retired and is removed.

### Character Balance

Always load and emit the complete generated character-override table. It
continues to contain tier metadata even when gameplay balance is `Original`.

The substitution-cost helper already receives the native cost. When Character
Balance is `Original`, it returns that native value without applying the base
or character table. When it is `Overrides`, it retains the current base,
literal, and tier-delta resolution. The normalized fraction helper uses the
native `1/15` equivalent in Original mode.

The current read-only `character_overrides_enabled` fragment is replaced by
the shared mutable field. The conditional table-owner selection and conditional
configuration loading are removed; the settings parent owns the table once.

No other generated override columns currently have runtime consumers. This
task does not invent new HP, damage, or recovery behavior.

### Balance Overlay

Always install the guarded Character Select draw wrapper. It always calls the
native player-panel draw first.

- Off returns after the native draw.
- On draws the selected character's tier from the always-present table.
- On also draws resolved substitution cost only when Character Balance is
  Overrides, preserving the current distinction between metadata and applied
  gameplay values.

### Support Selection

Always install the support-list, compatibility, confirmation, finalization,
Back, compact-cell, and bounded-navigation hooks and their helper bodies.
Remove the build-time `all` specialization that omits compact code.

Every consumer reads the shared enum:

- All prepends No Support and retains the filtered native selectable roster,
  native wrapping, and native positioning.
- Relevant prepends No Support and includes only the existing directional
  relationship table, with compact centered and bounded navigation.
- None keeps only No Support and skips the support-selection screen where the
  current one-entry behavior does so.

Changing the setting occurs on Mode Select before a Character Select object is
constructed, so no live roster migration is required.

## Builder and source changes

Implementation should make these cohesive changes:

1. Attach the Mod Settings runtime patch to the `settings` parent and the
   always-present overlay/support hooks to the `character_select` parent.
   Convert `new_controls`, `character_overrides`, and `balance_overlay` from
   marker settings to `setting<bool>`. Keep the existing five configuration
   paths as default inputs. `simple_display` and `support_selection` must be
   populated with their declared enum values; `false` is no longer a supported
   omission for maintained configurations.
2. Add one settings-owned generator for the writable state fragment, its five
   defaults, and the five-row schema. Always load and attach the character
   override table to the settings runtime package.
3. Split generic transaction/session behavior out of the current Practice C
   adapter. Retain Practice-specific native rows and callbacks in the Practice
   adapter; add the runtime-only Mod Settings adapter.
4. Add the resident Mode Select launcher/update, draw, and cleanup bridges.
   They call BTL Practice entries only during the established BTL-resident Mode
   Select lifetime.
5. Replace the three direct Control Scheme gameplay edits with runtime-aware
   bridges while leaving editor/storage/default-assignment behavior installed.
6. Replace the Simple Display instruction adapter with the runtime bit-store
   bridge and live-pack setter.
7. Make character-cost, balance-overlay, and support-selection consumers import
   `ModSettingsState`; remove their build-time enable constants and fragment
   omission logic.
8. Delete retired conditional helpers, including conditional character-table
   ownership, the read-only override-enabled fragment, the Simple Display
   adapter, and Support Selection's `all`-mode code omission.
9. After implementation, update the Battle, Character Select, Practice, and
   Substitution feature documents from build-time selection to the accepted
   runtime contract. The draft design is then promoted or deleted through the
   normal acceptance workflow.

Likely source ownership is:

```text
na228_builder/patches/settings/ingame/shared/
  generic schema/session/presentation code

na228_builder/patches/settings/ingame/practice_mode/
  native Practice adapter only

na228_builder/patches/settings/mod_settings/
  state, schema bindings, Mode Select host, and ABI bridges

na228_builder/patches/settings/new_controls/
  editor behavior plus runtime gameplay bridges

na228_builder/patches/settings/character_overrides/
  always-present table consumer gated by Character Balance

na228_builder/patches/character_select/
  always-present overlay and support consumers
```

No new manifest, save schema, persistent file, workflow, overlay loader, or
manager callback is required.

## Remaining work and limits

The following work remains after this design:

- implement the generic adapter split and five-row schema;
- implement and byte-guard the Mode Select update, draw, cleanup, Control
  Scheme, and Simple Display bridges;
- make table/state packaging unconditional and remove the retired conditional
  code paths;
- update all five consumers and the accepted feature documentation;
- confirm linked payload placement and available resident/BTL injection space
  after the new fragments are composed;
- build every byte-affecting change with `na228 build b` after implementation;
  and
- perform runtime validation only through an explicitly requested maintained
  E2E workflow.

Static evidence establishes the host, lifecycle, input, transaction, and
consumer boundaries. It does not demonstrate the proposed modal running, its
final title placement, cross-mode runtime changes, or allocation behavior in a
modified build. The supplied savestate is diagnostic evidence and cannot be
used as validation.
