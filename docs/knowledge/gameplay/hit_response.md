# Battle hit-response state

This document records the native battle state entered after a hit has already
been accepted. It covers ordinary hit reactions, table-driven displacement,
launch/ground-contact branches, downed recovery, and guarded-hit reactions.
Collision-candidate generation, damage arithmetic, generic effect/status
processing, resource accounting, match outcomes, and non-battle modes are
outside its scope.

The names below describe demonstrated control-flow behavior. They are not
claims about the game's original internal terminology.

## Research coverage

- **Assigned scope:** battle hit-response state after an incoming hit has
already passed acceptance: ordinary reaction selection and timing, planar and
vertical response motion, launch/contact transitions, timed downed recovery and
get-up choices, conditional rehit protection, and guarded-reaction entry and
exit. The investigation was static and bounded rather than globally exhaustive.

- **Exploration depth:** coverage used the exact clean resident `SLPS_258.37` and `PRG/BTL.BIN` artifacts
identified below, together with their maintained C and instruction exports. The
resident trace followed the representative native chain through
`FUN_002209A0`, `FUN_00231C60`, `FUN_00232B80`, `FUN_00233870`,
`FUN_002346B0`, `FUN_00234DA0`, `FUN_00235510`, `FUN_00235690`, the general
timeline/countdown drivers, guard routines `FUN_00228320`, `FUN_00228760`, and
`FUN_00228E90`, and accepted-hit classifiers `FUN_002406B0` and
`FUN_002409E0`. Their directly required helpers and callers were traced far
enough to establish field ownership, ordering, branch thresholds, and exit
consumers; unrelated callers were not exhaustively classified.

The decoded authored-data coverage is exhaustive for these exact clean ranges:

- all 54 `0x18`-byte ordinary motion/timing rows for substates `0x27..0x5C` at
  resident runtime `0x00407670` (ELF file `0x00307770`);
- all 60 native descriptor slots, identifiers, and reachable phase records for
  substates `0x27..0x62` from the overlay descriptor table at live
  `0x0089AEB0` (preserved export `0x0089AE70`, file `0x001E6FB0`); and
- all ten `0x1C`-byte guarded-response rows at resident runtime `0x00407550`
  (ELF file `0x00307650`).

- **Confirmed coverage:** the ordinary/guarded accepted-hit
split; exact native selector mappings and bounded overrides; descriptor phase
conditions and non-default rates; table-driven response impulses and damping;
ordered fighter-update pause and action-entry lock behavior; contact, held, and
downed handoffs; exact timed/input recovery thresholds and exits; guard table
initialization and transition gates; and the direct conditional-rehit predicate
plus attack-record exceptions. Negative-result tracing was sampled and bounded
to the named target/interaction predicates near the end of this document; it
was sufficient to reject several tempting invulnerability interpretations, not
to prove all target-selection behavior.

- **Unresolved or untested:** animation and player-facing move names, seconds
  or display-frame durations, non-default input bindings, character-specific
  callback coverage, attacker-flag exception frequency, and the distinction
  among hurtbox, collision, and higher-level target selection remain
  unresolved.
- **Deliberate exclusions and overlap:** collision-candidate generation, damage and damage
scaling, generic status/effect processing, chakra or guard-resource accounting,
match outcomes, practice-mode mechanics, all other non-battle modes, and
character-specific behavior beyond callbacks reached by the representative
native chain. Those boundaries avoid overlap with collision, combat-arithmetic,
resource, outcome, and mode-specific research.

- **Evidence limitations:** the investigation was static and bounded rather
  than globally exhaustive. No emulator instrumentation, live-memory capture,
  frame stepping, or runtime hit-attempt matrix was performed. The static
  evidence establishes control-flow and authored values, but not those runtime
  observables.

## Evidence identity and address conventions

The static evidence is the clean NA2 v2.28 resident executable and battle
overlay preserved in the maintained read-only disassembly archive:

| Artifact | Bytes | SHA-256 |
| --- | ---: | --- |
| `@source/NA2.iso.files/SLPS_258.37` | 5,273,256 | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |
| `@source/NA2.iso.files/PRG/BTL.BIN` | 2,237,184 | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |

Resident `SLPS_258.37` addresses in this document are EE runtime addresses.
For the mapped resident segment used here, `ELF file = runtime - 0x000FFF00`.

The clean `BTL.BIN` is an MWo3 image loaded with its complete `0x40`-byte
header at live EE `0x006B3F00`. The preserved Ghidra/export baseline omitted
that header, so an overlay-local byte or function has these relationships:

