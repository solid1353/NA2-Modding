# End-demo presentation

This document records how the retail NA2 (`SLPS-25837`) BTL end-demo
presentation requests, looks up, animates, draws and releases its character
resources. The controller is the pause-controller child selected by
controller `+0x0D == 1`; its end-demo label is the functional identification
recorded in
[Shared ownership and controller lifecycle](../session/pause_and_replay.md#shared-ownership-and-controller-lifecycle),
not a recovered name.

## Research coverage

- **Assigned scope:** The BTL end-demo controller's 3EYE and `enddemo`
  requests, its fifteen-entry lookup holders, selected win-animation instances,
  instance cleanup and wrapper teardown, selected-instance drawing, and the
  shared nine-entry 3EYE appearance holders and character-specific appearance
  overrides it uses.
- **Exploration depth:**
  - The resident 3EYE request/adoption/release family and its direct BTL
    calls, the controller's first two states, all fifteen lookup-table
    entries, and both actor arrays were read.
  - Split cleanup, wrapper teardown, animation-selection and appearance
    bodies were followed through their instruction bytes past decompiler
    exits.
  - Both win-animation call sites, model preparation, the draw routine and
    the shared nine-entry appearance table with all seven selector branches
    were read completely.
  - Eight win animations and their body/face providers were decoded in four
    representative clean 3EYE/1BOD1 pairs.
- **Confirmed coverage:** The controller requests the selected 3EYE file and
  `3eye/enddemo.ccs`, waits for the queue worker, adopts 3EYE and looks up
  `enddemo`. Its lookup holders select win animations from 3EYE together with
  palettes, a texture and body/face models from 1BOD1. The win tracks bind
  external body/face providers through local parent links; instantiated
  targets reach drawing and are released separately from the borrowed lookup
  arrays, `enddemo` and the 3EYE container. Appearance selection uses separate
  shared texture/palette holders, with character-specific exceptions.
- **Unresolved or untested:** Direct consumption of the controller's cached
  lookup slots 5..14 is unproved outside the bounded consumer scan; the
  established animation-driven attachment path does not require it. The
  remaining nine controller states, the exact visible phase, and
  player-facing naming of the controller states are not established.
- **Deliberate exclusions and overlap:** Selector dispatch, the controller
  lifecycle and its pause-suppression writes belong to
  [Pause and replay](../session/pause_and_replay.md#proven-btl-suppression-writers). The
  3EYE/3PCT filename tables and the 3EYE-to-1BOD1 file dependency belong to
  [Character asset tables](../../game/character_assets.md#ccs-format). Generic
  target construction and bone binding belong to
  [Model and skeleton runtime](../../runtime/rendering/model_runtime.md#animation-binding-to-scene-nodes),
  playback to [Animation runtime](../../runtime/animation_runtime.md#descriptor-and-player-separation),
  material binding to
  [Texture and material runtime](../../runtime/rendering/texture_material_runtime.md#material-binding-and-coordinate-updates),
  and packet ownership to [Render submission](../../runtime/rendering/render_submission.md).
  CCS loading and queue contracts belong to
  [Resident CCS runtime](../../game/files/ccs_runtime.md#loading-and-cancellation).
- **Evidence limitations:** All findings are static reads of the clean
  resident ELF, BTL overlay and CCS files. The selected 3EYE payload reads
  establish eight animations' body/face links, not a complete geometry
  decoding or every character-specific attachment. Direct-call searches do not
  exclude indirect callers.

## Evidence and address conventions

Inputs and preserved/live/raw address conversion follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
BTL addresses are given as live addresses with their preserved addresses where
the source differs. CCS files were gzip-decompressed in memory.

## Request and lookup

**Observation:** This family is separate from the nine per-side request slots.
`FUN_001E90F0(character_ID)` constructs `3eye/<3EYE basename>` in global
path buffer `0x006B2880`. A published container is adopted directly into
global handle `0x0060763C`; a miss queues the file and nulls that handle.
`FUN_001E9180(character_ID)` only performs lookup when the global handle is
zero. `FUN_001E91E0` destroys a nonzero handle and clears it. The request
helper itself does not start the queue worker or release a formerly held
different container before assigning its new result.

Direct `jal` calls to these helpers occur only in BTL among the resident ELF,
BTL and ETC: the request at preserved `0x0076CC50` / live `0x0076CC90`,
adoption at preserved `0x0076CD88` / live `0x0076CDC8`, and releases at
preserved `0x0076F75C` / live `0x0076F79C` and preserved `0x0076FA98` / live
`0x0076FAD8`. Indirect calls and other programs are outside that search.

**Observation:** The controller at preserved `0x0076CBC0` / live
`0x0076CC00` uses an eleven-target state table at live `0x008CADA0`
(preserved bytes `0x008CAD60`). The first two targets are live
`0x0076CC60` and `0x0076CCF0`. Its first state requests both the selected
3EYE file and `3eye/enddemo.ccs`, starts the queue worker, and advances its
state. The next state waits for no active worker, clears the queue, adopts
3EYE, looks up the separate `enddemo` container into controller `+0x160`,
and calls setup at live `0x0076C670` (preserved `0x0076C630`). These calls
and stores are corroborated by preserved bytes
`0x0076CC20..0x0076CDB7`; the decompiler cannot recover these states from
its split indirect dispatch. This establishes ordering without assigning a
player-facing name to the controller state or asserting successful loads.

The setup publishes both characters through `FUN_001E1530` (see
[Character asset tables](../../game/character_assets.md#fun_001e1530--publish-six-match-asset-selections)),
then calls `FUN_001E19D0` for two lookup holders at controller
`+0x150/+0x158`, with actor indices 0 and 1 and entry count 15. The complete
table is at live `0x008CA010..0x008CA087`, preserved
`0x008C9FD0..0x008CA047`:

| Lookup slots | Provider family | Name templates |
| --- | --- | --- |
| 0, 1 | 3EYE, family 2 | `ANM_3xxxwin00`, `ANM_3xxxwin10` |
| 2, 3 | 3EYE, family 2 | Both `ANM_3xxxeye00` |
| 4 | 3EYE, family 2 | `ANM_3xxxnut00` |
| 5 | 1BOD1, family 1 | `CLT_1xxxbodyc1` |
| 6, 7 | 1BOD1, family 1 | Both `CLT_1xxxbod2c1` |
| 8, 9 | 1BOD1, family 1 | `CLT_1xxxbodyc2`, `CLT_1xxxbod2c2` |
| 10 | 1BOD1, family 1 | `TEX_1xxxbod2` |
| 11..14 | 1BOD1, family 1 | `MDL_1xxx00t0 body`, `MDL_1xxx00t0 eye1`, `MDL_1xxx00t0 eye2`, `MDL_1xxx00t0 mou1` |

`FUN_001E19D0` allocates the holder's pointer array, takes the actor's
published container from `0x006B26D0 + family*8 + actor*4`, and replaces
the template's literal `xxx` with the corresponding three code bytes from
`0x006B2710 + family*8 + actor*4` through `FUN_001E16A0`. For this table's
family-1/family-2 entries, object lookup is optional
`FUN_001A8F00(container,name,1)`; a missing container or name yields a zero
slot. A zero/nonzero slot therefore has a different contract from common
fighter setup's required model lookup. The two actor arrays borrow resource
pointers; they do not load files or materialize each returned model.

## Cleanup and teardown

**Observation:** Instance cleanup at live `0x0076C2E0`, preserved
`0x0076C2A0`, releases the controller's animation instances, including all
eight pointer slots `+0x164..+0x180` and its three `0x14`-stride instances
at `+0x198`. It then destroys its separate `enddemo` container at `+0x160`.
The full byte range `0x0076C2A0..0x0076C62F` corroborates continuation
after each destructor call; the decompiler misleadingly ends those branches
at the calls. Wrapper teardown at live `0x0076F840`, preserved
`0x0076F800`, reaches that cleanup, frees the `+4` work allocations of the
selected instance's model targets retained at `+0x424/+0x428`, clears both
target pointers, then destroys and clears the selected `+0x41C` player through
`FUN_001B7570(player,1)`. Preserved bytes `0x0076F800..0x0076F937`
corroborate this continuation and the later destruction of the two lookup
holders through live `0x0076F980`, preserved `0x0076F940`. The holder destructor
receives delete flag `-1` from the array teardown and frees only its pointer
array. The wrapper completion paths finally call
resident `FUN_001E91E0` to release the selected 3EYE container. This ordering
separates instantiated controllers, borrowed lookup arrays, `enddemo`, and
the selected 3EYE handle; it does not release the 1BOD1 provider through the
lookup-holder destructor.

## Animation instances and model adoption

**Observation:** The presentation controller reads its actor index from its
configuration's byte `+0x0C`, then takes the character ID from configuration
`+0x04 + actor`. Its animation-selection helper at live `0x0076BA70`
(preserved `0x0076BA30`) receives the two holders beginning at controller
`+0x150`, selects `holder[actor][animation_slot]` through `FUN_001E19A0`,
and returns without changing the instance when that resource is zero. The
two established direct calls, preserved `0x0076D090` and `0x0076D490`,
select lookup slots 0 and 1 respectively and the `0x14`-byte instance record
at controller `+0x41C`. Its first word is the animation player; byte `+4`
is cleared on selection, and words `+8/+0x0C` retain two optional model
targets with extra working allocations. Before rebinding a nonzero resource,
the helper frees those targets' `+4` allocations and clears both retained
target pointers. This is instance work, not a container release.

**Observation:** The complete instruction range
`0x0076BA30..0x0076BFA3` continues past both allocation calls that truncate
the decompiler. It creates a `0x120`-byte player when necessary and binds the
selected animation through `FUN_001B99B0(player,animation,0)`. It then
collects that player's model targets through `FUN_001BAA20` with pattern
`MDL_*` (resident string `0x00604E50`). The ordinary appearance branch prepares
each collected model through `FUN_00198B10(model,0x2000)` and, when model
flags `+0x18 & 0x804` are nonzero, applies nonzero texture and palette choices
through `FUN_00198990` and `FUN_00198AB0`. The texture/palette choices come from
`FUN_001E1760(actor,1,appearance,out_texture,out_palette)`, which reads the
separate global lookup holders at `0x006B26A0 + family*0x10 + actor*8`
described under [Appearance resources](#appearance-resources).
Those are not the controller's fifteen-slot arrays. Therefore neither the
presence of fifteen lookup entries nor these appearance calls alone proves
direct consumption of controller slots 5..14.

**Clean-file observation:** Both `win00` and `win10` were followed in the
four representative `3NRT3EYE`, `3KNW3EYE`, `3CHY3EYE` and `3SIN3EYE`
containers. All eight animations contain typed `0x0102` tracks for their
character's body, two eyes and mouth. Those tracks select local `0x0A00`
wrapper records whose provider links name the same-code external
`#c\1???\max\1???bod1.max`. The wrappers attach the body to the local
pelvis track and the eyes/mouth to the local head track. In the corresponding
four `1???BOD1` files, the provider `0x0100` object records select the exact
`MDL_1???00t0 body/eye1/eye2/mou1` models, with the same parent names.
For example, `3NRT3EYE`'s first animation uses body wrapper ID 103,
parent ID 7 (`pelvis`) and external provider ID 104; its eye1 wrapper
ID 37 uses parent ID 35 (`head`) and provider ID 38. `win10` has separate
local wrapper IDs and parents but shares those external provider records.
This supplies a concrete attachment path independent of directly reading the
four cached model slots.

The reads were bounded to these eight animations and their matching
body/face descriptors. All eight nested animation walks ended exactly at
their declared payload ends. The selected `0x0100`/`0x0A00` payloads were
matched at aligned tag/record-ID sites and checked against the resident
parsers; no whole-file geometry decoder is claimed.

**Inference, high confidence:** A new presentation player has no pre-attached
composition list (`FUN_001B7520` clears `+0xE4` and `+0xF7`). Binding these
tracks therefore follows the animation's wrapper/provider records to create
the character's scene nodes and runtime models, then attaches them according
to the animation's local parent map. `FUN_001A29D0` builds that map from
the wrappers' parent links, `FUN_00116210` resolves their providers,
and `FUN_001BA930 -> FUN_00196B40` materializes each provider object's model.
The generic binding and hierarchy contract remains in the linked model
runtime owner. An instruction scan of preserved
`0x0076BA30..0x0076E95F` found only holder initialization/reset and the two
animation-selection arguments among direct `lw`, `sw` and `addiu` accesses
to controller `+0x150/+0x154/+0x158/+0x15C`; its sole direct
`FUN_001E19A0` call is the animation selector above. This bounds the traced
consumer family; it does not prove cached slots 5..14 unused by other code
or by a differently formed alias.

## Selected-instance drawing

**Observation:** The draw routine at live `0x0076DCF0`, preserved
`0x0076DCB0`, draws the selected instance at `+0x41C` only under controller
flag `+4 & 0x400`, and skips its whole body for state 8. It temporarily
changes the selected player's `+0x10C` node's local translation by
`(-20,+20,-70)`, calls `FUN_001BB790`, then restores all four original words
at node `+0x40..+0x4C`. Its regular animation instances use the same draw
helper with controller-selected renderers. `FUN_001BB790` traverses bound
player targets, drawing flagged type-`0x0100` nodes and type-`0x0E00` effects.
This connects animation-created character nodes to submission without
equating borrowed model descriptors with drawable instances. General target
construction, hierarchy attachment and bone rebinding remain in
[Model and skeleton runtime](../../runtime/rendering/model_runtime.md#animation-binding-to-scene-nodes);
playback and target lifetime remain in
[Animation runtime](../../runtime/animation_runtime.md#descriptor-and-player-separation),
and packet/list ownership in [Render submission](../../runtime/rendering/render_submission.md).

## Appearance resources

**Observation:** `FUN_001E13A0` creates three pairs of shared nine-entry
lookup holders at `0x006B26A0/+0x10/+0x20`, one holder per actor in each
pair. The family-1 pair uses the complete table at
`0x005C0570..0x005C05B7`; every row selects provider family 1:

| Shared slot | Resource template |
| --- | --- |
| 0 | `CLT_1xxxbody` |
| 1 | `CLT_1xxxbodyc1` |
| 2 | `CLT_1xxxbod2` |
| 3 | `CLT_1xxxbod2c1` |
| 4, 5 | Both `CLT_1xxxbodyc2` |
| 6 | `CLT_1xxxbod2c2` |
| 7 | `TEX_1xxxbody` |
| 8 | `TEX_1xxxbod2` |

This uses the same template substitution and optional object lookup as the
fifteen-entry table. Resident `FUN_0035CE20` publishes the two characters and
builds these shared holders; its callers include `FUN_001EF330` and the
cinematic callback `FUN_0035A070`. This identifies shared setup, without
equating it with the presentation controller's later local lookup setup.

`FUN_001E1760` clears both output pointers, dispatches unsigned selectors
below 7 through the seven-target table at `0x005C05C0`, and selects:

| Appearance selector | Texture slot | Palette slot | If texture slot 8 is zero |
| --- | ---: | ---: | --- |
| 0 | 7 | 0 | — |
| 1 | 7 | 1 | — |
| 2 | 8 | 2 | Retry selector 0 |
| 3 | 8 | 3 | Retry selector 1 |
| 4 | 7 | 4 | — |
| 5 | — | — | Outputs remain zero |
| 6 | 8 | 6 | Retry selector 4 |

Selectors outside that dispatch leave both outputs zero. Instructions
`0x001E1760..0x001E199F` establish the output order and retry branches.
The 3EYE caller passes family 1, applies the chosen texture before the palette,
and skips each zero output independently. Model flags and character-specific
selectors restrict which collected models receive these changes; this is
not a blanket replacement of every body/eye/mouth material. The generic
binding behavior belongs to
[Texture and material runtime](../../runtime/rendering/texture_material_runtime.md#material-binding-and-coordinate-updates).

**Observation:** The selector at live `0x0076E180`, preserved `0x0076E140`,
compares character ID and exact model name for the selected win slots 0/1
when the model flags include `0x804`. Return 0 skips the ordinary appearance
branch, return -1 enters a separate palette lookup, and returns 10/11 allocate
two retained `0x30`-byte model-work blocks. Representative complete branches
establish:

- ID 18 returns -1 for `MDL_1krs00t0 body` and `MDL_1mnt00t0 mant`,
  but the separate palette helper returns zero for that ID, leaving these
  models without this appearance override.
- ID 60 skips `MDL_1krs00t0 body`, `MDL_2kar00t0 bod2` and
  `MDL_1kar00t0 mant`; its `MDL_1mnt00t0 mant` and
  `MDL_1kar10t0 mant2` receive the retained work blocks.
- ID 62 skips `MDL_st5600t0 bod`, `MDL_st5600t0 hed` and
  `MDL_st5700t0 hed`. Its `MDL_st5601t0 bod` instead selects
  `CLT_st56bodyc1` from `3chy3eye` through the helper at live
  `0x0076E7C0`, preserved `0x0076E780`.

For a model with `0x804` clear and appearance bits `& 5` nonzero, the helper
at live `0x0076E870`, preserved `0x0076E830`, additionally handles ID 17's
`MDL_3sinpok01` and `MDL_3sinpok02`. It looks up `3sin3eye`, then chooses
`CLT_3sinbodyc2` when appearance bit 4 is set, otherwise `CLT_3sinbodyc1`.
The exact names were read at preserved `0x008A60E0..0x008A6537`;
instructions `0x0076E780..0x0076E957` corroborate both palette helpers past
their split decompiler exits. These special resources come from 3EYE itself;
the shared family-1 appearance table remains a distinct provider.
