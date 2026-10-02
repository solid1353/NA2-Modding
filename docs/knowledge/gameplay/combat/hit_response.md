# Battle hit-response state

This document records the native battle state entered after a hit has already
been accepted in retail NA2 (`SLPS-25837`). It covers ordinary hit reactions,
table-driven displacement, launch/ground-contact branches, downed recovery,
and guarded-hit reactions.

The names below describe demonstrated control-flow behavior. They are not
claims about the game's original internal terminology.

## Research coverage

- **Assigned scope:** battle hit-response state after an incoming hit has
  already passed acceptance: ordinary reaction selection and timing, planar
  and vertical response motion, launch/contact transitions, timed downed
  recovery and get-up choices, character contact-flag and recovery-source
  lifetimes, conditional rehit protection, how attack-record fields select
  these, and guarded-reaction entry and exit.
- **Exploration depth:** static, bounded tracing of the accepted-hit router,
  the ordinary selection, initialization, transition and update chain, timed
  downed recovery, the guard routines and rehit classifiers; the per-update
  order from `FUN_001F03E0` through the fighter coordinator and the
  attacker-side pause; animation timing through the character loader, phase
  animation selector and CCS animation-chunk loader; knockback and gravity;
  contact-rebound proposal and entry, both ordinary input-recovery predicates,
  effect membership and removal; all 74 primary response callbacks plus Guy's
  delegated handler, and all five direct BTL callers of the downed handoff;
  selected Lee, Guy, Deidara, Classic Lee and Loopy Fist Lee bodies; and the
  recovery-source writers. Directly required helpers and callers were traced
  far enough to establish field ownership, ordering, thresholds and exit
  consumers; unrelated callers, immediate-offset aliases and indirect callers
  were not exhaustively classified. Decoded authored data is exhaustive for:
  - all 54 `0x18`-byte ordinary motion/timing rows for substates `0x27..0x5C`
    at resident runtime `0x00407670` (ELF file `0x00307770`);
  - all 60 native descriptor slots, identifiers, and reachable phase records
    for substates `0x27..0x62` from the overlay descriptor table at live
    `0x0089AEB0` (file `0x001E6FB0`);
  - all ten `0x1C`-byte guarded-response rows at resident runtime
    `0x00407550` (ELF file `0x00307650`);
  - the hit-response fields (`+0x10`, `+0x14`, `+0x2C`, `+0x2D`, `+0x2E`,
    `+0x30`, `+0x32`) of all 3,428 records in the 74 primary action tables;
  - the animation names and animation-chunk frame counts of every slot used
    by substates `0x27..0x62` for those 74 records, from `CMN/2CMNBOD1.CCS`
    and the characters' `PL/2???BOD1.CCS` files: all 40 referenced slots
    resolve for every character across 75 files; and
  - all five guard-animation slots for those 74 primary records.
- **Confirmed coverage:** the ordinary/guarded accepted-hit split and
  source-mode-specific rejection, interception, and paired-fighter side
  effects; selector mappings and bounded overrides with the authored
  distribution of every selector and timing field; descriptor phase
  conditions, non-default rates, native animation names and the
  animation-gated length of every phase; table-driven impulses and damping,
  the attack knockback scale and hit-response gravity; the exact per-update
  order of hit routing, event `0`, receiver and attacker pauses, lock,
  animation and timeline advance, giving elapsed counts in 30 Hz fighter
  updates; contact, held and downed handoffs; contact-rebound proposal order,
  its attack-flag suppression/override and live callback writers; the
  first-grounded and later input-recovery predicates, input-history timing,
  effect-ID suppression and receiver ownership, recovery motion and direct
  entry exceptions; timed/input recovery thresholds, input priority and exit
  rejection writes; bounded recovery-source persistence; guard initialization
  and transition gates; the conditional-rehit predicate and the `+0x230`
  rejection countdown with their consumers; ordinary-hit counter
  initialization; all 74 response-callback entries; and overlay downed
  overrides with stage-owned recovery placement. Control flow and inputs
  establish major `5` as the ordinary hit-response family, `(6,0x5D)` as a
  timed downed state, and the two threshold-triggered paths as get-up
  choices; these roles are strong inferences because the animations were not
  visually observed.
