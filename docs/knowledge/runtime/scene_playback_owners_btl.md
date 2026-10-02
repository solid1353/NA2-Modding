# BTL scene playback owners

This document classifies the direct animation-seek call sites in the retail
NA2 (`SLPS-25837`) `BTL.BIN` overlay by owning object, phase and playback
policy, together with the advance, submission and release paths each owner
needs to explain its seeks. The playback families, the streamed worker, the
direct-call census and the resident and ETC owners belong to
[Scene playback callers and owners](scene_playback_owners.md). Addresses are
preserved BTL addresses unless marked live, following the
[address conventions](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** every classified direct seek site in `BTL.BIN`, with the
  owner's gates, step producers, advance, submission and release paths where
  they determine what the seek means.
- **Exploration depth:** 189 of the 214 direct BTL seek byte sites are
  classified below; the other 25 remain leads in the
  [direct-call census](scene_playback_owners.md#direct-call-census-and-analysis-limits).
  Each classified site was read in decompilation and in the surrounding
  instruction bytes, including bytes outside analyzed function bodies.
  Resident vtables and type records identify classes where present. BTL
  advance sites were followed only where an owner's seeks depend on them.
- **Confirmed coverage:** the per-owner policies in the
  [summary](#summary): omitted advance versus zero step, explicit repeat by
  seek, initial-frame choice, saved-frame restoration, threshold latches and
  fades, captured-pose reuse, typed-resource construction and cleanup,
  even-counter advance gates, linked-node destruction, array descriptor
  transitions, and buddy descriptor-change suppression. KIB repeats its
  embedded player after completion within one state-2 update; TYV fading
  states still reach ordinary advance; raw array-update branches contradict a
  decompiler-only advance gate; a typed caller's terminal counter check
  follows its playback operation. Primary descriptor setters and counter
  transitions do not establish the inherited player's full schedule.
- **Unresolved or untested:** the 25 unclassified BTL seek leads; the
  allocation, advance schedule and release of the inherited primary player
  `+0x320`; GAR's continuing update body; playback of the objects created by
  the SKN/SKM factories; linked-node flag bit 1; selection of typed-resource
  type 3 and derived virtual initialization of types 3/4; array upstream
  scheduling; all producers of the buddy outer gate `+0xF2`; indirect callers;
  dispatcher order and cadence; and the BTL advance owners not reached through
  a seek site.
- **Deliberate exclusions and overlap:** playback families, census totals and
  resident/ETC owners belong to
  [Scene playback callers and owners](scene_playback_owners.md); evaluation
  algorithms to [Animation runtime](animation_runtime.md); stage-object
  contact, timer, geometry and lifetime algorithms to
  [Stages](../gameplay/stages/stages.md#animated-and-breakable-background-evidence);
  CCS parsing and resource lifetime to
  [CCS runtime](../game/files/ccs_runtime.md). High-level character or action
  names are not assigned from resource prefixes.
- **Evidence limitations:** static evidence only. Direct-caller searches are
  bounded exact-JAL byte searches and do not enumerate indirect dispatch.
  Split decompiler functions and false no-return boundaries required raw-byte
  corroboration. No wall-clock cadence or observed instance behavior is
  established.

## Summary

Seek counts are direct seek call sites in each section. "Frame 1" is the seek
target `0x100`; every listed seek also carries the
[active-blend exception](scene_playback_owners.md#playback-families).

| Owner | Seek sites | Policy class |
| --- | ---: | --- |
| [Stage objects](#btl-stage-owner-playback): `ccBgBreak*`, `ccBgTransAnm`, `ccCraneTruck`, and two earlier reset owners | 22 | Scene-rate advance; trigger, end and rebirth requests at zero, frame 1 or `(F-1)`; construction frames |
| [Additional local contracts](#additional-btl-local-owner-contracts) | 19 | Whole-frame adapter, descriptor and controller selectors, fixed frames with step zero, shared-player draw restoration |
| [Requested-state sequencing](#btl-requested-state-and-endpoint-sequencing) | 11 | State-selected descriptor at frame 1; endpoint request followed by advance |
| [Byte selectors](#btl-byte-selectors-and-frame-one-requests) | 10 | Byte-selected descriptor at frame 1 |
| [Gauge players](#btl-threshold-latched-gauge-players) | 3 | Threshold-latched activation at frame 1; fade-out reset |
| [Captured poses and typed owners](#btl-captured-poses-and-typed-owners) | 2 | Captured whole-frame sample; typed-resource construction at frame 1 |
| [Input and endpoint requests](#btl-input-and-endpoint-request-owners) | 5 | Input-armed zero requests; endpoint and counter-derived requests |
| [Recreation and restoration](#btl-player-recreation-and-descriptor-restoration) | 12 | Recreate and restore a saved frame; descriptor change at frame 1 or `(F-1)` |
| [Frog `ccSkillJRY001Frog`](#btl-wrapped-frog-player) | 1 | State transition at frame 1 with conditional rate write |
| [`ccSkillGUW001`](#btl-guw-embedded-player) | 1 | Selector-gated frame 1 on an embedded player |
| [GAR and GAV](#btl-gar-and-gav-primary-player-transitions) | 5 | Primary-player state transitions at frame 1 |
| [`ccSkillTOV001`](#btl-tov-variant-selected-primary-player-seeks) | 7 | Variant-selected state transitions at frame 1 |
| [`ccSkillASM001`](#btl-asm-requested-state-primary-player-seeks) | 4 | Requested-state transitions at frame 1 |
| [`ccSkillKIB001New3`](#btl-kib-primary-and-looping-embedded-player) | 6 | State transitions at frame 1; completion-driven embedded repeat |
| [SKN and SKM](#btl-skn-and-skm-counter-gated-primary-players) | 2 | Counter-gated transition at frame 1 |
| [TYV parent and object](#btl-tyv-parent-and-allocated-player-object) | 3 | Counter-gated transitions and allocated-object setup at frame 1 |
| [`ccSkillObjSawarabi`](#btl-sawarabi-embedded-player-array) | 2 | Record-state array: setup and delayed transition at frame 1 |
| [ZBZ and KMV](#btl-zbz-and-kmv-counter-gated-primary-players) | 4 | Counter-gated transitions at frame 1 |
| [`ccSkillObjWaterDragon`](#btl-water-dragon-embedded-player) | 2 | Setup at frame 1; advance then frame-1 request in an explicit update |
| [`ccSkillANB000`](#btl-anb-embedded-and-associated-players) | 8 | Range-index and requested-state descriptor changes on embedded, associated, linked and controller players |
| [`ccSkillFOR000`](#btl-for-embedded-player-pair) | 2 | Activation pair at frame 1 |
| [`ccSkillTND001`](#btl-tnd-embedded-player-group) | 3 | Randomized initial frames; frame 1 with completion latch |
| [`ccSkillCHY000`](#btl-chy-supplementary-player) | 1 | Construction request at cursor zero |
| [Wall and gate players](#btl-wall-and-gate-players) | 4 | Construction at frame 1; endpoint `(F-1)`; even-counter advance gate |
| [Linked-player owners](#btl-linked-player-owners) | 30 | Construction at cursor zero; list advance ignores completion |
| [Descriptor-switched array](#btl-descriptor-switched-player-array) | 5 | Setup at frame 1; transitions at frame 1 or a randomized frame |
| [Buddy resources](#btl-buddy-resource-descriptor-changes) | 15 | Descriptor replacement at frame 1; one-invocation advance suppression |
| Total | 189 | |
## BTL stage-owner playback

This section classifies the 20 direct seek candidates in preserved
`0x006C4910..0x006D3570`, including bytes outside Ghidra's analyzed function
bodies. Class/factory identification and contact, timer, geometry and lifetime
algorithms belong to [Stages](../gameplay/stages/stages.md#animated-and-breakable-background-evidence).
Here the class labels identify the playback owner; they do not duplicate
those algorithms. All seek arguments in this table use flag 0.

| Owner / preserved body | Increment or reset phase | Preserved seek sites |
| --- | --- | --- |
| `ccBgBreakObjectBattle`, trigger `0x006C4770`, update `0x006C4A90` | Trigger changes active model index `+0x30` in list `+0x28`, requests zero for a selected model before a finite threshold, and clears completion `+0x180`. Update writes step `256 * scene.float(+8)` and records end. With threshold `-1`, end of active index 1 switches back to index 0 and requests `(F-1)<<8`. | `0x006C4910`, `0x006C4F8C` |
| `ccBgBreakObjectBattleAnm`, trigger `0x006C57C0`, update `0x006C5B20` | Parallel owner uses list/index `+0x3C/+0x44` and completion `+0x190`. Trigger requests zero; update writes step `256 * owner.float(+0x34) * scene.float(+8)`. End of index 1 with config `-1` switches to index 0 and requests `(F-1)<<8`; its timed rebirth branch separately requests frame 1 and clears completion. | `0x006C5998`, `0x006C5FF8`, `0x006C60C8` |
| Same animation-break owner, parser `0x006C6310` | Per-player construction binds the selected animation, requests configured whole frame `<<8`, then performs one unsigned-default-step advance/composition. | `0x006C6590` |
| `ccBgBreakDollBattle`, update `0x006C6900` (live `0x006C6940`) | Nonzero cooldown byte `+0x190` decrements and returns before playback. Contact acceptance resets index `+0x30` to zero and requests zero. Later advance uses `256 * scene.float(+8)`; end-driven list transitions request frame 1 at intermediate indices, or zero when returning to index 0. | `0x006C6CF0`, `0x006C6EF0`, `0x006C6F4C`, `0x006C6F94`, `0x006C6FEC` |
| `ccBgTransAnm`, parser `0x006C7C90`, update `0x006C80A0` | Setup requests configured frame or `FUN_00180210(F-1)<<8`. Update requires the battle global to be nonnull, writes `cached_default_step(+0x60) * multiplier(+0x5C) * scene.float(+8)` to player `+0x94`, then advances/composes before its proximity/render-value handling. | `0x006C7F0C`, `0x006C7F34` |
| `ccBgBreakObjectRebornBattle`, update `0x006CDD40` | Runs base playback first; timed rebirth selects list index zero, requests frame 1, and clears completion `+0x180`. | `0x006CDDE4` |
| `ccBgBreakObjectMoveBattle`, update `0x006CEAD0` | Runs mover and base playback; reset-delay expiry selects list index zero, requests frame 1, clears completion `+0x180` and break count `+0x34`. | `0x006CEB70` |
| `ccCraneTruck`, update `0x006D0040` | Own player `+0x2C` advances in both inspected state branches. Completion of the alternate animation rebinds the default, advances/composes it once, then requests frame 1 on the separately owned linked break object's list-zero player and clears that object's playback/count. The sought player is not the crane player. | `0x006D022C` |
| `ccBgBreakObjectBattleChandelier`, trigger fragment `0x006D2370`, update `0x006D2DB0` | Trigger requests zero on selected list `+0x3C`, clears completion `+0x2E0`. Update derives `256 * owner.float(+0x34) * scene.float(+8)`, advances/composes, and has separate `(F-1)<<8` list-return and frame-1 timed-rebirth requests. | `0x006D245C`, `0x006D2F9C`, `0x006D306C` |
| Same chandelier owner, parser construction bytes | Allocates/binds each player, requests configured frame `<<8`, then advances/composes once before installing the player in the list. | `0x006D3570` |

**Observation:** decompilation truncates both base break updates after the
combatant lookup `FUN_003769C0`, incorrectly presenting a return where retail
bytes continue contact processing. Bytes `0x006C4AD0..0x006C4AFF` and
`0x006C5B60..0x006C5B87` show use of the returned combatant pointer.
Contact-tail bytes `0x006C4DC0..0x006C4E7F` and
`0x006C5E30..0x006C5ECF` then join the recorded rate/advance tails.
Consequently the initial count/flag comparisons select whether contact
processing is needed; the truncated decompiler's apparent returns cannot
establish a playback pause. The recorded formulas are reached through those
tails or their direct shortcut branches.

**Evidence:** decompilation/disassembly of the table's preserved update
and trigger functions; raw construction bytes
`0x006C6500..0x006C65FF`, doll transition bytes
`0x006C6CC0..0x006C702F`, transition-animation setup
`0x006C7EB0..0x006C7F9F`, crane completion/reset
`0x006D0180..0x006D024F`, and chandelier setup
`0x006D3440..0x006D35AF`. Resident vtable `0x005DDA70` bytes confirm doll
update slot `+8 = live 0x006C6940`.

Two earlier BTL seek owners are structurally separate. `FUN_006B6BF0`
changes counter `+8`, and when its clamped value exceeds 1 requests frame 1
on player `+0x40`, arms owner flags and sets that player's step to zero.
`FUN_006C0340` clears owner state, requests frame 1 on player `+0x24`, and
resets its two associated records. Their seek sites are preserved
`0x006B6C7C` and `0x006C0378`; decompilation establishes explicit
initialization/reset phases, but their complete scheduling chains are not
established here.

## Additional BTL local owner contracts

This section covers the analyzed seek-containing functions above
preserved `0x00750000`. The rows below retain complete local contracts or
instruction-corroborated fragments. A fragment does not establish its
enclosing action's entry, full scheduling gate, or character identity.

| Preserved helper/body | Owner, operation and phase |
| --- | --- |
| `FUN_00750D70`, seek `0x00750D94` | Thin whole-frame adapter: checks passed player `+0xFC`, shifts the passed frame left 8, and calls seek without changing argument register `a2`. Flags come from its caller, despite the decompiler omitting that third parameter. |
| Actual helper `FUN_007B8AB0`, seek `0x007B8AF4` | Descriptor-selection method takes owner and index, binds player `+0x320` to descriptor `owner+0x100C+index*4` with blend duration zero, then requests frame 1 with flag 0 when valid. Complete bytes recover the entry and target omitted by the split `FUN_007B8AF0` decompilation. It has no advance. |
| Fragments `FUN_007780B0`, `FUN_007781D0`, seeks `0x00778134`, `0x0077822C` | Reach a player at associated owner `+0x158 -> +0xB34`. Request `(current_integer+1)&0xFFFF` or `(current_integer-1)&0xFFFF`, shifted left 8, with distinct `F-2`/`F-1` upper comparisons. These are whole-frame seeks, not negative deltas passed to advance. Complete entry/underflow guarantees remain unresolved. |
| `FUN_007AD980`, `FUN_007CDDD0`, seeks `0x007AD9C0`, `0x007CDE10` | When owner byte `+0xF10` is zero, request respectively frame 20 or frame 50 on player `+0x320`, then write that player's step zero. This explicitly combines pose selection with stopped increments. |
| `FUN_007B3E40`, seek `0x007B3E6C` | [Wall-player endpoint request and counter gate](#btl-wall-and-gate-players). |
| `FUN_007CAC50`, seek `0x007CAC7C` | [Gate-player endpoint request and counter gate](#btl-wall-and-gate-players). |
| Actual selector `FUN_007BB0A0`, seek `0x007BB0F4` | [Descriptor selection and pointer substitution](#btl-player-recreation-and-descriptor-restoration). |
| `FUN_007DF340`, seeks `0x007DF3E4/4F8/608` | [Requested-state descriptor selection](#btl-requested-state-and-endpoint-sequencing). |
| `FUN_007E0620/0ED0/1B20`, seven seeks | [Related descriptor and state-transition gates](#btl-requested-state-and-endpoint-sequencing). |
| `FUN_0080DBB0`, seek/advance `0x0080E204/224` | [Endpoint request followed by ordinary advance](#btl-requested-state-and-endpoint-sequencing). |
| `FUN_007BD200`, seek `0x007BD3A8` | [Wrapped frog-player state transition and lifetime](#btl-wrapped-frog-player). |
| Actual selector `FUN_007EDEA0`, seek `0x007EE14C` | [GUW embedded-player selection, enable gate and lifetime](#btl-guw-embedded-player). |
| `FUN_007EFCD0`, seek `0x007EFF1C` | [Reused-player descriptor request after a virtual callback](#btl-player-recreation-and-descriptor-restoration). |
| `FUN_007F56E0`, actual `FUN_007FAC70/7FCA00`, `FUN_00802320`, ten seeks | [Byte-selector frame-1 requests](#btl-byte-selectors-and-frame-one-requests). |
| `FUN_007FF270`, seek `0x007FF2B8`; actual `FUN_00801C10`, seek `0x00801C58`; `FUN_00806050`, seek `0x00806098`; `FUN_00812EB0`, seek `0x00812EF8` | All take owner `a0`, controller `a1` and selector `a2`, bind the referenced player at `controller+0x120` with blend duration zero, request frame 1 with flag 0 when valid, then clear controller counter `+0x158`. They index descriptors with the selector's low byte at respectively `owner+0x103C`, `owner+0xFFC`, `owner+0x1000` and `owner+0x10E0`. None of the full bodies directly advances or writes the player step; their referenced-player lifetimes remain unresolved. The fourth belongs to `ccSkillSIN001`; its state setter calls it on controller `owner+0x200`, with index 1/2 for requested signed-halfword state 1/2. |
| `FUN_007FFB50/800290`, seeks `0x007FFBF8/7FFC80/800304` | [TND embedded-group initial frames and completion latches](#btl-tnd-embedded-player-group). |
| Actual `FUN_00805660`, seeks `0x00805A60/AC8` | [FOR embedded-player activation and immediate update](#btl-for-embedded-player-pair). |
| Actual entry `FUN_007DFD60`, seeks `0x007DFDB0`, `0x007DFE38` | Writes owner state word `+0x1118` to 8, binds player `+0x320` to descriptor `+0x1100` with blend duration zero and requests frame 1 with flag 0 when valid. After clearing owner word `+0x358` and conditional primary-player substitution, it requests frame 1 on the same player again, without an intervening bind or direct advance. Byte `+0x389` and the association predicate gate substitution, rather than either valid-player seek. The complete body has no direct advance or player-step write; upstream scheduling and descriptor lifetime remain unresolved. |
| `FUN_00814230`, advance/seek `0x00814414` / `0x00814440` | [Water Dragon embedded-player transform/update and separate frame-one request](#btl-water-dragon-embedded-player). |
| `FUN_00854D40`, four seeks `0x00854D9C`, `0x00854DD8`, `0x00854E14`, `0x00854E50` | Setup binds four embedded players at owner `+0x1DC0`, `+0x1CA0`, `+0x1EE0`, `+0x2010`, then requests frame 1 for each valid player. |
| `FUN_00855160`, seek `0x00855278` | Submission loop, gated by byte `+0x217C == 0`, iterates 20 instance records of stride `0xE0`. For each record with nonzero float `+0xB00`, uses player `+0x1DC0` for instance 0 and shared player `+0x1CA0` for the others, writes instance transform/opacity, seeks to signed owner halfword `+0x1C72<<8`, then calls `FUN_001BB790`. This confirms sequential sharing for rendering; this loop does not advance the logical frame. Its separate frame producer is described below; high-level owner identity remains unresolved. |
| `FUN_0085A0F0`, seek `0x0085A18C` | With selector argument 1 and owner byte `+0xBAA == 1`, writes player `+0xAF0` step zero and requests frame 1; the alternate byte branch writes step `0x100`. This is a local state-dependent rate/pose policy. |
| Fragment `FUN_00865470`, seek `0x008654EC` | Selector argument 2 updates the owner player and requests frame 9 on player `+0x320`. Full action entry/state identity remains unresolved. |

**Evidence:** decompilation of the listed functions,
complete instruction sequence for the adapter `0x00750D70..0x00750DA8`,
descriptor-selector bytes `0x007B8AB0..0x007B8B0F`, complete transition
bytes `0x007DFD60..0x007E015F`,
embedded-player disassembly `0x008143D4..0x00814448`, draw-loop disassembly
`0x00855160..0x008552A0`, and bytes
`0x007BB0A0..0x007BB18F`. The whole-frame adapter, descriptor selector
and draw-loop call show why API-level caller identity alone cannot
distinguish update from explicit frame selection or submission.
The four controller selectors use complete bytes
`0x007FF270..0x007FF2DF` and `0x00801C10..0x00801C7F`,
plus `0x00806050..0x008060BF` and `0x00812EB0..0x00812F1F`,
which recover the seek/clear tail omitted by the analyzed bind-only bodies.
The fourth's complete state-setter bytes `0x00812DB0..0x00812EAF`
preserve the selector register through both calls; a direct-JAL search
for live `0x00812EF0` finds only those two sites,
`0x00812E3C/2E68`. Resident vtable `0x005EB320`
and preserved type/name bytes `0x008CF398..0x008CF3AF` /
`0x008BBC38..0x008BBC47` establish the `ccSkillSIN001` identity.

The shared draw owner's separate producer is `FUN_00855040` (live
`0x00855080`), reached by resident vtable `0x005E2930` slot `+0x10`.
It increments signed owner halfword `+0x1C72` by one per invocation and
stores 1 when the new signed value reaches the descriptor frame count
through `owner+0x1D30`. It also clears byte `+0x217C` before its state helper,
and advances/composes the two other embedded players at `+0x1EE0/+0x2010`
using each player's unsigned `+0x94`. The logical whole-frame producer and
those ordinary fixed-point players therefore have different step policies
inside one owner. **Evidence:** complete decompilation and bytes
`0x00855040..0x0085515F`, plus resident vtable bytes
`0x005E2930..0x005E297F`. The method's invocation frequency and helper-driven
draw gate are not established by its direct playback calls.

## BTL requested-state and endpoint sequencing

**State-selector observation:** complete preserved `FUN_007DF340`
takes an owner and selector, stores the request at `+0x112C`, clears
`+0x1130/+0x1134`, then dispatches selectors `0..8`. The jump table's
encoded live branch addresses recover three binding/seek paths omitted
by the split decompiler. Every path below binds owner player `+0x320`
with blend duration zero, requests frame 1 with flag 0 when `+0xFC`
is valid, and clears owner word `+0x358` afterward.

| Requested selector | Stored state `+0x1118` / selected descriptor | Preserved seek |
| --- | --- | --- |
| 1 / 2 / 3 | State 4 / 1 / 7 respectively; descriptor `owner+0x10E0+state*4` | `0x007DF4F8` |
| 4 or 5 | State 10; descriptor `+0x1108` | `0x007DF3E4` |
| 7 | State 13; descriptor `+0x1114` | `0x007DF608` |

Selectors 0/6 go to the common return; selector 8 takes a separate geometry
path without one of these direct seeks. Unsigned selectors outside `0..8`
skip the dispatch after the initial request/counter writes. Byte `+0x389`
and the associated-object predicate gate subsequent primary-player
substitution, rather than the preceding valid-player requests. The complete
method contains no direct ordinary advance or player-step write. A bounded
JAL search finds seven calls to its live entry `0x007DF380`: six in
`FUN_007DEDF0` at `0x007DEE44/68/7C/90/A4/B8`, and one at
`0x007DFBF0` in `FUN_007DFA80`. The first caller consumes pending
word `+0x1120` and passes selectors 0/8/7/4/5/6; its other branch invokes
the separately classified state-8 transition. The latter call selects 2 or
3 through preceding geometry comparisons. Full upstream scheduling and
descriptor retention remain unresolved.

Three related complete methods supply seven further direct seek contracts.
All use a zero-blend bind, seek flag 0 and a valid-track guard. None of
these bodies directly advances the player or changes its step:

| Preserved method / seek | Gate and descriptor operation | Order and retained ownership |
| --- | --- | --- |
| `FUN_007E0620`, `0x007E0818` | After earlier helper/virtual handling, binds player `+0x4D0` to associated `+0x4CC` descriptor-array entry 5 (`+0xB84` array, byte offset `+0x14`), or null when its predicate is zero; requests frame 1 when valid. | The preceding direction comparison can set byte `+0x1189` and copy rotation, but both branches select entry 5. Later byte `+0x539` plus association checks gate primary-player substitution. Owner pending word `+0x1120` is then set to 3. |
| `FUN_007E0ED0`, `0x007E0F74/1024/10D4` | With owner word `+0x358 !=0`, states `+0x1118` 1/4/7 become 2/5/8, bind descriptors `+0x10E8/+0x10F4/+0x1100` respectively and request frame 1. | The method saves/increments counter `+0x1130` before this gate. Each transition clears `+0x358`; conditional primary-player substitution follows, then geometry and later substate handling continue. |
| Same method, `0x007E16F0` | Later substate `+0x1134 ==1`, saved old counter `+0x1130 ==0` and `+0x1124 ==-1` enable another bind/seek. Requested selector `+0x112C` 1/2/3 selects state 6/3/9; other selector values also select state 3. It binds `owner+0x10E0+state*4` and requests frame 1. | Clears `+0x358` and conditionally substitutes the primary player afterward. This later request can follow an earlier bind/seek in the same method; it is not an ordinary increment. If `+0x1124 !=-1`, this branch writes pending request `+0x1120 =6` instead of seeking. |
| `FUN_007E1B20`, `0x007E1D7C` | Substate `+0x1134 ==0` and saved old counter `+0x1130 ==15` select state `+0x1118 =11`, bind descriptor `+0x110C` to player `+0x320` and request frame 1. | Initial counter increment and geometry/virtual work precede the bind. Clears `+0x358`, then performs conditional substitution and other owner callbacks before incrementing substate to 1. |
| Same method, `0x007E1FD4` | The common tail requires current substate 1 or 2, state `+0x1118 ==11` and `+0x358 !=0`; it selects state 12, binds descriptor `+0x1110` and requests frame 1. | Clears `+0x358` and conditionally substitutes the primary player. The gate is checked after the earlier substate branches, so its current fields must not be replaced with their entry values. No allocation or release occurs in either direct seek sequence. |

The associated-object predicate and mapping bytes in these methods do not
replace their local state gates. Rebinding a retained player is also distinct
from releasing it; the complete upstream schedule and backing-descriptor
retention for this family remain unresolved.

**Endpoint/advance observation:** complete preserved `FUN_0080DBB0`
first prepares position and transforms, then obtains owner player `+0x320`.
A valid track requests `(F-1)<<8` with flag 0 at `0x0080E204`, immediately
followed by another valid-track check and ordinary advance at
`0x0080E224`, using unsigned player `+0x94`, third argument zero and
composition. There is no intervening bind or local step change. This is an
endpoint request followed by playback in the same invocation; the descriptor
end/loop policy and active-blend seek exception still apply.

Owner ID `+0x56C ==0x8F`, associated byte `+0x61` bit 3, byte `+0x389`
and association checks choose transform preparation and conditional pointer
mapping in the prefix. The raw branches converge before the seek/advance
pair; the decompiler's apparent returns at association calls do not establish
a playback gate. Later matrix copies, geometry corrections and secondary
player substitution continue after the pair. A bounded direct-JAL search
finds exactly two callers at `0x00809624` and `0x0080C7E8`; the first
then increments owner halfword `+0x1038`, while the second continues two
local object passes. Both calls belong to state-4 paths of the
[ANB owner](#btl-anb-embedded-and-associated-players), whose section
records their surrounding gates.

**Evidence:** decompilation of `FUN_007DF340/380` and
`FUN_0080DBB0/DBF0`; complete bytes `0x007DF340..0x007DF89F`
and `0x0080DBB0..0x0080E97F`, preserved selector tables
`0x008CD690..0x008CD6D3`, caller prefix `0x007DEDF0..0x007DEF2F`,
geometry-call region `0x007DFB80..0x007DFC4F`, and caller regions
`0x008095D0..0x0080966F` and `0x0080C7A0..0x0080C84F`.
Neither direct-caller search enumerates indirect dispatch. The seven related seeks use decompilation of
`FUN_007E0620/0ED0/1B20` and complete bytes
`0x007E0620..0x007E0A1F`, `0x007E0ED0..0x007E17AF`
and `0x007E1B20..0x007E205F`. The second method's saved counter and
later substate checks are confirmed by its continuing raw tail.

## BTL byte selectors and frame-one requests

**Observation:** the first three complete selector bodies store the low byte
of their incoming selector at owner `+0xFF0`; the fourth reads stored byte
`+0x18F3`. Each listed branch binds the existing
owner player `+0x320` with blend duration zero and requests frame 1 with
flag 0 when player `+0xFC` is nonzero. None of the complete bodies contains
a direct ordinary advance or a player-step write. The branches' virtual and
helper calls remain separate from this direct-call classification.

| Actual preserved entry / seek sites | Selector branch and binding | Subsequent local work |
| --- | --- | --- |
| `FUN_007F56E0`, `0x007F5788` | Selector 2 calls virtual slot `+0x17C`, then binds descriptor `+0x1000` and requests frame 1. Selectors 0/1/3 and other byte values do not reach this direct seek. | Calls three local helpers after the valid-track check. The full body does not return at the bind, despite the decompiler's apparent exit. |
| `0x007FAC70`, `0x007FAF64/7FB0C8` | Selector 3 performs earlier record and virtual handling, binds descriptor `+0xFF8`, then seeks at `0x007FAF64`. Selector 4 calls virtual slot `+0x17C`, binds descriptor `+0xFF4`, then seeks at `0x007FB0C8`. Other byte selectors skip both direct seeks. | Each branch clears word `+0x358` after its valid-track check. Selector 3 continues resource lookup/local-object creation after its seek; selector 4 reaches the common footer. |
| `0x007FCA00`, `0x007FCC74/CCD4` | Selector 3 performs earlier virtual/helper handling, binds descriptor `+0xFFC`, then seeks at `0x007FCC74`. Selector 4 calls virtual slot `+0x17C` and a local helper, binds descriptor `+0xFF8`, then seeks at `0x007FCCD4`. Other byte selectors skip both direct seeks. | Each branch clears word `+0x358` after its valid-track check and reaches the common footer. |
| `FUN_00802320`, `0x008023A4/E4/2424/2464/24A4` | Stored byte `+0x18F3` 0/1/2/3/4 selects descriptor `+0x100C/+0x1008/+0x1010/+0x1014/+0x1018` and the corresponding seek. Other byte values skip all five binds/seeks. | Each selected branch clears word `+0x358` after its valid-track check. The footer invokes a local helper with value `0x1028` for byte 4 or `0x1027` otherwise, including unrecognized byte values. Direct caller `0x00801BE4` follows earlier virtual handling; its complete request gate is untraced. |

The selected descriptors and players are reused slots; these selector bodies
do not allocate or destroy the animation player. Complete upstream selection,
scheduled update and backing-descriptor lifetimes remain unresolved.

**Evidence:** decompilation of `FUN_007F56E0` and split
`FUN_007FACB0/7FCA40`, with complete raw bodies
`0x007F56E0..0x007F57EF`, `0x007FAC70..0x007FB0EF`
and `0x007FCA00..0x007FCCFF`. The raw entry bytes recover the incoming
argument and low-byte dispatch omitted by the latter two analyzed fragments.
The fourth row uses decompilation of `FUN_00802320` and complete
bytes `0x00802320..0x008024FF`, with caller bytes
`0x00801B90..0x00801BFF` and one exact direct JAL match.

## BTL threshold-latched gauge players

**Observation:** preserved `FUN_0071D9B0` (live `0x0071D9F0`) is one
complete retail routine through preserved `0x0071E02C`. The analyzed
`FUN_0071D9F0` begins in its delay-slot/continuation region; it is not a
second owner. The direct call at preserved `0x0071E058` in
`FUN_0071E030` encodes live `0x0071D9F0`, resolving the caller despite the
empty analyzed caller list for `FUN_0071D9B0`. This caller orders value
update, local counters, the three-player pass, then its separate texture
offset update. No broader invocation cadence is established.

The owner keeps a fighter pointer at `+8` and three separately allocated
players. Its threshold predicate scans fighter `+0xA54` records 4 through 9
of stride `0x54`, chooses the first with nonzero `+0x10`, and compares that
record's float `+0x20` with owner float `+0x34`. A missing qualifying record
produces `-1`; activation requires `0 <= value <= owner.float(+0x34)`.
These offsets establish a predicate, not a player-facing name for its value.

| Player / latch | Activation and periodic advance | Deactivation / seek |
| --- | --- | --- |
| `+0x48` / byte `+0x50` | An inactive player requests frame 1 when the threshold predicate becomes true, then sets its latch. An already active player advances/composes using unsigned player `+0x94` before checking the predicate again. | A failed predicate clears the latch after that invocation's advance. It does not destroy or rewind the player there. |
| `+0x44` / byte `+0x51`, fade `+0x54` | Activation additionally requires the `+0x48` latch clear or that player's integer cursor plus 10 at least its descriptor frame count. It requests frame 1, sets the latch and fade 1. Active invocations advance/compose first. | A true predicate restores fade 1; a false predicate subtracts `0.1` and clears the latch at fade `<=0`. Advance continues during this fade. There is no seek at fade expiry. |
| `+0x4C` / byte `+0x52`, fade `+0x58` | Inactive activation requires a nonnull fighter with signed halfwords `+0x18E == 0` and `+0x190 == 4`; it sets latch/fade without a seek. Active invocations advance/compose first and restore fade 1 while that state comparison holds. | Otherwise fade decreases by `0.033333335`; at `<=0` the valid player requests frame 1 with flag 0 and its latch clears. |

All three advances use third argument zero and require player `+0xFC`.
Each seek uses flag 0. Activation is an owner policy separate from geometric
animation completion: this routine does not use the advance return value to
clear these latches. The reset requests retain the
[active-blend seek exception](scene_playback_owners.md#playback-families).

**Ownership observation:** setup `FUN_0071D3A0` obtains the existing
`battlegauge` container into owner `+4`; `FUN_0071D5E0` constructs the
three players through resident `FUN_0037D5B0`, which allocates `0x120`,
binds with blend duration zero and advances/composes once. Thus latch-zero
setup does not mean these players have never been evaluated. Its live name
table at `0x00899E60` contains live pointers `0x00899E30/40/50` to
`ANM_ef_gau02a`, `ANM_ef_gau01a`, `ANM_ef_gau00a`, respectively for
owner `+0x44/+0x48/+0x4C`. In the preserved mapping that table is at
`0x00899E20` and the strings at `0x00899DF0..0x00899E10`; the encoded
pointers do not receive another `0x40` adjustment.

Cleanup starts at preserved `0x0071D2B0`, not its split continuation
`FUN_0071D2F0`. It destroys and clears all three players through
`FUN_001B7570(player,1)`, releases its other local resources and does not
release container `+4` in the inspected body. The decompiler's apparent
returns after the first destructor are contradicted by the continuing raw
instructions. Clearing a latch is consequently distinct from this cleanup.

**Evidence:** decompilation of `FUN_0071D9B0`, `FUN_0071E030`,
`FUN_0071D3A0/D530/D5E0`, and resident `FUN_0037D5B0`; complete bytes
`0x0071D9B0..0x0071E02F`, cleanup `0x0071D2B0..0x0071D39F`, setup
`0x0071D3A0..0x0071D4B3`, caller `0x0071E030..0x0071E09F`, and
names/table `0x00899DC0..0x00899E4F`. Advance sites are preserved
`0x0071D9EC`, `0x0071DBB4`, `0x0071DDF4`; seeks are
`0x0071DB7C`, `0x0071DDB4`, `0x0071DE90`. The direct-JAL search for
live `0x0071D9F0` returned one BTL byte match; indirect callers are not
enumerated.

## BTL captured poses and typed owners

**Observation:** preserved `FUN_007237B0` selects the first inactive record
from a pool of signed-halfword count `pool+0`, record array `pool+4`, stride
`0x80`. A usable record has a fighter at `record+0x14` and a separately
allocated player at `+8`. The spawn path binds the fighter's current
descriptor from `fighter+0xB84[fighter.s16(+0xB8C)]` with blend duration
zero, requests `fighter.primary_player(+0xE70).u32(+0x98)<<8` with flag 0,
optionally applies the record's `+0x0C/+0x10` pair through
`FUN_001BC180`, and copies the primary player's four transform columns to
record `+0x20..+0x5F`. It stores opacity 1, fade increment `-0.1`, and sets
record byte `+0x70` bit 0. This seek samples a captured whole frame for an
instance; it is not the primary fighter's periodic increment.

The separate update at preserved `0x00723660..0x00723734` visits active
records with nonnull fighter/player and changes opacity by
`record.float(+0x64) * fighter.float(+0x1AC)`. A negative result clamps
to zero and clears active bit 0; the inspected upper comparison writes zero
for values above 1. It performs neither advance nor seek. Submission
`FUN_00723250`, called for every record by `FUN_00723740`, requires those
pointers, active bit 0 and opacity `>=0.01`; it restores the recorded
transform/opacity and calls `FUN_001BB790`, with no playback operation.
The player therefore retains the spawn-selected pose throughout the
inspected fade/update/submission paths. This is distinct from the compact
cursor wrappers, which restore a saved frame on every submission.

**Ownership observation:** `FUN_00723380` allocates/constructs the pool
array and runs setup at preserved `0x00722FA0` per record. Its raw setup
allocates an animation player of `0x120` bytes into record `+8`, with
separate local model/composition resources. Array release `FUN_00723610`
supplies live destructor address `0x00723490`, whose actual preserved entry
is `0x00723450`. Complete cleanup bytes show player destruction and pointer
clear, then the other owned resource releases and clears; the first player
destructor is not a retail early return. Fade expiry only makes the record
reusable; it does not free the player. Exact direct-JAL searches in BTL for
the spawn and fade entries' live addresses each returned zero matches.
Their indirect or higher-level scheduling remains unresolved.

**Evidence:** decompilation of `FUN_00723380/23450/23610/23740/237B0`
and `FUN_00723250`; bytes `0x007237B0..0x007238F3`,
`0x00722FD0..0x00723243`, and `0x00723450..0x0072373F`. The seek site
is preserved `0x00723840`, live `0x00723880`. Opcode `0x8C650098`
confirms that this caller reads a word at the primary player's `+0x98`,
rather than assuming the halfword width used by other cursor consumers.

**Observation:** a different typed owner constructs resource at `+0x64`
in preserved `FUN_0072C080`. It first destroys the previous type-2 player
with `FUN_001B7570`, or type-1 effect with `FUN_001951A0`; it also releases
the separate effect at `+0x68`. The incoming type byte comes from a
`0x0C`-stride table and is stored at owner `+0x80`. Type 1 allocates/binds
an `0xA0` effect; type 2 allocates/binds an `0x120` animation player and
requests frame 1 with flag 0 before installing it at `+0x64`. This is a
replacement/construction seek, not a periodic reset.

The separate full setup entry is preserved `0x0072B990`, not its analyzed
continuation `FUN_0072B9D0`. It selects the type using the signed row index
at `owner+0x74` record `+4`; owner IDs `+0x78 ==0xB4/0xB5` force type 4.
The type table starts at live `0x008C4630` (preserved `0x008C45F0`), with
type byte at row `+5`. When row halfword `+6 ==0x14`, types 1/2 allocate
and bind their effect/player from the descriptor table. Type 3 instead
allocates/constructs an `0xA0` effect, and type 4 an `0x120` player, then
passes that resource to virtual slot `+0x68` before storing it at `+0x64`.
These are owned allocations. The base vtable at resident `0x005E0810`
maps that slot to live `0x007305F0`, whose preserved body `0x007305B0`
only returns. Derived implementations of that slot remain untraced.
Inspected type-table rows 62..64 also select type 4; this establishes a
type-4 producer, while selection of the implemented type-3 arm remains
unresolved. The table's high-level resource/character identity is not assigned.

Update helper `FUN_0072C760` requires resource `+0x64`. Types 1/3 copy the
owner transform and update an effect; types 2/4 copy transform/opacity and,
with player `+0xFC`, advance/compose by unsigned player `+0x94`, third
argument zero. The advance result is not used to retire the resource.
Two direct callers have different local gates:

| Preserved caller / helper site | Gate before playback | Work after playback |
| --- | --- | --- |
| `FUN_0072C900`, `0x0072C9A0` | Signed delay `+0x84 >0` decrements and returns; byte `+0x89 ==0` also returns. After a preliminary owner update, dispatcher `0x0072CF10` can return 1 and skip playback. Its raw eight-entry table maps state `+0x7E ==7` to that return-1 arm. Otherwise virtual slots `+0x20/+0x4C` run before the typed helper. | State-2 virtual handling, opacity/geometry handling and bounds/lifetime handling follow the helper. These later operations are not gates on the advance already performed. |
| `FUN_007443C0`, `0x0074467C` | The same delay/enable checks apply. State `+0x7E ==7` returns 0; state 6 writes 7 and returns 1. Other paths prepare transform and call virtual slot `+0x4C` before the typed helper. | Counter `s16(+0x200) ==90` returns 0 only after the helper. Otherwise it adds `float(+0x278)` to `float(+0x1FC)`, increments the counter and returns 1. Counter 90 therefore still permits that invocation's playback. |

Submission entry preserved `0x0072CD60` requires delay `+0x84 <=0`,
byte `+0x89 !=0` and signed state `+0x7E >1`. A nonnull resource is
submitted as an effect for types 1/3 or animation player for types 2/4;
the inspected body has no advance or seek. This draw gate differs from
both update callers, including its handling of states 6/7.

Full cleanup at preserved `0x0072B840..0x0072B96F` destroys types 1/3
through `FUN_001951A0(resource,1)` and types 2/4 through
`FUN_001B7570(resource,1)`, then clears `+0x64`. It also releases/clears
the separate `+0x68` effect and other local resources before resetting
owner defaults. Destructor `0x0072B7C0` calls this cleanup, then base
destruction and optional owner deallocation. By contrast, replacement
`FUN_0072C080` explicitly destroys only old types 1/2; the inspected
code does not establish that replacement is used on a type-3/4 owner.

**Evidence:** decompilation of `FUN_0072B990/C080/C760/C900/CD60`
and `FUN_007443C0`; full setup bytes `0x0072B990..0x0072BF2F`,
replacement `0x0072C080..0x0072C25F`, update helper
`0x0072C760..0x0072C86F`, first caller `0x0072C900..0x0072CA1F`,
dispatcher `0x0072CF10..0x0072CFCF` and its table
`0x008C4AA0..0x008C4ABF`, second caller gates/tail
`0x007443C0..0x0074444F` and `0x00744660..0x007446DF`, submission
`0x0072CD60..0x0072CF0F`, cleanup `0x0072B7C0..0x0072B96F`,
type-table rows `0x008C45F0..0x008C48FB`, resident vtable
`0x005E0810..0x005E086F`, and virtual initializer bytes
`0x007305B0..0x007305BF`. A direct-JAL search
found the two helper sites above. The replacement seek is preserved
`0x0072C230`, live `0x0072C270`; the ordinary advance is preserved
`0x0072C838`, live `0x0072C878`.

## BTL input and endpoint-request owners

This closes the local classification of all ten direct seek candidates in
preserved `0x0071499C..0x0072C230`: the three gauge seeks and the two
construction/capture seeks above, plus the five sites below. It does not
establish every caller of the surrounding owner methods.

| Preserved owner / seek sites | Local scheduling and seek purpose |
| --- | --- |
| Input selector `FUN_007147F0`, `0x0071499C/14A28`; update `FUN_007157F0` | Direction bits with settled float `+0x78` comparisons arm bytes `+0x161/+0x160` and request zero on players `+0x168/+0x164`. The update advances only armed directional players and clears their bytes on completion; it separately advances valid decoration players at `+0x15C`, `+0xCC/+0xD0/+0xD4/+0xD8/+0xDC`. A raw call at `0x00715930` connects the input helper to the update's state dispatch. Its complete upstream state/entry relationship is not inferred from the decompiler's broken switch. |
| Positioning helper `FUN_00717A20`, recovered `0x00717B2C/17B68` | After local position binding, player `+0x11C` requests `F<<8` when selector argument `a1` (saved in `s0`) is zero; otherwise it requests owner unsigned-halfword `+0x14<<8` and inspects the seek result and integer cursor. Both seeks use flag 0. Bytes continue past the analyzed end at `0x00717AAC` to a real return at `0x00717BF0`; there is no advance in this recovered tail. |
| State controller `FUN_00717F80`, `0x00718214` | Signed state halfword `+0x12 ==0` binds/reinitializes player `+0x48` and advances/composes once, then enters state 1. State 1 advances/composes until completion and changes to state 3. State 4 instead requests `(F-owner.u16(+0x14))<<8` with flag 0; a nonzero result sets completion byte `+0x18` and clears state/count. State 2 has no local advance/seek. The counter's producer is draw routine `FUN_007182E0`: in its positive-state branch it increments `+0x14` by one (`lhu`/`addiu 1`/`sh` at `0x007188E4..0x007188EC`), so each such draw moves the state-4 target one frame earlier. The controller's full caller chain remains unresolved. |

Cleanup `FUN_00717C70` destroys/clears state-controller player `+0x48`
and then releases the remaining local resources. Construction `FUN_00717D60`
creates that player through resident `FUN_0037D5B0`. The input selector's
separate cleanup `FUN_00713AE0` contains destructor sites for its decoration
and directional players, but its full recovered cleanup path is not claimed
here. All listed seek requests retain the active-blend qualification.

**Evidence:** decompilation of `FUN_007147F0/157F0/17F80/17C70/17D60`;
disassembly of `FUN_00717A20/17F80`; bytes
`0x00715900..0x00715A7F`, `0x00717AB0..0x00717BF7`,
`0x00717C70..0x00717D5F`, and `0x00717D60..0x00717F43`.

## BTL player recreation and descriptor restoration

**Observation:** preserved entry `0x007827D0` captures descriptor
`old_player+0x90` and unsigned-halfword whole frame `+0x98` from owner
player `+0xB34`, destroys that player, allocates/constructs a new `0x120`
player and installs it in the same slot. It associates the new reader with
local container/effect `+0xB38`, binds the saved descriptor with blend
duration zero, then seeks the saved whole frame `<<8` with flag 0 when
the new player has nonzero `+0xFC`. The inspected body performs no advance.
Only that descriptor/frame pair is explicitly captured; this does not
establish preservation of the prior step, fractional cursor or active blend.

Two recovered update bodies consume this slot with different completion
policies. Actual entry `0x00783450` requires owner byte `+0` bit 1,
nonnull `+0xB34` and nonnull player descriptor `+0x90`. It updates local
opacity, advances/composes a player with nonzero `+0xFC` by its unsigned
step `+0x94`, and stores completion at owner `+0xB48`. The alternate body
`FUN_00784030` has the owner-bit gate, then writes player step zero when
the previous `+0xB48` is nonzero before performing the same advance and
composition. Its zero step is distinct from omitting the call. Full cleanup
at preserved `0x00783310` destroys/clears `+0xB34`, releases/clears
`+0xB38/+0xB3C` and other local resources. Recreation and ordinary update
therefore have separately observed ownership phases.

**Observation:** complete selector `0x00787600..0x0078781F` takes a
controller as `a1`, descriptor index as `a2`, restart argument as `a3`
and force argument as `t0`. It returns without changing selection when the
index equals controller word `+0xCC` and force is zero. With a nonnull
descriptor at `controller+0x44+index*4`, it binds player `+0x120` with
blend duration zero. Nonzero restart then requests frame 1 with flag 0
when player `+0xFC` is nonzero and clears controller counter `+0x158`.
The valid-descriptor path always writes player step `0x100`, including
when restart is zero. It also performs association handling, copies the
old selector word `+0xC8` to `+0xCC`, and stores the incoming index at
`+0xC8`; the body has no advance. Allocation/ownership of this referenced
player and the selector's higher-level callers remain unresolved.

**Observation:** `FUN_00788000` and `FUN_007881E0` form a descriptor/frame
capture and restore-request pair for owner player `+0x320`. The first clears
the capture record at `+0xF10..+0xF2F`, then requires virtual slot
`+0x1D0` to return nonzero. After virtual slot `+0x24`, it sets capture
byte `+0xF10` and saves the associated fighter primary player's descriptor
word `+0x90` and whole-frame word `+0x98` into `+0xF14/+0xF18`.
It binds owner player `+0x320` from descriptor `+0xF1C`, requests frame 1
with flag 0 when valid, and establishes its transform. A separate byte
`+0x389` and resident predicate `FUN_003083A0` gate substitution of that
player into associated fighter `+0xE70`; the frame-1 seek does not depend
on this substitution succeeding.

The second method calls virtual slot `+0x20` first. With capture byte
`+0xF10 !=0`, it rebinds player `+0x320` to saved descriptor `+0xF14`
with blend duration zero, requests saved word `+0xF18<<8` with flag 0
when valid, then clears the capture record. Neither complete method calls
advance. This establishes descriptor/frame restoration requests for that
slot; the effects of their virtual calls and the complete lifetime of any
primary-player substitution remain untraced.

Eight further descriptor-change seeks are recovered in complete surrounding
bodies. They use flag 0 and blend duration zero at the preceding bind. None
of these bodies has a direct call to the ordinary advance API:

| Preserved entry / seek site | Local gate and descriptor/frame operation | Lifetime or later phase |
| --- | --- | --- |
| `FUN_0078B1F0`, `0x0078B320` | Argument `a1 ==0` enters the binding path for owner player `+0x4D0`. A nonzero associated-object predicate selects descriptor `associated(+0x4CC)+0xB84` entry `+0xA4`; otherwise it binds null. A valid player requests frame 1. Argument `a1 !=0` skips this binding/seek sequence. | Byte `+0x539` plus the association predicate separately gate substitution into the associated fighter's `+0xE70`; they do not gate the frame-1 seek directly. The method also stores a local position capture and control bytes. |
| `FUN_00790190`, `0x00790338` | Requires owner byte `+0x1A0` bit 0, a nonzero predicate for associated object `+0x4CC`, and a nonnull linked object at `+0x18C` with player `+0xB34` and descriptor `+0x90`. A valid owner player `+0x4D0` binds that descriptor and requests `(F-1)<<8`. A table-selected record byte `+5 ==1` skips this sequence. | Conditional primary-player substitution/transform work follows. Later in the same body, virtual destruction of linked object `+0x18C` runs and the pointer is cleared. The copied descriptor's complete backing-resource lifetime is not established. |
| `FUN_00791560`, `0x00791760` | Requires pending byte `+0x50 !=0`, descriptor `+0x4C !=0` and a nonzero predicate for associated object `+0x31C`. Binds owner player `+0x320` to that pending descriptor and requests frame 1 when valid. | Conditional primary-player substitution follows. The method clears pending descriptor `+0x4C`, byte `+0x50` and associated request values `+0x54/+0x58` after processing; this clears a request, rather than freeing the animation player. |
| Actual entry `0x00795950`, `0x00795D64` | Requires owner byte `+0x1C0 ==0` and `+0x1A0` bit 3. The playback tail further requires a selected table record with nonzero byte `+4` and byte `+5 ==1`, a nonzero predicate for associated object `+0x4CC`, and that object's byte `+0x61` bit 0 clear. A nonnull descriptor from its `+0xB84` array at signed owner index `+0xB8C` is bound directly to its primary player `+0xE70`, then requested at frame 1 when valid. | Object/pool handling precedes this tail, and an associated-fighter helper follows the seek. The complete scheduling and resource lifetime of this descriptor change remain unresolved. |
| `FUN_007B9670`, `0x007B9764` | Owner word `+0x1004 ==1` and `+0x100C ==0` enable binding player `+0x4D0`. A nonzero associated-object predicate selects descriptor `associated(+0x4CC)+0xB84` entry `+0x38`; otherwise the bind uses null. A valid player requests frame 1. | Earlier handling of a nonnull owner `+0x1080` calls its virtual slot `+0x5C` and temporarily changes an associated float. Later byte `+0x539` and association checks control primary-player substitution and transform copying. Those later gates do not skip the preceding valid-player seek. |
| `FUN_007BABC0`, `0x007BAEA4` | After earlier virtual/global handling, the binding tail requires argument `a1 !=0`, owner `+0x1004 !=2`, byte `+0x1010 !=0`, a nonnull global context and its indexed `+0xDE0` entry. It binds player `+0x4D0` from associated `+0x4CC` descriptor-array entry `+0xA4` or `+0xDC`, then requests frame 1 when valid. | Entry `+0xA4` is selected when byte `+0x539`, the association predicate and associated byte `+0x63` bit 7 all hold; the other path selects `+0xDC`. Each lookup separately requires a nonzero association predicate or binds null. Subsequent substitution is gated separately. Neither this body nor the preceding row writes the player step. |
| Actual entry `0x007BB0A0`, `0x007BB0F4` | Takes owner and descriptor index, binds player `+0x320` from `owner+0xFF0+index*4` with blend duration zero, then requests frame 1 with flag 0 when valid. | Byte `+0x389` and the associated-object predicate gate subsequent primary-player substitution into associated `+0x31C`. The method then clears owner word `+0x358` and stores the selected index at `+0x1000`. The full body contains no player-step write or ordinary advance. |
| `FUN_007EFCD0`, `0x007EFF1C` | After counter/resource work, owner word `+0x358 !=0` and byte `+0x102C ==0` enable virtual slot `+0x230`. The method then rereads those fields: `+0x358 !=0` and `+0x102C ==1` enable a zero-blend bind on player `+0x320`. The comparison `float(+0x1018) <=0` selects descriptor `+0x1028`; otherwise it selects `+0x1024`. A valid player requests frame 1 with flag 0. | It clears byte `+0x102C` after the valid-player check and continues a two-record cleanup loop. The full body has no direct advance or player-step write. The virtual callback's effects cannot be replaced by entry values when describing the later seek gate; allocation and backing-descriptor lifetime remain unresolved. |

**Evidence:** decompilation of `FUN_007827D0`,
`FUN_00783490/84030`, `FUN_00787600` and
`FUN_00788000/881E0`, corroborated by complete bytes
`0x007827D0..0x0078299F`, `0x00783310..0x007836CF`,
`0x00784030..0x0078429F`, `0x00787600..0x0078781F`
and `0x00788000..0x0078829F`. The local opacity helper at actual
`0x00782340..0x007825BF` writes owner float `+0xB7C`, rather than
producing the player step. Seek sites are preserved `0x007828AC`,
`0x00787694`, `0x0078815C`, `0x0078824C`; the two local advance sites
are `0x007834C4`, `0x007840A0`. Preserved continuations that falsely
return after destruction or binding do not establish retail early exits.
The first four further rows use decompilation of
`FUN_0078B1F0`, `FUN_00790190`, `FUN_00791560` and
`FUN_00795950/95990`, with complete surrounding bytes
`0x0078B1F0..0x0078B42F`, `0x00790190..0x0079051F`,
`0x00791560..0x007917FF` and `0x00795950..0x00795D9F`.
The two owner-ID lookups index live pointer table `0x008AD8E4` with
stride 8 and require the signed index in `0..0xC4`; the rows describe
the subsequent byte comparisons, without assigning the table a character
or resource identity.
The next three use decompilation of `FUN_007B9670/7BABC0`
and split `FUN_007BB0D0`, with complete surrounding bytes
`0x007B9670..0x007B986F`, `0x007BABC0..0x007BAF7F`
and `0x007BB0A0..0x007BB18F`. Allocation and complete backing-descriptor
lifetimes for these reused slots remain untraced.
The last row uses decompilation of `FUN_007EFCD0` and complete bytes
`0x007EFCD0..0x007EFFDF`. Apparent decompiler returns at the random helper
and either descriptor bind are contradicted by the continuous raw body.

## BTL wrapped frog player

**Ownership observation:** resident owner vtable `0x005F79A0` and its
type record identify `ccSkillJRY001Frog`. Setup `FUN_007BCB60`
resolves two descriptors into owner `+0x8B4/+0x8B8`, then calls
resident `FUN_0030F290(owner+0xAF0,descriptor(+0x8B4),1,0,0,0)`.
The resident kind-1 branch allocates/constructs an `0x120` animation
player, binds with blend duration zero and stores it at wrapper `+0x1A0`,
which is owner `+0xC90`. This player belongs to the embedded wrapper;
it is not an embedded animation-player structure at that offset.

**State-transition observation:** `FUN_007BD200` first calls wrapper
virtual slot `+0x14`, saves the old owner counter `+0xD0C`, then increments
that counter. A position below `-499` selects an owner virtual callback
instead of the state branches. Otherwise, state word `+0xD04 ==1` and
byte `+0xA42 !=0` enable the seek sequence: bind `+0xC90` to descriptor
`+0x8B8` with blend duration zero and request frame 1 with flag 0 when
valid. Owner word `+0x90 !=0x54` additionally writes player step `0x200`;
value `0x54` leaves its step unchanged. The method clears completion byte
`+0xC9F`, then sets state `+0xD04 =2` and clears counters
`+0xD0C/+0xD08`. The seek therefore precedes the conditional rate write
and completion-latch reset. The complete state method has no direct
ordinary advance call.

**Phase observation:** this class's owner vtable slot `+0x10` points
to live `0x007BD100`, actual preserved `0x007BD0C0`, which calls the
embedded wrapper's virtual slot `+0x0C`. The wrapper's resident vtable
`0x005DC830` resolves that slot to `FUN_003108A0`, the advance/repeat
policy already classified under
[resident explicit seeks](scene_playback_owners.md#resident-explicit-seek-classification).
Its completion field `wrapper+0x1AF` is exactly the owner `+0xC9F`
cleared by the transition. The state method is separately connected through
owner slot `+0x18` to live `0x007BD240`. Its initial wrapper slot
`+0x14` resolves to `FUN_00310A90`, which performs wrapper bookkeeping
without a direct seek/advance. The slot connections establish separate
phases; the full dispatcher order between them remains unresolved.

Owner draw at preserved `0x007BD100`, slot `+0x68`, sets a temporary
render context and calls wrapper slot `+0x10`, resident `FUN_00311C60`.
That wrapper submission requires a nonnull resource, byte `+0x39 !=0`
and signed delay `+0x208 <1`; kind 1 submits the player. Neither inspected
draw body advances or seeks it. Owner destructor `FUN_007BCAD0` calls
`FUN_0030E830(owner+0xAF0,-1)`. The resident destructor forces wrapper
ownership byte `+0x1B0 =1`, then `FUN_0030EC30` destroys a kind-1 player
with `FUN_001B7570(player,1)` and clears wrapper `+0x1A0`. The local
completion reset consequently does not release player ownership.

**Evidence:** decompilation of `FUN_007BCB60/7BD200`,
`FUN_0030F290/30E770/30E830/30EC30`,
`FUN_003108A0/310A90/311C60`, and split `FUN_007BD0B0`;
complete owner setup bytes `0x007BCB60..0x007BCE9F`, destructor
`0x007BCAD0..0x007BCB5F`, advance wrapper
`0x007BD0C0..0x007BD0FF`, draw `0x007BD100..0x007BD1FF`,
state method `0x007BD200..0x007BD7AF`, and adjacent helper
`0x007BD7B0..0x007BD7CF`. Resident allocation branch bytes
`0x0030F290..0x0030F43F`, cleanup `0x0030EC30..0x0030ED3F`,
destructor `0x0030E830..0x0030E8CF`, complete advance body
`0x003108A0..0x00310A8F` and submission prefix
`0x00311C60..0x00311D2F` corroborate the player and gate arguments.
Owner/wrapper tables are `0x005F79A0..0x005F7A3F` and
`0x005DC830..0x005DC86F`; preserved type record/name bytes are
`0x008CFEC8..0x008CFEDF` and `0x008BC2E0..0x008BC2F7`.
The additional BTL seek site is preserved `0x007BD3A8`.

## BTL GUW embedded player

**Ownership observation:** resident vtable `0x005EDF00` and its type
record identify `ccSkillGUW001`. Actual constructor
`0x007ECB10..0x007ECC7F` constructs the animation player inside the owner
at `+0x10E0`, calls resident initialization `FUN_001B7520` on it, and
clears owner byte `+0x1201`. This is an embedded player rather than a
separately allocated pointer slot. Complete destructor `FUN_007ECC80`
calls `FUN_001B7570(owner+0x10E0,-1)` and continues array/base cleanup
and optional owner deallocation. The player structure is not independently
freed by that call.

**Selection observation:** actual selector
`0x007EDEA0..0x007EE19F` stores incoming selector `a1` at `+0x1098`
and clears counters `+0x109C/+0x10A0`. Selectors 0, 1 and 2 resolve
`ANM_2guwcha1a`, `ANM_2guwcha1b` and `ANM_2guwcha1c`
respectively through owner container `+0x1F0`. Their common footer binds
a nonnull resolved descriptor to embedded player `+0x10E0` with blend
duration zero and sets byte `+0x1201 =1`. A null descriptor clears that
byte instead. Selector 3 performs other request/callback handling, then
reaches the null-descriptor footer; other selector values also reach that
footer without resolving one of these three assets.

The only direct seek in this complete selector is preserved `0x007EE14C`.
After binding, it requires the current stored selector `+0x1098 ==2`
and valid player track at owner `+0x11DC` (player `+0xFC`), then
requests frame 1 with flag 0. Earlier virtual/helper calls precede this
comparison, so the footer gate is described by its reread word rather
than assuming they preserve every entry field. The selector contains no
ordinary advance or player-step write. Setting the enable byte is separate
from the explicit seek; the other two asset branches have no direct seek.

**Update observation:** complete `FUN_007EDD50` requires byte
`+0x1201 !=0`, derives the player transform from owner resource
`+0x1090`, local float `+0x10D0` and owner rotation, and marks its
transform changed. With nonzero track `+0x11DC`, it advances at preserved
`0x007EDE70` using unsigned halfword `+0x1174` (player step `+0x94`)
and third argument zero, then composes. Completion is ignored.
`FUN_00874060` contains the same local gate/transform/advance policy,
with its advance at `0x00874180`; the resident class vtable slot
`+0x1E0` points to its live entry `0x008740A0`.

Complete caller `FUN_007ED7B0` invokes live `0x007EDD90`
(actual `FUN_007EDD50`) after other local transform bookkeeping and
before its association checks and virtual slot `+0x244`. Thus those later
association checks do not skip this preceding embedded-player update.
The same class vtable connects this caller through slot `+0x100`
to live `0x007ED7F0`. The full dispatcher order and whether both update
routes execute in any one scheduling cycle remain unresolved; the two
direct sites do not establish two increments per displayed frame.

**Submission observation:** `FUN_007ED6D0` uses byte `+0x1201`
to gate submission of the embedded player. It selects the context at
`*(gp-0x3300)+0x2990`, writes player opacity `+0x88` to `0.8`,
submits and restores the context. A separate local object `+0x1094`
can still be submitted afterward, independently of the embedded-player
enable byte. This complete method has no seek or advance. Vtable slot
`+0xFC` points to its live entry `0x007ED710`, while `+0x228`
points to the destructor's live entry `0x007ECCC0`.

**Evidence:** decompilation of split `FUN_007ECB50`,
`FUN_007ECC80`, `FUN_007EDEA0/7EDEE0`, `FUN_007EDD50`,
`FUN_007ED7B0` and `FUN_00874060`, with complete construction/destruction
bytes `0x007ECB10..0x007ECE3F`, selector
`0x007EDEA0..0x007EE19F`, direct update
`0x007EDD50..0x007EDE9F`, caller
`0x007ED7B0..0x007ED90F`, submission
`0x007ED6D0..0x007ED7AF`, and alternate update
`0x00874060..0x008741AF`. Resident vtable bytes are
`0x005EDF00..0x005EE14F`; preserved type record/name bytes are
`0x008CF610..0x008CF637` and `0x008BBDF8..0x008BBE07`,
with asset strings at `0x008B3078..0x008B30A7`.

## BTL GAR and GAV primary-player transitions

**Identity/resource observations:** constructor prefix
`0x00823C40..0x00823C8F` installs resident vtable `0x005E9B30`,
whose type/name identify `ccSkillGAR001New3`. Setup prefix
`0x008240D0..0x0082416F` loads `ANM_pgarcha11/12` into
`+0xFF0/+0xFF4` from container `+0x1F0`. Complete constructor
`FUN_00825A40` installs vtable `0x005E98E0`, identifying
`ccSkillGAV001`. Complete setup `FUN_00825C00` loads
`ANM_pgavcha11/12/13` into `+0xFF0/+0xFF4/+0xFF8`
from container `+0x1F0`.

All five seeks below reuse the primary player in inherited field
`+0x320`, follow a zero-blend bind, require player `+0xFC`,
and request frame 1 with flag 0.

| Owner / method and gate | Descriptor and local bookkeeping | Preserved seek |
| --- | --- | --- |
| GAR complete setter `FUN_008252F0`, requested low byte 1 | `+0xFF0`; clears byte counter `+0x1004` before bind | `0x00825368` |
| GAR setter, requested low byte 2 | `+0xFF4` | `0x008253A8` |
| GAV complete update `FUN_00825D10`, signed state `+0xFFE ==0`, `+0x358 !=0` | `+0xFF0`; clears counter `+0xFFC`, stores state 1 afterward | `0x00825DA4` |
| GAV update, state 1, virtual slot `+0xF4` returns low byte zero | `+0xFF4`; clears counter, stores state 2 afterward | `0x00825E34` |
| GAV update, state 2, current `+0x358 !=0` | `+0xFF8`; clears counter, stores state 3 afterward | `0x00825EA0` |

GAR's setter first stores the sign-extended low byte of its request in
halfword state `+0x1006`; other requested values do not bind/seek.
The inspected update prefix `0x00824440..0x008244FF` increments
byte counter `+0x1004` before its state checks. State 0 with
`+0x358 !=0` requests state 1 at `0x008244BC`. State 1 with
the current signed byte counter `>=31` requests state 2 at
`0x008244DC`. Complete helper `FUN_00825240` also requests
state 2 at `0x00825258`, before its other resource cleanup.
Only this GAR update prefix is recovered; its continuing
body and complete scheduling contract remain unresolved.

GAV's complete update increments unsigned 16-bit counter `+0xFFC`
before dispatching on signed halfword state `+0xFFE`. In state 2,
counter value 2 invokes `FUN_00825EF0` before the later `+0x358`
check and transition seek. State 3 with `+0x358 !=0` invokes
virtual slot `+0x230`. The complete GAR setter and GAV update contain
no direct ordinary advance or player-step write. Their primary-player
allocation, full advance schedule and release remain unresolved.

**Evidence:** decompilation of `FUN_008252F0/825D10`;
complete bytes `0x00825240..0x008252EF`,
`0x008252F0..0x008253CF`, `0x00825A40..0x00825AAF`,
`0x00825C00..0x00825D0F` and `0x00825D10..0x00825EEF`,
with the GAR constructor/setup/update prefixes above. Resident vtable
bytes are `0x005E9B30..0x005E9B3F`,
`0x005E98E0..0x005E98EF` and `0x005E99D0..0x005E99EF`;
GAV update slot `+0xF8` points to live `0x00825D50`.
Preserved type/name bytes are `0x008CF1C8..0x008CF1F7`,
`0x008BBAC8..0x008BBAD7` and `0x008BBAE0..0x008BBAF7`;
descriptor strings are `0x008B6850..0x008B686F` and
`0x008B68D8..0x008B6907`. A direct-JAL byte search for the
GAR setter's live entry `0x00825330` found the three caller sites
above; indirect callers remain open.

## BTL TOV variant-selected primary-player seeks

**Identity/resource observations:** complete constructor
`FUN_00822260` installs resident vtable `0x005E9D80`, whose
type/name identify `ccSkillTOV001`. Complete setup `FUN_008224D0`
loads eight descriptors from container `+0x1F0` into
`+0xFF0/+0xFF4/+0xFF8/+0xFFC/+0x1000/+0x1004/
+0x1008/+0x100C`, named `ANM_ptovcha11/12/13/14/15/16/17`
and `ANM_2tovdash01`, respectively. The primary player is inherited
owner field `+0x320`; this constructor does not construct a separate
animation player.

**Seek observations:** complete setter `FUN_00822D00` stores the
incoming signed-halfword state at `+0x1040` before dispatching.
States 1/2/4 bind the existing primary player with blend duration zero,
then request frame 1 with flag 0 under its `+0xFC` guard. Local
bytes `+0x10F0/+0x10F1` choose distinct descriptors; their high-level
action names are not established.

| Requested state and selector gate | Descriptor | Preserved seek |
| --- | --- | --- |
| 1, `+0x10F0 ==1` | `+0xFFC` | `0x00822DA0` |
| 1, `+0x10F0 !=1` | `+0xFF0` | `0x00822E34` |
| 2, `+0x10F0 ==1` | `+0x1000` | `0x00822E98` |
| 2, `+0x10F0 !=1` | `+0xFF4` | `0x00822F28` |
| 4, `+0x10F0 ==1` and `+0x10F1 ==1` | `+0x1008` | `0x00823218` |
| 4, `+0x10F0 ==1` and `+0x10F1 !=1` | `+0x1004` | `0x0082325C` |
| 4, `+0x10F0 !=1` | `+0xFF8` | `0x0082329C` |

Setter states 0/3 do not seek. State 3 saves counter `+0x1010`
in `+0x1012`, clears that counter and later clears selector byte
`+0x10F1`. State 2's `+0x10F0 !=1` branch sets signed limit
`+0x1014 =5` and clears counter `+0x1010` after its bind/seek;
the other state-2 branch does not perform those counter writes.

**Caller/order observations:** complete update `FUN_008228E0`
increments 16-bit counter `+0x1010`, performs local effect countdown
work and virtual slot `+0x244`, then branches on signed state
`+0x1040`. State 0 requests state 1 at `0x00822A10` without a
`+0x358` gate. State 1 with `+0x358 !=0` requests state 2 at
`0x00822A38`. In state 2 with selector `+0x10F0 ==1`, helper
`FUN_008235F0` returning a nonzero low byte makes the later state-4
request eligible; result exactly 1 also sets `+0x10F1 =1` before
that request. With `+0x10F0 !=1`, signed counter `+0x1010`
exceeding signed limit `+0x1014` makes it eligible. The common request
is preserved JAL `0x00822B24`.

In state 3, signed counter `+0x1010 >10` and resident helper
`FUN_003737A0` returning low byte 1 instead copy `+0x1012` back
into the counter and write state 2 directly at `0x00822BE4`.
That transition bypasses the setter and performs no local bind/seek.
Setup requests state 0 at `0x008228C0`. Neither complete update
nor setter directly advances a player or writes its step `+0x94`;
the inherited player's lifetime and complete upstream playback gates
remain unresolved.

**Evidence:** decompilation of `FUN_00822D00`,
`FUN_00822260` and `FUN_00822360`; complete bytes
`0x00822260..0x0082235F`, `0x008224D0..0x008228DF`,
`0x008228E0..0x00822C4F` and `0x00822D00..0x008233AF`.
Resident vtable bytes `0x005E9D80..0x005E9D8F` and
`0x005E9E70..0x005E9E8F` connect update slot `+0xF8`
to live `0x00822920`. Type/name bytes are
`0x008CF1F8..0x008CF20F` and `0x008BBAF8..0x008BBB07`;
descriptor strings are `0x008B65E8..0x008B6667`.

## BTL ASM requested-state primary-player seeks

**Identity/resource observations:** constructor prefix
`0x0081FAE0..0x0081FB2F` installs resident vtable `0x005E9FD0`.
Its type/name identify `ccSkillASM001`. Setup prefix
`0x0081FD80..0x0081FEAF` loads descriptors
`+0xFF0/+0xFF4/+0xFF8/+0xFFC` from container `+0x1F0`,
named `ANM_paswcha11/12/13/14`. The names do not substitute
for the RTTI class identity.

The complete state setter starts at preserved `0x008208B0`;
`FUN_008208F0` is its indirect-jump fragment. It stores the incoming
signed-halfword state at owner `+0x1090`, then dispatches through six
entries for states 0..5. States 1/2/3/5 rebind the existing primary
player `+0x320` with blend duration zero, then request frame 1 with
flag 0 if player `+0xFC` is valid. States 0/4 contain no direct seek.

| Requested state | Selected descriptor | Preserved seek |
| --- | --- | --- |
| 1 | `+0xFF0` | `0x00820980` |
| 2 | `+0xFF4` | `0x008209E8` |
| 3 | `+0xFF8` | `0x00820BB0` |
| 5 | `+0xFFC` | `0x00820E60` |

**Caller observations:** complete update `FUN_00820270` increments
16-bit counter `+0x1010`, calls virtual slot `+0x244` and local
helpers, then dispatches on signed state `+0x1090`. The recovered
direct calls to the setter are:

| Calling phase / local gate | Requested state / preserved JAL |
| --- | --- |
| Setup tail | 0 / `0x00820244` |
| Update state 0, `+0x358 !=0` | 1 / `0x00820378` |
| Update state 1, virtual slot `+0xF4` returns low byte zero | 2 / `0x008203B4` |
| Update state 2, `+0x358 !=0` | 3 / `0x008203EC` |
| Update state 3, signed counter `+0x1010` exceeds signed limit `+0x1014` | 5 / `0x00820438` |
| Update state 4, signed counter `+0x1010 >11` and helper `FUN_003737A0` returns low byte 1; copies `+0x1012` into the counter first | 5 / `0x0082051C` |
| `FUN_00820740` | 4 / `0x0082074C` |

The raw update continues after associated-object/resource calls that the
decompiler treated as returns. Neither the complete update nor setter
directly calls ordinary advance or writes primary-player step `+0x94`.
Indirect/helper playback and the inherited primary player's allocation,
complete advance schedule and release remain unresolved. The table records
state-change seek requests, not elapsed time or a whole-owner pause.

**Evidence:** decompilation of split `FUN_008208F0`,
`FUN_0081FD80` and `FUN_00820270`; complete bytes
`0x008208B0..0x00820EDF`, `0x00820270..0x008206BF`,
setup tail `0x00820200..0x0082026F`, and helper
`0x00820740..0x0082076F`, with the constructor/setup prefixes above.
Preserved update/setter tables `0x008CDA70..0x008CDAA7`
contain live pointers. Resident vtable bytes
`0x005E9FD0..0x005E9FDF` and `0x005EA0C0..0x005EA0EF`
connect update slot `+0xF8` to live `0x008202B0`.
Type/name bytes are `0x008CF210..0x008CF227` and
`0x008BBB08..0x008BBB17`, with descriptor names at
`0x008B6540..0x008B657F`. A direct-JAL byte search for the
setter's live entry `0x008208F0` found the seven caller sites above;
it does not enumerate indirect callers.

## BTL KIB primary and looping embedded player

**Ownership/resource observations:** constructor `FUN_0081D2E0`
installs resident vtable `0x005EA220`, whose type/name identify
`ccSkillKIB001New3`, and constructs an embedded player at owner
`+0x11C0`. Setup `FUN_0081D750` loads six descriptors from
container `+0x1F0` into `+0xFF0/+0xFF4/+0xFFC/+0x1000/
+0x1004/+0x1008`, respectively named
`ANM_pkibcha11/15/12/14/16/17`. It finishes by calling the
state setter with state 0. The inherited primary player is owner `+0x320`.

**Seek observations:** the complete setter starts at preserved
`0x0081E510`; analyzed `FUN_0081E550` is a fragment inside it.
It stores the incoming signed-halfword state at `+0x100E` before
branching. Every seek below follows a zero-blend bind, requires the
selected player's `+0xFC`, and requests frame 1 with flag 0.

| Local setter state / update gate | Player and descriptor | Preserved seek |
| --- | --- | --- |
| State 1; owner byte `+0x389` is zero, association predicate for `+0x31C` is false, or associated byte `+0x63` bit 7 is clear | Primary `+0x320`, descriptor `+0xFF4` | `0x0081E5E8` |
| State 1; all three preceding conditions take their opposite branch | Primary `+0x320`, descriptor `+0xFF0`; later sets owner byte `+0x135C` bit 4 and byte `+0x1300 =1` | `0x0081E678` |
| State 2 entry, after resetting counter `+0x100C` and preparing position/direction | Embedded `+0x11C0`, descriptor `+0xFFC` | `0x0081E9B4` |
| State 3 entry | Primary `+0x320`, descriptor `+0xFFC` | `0x0081EADC` |
| State 4 entry | Primary `+0x320`, descriptor `+0x1004` | `0x0081EC48` |
| Update in state 2, embedded ordinary advance returns nonzero | Embedded `+0x11C0`, descriptor `+0xFFC` | `0x0081DF2C` |

**Advance/order observations:** complete update `FUN_0081DC10`
increments unsigned 16-bit counter `+0x100C` before dispatching on
signed state `+0x100E`. In state 2, position and transform helpers
precede the embedded player's valid-track gate. A valid player advances
at preserved `0x0081DEE0` using unsigned owner `+0x1254`
(player `+0x94`), third argument zero, then composes. Nonzero completion
causes the final table row's rebind/seek in that same invocation; zero
completion skips it. The associated-object checks earlier in this state
select position sources and converge before advance, rather than pausing
it. Rebinding lies between advance and seek; the body does not write the
step between those operations. This is a local completion-driven repeat,
not a wall-clock loop guarantee.

State 0 with `+0x358 !=0` calls the setter for state 1; state 1
with that field nonzero requests state 2. In state 2, current unsigned
counter `>25` requests state 4 after the embedded advance/repeat work.
Thus the invocation that changes to state 4 can already have advanced
and repeated the embedded player. States 3/4 invoke virtual slot
`+0x230` when `+0x358 !=0`. The setter performs no direct ordinary
advance; the primary player's complete advance schedule remains open.

**Submission/release observations:** complete `FUN_0081E270`
submits the embedded player only while signed owner state `+0x100E ==2`,
temporarily using the global context's `+0x2990` render area. It has no
additional local valid-track guard and performs no seek/advance.
Cleanup `FUN_0081D530` destroys the embedded player with
`FUN_001B7570(player,-1)`, continues through other local resources
and inherited cleanup, and conditionally frees the owner. State changes
reuse the embedded player. Primary-player allocation/release and the full
upstream invocation gates remain unresolved.

**Evidence:** decompilation of `FUN_0081D750/81DC10/81E510`,
its split `FUN_0081E550`, and `FUN_0081E270`; complete bytes
`0x0081D2E0..0x0081D52F`, `0x0081D530..0x0081D74F`,
`0x0081D750..0x0081DC0F`, `0x0081DC10..0x0081E26F`,
`0x0081E270..0x0081E2BF` and `0x0081E510..0x0081ED8F`.
The complete transform helper `0x0081F090..0x0081F1AF`
contains no seek/advance. Resident vtable bytes
`0x005EA220..0x005EA22F`, `0x005EA310..0x005EA33F`
and `0x005EA440..0x005EA45F` connect slots `+0xF8/+0xFC`
to live `0x0081DC50/0x0081E2B0`, and slots `+0x228/+0x22C`
to live `0x0081D570/0x0081D790`. Preserved type/name bytes
are `0x008CF228..0x008CF23F` and `0x008BBB20..0x008BBB5F`;
descriptor strings are `0x008B63B0..0x008B640F`.

## BTL SKN and SKM counter-gated primary players

**Identity/resource observations:** constructor `FUN_00818CC0`
installs resident vtable `0x005EA800`, whose type/name identify
`ccSkillSKN001`. Constructor `FUN_0081ABA0` installs vtable
`0x005EA510`, identifying `ccSkillSKM001New3`. The latter identity
comes from RTTI, despite its selected descriptor's different name.
Setup `FUN_00818EA0` loads `ANM_pskncha12/11` into
`+0xFF0/+0xFF4` from container `+0x1F0`; `FUN_0081AD80`
loads `ANM_psikcha12` into `+0xFF0` from that container field.
Both constructors clear their local counters/states. The state methods
use the primary player in inherited owner field `+0x320`.

Both complete state methods increment their unsigned 16-bit counter
before dispatching on a signed halfword state. The following seeks reuse
the existing primary player, bind descriptor `+0xFF0` with blend duration
zero, then request frame 1 with flag 0 only if player `+0xFC` is nonzero.

| Owner / complete state method | Local seek gate and transition | Preserved seek |
| --- | --- | --- |
| SKN, `FUN_00818F50` | State `+0xFFA ==1`, current unsigned counter `+0xFF8 >10`; clears counter before bind/seek, increments the current state afterward | `0x00819190` |
| SKM, `FUN_0081AE20` | State `+0xFF6 ==0`, owner `+0x358 !=0`; calls object factory `FUN_0081AF00` before bind/seek, then clears counter `+0xFF4` and increments the current state | `0x0081AEA4` |

SKN state 0 with `+0x358 !=0` clears its counter and increments
the state without seeking. In state 1, counter value 9 invokes factory
`FUN_008191F0` and other resource/effect work before the later `>10`
check. That factory allocates a `0xD10`-byte object, passes owner and a
local position to its constructor, then registers a successful object
through owner `+0xFFC` if the registry is available. SKM's factory
similarly allocates `0xCA0` bytes and registers through owner `+0xFF8`.
The created objects' playback contracts are not established by these
factory bodies.

SKN state 2 and SKM state 1 invoke virtual slot `+0x230` when
`+0x358 !=0`. Neither complete state method directly advances a
player or writes its step `+0x94`; the inherited primary player's
allocation, advance schedule and release remain unresolved. These local
counter transitions do not establish elapsed time.

**Evidence:** complete bytes for constructors
`0x00818CC0..0x00818D4F` and `0x0081ABA0..0x0081AC2F`,
setups `0x00818EA0..0x00818F4F` and
`0x0081AD80..0x0081AE1F`, state methods
`0x00818F50..0x008191EF` and `0x0081AE20..0x0081AEFF`,
and factories `0x008191F0..0x0081929F` and
`0x0081AF00..0x0081AFAF`. Resident vtable/type-slot bytes are
`0x005EA800..0x005EA81F`, `0x005EA8F0..0x005EA90F`,
`0x005EA510..0x005EA51F` and `0x005EA600..0x005EA61F`;
slot `+0x100` points to live `0x00818F90/0x0081AE60`.
Preserved type/name bytes are `0x008CF260..0x008CF277`,
`0x008CF2A0..0x008CF2B7`, `0x008BBB60..0x008BBB87`
and `0x008BBB88..0x008BBBAF`; descriptor strings are
`0x008B60C0..0x008B60DF` and `0x008B62C0..0x008B62CF`.

## BTL TYV parent and allocated-player object

**Parent observations:** resident vtable `0x005EAAF0` and its type
record identify `ccSkillTYV001`. Complete setup `FUN_00816C20`
loads descriptors `+0xFF0/+0xFF4` from container `+0x1F0`, named
`ANM_ptyvcha15/12`. The state method actually starts at
`FUN_00816D10`, after setup's return. It increments 16-bit counter
`+0xFF8`, then selects work using signed state halfword `+0xFFA`.
In state 0, current unsigned counter 9 calls object factory
`FUN_00816FF0` before the later `+0x358` check. When that word is
nonzero, it binds existing player `+0x320` to descriptor `+0xFF0`
with blend duration zero, requests frame 1 with flag 0 at
`0x00816DB0` when valid, clears the counter and increments the current
state. State 1 with current unsigned counter `>30` clears the counter,
binds descriptor `+0xFF4`, requests frame 1 with flag 0 at
`0x00816E14` when valid, then increments the current state and continues
other local work. State 2 and nonzero `+0x358` invokes virtual
`+0x230` instead. This complete method contains no direct ordinary
advance or player-step write. Vtable slot `+0x100` points to live
`0x00816D50`; the primary player's full inherited lifetime is untraced.

The factory allocates a `0xC20`-byte object and calls constructor live
`0x00817150` (actual `FUN_00817110`) with the parent. It passes
the constructed object and parent registration fields `+0x1000` to
live helper `0x007786E0` when the registry pointer is present, then
continues effect work. Parent cleanup `FUN_00816A10` checks byte
`+0xFFC ==0`, a nonnull registry, slot `+0x1000` within `0..31`,
and matching registration values `+0x1004/+0x1008` in either of two
registry entries. A match calls actual `FUN_00818300` on the referenced
object, setting its state byte `+0xBFC =3` and clearing counter
`+0xBFE`. This is a fade-state request; this parent path does not directly
destroy the object's animation player.

**Object ownership/setup observations:** resident vtable `0x005EAA50`
and its type record identify the created class `ccSkillObjTYV001`.
Constructor `FUN_00817110` clears player pointer `+0xB90` and
composition pointer `+0xB94`. Complete setup `FUN_00817480`
looks up `ANM_ptyvcha11` in container `+0x94`, allocates a separate
`0xA0`-byte composition and `0x120`-byte animation player, and stores
the initialized player at `+0xB90` when allocation succeeds. It connects
the local resources, binds the looked-up descriptor with blend duration
zero, then requests frame 1 with flag 0 at `0x00817680` when the
player's track is valid. Setup has no direct ordinary advance. Complete
destructor `FUN_00817340` destroys/clears the player with
`FUN_001B7570(player,1)`, destroys/clears the composition, and continues
other resource/array/base cleanup and optional owner deallocation. The
apparent decompiler return after the first release is not a complete cleanup.

**Object update/order observations:** complete `FUN_00817B20`
prepares counters, movement and opacity using signed state byte `+0xBFC`.
Its inspected branches for states 0/1/2/3/4 and other byte values all
converge on the same player-transform/advance tail. In particular, state
0's counter transition, state 1's later transition, state 2's object lookup,
and states 3/4's fade or virtual termination call do not locally bypass that
tail. The raw branches contradict the decompiler's apparent returns at
several resident helpers.

The tail writes owner opacity float `+0xBD4` to player `+0x88`,
applies its matrix, then advances/composes when `player+0xFC` is valid,
using current unsigned `player+0x94` and third argument zero at
`0x008180A4`. It ignores the advance completion result, and continues
attachment/effect work. State changes and fading thus do not independently
constitute an animation pause in this method. No explicit seek occurs in
its full body. Higher-level scheduling can still omit the method.

One recovered outer route is `FUN_00817A10`: after local association
work, it invokes this object's virtual slots `+0x1C` and `+0x10`
when owner `+0xA20` bit 0 is clear, owner byte 0 bit 1 is set, and
`+0xAE4` bit 0 is clear after its countdown update. The `+0xA20`
bit-0-set branch invokes virtual `+0x6C` instead. This wrapper does not
establish every caller or the elapsed cadence.

**Object submission observation:** complete `FUN_008181C0`
updates the player's matrix and submits pointer `+0xB90` in context
`*(gp-0x3300)+0x2990`, then restores the prior context and performs
optional additional drawing. It has no local state/opacity/valid-track gate
around that submission and no direct seek/advance. Vtable slots
`+0x0C/+0x10/+0x60/+8` point to live setup/update/submission/destructor
entries `0x008174C0/0x00817B60/0x00818200/0x00817380`;
slot `+0x5C` points to outer wrapper live `0x00817A50`.
All three seeks here are initial/descriptor-transition frame-one requests;
the created object's local fade state and its later allocation release are
separate lifetime events.

**Evidence:** decompilation of `FUN_00816A10/817340`,
`FUN_00817480/817B20/8181C0/817A10`, with complete parent setup/state
bytes `0x00816C20..0x00816FEF`, factory
`0x00816FF0..0x0081710F`, parent cleanup
`0x00816A10..0x00816C1F`, object constructor/destructor
`0x00817110..0x0081747F`, object setup
`0x00817480..0x008177AF`, outer wrapper
`0x00817A10..0x00817B1F`, object update
`0x00817B20..0x008181BF`, and submission/retirement request
`0x008181C0..0x0081831F`. Resident vtable bytes are
`0x005EAA50..0x005EAB0F` and `0x005EABE8..0x005EABFF`;
preserved type/name bytes are `0x008CF2C8..0x008CF307` and
`0x008BBBA0..0x008BBBCF`. Descriptor-name bytes are
`0x008B5DE0..0x008B5DFF` and `0x008B5E18..0x008B5E27`.

## BTL Sawarabi embedded-player array

**Ownership observation:** resident vtable `0x005EAD40` and its type
record identify `ccSkillObjSawarabi`. Constructor `FUN_00815A60`
constructs 20 records starting at owner `+0xAF0`, stride `0x340`,
through resident `FUN_00119290`. Each record begins with an embedded
animation player; record constructor actual `FUN_00815CC0` constructs
that player and two arrays of three attachment records. Owner destructor
actual `FUN_00873E50` destroys all 20 records through
`FUN_00119220`, then continues base cleanup and optional owner
deallocation. Record destructor actual `FUN_00815C20` destroys its
attachment arrays, then `FUN_001B7570(player,-1)`. Playback-state
retirement does not replace this storage lifetime.

**Initial-request observation:** complete setup `FUN_00815D60`
looks up `ANM_pkmvswrb00/02` in container `owner+0x94` and stores
the descriptors at `+0x4BF0/+0x4BF4`. It resets all 20 records using
actual `FUN_00816650`, clearing local position and timer halfwords
`record+0x130/+0x132`, and setting state halfword `+0x134 =-1`.
It then configures consecutive records while a placement query succeeds.
If the first query fails, it uses a local fallback position for that first
record and stops before configuring another; a later failure stops the
remaining pass. The complete body therefore does not guarantee 20 active
players in every instance.

For each configured record it sets state `+0x134 =0`, binds descriptor
`owner+0x4BF0` with blend duration zero, and requests frame 1 with
flag 0 at preserved `0x00816048` when track `player+0xFC` is valid.
It assigns local position/transform and delay values afterward. No direct
ordinary advance occurs in setup. The single seek instruction can serve
multiple records; it is one census site, not 20 distinct call sites.

**Update observations:** complete `FUN_00816160` visits all 20 records
and selects work using each signed state halfword `record+0x134`.

| Record state | Local playback contract |
| --- | --- |
| `-1` | Omit the record's state/playback work |
| 0 | Decrement signed delay `+0x130`; while the new value is positive omit advance. Otherwise run local activation work, advance/compose when valid at `0x00816248`, then increment the current state |
| 1 | Advance/compose when valid at `0x0081630C`; completion increments the current state and runs the two attachment-pointer passes |
| 2 | Decrement signed delay `+0x132`; when the new value is nonpositive, bind descriptor `owner+0x4BF4` with blend duration zero, request frame 1 with flag 0 at `0x008163D0` when valid, then increment the current state. This branch has no direct ordinary advance |
| 3 | Advance/compose when valid at `0x00816454`; completion stores state `-1` without destroying the embedded player |

All three ordinary advances use the current unsigned player step `+0x94`
and third argument zero. Missing tracks produce zero completion in states
1/3, so those branches do not retire a missing-track record through their
completion condition. Other state values take no matching state action.
The state-2 seek continues the loop rather than returning from the entire
owner method at the bind, as the truncated decompiler suggests.

The owner invokes virtual slot `+0x80` only when no record passed the
`state !=-1` check during that pass. Retiring the last active record in
state 3 consequently does not itself satisfy that pass's termination gate.
The counter/advance relationships here are per invocation; their elapsed
duration is unestablished.

**Submission observation:** complete `FUN_008164F0` visits all records
in render context `*(gp-0x3300)+0x2990`. It submits every state other
than `-1` or 0, with no direct seek/advance. State 2 therefore remains
eligible for submission during its delay while ordinary advance is omitted.
Resident vtable slots `+0x0C/+0x10/+0x60/+8` point to live
setup/update/submission/destructor entries
`0x00815DA0/0x008161A0/0x00816530/0x00873E90`.
Full dispatcher cadence and indirect state/control producers are untraced.

**Evidence:** decompilation of `FUN_00816160/8164F0`,
`FUN_008166A0` and `FUN_00873E50`, with complete constructor
bytes `0x00815A60..0x00815C1F`, record constructor/destructor
`0x00815C20..0x00815D5F`, setup
`0x00815D60..0x0081615F`, update
`0x00816160..0x008164EF`, submission
`0x008164F0..0x0081659F`, record reset
`0x00816650..0x0081669F`, placement query
`0x008166A0..0x0081673F`, and owner destructor
`0x00873E50..0x00873EDF`. Resident vtable bytes are
`0x005EAD40..0x005EADDF`; preserved type/name bytes are
`0x008CF308..0x008CF31F` and `0x008BBBD0..0x008BBBE7`.
Descriptor strings are preserved `0x008B5CA0..0x008B5CBF`.

## BTL ZBZ and KMV counter-gated primary players

**Ownership/descriptor observations:** resident vtables
`0x005EB030/0x005EADE0` and their type records identify
`ccSkillZBZ000New/ccSkillKMV001`, respectively. Their setup methods
`FUN_00814E60/815720` populate descriptors `+0xFF0/+0xFF4` from
container `+0x1F0`: `ANM_pzbzcha01/02` for the first class and
`ANM_pkmvcha11/12` for the second. The methods below reuse the
existing player referenced by owner `+0x320`; they do not replace its
storage. Its complete inherited allocation/destruction chain remains
unresolved.

Both complete methods increment the 16-bit counter `+0xFF8` first,
then select work using signed state halfword `+0xFFA`. The threshold
checks reload the counter as unsigned, including its stored 16-bit wrap.

| Method / preserved seek site | Local gate and transition |
| --- | --- |
| `FUN_00814FD0`, `0x00815058` | State 0 and nonzero owner word `+0x358`: bind descriptor `+0xFF0`, request frame 1, clear counter `+0xFF8`, perform local resource/effect work, then increment the current state |
| `FUN_00814FD0`, `0x008152B4` | State 1 and current unsigned counter `+0xFF8 >40`: bind descriptor `+0xFF4`, request frame 1, then increment the current state; this branch does not require nonzero `+0x358` |
| `FUN_00815870`, `0x008158FC` | State 0 and nonzero `+0x358`: clear counter, bind descriptor `+0xFF0`, request frame 1, then increment the current state |
| `FUN_00815870`, `0x008159FC` | State 1 and current unsigned counter `+0xFF8 >45`: clear counter, bind descriptor `+0xFF4`, request frame 1, then increment the current state |

Each request follows a zero-blend bind and requires player `+0xFC` to
be valid, with flag 0. State 2 and nonzero `+0x358` instead set byte
`+0xFFC =1` and invoke virtual slot `+0x230`, without taking these
seek branches. In the second method, state 1 also performs allocation/local
work at counter 5, then continues to the separately reloaded `>45` check;
the decompiler's apparent return at allocation is not the complete body.
Neither full method directly calls ordinary advance or writes the referenced
player's step. A seek here consequently identifies a descriptor-transition
request, not the owner's entire playback schedule.

Resident vtable slot `+0x100` points to the methods' live entries
`0x00815010/0x008158B0`. The first class's `+0xF8/+0xFC`
entries instead resolve to trivial return bodies
`0x00814FB0/0x00814FC0`; assigning the state method to those slots
would misidentify its phase. Full invocation cadence, inherited player
advancement and the source of `+0x358` remain untraced.

**Evidence:** decompilation of `FUN_00814FD0/815870`, with
complete method bytes `0x00814FD0..0x0081542F` and
`0x00815870..0x00815A5F`, complete setup
`0x00814E60..0x00814FAF` and `0x00815720..0x0081586F`, and
trivial bodies `0x00814FB0..0x00814FCF`. Resident vtable bytes are
`0x005EB030..0x005EB03F`, `0x005EB120..0x005EB13F`,
`0x005EADE0..0x005EADEF` and `0x005EAED0..0x005EAEEF`;
preserved type/name bytes are `0x008CF320..0x008CF357` and
`0x008BBBE8..0x008BBC1F`. Descriptor-name bytes are
`0x008B5BC8..0x008B5BE7` and `0x008B5C18..0x008B5C37`.

## BTL Water Dragon embedded player

**Ownership observation:** resident vtable `0x005EB280` and its type
record identify `ccSkillObjWaterDragon`. Constructor
`FUN_00813230` constructs the embedded player at owner `+0xD60`
and clears separate activation byte `owner+0xE80`. Actual destructor
`0x008135F0..0x0081371F` destroys it with
`FUN_001B7570(player,-1)`, then continues array/base cleanup and
optional owner deallocation. The decompiler fragment starting at
`FUN_00813610` does not expose that complete lifetime.

**Setup/order observation:** complete setup `FUN_00813720` looks up
`ANM_psrdbod1` in container `owner+0x94`, binds embedded player
`+0xD60` with blend duration zero, requests frame 1 with flag 0 at
`0x0081379C` when its track `owner+0xE5C` is valid, then installs
callback live `0x00773C20` at player `+0xE8`. These operations precede
the activation-byte check. If `+0xE80` was already nonzero, setup
advances/composes using the current unsigned step `player+0x94`
(`owner+0xDF4`) at `0x008137E0`, stores completion at `+0xEF4`
(zero for an absent track), and applies its transform. It then sets
activation byte `+0xE80 =1`, initializes scale, writes step `0x140`,
and writes player float `+0x88 =0.8f`, before continuing resource/node
setup. Thus its conditional advance uses the prior step, and the frame-one
request is eligible even while ordinary playback was disabled.

**Periodic gate observation:** complete `FUN_00813C80` advances the
valid embedded player only when signed state halfword `+0xF00 !=1`
and activation byte `+0xE80 !=0`. It uses unsigned step `+0x94`
and third argument zero at `0x00813CD4`, composes, stores completion
at `+0xEF4`, and applies the local transform. Separate attachment work
through `FUN_001BB190` still runs for active players with nonnull
`+0xEE0`, independently of state 1. The later state handling can
change `+0xF00` after the current advance decision; a new state does
not retroactively gate that earlier operation.

**Explicit transform/update observation:** complete `FUN_00814230`
copies its supplied position and rotation, applies the transform and calls
a local movement helper. It then advances/composes the valid embedded
player at `0x00814414`, followed by a separate valid-track check and
frame-one seek with flag 0 at `0x00814440`. No bind or step write occurs
between those calls. This method has no local activation-byte or state-1
gate, unlike periodic update. The API's
[active-blend seek exception](scene_playback_owners.md#playback-families) still limits what can
be inferred from its target alone. Full upstream invocation conditions
for this transform method remain unresolved.

**Submission observation:** complete `FUN_00813C10` requires only
activation byte `+0xE80 !=0`, temporarily selects render context
`+0xEF8` when nonnull, submits the embedded player and restores the
context. It neither checks state 1 nor directly seeks/advances. The static
draw gate therefore permits submission while state 1 omits ordinary
periodic advance. Resident vtable slots `+0x0C/+0x18/+0x60/+8`
point to live setup/update/submission/destructor entries
`0x00813760/0x00813CC0/0x00813C50/0x00813630`.
Their complete dispatcher ordering and cadence are untraced.

**Evidence:** decompilation of `FUN_00813720/813C80/813C10`,
`FUN_00814230` and fragment `FUN_00813610`, with complete
constructor bytes `0x00813230..0x0081345F`, destructor
`0x008135F0..0x0081371F`, setup
`0x00813720..0x00813C0F`, submission
`0x00813C10..0x00813C7F`, periodic update
`0x00813C80..0x0081406F`, and explicit transform/update
`0x00814230..0x008144EF`. Resident vtable bytes are
`0x005EB280..0x005EB31F`; preserved type/name bytes are
`0x008CF358..0x008CF36F` and `0x008BBC20..0x008BBC37`.
The setup descriptor string is preserved `0x008B5BB8..0x008B5BC7`.
Raw tails establish bind/seek/advance and continuing cleanup despite false
no-return annotations in the analyzed setup/destructor.

## BTL ANB embedded and associated players

**Ownership observation:** resident vtable `0x005EB610` and its type
record identify `ccSkillANB000`. Actual constructor
`0x00807A80..0x00807DAF` constructs an embedded animation player at
owner `+0x11B0`, clears its separate activation byte `owner+0x12D0`,
and initializes local transform/completion fields. Complete destructor
`FUN_00807DB0` destroys this player with `FUN_001B7570(player,-1)`
and continues other resource/base cleanup and optional owner deallocation.
The embedded storage is owned independently of its activation state.

**Setup/selection observations:** complete setup `FUN_008085A0`
fills 17 descriptor slots at `+0xFF0..+0x1030`, selecting a name table
from owner word `+0x56C`. A nonzero resource-name entry is looked up in
container `+0x1F0`; a zero entry stores a null descriptor. After other
resource setup it binds embedded player `+0x11B0` to descriptor
`+0x1014` with blend duration zero, requests frame 1 with flag 0 at
preserved `0x00808A58` when track `owner+0x12AC` is valid, installs
callback live `0x00773C20` at player `+0xE8`, then clears activation
byte `+0x12D0`. Setup therefore does not enable the ordinary playback/draw
gate merely by issuing this seek. Its complete raw body contains no direct
ordinary advance or player-step write.

Update `FUN_00808EE0` dispatches on signed halfword `+0x103A` through
an 11-entry live-pointer table. In case 1, the recovered range selection
uses float `owner+0x5E0` and three inclusive intervals, tested in order:
`[0,0.5]`, `[0.5,0.8f]`, `[0.8f,1]`. The first match selects index
0/1/2; no match selects `-1`. When that index differs from signed byte
`+0x1350`, the method stores the index, binds embedded player `+0x11B0`
to descriptor `owner+0x1014+4*index` with blend duration zero, requests
frame 1 with flag 0 at `0x0080923C` when valid, and reinstalls the
callback. Index `-1` consequently selects the adjacent slot `+0x1010`;
the inspected sequence has no additional index guard. Equality skips this
bind/seek sequence. Case 1 subsequently joins the shared playback tail.

| Preserved seek site | Local phase and request |
| --- | --- |
| `0x00808A58` | Initial embedded-player bind to `+0x1014`, frame 1; setup later clears the activation byte |
| `0x0080923C` | State 1 range-index change, embedded descriptor `+0x1014+4*index`, frame 1 |
| `0x00809F64` | State 4 update transition: existing associated player `+0x4D0`, descriptor index 9 / frame 3 when current byte `+0x1190 ==0`, otherwise index 4 / frame 6 |
| `0x0080CBDC` | Requested state 4: associated player `+0x4D0`, the same descriptor-index/frame pairs selected by geometry branches, also stored in byte `+0x1190` |
| `0x0080CCA4` | Requested state 4, current signed byte `+0x1350 ==0`: embedded player, descriptor `+0x1018`, frame 1 |
| `0x0080CF70` | Later requested-state-4 branch: linked player `*(owner+0x18C)+0xB34`, descriptor taken from the associated fighter's primary player `+0x90`, reusing the selected whole frame 3 or 6 |
| `0x0080D2A8` | Requested state 5, current byte `+0x1191 ==0`: embedded player, descriptor `+0x1018`, frame 1 |
| `0x0080DB88` | Controller-selection helper `FUN_0080DB40`: existing `controller+0x120` player, descriptor `owner+0xFF0+4*(index&0xFF)`, frame 1; clears controller word `+0x158` |

Every table request has a valid-track check and flag 0 after a zero-blend
bind. The two associated `+0x4D0` paths bind a null descriptor if
`FUN_003083A0(owner+0x4CC)` returns false. The update-side transition
at `0x00809F64` additionally lies behind the state-4 counter/geometry
handling, a nonnull `+0x4CC`, negative float `+0x1050`, and byte
`+0x10EA ==1`; it clears `+0x10EA` before choosing the frame pair.
The linked-player branch requires the associated-pointer predicate; its
later pointer-exchange helper and the complete linked-player lifetime are
not traced. Neither embedded state request reallocates that player.

The requested-state method actually starts at `FUN_0080C040`;
`FUN_0080C080` is its indirect-jump continuation. It saves the prior
state at halfword `+0x10E8`, stores the incoming signed-halfword state
at `+0x103A`, and skips its case work for values outside `0..10`.
Requested state 0 sets activation byte `+0x12D0 =1`. Requested state 4
also calls the earlier endpoint-seek/advance helper actual `FUN_0080DBB0`
at `0x0080C7E8`, before its later seeks above. State-4 update calls the
same helper at `0x00809624`. Their ordering connects the existing
[endpoint-seek/advance finding](#btl-requested-state-and-endpoint-sequencing)
to this owner; it does not establish an invocation cadence. Calls to the
controller-selection helper are also present in requested states
1/3/4/6/7/8/9; the full controller-player allocation/destruction chain
remains outside this local contract.

**Advance/submission observations:** the shared update tail requires
activation byte `+0x12D0 !=0`, then a valid embedded track to advance
using current unsigned player step `+0x94` (`owner+0x1244`) and third
argument zero at `0x0080AAF0`, followed by composition. It stores the
returned completion word at owner `+0x1344`, or zero when the track
is absent, and continues transform preparation. Its earlier exact-value
gate `+0x12D0 ==1` controls additional attachment/position handling;
the later advance gate accepts any nonzero value. The inspected state-1
seek can therefore precede ordinary advance in the shared tail when enabled.

Complete submission method `FUN_0080B8B0` also requires
`+0x12D0 !=0` to submit the embedded player. It temporarily uses render
context `+0x1348` when nonnull and restores the prior context, then calls
a separate object's virtual draw method regardless of this activation byte.
It performs no direct seek/advance. Resident vtable slots
`+0xF8/+0xFC/+0x228/+0x22C` point to live
`0x00808F20/0x0080B8F0/0x00807DF0/0x008085E0`, respectively.
Complete dispatcher order, all activation-byte producers and the remaining
update cases have not been recovered; the shared tail is a bounded static
contract, not an assertion that every upstream path reaches it.

**Evidence:** decompilation of `FUN_008085A0/808EE0/80B8B0`,
split `FUN_0080C040/80C080` and `FUN_0080DB40`, with complete
constructor/destructor bytes `0x00807A80..0x008081BF`, setup
`0x008085A0..0x00808EBF`, requested-state method
`0x0080C040..0x0080D49F`, controller-selection helper
`0x0080DB40..0x0080DBAF`, and submission
`0x0080B8B0..0x0080B93F`. Selected update bytes cover the prefix and
state 1 `0x00808EE0..0x0080943F`, state 4
`0x0080961C..0x0080A00F`, and shared tail
`0x0080A820..0x0080ADC7`. Preserved range/table bytes are
`0x008B4C04..0x008B4C27`, update jump table
`0x008CDA10..0x008CDA3B`, and requested-state jump table
`0x008CDA40..0x008CDA6B`. Resident vtable bytes are
`0x005EB610..0x005EB61F`, `0x005EB700..0x005EB71F`,
and `0x005EB830..0x005EB84F`; preserved type/name bytes are
`0x008CF3D0..0x008CF3F7` and `0x008BBC88..0x008BBC97`.
The truncated decompiler's apparent predicate/bind returns and incorrect
case associations do not override these raw branches and live jump targets.

## BTL FOR embedded-player pair

**Ownership observation:** resident vtable `0x005EB890` and its type
record identify `ccSkillFOR000`. Constructor `FUN_00804630`
constructs two embedded animation players at owner `+0x11A0/+0x1330`;
complete destructor `FUN_00804760` destroys each with
`FUN_001B7570(player,-1)` and continues array/base cleanup and optional
owner deallocation. Their storage belongs to the owner, independently of
whether the activation bytes below enable playback or submission.

**Activation observation:** actual state selector
`0x00805660..0x00805DDF` saves the incoming selector's low byte at
`+0xFF0`. Selector 2 performs earlier virtual, association, geometry and
request handling, then binds player `+0x11A0` to descriptor `+0x1004`
with blend duration zero and requests frame 1 with flag 0 when valid,
at preserved `0x00805A60`. It initializes local timer/transform fields
and sets that record's byte `player+0x166 =1`. It similarly binds player
`+0x1330` to descriptor `+0x1008`, requests frame 1 at `0x00805AC8`
when valid, and sets its byte `player+0x166 =1`. The raw body reaches
both sequences after its association handling; apparent decompiler returns
at those resident predicates are not retail exits.

Still in selector 2, it invokes transform helper actual `FUN_00807020`
on the second record, then update helpers actual `FUN_00806900`
on the first and `FUN_00806D80` on the second. Their ordinary advances
can therefore follow these seek requests in the same invocation. There is
no direct ordinary advance in the selector body itself. Selector 3 clears
both activation bytes while doing other state handling; selector 0 clears
a local counter, and other incoming byte values skip these two seek sites.

**Update observations:** complete `FUN_00806900` performs conditional
timer-driven position/rotation/scale work, then requires byte
`player+0x166 ==1` and nonzero track `+0xFC` to advance using the
current unsigned player step `+0x94` and third argument zero, at
`0x00806D48`, then compose. It subsequently writes player step `+0x94`
from unsigned record halfword `+0x180`, even when the advance gate is
closed. This ordering establishes a later step replacement; the producer
of record `+0x180` remains unresolved. Its positive timer branches do
not return before this common playback/step tail in the raw body.

Complete `FUN_00806D80` likewise performs timer-driven transform work,
then uses the same activation/valid-track gate and current unsigned step
for advance at `0x00806F68`, followed by composition. It has no matching
step replacement. Neither helper consumes completion or releases the player.
Owner update `FUN_00804C80` calls these helpers on the same two records
after its earlier virtual/local methods. Resident vtable slot `+0xF8`
points to this wrapper's live entry `0x00804CC0`.

**Submission observation:** owner `FUN_00804D00` calls common helper
actual `FUN_00806FA0` on both records before its other local submission.
That helper requires byte `player+0x166 ==1`, applies record position,
rotation and scale in context `0x00609160`, submits, then restores the
context. It contains no seek/advance and has no completion check. Vtable
slot `+0xFC` points to wrapper live `0x00804D40`, and `+0x228`
points to destructor live `0x008047A0`. The two helper phases and the
state-selector invocation are statically connected, but their full dispatcher
order/cadence and all record-control producers remain untraced.

**Evidence:** decompilation of split `FUN_00805660/56A0`,
`FUN_00804760`, `FUN_00806900/6D80/7020`,
`FUN_00804C80/4D00` and `FUN_00806FA0`, with complete
construction/destruction bytes `0x00804630..0x00804A3F`, selector
`0x00805660..0x00805DDF`, first update
`0x00806900..0x00806D7F`, second update
`0x00806D80..0x00806F9F`, initial transform
`0x00807020..0x0080718F`, wrappers
`0x00804C80..0x00804DFF`, and submission
`0x00806FA0..0x0080701F`. Resident vtable bytes are
`0x005EB890..0x005EBADF`; preserved type/name bytes are
`0x008CF400..0x008CF427` and `0x008BBCA8..0x008BBCB7`.

## BTL TND embedded-player group

**Ownership observation:** resident vtable `0x005EBD30` and its type
record identify `ccSkillTND001`. Actual constructor
`0x008004D0..0x0080068F` constructs a group inside the owner at
`+0x1240`, with one embedded animation player at group `+0x40`
and three more at `+0x160+i*0x150`. Resident array construction uses
record constructor live `0x007FFB40` (preserved `FUN_007FFB00`),
destructor live `0x007FFAD0` (preserved `FUN_007FFA90`), stride
`0x150` and count 3. The owner constructor clears group bytes `+0/+1`,
which are separate update/draw gates.

Complete owner destructor `FUN_00800690` runs array destruction on the
three records, then `FUN_001B7570(group+0x40,-1)`, and continues other
owner/base cleanup and optional owner deallocation. The record destructor
also calls the animation destructor with `-1`; the embedded player storage
is not independently freed. This release is separate from completion latching.

**Initial-frame observation:** `FUN_007FFB50(group,child_descriptor,
main_descriptor)` binds all three record players to the same child
descriptor with blend duration zero. For each it reads frame count `F`
and calls `FUN_00180210(3)`, then `FUN_00180210(F-3)+1` to produce
the requested whole frame. It requests that value `<<8` with flag 0
at preserved `0x007FFBF8` when valid. The random helper returns an
unsigned remainder modulo `abs(argument)+1`; for `F>=3` the second
request is in `1..F-2`. The first random result is not used as the seek
target. A general `F>=3` resource guarantee is not established.

After each request, setup initializes local placement/scale fields and
clears both record bytes `player+0x140/+0x141`. It then binds main
player `group+0x40` to the main descriptor with blend duration zero,
requests frame 1 with flag 0 at `0x007FFC80` when valid, and sets
group active byte `+0 =1`. Its direct caller at `0x00800C48` passes
`owner+0x1240`, descriptor `owner+0x1024` and descriptor
`owner+0x1038`; it later clears group draw-suppression byte `+1`.
The complete setup helper has no ordinary advance or player-step write.

**Update observation:** complete `FUN_007FFCC0` returns while group
byte `+0 ==0`. Otherwise it iterates the three child records. A record
whose byte `player+0x141 ==1` omits advance/composition. The others
advance when `player+0xFC` is valid, using unsigned player step `+0x94`
and third argument zero at preserved `0x007FFD44`, then compose.
If record byte `player+0x140 ==1` and this advance returns completion,
it writes `player+0x141 =1`; other completed records are not latched
by this method. The body continues local movement/effect bookkeeping
after the player loop. It does not directly advance main player `group+0x40`.

`FUN_00800290` takes a signed-halfword record index and descriptor in
`a2`, clears that record's local word at `group+0x290+index*0x150`,
binds its existing player with blend duration zero, requests frame 1 with
flag 0 at `0x00800304` when valid, and sets `player+0x140 =1`.
Its complete body does not clear `player+0x141`, call ordinary advance
or write the player step. Thus this bind/seek does not by itself establish
resumption of a record already latched by update. A direct caller exists
at `0x008012DC`; its full request gates remain untraced.

**Submission/scheduling observations:** actual submission entry
`0x007FFFD0..0x0080028F` requires group byte `+0 !=0` and
draw-suppression byte `+1 ==0`, then submits all three child players
with per-record transforms and main player `group+0x40`. It does not
check the child completion latch before submission, and contains no direct
seek/advance. An ended child can therefore remain eligible for submission
while its ordinary update is omitted. This is a static gate relationship,
not an observation of any particular displayed instance.

Owner update `FUN_00800E30` invokes group update through preserved
JAL `0x00800EAC` after its virtual/local-object operations. Owner draw
`FUN_00800ED0` invokes group submission at `0x00800EE8` before
handling another embedded player. Resident vtable slots `+0xF8/+0xFC`
point to their live entries `0x00800E70/0F10`; `+0x228` points to
destructor live `0x008006D0`. Full dispatcher cadence and all producers
of the group's draw/update gates remain unresolved.

**Evidence:** decompilation of split `FUN_00800510`,
`FUN_00800690`, `FUN_007FFB00/7FFB50/7FFCC0/7FFD00`,
`FUN_00800010/800290/800E30/800ED0`, with complete construction/destruction
bytes `0x008004D0..0x0080095F`, record constructor/destructor
`0x007FFA90..0x007FFB4F`, setup
`0x007FFB50..0x007FFCBF`, update
`0x007FFCC0..0x007FFF6F`, submission
`0x007FFFD0..0x0080028F`, record reassignment
`0x00800290..0x008004CF`, and wrapper bytes
`0x00800E30..0x00800FAF`. Setup caller bytes
`0x00800BA0..0x00800D0F` establish the group pointer/descriptors;
exact JAL searches find one direct update, submission and reassignment
caller each. Resident vtable bytes are `0x005EBD30..0x005EBF7F`;
preserved type/name bytes are `0x008CF440..0x008CF457`
and `0x008BBCC8..0x008BBCD7`. Resident random-helper disassembly
`0x00180210..0x00180258` establishes unsigned modulo and absolute argument
handling rather than the decompiler's misleading signed-remainder expression.

## BTL CHY supplementary player

**Ownership observation:** resident vtable `0x005EF5D0` and its type
record identify `ccSkillCHY000`. Constructor `FUN_007E4EE0` clears
owner player slot `+0x1110`. Setup `FUN_007E5370` resolves
`ANM_pchycha03` through owner container `+0x1F0`; a nonnull descriptor
enables allocation/construction of an `0x120` player and storage at
`+0x1110`. It binds with blend duration zero and requests cursor zero
with flag 0 when the track is valid, then continues object/resource lookups.
No ordinary advance appears in this setup body. The zero request does not
prove that frame-zero records were evaluated: the equal-cursor return
described under [playback families](scene_playback_owners.md#playback-families) still applies.

**Update observation:** complete `FUN_007E4FB0` handles earlier owner
events before its supplementary-player pass. Owner `+0x2C8 >0` and the
primary player's integer cursor equal to `F-5` enable a separate event;
owner `+0x1DC ==1` takes a randomized local callback path. Neither path
returns before the supplementary player in the raw body, despite the
decompiler's apparent return at the random helper. The method then requires
nonnull `+0x1110`, sets its transform from owner `+0x330/+0x340`, and
advances/composes when `+0xFC` is valid, using unsigned player step
`+0x94` and third argument zero. Completion is ignored; this method does
not unlink or destroy an ended player.

**Submission/release observations:** separate `FUN_007E51F0` submits
a nonnull `+0x1110`. Its fighter-predicate/geometry checks choose either
the default render context `0x00609160` or the context at
`*(gp-0x31AC)+0x32E0`, then restore the previous context after submission.
Those checks select a context rather than skipping the draw, and this
body contains no seek/advance. Complete destructor `FUN_007E4F20`
destroys the nonnull player with `FUN_001B7570(player,1)`, clears
`+0x1110`, invokes base destruction and optionally deallocates the owner.
Ignoring completion in update is therefore distinct from this ownership
release.

The class vtable connects update/draw through slots `+0xF8/+0xFC`
to live `0x007E4FF0/5230`, setup through `+0x22C` to live
`0x007E53B0`, and destructor through `+0x228` to live
`0x007E4F60`. The full dispatcher gate/cadence remains unresolved.

**Evidence:** decompilation of `FUN_007E5370/4FB0/51F0`,
complete construction/destruction bytes `0x007E4EE0..0x007E4FAF`,
update `0x007E4FB0..0x007E51EF`, submission
`0x007E51F0..0x007E536F`, and setup
`0x007E5370..0x007E54DF`. The additional seek is preserved
`0x007E5440`, and advance is `0x007E51BC`. Asset/object strings
are preserved `0x008B2750..0x008B276F`; resident vtable fragments
are `0x005EF5D0..0x005EF5DF`, `0x005EF6C0..0x005EF6DF`
and `0x005EF7F0..0x005EF80F`, with preserved type record/name
bytes `0x008CF758..0x008CF777` and `0x008BBEA8..0x008BBEB7`.

## BTL wall and gate players

**Ownership observation:** preserved setup `FUN_007B36D0` resolves
`ANM_phkgwal00` through owner resource `+0x94`, allocates/constructs
an `0x120` player, binds the descriptor with blend duration zero and stores
the player at owner `+0xAF0`. It requests frame 1 with flag 0 when valid,
then establishes the transform. Resident vtable `0x005F84C0` is tied by
its type record to name `ccSkillHKG001Wall`; the name identifies this
inspected retail class without assigning a player-facing character/action.

**Advance observation:** method `FUN_007B3F00`, selected by vtable slot
`+0x10` through live `0x007B3F40`, advances only when signed owner word
`+0xAD4` has even remainder modulo 2. A valid player consumes its unsigned
step `+0x94`, third argument zero, then composes; completion is stored
at owner `+0xAF4`. Odd values skip this advance/completion assignment,
but still reach transform and later object/contact handling. Counter zero
also caches the player's `OBJ_wall_top` object in owner `+0xAF8`.
With that cache nonnull and completion zero, a `FUN_001BF100` result
different from `-1.0` writes player step zero and clears the cache.
That happens after the parity-selected advance; cache clearing does not
destroy the player.

**Counter-producer observation:** the same vtable's slot `+0x64` points
to live `0x00781320`, actual preserved `FUN_007812E0`. With owner byte
`+0xA20` bit 0 clear, owner byte `+0` bit 1 set and `+0xAE4` bit 0
clear, this method calls virtual slot `+0x18`, performs local event/countdown
handling and increments `+0xAD4` once. When `+0xA20` bit 0 is set, it
instead calls virtual slot `+0x74` and increments signed-halfword
`+0xA22`; it does not increment `+0xAD4` on that arm. Common initialization
`FUN_0077F2B0` writes `+0xAD4` zero. The counter is therefore tied to a
gated owner phase. The scheduling/order of the counter method relative to
the playback method is not established here, so this does not prove an
advance every two rendered frames.

**Other phases:** endpoint method `FUN_007B3E40`, vtable slot `+0x34`,
requests `(F-1)<<8` with flag 0 when valid and changes neither the step
nor ownership. Submission `FUN_007B4420`, vtable slot `+0x80`, installs
its render context, calls `FUN_001BB790` on `+0xAF0`, restores the context
and returns; its complete body has no seek/advance or local parity gate.
Full destructor `FUN_007B3310` destroys the owned player through
`FUN_001B7570(player,1)`, clears `+0xAF0`, releases other local resources
and invokes base destruction before optional owner deallocation. These
phases distinguish omitted increments, a zero step, endpoint selection,
submission and ownership release in one class.

**Parallel owner observation:** resident vtable `0x005F50E0` and its
type record identify `ccSkillSKV001Gate`, with owned player at `+0xDC0`.
Allocation method `FUN_007CAE00`, vtable slot `+0x5C`, creates that
player only when owner counter `+0xAD4 ==0` and the slot is null. It
resolves `ANM_pskvcha13`, allocates/constructs an `0x120` player, binds
with blend duration zero, requests frame 1 with flag 0 when valid, sets
transform and writes step `0x40` before storing it at `+0xDC0`. The
remaining method wraps a base operation with player handling, so its
construction branch is not an unconditional return at the resource lookup.

Its update `FUN_007CB050`, vtable slot `+0x10`, performs position handling
before applying the same even-`+0xAD4` advance gate. Valid playback uses
unsigned step `+0x94`, third argument zero and composition, storing
completion at `+0xDF0`. Counter zero caches `OBJ_wall_top` at `+0xDC4`.
Subsequent transform/contact handling also runs on odd counter values; its
probe-result branch writes step zero and clears that cache after playback.
This vtable also maps slot `+0x64` to the shared `FUN_007812E0` counter
producer described above. The local step `0x40` and the counter gate are
separate controls; their values alone do not establish elapsed-time cadence.

Endpoint method `FUN_007CAC50`, slot `+0x34`, requests `(F-1)<<8`
without changing the step. Draw method `0x007CB430`, slot `+0x80`,
submits a nonnull `+0xDC0` under its render context with no local parity
gate or playback call. Complete destructor `FUN_007CA0D0` destroys and
clears `+0xDC0`, then continues other local/base destruction and optional
owner deallocation. The two classes therefore share a counter producer
and increment-omission policy while retaining their own player slots,
construction steps, completion fields and lifetimes.

**Evidence:** decompilation of `FUN_007B3E40/3F00/4420` and
`FUN_007812E0`; complete bytes `0x007B36D0..0x007B383F`,
`0x007B3E40..0x007B3E8F`, `0x007B3F00..0x007B441F`,
`0x007B4420..0x007B446F`, `0x007B3310..0x007B341F`,
`0x007812E0..0x0078141F`, initialization prefix
`0x0077F2B0..0x0077F2FF`, resident vtable
`0x005F84C0..0x005F856F`, type record
`0x008CFF98..0x008CFFA7`, type-name bytes
`0x008BC380..0x008BC397`, and asset/object strings
`0x008AF490..0x008AF52F`. The construction seek is preserved
`0x007B37AC`; endpoint seek is `0x007B3E6C`, and advance is
`0x007B3F64`.
The gate-player findings use decompilation of
`FUN_007CA0D0/CAE00/CB050/CAC50`, complete bytes
`0x007CAE00..0x007CB04F`, `0x007CB050..0x007CB47F`,
`0x007CA000..0x007CA1DF`, resident vtable
`0x005F50E0..0x005F518F`, type record
`0x008CFC18..0x008CFC37`, type-name bytes
`0x008BC110..0x008BC127`, and asset strings
`0x008B08C0..0x008B095F`. Its additional construction seek is
preserved `0x007CAEC0`; endpoint seek is `0x007CAC7C`, and
advance is `0x007CB114`.

## BTL linked-player owners

**Ownership observation:** a separate BTL family stores a player-list head
at owner `+0x10B4`. Each node is a freshly allocated `0x130`-byte animation
player, with flags at `+0x120`, an optional render-context pointer at
`+0x124`, and next pointer at `+0x128`. The recovered setup paths below
look up descriptors in owner container `+0x1F0`, construct/init the player,
bind with blend duration zero, and request cursor zero with seek flag 0
when player `+0xFC` is valid. They clear flags/context, prepend the node,
then install their flag mask. Each resource name in the table was recovered
from the live pointer's preserved bytes; no character/action identity is
assigned from the resource prefix alone.

| Preserved setup entry | Resource names, in construction order | Seek sites / installed masks |
| --- | --- | --- |
| `0x007C8400` | `ANM_ptyvcha03`, `ANM_ptyvcha04` | `0x007C84FC/85B8`; both 0 |
| `0x0084C3A0` | `ANM_pinwcha03` | `0x0084C478`; 1 |
| `0x0084CBB0` | `ANM_psnwcha04` | `0x0084CCA0`; 1 |
| `0x0084D130` | `ANM_tnw_effect` | `0x0084D208`; 1 |
| `0x0084D7E0` | `ANM_ptywcha03` | `0x0084D8B8`; 1 |
| `0x0084DC80` | `ANM_pbdycha33`, `ANM_pbdycha34` | `0x0084DD70/DE3C`; 2, 1; first node also stored at owner `+0x1110` |
| `0x0084E360` | `ANM_porwcha03` through `ANM_porwcha08` | `0x0084E450/E518/E5E0/E6A8/E770/E838`; 2, 2, 2, 2, 2, 1 |
| `0x0084F300` | `ANM_sswcha0_effect` | `0x0084F3F0`; 1 |
| `0x0084F920` | `ANM_pjrwcha03`, `ANM_pjrwcha04` | `0x0084F9F8/FAC0`; 1, 2 |
| `0x00850500` | `ANM_psaicha03` | `0x008505D8`; 2 |
| `0x008510B0` | `ANM_pbdycha13` | `0x008511A0`; 2 |
| `0x00851630` | `ANM_pbdycha43` through `ANM_pbdycha47` | `0x0085170C/17D4/189C/1990/1A84`; 2, 3, 2, 2, 2 |
| `0x008520A0` | `ANM_pbdycha22`, `ANM_pbdycha23` | `0x00852194/225C`; 2, 1 |
| `0x00852590` | `ANM_pbdycha03/04/05/06` | `0x00852684/2750/281C/2978`; 2, 2, 2, 1 |

These 30 direct seek sites are construction requests. The complete setup
bodies contain no ordinary advance/compose for these list nodes. A zero
request after a fresh zero-blend bind must not be described as proof that
the seek evaluated frame-zero records: the API's equal-cursor return still
applies. The active-blend exception is a separate API behavior, rather than
evidence that these fresh nodes were already blending. Some setup bodies
also bind models or a separate embedded player; those resources do not
change the list-node classification.

**Advance observation:** common preserved `FUN_0079C1F0` walks this list
and first sets each node's transform through `FUN_0019C970`. Mask bit 0
clear uses owner vectors `+0x330/+0x340`; bit 0 set uses the VU constant
`vf0` position vector and a zero rotation vector. It then requires node
`+0xFC` and advances/composes with unsigned node `+0x94`, third argument
zero. The complete loop ignores the advance result, does not unlink an
ended player, and has no local pause check. Installed mask 2 therefore
still takes the owner-vector branch, while masks 1 and 3 take the constant
branch. The meaning and consumers of mask bit 1 remain unresolved.

The same local list pass precedes further owner logic in inspected
`FUN_007C7BB0`, `FUN_0084C4C0`, `FUN_0084CD30`,
`FUN_0084DEE0`, `FUN_0084EA90`, `FUN_0084FCE0`,
`FUN_00850680`, `FUN_008512A0`, `FUN_00851DB0`, and
`FUN_00852350`. For example, `FUN_0084C4C0` finishes the list pass before
its owner `+0x1DC ==0x78` event. That later event is not a gate on the
preceding node advances. This identifies the inspected pass order; it does
not establish the frequency or full upstream gate of any owner method.

**Caller observation:** the thin wrapper at preserved `0x0079A930`
encodes a call to live `0x0079C230`, which is the actual common update's
preserved `0x0079C1F0` entry. Resident base vtable `0x005FB240` supplies
the wrapper's live address `0x0079A970` at slot `+0xF8`, and the draw
wrapper's live `0x0079A990` at `+0xFC`. Derived vtable `0x005E5B80`
instead supplies live `0x0084C500` (preserved update `0x0084C4C0`) at
`+0xF8`, retains the common draw wrapper at `+0xFC`, and supplies live
`0x0084C3E0` (preserved setup `0x0084C3A0`) at `+0x22C`. Its destructor
at preserved `0x00872780` installs that table in owner `+0x110` before
calling the base destructor. These bytes connect the methods through
retail virtual dispatch without requiring analyzed direct xrefs to agree
with the import address shift. The full dispatcher calling slots
`+0xF8/+0xFC/+0x22C` is not recovered here.

**Submission observation:** common preserved `FUN_0079C2C0` installs
default render context `0x00609160`, walks the same list, temporarily uses
nonzero node `+0x124` as that node's render context, and calls
`FUN_001BB790`. It restores the preceding context between nodes and the
original context at return. There is no seek or advance in this body.
Thus `+0x124` is a context override in this path, not a completion latch.
The common draw wrapper at preserved `0x0079A950` calls live
`0x0079C300`, locating the actual preserved `0x0079C2C0` body.

**Release observation:** common preserved `FUN_0079C170` saves each
node's `+0x128` before calling `FUN_001B7570(node,-1)` and then
`FUN_00117000(node)`. It repeats for all nodes; the apparent decompiler
return after the first player destructor is contradicted by the raw loop.
This helper does not clear owner `+0x10B4` in its inspected body. The base
owner destructor at preserved `0x00797360` installs vtable `0x005FB240`
at owner `+0x110` and calls live `0x0079C1B0`, recovering the list release
entry. This supplies a destruction path separate from the update's ignored
completion result; it does not prove that every owner shutdown route was
enumerated.

**Evidence:** decompilation of the common update/draw and listed
advance methods; complete common update bytes `0x0079C1F0..0x0079C2BF`,
release bytes `0x0079C170..0x0079C1EF`, wrappers
`0x0079A930..0x0079A96F`, base-destructor prefix
`0x00797360..0x007973DF`, and derived-destructor bytes
`0x00872780..0x008727EF`. Constructor bytes were recovered through their
returns within `0x007C8400..0x007C85EF`,
`0x0084C3A0..0x0084C4BF`, `0x0084CBB0..0x0084CD2F`,
`0x0084D130..0x0084D24F`, `0x0084D7E0..0x0084D8FF`,
`0x0084DC80..0x0084DEDF`, `0x0084E360..0x0084E87F`,
`0x0084F300..0x0084F43F`, `0x0084F920..0x0084FB0F`,
`0x00850500..0x0085067F`, `0x008510B0..0x0085129F`,
`0x00851630..0x00851B5F`, `0x008520A0..0x0085234F`, and
`0x00852590..0x008529BF`. Name bytes are preserved
`0x008B0400..0x008B043F`, `0x008B8C78..0x008B9187`, and
`0x008B90B0..0x008B96CF`; live name pointers in the constructors are
`0x40` higher. Resident vtable bytes are
`0x005FB240..0x005FB4CF` and `0x005E5B80..0x005E5DEF`.

## BTL descriptor-switched player array

**Ownership observation:** preserved `FUN_00853110` owns a different
playback record at owner `+0x1074`: player-array pointer `+0x1078`,
per-instance float-array pointer `+0x107C`, signed count `+0x1080`, and
five descriptor pointers `+0x1084..+0x1094`. Its recovered body destroys
previous arrays, allocates four players of stride `0x120` plus four floats,
and stores count 4. The player-array constructor is live `0x006E0450`,
preserved `FUN_006E0410`; it constructs the transform/reader and initializes
player state. The five lookups use live table `0x008B9720`, preserved
`0x008B96E0`, whose live pointers resolve to preserved strings
`ANM_pnwvcha10t` through `ANM_pnwvcha14t`. Setup binds descriptor
`+0x1084` to every player with blend duration zero and requests frame 1
with flag 0 at preserved `0x00853340`. It then calls the common update
through live `0x00854600`, actual preserved `0x008545C0`.

State method `FUN_00853390` selects later descriptors from owner state
`+0x2C8`. Each transition below reuses the four players, binds its selected
descriptor with blend duration zero, and seeks only players with `+0xFC`.
All seeks use flag 0.

| Local state branch and transition gate | Descriptor / requested target | Preserved seek |
| --- | --- | --- |
| State `-1`, owner `+0x358 !=0`; virtual state setter requests state 0 | `+0x1088`; independently calls `FUN_00180210(F-1)+1` per player, then shifts left 8 | `0x00853484` |
| State 0, after virtual predicate slot `+0xF4` returns low byte zero; setter requests state 1 | `+0x108C`; frame 1 | `0x008539E8` |
| State 1, owner `+0x358 !=0`; setter requests state 2 | `+0x1090`; the same per-player randomized target formula | `0x00853E74` |
| State 2, incremented owner counter `+0xFF0` exceeds signed limit `+0xFF4`; setter requests state 3 | `+0x1094`; frame 1 | `0x0085414C` |

Here `F` is the selected descriptor's word `+0x0C`. Resident random helper
instructions use unsigned remainder modulo `abs(argument)+1`; for positive
`F`, the caller's requested whole frame is therefore in the inclusive
range `1..F`, including the endpoint `F`. No additional frame clamp appears
between that calculation and seek. The requests are state-transition
phase choices, not variable periodic increments. Earlier geometry and
associated-resource logic in each branch does not establish a high-level
action name or the meaning of the transition fields.

**Advance observation:** all inspected state branches converge at preserved
`0x00854194` and call the common helper through encoded live
`0x00854600`; setup has the other recovered direct call at
`0x00853364`. The helper actually starts at preserved `0x008545C0` and
returns at `0x008547F8`. It looks up an object in owner `+0x320`, prepares
its transform, then advances/composes every valid array player with unsigned
`+0x94`, third argument zero. It ignores completion results. Subsequent
passes apply each instance's float offset to the transform and copy an
associated fighter player's `+0x88` value, or zero, into all array players.

The raw body contradicts a material decompiler gate: owner byte `+0x389`
and the result of `FUN_003083A0(owner+0x31C)` select whether an additional
transform vector is copied. Neither branch skips the player advance loop
at `0x00854680..0x008546E4`. The analyzed fragment `FUN_00854600`
starts inside the enclosing helper's earlier branch; its apparent
byte-conditioned early return is not a retail pause contract. The full
upstream invocation gate remains unresolved.

**Submission/release observations:** separate `FUN_008541E0` submits all
array players with `FUN_001BB790`, using render context `0x00609160` and
bracketing associated fighter rendering. It performs no seek or advance.
Resident owner vtable `0x005E29D0` slots `+0xF8/+0xFC` point to live
`0x008533D0/0x00854220`, resolving the preserved state/update and draw
methods. Cleanup `FUN_00852C90` reaches a continuing tail that destroys
the player array through `FUN_00119180(array,FUN_001B7570)`, releases
the float array through `FUN_00119490`, and clears both pointers. Setup
uses the same array-release pair before replacement; transition seeks do
not destroy/reallocate these players.

**Evidence:** decompilation of `FUN_00853110/53390/541E0/545C0`,
its split `FUN_00854600`, `FUN_00852C90`, and `FUN_006E0410`;
complete setup bytes `0x00853110..0x0085338F`, state body
`0x00853390..0x008541DF`, common update
`0x008545C0..0x008547FF`, and cleanup tail
`0x00852F38..0x00853067`. Names/table bytes are
`0x008B9690..0x008B96FF`; resident vtable bytes are
`0x005E2AC0..0x005E2AEF`. Complete resident disassembly
`0x00180210..0x00180258` confirms the random helper's `divu`/`mfhi`
argument contract. A direct-JAL byte search for live `0x00854600` found
exactly the setup/state calls above; indirect callers remain outside
that result.

## BTL buddy-resource descriptor changes

**Ownership observation:** setup starts at preserved `0x00887F90`, not
the analyzed continuation `FUN_00887FD0`. It obtains containers through
formatted `buddy/2%sbdy.ccs` and `buddy/2%sbdy%d.ccs` paths, replaces a
separately allocated `0x120`-byte player at owner `+0x70`, and fills five
descriptor slots `+0x80..+0x90`. The descriptor-name formatter uses
`ANM_p%s%s%d`; the inspected switches and format tables do not establish
the selected character/action for an arbitrary instance. Setup installs
resident callback `0x00308DC0` at player `+0xE8`, requests frame 1 at
preserved `0x00888378`, then later forces descriptor selector zero through
the helper below. Thus the early setup seek is not the final descriptor
selection in that body.

**Descriptor-change observation:** preserved `FUN_008893F0` returns early
only when the force argument's low byte is zero and the requested selector
already equals owner byte `+0x98`. Otherwise it binds
`owner.descriptors(+0x80)[selector]` to player `+0x70` with blend duration
zero, requests frame 1 with flag 0 if `+0xFC` is valid, runs virtual slot
`+0x64` and conditionally slot `+0x70`, then stores the selector, clears
completion byte `+0xF1`, and sets byte `+0xF0 =1`. The sole recovered
direct JAL to its live entry `0x00889430` is setup at preserved
`0x0088862C`, with selector 0 and force 1. Other descriptor-change paths
inline the same bind/seek/latch sequence.

| Preserved seek site(s) | Local owner phase / selected descriptor |
| --- | --- |
| `0x00888378` | Initial player construction, before the later forced selector call |
| `0x0088945C` | General selector helper, slot `+0x80 + selector*4` |
| `0x0088965C/8974C/89854/898F4` | State setter starting at actual `0x00889500`: requested owner byte `+0xE6` values 1/2/3/4 select descriptor slots `+0x84/+0x8C/+0x90/+0x80`, respectively |
| `0x008899DC` | `FUN_00889970`, local state halfword `+0xE8 ==0` and selector `+0x98 !=0`; slot `+0x80` |
| `0x00889D1C/89F2C/8A048/8A0D0/8A1C4/8A3F8/8A4DC/8A634` | `FUN_00889BD0`, local substate/completion/geometry branches; respective slots `+0x90/+0x84/+0x84/+0x90/+0x88/+0x80/+0x84/+0x88` |

All 15 direct seeks in this family request `0x100`
(frame 1) with flag 0 and a valid-track guard. Each selector/state seek in
the table follows a zero-blend bind and clears the completion latch before
setting the one-invocation suppression byte. Their role is descriptor
replacement, rather than a periodic looping rule. Recovered retail tails
continue after resident lookups and binds despite false no-return
boundaries in several analyzed functions.

**Rate observation:** periodic update actually starts at preserved
`0x008886E0` and returns at `0x00888D68`; `FUN_00888720` is a fragment
inside its initial rate branch. The owner chooses the player step before
its later gates. When live helper `0x00772BD0` returns low byte 1, it
copies unsigned step `+0x94` from the primary fighter player
`fighters[owner.s8(+0xE4)]+0xE70`. The helper's preserved body
`0x00772B90..0x00772BC8` returns true for the optional global-context
pointer's `+8` object having word `+0x14 ==3`; that field's high-level
meaning is unresolved. Otherwise, an associated opposite fighter satisfying
`FUN_00306420(fighter,0x4A)` and a subsequent geometry-helper result
`<=400` selects step `0x40` (owner float `+0xE0 =0.25`); the other branch
selects `0x100` (float 1). The copied-step branch stores step/256 in that
float. These are recovered rate producers, not timing observations.

**Gate/order observation:** rate preparation is followed by owner cursor
bookkeeping: `+0xF8` captures player `+0xEC` with its fraction cleared,
while separate accumulator `+0x108` adds the chosen step. Bytes
`+0x100/+0x110` report whole-frame changes in those respective values.
Both occur before owner byte `+0xF2` is checked. A nonzero `+0xF2`
skips the later state/advance/transform pass; value 1 becomes 2 before
return. This gate consequently does not stop the earlier accumulator.

With `+0xF2 ==0`, virtual state handlers for owner `+0xE6` run before
the advance decision. A handler can replace the descriptor and set
`+0xF0 =1` in that same invocation. Nonzero `+0xF0` then skips ordinary
advance/compose and the adjacent `FUN_001BB190` call; the update clears
`+0xF0` afterward and continues its transform/attachment pass. Otherwise,
the valid player advances/composes using unsigned `+0x94`, argument 3
zero, and stores the advance result in owner byte `+0xF1` (zero when the
track pointer is absent). This is suppression for one eligible invocation
after a descriptor change, separate from the `+0xF2` gate. The full
upstream schedule and all producers of `+0xF2` remain unresolved.

**Submission/release observations:** submission starts at preserved
`0x00888D70`; it also returns early for nonzero owner `+0xF2`. Its later
body submits player `+0x70`, with virtual hooks and temporary transform
adjustments, but no direct seek/advance. Cleanup's recovered
`0x00887E30..0x00887E80` destroys/clears player `+0x70`, effect `+0x74`
and composition `+0x78` in sequence. The apparent return immediately after
player destruction in the analyzed `FUN_00887D90` is contradicted by those
bytes. Container retention beyond these local releases is not established.

**Evidence:** decompilation of `FUN_00887FD0`, `FUN_00888720`,
`FUN_00888DB0`, `FUN_008893F0`, `FUN_00889540`,
`FUN_00889970`, `FUN_00889BD0`, and `FUN_00887D90`; bytes
`0x00887F90..0x00887FDF`, setup/descriptor setup
`0x00888000..0x0088854F`, setup tail `0x008885F0..0x008886DF`,
update prefix `0x008886E0..0x00888A2F`, update tail
`0x00888B30..0x00888D6F`, draw prefix `0x00888D70..0x00888DEF`,
selector `0x008893F0..0x008894BF`, state setter
`0x00889500..0x0088997F`, substate methods
`0x00889970..0x00889BCF` and `0x00889BD0..0x0088A77F`, and cleanup
`0x00887E08..0x00887EB7`. Resource-format bytes are preserved
`0x008BF600..0x008BF663`. Direct advance byte census contains one site
for this family, preserved `0x00888BB8`; raw surrounding instructions
establish the owner and gate. The selector-JAL search does not enumerate
indirect callers.