```text
live EE = preserved Ghidra/export + 0x40
file offset = live EE - 0x006B3F00
```

Raw encoded absolute pointers and JAL targets in the overlay are already live
addresses. For example, the direct phase setter is preserved as
`FUN_0071eeb0` at export `0x0071EEB0`, but is live at `0x0071EEF0` and file
offset `0x0006AFF0`. The common phase/event updater is preserved as
`FUN_0071f120` at export `0x0071F120`, but its live entry is `0x0071F160` and
file offset `0x0006B260`. This `+0x40` rule is not applied to any resident
address.

Method: direct inspection of the maintained C and instruction exports, plus
byte decoding of the exact clean binaries for response tables and native action
identifiers. No live-memory capture was used, so frame-visible animation names
and player-facing move labels remain unassigned.

## Selectable extra-hit branch gates

Two previously unconditional edits were traced to their clean resident control
flow before being replaced by runtime selectors:

- In `FUN_0023b280`, runtime `0x0023B5E8` (ELF file `0x0013B6E8`) is
  `beq v0,1,0x0023B60C` with a `nop` delay slot. The `v0 == 1` path runs the
  call block at `0x0023B60C..0x0023B638`; its former disabled edit instead
  branched directly to `0x0023B910`. Other results continue at `0x0023B5F0`.
  A runtime gate can therefore preserve the non-`1` branch and select either
  the call block or its established disabled continuation only for result `1`.
- In `FUN_002455b0`, runtime `0x002457C8` (ELF file `0x001458C8`) is
  `beqz v0,0x002459B4` with a `nop` delay slot. A nonzero predicate normally
  enters the side-effect path at `0x002457D0` and returns `1` through
  `0x002459A8`; the former three-edit disabled form skipped those side effects
  while preserving the zero/nonzero return through `0x002459B4` or
  `0x002459A8`. A runtime gate can make the same choice without changing the
  predicate's return value.

The player-facing names `Extra Hit` and `Shadowblur Extra Hit` come from the
pre-existing canonical patch IDs and descriptions. This static trace
establishes the exact branch and continuation behavior, not those gameplay
names. Runtime gameplay confirmation remains pending.

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
| `+0x230` | `s32` | Current count in a secondary countdown block at `+0x224`; guarded-response table field `+0x16` initializes it, and response substates `0x3A/0x3B` test it for rehit suppression. |
| `+0x254` | `s32` | Current count in the action-lock block at `+0x248`; native action selection refuses actions until it reaches zero. |
| `+0x338` | `u32` | Current logical input bits; guard is `0x10000000`, while downed choices test newly pressed binding 2 (`0x00010000`, default Cross) and binding 1 (`0x00001000`, default Circle). |
| `+0x994` | `f32` | Oriented planar response speed written by the reaction table. |
| `+0x998` | `f32` | Vertical response speed written by the reaction table. |
| `+0x9B4` | `f32` | Auxiliary motion multiplier copied from response-table field `+0x10` when that field differs from `1.0`. |
| `+0x9B8` | flags | Low two bits participate in choosing the grounded-family reaction variant. |
| `+0xA30` | pointer | Current action-descriptor row; for native substates below `0x66`, the state setter indexes the overlay descriptor table directly. |
| `+0xB88` | `u32` | Latest animation-advance completion result. Animation selection clears it; the animation driver rewrites it with the nonzero end result consumed by phase records. |
| `+0xB90` | `u16` | Current secondary-timeline rate loaded from the phase record's fourth halfword and interpreted as a `/256` fixed-point factor. |
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

The router has four source-object modes (`0`, `1`, `2`, and `3`) that converge
on the same ordinary-versus-guarded decision. This document does not assign
gameplay names to those source modes.

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

Additional proven selection behavior prevents treating this as a final
one-to-one enum:

- a guard-invalidated call requests response `0x4F` directly;
- a missing attack record starts from `0x27`;
- a failed contextual query selects `0x3A` or `0x3B` according to source
  object presence;
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
`8` for `0x3B`. The capped-repeat `60` is itself written positive with the
pending flag clear. Consequently, when raw attack `+0x32 == 0x7FFF`, the later
event-`0` path can replace the remaining `60` count with the adjusted `6`/`8`
base. When that sentinel is absent, the direct `60` remains and becomes
eligible to decrement once fighter-update pause has cleared.

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
records. For native actions, the first signed halfword selects an animation
slot, the second signed halfword controls phase advancement, and a first
halfword of `-1` is the terminal record. The third halfword feeds animation
selection state, while the fourth sets the secondary action-timeline rate at
`+0xB90`.