- **Unresolved or untested:** exact ground-contact timing of `G`, `O`, and
  `B` phases, which depends on stage collision geometry; visual confirmation
  of animation roles and player-facing move names, including which native
  action the player-facing term *rebound* identifies; non-default input
  bindings; full match reachability of the character callback branches,
  signed chain-byte wrap, and player-facing identities of the five overlay
  downed owners; and the distinction among hurtbox, collision, and
  higher-level target selection. Rate-writer coverage is bounded to the
  identified fighter/effect paths. Contact-flag restoration outside the
  inspected reset/setup families, Deidara's response-window baseline lifetime
  outside the named branches, and all recovery-source pointer aliases remain
  unresolved. No separate native rebound meter was established. The
  retention of the per-side statistic bank across fighter construction is
  resolved in [Awakening](../characters/awakening.md#state-retained-across-the-native-rebuild).
- **Deliberate exclusions and overlap:** [Collision](collision.md) owns
  collision-candidate generation; [Damage](damage.md) owns damage and
  scaling; [Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md)
  owns generic effect processing; [Chakra and guard](chakra_and_guard.md)
  owns resources and the guard-input lifecycle; [Match outcomes](../session/match_outcomes.md)
  owns outcomes; [Battle statistics](../session/battle_statistics.md) owns
  statistic-derived conditions; [Practice mode](../modes/practice_mode.md)
  owns Practice mechanics; [Extra Hit](extra_hit.md) owns the paired exchange;
  [Throws and captures](throws_and_captures.md) owns capture coordination;
  [Combat action execution](combat_action_execution.md) owns common action
  and phase dispatch; [Target selection](target_selection.md) owns source and
  provenance contracts; [Character action callbacks](../characters/character_action_callbacks.md)
  owns character algorithms beyond the response-callback audit.
- **Evidence limitations:** the investigation was static and bounded rather
  than globally exhaustive. No live-memory capture was used, so control flow
  and clean authored values do not establish visual animation roles,
  player-facing move names, or all possible hit outcomes. Update counts are
  derived from the traced update order and the documented 30 Hz cadence, not
  measured; physics-gated phases and character callbacks can change them.

## Evidence identity and address conventions

Binary identities and address conversions are defined in
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
Overlay routines named by a preserved export label below (for example
`FUN_0071f120`) have live entry `export + 0x40`; raw encoded pointers and JAL
targets are already live. Resident addresses take no such bias.

## Fighter fields used by the response machine

These fields are statically confirmed by reads and writes in the routines
described below:

| Fighter offset | Type | Demonstrated use |
| ---: | --- | --- |
| `+0x18E` | `s16` | Major action state. Ordinary accepted hits enter `5`; timed downed recovery uses `6`; guard stance/reactions use major `0`. |
| `+0x190` | `s16` | Action substate. Ordinary response substates occupy `0x27..0x5C`; downed recovery uses `0x5D..0x62`; guard uses `5..7`. |
| `+0x192` | `s16` | Phase within the current action. The overlay phase setter writes it directly. |
| `+0x1AC` | `f32` | Current fighter update-rate scalar used to advance the action timelines and decrement the action-lock block. |
| `+0x1B0` | `f32` | Local override source for `+0x1AC`; response `0x4F` temporarily changes it on both paired fighters. |
| `+0x1C4` | `s32` | Primary action-timeline cursor tested by reaction completion and downed-recovery thresholds. |
| `+0x1E8` | `s32` | Secondary action-timeline cursor tested by positive phase-record thresholds and guarded-response gates. |
| `+0x20C` | `s32` | Current count in the fighter-update pause block at `+0x200`; positive values stop normal action-timeline and per-action updates. |
| `+0x230` | `s32` | Current count in a secondary countdown block at `+0x224`. While positive, accepted-hit router modes `0`, `2`, and `3` discard new hits; attack record `+0x32`, ordinary-response row `+0x16`, guarded-response row `+0x16`, and several fixed values initialize it. See [Accepted-hit rejection countdown](#accepted-hit-rejection-countdown). |
| `+0x538`, `+0x53A` | `s16`, `s16` | Receiver's accepted ordinary-hit count (saturating at `9999`) and its running maximum; see [Hit count](#hit-count). |
| `+0x7C8`, `+0x7CC` | pointer, pointer | Retained recovery source and record, separate from `+0xE58/+0xE54`; see [Retained recovery-source lifetime](#retained-recovery-source-lifetime). |
| `+0x830` | `u8` | Receiver grounding saved when the recovery source/record is written; the inspected `0x61` motion branch clears it. |
| `+0xB00` | flags | Extra Hit exchange roles; see [Extra Hit](extra_hit.md#exchange-state-at-fighter-0xb00). |
| `+0x254` | `s32` | Current count in the action-lock block at `+0x248`; native action selection refuses actions until it reaches zero. |
| `+0x338` | `u32` | Current logical input bits; guard is `0x10000000`, while downed choices test newly pressed binding 2 (`0x00010000`, default Cross) and binding 1 (`0x00001000`, default Circle). |
| `+0x994` | `f32` | Oriented planar response speed written by the reaction table. |
| `+0x998` | `f32` | Vertical response speed written by the reaction table. |
| `+0x9B4` | `f32` | Gravity argument for the next movement pass, copied from response-table field `+0x10` when that field differs from `1.0` and reset to `1.0` after each pass; see [Gravity and airtime](#gravity-and-airtime). |
| `+0x9B8` | flags | Low two bits participate in choosing the grounded-family reaction variant. |
| `+0xA30` | pointer | Current action-descriptor row; for native substates below `0x66`, the state setter indexes the overlay descriptor table directly. |
| `+0xB88` | `u32` | Latest animation-advance completion result. Animation selection clears it; the animation driver rewrites it with the nonzero end result consumed by phase records. |
| `+0xB84` | pointer | Animation-object table indexed by phase-record animation slot. |
| `+0xB90` | `u16` | Current secondary-timeline and animation rate loaded from the phase record's fourth halfword and interpreted as a `/256` fixed-point factor. |
| `+0xB94` | `s16` | Animation start frame loaded from the phase record's third halfword. |
| `+0xB9A` | `s16` | Consecutive grounded-update count, saturating at `0x7FFF`; reset to zero while airborne. |
| `+0xB9C` | flags | Ground/air history for the current action: low nibble `1` means entered grounded and `2` means entered airborne; `0x20` latches a later airborne update for the former, while `0x10` latches a later grounded update for the latter. |
| `+0x95A` | `s16` | Guard temporal state/counter; `< 1` selects ordinary response and `>= 1` selects guarded response. |
| `+0x95C` | `s16` | Guard-input timing state. |
| `+0x95E` | `s16` | Direction/facing-adjusted guarded-response index. |
| `+0x960`, `+0x962` | `s16`, `s16` | Private stage and per-stage invocation counter used by ordinary response `0x4F`. |
| `+0xB66` | `s16` | Automatic downed-recovery threshold. |
| `+0xB68` | `s16` | Earliest input-driven downed-recovery threshold. |
| `+0xB6E` | `s16` | Raw repeat/response count used by the rehit exception and by the scaled `0x3A/0x3B` downed handoff. No player-facing name is assigned. |
| `+0xB60`, `+0xB64` | pointer, `s16` | Retained attack record and consecutive ordinary-response streak count used by two final selector overrides; both are reset on leaving major state `5`. |
| `+0xE54` | pointer | Attack-record pointer retained for the active response. |
| `+0xE58` | pointer | Source object retained for the active response. |
| `+0xE5C` | `s16` | Attack-record repeat/sample countdown copied from attack record `+0x2E`. |

The high bit of fighter byte `+0x63` is used consistently as the grounded
branch in the traced paths: guard stance is entered only when it is set, and
guard release goes to neutral only when it is set. References below therefore
say *grounded* for that tested condition.

## Resident routine map

| Preserved symbol | EE runtime | ELF file | Demonstrated role |
| --- | ---: | ---: | --- |
| `FUN_00217e40` | `0x00217E40` | `0x00117F40` | Central action-state setter; stores major/substate, resets action cursors, and selects the state descriptor. |
| `FUN_00218190` | `0x00218190` | `0x00118290` | Selects a descriptor-specified animation slot and clears `+0xB88` when that selection changes. |
| `FUN_00211d80` | `0x00211D80` | `0x00111E80` | Advances a generic integer/fractional timeline block by a floating-point rate. |
| `FUN_00211e70` | `0x00211E70` | `0x00111F70` | Decrements a generic integer/fractional countdown block and clamps its current count at zero. |
| `FUN_0021acb0` | `0x0021ACB0` | `0x0011ADB0` | Shared response-table motion/event-gate engine. |
| `FUN_002209a0` | `0x002209A0` | `0x00120AA0` | Accepted-hit router that selects ordinary or guarded response from `+0x95A`. |
| `FUN_00224510` | `0x00224510` | `0x00124610` | Initializes the fighter-update pause channel from attack record `+0x30`. |
| `FUN_00228320` | `0x00228320` | `0x00128420` | Updates guard-input age/temporal state and enters guard stance when eligible. |
| `FUN_00228760` | `0x00228760` | `0x00128860` | Guarded-hit state selection and guarded-response initialization. |
| `FUN_00228e90` | `0x00228E90` | `0x00128F90` | Guard stance/reaction continuation and exit selection. |
| `FUN_00231a40` | `0x00231A40` | `0x00131B40` | Runs the paired update-rate sequence required by the normal `0x4F` exit. |
| `FUN_00231c60` | `0x00231C60` | `0x00131D60` | Converts attack record `+0x2C` plus fighter context into an ordinary response substate. |
| `FUN_00232b80` | `0x00232B80` | `0x00132C80` | Enters ordinary major state `5`, retains hit provenance, and initializes response side effects. |
| `FUN_00233870` | `0x00233870` | `0x00133970` | Ordinary-response transition dispatcher, including completion, contact, and downed handoffs. |
| `FUN_002346b0` | `0x002346B0` | `0x001347B0` | Applies response-table timing/lock values and related per-response side effects. |
| `FUN_00234da0` | `0x00234DA0` | `0x00134EA0` | Per-update ordinary-response driver; advances table motion and event impulses. |
| `FUN_00235510` | `0x00235510` | `0x00135610` | Initializes timed downed recovery and enters `(6,0x5D)`. |
| `FUN_00235690` | `0x00235690` | `0x00135790` | Updates downed/recovery substates `0x5D..0x62`. |
| `FUN_00239e50` | `0x00239E50` | `0x00139F50` | Action-entry eligibility predicate; returns false while `+0x254` is nonzero. |
| `FUN_002406b0` | `0x002406B0` | `0x001407B0` | Classifies current response windows for conditional rehit suppression. |
| `FUN_002409e0` | `0x002409E0` | `0x00140AE0` | Combines incoming-attack, current-response, and repeat-record conditions into the router's response-gate bits. |
| `FUN_00249640` | `0x00249640` | `0x00149740` | Per-action update dispatcher; sends major `5` to `FUN_00234da0` and major `6` to the recovery updater. |
| `FUN_0024c440` | `0x0024C440` | `0x0014C540` | Main fighter countdown maintenance, including the ordered `+0x20C` then `+0x254` updates. |
| `FUN_0024d1c0` | `0x0024D1C0` | `0x0014D2C0` | Advances the current animation and stores its end result at `+0xB88`. |
| `FUN_0024d5e0` | `0x0024D5E0` | `0x0014D6E0` | Advances the primary and secondary action timelines while fighter-update pause is inactive. |
| `FUN_0024fd80` | `0x0024FD80` | `0x0014FE80` | Active-fighter loop that suppresses normal action updates while `+0x20C` is positive. |
| `FUN_00248ec0` | `0x00248EC0` | `0x00148FC0` | Normal battle-input update that passes logical input `+0x338` to `FUN_00228320`. |
| `FUN_001f03e0` | `0x001F03E0` | `0x000F04E0` | Battle update that calls the registry slots `+0x0C`, `+0x10`, and `+0x14` in that order. |
| `FUN_0024de40` | `0x0024DE40` | `0x0014DF40` | Fighter virtual slot `+0x18`; advances action timelines through `FUN_0024D5E0`. |
| `FUN_0021ed70` | `0x0021ED70` | `0x0011EE70` | Pair hit resolver; edits both fighters' `+0xE3C` hit bits and calls `FUN_002426C0`. |
| `FUN_00224870` | `0x00224870` | `0x00124970` | Initializes countdown `+0x230` from attack record `+0x32`. |
| `FUN_00220690` | `0x00220690` | `0x00120790` | Attacker-side handling of a landed hit, including the attacker pause. |
| `FUN_00232a50` | `0x00232A50` | `0x00132B50` | Retains a new attack record, repeat count, and knockback scale, then re-enters the router. |
| `FUN_00248580` | `0x00248580` | `0x00148680` | Runs the phase updater and the per-major exit dispatchers. |
| `FUN_0024da50` | `0x0024DA50` | `0x0014DB50` | Fighter virtual slot `+0x10`; movement and animation pass, or input selection during a pause. |
| `FUN_0024a660` | `0x0024A660` | `0x0014A760` | Movement, ground contact, and gravity application. |
| `FUN_002183d0` | `0x002183D0` | `0x001184D0` | Applies gravity to a vertical speed. |

## Accepted-hit routing

`FUN_002209a0` is downstream of collision acceptance. Its representative
native branch is exact:

```text
fighter[+0x95A] < 1   -> FUN_00232b80(...)  ordinary response
fighter[+0x95A] >= 1  -> FUN_00228760(...)  guarded response
```

Before that selection, attack-record `+0x14` flag `0x00800000` can change a
nonzero `+0x95A` to sentinel `-1` under the shown facing condition, and flag
`0x00400000` clears it to zero. Both values route the accepted hit through the
ordinary branch. Static code proves guard invalidation/bypass, but not the
authoring names of those two flags.

The ordinary initializer consumes exactly the sentinel `-1` at resident
`0x00232CCC..0x00232CE0`: it clears `+0x95A` and passes fifth argument `1`
to `FUN_00231C60` at `0x00232CFC` (ELF file `0x00132DFC`). The selector's
early branch returns `0x4F`, before authored mapping or character callbacks,
so this becomes `(5,0x4F)`. Clearing the guard field to zero instead reaches
normal response selection. The two invalidation flags therefore have distinct
ordinary-response outcomes. Guard-field ownership and the differently shaped
overlay nonzero/positive checks are documented in
[Chakra and guard](chakra_and_guard.md#guarded-hit-selection-and-break-like-flags).

The complete resident router occupies `0x002209A0..0x0022111F`. Its
decompilation and instructions establish four source-object modes (`0`, `1`,
`2`, and `3`). Their normal paths converge on the
same ordinary-versus-guarded decision, but their admission gates and side
effects are not interchangeable:

| Mode | Exact additional behavior before the response branch |
| ---: | --- |
| `0` | May replace the record returned by `FUN_00222B20` with `FUN_00222A40(fighter[+0x20])` when retained source `+0xE58` is non-null, source `+0x0C` is nonzero, original attack `+0x50` is zero, and the replacement is non-null. It rejects the hit when `FUN_002247A0(fighter)` is nonzero or `FUN_00222BD0(fighter)` is zero. |
| `1` | Requires retained source `+0xE58`, source halfword `+0x02 == 0x474F`, source word `+0x0C == 1`, and a nonzero result from live overlay target `0x0072EDE0(source,fighter)`. It runs the interception predicate described below before invoking a source virtual callback at vtable `+0x58` and live overlay target `0x0072E5D0(1.0,source,fighter,attack)`. |
| `2` | Requires retained source `+0xE58` and `FUN_002247A0(fighter) == 0`, then runs the same interception predicate. On its normal route it writes paired fighter `fighter[+0x20] + 0xB58` to `1` for ordinary response or `-1` for guarded response; its intercepted route writes `-2`. |
| `3` | Requires retained source `+0xE58` and `FUN_002247A0(fighter) == 0`, then performs the common guard invalidation and ordinary/guarded branch without mode `0`'s replacement-record and positive-repeat gates. |

`FUN_002247A0` is exactly the predicate `fighter[+0x230] > 0`.
`FUN_00222BD0` returns positive retained repeat value `+0xE5C` while
`+0xB00 == 0`, otherwise zero, and returns `1` while `+0xB00 != 0`; thus the
mode-`0` admission test is specifically a nonzero expected-repeat requirement,
not a generic validity check. The record lookup order of `FUN_00222B20` is
owned by [Target selection](target_selection.md#retained-source-writers-and-record-lookup).

Modes `1` and `2` call
`FUN_00229130(fighter,attack,5,selected_response,1)`. A zero result continues
to ordinary or guarded response. A nonzero result diverts into
`FUN_002297D0`: mode `1` supplies code `0x21`, while mode `2` supplies `0x41`.
That diversion stores the code at fighter `+0x964`, clears the complete
action-lock block and conditionally primes the secondary countdown to `-20`,
brings planar and vertical response speeds toward zero, and force-enters
`(major,substate) = (0,8)`. Subject to its internal gates, it also subtracts
`1.0` from fighter float `+0x70`, clamps the result at zero, and writes `15.0`
to `+0x1A0`. These are observed state mutations; the player-facing meaning of
the interception, codes, and two float fields remains unresolved.

The intercepted paths return `0` from `FUN_002209A0` without entering the
ordinary/guarded response. A normally routed accepted hit returns `1` after
the branch. On mode `2`, `FUN_00233540(fighter,1)` consumes the paired
`+0xB58` marker after routing: among the three values written here, only
ordinary marker `1` passes its notification condition; guarded `-1` and
intercepted `-2` do not. This proves a mode-specific paired-fighter side effect
without establishing names for the four source modes.

The separate source-retaining wrapper `FUN_002333A0` can also populate
recovery provenance `+0x7C8/+0x7CC` under its source gates. Its two BTL
callers at preserved `0x0079FEE8/0x007D4598` then add a pending combo count
through `FUN_00239230`
([Combo accounting](combo_accounting.md#explicit-and-pending-updates)); they
create no `+0xE3C` response request and do not run `FUN_002209A0`. A
retained recovery-source pointer or a new pending combo count therefore does
not establish a new ordinary response initialization. The retained record's
setup and the wrapper's independent damage amount belong to
[Damage](damage.md#all-fifteen-btl-source-retaining-calls).

When the struck fighter's byte `+0x61` bit `3` is clear, that wrapper's tail
calls `FUN_00216A60` on both paired fighters. For each fighter whose byte
`+0x62` bit `0` is clear, this helper tears down the Extra Hit exchange
through [`FUN_00243EF0`](extra_hit.md#initialization-and-teardown), releases held `(5,0x50)` to neutral when present,
and sets byte `+0x62` bits `0/1`. This is a distinct cleanup path affecting
response lifetime and the hit-statistic/pending-count gates.

## Ordinary response selection

`FUN_00232b80` calls `FUN_00231c60`, then forcibly enters
`(major,substate) = (5, selected_response)` through `FUN_00217e40(...,1)`.
The selected response is not simply an animation number. It indexes a resident
state slot whose descriptor table is in the battle overlay at live
`0x0089AEB0`, preserved Ghidra/export `0x0089AE70`, and `BTL.BIN` file offset
`0x001E6FB0`, plus the separate resident motion table described below.

The primary authored selector is attack-record byte `+0x2C`. The following is
the direct mapping before later callback and repeat-hit remaps. A
*grounded-family* choice additionally requires fighter `(+0x9B8 & 3) < 2` and
the grounded bit at `+0x63`.

| Attack `+0x2C` | Grounded-family result | Other result |
| ---: | --- | --- |
| `0x00`, `0x01` | `0x27`, `0x28` | `0x2F` |
| `0x02`, `0x03` | `0x29`, `0x2A` | `0x30` |
| `0x04..0x07` | `0x2B..0x2E`, one-for-one | `0x31` |
| `0x08`, `0x09`, `0x0A` | `0x2F`, `0x30`, `0x31` | same |
| `0x0B..0x0E` | `0x32..0x35`, one-for-one | same |
| `0x0F` | `0x36` | `0x37` |
| `0x10`, `0x11` | `0x38`, `0x39` | same |
| `0x12` | `0x3C` or `0x3D` from orientation | same |
| `0x13..0x16` | `0x3E..0x41`, one-for-one | same |
| `0x17..0x1B` | `0x4A..0x4E`, one-for-one | same |
| `0x1C` | `0x50` | same |
| `0x1D..0x20` | odd `0x51/53/55/57` | paired even `0x52/54/56/58` |
| `0x21` | `0x59` | same |
| `0x22..0x24` | random member of `0x27/28`, `0x29/2A`, or `0x2B/2C` | `0x2F`, `0x30`, or `0x31` |
| `0x25` | random `0x27..0x2A` | random `0x2F..0x30` |
| `0x26` | random `0x29..0x2C` | random `0x30..0x31` |
| `0x27` | random `0x27..0x2C` | random `0x2F..0x31` |
| any other byte | `0x27` | `0x2F` |

A read-only scan of all 74 primary action tables (3,428 `0x54`-byte records)
gives the authored use of this selector. Among the 2,484 records with nonzero
damage `+0x24`:

| `+0x2C` | Direct result | Records |
| --- | --- | ---: |
| `0x00..0x07` | light family `0x27..0x2E` / `0x2F..0x31` | 645 |
| `0x08..0x0A` | `0x2F..0x31` | 61 |
| `0x0B..0x0E` | `0x32..0x35` | 131 |
| `0x0F` | `0x36` / `0x37` | 95 |
| `0x10`, `0x11` | `0x38`, `0x39` | 135 |
| `0x12` | `0x3C` / `0x3D` | 490 |
| `0x13` | `0x3E` | 24 |
| `0x14` | `0x3F` | 390 |
| `0x15` | `0x40` | 433 |
| `0x16` | `0x41` | 22 |
| `0x17..0x19` | held `0x4A..0x4C` | 10 |
| `0x1C` | `0x50` | 2 |
| `0x1D`, `0x1E` | `0x51/0x52`, `0x53/0x54` | 46 |

No damaging record uses `0x1A`, `0x1B`, `0x1F..0x27`, or any other byte, so
the random selectors `0x22..0x27` are unused by stock damaging attacks. The
300 records with `+0x2C == 0xFF` are all non-damaging. The guarded-response
byte `+0x2D` on damaging records is `0..4` on 2,311 and `6..9` on 173; no
record uses `5` or a negative value.

Additional proven selection behavior prevents treating this as a final
one-to-one enum:

- a guard-invalidated call requests response `0x4F` directly;
- a missing attack record starts from `0x27`;
- a failed contextual query selects `0x3A` or `0x3B` according to source
  object presence;
- before the byte mapping, an attack with nonzero `+0x50` returns `0x37` when
  the receiver is in `(5,0x3F)` with `+0x230 < 1` and negative vertical speed,
  a standard source is present, and receiver `+0xBA4` is neither the sentinel
  `-17320.508` nor at least `2 * source[+0xE4] * source[+0x2F0]`;
- a standard source object (raw field `+0x0C == 0`) can dispatch a response
  callback whose result overrides the authored mapping when it returns anything
  other than `-1`; and
- the active-effect path can force response `0x37` for response classes it
  does not accept.

When that source callback is absent or returns `-1`, a repeat-collapse pass is
possible. It requires the standard source object, attack record
`(+0x10 & 0x00F00000) == 0`, and an expected repeat count greater than `1`.
Authored results `0x52/0x54/0x56/0x58` are explicitly exempt. The remaining
exact remaps are:

| Authored result | Repeat-collapse result |
| --- | --- |
| `0x37` | `0x30` |
| `0x3F` | `0x32` |
| `0x40/0x41` | `0x2C` for the grounded-family condition, otherwise `0x35` |
| `0x3C..0x3E` | `0x2B` when grounded-family and the source is grounded; `0x35` when grounded-family and the source is airborne; otherwise `0x30` |
| `0x32` | `0x30` |
| `0x36`, `0x38`, `0x39`, `0x4A..0x50` | random `0x29/0x2A` when the fighter's grounded bit is set, otherwise `0x30` |

All other results survive this pass unchanged. The *expected repeat count* is
the same raw value used later by the rehit exception: positive `+0xE5C`
(otherwise zero) while `+0xB00 == 0`, or `1` while `+0xB00 != 0`.

Two subsequent streak checks can still force `0x37`. The count at `+0xB64`
increments only when the accepted attack satisfies raw gates at `+0x10` and
`+0x50`, its signed `+0x2E` equals the expected repeat count, and retained
record `+0xB60` is null or the same record. A provisional `0x2F` becomes
`0x37` when the expected repeat count is below `2`, `+0xB64 > 2`, and the
standard source is grounded. Independently, any provisional result becomes
`0x37` when the receiver is grounded, `+0xB64 > 3`, and attack byte `+0x19`
is zero. The raw attack gates are intentionally not given speculative content
names.

`FUN_00230A70` clears both retained record `+0xB60` and count `+0xB64`
when the destination major state is not `5`; transitions within major `5`
preserve them. This counter is distinct from cumulative ordinary-hit statistics
at `+0x538`. Character timing writers can inspect either fighter's response
counter and change live attack fields before later predicates; their timing
field and callback-order evidence belongs to
[Substitution](../characters/substitution.md#callback-ordering-and-counter-ownership).

Two final substates are initializer overrides rather than direct `+0x2C`
selector results. `FUN_002346b0` zeros both response-speed fields and enters
`0x5B` if grounded or `0x5C` if airborne when all three raw prerequisites hold:
fighter byte `+0x62` bit `0` is clear, `FUN_00244f80(fighter[+0x20])` returns
zero, and attack record `+0x10 & 0x00F00000` is nonzero. The first two
prerequisites and the attack mask are left unnamed because their player-facing
meanings are not established.

These are confirmed mechanics, but the static evidence does not justify names
such as “light stagger,” “crumple,” “wall splat,” or “guard crush” for any raw
substate.

When the selected result is `0x3A` or `0x3B`, ordinary-response initialization
increments fighter `+0xB6E` up to `3`. If it is already `3` and secondary block
`+0x224` has no pending activation (`flag 0x0004` clear), initialization instead
primes `+0x230` with `60`. The
later downed handoff reads the updated `+0xB6E`, so its
`1.0 - 0.25 * +0xB6E` scale progresses through `0.75`, `0.50`, and `0.25`.
This is also why the `0x3A/0x3B` rehit predicate's `+0x230 <= 0` condition is
material on a capped repeat.

There is a second ordinary-response source for that countdown. When the
primary timeline crosses event `0`, `FUN_002346B0` tests raw attack halfword
`+0x32`. If it equals `0x7FFF` and secondary block pending flag `0x0004` is
clear, the routine stages `+0x230` from the response row's `+0x16` value after
an update-rate adjustment. Let receiver rate `r` and paired-fighter rate `p` be
their respective `+0x1AC` values. Starting from the row base, the exact
instruction sequence multiplies by `2-r` when `r != 1`, multiplies by `2-r`
again when `p > 1`, and multiplies by `2-p` when `p < 1`. The repeated `r` in
the `p > 1` branch is present in the clean instructions and is not normalized
to a symmetric formula. The result is converted by EE `cvt.w.s` under the
active FPU rounding mode and stored through a signed halfword; this local path
does not set that rounding mode. The unadjusted bases are `6` for `0x3A` and
`8` for `0x3B`.

The capped-repeat `60` competes with the attack's own `+0x32` value, which
`FUN_00224870` applies earlier in the same initializer. That call leaves the
pending flag set for a positive or zero `+0x32`, so the `60` is written only
when `+0x32` is sentinel `0x7FFF` (with no earlier pending value) or negative.
The `60` is written positive with the pending flag clear. With the sentinel,
the event-`0` path then replaces it with the adjusted `6`/`8` base; per
[Hit update order](#hit-update-order-and-elapsed-updates), that replacement
happens in the hit update itself unless a pause is already active. With a
negative `+0x32`, the `60` remains.

### Character response callbacks

The callback is selected from the standard source fighter's vector
`source[+0xA8]+0x0C`. Although `FUN_00231C60` has a branch that could use
the receiver's vector, its predicate `FUN_00307A50` is a literal zero-return
stub in the clean resident ELF. The source vector is therefore the one used
on this path. The initializer calls the callback with
`(source,receiver,2)`; the earlier paired-hit classifier
`FUN_0021F610` calls the same selector with mode `0`.

A return other than `-1` replaces the byte-mapped response and skips the
generic repeat-collapse pass. The two streak checks and active-effect remap
still follow it. A return of `-1` preserves those generic selection steps,
but does not mean the callback has no side effects. Most callbacks gate
receiver motion writes on mode `2`; live attack-record changes can precede
that gate. Hanabi's callback also writes receiver `+0x9A0` without a mode
gate. Thus the earlier mode-`0` call is not uniformly a read-only query.

The repeat helper `FUN_00231BF0` uses the source's current attack at
`+0xA4C` only while the source is in major `8`. If it is the receiver's
retained record `+0xE54`, it returns the positive receiver `+0xE5C`
(otherwise zero), or `1` when receiver `+0xB00` is nonzero. For a different
record it returns that record's signed `+0x2E`; without a current attack it
returns zero. Callback comparisons such as `<2` therefore use this
record-sensitive value, not the cumulative hit count `+0x538`.

All 74 primary metadata records have a
nonzero vector at metadata `+0x1C` and a nonzero response callback at vector
`+0x0C`. The exact clean callback entries are below. These are resident EE
addresses; their ELF offsets use the conversion in
[Evidence identity](#evidence-identity-and-address-conventions).

| Character ID | Metadata owner | Resident callback |
| ---: | --- | --- |
| 57 | Naruto Uzumaki | `0x0029AC50` |
| 73 | Nine-Tailed Fourth Awakened State | `0x002D2560` |
| 58 | Sakura Haruno | `0x0029B8A0` |
| 70 | Kakashi Hatake | `0x002C7E90` |
| 92 | Sai | `0x002FEF00` |
| 65 | Neji Hyuga | `0x002B84F0` |
| 67 | Rock Lee | `0x002BF9A0` |
| 69 | Might Guy | `0x002C55B0` |
| 66 | Tenten | `0x002BB960` |
| 81 | Choji Akimichi | `0x002EAD30` |
| 68 | Shikamaru Nara | `0x002C1380` |
| 82 | Ino Yamanaka | `0x002EBB50` |
| 86 | Asuma Sarutobi | `0x002F1760` |
| 79 | Shino Aburame | `0x002E5340` |
| 78 | Kiba Inuzuka | `0x002E2360` |
| 80 | Hinata Hyuga | `0x002E7FC0` |
| 59 | Kazekage Gaara | `0x0029E6E0` |
| 87 | Kurenai Yuhi | `0x002F37A0` |
| 60 | Kankuro | `0x002A47B0` |
| 61 | Temari | `0x002A7A90` |
| 77 | Granny Chiyo (Taijutsu) | `0x002DA970` |
| 72 | Kisame Hoshigaki | `0x002CDA90` |
| 71 | Itachi Uchiha | `0x002CB950` |
| 64 | Deidara | `0x002B68F0` |
| 62 | Granny Chiyo | `0x002AE680` |
| 63 | Sasori | `0x002B34D0` |
| 75 | Sasori (Puppet) | `0x002D3F70` |
| 76 | Sasori (Hiruko) | `0x002D5320` |
| 84 | Tsunade | `0x002EF7E0` |
| 83 | Jiraiya | `0x002ED720` |
| 85 | Shizune | `0x002F0B10` |
| 89 | Orochimaru | `0x002F7890` |
| 91 | Yamato | `0x002FCA90` |
| 90 | Kabuto Yakushi | `0x002F8DC0` |
| 93 | Sasuke Uchiha | `0x00303010` |
| 1 | Naruto Uzumaki (Classic) | `0x002536C0` |
| 47 | Naruto Uzumaki (Nine-Tailed) | `0x002806A0` |
| 2 | Sasuke Uchiha (Classic) | `0x002541D0` |
| 48 | Second Stage Sasuke Uchiha | `0x002821D0` |
| 7 | Sakura Haruno (Classic) | `0x0025A8B0` |
| 6 | Neji Hyuga (Classic) | `0x00259C90` |
| 3 | Rock Lee (Classic) | `0x002554D0` |
| 49 | Loopy Fist Lee | `0x00284FE0` |
| 13 | Tenten (Classic) | `0x0025E510` |
| 5 | Shikamaru Nara (Classic) | `0x00258950` |
| 14 | Choji Akimichi (Classic) | `0x0025FDA0` |
| 51 | Super Choji | `0x00287770` |
| 16 | Kiba Inuzuka (Classic) | `0x00262F60` |
| 15 | Ino Yamanaka (Classic) | `0x00260C90` |
| 17 | Shino Aburame (Classic) | `0x00264A90` |
| 12 | Hinata Hyuga (Classic) | `0x0025D5C0` |
| 41 | Hanabi Hyuga | `0x0027B330` |
| 40 | Konohamaru Ninja Squad | `0x0027AA80` |
| 46 | Anko Mitarashi | `0x0027E4F0` |
| 42 | The First Hokage | `0x0027CEC0` |
| 43 | The Second Hokage | `0x0027D9C0` |
| 39 | The Yellow Flash | `0x00278310` |
| 22 | The Third Hokage | `0x0026F000` |
| 4 | Gaara (Classic) | `0x00257BD0` |
| 50 | Possessed Gaara | `0x002860D0` |
| 19 | Temari (Classic) | `0x0026D760` |
| 18 | Kankuro (Classic) | `0x0026B5D0` |
| 38 | Kimimaro | `0x00276370` |
| 56 | Second Stage Kimimaro | `0x00295410` |
| 37 | Sakon | `0x002746A0` |
| 55 | Second Stage Sakon | `0x00293C50` |
| 36 | Tayuya | `0x002730C0` |
| 54 | Second Stage Tayuya | `0x002911C0` |
| 35 | Kidomaru | `0x00271920` |
| 53 | Second Stage Kidomaru | `0x00289A90` |
| 34 | Jirobo | `0x00270270` |
| 52 | Second Stage Jirobo | `0x00288870` |
| 11 | Zabuza Momochi | `0x0025C070` |
| 10 | Haku | `0x0025B5D0` |

The bounded body audit covered all 74 entries and Guy's delegated
`FUN_002C6380`. First Hokage's entry is an undefined analysis span, but its
clean bytes at resident/file `0x0027CEC0 / 0x0017CFC0` are simply
`li v0,-1; jr ra; nop`. Second Stage Kidomaru's callback calls the repeat
helper and returns `-1`. Sakura and Ino's callbacks also always return
`-1`, while changing response motion or live attack fields. The other
70 entries contain direct or delegated non-default response branches.
This bounds the callback inventory and demonstrates why the authored-byte
counts above are not a complete inventory of final reactions; it does not
assign player-facing move names or prove every branch reachable in a match.

Representative exceptions preserve the specific evidence needed to interpret
the shared response machine:

- Fourth Awakened Naruto, `FUN_002D2560`, action index `0x28`: a
  grounded receiver gets `0x40` while the repeat value is below `2`, then
  random `0x27/0x29/0x2A`; an airborne receiver gets `0x40`. The callback
  writes the live record's `+0x2E/+0x30/+0x32` to `10/-1/1` when grounded
  and `2/2/1` when airborne, independently of the mode-`2` motion gate.
- Rock Lee, `FUN_002BF9A0`, action index `0x18`, phase `3`: returns
  `0x3D` and writes live attack `+0x32 = 0x7FFF`; other phases restore
  that field to `1`. Guy's delegated handler does the corresponding
  phase-`3` override for action `0x1C`, returning `0x39` and writing
  `0x7FFF`, while other phases write `2`. These are concrete writers of
  the rejection-countdown sentinel described above.
- Loopy Fist Lee, `FUN_00284FE0`, action `0x1B`: phases `0/1/2`
  select `0x4A/0x2B/0x39`. A callback can therefore enter the held-response
  group even when a clean damaging record's authored byte does not name it.
- The Yellow Flash, `FUN_00278310`, action `0x1B`, phase `2`:
  repeat value below `2` selects `0x51` for a grounded receiver or
  `0x52` otherwise; a repeat value of `2` or more selects
  `0x35`. Action `0x28` selects held response `0x4C` below `2`
  and `0x33` afterward.
- Hanabi, `FUN_0027B330`, action `0x18`: receiver helper
  `FUN_00222BD0` below `2` selects `0x3F` and writes
  `+0x9A0 = 1.0`; otherwise it selects `0x32` and writes `0.5`.
  These writes apply in both selector modes.

Action indices in these examples come from `FUN_00217860(source)`; they
are character-local attack indices, distinct from the receiver's response
substate. Callback receiver fields `+0x9A0/+0x9A8/+0x9AC` are the
transient motion modifiers consumed by the response initialization described
in [Velocity modifier order](#velocity-modifier-order). Phase, repeat,
grounded-state, private character fields, and random branches can therefore
change response choice or motion without changing the original clean table.

#### Representative Lee variants and shared recovery eligibility

The complete response bodies for Classic Lee `FUN_002554D0` and Loopy Fist
Lee `FUN_00284FE0` were compared with Lee `FUN_002BF9A0` and Guy's
two-body response family. Classic Lee's body writes only mode-`2` receiver
motion modifiers; Loopy Fist Lee additionally changes live attack `+0x48`
for action `0x1B`, but neither body writes contact bits
`0x00080000/0x00100000`. Their response choices can nevertheless change
which shared recovery or automatic-contact predicates apply:

| Callback branch | Provisional response and motion | Shared eligibility consequences if that response survives final remaps |
| --- | --- | --- |
| Classic Lee action `0x1A`, phase `2/3` | `0x3D` when receiver facing `+0x990 == +0x326`, otherwise `0x3C`; mode `2` sets attack scale `+0x9A0 = 1.35` | Both ordinary input-recovery state lists include these responses; contact bit `6` can propose `0x48`, subject to the shared scale/record/cursor gates. |
| Loopy Fist Lee action `0x18`, repeat value `<2` | `0x3E`; no explicit transient attack-scale write in that branch | Neither ordinary input-recovery state list includes `0x3E`; its automatic contact proposal `3` remains a separate path. |
| Same action, repeat value `>=2` | grounded random `0x29/0x2A`, otherwise `0x30`; mode `2` sets scale `0.5` | Those states match neither ordinary recovery state list nor an automatic contact proposal. |
| Loopy Fist Lee action `0x20`, odd repeat value `>=3` | `0x40`; mode `2` sets attack/planar/vertical transient scales `0.75/5.0/1.0` | The first-grounded input state list includes `0x40`; the later history-gated list excludes it. Ground contact can propose `0x49`. |
| Loopy Fist Lee action `0x20`, even repeat value `>=2` | `0x30`; mode `2` sets scales `1.0/1.5/-0.5` | Neither of those recovery state lists nor the contact proposal includes `0x30`. |
| Loopy Fist Lee action `0x2B`, repeat value `<2` | `0x40`; mode `2` sets attack scale `1.25` | The same first-grounded-versus-later distinction as the `0x40` branch above. |
| Same action, repeat value `>=2` | grounded `0x29`, otherwise `0x30`; mode `2` sets attack scale `0.0` | The callback exits the contact-proposal response family rather than setting a suppression bit. |

These are response/state membership consequences, not visible move names or
successful recovery claims. Repeat values come from the record-sensitive
helper described above. The final streak/effect remaps still run after the
callback; contact and input gates must still pass. The selected clean
records carry no contact bits on Classic Lee action `0x1A` and Loopy Fist
Lee actions `0x18/0x20/0x2B`, at resident record bases `0x00418298`,
`0x004B18B0`, `0x004B1B50`, and `0x004B1EEC`. The clean tables are not
another live-writer census.

### Native action identifiers

The overlay descriptor table is indexed directly by substate and has an
`0x08`-byte row containing two encoded live pointers: a NUL-terminated action
identifier and descriptor data. Because those pointers are already live
values, each target's file offset was decoded as `pointer - 0x006B3F00`; the
preserved export's target labels are `0x40` too high under the header-omission
convention. The exact relevant identifiers are:

| State | Native identifier | State | Native identifier | State | Native identifier |
| ---: | --- | ---: | --- | ---: | --- |
| `0x27` | `ACT_DMG_NSH` | `0x3B` | `ACT_DMG_DDL` | `0x4F` | `ACT_DMG_GBR` |
| `0x28` | `ACT_DMG_NSL` | `0x3C` | `ACT_DMG_BSF` | `0x50` | `ACT_DMG_CNT` |
| `0x29` | `ACT_DMG_NMH` | `0x3D` | `ACT_DMG_BSB` | `0x51` | `ACT_DMG_AND` |
| `0x2A` | `ACT_DMG_NML` | `0x3E` | `ACT_DMG_BSG` | `0x52` | `ACT_DMG_ANDA` |
| `0x2B` | `ACT_DMG_NLH` | `0x3F` | `ACT_DMG_BR` | `0x53` | `ACT_DMG_AFD` |
| `0x2C` | `ACT_DMG_NLL` | `0x40` | `ACT_DMG_BD` | `0x54` | `ACT_DMG_AFDA` |
| `0x2D` | `ACT_DMG_NHH` | `0x41` | `ACT_DMG_BS` | `0x55` | `ACT_DMG_ATD` |
| `0x2E` | `ACT_DMG_NHL` | `0x42` | `ACT_DMG_SSF` | `0x56` | `ACT_DMG_ATDA` |
| `0x2F` | `ACT_DMG_NAS` | `0x43` | `ACT_DMG_SSB` | `0x57` | `ACT_DMG_AWD` |
| `0x30` | `ACT_DMG_NAM` | `0x44` | `ACT_DMG_SR` | `0x58` | `ACT_DMG_AWDA` |
| `0x31` | `ACT_DMG_NAL` | `0x45` | `ACT_DMG_SD` | `0x59` | `ACT_DMG_XF` |
| `0x32` | `ACT_DMG_NB12` | `0x46` | `ACT_DMG_SD2` | `0x5A` | `ACT_DMG_XD` |
| `0x33` | `ACT_DMG_NB13` | `0x47` | `ACT_DMG_SD3` | `0x5B` | `ACT_DMG_XB` |
| `0x34` | `ACT_DMG_NB14` | `0x48` | `ACT_DMG_SBS` | `0x5C` | `ACT_DMG_XB` |
| `0x35` | `ACT_DMG_NB15` | `0x49` | `ACT_DMG_SBD` | `0x5D` | `ACT_DWN_0` |
| `0x36` | `ACT_DMG_ND` | `0x4A` | `ACT_DMG_HOLD` | `0x5E` | `ACT_DWN_1` |
| `0x37` | `ACT_DMG_NDA` | `0x4B` | `ACT_DMG_HOLD_A` | `0x5F` | `ACT_DWN_2` |
| `0x38` | `ACT_DMG_NDH` | `0x4C` | `ACT_DMG_HOLD_L` | `0x60` | `ACT_DWN_3` |
| `0x39` | `ACT_DMG_NDL` | `0x4D` | `ACT_DMG_HOLD_D` | `0x61` | `ACT_DDM_0` |
| `0x3A` | `ACT_DMG_DDS` | `0x4E` | `ACT_DMG_HOLD_F` | `0x62` | `ACT_DDM_1` |

These strings are canonical authored identifiers, not licenses to expand `NSH`,
`GBR`, `DWN`, or other abbreviations into unverified player-facing names.

### Descriptor phase control

The descriptor row's second live pointer targets an array of `0x08`-byte phase
records with the four-halfword contract (animation slot, progression
condition, start frame, rate) and the condition meanings owned by
[Combat action execution](combat_action_execution.md#shared-phase-progression).
Every condition used by substates `0x27..0x62` is one of the five
animation-end/grounded forms, held condition `0`, or a positive secondary
cursor value `3`, `4`, or `6`; no relative jump occurs in these descriptors.

Decoding every ordinary-response descriptor from the exact clean image gives
the following complete phase-condition sequences. Each sequence is read from
phase `0` toward its terminal record. `E` is animation end (`-0x10`), `G` is
grounded (`-0x11`), `D` is negative vertical speed or grounded (`-0x12`), `O`
is animation end or grounded (`-0x13`), `B` is animation end and grounded
(`-0x14`), `C<n>` is secondary cursor `<n>`, `H` is held condition `0`, and
`T` is the terminal `-1` record.

| Phase-condition sequence | Ordinary substates |
| --- | --- |
| `E, E, T` | `0x27..0x2E`, `0x47` |
| `D, C6, T` | `0x2F..0x31` |
| `C4, E, T` | `0x32..0x34` |
| `C4, B, T` | `0x35` |
| `D, G, E, E, T` | `0x36` |
| `D, G, E, T` | `0x37`, `0x52/0x54/0x56/0x58` |
| `G, E, T` | `0x38/0x39`, `0x42..0x44` |
| `E, T` | `0x3A/0x3B`, `0x45/0x46`, `0x4F`, `0x51/0x53/0x55/0x57`, `0x5B` |
| `E, C4, G, E, T` | `0x3C/0x3D` |
| `E, E, E, T` | `0x3E` |
| `E, D, G, E, T` | `0x3F`, `0x59` |
| `O, O, E, E, T` | `0x40/0x41` |
| `C3, G, E, T` | `0x48/0x49` |
| `H, T` | `0x4A..0x4E`, `0x50` |
| `O, G, E, T` | `0x5A` |
| `C4, C6, G, E, T` | `0x5C` |

The primary cursor `+0x1C4` advances by `+0x1AC` and the secondary cursor
`+0x1E8` by `+0x1AC * (+0xB90 / 256)`, and a positive `+0x20C` pause
suppresses both, as described in
[Action and phase clocks](combat_action_execution.md#action-and-phase-clocks).

Most response-phase records author `+0xB90 = 256` (`1.0`). The complete set of
non-default rates in substates `0x27..0x62` is:

| Substate and phase | Authored `+0xB90` | Secondary rate |
| --- | ---: | ---: |
| `0x29/0x2A`, phases `0/1` | `240` | `0.9375` |
| `0x2B/0x2C`, phases `0/1` | `224` | `0.875` |
| `0x2D`, phases `0/1` | `176` | `0.6875` |
| `0x2E`, phases `0/1`; `0x3B`, phase `0` | `192` | `0.75` |
| `0x32..0x35`, phase `1`; `0x3E`, phase `1`; `0x60`, phase `0` | `512` | `2.0` |
| `0x5A`, phase `0` | `64` | `0.25` |
| `0x5B`, phase `0`; `0x5E`, phase `0` | `384` | `1.5` |

Thus ordinary hit-response duration is not one fixed hitstun counter. Most
substates advance at authored animation/contact/timeline conditions, while the
`H` rows require state-specific external progression because the common phase
updater cannot advance condition `0` by itself. The animation-gated lengths
are decoded in
[Animations and animation-gated phase lengths](#animations-and-animation-gated-phase-lengths);
physics-gated phases have no static length.

This is stronger than inferring contact from an action name: `+0xB88` is
cleared when `FUN_00218190` changes animation and is later overwritten by the
return from the resident animation-advance routine. That return becomes
nonzero when the animation reaches its end.

The recovery descriptors independently corroborate the resident recovery
dispatcher. Their complete sequences and authored secondary rates are:

| Recovery substate | Phase sequence | Non-default rate |
| ---: | --- | --- |
| `0x5D` | `H, T` | none |
| `0x5E` | `G, T` | phase `0`: `384/256 = 1.5` |
| `0x5F` | `D, T` | none |
| `0x60` | `C3, T` | phase `0`: `512/256 = 2.0` |
| `0x61` | `E, H, T` | none |
| `0x62` | `G, E, H, T` | none |

Thus the common updater cannot complete held `0x5D` by itself; the resident
threshold dispatcher owns its choices. It completes `0x5E` when grounded,
`0x5F` when vertical response is negative or the fighter is grounded, and
`0x60` at secondary cursor `3`. The separate `0x61/0x62` route ultimately
reaches held phases as well, matching its external state-specific placement
progression rather than the `0x5D` threshold logic.

### Animations and animation-gated phase lengths

The animation slot indexes fighter pointer `+0xB84`, whose entries are the
animation objects that `FUN_001A8F00` looks up by name from the character
record's `ANM_` name array (record `+0x44/+0x48`). The main character loader
`FUN_00215950` preserves this index correspondence, selects the common
container for names whose character-code field is `cmn`, and otherwise uses
the filename at character record `+0x08`. Every `ANM_pcmn` name used below
was found in `CMN/2CMNBOD1.CCS`, and every other required name was found in
that character's named `PL/2???BOD1.CCS` file.

Across all 74 primary records, most referenced slots share one suffix.
Slots `31..33` are `col0..col2`, slot `34` is `kno0`, slot `47` is `gbr0`,
and slot `48` is `ost0`. Three referenced slots have suffix differences: Hiruko uses
`htn0` at slot `1` and `hxn0` at slot `60`, where the other records use
`htn4/hxn4`; slot `69` is `jmp0` for Hiruko and `jmp3` for Classic
Kankuro, rather than the other records' `jpz1`. The counts below include
those actual resources.

The resident CCS loader `FUN_001B1470` stores an animation chunk's
(`0xCCCC0700`) second word as the animation object's frame count `+0x0C`.
`FUN_0024D1C0` advances the animation by `+0xB90 * +0x1AC` in `1/256`-frame
units once per update while `+0x20C < 1`, and `FUN_001BB210` reports the end
once the position reaches `(frame_count - 1) * 256` (non-looping animations).
When a new animation starts, `FUN_00218060` loads it through
`FUN_001B99B0(..., 0)`, which discards any blend object and creates none, then
seeks to start frame `S`; a phase with `R < 256` and `S == 0` is instead
seeked to frame `1`. An animation-end phase with frame count `F`, effective
start `S`, and rate `R` therefore needs `n = max(1, ceil((F - 1 - S) * 256 /
R))` animation advances, one per unpaused update at `+0x1AC == 1.0`.

Within one update, `FUN_00248580` runs the phase updater (live `0x0071F160`)
on the previous animation result, `FUN_00249640` ends by selecting the current
phase's animation (live `0x0071F640`), and the animation pass
(`FUN_0024DA50` -> `FUN_0024D1C0`, reached through the coordinator's removal
pass after `FUN_0024FD80`) then advances it. An animation-end phase therefore
occupies exactly `n` updates, and a timeline phase `C<k>` occupies
`ceil(k * 256 / R)` updates. The state setter does not clear `+0xB88`, but a
state entered by hit routing cannot consume the previous animation's latched
end: the routing pass of `FUN_0024FD80` sets fighter byte `+0x63` bit `0`
while primary event `0` is armed, `FUN_00248580` returns immediately while
that bit is set, and `FUN_0024DA50` clears it after the animation pass.

Decoding every referenced animation chunk in `CMN/2CMNBOD1.CCS` and the
74 characters' named `PL/2???BOD1.CCS` files gives these per-phase counts.
All 40 referenced slots resolve for every primary record, including Second
Stage Kimimaro (`2kmvbod1`) and Second Stage Kidomaru (`2kdvbod1`). The chunk
headers were matched to the
[CCS directory's record names](../../game/files/ccs_runtime.md#parsing-type-dispatch-and-publication),
with in-range record IDs and lengths, matching payload word counts, and a
first nested `0xFF01` command. Each cell is
the phase condition, the animation-name suffix, and `n` (or `ceil` form for
`C<k>`); a range gives the minimum and maximum across all 74 characters with the
median in parentheses. `G` and `D` phases end on physics, so only their
animation is listed; `O` ends no later than `n`, `B` no earlier.

| Substate | Phases and animation-gated update counts |
| --- | --- |
| `0x27/0x28` | E `htn4/htn0` 3, E `hxn4/hxn0` 3..11 (7) |
| `0x29` | E `htn0` 3, E `hxn0` 3..15 (10) |
| `0x2A` | E `htn1` 3, E `hxn1` 3..12 (12) |
| `0x2B` | E `htn0` 3, E `hxn0` 3..16 (11) |
| `0x2C` | E `htn1` 3, E `hxn1` 3..13 (13) |
| `0x2D` | E `htn0` 3, E `hxn0` 3..21 (14) |
| `0x2E` | E `htn1` 3, E `hxn1` 3..15 (15) |
| `0x2F..0x31` | D `fht0`, C6 `jmp2` 6 |
| `0x32..0x34` | C4 `fht0` 4, E `jpz1/jmp0/jmp3` 8..15 (9) |
| `0x35` | C4 `fht0` 4, B `jpz1/jmp0/jmp3` 8..15 (9) |
| `0x36` | D `fht0`, G `fxk0`, E `fxk2` 2, E `col1` 8..28 (28) |
| `0x37` | D `fht0`, G `fxk0`, E `col2` 13..28 (28) |
| `0x38/0x39` | G `spn0`, E `col1` 8..28 (28) |
| `0x3A` | E `col0` 8 |
| `0x3B` | E `col0` 10 |
| `0x3C` | E `nxf1` 3, C4 `fht1` 4, G `fxk1`, E `col1` 8..28 (28) |
| `0x3D` | E `nxf0` 7, C4 `fht0` 4, G `fxk0`, E `col1` 8..28 (28) |
| `0x3E` | E `nxf0` 7, E `yft0` 20, E `col1` 8..28 (28) |
| `0x3F`, `0x59` | E `nxf2` 2..10 (4), D `fht2`, G `fxf0`, E `col2` 13..28 (28) |
| `0x40` | O `nxf3` 4..5 (4), O `fal0` 10, E `fxk2` 2, E `col0` 8 |
| `0x41` | O `nxf3` 4..5 (4), O `yft0` 40, E `fxk0` 6, E `col1` 8..28 (28) |
| `0x42` / `0x43` / `0x44` | G `fxc1` / `fxc0` / `fxc2`, E `col2` 13..28 (28) |
| `0x45/0x46` | E `col2` 13..28 (28) |
| `0x47` | E `fxk0` 6, E `col1` 8..28 (28) |
| `0x48` | C3 `fxc1` 3, G `spn0`, E `col1` 8..28 (28) |
| `0x49` | C3 `col2` 3, G `bnd0`, E `col1` 8..28 (28) |
| `0x4A..0x4E`, `0x50` | H `hth0`, `hah0`, `hth1`, `nxf3`, `hth2`, `hth0` |
| `0x4F` | E `gbr0` 14..34 (24) |
| `0x51/0x53/0x55/0x57` | E `htn3` 40..60 (40) |
| `0x52/0x54/0x56/0x58` | D `fht0`, G `fxk0`, E `col2` 13..28 (28) |
| `0x5A` | O `fxk1` 20..24 (24), G `fal0`, E `col1` 8..28 (28) |
| `0x5B` | E `ost0` 26..30 (27) |
| `0x5C` | C4 `fht0` 4, C6 `jmp2` 6, G `dow0`, E `lan0` 9..20 (10) |

The `nxf3` upper bound comes from Second Stage Kidomaru's six-frame
`ANM_pkdvnxf3` chunk at decompressed `2KDVBOD1.CCS` offset `0x111D30`.
The `0x5B` lower bound comes from Asuma's 39-frame `ANM_paswost0` chunk
at decompressed `2ASWBOD1.CCS` offset `0x8526C`: its rate `384` gives
`ceil(38 * 256 / 384) = 26` advances.

For example, a grounded light hit `0x27` on a median character occupies about
`3 + 7 = 10` unpaused updates of animation before it returns to neutral, in
addition to the attack pause described below, while the downed `col` phases
dominate the knockdown rows. **Inference:** the `htn`/`hxn` pairs are hit and
recovery halves of the light reactions and `col` is the landing/collapse
animation; the names are recorded, not visually confirmed.

The recovery substates use `kno0` (`0x5D`, two frames), shared or
character-owned `jmp2` for `0x5E..0x60`, `col0` then `kno0` for `0x61`, and per-character `dow0`,
`lan0`, `nut0` for `0x62`. Timeline phase `0x60` therefore completes after
`ceil(3 * 256 / 512) = 2` updates, and the `col0` phase of `0x61` after 8.

## Table-driven knockback and launch

The ordinary response table begins at resident runtime `0x00407670`, ELF file
offset `0x00307770`. It has `0x18`-byte entries indexed by
`substate - 0x27`, covering all 54 rows through `0x5C`. The bytes immediately
after the `0x5C` row begin unrelated pointer/data content, independently
confirming the table boundary. Decoding the exact clean bytes and tracing every
consumed field establishes this layout:

| Entry offset | Type | Demonstrated consumer behavior |
| ---: | --- | --- |
| `+0x00` | `u16` flags | Low bits choose the primary/secondary action timeline; high byte chooses replacement/addition behavior for the two response-speed fields. |
| `+0x02` | `s16` event gate | Timeline point tested before applying the entry's motion. Values used here are `0..3`. |
| `+0x04` | `f32` | Planar response speed ultimately stored at fighter `+0x994`, with orientation and combat modifiers. |
| `+0x08` | `f32` | Vertical response speed ultimately stored at fighter `+0x998`, with combat modifiers. |
| `+0x0C` | `f32` | Approach/damping factor used while moving `+0x994` toward zero on updates that do not cross the event gate. |
| `+0x10` | `f32` | Gravity argument copied to fighter `+0x9B4` when not `1.0`; in hit response it only lifts the terminal-speed clamp. |
| `+0x14` | `s16` | Event impulse copied, with sign handling, into the `+0x204..+0x21C` response channel. |
| `+0x16` | `s16` | Minimum raised into general timer/lock `+0x254`; an attack-record `+0x30` contribution may be added. |

`FUN_00234da0` invokes the common table updater every action update. All 54
rows select the primary timeline. On the exact update where that cursor crosses
the row's event gate, the updater writes the two response-speed components and
preserves a copy of the attack-owned motion scale. On every invocation that
does not cross the gate, including later ones, it instead approaches planar
speed `+0x994` toward zero using the row's damping factor. The gate is therefore
a one-shot event edge, not a condition that remains true after the threshold.
The auxiliary value `+0x10` is copied whenever this updater runs and it differs
from `1.0`.

A separate crossing test applies entry `+0x14` to the pause channel. With
fighter `+0xB00 == 0`, it uses the row's authored event gate; with `+0xB00`
nonzero, it uses primary event `0` instead. Therefore displacement is not
encoded in the substate alone: it is the substate's table row plus event edge,
orientation, attacker and defender modifiers, and current motion.

The complete clean table is compacted below only where rows are byte-equivalent.
`R` means flags `0x0101`: use the primary timeline and replace both speed
components. `A` means `0x0201`: use the primary timeline and add both speed
components to their current values.

| Substate(s) | Mode | Gate | Planar | Vertical | Damping | Aux | Pause | Lock |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0x27/0x28` | R | `0` | `10` | `0` | `0.35` | `1` | `1` | `5` |
| `0x29/0x2A` | R | `0` | `30` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2B/0x2E` | R | `0` | `45` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2C` | R | `0` | `40` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2D` | R | `0` | `50` | `0` | `0.35` | `1` | `1` | `5` |
| `0x2F` | R | `0` | `30` | `25` | `0.25` | `1` | `1` | `5` |
| `0x30` | R | `0` | `40` | `30` | `0.25` | `1` | `1` | `5` |
| `0x31` | R | `0` | `50` | `35` | `0.25` | `1` | `1` | `5` |
| `0x32` | R | `0` | `10` | `50` | `0.125` | `1` | `2` | `5` |
| `0x33` | R | `0` | `30` | `45` | `0.125` | `1` | `2` | `5` |
| `0x34` | R | `0` | `50` | `40` | `0.125` | `2` | `5` | `0` |
| `0x35` | R | `0` | `65` | `25` | `0.12` | `1` | `2` | `5` |
| `0x36` | R | `0` | `55` | `20` | `0.10` | `1` | `1` | `120` |
| `0x37` | R | `0` | `50` | `32.5` | `0.15` | `1` | `1` | `120` |
| `0x38` | R | `0` | `50` | `40` | `0.075` | `2.5` | `1` | `120` |
| `0x39` | R | `0` | `60` | `25` | `0.075` | `2` | `1` | `120` |
| `0x3A` | R | `0` | `10` | `0` | `0.25` | `1` | `1` | `6` |
| `0x3B` | R | `0` | `30` | `0` | `0.25` | `1` | `1` | `8` |
| `0x3C/0x3D` | R | `0` | `60` | `20` | `0.075` | `1` | `2` | `120` |
| `0x3E` | R | `0` | `80` | `0` | `0` | `1` | `2` | `120` |
| `0x3F` | R | `0` | `0` | `55` | `0.35` | `1` | `2` | `120` |
| `0x40` | R | `0` | `0` | `-50` | `0.35` | `1.25` | `1` | `120` |
| `0x41` | R | `0` | `60` | `-50` | `0.05` | `0.8` | `2` | `120` |
| `0x42/0x45` | R | `2` | `0` | `0` | `0.35` | `1` | `2` | `120` |
| `0x43` | R | `3` | `0` | `0` | `0.35` | `1` | `2` | `120` |
| `0x44` | A | `2` | `0` | `-30` | `0.35` | `1` | `2` | `120` |
| `0x46` | R | `1` | `15` | `7.5` | `0.075` | `1` | `2` | `120` |
| `0x47` | A | `1` | `20` | `0` | `0.05` | `1` | `1` | `120` |
| `0x48` | R | `2` | `0` | `40` | `0.075` | `1` | `2` | `5` |
| `0x49` | R | `3` | `10` | `40` | `0.075` | `0.75` | `2` | `5` |
| `0x4A/0x4B/0x4C/0x4E` | R | `0` | `0` | `0` | `0.35` | `1` | `1` | `0` |
| `0x4D` | R | `0` | `0` | `0` | `0.35` | `1.5` | `1` | `0` |
| `0x4F` | R | `0` | `20` | `0` | `0.5` | `1` | `0` | `5` |
| `0x50` | R | `0` | `0` | `0` | `0.35` | `1` | `4` | `0` |
| `0x51/0x53/0x55/0x57` | R | `0` | `40` | `0` | `0.35` | `1` | `1` | `120` |
| `0x52/0x54/0x56/0x58` | R | `0` | `40` | `30` | `0.075` | `1` | `1` | `120` |
| `0x59` | R | `0` | `0` | `55` | `0.075` | `1` | `2` | `120` |
| `0x5A` | A | `0` | `0` | `0` | `0.25` | `1` | `0` | `120` |
| `0x5B` | R | `0` | `40` | `0` | `0.10` | `1` | `0` | `5` |
| `0x5C` | R | `0` | `40` | `40` | `0.10` | `1` | `1` | `6` |

Negative vertical values are preserved as authored and processed through the
same velocity field; this document does not assume which screen-space
direction the content author considered positive.

### Velocity modifier order

The table values are authored bases, not guaranteed final speeds.
`FUN_0021ACB0` first applies orientation and the row's replace/add flags, then
uses the following mutually exclusive source/receiver modifier chain:

1. If `FUN_00307320(source)` returns scalar `s != 1.0`, planar speed is
   multiplied by `s` and vertical speed by `1 + 0.5 * (s - 1)`.
2. Otherwise, in ordinary major state `5` with `(fighter[+0xB00] & 0xFF00)`
   nonzero, both components are multiplied by `1.25`.
3. Otherwise, source field `+0x154` applies the same planar/full and
   vertical/half-strength formula. Receiver field `+0x150` is then clamped to
   `[0,2]`; for clamped value `q`, planar speed is multiplied by
   `1 - 0.75 * (q - 1)` and vertical speed by `1 - 0.25 * (q - 1)`.

After that chain and the shared response-coupling helper, transient fighter
modifiers at `+0x9A0`, `+0x9A8`, and `+0x9AC` can further scale both
components, planar only, and vertical only respectively. Each consumed
transient is reset to `1.0`. The source object itself is accepted for this
chain only when non-null and its raw field `+0x0C` is zero. These facts explain
why the clean table supports reproducible base comparisons but cannot alone
predict character- and situation-specific displacement.

`+0x9A0` is the attack's own knockback scale. When a hit arrives with a new
attack record, `FUN_00232A50` (or the retarget path of `FUN_00241F10`)
retains the record, resets the repeat count `+0xE5C` from record `+0x2E`,
and, when that count is nonzero, copies record float `+0x28` to `+0x9A0`.
At the row's event edge `FUN_0021ACB0` saves it to `+0x9A4` and, for scale
`s != 1.0`, multiplies planar speed by `s` and vertical speed by
`1 + 0.5 * (|s| - 1)` when `|s| > 1`; for `|s| <= 1` vertical speed is
multiplied by `|s|`, or by the half-strength form when the source scalar is
below `1.0`. Before replacing or adding the row speeds, the same edge clamps
the current planar speed to the character-table limit at `+0x60` (grounded)
or `+0x74` (airborne) and the current airborne vertical speed to at least
`-3 * +0x70` of the table selected by `FUN_00307C50`.

Of the 2,484 damaging records, 1,859 author `+0x28 == 1.0`; 423 are
stronger (`1.5` on 154, `1.25` on 149, `1.2` on 37, `2.0` on 33, and other
values from `1.1` to `3.0` on 50), 200 are weaker (`0.75` on 63,
`0.8` on 29, down to `0.0` on 11), and two are negative (`-0.5`, `-2.0`),
which reverses the planar direction.

### Gravity and airtime

The movement pass `FUN_0024A660` (called from `FUN_0024CFD0` in the
`FUN_0024DA50` animation pass, so only while `+0x20C < 1`) moves the fighter
by its current speeds times `+0x1AC` and then, while airborne, applies
`FUN_002183D0(+0x9B4, fighter, &+0x998)`. For a fighter in major state `5`,
with nonzero `+0xB00`, or with byte `+0x61` bit `7` set, that routine uses a
fixed gravity of `3.0 * +0x1AC` per update and a terminal vertical speed of
`-90`; the ordinary character-record gravity used by other states is owned by
[Movement and physics](../stages/movement_and_physics.md#gravity-and-input-smoothing).
Thus the response row's auxiliary field `+0x10`, copied to
`+0x9B4` on every response update, does not scale hit-response gravity: a
nonzero value only removes the `-90` clamp when it differs from `1.0`, and
`+0x9B4` is reset to `1.0` after each movement pass.

Because the launch speed is written in the hit update and the first movement
pass follows in the same update, an ordinary response launched with final
vertical speed `v > 0` (row value after the modifiers above) at rate `1.0`
reaches a negative vertical speed, satisfying a `D` phase, after
`floor(v / 3) + 1` active updates. **Inference:** over flat ground at the
launch height the fighter lands after roughly `2v/3 + 1` active updates,
for example about 14 to 15 for the unmodified `0x3C/0x3D` value `20` and
about 38 for the `55` of `0x3F`; ground contact is decided by stage collision
geometry, so these are not exact. The pause updates add to these counts
because they suspend movement.

## Fighter-update pause and action lock

The response timing uses two ordered generic countdown blocks rather than one
undifferentiated “hitstun timer”:

1. The current count at `+0x20C` is decremented at a fixed rate of `1.0`.
   While it is positive, the main fighter loop does not run the normal action
   timeline or per-action update dispatch. The displayed position instead uses
   a jittered copy whose variation is driven by this count. This establishes a
   fighter-update pause, conventionally comparable to hitstop, without assuming
   a display-frame duration.
2. Only after `+0x20C < 1` does the main timer update decrement `+0x254`, using
   the fighter's update-rate scalar at `+0x1AC`. `FUN_00239e50`, which is called
   by native action-selection and input-action paths, returns false whenever
   `+0x254` is nonzero. This establishes an action-entry lock.

Initializers normally stage authored positive value `N` as `-N` with block
flag `0x0004`; the next `FUN_0024C440` maintenance pass activates it to `N`
instead of decrementing, so a newly staged pause is not shortened on that
pass, and a read between initialization and activation can see a negative
`+0x20C` or `+0x230`. Activation and the `FUN_00211E70` decrement arithmetic
are owned by
[Timer primitives](../../runtime/timer_primitives.md#fractional-integer-cursor-block).

Ordinary response-table field `+0x14` feeds the `+0x20C` pause channel at its
timeline event, subject to the `+0xB00` event-`0` override above. A positive
table value is staged negative with pending flag `0x0004`, but only when that
flag is not already set; when activated, the pause suspends both action
timelines and the per-action dispatcher.

Attack-record signed halfword `+0x30` feeds the same channel earlier, during
accepted-hit initialization (`FUN_00224510(fighter, attack, 0)` from
`FUN_00232B80`). An authored positive `N` is staged as `-N` with the pending
flag, while an authored negative `-N` is written immediately as positive `N`
without that flag. Zero clears the block but leaves the pending flag set with
a zero count, and sentinel `0x7FFF` does not touch the block. Because the row
pause is skipped while the flag is pending, a positive or zero attack value
suppresses the row's `+0x14` pause on a gate-`0` row; the row value applies
after sentinel `0x7FFF` or a negative attack value, or on a later gate.

`FUN_002346B0` applies the row's `+0x16` action-lock minimum when the primary
timeline crosses event `0`. When the table minimum raises `+0x254`, the
absolute attack-record `+0x30` contribution is added unless it is sentinel
`0x7FFF`; when the current lock already meets the minimum, the lock is left
unchanged. The lock is written directly as a positive count without a pending
flag.
Attack-record `+0x10` bit `0x00000002` instead forces a count of `20`. With
that bit clear, the table minimum is bypassed when either raw attack type mask
`0x00F00000` or `0x000F0000` is nonzero.
The full time before a fighter can act therefore includes
the ordered pause and action-lock counts as well as the response state's own
timeline and exit conditions; `+0x254` alone is not total hitstun. The exact
update-by-update order is in
[Hit update order and elapsed updates](#hit-update-order-and-elapsed-updates).

`FUN_00239e50` makes that last distinction concrete. Once `+0x254` is zero,
ordinary major state `5` still rejects ordinary action entry throughout
`0x27..0x5A`; `0x5B/0x5C` are immediately eligible, while a special selector
value `2` can bypass the ordinary-state rejection. In recovery major state `6`,
`0x5D/0x5E` remain ineligible, `0x5F` becomes eligible at action cursor
`+0x1C4 >= 8`, and `0x60` becomes eligible at cursor `>= 3`. Other recovery
substates are rejected by this predicate. These are action-entry gates, not
animation-completion tests.

## Hit update order and elapsed updates

Native battle gameplay advances fighter updates at 30 Hz at nominal speed
([Battle lifecycle](../session/battle_lifecycle.md#battle-update-cadence)). Within one
update, resident `FUN_001F03E0` calls the fighter coordinator's registry slot
`+0x0C` (`FUN_002504B0`), then slot `+0x10`, then slot `+0x14`
(`FUN_00250800`). `FUN_002504B0` runs `FUN_0024FD80` and then the generic
removal pass (live `0x00709C70`, see
[Battle entities](../session/battle_entities.md)), which calls every fighter's virtual
slot `+0x10`, `FUN_0024DA50`: while `+0x20C < 1` it runs the movement pass
`FUN_0024CFD0` and the animation pass `FUN_0024D1C0`. Coordinator slot
`+0x14` finally calls every fighter's virtual slot `+0x18`, `FUN_0024DE40`,
which advances both action timelines through `FUN_0024D5E0` while
`+0x20C < 1`.

`FUN_0024FD80` itself runs these passes in order over the fighter list:

1. `FUN_0024C440` maintenance for every fighter (lock decrement while the
   pause count is below `1`, secondary and pause block activation or
   decrement);
2. pair and interaction helpers, then for each active fighter the pair hit
   resolver `FUN_0021ED70` and the `+0xE3C` hit bits: `0x100` calls
   `FUN_00220690`, `0x1` calls router mode `0`, `0x8` mode `2`, and `0x4`
   mode `1`;
3. removal of fighters whose slot `+0x1C` requests it;
4. for every fighter with `+0x20C < 1`: `FUN_00217320`, `FUN_002173D0`,
   `FUN_00248580`, input update `FUN_00248EC0`, and per-action dispatcher
   `FUN_00249640`; and
5. `+0xE3C` bit `0x2` handling through `FUN_00221600`.

The action-state setter clears the primary block with its step flag set, so
`FUN_002118A0(block, 0)` reports event `0` on the first per-action update
after entry and stops reporting it once `FUN_0024D5E0` advances the cursor.
Because routing (pass 2) precedes the per-action pass (pass 4) in the same
update, event `0` of a new ordinary response runs in the hit update itself
whenever `+0x20C` is still below `1` after routing. That is the case for a
positive, zero, or sentinel attack `+0x30` with no active pause, because the
positive form is only staged negative. It is not the case for a negative
`+0x30`, which activates the pause immediately and delays event `0` until the
pause ends.

For an authored positive attack pause `N`, rates `+0x1AC == 1.0` for both
fighters, and no already-pending blocks, the exact sequence is:

| Update | Receiver behavior |
| ---: | --- |
| `0` | Accepted hit routed; `(5, response)` entered; pause staged `-N`; per-action pass runs event `0`: gate-`0` response motion, gated attack damage (see [Damage](damage.md)), action lock, and the `+0x230` countdown staging below; row pause skipped because the attack pause is pending; first movement and gravity step and first animation advance; the timeline advances to cursor `1`. |
| `1` | Maintenance decrements the lock once (pause still `-N` at that check), then activates the pause at `N`. Per-action, movement, animation, and timeline passes are suppressed. |
| `2..N` | Pause counts down; everything action-related remains suppressed and the lock does not decrement. |
| `N+1` | Maintenance sees pause `1` at the lock check (no lock decrement), then reaches `0`; the per-action pass and timelines resume. |

The freeze is not total. While `+0x20C >= 1`, slot `+0x10` (`FUN_0024DA50`)
skips the animation pass but, for fighters whose `+0x60` bits `5..8` are
zero, still runs the command bridge `FUN_00217320`, input action selection
`FUN_0023A390` with `+0x338`, and the `+0x95C` guard-input age update. A
candidate such as an Extra Hit counter can therefore be chosen during the
pause.

Thus an authored pause of `N` suspends the receiver's action, timeline, and
animation updates for exactly `N` updates after the hit update, or `N/30` s
at nominal speed. If the row minimum `L` set the lock
to `L + N` in update `0`, the lock reaches zero in update `2N + L`. For a
negative authored `-N`, updates `0..N-1` are frozen and event `0` runs in
update `N`; if the row pause then applies, a second freeze of the row's
`+0x14` count follows. A rate other than `1.0` scales the lock and timeline
steps, but not the pause, which always decrements by `1.0`.

The attacker receives a matching pause through `+0xE3C` bit `0x100`, handled
by `FUN_00220690(attacker)` in the same routing pass. It applies the router's
two early-return bit patterns to the result of the sibling classifier
`FUN_00240990` and requires the defender's `+0x230`
to be non-positive and either attack `+0x10` bit `0x2` or a nonzero expected
repeat count. Unless `+0x10` bit `0x2` is set, it then calls
`FUN_00224510(attacker, attack, 1)`, whose attacker/guard mode inverts the
sign convention: an authored positive `N` is written as an active `N`
immediately, so the attacker is suspended in updates `0..N-1`, one update
earlier than the receiver. Attack `+0x14` bit `0x00020000` skips the
attacker pause entirely (151 records, 138 damaging). With sentinel `0x7FFF`,
the attacker instead takes the `+0x14` pause of the response row that
`FUN_00231C60` selects for the defender, or of the guarded-response row when
the defender's `+0x95A` guard state applies, also active immediately.

The clean attack tables give the following authored pause values. Of 2,484
records with nonzero damage `+0x24`, `+0x30` is `2` on 914, `3` on 415, `1`
on 271, `4` on 194, `5` on 86, sentinel `0x7FFF` on 477, zero on 44, and a
negative value on 66; the remaining 17 use `6..16`.

## Response exits, contact stages, and downed handoff

Live overlay `0x0071F160` (preserved export `FUN_0071f120` at
`0x0071F120`) produces the common phase/event-completion signal. The resident
per-frame dispatcher passes that signal to `FUN_00233870`. The following
transitions are direct static facts:

| Current ordinary substate | Completion/contact behavior |
| --- | --- |
| `0x27..0x2E` | Completion enters neutral `(0,0)`. |
| `0x2F..0x31` | Completion enters `(4,0x26)` if grounded, otherwise `(3,0x1E)`. |
| `0x32..0x35` | Completion enters `(4,0x26)` if grounded, otherwise `(3,0x25)`. |
| `0x36..0x39` | Completion calls the timed-down handoff with scale `1.0`. |
| `0x3A..0x3B` | Completion calls the same handoff with scale `1.0 - 0.25 * fighter[+0xB6E]`. |
| `0x3C..0x41` | Completion calls the timed-down handoff; later grounded/contact checks can replace it with `0x42..0x47`. |
| `0x42..0x49` | Completion calls the timed-down handoff. |
| `0x4A..0x4E` | Their held descriptors call the separate `FUN_002316d0` handoff every update; its exact paired-fighter matrix is below. |
| `0x4F` | Uses the dual neutral-exit gates detailed below; animation completion alone is not always sufficient. |
| `0x50` | Enters neutral immediately when the paired fighter is not in major state `8`; while the pair remains in major `8`, it requires an external nonzero completion signal. |
| `0x51..0x58` | Completion calls the timed-down handoff. |
| `0x59` | Crossing primary-timeline event `1` calls the separate paired callback `FUN_00216d00(...,5)`; descriptor completion itself causes no transition in this switch. |
| `0x5A` | While grounded and below phase `2`, each dispatch forces phase `2`; completion calls the timed-down handoff. |
| `0x5B` | On completion, nonzero `+0xB10` on either paired fighter transfers this fighter to `(8,0x14)`; otherwise it enters neutral. While its own `+0xB10` is nonzero, it also runs a dedicated planar-motion continuation helper. |
| `0x5C` | On completion, the same paired `+0xB10` condition transfers to `(8,0x14)`; otherwise it enters neutral if grounded or `(3,0x1E)` if airborne. It uses the same continuation helper. |

For held `0x4A..0x4E`, `FUN_002316D0` first inspects the fighter at `+0x20`.
When there is no non-null major-state-`8` current action record, paired recovery
`(6,0x61/0x62)` transfers this fighter to `(6,0x61)`; every other paired state
enters `(2,0x1D)`. Before the latter entry, the routine restores the saved
response position at `+0xAE0..+0xAEC` when the paired action pointer is null,
or its `+0x10 & 0x00000F00` mask is zero, or its
`+0x14 & 0x04000000` flag is zero. It then refreshes facing/position state. No
player-facing name is assigned to `(2,0x1D)`.

When the paired fighter is in major state `8` with a non-null current action
record, these are the complete remaining branches:

| Paired action/event condition | Held fighter result |
| --- | --- |
| action `+0x14 & 0x04000000` nonzero | no transition |
| that flag clear, action `+0x10 & 0x00000100` nonzero, and current event-record bit `0x2` clear | neutral `(0,0)` |
| same action bit set and event-record bit `0x2` set | no transition |
| action bits `0x100` and `0x200` both clear | neutral `(0,0)` |
| action bit `0x100` clear, bit `0x200` set, and current event-record bit `0x8` set | re-enter `FUN_00232B80` with that paired action, allowing another ordinary response to be selected |
| preceding action-bit form but event-record bit `0x8` clear | no transition |

Thus the condition-`0` descriptor is an externally held response synchronized
to paired-fighter state, not indefinite hitstun or an autonomous timer. The
sender-side capture actions, anchor attachment and handoff that drive these
held responses are owned by
[Throws and captures](throws_and_captures.md#common-entry-handoff-and-interruption).

Response `0x4F` has a separate paired-rate sequence. At primary event `0`,
`FUN_00231A40` clears private stage/counter `+0x960/+0x962`. On that same
driver invocation, stage `0` writes `0.1` to both paired fighters' `+0x1B0`,
runs a separate paired effect, and enters stage `1`. Stage `1` advances to
stage `2` when the pre-increment counter is greater than `4`, which takes six
driver invocations from counter zero. Stage `2` likewise takes six invocations,
approaches both `+0x1B0` values toward `1.0` on each call, and finally enters
stage `3`, explicitly restoring both values to `1.0`. Counting the initial
stage-`0` call, stage `3` is reached on the thirteenth unpaused
`FUN_00231A40` invocation.

The exit dispatcher sends `0x4F` to neutral under either exact condition:

```text
paired fighter is major 8, has a non-null current action record,
and action[+0x10] & 0x00F00000 is nonzero

or

the 0x4F animation descriptor is complete and fighter[+0x960] == 3
```

The first branch also clears the complete `+0x248` action-lock block. The
second proves why descriptor completion can remain latched for additional
updates until the paired-rate sequence finishes. The native identifier
`ACT_DMG_GBR` is not expanded into a speculative gameplay label.

Response `0x50` is another externally held row. Its descriptor is `H, T`, so
the common updater cannot complete it. The ordinary exit switch converts a
zero completion signal to nonzero whenever the paired fighter is not in major
state `8`, then enters neutral. If the pair remains in major `8`, `0x50` stays
held until another path supplies a nonzero completion signal. This is paired
state synchronization, not a fixed counter.

### Automatic contact impulses and their suppression

Before that per-state switch, `FUN_002310F0` can replace a live launch response
with `0x48` or `0x49`, without recovery input. These are mechanically
demonstrated contact rebounds: their response-table event supplies positive
vertical speed `40`, while the action remains ordinary major `5`. The exact
proposal order is:

| Current response and contact | Proposal code / destination | Primary-cursor ceiling |
| --- | --- | ---: |
| `0x3C/0x3D/0x41`, byte `+0x63` bit `6` set | `1 / 0x48` | `5` |
| `0x3E`, that bit set, phase below `2` | `3 / 0x48` | `0x7FFFFFFF` |
| `0x40/0x41`, grounded bit set | `2 / 0x49` | `5` |

The ground proposal is evaluated last, so it wins when `0x41` has both
contact bits. Every proposal requires retained attack `+0xE54`, saved
motion scale `+0x9A4 > 0.5`, external mode zero, and attack
`(+0x14 & 0x00080000) == 0`. It then requires either cursor strictly below
the ceiling or attack `(+0x14 & 0x00100000) != 0`; nonzero fighter `+0xB00`
also requires that latter flag. That flag overrides the cursor and exchange
gates, not the `0x00080000`, scale, contact, or external-mode gates.
The helper returns a proposal rather than changing state. The dispatcher
force-enters its destination, sets transient motion scale `+0x9A0 = 2.0`
for proposal `3`, calls `FUN_00237060`, and returns before the ordinary
state switch. That call can consume the struck fighter's own chakra under
its resource/effect gates; it is not a recovery-input test. Resource
ownership belongs to [Chakra and guard](chakra_and_guard.md).
Contact entry `FUN_002312B0` changes facing for `0x48` and clears a positive
retained repeat count `+0xE5C`; entry to `0x49` instead restores transient
attack scale `+0x9A0` from saved `+0x9A4`. The `0x3E` proposal's later
`2.0` write applies after that initialization. The new row's motion uses the regular event engine:
`0x48` writes its impulse at primary event `2`, `0x49` at event `3`, with
the modifiers described above. Their descriptors ultimately hand off to
the timed downed state; they do not directly grant neutral action entry.

The contact producer is the fighter's movement pass `FUN_0024A660`, which
clears and recomputes side bit `+0x63 & 0x40`, grounded bit `+0x63 & 0x80`
and ceiling bit `+0x64 & 1`, saves the pre-contact vertical speed in
`+0x9B0` on first grounding, and maintains grounded count `+0xB9A`
([Movement and physics](../stages/movement_and_physics.md#floor-side-surfaces-and-limits)).
These are refreshed contact facts on the struck fighter, not a persistent
rebound-enable flag.

A data scan of all 3,428 primary records in the 74 clean tables
found one record with attack `+0x14 & 0x00080000`: Classic Choji, action
index `25`, authored selector `0x15` (`0x40`). Exactly 25 damaging records
in 13 tables have `0x00100000`: selectors `0x12/0x13/0x15/0x16` occur
`3/3/14/5` times. None has both flags. These are initial authored values;
the audited response callbacks contain these direct live-record writers:

| Source callback / action index | Contact flag change |
| --- | --- |
| Rock Lee `FUN_002BF9A0`, `0x36` | Clears `0x00080000` while source byte `+0x67FC < 1`, otherwise sets it; mode `2` then increments that byte. |
| Deidara `FUN_002B68F0`, `0x2C` | Clears `0x00080000`, then sets it when receiver response count `+0xB64 >= 3`. |
| Guy `FUN_002C55B0`, `0x25` | Sets `0x00100000` while source byte `+0x69B0 < 2`, otherwise clears it. |

The retained attack pointer belongs to the struck fighter, while its record
and these callback writes originate from the source's live action table.
`+0x9A4` is the saved attack scale from the response event. A new retained
attack/event or a new contact pass changes these inputs; no separate rebound
countdown is read by `FUN_002310F0`. The callback inventory is bounded to
the 74 response entries and Guy's delegated entry, not all action-record
writers elsewhere in the program.

#### Character contact-flag lifetimes

**Observation:** Lee's action `0x36` uses an attacker-owned signed byte,
not a decrementing time block. Constructor `FUN_002BCCB0` zeroes the
`0x20`-byte block starting at `+0x67F8`, including byte `+0x67FC`.
Channel-2 callback `FUN_002BDB50` clears `+0x67FC/+0x67FD` whenever the
paired fighter's major state is not `5`. Instructions
`0x002BDB94..0x002BDBC0` establish the opponent pointer, the major-state
comparison, and the two byte stores through base `source+0x67F8`.
It does not clear the live action's contact flag in that branch.

The response callback tests the old byte before incrementing it:
`0x002BFFA0..0x002BFFD4` uses signed `lb`, clears attack `+0x14` bit
`0x00080000` at byte values `<=0`, and sets it at values `>0`;
`0x002BFFD8..0x002BFFEC` increments the byte only for mode `2`.
Thus a mode-`0` selection query can rewrite the flag but cannot increment
this counter. Under an uninterrupted nonnegative sequence starting at zero,
the first mode-`2` callback clears the flag and leaves byte `1`; the next
sets the flag and leaves byte `2`. This is a callback-count condition,
not a proved count of visible rebounds. The byte addition has no saturation
check in this branch; signed wrap remains possible in the instructions,
without evidence that an ordinary match reaches it.

**Observation:** Guy's action `0x25` instead tests signed source byte
`+0x69B0` without incrementing it in the response callback. The clean
`lb; slti ...,2` at `0x002C58FC/0x002C5900` leads to a set of
`0x00100000` below `2` and a clear at `2` or more, ending at
`0x002C5934`. The constructor, channel-2 reset, and channel-3 event
increments of this shared chain byte are documented in
[Substitution](../characters/substitution.md#callback-ordering-and-counter-ownership).
Their ordering matters here: hit routing queries the response callback
before the later channel-2/channel-3 pass, so a later reset or event increment
does not retroactively recompute a flag already selected during that update.
The reset writes the byte, not the contact bit. A later response query for
action `0x25` must rewrite that bit from the then-current byte.

Deidara's action `0x2C` reads the receiver's existing `+0xB64` before
ordinary initializer `FUN_00232B80` performs its gated increment of that
counter. The callback clears `0x00080000` first and sets it only when the
value read is at least `3`; the later increment can therefore raise the
counter to `3` while this query still leaves the flag clear. This statement
is conditional on the initializer's increment gates, rather than a claim
that the fourth visible hit always suppresses contact rebound. Counter
ownership and the major-state reset are described in
[Ordinary response selection](#ordinary-response-selection).

All three writers change the source's writable record, not a flag copied
into the receiver. `FUN_00238A70` selects `+0xA54 + index*0x54` as the live
current record and calls `FUN_002391B0`, which clears only fighter action
bytes `+0xA40/+0xA42/+0xA43/+0xA44`. Neither routine restores attack
`+0x14`. The inspected counter-reset branches likewise do not restore it.
**Bounded inference:** resetting a chain counter or re-entering an attack
does not alone restore its clean contact bits; a subsequent relevant
callback or separate action-table setup can change them. This does not
exclude other writers or reloads outside the inspected families.
Static definitions and writable action-table setup are owned by
[Action commands](action_commands.md#action-table-source-and-setup).

The Lee and Guy byte writers above were located from resident immediate
`0x67F8/0x67FC` and `0x69B0` matches, followed by the constructors and
callbacks. The Lee counter is accessed at `+4` from `source+0x67F8`, so an
exact `0x67FC` immediate alone misses it. These bound the immediate forms,
not pointer aliases, overlay writers, or indirect stores. No native
contact-rebound meter or countdown is established by them.

Deidara has a separate attack-side response-window baseline. Channel-3
`FUN_002B5250` sets source bytes `+0x5BCC/+0x5BCD` to `-1` at primary
event `0` of action `0x2C` (`0x002B6160..0x002B6180`, with base
`source+0x5BCC`). This is an event reset, not a countdown. In response
callback `FUN_002B68F0`, phase `0` writes baseline `+0x5BCC = 0` and
returns `0x33`. Other phases use repeat value `R` from `FUN_00231BF0`:

```text
if (phase == 1 and baseline == -1) or (R > 5 and +0x5BCD == -1):
    baseline = byte(R - 5)
    +0x5BCD = 0

R - signed baseline < 3 -> response 0x41, attack +0x32 = 0x7FFF
otherwise               -> grounded 0x29, airborne 0x35
```

Before those branches, this callback always writes attack `+0x32 = 1`;
only the `0x41` branch replaces it with the sentinel. The subtraction and
signed baseline load are at `0x002B6C18..0x002B6C30`, and the sentinel
store at `0x002B6CC8..0x002B6CCC`. These baseline and record writes occur
before the mode-`2` receiver-motion gate, so mode-`0` queries can change
them too. They are independent of the earlier receiver-`+0xB64` contact
suppression test in the same callback. Thus one query can select `0x41`
and its row-owned rejection count while separately setting the flag that
prevents the automatic contact replacement.

Action `0x2B` in that response callback has another explicit switch:
it first writes `+0x32 = 1`, then returns `0x3F` with `+0x32 = 0x7FFF`
when `R < 3`; at `R >=3` it returns `0x34` and retains `1`
(`0x002B6AB8..0x002B6AF4`). The `0x3F/0x41` rows have base rejection
count `120` when the sentinel reaches ordinary event `0`, whereas the
explicit `1` uses attack-owned initialization. The generic pause/rate and
pending-channel rules still apply; this is not a fixed measured lockout.
The channel-2 body `FUN_002B4D60` changes action `0x2C` motion rows at
phase events but does not reset these two bytes or the contact bit.
Wider lifetime of the baseline outside this inspected event/query family
remains unproved.

If neither the earlier input-recovery entry nor that pre-switch replacement
returns, the state switch evaluates these later contact conditions:

| Current | Later contact transition |
| --- | --- |
| `0x3C` | Airborne plus fighter byte `+0x63` bit `6` set enters `0x42`. |
| `0x3D` | The same condition enters `0x43`. |
| `0x3E` | Fighter byte `+0x63` bit `6` set enters `0x43`, without the additional airborne test. |
| `0x3F` | Fighter byte `+0x64` bit `0` set enters `0x44`. |
| `0x40` | On becoming grounded, enters `0x46` when primary cursor is below `4` and external mode is zero; otherwise enters `0x45`, clears the grounded bit, and writes vertical speed as `-0.5 * +0x9B0`, reading that field after the state change. |
| `0x41` | On becoming grounded, enters `0x47` and clears the grounded bit. |

The `0x3C..0x41` cases call `FUN_00235510` when the completion argument is
nonzero, then continue to the contact test; they do not return from the
handoff. The switch uses the substate captured at function entry
(`0x0023388C`), while those later tests read current fighter fields.
**Bounded observation:** when both tests are admitted, the contact transition
can replace a just-entered downed state in the same dispatch. For `0x40`,
`0x00233EE8` calls the handoff and `0x00233F04` subsequently reloads the
cursor. That handoff has reset it to zero, so the external-mode-zero branch
can choose `0x46` even if the pre-handoff cursor was at least `4`.
This is instruction ordering, not proof that every completion/contact
combination is reachable with the retail descriptors and stage geometry.

This proves staged launch/contact reactions and explains why `0x42..0x49`
are not direct attack-byte selections. Suppressing the `0x48/0x49`
replacement does not suppress every contact impulse: the `0x40 -> 0x45`
branch still writes `-0.5 * +0x9B0`, and `0x40 -> 0x46` uses its own
positive table impulse. Neither branch tests `0x00080000`. The former is
not an unconditional half-speed bounce: `FUN_00217E40` first calls action
exit `FUN_00217BD0`, whose major-`5` branch calls `FUN_00230A70`. That
cleanup zeros `+0x9B0` and movement mode `+0x988` whenever `+0xB00 == 0`,
including a transition within major `5`. The later expression then reads
zero on that ordinary path. With nonzero `+0xB00`, this cleanup preserves
the field. Visual identities of the stages remain unassigned.

#### Dispatch precedence at contact

The first-grounded binding-2 entry runs **before** automatic contact proposal
`FUN_002310F0`. Its call to `FUN_0022AF10` at `0x00233B68` jumps directly
to the dispatcher return; the proposal call follows at `0x00233B84`.
Thus a successful first-grounded input entry takes precedence over an
otherwise eligible `0x49` ground proposal. It does not consult either
contact-record bit `0x00080000/0x00100000`. Conversely, effect IDs `0/1`
can block that input entry without blocking the later automatic proposal.
The exact two call/return branches are corroborated by bytes
`0x00233B54..0x00233BD4`.

A successful proposal also returns immediately, before the captured-substate
switch and the later five-sample recovery query. If neither early entry
returns, that later query sees the state and cursor left by the switch,
rather than a saved launch state. A completed downed handoff therefore fails
its required major `5`; a staged contact entry restarts the cursor; and the
final environment fallback can still replace a successful late recovery
entry because it follows it without an early return. The first-grounded
entry's immediate return avoids that final fallback on this invocation.

There is an additional earlier exit for `0x3C..0x3E` with contact byte
`+0x63` bit `6`: the dispatcher copies the position, passes the copy to
`FUN_0021C9A0(fighter,copy,0x10,0)`, and compares the absolute change in
component `+0x30` with `500.0`. When it is greater, it brings planar
response speed toward zero and returns before either input recovery,
automatic proposal, or the state switch (`0x002338D4..0x002339DC`).
The absolute operation is the sign-bit clear in `FUN_0016E6F0` between
float/double conversion helpers. Stage correction details remain owned by
[Movement and physics](../stages/movement_and_physics.md); this is a bounded dispatch
gate, without a player-facing collision name.

The top-level `FUN_00233870` gate separately bypasses all of its ordinary
response handling for an initial substate in `0x3C..0x41` whenever
`fighter[+0xB00] & 0x1500` is nonzero. This is a whole-dispatch suppression for
that update, not merely an input-recovery restriction.

After the state switch and later input-recovery test, the dispatcher has one
more raw fallback. It skips the check only when the fighter is currently
`(5,0x45)` or `(5,0x5A)`. Otherwise it forces `(5,0x5A)` with transition
argument `1` when all of the following are true:

```text
fighter[+0xBA4] is the exact sentinel -17320.508
    or fighter[+0xBA4] >= fighter[+0xE4] * fighter[+0x2F0]
not ((fighter[+0x68] == 0x40 or 0x3B) and fighter byte +0x63 bit 5 is set)
fighter signed halfword +0xB8C is in 0x1E..0x22 inclusive
```

Because the major/substate exclusion is read after the switch, the code does
not require the fighter still to be in major state `5`; the fallback can
replace a transition just taken earlier in the same dispatch. `+0xB8C` is the
animation selector maintained by `FUN_00218190`; values `0x1E..0x22`
select `fxk2`, `col0`, `col1`, `col2`, and `kno0`, respectively, as decoded
above. The `+0xBA4` boundary's geometry meaning remains unassigned, so this
is an environment-dependent response fallback rather than a named collision
event.

### Input-driven recovery actions during ordinary response

The same ordinary-response dispatcher has two binding-2 recovery paths before
the timed-down handoff. Both consume logical input bit `0x00010000`, already
established as newly pressed binding 2 (default Cross), but they have different
windows and native destinations. These input actions, the automatic contact
impulses above, the timed downed choices below, and the paired Extra Hit
counter are separate native paths. Static identifiers `ACT_RCV_0/1` do not
establish which player-facing use of the word *rebound* denotes either action.
The receiver-owned effect query and source-owned contact-record flags below
are distinct mechanisms; an effect on the attacker alone does not satisfy the
receiver's query.

The earlier path is available in substates
`0x36..0x39`, `0x3C/0x3D`, `0x3F..0x41`, and `0x48/0x49`. It requires primary
cursor `+0x1C4 >= 2`, position component `+0x38 > -500.0`, a retained attack
pointer other than the dummy-drop record when that pointer is non-null,
`FUN_00306A60(fighter) != 1`, the fighter's grounded bit set, and contact
history count `+0xB9A == 1`. The exact instructions at
`0x00233B18..0x00233B34` reject a clear grounded bit and any grounded-update
count other than `1`; this is the first grounded update, not an airborne
recovery window. For the eligible `0x3C/0x3D` and `0x3F..0x41`
states, the top-level fighter `(+0xB00 & 0x1500)` must also be zero. When input
is present, the dispatcher calls `FUN_0022AF10(1.0,1.0,fighter,1)`, which forces
`(0,0x0A)`, clears the action-lock block, and clears the secondary block when
its pending flag is clear. The clean descriptor names this state `ACT_RCV_1`.

The later path can run only if the earlier path did not return and the fighter
is still in ordinary major state `5`. Its shared gates are:

```text
substate is 0x38/0x39, 0x3C/0x3D, 0x3F, or 0x48/0x49
external mode == 0
fighter[+0x20C] < 1
fighter[+0xB00] == 0
FUN_00306A60(fighter) != 1
retained source +0x7C8 and attack record +0x7CC are both non-null
input +0x338 has 0x00010000
FUN_00217260(fighter,0x00010000,5,0) == 0
```

It then requires the primary cursor to lie inside one of these inclusive
windows:

| Current substate | Additional raw conditions | Inclusive `+0x1C4` window |
| --- | --- | --- |
| `0x38/0x39`, `0x48/0x49` | none | `4..6` |
| `0x3C/0x3D` | unless source `+0x0C == 0` and attack `+0x10 & 0x200` is set | `4..8` |
| `0x3C/0x3D` | source `+0x0C == 0` and attack `+0x10 & 0x200` set; random `r` in `0..3` | `r+4 .. r+6` |
| `0x3F` | source `+0x0C == 0`, attack `+0x14 & 0x2` set, and vertical speed `+0x998 >= 0`; random `r` in `0..2` | `r+3 .. r+5` |

`FUN_0022A890` samples the random value on each invocation of the applicable
branch, before testing current input; it does not store a window chosen at
action entry. These randomized windows are therefore per-query conditions.

The history check counts matching samples in a 32-slot ring at
`fighter +0x344 + index*0x0C`, starting at index `+0x4C4` and walking backward.
With count `5` and offset `0`, it rejects a matching press in any of the
previous five stored samples. The current `+0x338` press is checked separately:
`FUN_0024DE40` appends `+0x338/+0x33C/+0x340` only later in the fighter update,
after `FUN_0024D5E0`. That append is outside the `+0x20C` pause guard, although
the action-timeline advance is guarded, so eligible late passes can advance
input history while the action cursor is paused. Forced contact state entry
restarts the cursor without clearing this ring in the state setter. The
separate initializer `FUN_002171C0` clears all 32 samples, current input, and
the ring index. Five stored samples therefore need not mean five advancing
action-cursor updates.

A successful later path forces `(0,0x09)` and clears the complete action-lock
block. Its clean native identifier is `ACT_RCV_0`. Descriptor `ACT_RCV_0` has
sequence `D, T`; on completion it enters `(4,0x26)` if grounded and
`(3,0x24)` otherwise. `ACT_RCV_1` has sequence `E, E, G, E, T`, with a
`2.0` secondary rate in phase `0` and `1.0` thereafter; on completion it
enters neutral if grounded and `(3,0x1E)` otherwise. While airborne with
`+0xB00 == 0`, `ACT_RCV_1` can also enter `(3,0x1E)` as soon as vertical speed
becomes negative. These are exact native recovery transitions, but the static
evidence does not establish their player-facing move names.

Both paths test the recovering fighter's own effect list.
`FUN_00306A60` scans fighter `+0x8C8`, bounded by count `+0x8C4`, for node
effect ID `+0x68` equal to `0` or `1`. It returns `1` on either membership
match and otherwise `0`; it does not inspect the node's countdown `+0x6C`.
A zero-countdown node awaiting removal therefore still suppresses these
input recoveries. The automatic contact replacement to `0x48/0x49` does not
call this predicate. Effects applied only to the attacking fighter do not
make this query true on the struck fighter: the pointer passed here is the
receiver itself. Definition flags for IDs `0/1` are local `0x02`, so even
route argument `1` in `FUN_00305C30` installs them only on its supplied
fighter; they do not automatically traverse opponent pointer `+0x20`.
Effect-list ownership and removal are described in
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#update-expiry-and-removal).

A bounded overlay application confirms why the supplied fighter matters.
At preserved BTL entry `0x00739130` (live `0x00739170`, file `0x00085270`),
object byte `+0x8A == 0/1` selects manager fighter pointer `+0xDE4/+0xDE8`;
other values select no fighter. Its effect-ID `1` application uses that
selected fighter, with no opponent-pointer traversal in this path. The
object-to-effect mapping and requested countdown belong to
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#other-direct-numeric-mappings).
The object identifier's player-facing name remains unassigned; this is one
application example, not an inventory of every producer of IDs `0/1`.

This effect membership is broader than recovery suppression. At the end of
ordinary selection `FUN_00231C60`, an airborne receiver with either ID
retains the selected response only for `0x36..0x49`, `0x51..0x58`, or
`0x5A`; other provisional results become `0x37`. A grounded receiver is
not remapped by that final effect check. The [Extra Hit](extra_hit.md) candidate query
`FUN_0023A0D0` and candidate helper `FUN_0021DDB0` also consume the same
membership predicate. Thus it is not evidence for a recovery-only status.

Release is tied to effect removal. Before entering `(6,0x5D)`,
`FUN_00235510` requests removal of both IDs through `FUN_00306B00(fighter,1)`
when either is present; recovery initialization `FUN_00235100` does the same
for `0x61/0x62`. The request uses normal reason-`1` removal, so a locked
countdown `-2` is protected. Ordinary finite nodes can also expire through
the maintained effect countdown pass; removal makes the membership query
false once neither ID remains. Countdown normalization, decrement gates,
input-accelerated expiry, and hard cleanup belong to the linked effect
document. No separate recovery-suppression reset bit was established.

The two recovery actions have different motion producers.
`FUN_0022AB80` supplies `ACT_RCV_0` at initial primary event `0`: with
`g = 3 * fighter[+0xF8]`, vertical speed is `sqrt(2*g*250) - g/2`; planar
speed approaches fighter parameter `+0x100`, then damps toward zero.
It also clears the secondary rejection block when no activation is pending.
`FUN_0022B160` supplies `ACT_RCV_1` at secondary event `0` of phase `1`:
vertical speed is `sqrt(2 * (+0x9AC) * (+0xF8) * 180 * g) - g/2`, and
planar speed approaches `40 * +0x9A8`. Both transient scales are reset to
`1.0` after use. Its phase-`1` planar damping grows with secondary cursor;
later phases use grounded or airborne damping parameters. These impulses
and the existing descriptors establish upward recovery motion without
requiring either action to be the automatic contact rebound.

Both successful player-input entries increment the same receiver statistic
pair `+0x520/+0x522` (count/max, capped at `9999`) when byte `+0x62` bit `0`
is clear. They do not decrement a separate rebound resource in these paths.
Direct entry is nevertheless possible without the ordinary eligibility
checks: effect `0x7D` calls `FUN_0022AAB0` to enter `ACT_RCV_0` after its
cursor-`60` conditions, while `FUN_0023F170` can enter `ACT_RCV_1` on the
grounded completion of an attack with `+0x10 & 0x200` and
`+0x14 & 0x04000000`. Its fourth argument is `0`, so that automatic
`ACT_RCV_1` entry does not increment the player-input statistic.
Character-local callbacks `FUN_00287F50` and `FUN_0026FAA0` also use that
entry with argument `0`, scales `0.25/0.5`, in action `0x29`, phase `1`,
after secondary cursor `6`. The shared entry routines do not recheck
effect IDs `0/1`; blocking the two ordinary input predicates therefore
does not establish a block on every possible entry to these actions.

`BTL.BIN` contains no encoded direct JAL to `FUN_0022AAB0`, `FUN_0022AF10`,
`FUN_0022A890`, or `FUN_00306A60`. This does not exclude indirect calls,
inline state writes, or other recovery entrypoints.

#### Retained recovery-source lifetime

The later input path's non-null `+0x7C8/+0x7CC` requirement is a retained
source/record condition, not a fresh-hit marker or decrementing recovery
cooldown. Fighter initialization `FUN_00214A40` clears both pointers and
byte `+0x830` at `0x00214EA4..0x00214EAC`. Ordinary response initialization
`FUN_00232B80` writes them at `0x002330E0..0x002330E8` only when the source
is non-null, source halfword `+0x02 == 0x474F`, receiver byte `+0x62` bit
`0` is clear, and `FUN_00216820(receiver) == 0`. A failed source gate leaves
the earlier values intact rather than clearing them.

Whether `+0x7C8` retains the source itself or a copied source prefix at
`+0x7D0`, and the limits of that copy, are owned by
[Target selection](target_selection.md#copied-provenance-and-pointer-lifetime-limits).
The record at `+0x7CC` remains the supplied record pointer, and byte
`+0x830` saves the receiver's grounded bit at the write. These fields are
separate from accepted-hit source/record `+0xE58/+0xE54`, which the
automatic contact proposal uses.

The guarded initializer `FUN_00228760` uses the same source gates, with an
additional requirement that attack `+0x10 & 0x00F00000` is clear. Paired
response `FUN_00221120` can write each fighter's recovery source/record
independently after entering `0x5B/0x5C`. The source-retaining wrapper
`FUN_002333A0` also writes them without creating an ordinary response, as
described in the [accepted-hit routing trace](#accepted-hit-routing).
The common ordinary exit `FUN_00230A70`, downed exit `FUN_00235200`, and
the inspected `ACT_RCV_0/1` entry and motion bodies do not clear either
pointer. Leaving those states therefore does not itself expire this pair.

Two inspected branches replace the pair with a self-source and the resident
`PL_ATK_DUMMY` record at `0x00407C00`. Fighter maintenance `FUN_0024C440`
does so under its own gates, as described in
[Target selection](target_selection.md#copied-provenance-and-pointer-lifetime-limits).
Downed motion `FUN_00235C60` (stores `0x00236320..0x00236328`) installs the
same self/dummy pair and clears `+0x830` in substate `0x61` at primary event
`0`, after its preceding helper calls and under the usual signature,
byte-`+0x62`, and `FUN_00216820` gates.

These are conditional overwrites, not a proof that every recovery exit clears
the original source on the following update. `FUN_00216820` reads a word
through the global context pointer; this trace does not assign that word a
mode name. The initialization, shared response, maintenance, and recovery
bodies above were inspected from resident immediate `+0x7C8` matches; other
character/effect paths and pointer aliases were not exhaustively audited. No
universal lifetime or expiry rule for `+0x7C8/+0x7CC` is established.

## Timed downed recovery and get-up choices

`FUN_00235510(scale,fighter)` is the common handoff from the response groups
above. It enters `(6,0x5D)`. When fighter byte `+0x61` bit `3` is set, it also
initializes two action-timeline thresholds:

| Profile condition | Automatic threshold `+0xB66` | Earliest input threshold `+0xB68` |
| --- | ---: | ---: |
| fighter byte `+0x62` bit `5` clear | `45` | `8` |
| fighter byte `+0x62` bit `5` set | `90` | `40` |

Both values are multiplied by the handoff scale and then by the temporary
factor returned by `FUN_00306d30` when that factor is below `1.0`. The units are
the same primary action-timeline cursor at `+0x1C4`. Each multiplication is
followed by EE `cvt.w.s` under the active FPU rounding mode and a signed-halfword
store; when the temporary factor applies, that is a second multiply, conversion,
and store. This local path does not set the rounding mode, so static evidence
does not justify describing fractional results as unconditional truncation
toward zero.

The temporary factor cannot apply on the resident path. `FUN_00306D30` adds
the `+0x7C - 1.0` contributions of the fighter's active effect list at
`+0x8C8` (count `+0x8C4`), caps the sum at `1.25`, and then forces exactly
`1.0` whenever the fighter is in major state `5` or `6` (and in some other
conditions). All resident calls to `FUN_00235510` are in the ordinary-response
dispatcher `FUN_00233870`, before the handoff itself enters major `6`, so the
factor is `1.0` there.

All five direct overlay callsites call the handoff with scale `1.0`, then
overwrite both thresholds, so the profile and
temporary-factor products above are not their final thresholds:

| Preserved BTL callsite | Live callsite | BTL file | Target and final thresholds |
| --- | --- | --- | --- |
| `0x0078AE58` | `0x0078AE98` | `0x000D6F98` | Entry preserved `0x0078AE00` uses its second argument's fighter pointer `+0x11C`. Arguments 3/4 become `+0xB66/+0xB68`; each negative argument independently becomes `45`. |
| `0x007C2D2C` | `0x007C2D6C` | `0x0010EE6C` | Entry preserved `0x007C2CD0` uses owner pointer `+0x4CC`; both thresholds become `45`. |
| `0x007C4730` | `0x007C4770` | `0x00110870` | Entry preserved `0x007C46B0` uses owner pointer `+0x4CC`; both thresholds become `45`. |
| `0x007CDA7C` | `0x007CDABC` | `0x00119BBC` | Entry preserved `0x007CD990` first requires owner word `+0x2C8 == 1`, then uses owner pointer `+0x4CC`; both thresholds become `45`. |
| `0x007D4EAC` | `0x007D4EEC` | `0x00120FEC` | Entry preserved `0x007D4E50` uses owner pointer `+0x4CC`; both thresholds become `45`. |

Each local handoff is gated by resident `0x003083A0`, whose clean bytes
return true exactly when the target pointer and global `gp-0x339C` are both
nonzero. This predicate does not inspect the target's action or profile.
After the threshold stores, all five call live `0x0071F640` and resident
`FUN_0024D1C0` immediately to select/advance animation. They query the same
predicate again and, if true, clear target planar/vertical response speeds
`+0x994/+0x998`. The local evidence therefore establishes explicit downed
setup and timing overrides, while the owner classes and player-facing
sequences that reach these entries remain unidentified. These entries do not
set the timed-branch enable bit `+0x61` bit `3`; a final threshold of `45`
does not by itself prove an enabled automatic/input exit.

The same neutralization makes `+0x1AC` exactly `1.0` in every update whose
maintenance pass starts in major `5` or `6`, unless fighter `+0x1B0` or `+0x1B4` differs from `1.0`
(`FUN_0024C440` uses `+0x1B0` when it is not `1.0`, otherwise the factor, and
then multiplies by `+0x1B4` when that is not `1.0`). The state setter zeros the
cursor on entry and the same update's timeline pass advances it, so the
threshold tests in update `k` after entry see cursor `k`. At nominal speed
and rate `1.0`, the default profile therefore auto-recovers in update `45`
(1.5 s at 30 Hz) and accepts recovery input from update `9` (the test is a
strict `>`), and the `+0x62` bit-`5` profile uses updates `90` (3.0 s) and
`41`. The `0x3A/0x3B` scale shortens both proportionally.

The independent multiplier `+0x1B4` is not neutralized by major state `5/6`.
Fighter initialization `FUN_00214A40` sets it to `1.0`. Another resident
writer, `FUN_00247310`, increments counter `+0xB14` and, when paired byte
`+0xB17 <=` the fighter's byte, sets both `+0x1B0/+0x1B4` to `0.5` at
counter `30`, then restores both to `1.0` above `30`. Cleanup
`FUN_00246D10` restores the local pair in its argument-`1` branch and common
other-argument branch, and conditionally restores the paired fighter's values
in that latter branch. Its argument-`2` branch does not perform these writes.
These are additional direct rate writers, without assigning a gameplay name
to the surrounding `+0xB10` sequence.

Effect `0x4A` callback `FUN_002C8690` is a further `+0x1B4` writer for both
fighters; its writes, restore branches and destructor belong to
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#specialized-entry-exit-and-callback-behavior).
Its restore branch is taken when owner `+0x330 > 400`,
`FUN_00244110(owner)` is nonzero, owner `+0xB10 == -1`, or
`FUN_002354C0(owner)` is nonzero while owner `+0x310 == 0`. For hit response
it has two consequences: it can replace the paired fighter's substate `0x5D`
with `(6,0x5F)` whenever that fighter's major state is not `8`, bypassing the
ordinary input/threshold choice, and it redirects paired `(6,0x61)` through a
forced dummy-drop ordinary response. These are effect-specific response
exceptions, not changes to the ordinary threshold formula.

If fighter byte `+0x61` bit `3` is clear, `FUN_00235690` returns immediately
from its `0x5D` case. It neither initializes nor consumes the two thresholds on
this path, so no automatic or input-driven `0x5D` exit is proven there. With
the bit set but the fighter airborne, `(fighter[+0xBB8] & 0x00F0F0F0)` values
`0x202020` and `0xE0E000` hold `0x5D`; other values divert back to ordinary
response `(5,0x5A)`. The static evidence does not justify a gameplay name for
that environment-class field. An external global value of `3` separately
forces the automatic `0x5E` branch without waiting for `+0xB66`.

While `(6,0x5D)` is active and the timed branch is enabled,
`FUN_00235690` performs these exact choices:

```text
+0x1C4 >= +0xB66                         -> (6,0x5E)
+0x1C4 >  +0xB68 and input 0x00010000    -> (6,0x5F)
+0x1C4 >  +0xB68 and input 0x00001000    -> (6,0x60)
```

The automatic and binding-2 branches form an `if/else if`, followed by a
separate binding-1 test. The latter rereads the current primary cursor at
`0x00235850`, after the possible state-setter calls at
`0x00235804/0x00235848`. Changing `0x5D` to `0x5E/0x5F` resets that cursor
to zero through `FUN_00217E40` (`0x00217F50..0x00217F78`); recovery entry
`FUN_00235100` and exit `FUN_00235200` do not change `+0xB68` here.
Consequently, with a nonnegative input threshold, the final strict
`+0x1C4 > +0xB68` test fails after either earlier choice. At the default
thresholds, both input bits therefore choose `0x5F` before the automatic
threshold, and the automatic branch chooses `0x5E` once it is reached.
Binding 1 chooses `0x60` only when neither earlier branch changed the state.
The instruction bytes at `0x002357E0..0x00235890` corroborate the calls and
the fresh cursor load; syntactic order alone does not establish last-input
priority. A negative externally supplied threshold would require evaluating
the final test separately; no such default profile is established here.

At the first primary-timeline event of `0x5D`, `FUN_00235B70` primes secondary
count `+0x230` to `1` only if that countdown channel is inactive, and
unconditionally clears the complete `+0x248` action-lock block, including
`+0x254`. `0x5D` nevertheless remains ineligible for action entry and exits
only through the state-specific branches above. This is direct evidence that
the downed lockout is not an extension of the ordinary `+0x254` lock timer.

On completion, `0x5E` and `0x60` enter neutral `(0,0)`, while `0x5F` enters
`(3,0x20)`. The code therefore proves one automatic recovery and two
input-selected recoveries, one of which continues through a different major
state. The battle input translator independently establishes that
`0x00010000` is newly pressed binding 2 (default Cross) and `0x00001000` is
newly pressed binding 1 (default Circle), then the resident bridge copies those
logical bits directly to fighter `+0x338`. These are default bindings rather
than hard-wired physical-button requirements. Player-facing recovery labels
remain unassigned.

Their entry motion also differs. At its initial timeline event, automatic
branch `0x5E` zeros planar response speed and computes a vertical impulse from
native motion scalar `+0xF8` and constant `125`. Binding-2 branch `0x5F` sets
planar speed to `20` and computes the same form with constant `250`.
Binding-1 branch `0x60` sets facing/orientation fields but no corresponding
explicit response-speed impulse in this updater. These are native numeric
effects, not inferred animation labels.

### Recovery exit rejection counts and suppression boundaries

**Observation:** Major-`6` exit cleanup `FUN_00235200`, called by the
central state setter before installing the destination, also stages short
accepted-hit rejection counts according to the departing recovery substate:

| Departing substate | Staged `+0x230` | Resident store |
| ---: | ---: | --- |
| `0x5E` | `-4` with pending flag `0x0004` | `0x002352D4..0x00235300` |
| `0x5F` | `-3` with that flag | `0x0023533C..0x00235368` |
| `0x60` | `-2` with that flag | `0x002353A4..0x002353D0` |

Each branch is skipped while a secondary activation is already pending.
These counts share the existing `+0x224` channel and its pause-dependent
maintenance; they are not an input-recovery cooldown or a consumed resource.
The cleanup runs for state-setter departures, including an admitted action
or recovery cancel, rather than only animation completion. Entering a new
ordinary response can subsequently overwrite the channel from its attack
record, so these stores alone do not prove that the short interval survives
every interruption. Their router consumers belong to
[Accepted-hit rejection countdown](#accepted-hit-rejection-countdown).

The same cleanup clears repeat/response counter `+0xB6E` at
`0x00235270` except when the destination is exactly ordinary major `5`,
substate `0x3A` or `0x3B`. This explains how that counter can survive a
specific downed-to-response return while normal recovery departures reset
it. It is separate from receiver streak `+0xB64` and the attacker-owned
Lee/Guy bytes.

The complete `0x5D` threshold branch in `FUN_00235690` does not query effect
membership `FUN_00306A60`, contact bits in the source record, or the
five-sample input history. `FUN_00235510` requests removal of IDs `0/1`
before entering `0x5D`, but even if a locked node survives that request,
membership is not an additional condition in these three threshold choices.
This is a local static suppression boundary, not proof of every external
effect or input producer. It keeps timed downed recovery distinct from the
two ordinary-response input predicates that do query those IDs.

The normal input update also exposes a separate recovery cancel before the
per-action recovery dispatcher runs. `FUN_0022B630` accepts logical input bit
`0x00040000` throughout `0x5E` and `0x60`, and during `0x5F` while primary
cursor `+0x1C4 < 3`. It additionally requires all of these raw gates:

```text
fighter[+0x9F6] == fighter[+0x324]
fighter[+0x9F0] == 0
FUN_0022D5B0() == 0
fighter[+0xB00] == 0
```

When the gates and input bit hold, its sole caller invokes `FUN_0022BA30`,
which forces recovery major state `6` to `(0,0x0B)`. The clean descriptor names
that destination `ACT_BST_0`. The battle input translator derives
`0x00040000` from binding-2 input plus directional/condition tests, so no single
physical-button name is assigned here. This cancel does not include `0x5D` and
is distinct from the three threshold choices and normal completion exits.

Substates `0x61/0x62` are a separate recovery/placement route used by the
special `0x4A..0x4E` handoff. In `0x61`, a nonzero external mode or primary
cursor `+0x1C4 > 0x13` triggers the next branch: fighter byte `+0x61` bit `3`
set enters `0x62`, while that bit clear routes back through an ordinary
dummy-record response instead. In `0x62`, the resident updater performs its
placement event at cursor `0x1E`. It may return to neutral only after
`+0x1C4 > 0x1E` and when at least one of fighter halfwords `+0x308` or
`+0x318` is zero. These substates must not be folded into the timed `0x5D`
profile. In the bit-clear `0x61` branch and the `0x62` placement event,
`FUN_00235690` calls live BTL `0x007090B0` with the fighter's side bit and
position/orientation destinations `+0x30/+0x40`, storing the returned section
in `+0x9F6`. Case `0x62` additionally projects the position through live
`0x007090D0`. The placement helper uses the stage's `DMY_pp1_010` or
`DMY_pp2_010` position and side-specific orientation. The authored node
positions and exact helper behavior belong to
[Stages](../stages/stages.md#resident-generic-factories-and-mandatory-records); this establishes a
recovery-placement consumer, not a fixed elapsed ground-contact time.

## Guarded-hit transitions

Guard stance `(0,5)` entry and the guard temporal state `+0x95A` and
input-age field `+0x95C` consumed by the hit router follow the guard input
lifecycle owned by
[Chakra and guard](chakra_and_guard.md#guard-input-and-action-lifecycle).

`FUN_00228760` reads signed attack-record byte `+0x2D`, remaps values `0..4`
to `5..9` when the defender is airborne (grounded bit clear), and stores the
result at fighter `+0x95E`. A grounded defender keeps the authored index.
It then chooses:

- grounded reactions with adjusted indices `5..9`: `(0,7)`;
- other grounded adjusted indices: `(0,6)`; and
- non-grounded reactions: `(0,7)`.

Both reactions are forced state changes. Their per-update descriptors are the
`0x1C`-byte table at resident runtime `0x00407550`, ELF file offset
`0x00307650`, indexed by `+0x95E`. The action updater routes both `(0,6)` and
`(0,7)` through the same table engine used by ordinary response motion.

The same native descriptor table used by ordinary responses names guard stance
`(0,5)` as `ACT_GDN_0`, grounded guarded reaction `(0,6)` as `ACT_GDN_1`, and
the `(0,7)` reaction as `ACT_GDA_1`. Each descriptor begins with an
animation-end (`-0x10`) phase and then a condition-`0` phase. The common phase
updater therefore advances into, but cannot leave, that held second phase;
`FUN_00228E90` owns the exits described below. The identifiers are recorded
verbatim and are not expanded into unverified terms.

Decoded as in
[Animations and animation-gated phase lengths](#animations-and-animation-gated-phase-lengths),
the phases animate per-character `nxg0` then held `gdn0` for `(0,5)`,
`ght0` (7..11 frames, median 7) then held `gdn0` for `(0,6)`, and `gha0`
(6..9 frames, median 7) then held `dow0` for `(0,7)`. These resource names
and frame-count ranges were checked across all 74 primary records. The first phase's clean
rates (`256` and `192`) are replaced at run time by the guarded-row rate
described below.

The exact clean table rows are:

| Index | Planar `+0x04` | Vertical `+0x08` | Damping `+0x0C` | Pause `+0x14` | Secondary `+0x16` | Action lock `+0x18` | Phase rate `+0x1A` |
| ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `0` | `30` | `0` | `0.35` | `1` | `2` | `8` | `176` |
| `1` | `30` | `0` | `0.35` | `1` | `2` | `8` | `160` |
| `2` | `35` | `0` | `0.35` | `1` | `2` | `8` | `144` |
| `3` | `40` | `0` | `0.35` | `1` | `3` | `12` | `128` |
| `4` | `40` | `0` | `0.125` | `0` | `3` | `24` | `128` |
| `5` | `20` | `15` | `0.25` | `1` | `2` | `8` | `192` |
| `6` | `25` | `20` | `0.25` | `1` | `2` | `8` | `176` |
| `7` | `30` | `20` | `0.25` | `1` | `2` | `8` | `160` |
| `8` | `40` | `20` | `0.35` | `1` | `2` | `12` | `128` |
| `9` | `40` | `30` | `0.125` | `1` | `2` | `24` | `64` |

Every row also has flags `0x0101`, event gate `0`, and auxiliary multiplier
`1.0`. Guarded-hit initialization sends `+0x16` to secondary count `+0x230`
unless attack `+0x32` already staged a value there (see
[Accepted-hit rejection countdown](#accepted-hit-rejection-countdown)), and
raises action lock `+0x254` to at least `+0x18`. Field `+0x1A` is written
into halfword `+0x06` of the current phase record, the rate field that
[phase control](#descriptor-phase-control) loads into `+0xB90`. The authored
values `64..192` therefore set the guarded reaction's animation and secondary
timeline rate to `0.25..0.75`, decreasing with the row index within the
grounded rows `0..4` and the airborne rows `5..9`. The write modifies the
shared overlay descriptor data rather than a per-fighter field.

The positive `+0x16` values are staged as negative pending counts and become
positive on countdown maintenance. The positive `+0x18` action lock is written
directly without a pending activation. Maintenance can activate the secondary
count while a pause is active, but it does not decrement `+0x254` until
`+0x20C` has cleared.

Guard field `+0x14` is specifically an attack-pause fallback. The initializer
first processes signed attack halfword `+0x30` in guard mode. Finite nonzero
values provide their absolute count, but retain a sign-dependent activation
edge: authored positive `N` is written immediately as positive `N`, while
authored negative `-N` is staged as negative `-N` with pending flag `0x0004`.
Thus the positive-authored form is eligible to decrement on the first following
maintenance pass, whereas the negative-authored form activates without a
decrement on that pass. Zero explicitly clears the pause block. Only sentinel
`0x7FFF` reports the attack pause as unhandled and causes the selected guard
row's `+0x14` to initialize `+0x20C`; a positive fallback value is also written
directly without the pending flag. Attack flag
`+0x14 & 0x00020000` instead reports the pause as handled without changing the
block, so it also suppresses the table fallback. This arbitration prevents the
guard table's Pause column from being misread as an unconditional duration.

`FUN_00228e90` owns the return from guard stance and guarded response:

| `+0x254` | Guard input `0x10000000` | Grounded | Next state |
| ---: | --- | --- | --- |
| `0` | released | yes | neutral `(0,0)` |
| `0` | released | no | `(3,0x21)` |
| `0` | held | yes | guard stance `(0,5)` and phase `1` |
| `0` | held | no | `(3,0x21)` |
| nonzero | either | yes | guarded response `(0,6)` and phase/cursor `1` |
| nonzero | either | no | guarded response `(0,7)` and phase/cursor `1` |

The state updater reaches that exit matrix through different gates:

- guard stance `(0,5)` calls it when guard temporal state `+0x95A` reaches
  zero;
- guarded response `(0,7)` calls it directly while grounded; and
- guarded response `(0,6)` calls it at phase `1` after the secondary action
  timeline at `+0x1E8` is positive and the `+0x254` countdown block crosses
  zero, or under the same phase/timeline condition if the fighter is airborne.

Those gates explain why a nonzero `+0x254` can re-enter the appropriate guarded
response with phase/cursor `1` rather than exit immediately.

The action-exit dispatcher sends guard stance `(0,5)` to cleanup
`FUN_00228130` and both guarded reactions to `FUN_00228550`. Thus guard
reaction is a short action-state lifecycle governed by the same general timer
channel, not merely a branch that leaves the fighter in guard stance.

## Conditional rehit suppression and target-eligibility limits

A direct trace into the accepted-hit router establishes two rehit gates: the
state-window predicate described here and the time-based
[`+0x230` countdown](#accepted-hit-rejection-countdown). Neither is a
hurtbox-level invulnerability or global untargetability timer.
`FUN_002409e0` calls `FUN_002406b0(fighter)`. It sets result bit `0x10` only
when that predicate returns zero. At the top of `FUN_002209a0`, an otherwise
accepted hit returns without entering a new response when either:

```text
(result & 0x0F) == 0, (result & 0x10) == 0, (result & 0x20) != 0
(result & 0x0F) != 0, (result & 0x10) == 0
```

Consequently, `FUN_002406b0 == 1` marks response windows that suppress most
ordinary rehits. Other attack/repeat-result bits can still let a hit proceed,
so this is a conditional accepted-hit gate, not proof of absolute invulnerability.
The predicate returns one in these exact state-dependent windows:

| Response window | Additional condition |
| --- | --- |
| substate `0x5D` | always |
| `0x40`, `0x41`, `0x45`, `0x46`, `0x47` | grounded and action cursor `+0x1C4 > 3` |
| `0x3A`, `0x3B` | secondary count `+0x230 <= 0` |
| `0x36..0x39`, `0x3C`, `0x3D`, `0x3F`, `0x42..0x44`, `0x52`, `0x54`, `0x56`, `0x58`, `0x5A` | grounded after the current action has included airborne motion: entered airborne (`+0xB9C & 0x0F == 2`), or entered grounded and later left ground (`+0xB9C & 0x0F == 1` and flag `0x20`) |
| `0x48`, `0x49` | the preceding ground-after-air condition with more than four consecutive grounded updates (`+0xB9A > 4`), or phase `+0x192 == 2` |
| `0x3E` | phase `+0x192 == 2` |

When `FUN_002406b0 == 1`, the router can proceed only if the result's low
nibble and bit `0x20` are both clear. The low nibble is clear only for a
non-null incoming attack record satisfying either of these raw flag forms:

```text
attack[+0x14] & 0x00200000
(attack[+0x14] & 0x00000011) == 0x00000011
    and (attack[+0x10] & 0x00F00000) == 0
```

Bit `0x20` remains clear only while fighter `+0xB6E < 3` and either the incoming
record differs from retained record `+0xE54`, or it is the same record and its
signed `+0x2E` equals the expected repeat count. That expected count is positive
`+0xE5C` (otherwise zero) when `+0xB00 == 0`, and `1` when `+0xB00 != 0`.
These conditions describe the bypass exactly without assigning speculative
names to the attack flags or `+0xB00`.

The clean primary tables show how rare the attack-side exception is. Only 13
records carry `+0x14 & 0x00200000`, and 152 satisfy the `0x11` form (150 of
them damaging); together 158 records (156 damaging, about 6% of 2,484) in 72
of the 74 tables. All other damaging records cannot bypass the protected
windows above. Related guard flags are also sparse: `+0x14 & 0x00800000`
occurs on 109 damaging records, while `+0x14 & 0x00400000` occurs on none.

The action-state setter writes the initial `+0xB9C` low nibble, while the main
movement update maintains `+0xB9A` and latches the two transition flags. The
contact-history interpretation above is therefore direct static behavior, not
an animation-name inference. Substate `0x5D` is notable because its
rehit-suppression predicate is unconditional throughout the traced timed-down
state, even though its recovery thresholds and input choices remain separate.

Four tempting resident predicate groups were checked and rejected as proof:

- `FUN_002167a0` returns false for fighter byte `+0x61` bit `7`, all major
  state `6`, ordinary substates `0x42..0x49`, and nonzero `+0xB00`. Its
  traced BTL callers, including the field-pickup side selector in
  [Target selection](target_selection.md#admission-gate-and-selector-body),
  use the result to choose or suppress a participant; they do not establish
  an attack-acceptance gate.
- `FUN_002166a0` and `FUN_00216720` reject recovery substates `0x61/0x62` plus
  unrelated flags. A traced BTL caller uses that result in a visual-state path,
  again not enough to name combat invulnerability.
- `FUN_00230f20` and `FUN_00230ff0` classify broad sets of ordinary response
  substates for interaction and motion handling. Membership is not itself an
  untargetability window.
- `FUN_0022b630` explicitly recognizes recovery `0x5E/0x60` and early `0x5F`,
  but its only resident caller passes the mutable logical-input word and uses a
  nonzero result to enter `ACT_BST_0`. It establishes the recovery cancel above,
  not an accepted-hit or target-selection gate.

Accordingly, the confirmed target-eligibility claim remains bounded: the direct
accepted-hit path proves conditional suppression for the states above, while
the rejected predicates only show that some non-combat consumers also treat
downed/contact substates as ineligible. These bounded target predicates do not
distinguish hurtbox absence, collision filtering, and higher-level target
exclusion for every response state.

### Accepted-hit rejection countdown

Countdown `+0x230` is a second, time-based rehit gate. `FUN_002247A0` is
exactly `fighter[+0x230] > 0`, and `FUN_002209A0` returns without a response
in router mode `0` (the paired fighter as source), mode `2`, and mode `3`
whenever it is true. Mode `1` does not test it. The pair hit resolver
`FUN_0021ED70` also uses it before routing, and `FUN_00220690` uses it to
withhold the attacker's pause while the defender is protected.

The pair resolver's pre-response use is as follows. For a pending
attacker-side hit bit `+0xE3C & 0x100`, it calls
`FUN_0021F610(attacker)`. After the response classifier admits the attempt,
that helper tests the paired defender's `+0x230` at resident
`0x0021F720` (ELF file `0x0011F820`) and returns `0` immediately while it is
positive. The resolver then clears attacker bit `0x100` and defender bit `1`,
so the later fighter routing pass receives neither the attacker notification
nor the ordinary incoming-hit request. This rejection precedes substitution
checks `FUN_00229130` and any call to the response initializer. The helper's
other admitted results are `1` for ordinary response, `-1` for guarded
response, and `-2` for substitution; result `-2` also clears those hit bits.
The classifier's exact-zero result bypasses the countdown test and returns
ordinary marker `1`, so the pre-response countdown gate is conditional rather
than unconditional. Separately, simultaneous incoming/outgoing hits reach
`FUN_00221120` only when neither fighter has a positive countdown. That helper
enters both fighters into ordinary `0x5B` or `0x5C` according to groundedness;
it is a paired response arbitration path, not collision-candidate filtering.

Effect `0x7D`'s callback is
`FUN_00304070`, installed at resident vtable `0x005DA0A0 + 0x10` by
`FUN_00303F60`. For an owner with byte `+0x62` bit `0` clear, no current
attack record, ordinary major state `5`, and `+0xB10 == 0`, it force-clears
`+0x230` when the current phase condition is grounded (`-0x11`), animation end
and grounded (`-0x14`), or animation end or grounded (`-0x13`). The admitted
substates are `0x37..0x39`, `0x3C/0x3D`, `0x3F..0x44`, `0x48/0x49`,
`0x5A`, and `0x5C`. It recognizes the authored phase condition; it does not
require the phase's ground/animation test already to be satisfied. At primary
cursor greater than `60`, the same state branch also clears the countdown and
calls `FUN_0022AAB0` when fighter halfword `+0x60` bits `5..8` are nonzero or
the object at `+0x24` has `+0xAC & 0x10000`. Thus the countdown can end through
an effect callback before its ordinary decrement reaches zero. The effect's
construction and lifetime belong to
[Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#specialized-entry-exit-and-callback-behavior).

The block is decremented at a fixed rate `1.0` only while `+0x20C < 1`, but a
pending value is activated even during a pause. Its writers on the hit path
are:

| Source | Value |
| --- | --- |
| attack `+0x32` through `FUN_00224870`, from both `FUN_00232B80` and guarded `FUN_00228760` | `0` clears (leaving the pending flag set); positive `M` is staged pending; negative `-M` is active immediately as `M`; sentinel `0x7FFF` leaves the block unchanged |
| ordinary event `0` in `FUN_002346B0`, only for attack `+0x32 == 0x7FFF` and no pending value | response row `+0x16`, rate-adjusted as above |
| guarded-response row `+0x16`, written by `FUN_00228B50` after the attack value and only when that left nothing pending | `2` or `3` |
| capped `0x3A/0x3B` repeat | `60`, subject to the conditions above |
| receiver that counters an [Extra Hit](extra_hit.md#receiver-response-and-exchange-limit) | `60`, staged pending |
| downed `0x5D` first event | `1`, when the channel is inactive |
| generic setter `FUN_002247D0(fighter, v, force)` | count `-v`, pending when `v > 0`, skipped while a value is pending unless forced; the router uses it to clear the countdown when `FUN_002409E0` returns `0`, and the [Ultimate Jutsu](../characters/ultimate_jutsu.md) contest start sets both fighters to an active `60` |

With a positive attack pause `N`, a positive `+0x32 == M` activates in update
`1`, holds through the pause, and starts decrementing in update `N+2`, so
mode-`0` hits are discarded in updates `1..N+M` and accepted again from update
`N+M+1`. The row value used by the sentinel follows the same pattern from
update `0`.

The clean tables show how often each form is authored. Of 2,484 damaging
records, `+0x32` is sentinel `0x7FFF` on 1,462, `1` on 761, `2` on 173, `3`
on 33, `4` on 18, zero on 16, negative on 13, and `5..16` on 8. The sentinel
therefore uses the response row: `5` updates for most light and airborne
reactions and `120` for the knockdown and launch rows `0x36..0x39`,
`0x3C..0x47`, and `0x51..0x5A` (the complete row values are in the table
above). An Extra Hit clears the receiver's `+0x224` block when it starts the
exchange, which is consistent with launch rows otherwise refusing mode-`0`
rehits for their row count.

This is a rejection inside the accepted-hit router, not a hurtbox or
collision change; whether the collision owner still records contact during
the countdown belongs to [Collision](collision.md). No hurtbox-disable field
or global untargetability interval was established. `+0x254` is an
action-entry lock and guard-exit input, but it is not consulted by either
rehit gate. Guard substates `5..7` do not match any case in `FUN_002406B0`,
although guarded hits do set `+0x230`.

### Hit count

`FUN_00232B80` increments receiver halfword `+0x538`, saturating at `9999`,
and raises `+0x53A` to the new value when larger. It does so for every
ordinary accepted hit except when the source's `+0x0C` is `4`, the record is
`PL_ATK_DUMMYDROP`, attack `+0x10` bit `0x2` is set, or receiver byte `+0x62`
bit `0` is set. Guarded hits instead increment `+0x53C` (maximum `+0x53E`) in
`FUN_00228B50` under the same `+0x62` exception.

These pairs share the generic event-statistic layout used by
`FUN_00223140(fighter,index,block)`: it selects `fighter +0x4F0` when
`block` is zero, increments the indexed count up to `9999`, and raises its
adjacent maximum under the same byte-`+0x62` gate. It does not change the
fighter's action. The hit-specific meaning of indices `18/19` is established
by the inline writes in the two hit paths above, not by that generic helper.

The reset is indexed rather than a literal store to `+0x538`. Fighter
initialization `FUN_00214A40` calls `FUN_00222F00(fighter,0)`, which uses
the counter block at fighter `+0x4F0`. For each index `0..23`,
`FUN_00223100` clears halfword `block + index*4` and `FUN_00223120` clears
`block + index*4 + 2`. Ordinary count/max `+0x538/+0x53A` are index `18`;
guarded count/max `+0x53C/+0x53E` are index `19`. The helper entries are
resident/file `0x00223100 / 0x00123200` and
`0x00223120 / 0x00123220`.

The initializer then reloads all 24 pairs from a per-side external bank, so
final construction values are copied values, not unconditionally the earlier
zeroes; that bank's save, conditional clearing and reload ordering are owned
by [Awakening](../characters/awakening.md#state-retained-across-the-native-rebuild). The
named resident cross-references to the reset chain lead only through
`FUN_00214A40`, and `BTL.BIN` contains no direct JAL to `FUN_00222F00`,
`FUN_00223100`, or `FUN_00223120`. This establishes construction-time
clearing/copying but no separate in-match reset.

The only traced consumer is condition evaluator `FUN_00223450` (cases `0x1B`
for `+0x538` and `0x19` for `+0x53C`), owned by
[Battle statistics](../session/battle_statistics.md#statistic-derived-conditions).