Live overlay `0x0071F160` (preserved export `FUN_0071f120` at
`0x0071F120`) interprets every second-halfword form used by substates
`0x27..0x62` as follows:

| Phase condition | Proven advance condition |
| ---: | --- |
| `-0x10` | Current animation reaches its end (`+0xB88 != 0`). |
| `-0x11` | Fighter is grounded. |
| `-0x12` | Vertical response speed is negative, or the fighter is grounded. |
| `-0x13` | Current animation reaches its end, or the fighter is grounded. |
| `-0x14` | Current animation reaches its end and the fighter is grounded. |
| `0` | No automatic phase advance in this common updater. |
| positive | Secondary cursor `+0x1E8` reaches the authored value. Relevant values are `3`, `4`, and `6`. |

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

The two timeline cursors do not always share one time base. On each unpaused
steady-state call to `FUN_0024D5E0`, `FUN_00211D80` advances the primary block
at `+0x1B8` by fighter scalar `+0x1AC`, so its current integer cursor is
`+0x1C4`. It advances the secondary block at `+0x1DC` by
`+0x1AC * (+0xB90 / 256)`, making `+0x1E8` the current integer cursor. A
newly selected/restarted animation has a separate one-shot reset path, and a
positive `+0x20C` pause suppresses both advances.

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
updater cannot advance condition `0` by itself. Static descriptors establish
the gates and their order, but not their elapsed time without animation data
and runtime update cadence.

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
| `+0x10` | `f32` | Auxiliary multiplier copied to fighter `+0x9B4` when not `1.0`. |
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

The generic blocks have a pending-activation sign convention. Initializers
normally write authored positive value `N` as `-N` and set block flag
`0x0004`. On the next `FUN_0024C440` maintenance pass, that flag causes all
integer and floating count views to be sign-flipped to positive and clears the
flag; no decrement occurs during that activation pass. A live observation made
between initialization and activation can therefore see a negative `+0x20C`
or `+0x230` even though the ensuing active count is positive.

After activation, `FUN_00211E70` implements the decrement phase. It subtracts
the requested rate from the block's fractional accumulator at block offset
`+0x1C`, decrements the integer count at block offset `+0x0C` whenever that
accumulator crosses `-1.0`, and clamps the integer count at zero. This also
explains why a newly staged pause is not shortened on its activation pass.

Ordinary response-table field `+0x14` feeds the `+0x20C` pause channel at its
timeline event, subject to the `+0xB00` event-`0` override above. A positive
table value is staged negative with pending flag `0x0004`; when activated, that
new pause suspends both action timelines and the per-action dispatcher.

Attack-record signed halfword `+0x30` can also feed the pause channel during
accepted-hit initialization. In the ordinary path, an authored positive `N`
is staged as `-N` with the pending flag, while an authored negative `-N` is
written immediately as positive `N` without that flag. Both signs therefore
produce the same absolute active count, but on the first following maintenance
pass the positive-authored form activates without decrement and the
negative-authored form is already eligible to decrement. Zero explicitly
clears the block, while sentinel `0x7FFF` does not initialize it.

`FUN_002346B0` applies the row's `+0x16` action-lock minimum when the primary
timeline crosses event `0`. Because a positive `+0x20C` suppresses the
per-action dispatcher, this event and the lock initialization wait until the
accepted-hit pause has ended. When the table minimum raises `+0x254`, the
absolute attack-record `+0x30` contribution is added unless it is sentinel
`0x7FFF`.
Attack-record `+0x10` bit `0x00000002` instead forces a count of `20`. With
that bit clear, the table minimum is bypassed when either raw attack type mask
`0x00F00000` or `0x000F0000` is nonzero.
The full time before a fighter can act therefore includes
the ordered pause and action-lock counts as well as the response state's own
timeline and exit conditions; `+0x254` alone is not total hitstun.

`FUN_00239e50` makes that last distinction concrete. Once `+0x254` is zero,
ordinary major state `5` still rejects ordinary action entry throughout
`0x27..0x5A`; `0x5B/0x5C` are immediately eligible, while a special selector
value `2` can bypass the ordinary-state rejection. In recovery major state `6`,
`0x5D/0x5E` remain ineligible, `0x5F` becomes eligible at action cursor
`+0x1C4 >= 8`, and `0x60` becomes eligible at cursor `>= 3`. Other recovery
substates are rejected by this predicate. These are action-entry gates, not
animation-completion tests.

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
| `0x3C..0x41` | Completion calls the timed-down handoff; grounded/contact conditions can first redirect to `0x42..0x47`. |
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
to paired-fighter state, not indefinite hitstun or an autonomous timer.

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

Before that per-state switch, `FUN_002310F0` can replace a live launch response
with `0x48` or `0x49`. Fighter byte `+0x63` bit `6` proposes `0x48` from
`0x3C`, `0x3D`, or `0x41`, and from `0x3E` while phase is below `2`; the
grounded bit proposes `0x49` from `0x40/0x41`. The replacement additionally
requires a retained attack record, saved motion scale `+0x9A4 > 0.5`, external
mode zero, and the exact attack-flag gate
`(+0x14 & 0x00080000) == 0`, plus either cursor below the path's ceiling or
`(+0x14 & 0x00100000) != 0`. A nonzero `+0xB00` also requires that latter
attack flag. The cursor ceiling is `5` except that the `0x3E` proposal has no
practical ceiling. These are raw prerequisites, not named collision classes.

If that pre-switch replacement does not occur, the staged transitions are:

| Current | Non-completion transition |
| --- | --- |
| `0x3C` | Airborne plus fighter byte `+0x63` bit `6` set enters `0x42`. |
| `0x3D` | The same condition enters `0x43`. |
| `0x3E` | Fighter byte `+0x63` bit `6` set enters `0x43`, without the additional airborne test. |
| `0x3F` | Fighter byte `+0x64` bit `0` set enters `0x44`. |
| `0x40` | On becoming grounded, enters `0x46` when primary cursor is below `4` and external mode is zero; otherwise enters `0x45`, clears the grounded bit, and writes vertical speed as `-0.5 * +0x9B0` using the saved pre-contact component. |
| `0x41` | On becoming grounded, enters `0x47` and clears the grounded bit. |

This proves staged launch/contact reactions and explains why `0x42..0x49`
are not direct attack-byte selections. It does not prove the visual meaning of
fighter byte `+0x63` bit `6`, byte `+0x64` bit `0`, or each stage, so their raw
forms remain canonical.

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
selector maintained by `FUN_00218190`, but the static trace does not justify
names for its values or for the `+0xBA4` boundary, so this is recorded as an
environment-dependent response fallback rather than a named collision event.

### Input-driven recovery actions during ordinary response

The same ordinary-response dispatcher has two binding-2 recovery paths before
the timed-down handoff. Both consume logical input bit `0x00010000`, already
established as newly pressed binding 2 (default Cross), but they have different
windows and native destinations.

The earlier path is available in substates
`0x36..0x39`, `0x3C/0x3D`, `0x3F..0x41`, and `0x48/0x49`. It requires primary
cursor `+0x1C4 >= 2`, position component `+0x38 > -500.0`, a retained attack
pointer other than the dummy-drop record when that pointer is non-null,
`FUN_00306A60(fighter) != 1`, the fighter's grounded bit clear, and contact
history count `+0xB9A == 1`. For the eligible `0x3C/0x3D` and `0x3F..0x41`
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

A successful later path forces `(0,0x09)` and clears the complete action-lock
block. Its clean native identifier is `ACT_RCV_0`. Descriptor `ACT_RCV_0` has
sequence `D, T`; on completion it enters `(4,0x26)` if grounded and
`(3,0x24)` otherwise. `ACT_RCV_1` has sequence `E, E, G, E, T`, with a
`2.0` secondary rate in phase `0` and `1.0` thereafter; on completion it
enters neutral if grounded and `(3,0x1E)` otherwise. While airborne with
`+0xB00 == 0`, `ACT_RCV_1` can also enter `(3,0x1E)` as soon as vertical speed
becomes negative. These are exact native recovery transitions, but the static
evidence does not establish their player-facing move names.

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
toward zero. No 30/60-FPS calibration was performed, so these values should not
be published as seconds.

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

The two input tests are sequential, not mutually exclusive: if both bits are
present in the same update, the later `0x00001000` test changes the final state
to `0x60`. More precisely, the automatic test and binding-2 test form an
`if/else if`, while the binding-1 test is a separate final `if`. Binding 1 can
therefore also replace an automatic `0x5E` selection made earlier in that same
update whenever its own threshold and input condition hold.

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
than hard-wired physical-button requirements. Animation names remain unassigned.

Their entry motion also differs. At its initial timeline event, automatic
branch `0x5E` zeros planar response speed and computes a vertical impulse from
native motion scalar `+0xF8` and constant `125`. Binding-2 branch `0x5F` sets
planar speed to `20` and computes the same form with constant `250`.
Binding-1 branch `0x60` sets facing/orientation fields but no corresponding
explicit response-speed impulse in this updater. These are native numeric
effects, not inferred animation labels.

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
profile.

## Guarded-hit transitions

The normal fighter input path passes `+0x338` to `FUN_00228320`. When guard
input `0x10000000` is held and the fighter passes its state/lock predicates,
that routine enters guard stance `(0,5)` and increments `+0x95A` up to
`0x7FFF`; release or ineligibility clears `+0x95A`. This establishes the
temporal state consumed by the hit router without treating it as a resource.

The two temporal fields have distinct update rules. When nonnegative,
`+0x95C` increments once per guard-held input update and resets to zero on
release; a negative value instead increments toward zero regardless of current
guard input. Eligible guard-held updates likewise increment `+0x95A`, but with
explicit saturation at `0x7FFF`; release clears it. Ineligibility clears
`+0x95A`, except that the `(0,6)` and `(0,7)` guarded-reaction states bypass
this input-side mutation while active. Thus `+0x95A >= 1` is proven guard
temporal state, while `+0x95C` is a separate guard-input age/window value.

`FUN_00228760` reads signed attack-record byte `+0x2D`, remaps values `0..4`
to `5..9` for the opposite facing, and stores the result at fighter `+0x95E`.
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

The exact clean table rows are:

| Index | Planar `+0x04` | Vertical `+0x08` | Damping `+0x0C` | Pause `+0x14` | Secondary `+0x16` | Action lock `+0x18` | Event value `+0x1A` |
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
and raises action lock `+0x254` to at least `+0x18`. Field `+0x1A` is written
into field `+0x06` of the current animation/event record; its player-facing
meaning is not established.

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

A direct trace into the accepted-hit router establishes conditional rehit
suppression, but not a global invulnerability or untargetability timer.
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

The action-state setter writes the initial `+0xB9C` low nibble, while the main
movement update maintains `+0xB9A` and latches the two transition flags. The
contact-history interpretation above is therefore direct static behavior, not
an animation-name inference. Substate `0x5D` is notable because its
rehit-suppression predicate is unconditional throughout the traced timed-down
state, even though its recovery thresholds and input choices remain separate.

No dedicated post-hit invulnerability counter, hurtbox-disable field, or
global untargetability interval was established. In particular, `+0x254` is an
action-entry lock and guard-exit input, but it is not consulted by the proven
rehit-suppression predicate. Guard substates `5..7` also do not match any case
in `FUN_002406B0` and therefore return zero from that direct protection
predicate. Calling the lock or the guarded-reaction lifecycle an
invulnerability timer would exceed the evidence.

Four tempting resident predicate groups were checked and rejected as proof:

- `FUN_002167a0` returns false for all major state `6`, for ordinary substates
  `0x42..0x49`, and for several unrelated fighter flags. Its traced BTL callers
  use the result to choose or suppress a participant in an overlay-managed
  presentation/selection path; they do not establish an attack-acceptance
  gate.
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
downed/contact substates as ineligible. A runtime hit-attempt matrix would still
be required to measure attacker-flag exceptions and to distinguish hurtbox,
collision, and higher-level target-selection behavior frame by frame.

## Confidence and remaining limits

- **High static confidence:** binary identities; resident/file mappings;
  overlay `+0x40` convention; action fields; ordinary-versus-guarded router;
  authored-byte mapping; response table layout and exact values; response
  transition groups; ordered pause/action-lock countdowns; downed thresholds
  and input masks; guard reaction and exit transitions; conditional rehit gate.
- **Strong inference, explicitly bounded:** major `5` is the ordinary
  hit-response family; major `6`, substate `0x5D`, is a timed downed state; the
  two threshold-triggered paths are get-up/recovery choices. The control flow
  and inputs establish these roles, but animation labels were not observed.
- **Unresolved:** player-facing names for raw reaction categories; time in
  seconds at each framerate; animation names and non-default recovery bindings;
  exact hurtbox/collision/target-selection behavior and attack-flag exceptions
  during each substate; and character-specific overrides outside this
  representative native chain.

The maintained disassembly was inspected read-only. No names or metadata were
written back to it, and no transient analysis artifact was retained.
