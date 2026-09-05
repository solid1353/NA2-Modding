# Projectile gameplay lifecycle

Status: clean static baseline. The spawn, configuration, manager,
callback, transition/removal, and destruction paths are established from the clean
NA2 battle overlay. Class identity is additionally tied through the clean
resident vtables. No runtime trace was used.

This note deliberately does not cover damage calculation, substitution,
animation or frame-rate behavior, rendering, media, localization, Adventure,
or collision-system internals beyond the projectile-facing interface.

## Research coverage

- **Assigned scope:** this pass was limited to the clean NA2 `BTL.BIN`
`ccProjectile` entity lifecycle: configuration and class selection, construction
and registration, side/lineage identity, manager callbacks, the
projectile-facing collision query, transition/removal and destruction, and
evidence for limits or pooling. It also established the live/file/Ghidra address
relationship needed to make those findings auditable. The resident executable
was consulted only for allocator/service callees, vtable words, and class
identity.

- **Exploration depth:** coverage is mixed rather than globally exhaustive:

- The `0xB6` configuration records at live `0x0089C910` were enumerated
  exhaustively at their `0x68`-byte stride. Every record was included in the
  config-index/external-ID/selector crosswalk; all 103 accepted selector values
  (`0x00` through `0x66`), their factory branches, the 97 selectors used by the
  clean records, and the six unused selectors were accounted for. External-ID
  multiplicity, the common-profile table, and the record-controlled response
  tables were likewise enumerated over their complete established bounds.
- Instruction-level control-flow traces covered the factory at live
  `0x00729890`, root constructor and binder at `0x0072B190`/`0x0072B1F0`, spawn
  and external-ID entry points at `0x00736080`/`0x007362E0`, higher-level
  wrappers at `0x00736400`/`0x007364D0`, manager update/collision/unlink and
  cleanup entries at `0x00734BA0`, `0x00734D30`, `0x00734AD0`, `0x007349C0`,
  and `0x00735F30`, common state dispatch/transition at `0x0072CF50`,
  `0x0072E180`, and `0x00730950`, and root destruction/resource cleanup at
  `0x0072B800`/`0x0072B880`.
- The raw overlay was searched exhaustively for direct JALs to the manager
  spawn entry: all 87 sites were inventoried, including 29 in regions the
  maintained Ghidra export left undefined. The same direct-call inventory for
  collision query `0x00757B60` found 13 sites across seven identified classes.
  These are exhaustive inventories of direct encoded calls to those exact
  targets, not of indirect vtable calls or calls routed through other wrappers.
- Class coverage was exhaustive for the factory crosswalk and for the
  contiguous 99-descriptor `ccProj*`/`ccProjectile*` RTTI family inventory, but
  behavioral callback tracing was sampled. Detailed examples include
  `ccProjectileMakibishiLauncher`, the five listed `ccProjChar` records,
  `ccProjectileHomingDelay`, Clay Bird N/S, Explode S/L, Ink Snake N,
  Launcher DDR Fire, SIW Trap, Tew Skill Anki, Exc ORW Snake, Char NRW Other
  Self, Buddy Tonton, and Exc Item Tonton. Root and representative derived
  cleanup chains were traced; every derived class's complete state machine was
  not.
- A bounded raw-instruction scan of the projectile implementation region live
  `0x0072B000..0x00764000` found 104 direct constant writes of state `6` and 27
  of state `7` to object `+0x7E`. This confirms that the full helper at
  `0x00730950` is only one transition route: a direct state store does not by
  itself perform that helper's handle, notification, flag, or position-service
  side effects. Those sites were not all expanded into per-class call chains,
  so the helper-routed staged lifecycle documented below is proven for its
  cited paths, not a universal claim for every projectile class.
- The four-slot lineage/dedup structure was traced through lookup, insertion,
  replacement, age/consume handling, and its sole direct contact-response
  caller. The no-cap/no-object-pool result is a bounded negative result for the
  traced factory, allocator, spawn, manager-list, and destructor paths.

- **Confirmed coverage:** the evidence below establishes the complete common
factory-to-manager ownership chain, exact record/class identity, the common
callback and collision-facing interfaces, parent metadata inheritance and side
tag inversion, serial/list ownership, representative hit-to-removal paths,
class-aware destruction, and the distinction between the four-slot lineage
table and projectile object storage. Exact addresses use both overlay
conventions where applicable, and critical code/data claims were checked
against raw clean bytes rather than accepted solely from decompiler output.

- **Unresolved or untested:** remaining work includes indirect or data-driven
spawn and collision callers not reducible to the two direct-call inventories;
per-class interpretation of all direct state writes; complete behavior traces
for every derived callback; stable meanings for every record tail and instance
field; a proven direct owner or target pointer in the common object; and any
limit imposed outside the traced manager/factory path. The relationship, if
any, between the separate `ccSkillThrowProjectile` hierarchy and this entity
factory also remains unresolved.

- **Deliberate exclusions and overlap:** damage formulas or scaling, substitution, animation
or 60-FPS timing, widescreen/rendering, media, localization, Adventure, and
generic collision internals were intentionally left to other scoped work. Only
the collision services as observed by projectile classes are recorded here;
developer class names were not used to infer uncited gameplay semantics.

- **Evidence limitations:** this is clean-build static analysis of the hashed
`BTL.BIN` plus matching resident vtable/descriptor data. Raw instruction
decoding, complete bounded-table scans, direct-target call scans, and address
cross-checks validate the documented static claims. No PCSX2 execution,
savestate observation, runtime trace, injected probe, or empirical collision
test was performed, so callback cadence, real-time duration, dynamic target
choice, and runtime acceptance remain unvalidated. Absence claims are limited
to the explicitly stated assets, ranges, and paths.

## Evidence and address convention

The clean BTL identity and address conversion are defined in
[Standard game file identities](../game/files/file_identities.md).

The class vtable words were read from the matching clean
`@source_na2/SLPS_258.37`. The maintained Ghidra C and listing exports under
`@disassembly/NA2/exports/BTL.BIN/` were used as navigation aids, then critical
ranges were decoded again from the raw overlay bytes.

### Preserved-import limitation

Embedded absolute pointers and JAL targets in
the raw overlay are already live addresses. Ghidra may therefore resolve an
intra-overlay call to a label `0x40` after the physical function body or show
the wrong bytes for an embedded data pointer.

The most important mappings are:

| Purpose | Raw file offset | Ghidra/export body | Live EE address |
| --- | ---: | ---: | ---: |
| Projectile factory | `0x075990` | `0x00729850` | `0x00729890` |
| `ccProjectile` constructor | `0x077290` | `0x0072B150` | `0x0072B190` |
| Config binder | `0x0772F0` | `0x0072B1B0` | `0x0072B1F0` |
| Manager spawn/register | `0x082180` | `0x00736040` | `0x00736080` |
| External-ID wrapper | `0x0823E0` | `0x007362A0` | `0x007362E0` |
| Manager update pass | `0x080CA0` | `0x00734B60` | `0x00734BA0` |
| Manager collision pass | `0x080E30` | `0x00734CF0` | `0x00734D30` |
| Manager unlink entry | `0x080BD0` | `0x00734A90` | `0x00734AD0` |
| Manager-wide cleanup | `0x080AC0` | `0x00734980` | `0x007349C0` |
| Manager teardown entry | `0x082030` | `0x00735EF0` | `0x00735F30` |
| Manager serial lookup | `0x082090` | `0x00735F50` | `0x00735F90` |
| Serial absent-or-retiring predicate | `0x0820E0` | `0x00735FA0` | `0x00735FE0` |
| Common state-6 transition helper | `0x07CA50` | `0x00730910` | `0x00730950` |
| Common state dispatcher | `0x079050` | `0x0072CF10` | `0x0072CF50` |
| State-6 handler | `0x07A280` | `0x0072E140` | `0x0072E180` |
| Root deleting destructor | `0x077900` | `0x0072B7C0` | `0x0072B800` |
| Root resource cleanup | `0x077980` | `0x0072B840` | `0x0072B880` |
| Common-state jump table | `0x210BE0` | `0x008C4AA0` | `0x008C4AE0` |
| Record-`+0x09` jump table | `0x210C00` | `0x008C4AC0` | `0x008C4B00` |
| Config records | `0x1E8A10` | `0x0089C8D0` | `0x0089C910` |
| Factory jump table | `0x210A40` | `0x008C4900` | `0x008C4940` |
| Common profile table | `0x210734` | `0x008C45F4` | `0x008C4634` |
| Representative collision query | `0x0A3C60` | `0x00757B20` | `0x00757B60` |
| Root class descriptor | `0x214440` | `0x008C8300` | `0x008C8340` |

This distinction matters in practice. For example, the factory executes an
absolute pointer to live `0x0089C910`; the correct bytes are at file offset
`0x1E8A10` and Ghidra display `0x0089C8D0`, not at the export label
`DAT_0089c910`. Likewise, the real selector jump table starts at live
`0x008C4940` / file `0x210A40`. Reading the table at Ghidra display
`0x008C4940` shifts the dispatch by sixteen entries and produces false
constructor associations.

## Lifecycle summary

The established clean lifecycle is:

1. A caller supplies a config index directly to live `0x00736080`, or supplies
   a signed external ID to live `0x007362E0`, which linearly resolves it to an
   index.
2. Live `0x00729890` reads the `0x68`-byte config record and dispatches its
   selector through the 103-entry table at live `0x008C4940`.
3. The selected constructor allocates through resident `SUB_00117150` and
   builds a `ccProjectile` subclass. Live `0x0072B1F0` binds the record,
   index, external ID, and side tag to the object.
4. The spawn routine writes the two input vectors, invokes virtual slot
   `+0x54`, optionally copies lineage metadata from a parent projectile, and
   appends the object to the manager list.
5. Live `0x00734BA0` walks that list. It runs common pre-work, then calls
   virtual slot `+0x44`. A zero result causes unlinking and a deleting
   destructor call through slot `+0x08`.
6. Live `0x00734D30` is the projectile-facing collision/service pass. For an
   object with byte `+0x206` nonzero it invokes virtual slot `+0x48`.
7. Proven impact paths call live `0x00730950`, which enters transition state
   `+0x7E = 6`, clears `+0x82`, signals the handle at `+0x6C`, detaches the
   optional `+0x70` notification, clears `+0x216`, and invokes two resident
   position-associated cleanup/service calls.
8. On a later slot-`+0x44` invocation, common state dispatcher `0x0072CF50`
   routes state `6` to `0x0072E180`. Because `+0x82` was cleared, that handler
   promotes the object to state `7`. On a subsequent slot-`+0x44` invocation,
   state `7` makes the callback return zero, after which the manager unlinks
   and deleting-destructs the object. Full manager teardown also unlinks and
   deleting-destructs every remaining object.

## Configuration and factory

### Record set

The clean table at live `0x0089C910` contains exactly `0xB6` (182) records of
`0x68` bytes, ending at live `0x008A1300`. The clean records use 97 distinct
selector values in the inclusive range `0x00-0x66`. The factory accepts a
selector through `0x66`; its out-of-range path allocates a bare `0x290`-byte
object rather than entering a listed derived constructor.

The factory does not bounds-check its config-index argument before computing
`0x0089C910 + index * 0x68` and loading record `+0x06`, `+0x08`, and `+0x02`.
The selector itself is then checked as unsigned `< 0x67`. Thus a bad config
index is not converted into a clean lookup failure; the factory reads a record
address derived from that index first.

The external-ID wrapper at live `0x007362E0` has the raw calling convention
`a0 = external ID`, `a1 = side`, `a2/a3 = vector pointers`, and `t0 = optional
scalar-override flag`. It compares the signed halfword at record `+0x00` and
stops at the first match. There are 83 distinct external-ID values. External
ID zero appears in 100 records; every nonzero value in the clean table is
unique. Therefore config index and external ID are different identities and
must not be interchanged. A failed lookup passes index `-1` onward; this wrapper
contains no clean failure guard before the spawn call.

The wrapper calls `0x00736080` with factory extra and parent both zero. If its
flag is exactly `1`, it then overwrites the new object's `+0x258`: side `0`
selects battle global `+0xDE4`, side `1` selects `+0xDE8`, resident
`SUB_00217930(player, -3)` supplies an optional object, and that object's
`+0x24` float is used (or zero if absent). The wrapper has no null-object guard
before this overwrite. This is the same player selection made by opposite-tag
helper `0x00734160`, strengthening—but not turning into a named-field fact—the
source/target interpretation below.

There is one direct raw-overlay JAL to this wrapper, at live `0x007114D8`
(file `0x05D5D8`, Ghidra display `0x00711498`). That branch supplies external
ID `0x0027`, takes the side argument from its caller object `+0x20`, supplies
the same temporary vector for both vector inputs, and uses override flag `0`.
The wrapper therefore resolves clean config index `0x12`, whose selector
`0x07` constructs `ccProjectileMakibishiLauncher` (allocation `0x2A0`, resident
vtable `0x005E0510`). This is a complete external-ID-callsite-to-class example.

### Proven record fields

Names below describe observed consumers, not guessed game-design terminology.

| Record offset | Width | Proven use |
| ---: | ---: | --- |
| `+0x00` | `s16` | External ID copied to object `+0x7A`; searched by the external-ID wrapper. |
| `+0x02` | `u8` | Constructor/class selector for the 103-entry factory jump table. |
| `+0x04` | `s16` | Index into the shared `0x0C`-byte common profile table at live `0x008C4634`. |
| `+0x06` | `s16` | Loaded by the factory and passed into constructor branches. |
| `+0x08` | `s8` | Loaded by the factory and passed into constructor branches. |
| `+0x09` | `u8` | Selects common activation/orientation setup at live `0x0072D010`. |
| `+0x0C` | `f32` | Copied to object `+0x258`. |
| `+0x10` | `u32` | Copied to `+0x18` of a linked helper object by live `0x0072BF30`; semantics remain open. |
| `+0x14` | `u8` | Copied to object `+0x208`. |
| `+0x15` | `u8` | Selects the root slot-`+0x30` common action table; also tested by common contact logic. |
| `+0x16` | `u8` | Selects a 24-entry common response table and an additional state-6 branch. |
| `+0x17` | `u8` | Selects a 23-entry common response table. |
| `+0x18` | `u8` | Selects a 24-entry common contact-response table from root slot `+0x24`. |
| `+0x1C` | `f32` | Supplies object `+0x1E0` when that field still has its sentinel value. |
| `+0x20` | `u8` | Chooses among common helper/proxy setup modes `0`, `1`, and `2`. |
| `+0x21` | `u8` | Mode `1` causes object `+0x210` to receive value `3`. |
| `+0x24`, `+0x28` | `f32` | Passed as geometric extents to the projectile-facing proxy setup. |
| `+0x2C` | `s16` | Optional positional service ID consumed by live `0x00734030`; `-1` disables it. |
| `+0x2E` | `u8` | Enables an immediate player-side lookup/setup path during binding. |
| `+0x2F` | `u8` | Read by later common logic; no stable semantic name is established. |
| `+0x32` | `u8` | Selects a 15-entry common response table. |
| `+0x34` | `u8` | Common flag byte returned verbatim by live accessor `0x00732B10`. |
| `+0x38`, `+0x3C`, `+0x40` | `s32` | `ccProjectileHomingDelay` post-spawn initialization converts them to floats at object `+0x1E0`, `+0x298`, and `+0x29C`. |
| `+0x48` | `f32` | `ccProjectileHomingDelay` post-spawn initialization copies it to object `+0x2A0`. |
| `+0x50` | `s16` | One `ccProjClayBrdN` slot-`+0x1C` branch reads it and truncates the value into a helper byte at `+0x2C`. |
| `+0x64` | `f32` | Supplies a class-created helper scalar at `+0x28` in the exact consumers listed below. |

### Common profile selected by record `+0x04`

The clean records use 56 distinct profile indices in the inclusive range
`0x00-0x40`. Live `0x0072B9D0` consumes the selected `0x0C`-byte profile:

| Profile offset | Common consumer |
| ---: | --- |
| `+0x01` | Copied to object mode byte `+0x80`, except config indices `0xB4` and `0xB5`, which force mode `4`. |
| `+0x02` | Normally copied to object signed field `+0x212`; value `0x14` selects a special proxy/resource-allocation path instead. |
| `+0x04` | Normally copied to object signed field `+0x214`. |

Profile index `0x22` has an additional common random-selection branch. The
profile's remaining bytes include pointers used by the special setup path, but
their complete type is not established here. This profile table is separate
from both the `0x68`-byte projectile records and the selector jump table.

The special profile `+0x02 == 0x14` path is the proven constructor for object
`+0x64`, closing its lifecycle with the collision callback and root destructor:

- modes `+0x80 = 1` or `3` allocate `0xA0` bytes, initialize the object through
  resident `SUB_0019CD80`, pass it to projectile virtual slot `+0x68`, and store
  it at `+0x64`;
- modes `+0x80 = 2` or `4` allocate `0x120` bytes, run
  `SUB_0019CD80`, initialize its `+0xA0` member through resident
  `SUB_001AA940`, run `SUB_001B7520`, pass it through the same virtual slot
  `+0x68`, and store it at `+0x64`.

This exactly matches root cleanup: modes `1`/`3` release `+0x64` through
`SUB_001951A0`, while modes `2`/`4` use `SUB_001B7570`. The allocator branches
test for null before object-specific initialization; the raw path still passes
the resulting value through virtual slot `+0x68` and stores it at `+0x64`.
Within mode `2`, profile indices `0x11..0x13` additionally allocate a `0xA0`-
byte secondary object, initialize/configure it through resident
`SUB_0019CD80` and `SUB_001952F0`, store it at projectile `+0x68`, and associate
it with the primary `+0x64` service. Root cleanup's
`SUB_001951A0(+0x68, 1)` call is the matching release path.

### Additional binder side effects

The clean binder at live `0x0072B1F0` also establishes these common behaviors:

- it writes object `+0x0C = 1` before record-specific setup;
- record `+0x20` values `1` or `2` allocate a `0x4C`-byte helper stored at
  object `+0x70`, selecting a mode-specific template from live `0x008AB750 +
  0xB0 * mode`; mode `0` allocates none;
- record `+0x21 == 1` writes signed halfword `3` to object `+0x210`;
- when record `+0x2E` is nonzero, opposite-tag helper `0x00734160`, resident
  `SUB_00217930(player, -3)`, and resident `SUB_00306BD0(player)` derive object
  scalar `+0x258`; when it is zero, record float `+0x0C` supplies `+0x258`;
- it compares the signed halfword at `+0x9F6` of the two battle-player globals
  at battle-global `+0xDE4/+0xDE8` and writes object `+0x1F0 = 1` when they are
  equal, otherwise `0`;
- it selects the opposite-tag battle player from object `+0x8A`, takes the low
  byte of that player's signed halfword `+0x9F6`, and writes object `+0x202`;
- it ends by writing object byte `+0x25E = 1`.

The helper at `+0x70` is later registered and detached through the manager
service interface. Its concrete resident type remains unidentified.

### Record `+0x09` activation dispatch

Live `0x0072D010` signals `+0x6C`, invokes virtual slot `+0x2C`, and dispatches
record byte `+0x09` through the seven-entry table at live `0x008C4B00`. The
observable field setup is:

| `+0x09` value | Live target | Proven writes before common exit |
| ---: | ---: | --- |
| `0` | `0x0072D1D0` | No orientation-field write. |
| `1` | `0x0072D090` | Randomized quantized value at `+0xE4`; constant-derived value at `+0xD0`. |
| `2` | `0x0072D10C` | Randomized quantized value at `+0xE8`; constant-derived value at `+0xD0`. |
| `3` | `0x0072D188` | `+0xE4 = pi/2` (`0x3FC90FDB`). |
| `4` | `0x0072D19C` | `+0xE8 = pi/2` (`0x3FC90FDB`). |
| `5` | `0x0072D1B0` | `+0xE0 = pi/2` (`0x3FC90FDB`). |
| `6` | `0x0072D1C4` | `+0xE0 = -pi/2` (`0xBFC90FDB`). |

Every branch then writes common state `+0x7E = 2` and, when helper `+0x70` is
present, clears that helper's byte `+0x01`. Values outside `0..6` take the same
no-orientation-write exit as value `0`. Clean records use only values `0..7`:
counts are respectively `77, 53, 9, 5, 0, 2, 0, 36`, so implemented cases `4`
and `6` are unused in the clean table and value `7` intentionally takes the
default exit. These writes identify setup axes/angles mechanically; they do not
prove a camera-space or world-space naming convention.

### Record-controlled response selectors

Five more record bytes select bounded common dispatch tables. These are useful
projectile-interface facts even though the handlers beyond them enter
damage/substitution-adjacent combat-response code that is outside this lane:

| Record byte | Common reader (live) | Valid selector range | Jump table (live / file / Ghidra display) |
| ---: | ---: | ---: | --- |
| `+0x15` | root slot-`+0x30` target `0x00730140` | `< 0x17` | `0x008C4BA0` / `0x00210CA0` / `0x008C4B60` |
| `+0x16` | `0x00732430` | `< 0x18` | `0x008C4C00` / `0x00210D00` / `0x008C4BC0` |
| `+0x17` | `0x007332C0` | `< 0x17` | `0x008C4CB0` / `0x00210DB0` / `0x008C4C70` |
| `+0x18` | root slot-`+0x24` target `0x0072D200` | `< 0x18` | `0x008C4B20` / `0x00210C20` / `0x008C4AE0` |
| `+0x32` | `0x00731F80` | `< 0x0F` | `0x008C4C60` / `0x00210D60` / `0x008C4C20` |

The `+0x15` byte is also tested directly by common contact logic at live
`0x0072E8E4`. The `+0x16` byte is independently read in the slot-`+0x24`
path at live `0x0072D258`; selector value `2` can enter live `0x007306A0`
after a transition to state `6`. Live `0x00732B10` is a simple accessor that
returns record byte `+0x34` verbatim; observed consumers test bits including
`0x04` and `0x08`, so it is retained only as a common flag/filter byte.

All clean-table values fit their proven bounds. The clean records use 16
distinct `+0x15` values (maximum `0x16`), 15 distinct `+0x16` values (maximum
`0x17`), 17 distinct `+0x17` values (maximum `0x16`), 18 distinct `+0x18`
values (maximum `0x17`), and nine distinct `+0x32` values (maximum `0x0E`).
Record `+0x2C` is the separate signed positional-service selector: the clean
distribution is `-1` for 105 records, `9` for two, `0x11` for one, `0x12` for
29, and `0x13` for 45. Live `0x00734030` skips service construction for `-1`.
No descriptive names are assigned to individual response selectors here.

### Tail-field consumers and mutable records

Following the common object `+0x74` record pointer through the clean projectile
implementation establishes every direct `+0x50/+0x64` load in the range live
`0x0072B000..0x00764000`:

| Class / resident vtable | Callback | Record read | Proven destination |
| --- | ---: | ---: | --- |
| `ccProjClayBrdN` / `0x005DF730` | slot `+0x1C`, live `0x00752280` | `+0x64` at `0x00752310` and `0x007524D0`; `+0x50` at `0x007524C4` | `+0x64` is copied to a created helper's float `+0x28`; one branch truncates `s16(+0x50)` into helper byte `+0x2C`. |
| `ccProjClayBrdS` / `0x005DF6D0` | slot `+0x1C`, live `0x007536E0` | `+0x64` at `0x00753764` | Multiplies it by `1.2f`, then writes helper float `+0x28`. |
| `ccProjExplodeS` / `0x005DF310` | slot `+0x50`, live `0x00756D60` | `+0x64` at `0x00756DE0` | Copies it to float `+0x28` of the object returned by common entry `0x0072F420`. |
| `ccProjExplodeL` / `0x005DF2B0` | slot `+0x50`, live `0x00757110` | `+0x64` at `0x00757198` | Multiplies it by `1.5f`, then writes the returned object's float `+0x28`. |
| `ccProjInkSnakeN` / `0x005DE2D0` | slot `+0x1C`, live `0x00761370` | `+0x64` at `0x007613EC` | Copies it to a created helper's float `+0x28`. |

The first-activation branches (`object +0x87 == 1`) in
`ccProjClayBrdN`, `ccProjClayBrdS`, and `ccProjInkSnakeN` also write through
object `+0x74` into the shared record itself: `+0x15 = 0x0E` and
`+0x16/+0x17/+0x18 = 0x0D`. Since the binder points `+0x74` into the global
record table rather than making an object-local copy, those writes are shared
runtime mutation, not per-object configuration. They directly change the
selectors consumed by the five common response dispatchers above.

The same bounded direct-dataflow scan found no load through object `+0x74` for
record offsets `+0x4C`, `+0x54`, `+0x58`, `+0x5C`, or `+0x60`. This does not
prove that those bytes are globally unused: an aliased record pointer or a
consumer outside the projectile implementation range can evade this simple
pattern. No semantic name is assigned to them here.

### Representative post-spawn initialization

Spawn invokes virtual slot `+0x54` after copying both vector inputs but before
parent-lineage inheritance and manager insertion. The root slot is the no-op at
live `0x0072B490`; strategies can replace it with exact class-specific setup:

- `ccProjDist2Speed` slot `+0x54`, live `0x00739260`, obtains a random value
  from resident `SUB_0017B798`, uses `(value >> 3) % 42` to select one of 42
  resident 16-byte vectors at `0x0040BC80`, multiplies it by `7.5f`, writes the
  result at object `+0xB0`, and clears the words at `+0xB4` and `+0xBC`;
- `ccProjectileHomingDelay` slot `+0x54`, live `0x00743770`, converts signed
  record words `+0x38/+0x3C/+0x40` to floats at object
  `+0x1E0/+0x298/+0x29C`, copies record float `+0x48` to `+0x2A0`, and writes
  `+0x2A8 = -1`; config index `0x1B` additionally writes byte `+0x26D = 1`;
- `ccProjectileParabola` slot `+0x54`, live `0x007458D0`, has no universal
  vector rewrite. For config indices `0x30` and `0x9A` only, it visits two
  entries obtained from handle `+0x6C` and assigns a side-dependent word
  (`0x11000` for side tag `0`, `0x22000` for tag `1`) while clearing the
  adjacent word.

These are callback-local initialization facts. They do not imply real-time
rates, and the random `ccProjDist2Speed` vector is not given a stronger semantic
name than its observed storage and arithmetic support.

### Representative records with exact class identity

Five factory branches were followed through their constructors, resident
vtables, and vtable `+0x00` class handles. All five enter the `ccProjChar`
subfamily, whose constructor in turn enters `ccProjectile`.

| Config index | External ID | Selector | Allocation | Constructor (live) | Resident vtable | Descriptor handle / exact class |
| ---: | ---: | ---: | ---: | ---: | ---: | --- |
| `0x7A` | `0x0000` | `0x2A` | `0x470` | `0x0074F410` | `0x005DF990` | `0x008C8CD0` / `ccProjTest` |
| `0x7B` | `0x0000` | `0x2B` | `0x470` | `0x00751A70` | `0x005DF790` | `0x008C8C10` / `ccProjCharNRW` |
| `0xB3` | `0x0000` | `0x4F` | `0x4E0` | `0x0075E640` | `0x005DE6D0` | `0x008C8560` / `ccProjCharNRWOtherSelf` |
| `0xB4` | `0x0000` | `0x5D` | `0x470` | `0x0075F080` | `0x005DE660` | `0x008C8530` / `ccProjCharSZWBuddyTonTon` |
| `0xB5` | `0x006B` | `0x66` | `0x470` | `0x007605E0` | `0x005DE350` | `0x008C8420` / `ccProjSZWExcItemTonton` |

External ID `0x006B` is therefore a directly usable, unambiguous clean-table
identity for `ccProjSZWExcItemTonton`. The vtable link also corrects a misleading
Ghidra comment at displayed `0x007605D8`: its encoded live pointer
`0x008A4D10` addresses the resource string `2szwbod1.ccs`, while Ghidra shows
the bytes `0x40` later and labels them `ccProjInkBrdN`.

### Complete selector-to-class crosswalk

The following map is exhaustive for the clean 103-entry selector jump table.
Factory-block targets and allocation immediates come from raw instructions.
For each branch, the final object-`+0x50` vtable was taken either from the
factory block or the constructor it calls. Resident vtable `+0x00` then gives
the overlay RTTI handle; dereferencing that handle gives the exact class-name
pointer. This is a complete raw-byte-to-resident-vtable-to-overlay-RTTI chain,
not a name inferred from nearby strings.

Config indices and external IDs in this table are hexadecimal. `none` means
the applicable clean records use external ID zero. The six unused selectors
are `0x02`, `0x12`, `0x13`, `0x1A`, `0x22`, and `0x63`. Selector `0x24` is
used by config index `0x4D` / external ID `0x003F`, but intentionally reaches
the shared bare-`ccProjectile` factory block.

| Selector | Factory block (live) | Allocation | Final vtable | Exact class | Config indices | Nonzero external IDs |
| ---: | ---: | ---: | ---: | --- | --- | --- |
| 0x00 | 0x0072998C | 0x290 | 0x005E07B0 | ccProjectileStraight | 0x07, 0x08, 0x09, 0x19, 0x20, 0x22, 0x2F, 0x31, 0x32, 0x45, 0x46, 0x47, 0x48, 0x49, 0x4A, 0x52, 0x6A, 0x79, 0x7E | 0x0024, 0x002E, 0x0033, 0x005B |
| 0x01 | 0x0072990C | 0x2E0 | 0x005E0630 | ccProjectileChase | 0x04, 0x25, 0x51 | 0x0023 |
| 0x02 | 0x00729934 | 0x2A0 | 0x005E0690 | ccProjectileLauncherDelay | unused | none |
| 0x03 | 0x00729964 | 0x290 | 0x005E0750 | ccProjDist2Speed | 0x00, 0x01, 0x02, 0x03, 0x11, 0x14, 0x15, 0x16, 0x2C, 0x3A, 0x3D, 0x42, 0x43, 0x55, 0x75, 0x77, 0x8F, 0xA7, 0xAC, 0xAD, 0xAE, 0xAF | 0x000F, 0x0010, 0x0011, 0x0012, 0x0016, 0x001C, 0x003D, 0x006C, 0x0021 |
| 0x04 | 0x007299B4 | 0x2D0 | 0x005E05D0 | ccProjectileTenten1 | 0x05 | 0x0034 |
| 0x05 | 0x007299DC | 0x2A0 | 0x005E0570 | ccProjectileTenten2Launcher | 0x06 | 0x0035 |
| 0x06 | 0x00729A3C | 0x2A0 | 0x005E04B0 | ccProjectileMakibishi | 0x13 | none |
| 0x07 | 0x00729A0C | 0x2A0 | 0x005E0510 | ccProjectileMakibishiLauncher | 0x12, 0x9C | 0x0027, 0x006E |
| 0x08 | 0x00729A64 | 0x290 | 0x005E0450 | ccProjectileTenten0Launcher | 0x0E | 0x0013 |
| 0x09 | 0x00729A8C | 0x2B0 | 0x005E0390 | ccProjectileHoming | 0x10, 0x17, 0x1C, 0x1D, 0x24, 0x27, 0x2D, 0x33, 0x4F, 0x82, 0x99 | 0x0029, 0x002A |
| 0x0A | 0x00729AB4 | 0x2E0 | 0x005E0330 | ccProjSoundWave | 0x38, 0x39 | 0x0019, 0x001A |
| 0x0B | 0x00729ADC | 0x2B0 | 0x005E02D0 | ccProjHomingScatter | 0x37 | 0x0018 |
| 0x0C | 0x00729B18 | 0x2C0 | 0x005E03F0 | ccProjectileInsectLauncher | 0x0F, 0x98 | 0x0015, 0x0065 |
| 0x0D | 0x00729B40 | 0x2E0 | 0x005E0270 | ccProjectileKibakukunai | 0x0B | 0x0025 |
| 0x0E | 0x00729B68 | 0x340 | 0x005E01B0 | ccProjectileKibakufuda | 0x0D, 0xA0 | 0x0028 |
| 0x0F | 0x00729B90 | 0x290 | 0x005E0210 | ccProjectileExplosion | 0x18, 0x28, 0x29, 0x2A | none |
| 0x10 | 0x00729BB8 | 0x290 | 0x005E0150 | ccProjectileKagebunshinLauncher | 0x0A, 0x88, 0xA2 | 0x002B, 0x0057, 0x005E |
| 0x11 | 0x00729BE0 | 0x2A0 | 0x005E0090 | ccProjectileStickHead | 0x1A | none |
| 0x12 | 0x0072AD20 | 0x290 | 0x005E0810 | ccProjectile | unused | none |
| 0x13 | 0x0072AD20 | 0x290 | 0x005E0810 | ccProjectile | unused | none |
| 0x14 | 0x00729C08 | 0x2B0 | 0x005E00F0 | ccProjectileHomingDelay | 0x1B, 0x70, 0x89, 0xA3 | 0x004C |
| 0x15 | 0x00729C30 | 0x290 | 0x005E0030 | ccProjectileParabola | 0x0C, 0x30, 0x36, 0x3B, 0x4B, 0x9A, 0xA1, 0xB0 | 0x0026, 0x002F, 0x0017, 0x001D, 0x0069, 0x0054, 0x006F |
| 0x16 | 0x00729C58 | 0x290 | 0x005DFFD0 | ccProjectilePoisonExplosion | 0x1E | none |
| 0x17 | 0x00729C80 | 0x2B0 | 0x005E06F0 | ccProjectileLauncherHak1 | 0x1F | 0x0036 |
| 0x18 | 0x00729C80 | 0x2B0 | 0x005E06F0 | ccProjectileLauncherHak1 | 0x21, 0x26, 0x6B, 0x6C, 0x6D | 0x0037, 0x0048, 0x0049, 0x004A |
| 0x19 | 0x00729C80 | 0x2B0 | 0x005E06F0 | ccProjectileLauncherHak1 | 0x23 | 0x0038 |
| 0x1A | 0x00729CA8 | 0x330 | 0x005DFE90 | ccProjBakutiBall | unused | none |
| 0x1B | 0x00729CD0 | 0x2A0 | 0x005DFE30 | ccProjStickKibakuFuda | 0x2E | 0x002D |
| 0x1C | 0x00729CF8 | 0x2C0 | 0x005DFDD0 | ccProjFloatLauncher | 0x34 | 0x0032 |
| 0x1D | 0x00729D20 | 0x290 | 0x005DFD70 | ccProjecShotgunLauncher | 0x3C, 0x3F, 0x40, 0x41 | 0x001B, 0x003A, 0x003B, 0x003C |
| 0x1E | 0x00729D48 | 0x2B0 | 0x005DFD10 | ccProjFixedFire | 0x44, 0x9B | none |
| 0x1F | 0x00729D70 | 0x330 | 0x005DFE90 | ccProjBakutiBall | 0x35, 0x80 | 0x0030, 0x006A |
| 0x20 | 0x00729D98 | 0x2A0 | 0x005DFCB0 | ccProjKunaiBomb | 0x2B | 0x002C |
| 0x21 | 0x00729DC0 | 0x2A0 | 0x005DFC50 | ccProjSyncHand | 0x3E | 0x0039 |
| 0x22 | 0x00729DE8 | 0x2A0 | 0x005DFBF0 | ccProjBoomerang | unused | none |
| 0x23 | 0x00729E10 | 0x2C0 | 0x005DFB30 | ccProjLunFan | 0x4C | 0x003E |
| 0x24 | 0x0072AD20 | 0x290 | 0x005E0810 | ccProjectile | 0x4D | 0x003F |
| 0x25 | 0x00729E38 | 0x2C0 | 0x005DFAD0 | ccProjLunLinear | 0x4E | 0x0040 |
| 0x26 | 0x00729E60 | 0x2E0 | 0x005DFA70 | ccProjSandPellet | 0x50 | none |
| 0x27 | 0x00729E88 | 0x300 | 0x005DF8C0 | ccProjIronRain | 0x53 | none |
| 0x28 | 0x00729EB0 | 0x2A0 | 0x005DF860 | ccProjectileScoLauncher | 0x54 | none |
| 0x29 | 0x00729EE0 | 0x2E0 | 0x005DF800 | ccProjectileNrwCombo | 0x56, 0x57 | none |
| 0x2A | 0x0072ACF0 | 0x470 | 0x005DF990 | ccProjTest | 0x7A | none |
| 0x2B | 0x00729F1C | 0x470 | 0x005DF790 | ccProjCharNRW | 0x7B | none |
| 0x2C | 0x00729F4C | 0x2D0 | 0x005DF730 | ccProjClayBrdN | 0x58 | 0x0041 |
| 0x2D | 0x00729F74 | 0x2B0 | 0x005DF670 | ccProjLauncherClayBrdS | 0x5F | 0x0042 |
| 0x2E | 0x00729FA4 | 0x2A0 | 0x005DF610 | ccProjLauncherClayBrdSA | 0x60 | 0x0043 |
| 0x2F | 0x00729FD4 | 0x2D0 | 0x005DF6D0 | ccProjClayBrdS | 0x59, 0x5A | none |
| 0x30 | 0x0072A000 | 0x2B0 | 0x005DF550 | ccProjLauncherClayBrdU | 0x61 | 0x0044 |
| 0x31 | 0x0072A030 | 0x2B0 | 0x005DF4F0 | ccProjLauncherClayBrdUA | 0x62 | 0x0045 |
| 0x32 | 0x0072A060 | 0x2B0 | 0x005DF490 | ccProjLauncherClayBrdH | 0x65 | none |
| 0x33 | 0x0072A090 | 0x2C0 | 0x005DF5B0 | ccProjClayBrdU | 0x5B | none |
| 0x34 | 0x0072A090 | 0x2C0 | 0x005DF5B0 | ccProjClayBrdU | 0x5E | none |
| 0x35 | 0x0072A0BC | 0x2B0 | 0x005DF370 | ccProjLauncherClaySpd | 0x63 | 0x0046 |
| 0x36 | 0x0072A0EC | 0x2B0 | 0x005DF370 | ccProjLauncherClaySpd | 0x64 | 0x0047 |
| 0x37 | 0x0072A11C | 0x330 | 0x005DF430 | ccProjClaySpd | 0x5C | none |
| 0x38 | 0x0072A148 | 0x340 | 0x005DF3D0 | ccProjClaySpd2 | 0x5D | none |
| 0x39 | 0x0072A198 | 0x2B0 | 0x005DF310 | ccProjExplodeS | 0x66 | none |
| 0x3A | 0x0072A1C0 | 0x2B0 | 0x005DF2B0 | ccProjExplodeL | 0x67 | none |
| 0x3B | 0x0072A1E8 | 0x2B0 | 0x005DF250 | ccProjDDRFire | 0x68 | none |
| 0x3C | 0x0072A210 | 0x2A0 | 0x005DF1F0 | ccProjLauncherDDRFire | 0x69 | none |
| 0x3D | 0x0072A240 | 0x2A0 | 0x005DF190 | ccProjSIWTrap | 0x6E | 0x004B |
| 0x3E | 0x0072A288 | 0x2F0 | 0x005DF130 | ccProjCHYSkillKunai | 0x6F | none |
| 0x3F | 0x0072A2D0 | 0x2B0 | 0x005DF0C0 | ccProjLauncherTewAwake | 0x71 | 0x004D |
| 0x40 | 0x0072A314 | 0x2B0 | 0x005DEFE0 | ccProjLauncherTewRoll | 0x72 | 0x004E |
| 0x41 | 0x0072A358 | 0x2B0 | 0x005DF050 | ccProjLauncherTewKunai | 0x73 | 0x004F |
| 0x42 | 0x0072A39C | 0x2A0 | 0x005DEF80 | ccProjLauncherTewAnki | 0x74 | 0x0050 |
| 0x43 | 0x0072A3E4 | 0x2A0 | 0x005DEF20 | ccProjTewSkillAnki | 0x76 | none |
| 0x44 | 0x0072A42C | 0x2A0 | 0x005DEEC0 | ccProjSchSkillSenbon | 0x78 | none |
| 0x45 | 0x0072A474 | 0x290 | 0x005DEE60 | ccProjSCOGen | 0x91 | 0x001F |
| 0x46 | 0x0072A4B0 | 0x2B0 | 0x005DEE00 | ccProjDDRGen | 0x8A | 0x001E |
| 0x47 | 0x0072A4F8 | 0x2A0 | 0x005DEDA0 | ccProjSCVGen | 0x92 | 0x0022 |
| 0x48 | 0x0072A540 | 0x290 | 0x005DED40 | ccProjectileNumbnessBall | 0x85 | 0x0031 |
| 0x49 | 0x0072A57C | 0x2B0 | 0x005DECE0 | ccProjectileNumbness | 0x86 | none |
| 0x4A | 0x0072A5E8 | 0x290 | 0x005DEC80 | ccProjNumbnessSmoke | 0x87 | none |
| 0x4B | 0x0072A624 | 0x2C0 | 0x005DEC20 | ccProjSNWCmbULauncher | 0x96, 0x97 | none |
| 0x4C | 0x0072A66C | 0x290 | 0x005DEBC0 | ccProjINWFlower | 0x7F | none |
| 0x4D | 0x0072A6A8 | 0x2C0 | 0x005DEB60 | ccProjExcORWSnake | 0x9D | none |
| 0x4E | 0x0072A6F0 | 0x290 | 0x005DEB00 | ccProjTripleChase | 0x7D | 0x0051 |
| 0x4F | 0x0072AAB0 | 0x4E0 | 0x005DE6D0 | ccProjCharNRWOtherSelf | 0xB3 | none |
| 0x50 | 0x0072A72C | 0x290 | 0x005DEAA0 | ccProjKNWbuddy | 0x9E | none |
| 0x51 | 0x0072A768 | 0x290 | 0x005DEA40 | ccProjDDRExcItemLauncher | 0x8C | 0x0058 |
| 0x52 | 0x0072A7A4 | 0x2B0 | 0x005DE9E0 | ccProjDDRExcItemBullet | 0x8B | none |
| 0x53 | 0x0072A7EC | 0x290 | 0x005DE980 | ccProjExplode3 | 0x81 | none |
| 0x54 | 0x0072A828 | 0x290 | 0x005DE920 | ccProjDDRBuddy | 0x8D | none |
| 0x55 | 0x0072A864 | 0x290 | 0x005DE8C0 | ccProjDDRBuddyLauncher | 0x8E | none |
| 0x56 | 0x0072A8A0 | 0x2A0 | 0x005DE860 | ccProjSCVExcItemFire | 0x93 | 0x0061 |
| 0x57 | 0x0072A8E8 | 0x2A0 | 0x005DE800 | ccProjYMTSkillYari | 0xA4, 0xA5, 0xA6 | none |
| 0x58 | 0x0072A930 | 0x2A0 | 0x005DE7A0 | ccProjSSWGoukakyu | 0xA8 | none |
| 0x59 | 0x0072A978 | 0x2D0 | 0x005DE2D0 | ccProjInkSnakeN | 0xAA | none |
| 0x5A | 0x0072A9C4 | 0x2F0 | 0x005DE270 | ccProjInkBrdN | 0xA9 | none |
| 0x5B | 0x0072AA10 | 0x330 | 0x005DE210 | ccProjInkMouseN | 0xAB | none |
| 0x5C | 0x0072AA68 | 0x2B0 | 0x005DE740 | ccProjSCVSkillPupBullet | 0x94, 0x95 | none |
| 0x5D | 0x0072AAE0 | 0x470 | 0x005DE660 | ccProjCharSZWBuddyTonTon | 0xB4 | none |
| 0x5E | 0x0072AB10 | 0x290 | 0x005DE600 | ccProjTEWExcItemKagura | 0x83 | 0x005A |
| 0x5F | 0x0072AB4C | 0x290 | 0x005DE5A0 | ccProjSIWExcItemRakushiki | 0x84 | 0x005C |
| 0x60 | 0x0072AB88 | 0x290 | 0x005DE540 | ccProjKNWBuddyShikomi | 0x9F | none |
| 0x61 | 0x0072ACB4 | 0x290 | 0x005DE4E0 | ccProjSCHExcItemSenbon | 0x90 | 0x0062 |
| 0x62 | 0x0072ABC4 | 0x2A0 | 0x005DE480 | ccProjNWVGen | 0x7C | 0x0020 |
| 0x63 | 0x0072AD20 | 0x290 | 0x005E0810 | ccProjectile | unused | none |
| 0x64 | 0x0072AC0C | 0x290 | 0x005DE420 | ccProjBlueSmoke | 0xB1 | none |
| 0x65 | 0x0072AC48 | 0x290 | 0x005DE3C0 | ccProjWhiteSmoke | 0xB2 | none |
| 0x66 | 0x0072AC84 | 0x470 | 0x005DE350 | ccProjSZWExcItemTonton | 0xB5 | 0x006B |

## Construction and object layout

### `ccProjectile`

The root class descriptor is live `0x008C8340`; its class handle is
`0x008C8350`, and its name string is live `0x008A4D40` / file `0x1F0E40`:
`ccProjectile`.

The resident vtable at `0x005E0810` begins with class handle `0x008C8350`.
The clean factory's common constructor at live `0x0072B190`:

- invokes the lower object constructor at live `0x00709AA0`;
- installs vtable `0x005E0810` at object `+0x50`;
- clears `+0x248`, sets signed `+0x24A` to `-1`, clears `+0x24C`, and clears
  `+0x250`;
- calls the large common initializer at live `0x0072B4A0`.

The common initializer establishes the list, state, side, transform, proxy,
and callback-facing fields used below. The root object is at least `0x290`
bytes; multiple direct factory branches allocate exactly that size.

During subsequent common record setup, live `0x0072B9D0` allocates the
`0x24`-byte handle stored at `+0x6C`, initializes it through resident
`SUB_001DD8D0`, writes the projectile pointer back at handle `+0x1C`, and makes
two association calls to resident `SUB_001DDB70`. It then writes common state
`+0x7E = 2`. The code checks the allocator result before the initializer call
but, after storing it, unconditionally writes handle `+0x1C`; this is another
explicit success invariant. Terminal paths signal this handle through
`SUB_001DDA50`, and root cleanup later releases it through
`SUB_001DD920(value, 1)`.

### `ccProjChar`

`ccProjChar` is a proven direct `ccProjectile` descendant. Its descriptor is
live `0x008C83E0`, its handle is `0x008C83F8`, and resident vtable
`0x005DFA00` begins with that handle.

Its constructor at live `0x0074F290` calls `ccProjectile` constructor
`0x0072B190`, installs vtable `0x005DFA00`, initializes members and containers
at `+0x2D4`, `+0x300`, `+0x350`, and `+0x3B0`, and calls reset/setup entry
`0x0074D4C0`. That setup clears the resource members around `+0x290`, sets
`+0x2A8 = -1`, initializes the two small members at `+0x410` and `+0x420`,
sets `+0x430` and `+0x434` to `-1`, clears `+0x438-+0x454`, writes `1.0f` at
`+0x458`, clears `+0x45C`, and writes `1` at `+0x45E`.

The corresponding resource cleanup entry at live `0x0074D580` releases
non-null `+0x298` through resident `SUB_00119490`, releases non-null `+0x294`
through resident `SUB_001951A0`, clears both, and continues through live
`0x0074D820`. The deleting destructor at live `0x0074F130` tears down the
derived containers, restores parent vtables during destruction, and calls
resident deallocator `SUB_00117000` when its deleting flag is positive. The
container calls are exact: resident `SUB_001BEA90(member, -1)` handles members
at `+0x3C0`, `+0x360`, and `+0x300`, while resident
`SUB_001DD920(object+0x2D4, -1)` handles the member at `+0x2D4`. The root cleanup
entry at live `0x0072B880` and lower-object destructor `0x00709B60(object, 0)`
run as the vtable is restored to `ccProjectile`.

### Representative derived cleanup

The resident vtables give `ccProjCharSZWBuddyTonTon` deleting destructor live
`0x00763D70` and `ccProjSZWExcItemTonton` deleting destructor live
`0x007637F0`. Their raw bodies differ in the installed derived vtable but share
the same ownership chain: derived/root cleanup, common `ccProjChar` resource
cleanup `0x0074D580`, the four container teardowns above, final root cleanup,
and `SUB_00117000` only for a positive deleting flag. Both constructors allocate
a four-byte, one-entry pointer array at subclass offset `+0x298`; the common
resource cleanup is therefore directly responsible for memory acquired during
their construction.

`ccProjCharNRW` demonstrates additional subclass ownership. Its deleting
destructor at live `0x007651F0` releases non-null word `+0x460` with resident
`SUB_00199190(value, 1)` and non-null word `+0x464` with resident
`SUB_001951A0(value, 1)`, clears both fields, and only then continues through
the shared `ccProjChar` container/root/free chain. This establishes that the
manager's slot-`+0x08` deleting call reaches class-specific resource release,
not merely base-object deallocation.

### Core instance fields

| Object offset | Proven role |
| ---: | --- |
| `+0x30-+0x3C` | Current position vector initialized from spawn input vector 1. |
| `+0x50` | Resident vtable pointer. |
| `+0x60` | Manager singly-linked-list next pointer. |
| `+0x64` | Optional object used by the root collision/service callback. Its concrete type remains open. |
| `+0x68` | Optional owned object released by root cleanup through resident `SUB_001951A0(value, 1)`. |
| `+0x6C` | Handle signalled through resident `SUB_001DDA50` on several terminal/transition paths. |
| `+0x70` | Optional manager/service notification pointer; unlink writes `1` to the pointed byte and clears the pointer. |
| `+0x74` | Pointer to the selected `0x68`-byte config record. |
| `+0x78` | Config index. |
| `+0x7A` | External ID copied from record `+0x00`; parent spawn may overwrite it with the parent's value. |
| `+0x7E` | Common state; value `6` is a proven transition state and value `7` is the manager-removal sentinel. |
| `+0x80`, `+0x81` | Common setup modes/flags selected while binding the record. |
| `+0x82` | Common substate/counter; cleared by the state-6 transition helper. |
| `+0x84` | Common delay/state field used by derived callbacks. No time-unit claim is made. |
| `+0x86` | Manager-linked flag. |
| `+0x87-+0x89` | Common initialization/activation flags. |
| `+0x8A` | Two-valued side tag derived as the inverse of the spawn side argument. |
| `+0x8C` | Monotonic manager serial assigned at insertion. |
| `+0x90-+0x9C` | Second copy of spawn input vector 1. |
| `+0xA0-+0xAC` | Spawn input vector 2; its semantic use varies by derived class. |
| `+0x206` | Enables participation in the manager collision/service pass. |
| `+0x208` | Copy of config byte `+0x14`. |
| `+0x210` | Signed common service/state value; record `+0x21 == 1` sets it to `3`. |
| `+0x1EC` | Common transition scalar; the state-6 handler writes `float(+0x82) / 7.0`. |
| `+0x1F0` | Binder comparison flag: `1` when the two battle-player globals have equal signed halfword `+0x9F6`, otherwise `0`. |
| `+0x200` | Common active-update counter incremented by the root slot-`+0x44` path. |
| `+0x202` | Low byte of signed halfword `+0x9F6` from the opposite-tag battle player selected through object `+0x8A`. |
| `+0x212`, `+0x214` | Signed service IDs obtained from common profile `+0x02/+0x04`; `-1` disables the corresponding call. |
| `+0x216` | Common optional-service flag; cleared by the state-6 transition helper. |
| `+0x218` | Head of an owned heap-node chain drained by root cleanup. |
| `+0x248-+0x250` | Lineage/group tuple; key fields are inherited from a parent projectile. |
| `+0x258` | Copy of config float `+0x0C`, optionally overwritten by the external-ID wrapper's caller-controlled path. |
| `+0x25E` | Binder-complete flag; binder writes `1` after common record setup. |
| `+0x274` | Optional auxiliary heap allocation freed directly by root cleanup. |
| `+0x284`, `+0x288` | Additional metadata copied from a parent projectile. |

## Spawn, side identity, and lineage

Live `0x00736080` accepts:

```text
a0 = config index
a1 = side argument, required to be 0 or 1
a2 = pointer to 16-byte vector 1
a3 = pointer to 16-byte vector 2
t0 = factory/constructor extra argument
t1 = optional parent projectile pointer
```

An `a1` value other than `0` or `1` returns null before allocation. For valid
input, the routine computes `inverse = 1 - a1`, calls the factory, and calls
the binder with both values. The binder writes `inverse` to object `+0x8A`.
The spawn routine copies vector 1 to both `+0x30` and `+0x90`, copies vector 2
to `+0xA0`, then calls virtual slot `+0x54` as post-spawn initialization.
There is no null check between the factory return and the binder/object writes.
Factory branches do check the resident allocator result before calling a
constructor, but a null result reaches this unguarded spawn continuation. The
clean lifecycle therefore assumes allocation succeeds rather than supplying a
recoverable allocation-failure path.

The common side helpers make the relationship exact:

| Live entry | Result for object `+0x8A = 0` | Result for `+0x8A = 1` |
| ---: | --- | --- |
| `0x00734130` | numeric side `1` | numeric side `0` |
| `0x00734160` | battle global `+0xDE8` | battle global `+0xDE4` |
| `0x007341A0` | battle global `+0xDE4` | battle global `+0xDE8` |

Thus `0x007341A0` is the same-tag player lookup and `0x00734160` is the
opposite-tag lookup. A frequent child-spawn pattern passes
`0x00734130(parent)` as the new spawn side; the binder inverts it again, so the
child receives the parent's `+0x8A` tag.

If `t1` is non-null, spawn copies parent `+0x284`, `+0x288`, `+0x24A`,
`+0x24C`, and `+0x250`, and always copies parent external ID `+0x7A`. Before
consulting the manager's four-slot lineage table it requires signed parent
`+0x24A` to be in inclusive range `0..196`; an out-of-range value skips that
table work but not the external-ID copy. Spawn does not retain the parent
pointer in this path. This is strong evidence for inherited source/group
identity. Calling `+0x8A` specifically an owner or target field remains a
medium-confidence interpretation: the exact inversion and lookups are proven,
but no direct owner-pointer field was established.

### Higher-level spawn wrappers

Live `0x00736400` (file `0x082500`, Ghidra display `0x007363C0`) wraps the
common spawn with two floating-point post-parameters. It forwards its incoming
register `t1` as the common spawn's factory extra and incoming `t2` as the
parent pointer. Unlike common spawn itself, it tests the returned object for
null before post-initialization. On success it writes incoming `f12` to object
`+0x1E0`. When record selector `+0x02` is `0x14`
(`ccProjectileHomingDelay`), it additionally calls live
`0x007437D0(object, wrapper-t0)` and converts incoming `f13` to the signed word
stored at `+0x2A8`.

The wrapper has exactly one direct raw-overlay caller, live `0x007F1A90`
(file `0x13DB90`, Ghidra display `0x007F1A50`). That site requests config
`0x17`, whose selector `0x09` constructs `ccProjectileHoming` with resident
vtable `0x005E0390`; it supplies side from caller object `+0x350` and forces
both forwarded factory-extra and parent registers to zero. The caller therefore
uses the ordinary `+0x1E0` write but not the selector-`0x14` special branch, and
the resulting projectile receives no parent lineage.

Live `0x007364D0` (file `0x0825D0`, Ghidra display `0x00736490`) is a related
wrapper. It returns null immediately when its incoming `t0` is null, otherwise
calls common spawn with both factory extra and parent forced to zero and applies
the same `+0x1E0` and selector-`0x14` post-initialization. No direct JAL or
aligned absolute-function-pointer reference to `0x007364D0` exists in the
clean BTL overlay. Its runtime reachability is therefore not established.

### Direct spawn-call inventory

An aligned raw-word scan of the clean overlay finds 87 direct JAL instructions
to live `0x00736080` (instruction word `0x0C1CD820`). Every one is immediately
preceded by an explicit `t1` setup and followed by a NOP delay slot. Only 58 of
the calls appear as instructions in the maintained Ghidra listing; 29 more lie
in ranges that the export rendered as undefined bytes. The raw instruction
shape around all 29 makes the listing omission, rather than coincidental data,
the supported interpretation.

Exactly 25 call sites force `t1 = 0`:

```text
0072DC90 0072DCB8 00736360 00736528 00737AF0
00737C78 0073A2C8 007F0390 007F2910 007F37D4
00804048 0081CA0C 00825824 008261EC 0083A798
0083EA08 00846848 00848CEC 0084B4E8 0084B9BC
00859C14 008602C8 0086BFEC 0088B0A0 0088DA0C
```

The other 62 forward a register or stack-supplied value as `t1` and are thus
parent-capable calls. Sixty-one use a register move; live `0x0073EB48` instead
loads `t1` from stack `+0x120` immediately before the call. These are the exact
live call-site addresses:

```text
00730240 007303FC 00730E18 00730E90 00730F60 0073162C
0073169C 007317D0 007319AC 007328E4 00732950 007329A4
00732A30 00733800 00733858 007338E8 00736450 0073A7A8
0073DA6C 0073DAE0 0073DF20 0073E868 0073EB48 0073EF98
0074260C 00742AC4 007456A4 00745704 007477DC 007478EC
00747AE4 00747C48 00747D54 00748264 00748D24 00749974
0074AEFC 0074B534 0074C32C 0074C844 007500D4 007517E0
007519F8 00753EA4 00754328 00754D30 007551B0 00755640
00756810 00757AE0 00759954 0075A4BC 0075B51C 0075B5D0
0075B91C 0075C9B4 0075CDA0 0075D49C 0075D69C 0075F778
0075F8A0 0075FEA4
```

"Parent-capable" records the ABI value at the call site; it does not assert
that a forwarded value can never be null at runtime. Several representative
class callbacks do prove the intended linked-child use:

- Live `0x007303FC` spawns config `0x2E`, passes
  `0x00734130(current)` as `a1`, and passes the current projectile as `t1`.
  Spawn's second inversion preserves the current object's `+0x8A`, and the
  non-null parent path copies its lineage.
- Live `0x0073162C` and `0x0073169C` spawn configs `0x66` and `0x67`. Each
  computes `a1 = current +0x8A XOR 1` and passes the current projectile as
  `t1`, which has the same same-tag and lineage-preserving result.
- Live `0x0072DC90` and `0x0072DCB8`, in the common slot-`+0x24` callback,
  deliberately pass `t1 = 0` and pass the current object's `+0x8A` directly as
  `a1`. The first handles current config `0x6F` by spawning config `1`; the
  second uses the current config index otherwise. Because the binder inverts
  that direct tag, the new object gets the opposite `+0x8A`, and because `t1`
  is null it receives none of the parent-copy fields. This is a concrete
  unlinked/opposite-tag emission path, distinct from the linked-child pattern.

The raw-only call sites missing from the Ghidra instruction listing are live
`0x007319AC`, `0x00732950`, `0x007329A4`, `0x00733800`, `0x00733858`,
`0x007338E8`, `0x0073A7A8`, `0x0073DA6C`, `0x0073DAE0`, `0x0073E868`,
`0x0073EB48`, `0x0074AEFC`, `0x007500D4`, `0x007517E0`, `0x00753EA4`,
`0x00754328`, `0x00754D30`, `0x007551B0`, `0x00755640`, `0x00756810`,
`0x00757AE0`, `0x0075C9B4`, `0x0075CDA0`, `0x0075D69C`, `0x0075FEA4`,
`0x00848CEC`, `0x0084B9BC`, `0x00859C14`, and `0x0086BFEC`. This is also a
negative result for relying on exported listing XREF counts as complete.

## Manager ownership, callbacks, and cleanup

The global manager pointer is the GP-relative symbol `iGpffffce30`
(`gp - 0x31D0`). Its creation body at live `0x00735E70` allocates `0xD0`
bytes and calls constructor `0x007343A0`. Teardown begins at live
`0x00735F30`.

The relevant manager fields are:

| Manager offset | Role |
| ---: | --- |
| `+0x0C` | Active list count. |
| `+0x10` | Monotonic insertion serial source. |
| `+0x14` | List head. |
| `+0x18` | List tail. |
| `+0x1C` | Optional shared collision/service object. |
| `+0x20` | Suppresses the main update pass when nonzero. |
| `+0x21` | Suppresses the collision/service pass when nonzero. |
| `+0x64` onward | Two groups of four `0x0C`-byte lineage/dedup slots. |

After construction and post-spawn initialization, live `0x00736080` appends
the object only when object `+0x86 != 1`; an already-linked object skips the
insertion block. Insertion repairs `+0x14/+0x18`, writes object `+0x86 = 1`,
assigns the old manager serial to object `+0x8C`, and increments manager
`+0x10` and `+0x0C`. If manager `+0x1C` and object `+0x70` are both non-null,
the same block calls live `0x00708570(manager+0x1C, object+0x70)` to register
the optional notification/helper.

### Serial identity helpers

Live `0x00735F90(serial)` returns the first list object whose word `+0x8C`
matches, or null if the manager/list has no match. Live `0x00735FE0(serial)`
implements the complementary lifecycle predicate: it returns `0` only when a
matching object exists in a state other than `6` or `7`; it returns `1` when
the manager or serial is absent, or when the match is already in transition
state `6` or removal state `7`. These helpers prove that manager serial `+0x8C`
is a public object identity distinct from config index `+0x78` and external ID
`+0x7A`.

### Main update/removal interface

Live `0x00734BA0` walks from manager `+0x14` through object `+0x60`. For each
object it saves the next pointer, calls common pre-work at live `0x0072C8B0`,
then calls virtual slot `+0x44`. The root `ccProjectile` vtable maps that slot
to live `0x0072C940`.

### Activation gate before the survival/update callback

The common pre-work makes activation a distinct list-managed phase. When byte
`+0x89` is zero and signed halfword `+0x84` is nonpositive, live `0x0072C8B0`
writes `+0x89 = 1`. Unless common state `+0x7E` is already `6` or `7`, it then:

1. calls record-`+0x09` activation entry `0x0072D010`, which signals `+0x6C`,
   calls virtual `+0x2C`, performs the orientation dispatch documented above,
   writes state `2`, and clears helper `+0x70` byte `+0x01` when present;
2. clears signed halfword `+0x84`;
3. invokes virtual slot `+0x50` (the root target `0x0072B480` is a no-op);
4. calls optional positional-service setup `0x00734030`, where record
   `+0x2C == -1` disables construction.

The pre-work clears byte `+0x1F1` on every exit. Root slot `+0x44` has a
complementary gate: while signed `+0x84` is positive, it decrements that field
and returns survival value `1` without entering the state dispatcher or the
later virtual callbacks. These are ordering and counter facts only; no
real-time unit is assigned.

A zero return from slot `+0x44` causes:

1. live `0x00734AD0` to unlink the object, repair head/tail or predecessor
   links, clear object `+0x86`, decrement manager `+0x0C`, and signal/clear
   object `+0x70`;
2. a deleting-destructor call through virtual slot `+0x08` with argument `1`.

The base `ccProjectile` deleting destructor is live `0x0072B800`; subclasses
override it where required. Manager-wide cleanup at live `0x007349C0` repeats
the unlink/deleting-destructor sequence for every remaining list entry, then
releases the shared service. Manager teardown at `0x00735F30` invokes that
cleanup and frees the manager itself.

More exactly, manager-wide cleanup repeatedly takes the current tail, calls
live `0x00734AD0`, and invokes virtual deleting slot `+0x08` with argument `1`;
because unlink repairs `+0x18` to the predecessor, this drains the singly
linked list tail-to-head and includes the final head. It then calls live
`0x00734F80`, which releases and clears each non-null entry of a separate
19-pointer global service array at live `0x008EA830` through resident
`SUB_001951A0(value, 1)`. Non-null manager `+0x1C` is released through live
`0x00708480(value, 1)` and cleared, and live `0x00734470` zeroes the manager's
list/count/serial/gate fields. The teardown entry additionally destroys the
embedded manager member at `+0x2C` through resident
`SUB_001C4410(member, -1)`, frees the `0xD0`-byte manager, and clears the
GP-relative global pointer.

The root deleting destructor installs resident vtable `0x005E0810`, calls root
resource cleanup live `0x0072B880`, then calls lower-object destructor
`0x00709B60(object, 0)` and frees the object through resident
`SUB_00117000` only when its deleting flag is positive. Root resource cleanup
has the following exact ownership behavior:

- non-null `+0x64` is released through resident `SUB_001951A0(value, 1)` when
  mode byte `+0x80` is `1` or `3`, or through resident
  `SUB_001B7570(value, 1)` when the mode is `2` or `4`, then cleared;
- non-null `+0x274` is freed directly through `SUB_00117000` and cleared;
- non-null `+0x6C` is first signalled through `SUB_001DDA50`, then released
  through `SUB_001DD920(value, 1)` and cleared;
- non-null `+0x68` is released through `SUB_001951A0(value, 1)` and cleared;
- live `0x0072B9B0` writes `1` to byte zero of non-null helper `+0x70` and
  clears the object field without directly freeing the helper;
- live `0x0072FB10` walks the singly linked heap-node chain rooted at `+0x218`,
  preserves each node's word-zero next pointer before freeing it through
  `SUB_00117000`, and finally clears the head;
- live `0x0072B4A0` resets the common record/state fields, including config
  pointer `+0x74`, config/external IDs `+0x78/+0x7A`, state `+0x7E`, manager
  linkage `+0x60/+0x86`, serial `+0x8C`, and auxiliary pointers.

The non-null `+0x64` modes outside `1..4` lead to a deliberate null-address
store in the clean code. That is evidence of an invariant/assert-like invalid
mode path, not a recoverable cleanup case.

### Collision-facing interface

Live `0x00734D30` is gated by manager byte `+0x21`. It walks the same list and,
for each object whose byte `+0x206` is nonzero, invokes virtual slot `+0x48`
with argument `1`. Root `ccProjectile` slot `+0x48` is live `0x0072CDA0`.
The pass establishes and restores a shared resident collision context and
finishes by servicing manager `+0x1C`.

Live `0x00735E30` sets manager `+0x21`; live `0x00735E50` clears it. The
parallel update-pass gate `+0x20` is set/cleared by live `0x00735DF0` and
`0x00735E10`.

This establishes the projectile-to-collision interface without assigning
meanings to the collision engine's internal structures.

The representative query wrapper at live `0x00757B60` is deliberately thin.
It preserves caller arguments `a0` and `a1` (pointers to two 16-byte vectors)
and `a2` (a 32-bit filter/mask), sets the remaining resident-call arguments to
`a3 = 1`, `t0 = 0`, and `t1 = -1`, calls resident `SUB_001BF100`, and returns
its floating-point result unchanged. The Tonton callers below prove `-1.0f` as
the no-result sentinel for their masks. The resident routine's internal shape,
world, and contact semantics are intentionally not decoded here.

The wrapper has exactly 13 direct raw-overlay callers. All 13 contain an
explicit comparison path against `-1.0f`; `ccProjCharNRWOtherSelf` also applies
another numeric threshold before its sentinel branch. The complete class-facing
inventory is:

| Class / resident vtable | Reaching callback or helper | Query call site(s), live → mask |
| --- | --- | --- |
| `ccProjLauncherDDRFire` / `0x005DF1F0` | slot `+0x44`, live `0x00757820` | `0x007579D4` → `0x20000001`; `0x00757A28` → `0x40000000` |
| `ccProjSIWTrap` / `0x005DF190` | slot `+0x3C`, live `0x00757C60` | `0x00757CCC` → `0x20000001` |
| `ccProjTewSkillAnki` / `0x005DEF20` | slots `+0x1C` (`0x00759A70`) and `+0x28` (`0x00759E40`) reach shared helper `0x0075A0B0` | `0x0075A3EC` → `0x40000001`; `0x0075A450` → `0x20000001` |
| `ccProjExcORWSnake` / `0x005DEB60` | slot `+0x1C`, live `0x0075BC90`, including helper `0x0075C640` | `0x0075C0A0` → `0x40000001`; `0x0075C66C` → `0x20000001` |
| `ccProjCharNRWOtherSelf` / `0x005DE6D0` | slot `+0x64`, live `0x0075EB70`, reaches helper `0x0075ECE0` | `0x0075EDF8` → `0x40000001` |
| `ccProjCharSZWBuddyTonTon` / `0x005DE660` | slot `+0x64`, live `0x0075F340` | `0x0075F3EC` → `0x20000001`; `0x0075F430` → `0x40000001`; `0x0075F494` → `0x20000001` |
| `ccProjSZWExcItemTonton` / `0x005DE350` | slot `+0x64`, live `0x00760950` | `0x00760A9C` → `0x20000001`; `0x00760CDC` → `0x40000001` |

The mask distribution is seven calls with `0x20000001`, five with
`0x40000001`, and one with `0x40000000`. Raw call sites `0x007579D4`,
`0x00757A28`, and `0x0075C0A0` are in ranges omitted as instructions from the
Ghidra listing, another reason to derive call counts from the clean binary.
The inventory establishes filter values and class ownership only; it does not
name the resident query's internal collision categories.

The root slot-`+0x48` implementation at live `0x0072CDA0` makes that interface
more precise. It returns `1` in all observed paths and skips service work when
`+0x84` is positive, `+0x89` is zero, or state `+0x7E` is below `2`. Otherwise:

1. The manager's argument value `1` enables common transient-entry setup at
   live `0x0072CB50`.
2. If object `+0x64` is null, the callback chooses signed service ID `+0x212`
   or `+0x214` according to common state. A non-`-1` ID is submitted to live
   `0x00735680` together with scalar `+0x1EC`, transform storage at `+0x100`,
   and a zero final argument.
3. If object `+0x64` is non-null, mode byte `+0x80` selects the resident
   service call: modes `1`/`3` use `SUB_00194180(1.0f)`, while modes `2`/`4`
   use `SUB_001BB790`.
4. Common post-service entry live `0x0072FE40` runs last.

This also ties record `+0x04` and its common profile directly to the
projectile-facing collision/service path without assigning an internal shape
or engine type to `+0x64`.

### Representative callback composition

Comparing resident vtables against root `ccProjectile` vtable `0x005E0810`
shows that motion/state strategies replace selected callbacks rather than a
single universal "motion" slot. The following are every non-root target in
slots `+0x1C` through `+0x58` for seven representative clean selectors; all
unlisted slots in that range retain the root target:

| Root slot | Root live target |
| ---: | ---: |
| `+0x1C` | `0x0072E020` |
| `+0x20` | `0x0072E240` |
| `+0x24` | `0x0072D200` |
| `+0x28` | `0x00733080` |
| `+0x2C` | `0x00732FD0` |
| `+0x30` | `0x00730140` |
| `+0x34` | `0x007305A0` |
| `+0x38` | `0x00730120` |
| `+0x3C` | `0x00731F80` |
| `+0x40` | `0x00734280` |
| `+0x44` | `0x0072C940` |
| `+0x48` | `0x0072CDA0` |
| `+0x4C` | `0x0072C2A0` |
| `+0x50` | `0x0072B480` |
| `+0x54` | `0x0072B490` |
| `+0x58` | `0x007305F0` |

| Selector / exact class | Non-root slot → live target |
| --- | --- |
| `0x00` / `ccProjectileStraight` | `+0x1C` → `0x00738E40` |
| `0x03` / `ccProjDist2Speed` | `+0x1C` → `0x007392E0`; `+0x30` → `0x00739170`; `+0x54` → `0x00739260`; `+0x58` → `0x00739630` |
| `0x01` / `ccProjectileChase` | `+0x1C` → `0x0073B060`; `+0x20` → `0x0073BD20`; `+0x30` → `0x0073AA30`; `+0x3C` → `0x0073AB70`; `+0x40` → `0x0073C6D0`; `+0x48` → `0x0073C060`; `+0x4C` → `0x0073BF60`; `+0x50` → `0x0073C220` |
| `0x09` / `ccProjectileHoming` | `+0x1C` → `0x0073F6C0`; `+0x30` → `0x0073FCC0`; `+0x50` → `0x0073F610` |
| `0x14` / `ccProjectileHomingDelay` | `+0x1C` → `0x00743A00`; `+0x30` → `0x00743800`; `+0x48` → `0x007438E0`; `+0x54` → `0x00743770` |
| `0x15` / `ccProjectileParabola` | `+0x1C` → `0x00744820`; `+0x3C` → `0x00745390`; `+0x54` → `0x007458D0` |
| `0x0F` / `ccProjectileExplosion` | `+0x44` → `0x00741970` |

The invocation points that are proven globally are narrower than the class
names: spawn calls `+0x54`; the manager calls `+0x44`; the collision pass calls
`+0x48`; root active update calls `+0x20` and `+0x4C`; and common state `2`
dispatch calls `+0x24`. Other slots above are retained as exact interface
addresses without a universal semantic label.

The root `+0x20` target at live `0x0072E240` dispatches record `+0x09` values
`0..7` to orientation/transform helpers; its default branch builds matrix
storage at `+0x140..+0x170` from angles at `+0xE0`. This is why calling every
`+0x20` implementation simply a position integrator would be incorrect.
`ccProjectileChase` replaces it with live `0x0073BD20`: in common states `2`
and `5`, that body sets `+0x216 = 1` and updates angle `+0xE8` using signed
halfword `+0x204`, scalar `+0x278`, and explicit pi/32768 quantization. The body
does not directly write position `+0x30`; Chase's own slot-`+0x4C` target at
live `0x0073BF60` consumes `+0xE8` while building matrix storage at `+0x100`
and anchors that transform to position `+0x30`. In contrast, common state `5` is a proven
direct integrator because its handler adds vector `+0x1C0` to position `+0x30`
on each invocation. No invocation is equated to a frame or real-time duration.

`ccProjectileExplosion` demonstrates a real class-specific state contract. Its
live `+0x44` body returns `0` immediately for state `7`; for state `6` it writes
state `7` and returns `1`. Thus an explosion already placed in state `6`
transitions on that callback and is removed on a later manager callback, without
using common state-6 handler `0x0072E180`. When common counter `+0x200` is zero,
the same body also calls its virtual `+0x2C` entry and resident
`SUB_001D87C0(0x1000, object+0x30)`. No cadence or damage meaning is assigned.

## Hit and despawn evidence

### State-6 transition helper

The common state-6 helper at live `0x00730950` has the following complete
observable side effects in the raw clean body:

```text
object + 0x7E = 6
object + 0x82 = 0
SUB_001DDA50(*(object + 0x6C))
if (*(object + 0x70) != null):
    **(object + 0x70) = 1
    *(object + 0x70) = null
object + 0x216 = 0
SUB_00340170(object + 0x30, 0, 0)
SUB_001D87C0(0x0E, object + 0x30)
```

The meanings of the last two resident services are not assigned here. Their
exact arguments establish that both are associated with the projectile's
current position. The helper does not unlink or free the object.

There are 12 direct raw-overlay JAL sites to `0x00730950`. Their containing
common or virtual callback bodies are:

| Containing body (live) | Vtable association | Direct call sites (live) |
| ---: | --- | --- |
| `0x0072D200` | Common/root slot `+0x24` state-processing body | `0x0072DEE4` |
| `0x0074F690` | `ccProjTest` slot `+0x64` | `0x0074F9D8`, `0x0074FB64` |
| `0x00751F50` | `ccProjCharNRW` slot `+0x64` | `0x00751FE8` |
| `0x00758080` | `ccProjSIWTrap` slot `+0x58` | `0x007580E4` |
| `0x00759640` | `ccProjLauncherTewAnki` slot `+0x1C` | `0x0075969C` |
| `0x007596E0` | `ccProjLauncherTewAnki` slot `+0x5C` | `0x007596F0` |
| `0x0075F340` | `ccProjCharSZWBuddyTonTon` slot `+0x64` | `0x0075F3B4`, `0x0075F410`, `0x0075F454` |
| `0x00760950` | `ccProjSZWExcItemTonton` slot `+0x64` | `0x00760A40`, `0x00760D10` |

This inventory is a call-graph fact, not a claim that every site represents
the same kind of collision or gameplay event.

### State `6` to manager destruction

Root slot-`+0x44` callback `0x0072C940` consults live state dispatcher
`0x0072CF50`. The dispatch table is live `0x008C4AE0` / file `0x210BE0`.
All eight in-range entries are exact:

| State | Dispatch target | Proven result |
| ---: | ---: | --- |
| `0` | `0x0072CFF4` | Dispatcher returns `0`; no state-specific call. |
| `1` | `0x0072CF84` | Executes a deliberate null-address store, then reaches dispatcher return `0`; this is an invalid/assert-like path, not a normal state implementation. |
| `2` | `0x0072CF90` | Calls virtual slot `+0x24`, then dispatcher returns `0`. |
| `3` | `0x0072E030` | Calls live `0x00730110`. If that returns zero, detaches `+0x70`, signals `+0x6C`, and writes state `7`. Handler returns `1`, but dispatcher returns `0`. |
| `4` | `0x0072E0A0` | Decrements `+0x82`; when its old value is nonpositive, writes state `6`, resets `+0x82 = 7`, and clears the 16-byte blocks at `+0x1C0` and `+0x1D0`. Dispatcher returns `0`. |
| `5` | `0x0072E0E0` | Adds vector `+0x1C0` to position `+0x30`, writes `+0x1EC = float(s16(+0x82)) / 7.0`, and decrements `+0x82`; when the old value is nonpositive, signals `+0x6C`, writes state `7`, and detaches `+0x70`. Dispatcher returns `0`. |
| `6` | `0x0072E180` | Writes `+0x1EC = float(s16(+0x82)) / 7.0`, decrements `+0x82`, and, when the old value is nonpositive, signals `+0x6C` and writes state `7`. It returns `1` to its caller, but the dispatcher itself returns `0` for this case. |
| `7` | `0x0072CFE8` | The dispatcher returns `1`; root slot `+0x44` converts this to survival result `0`. |

An object state outside unsigned range `0..7` also reaches dispatcher return
`0`. The labels above describe only raw side effects and call relationships;
they do not assign design names or time units to states `0..5`.

Because `0x00730950` sets `+0x82 = 0`, the next state-6 dispatch necessarily
writes `+0x82 = -1` and promotes the object to state `7`. That slot-`+0x44`
invocation still returns survival result `1`. A subsequent invocation observes
state `7`, returns zero, and lets manager `0x00734BA0` perform unlink and the
deleting-destructor call. This sequence is expressed in callback invocations;
no frame-rate or real-time cadence is inferred.

### Direct out-of-bounds removal

The root slot-`+0x44` body has a second proven removal path independent of the
state-6 helper. After its state and virtual callbacks, it evaluates a resident
comparison derived from coordinate `+0x30` and constant `2500.0`, then directly
tests coordinate `+0x34` against `1500.0` and `-3000.0`, and coordinate `+0x38`
against `3500.0` and `-500.0`. A failing test signals handle `+0x6C` and writes
state `7` at live `0x0072CB14-0x0072CB18`. That invocation still returns `1`;
a later manager update observes state `7` and removes the object through the
normal unlink/destructor contract. The exact transform or comparison applied
to `+0x30` by the resident helpers is not named here.

On its continuing active path the same callback adds float `+0x278` to
accumulator `+0x1FC` and increments signed halfword `+0x200`. These are callback
counts/accumulation facts only, not frame or time-unit claims.

`ccProjSZWExcItemTonton` provides a concrete end-to-end example. Its resident
vtable `0x005DE350` has:

| Slot | Live target | Role established here |
| ---: | ---: | --- |
| `+0x00` | `0x008C8420` | Exact `ccProjSZWExcItemTonton` class handle. |
| `+0x08` | `0x007637F0` | Deleting destructor. |
| `+0x44` | `0x0072C940` | Shared manager survival/update callback. |
| `+0x48` | `0x0072CDA0` | Shared collision/service callback. |
| `+0x50` | `0x00760760` | Derived setup/state callback. |
| `+0x64` | `0x00760950` | Derived motion/impact callback. |
| `+0x68` | `0x007606B0` | Derived setup/resource callback. |

The slot-`+0x64` body is at Ghidra display `0x00760910` / file offset
`0x0ACA50`. It consumes object state including `+0x84`, performs projectile
position work, calls the collision-query interface at live `0x00757B60`, and
calls state-6 helper `0x00730950` on the proven impact branches. No claim is
made about call cadence, real-time duration, or damage.

Two related classes expose concrete projectile-facing query conventions:

- `ccProjCharSZWBuddyTonTon` slot `+0x64` at live `0x0075F340` first calls
  common predicate `0x0074DF10`; low byte `1` enters state `6`. It then submits
  position pairs to `0x00757B60` using masks `0x20000001` and `0x40000001`.
  For each of those two termination branches, a result other than `-1.0f`
  enters state `6`; `-1.0f` is therefore the proven no-result sentinel.
- `ccProjSZWExcItemTonton` slot `+0x64` at live `0x00760950` uses the same
  common predicate and masks. Its first `0x20000001` result feeds a continuing
  response path. A later `0x40000001` result other than `-1.0f`, or a local
  one-byte condition established earlier in the callback, enters state `6` at
  live `0x00760D10`. The local condition's game-design meaning is left open.

These masks and sentinel are documented as the class-facing collision-query
contract; no internal collision shape or damage meaning is inferred.

The resulting lifecycle is therefore a staged one: derived collision/motion
logic enters state `6` and performs position-associated cleanup; the common
state handler promotes it to state `7`; the common update contract later
returns the removal decision; the manager unlinks; the class destructor
releases derived resources; and the general allocator finally reclaims the
object.

## Limits and pooling

No hard simultaneous-projectile cap is checked in the traced spawn/register
path. Successful construction appends to the linked list and increments the
active count. Constructors use resident general allocator `SUB_00117150`, and
deleting destructors ultimately use resident `SUB_00117000`. No projectile
object free-list or object-reuse pool was found in this path.

There is a distinct bounded four-slot mechanism, but it is not an object pool.
The record address is:

```text
manager + 0x64 + side * 0x30 + slot * 0x0C,  slot = 0..3
```

Each record contains an unsigned 16-bit age at relative `+0x00`, a signed
16-bit key at `+0x02`, a word key at `+0x04`, and a byte flag at `+0x08`.
Live `0x00735CA0` returns zero when the `+0x02/+0x04` key pair already exists
in the selected four-slot group and one when it is absent; the flag is not part
of duplicate comparison. Live `0x00735D20` uses the first record whose signed
key is `-1`, or, when all four are occupied, replaces the record with the
largest unsigned age. It clears the record, resets age to zero, and writes the
new key pair and input flag.

Live `0x00735B70` is the matching age/consume interface. On each invocation it
increments the unsigned age of every occupied record in the selected group.
For a record matching the supplied key pair whose byte flag is zero, it calls
live `0x00715F90(side + 1, 0, 1)` and changes the flag to one. Its sole direct
caller is live `0x0072EB88` in common projectile contact-response logic; that
caller supplies projectile `+0x24A/+0x24C` after a side-tag check. This records
the interface and side effects without assigning damage semantics to the
resident call.

Parent spawn consults lookup/insertion while inheriting
`+0x24A/+0x24C/+0x250`; common setter `0x0072EC30` can register the same tuple
directly. The table group is selected with `0x00734130(projectile)`, the
numeric inverse of object tag `+0x8A` and therefore the original spawn-side
value. Duplicate detection suppresses only another table insertion: it does
not cancel projectile construction or manager-list insertion. This is a
bounded lineage/dedup/age/replacement table, not evidence of a four-projectile
cap.

Limits imposed by callers or unrelated systems were not established. The
traced path does establish that factory branches can return null after resident
allocator failure but spawn does not guard that result before binding and
dereferencing it; no graceful allocation-failure policy exists in this chain.
The negative cap/pool claim is limited to the traced manager and factory path.

## Class family

The clean overlay contains a contiguous custom-RTTI family of 99 descriptors
whose exact names begin `ccProj` or `ccProjectile`, including the root. Each
descriptor begins with common pointer live `0x008C2328`; derived descriptors
carry base-class handles, then a class-name pointer and a self descriptor
pointer. Resident vtable slot `+0x00` points at the applicable class handle,
which is how the factory examples above were identified without relying on
string proximity.

Representative exact relationships are:

| Class | Descriptor | Handle | Direct handles present in descriptor |
| --- | ---: | ---: | --- |
| `ccProjectile` | `0x008C8340` | `0x008C8350` | root |
| `ccProjChar` | `0x008C83E0` | `0x008C83F8` | `ccProjectile` |
| `ccProjectileHoming` | `0x008C8750` | `0x008C8768` | `ccProjectile` |
| `ccProjSNWCmbULauncher` | `0x008C8770` | `0x008C8790` | `ccProjectile`, `ccProjectileHoming` |
| `ccProjectileParabola` | `0x008C87C0` | `0x008C87D8` | `ccProjectile` |
| `ccProjectileNumbness` | `0x008C87E0` | `0x008C8800` | `ccProjectile`, `ccProjectileParabola` |
| `ccProjLauncher` | `0x008C8910` | `0x008C8928` | `ccProjectile` |
| `ccProjectileChase` | `0x008C8C20` | `0x008C8C38` | `ccProjectile` |
| `ccProjectileNrwCombo` | `0x008C8C40` | `0x008C8C60` | `ccProjectile`, `ccProjectileChase` |
| `ccProjSpecifyParam` | `0x008C8D00` | `0x008C8D18` | `ccProjectile` |
| `ccProjLunLinear` | `0x008C8D20` | `0x008C8D40` | `ccProjectile`, `ccProjSpecifyParam` |
| `ccProjBound` | `0x008C8E60` | `0x008C8E78` | `ccProjectile` |
| `ccProjBakutiBall` | `0x008C8E80` | `0x008C8EA0` | `ccProjectile`, `ccProjBound` |
| `ccProjectileStraight` | `0x008C9130` | `0x008C9148` | `ccProjectile` |

Other strongly identified strategy/base names include
`ccProjDist2Speed`, `ccProjectileHomingDelay`,
`ccProjectileExplosion`, `ccProjHomingScatter`,
`ccProjSoundWave`, and `ccProjectileInsectLauncher`. The names establish
developer-authored class intent; they do not by themselves prove the detailed
behavior of every subclass.

## Confidence, hypotheses, and negative results

### High confidence

- Complete-file live overlay mapping and the `+0x40` Ghidra/export correction.
- Config-table address, `0x68` stride, `0xB6` count, selector byte, external-ID
  field, real jump-table address, and first-match ID wrapper.
- Factory-to-constructor-to-vtable-to-descriptor identity for the five listed
  `ccProjChar` records.
- Spawn vector writes, post-spawn virtual call, parent metadata inheritance,
  manager insertion, serial/count changes, update/collision virtual slots,
  unlinking, deleting destruction, and manager-wide cleanup.
- Exact `+0x8A` inversion and same/opposite player lookups.
- State-6 helper writes, state-6-to-7 promotion, direct state-7 culling, and
  the concrete Tonton collision-to-removal call chains.
- Absence of a cap check or reusable-object free list in the traced spawn and
  manager path; separation of the four-slot lineage table from object storage.

### Medium-confidence interpretation

- Object `+0x8A` most likely denotes source/owner side and the spawn `a1`
  argument the opposing/target side. Child-spawn inversion and lineage
  preservation support this, but the static code does not name either role.
- Spawn vector 1 is a position. Vector 2 is an aim, destination, direction, or
  related input depending on subclass; no single stronger label fits all
  inspected consumers.
- The handle at `+0x6C` participates in state/effect notification. Its exact
  owned type is not identified here.

### Explicitly not established

- No direct owner pointer or target pointer was proven in the common object.
- No universal meaning is assigned to every config field, state value, or
  virtual slot beyond the observed callers and side effects above.
- No global maximum active-projectile count, allocation-failure policy, or
  object pool was proven.
- The separate `ccSkillThrowProjectile` skill hierarchy was not conflated with
  the `ccProjectile` entity hierarchy; a direct factory link was not established
  in this pass.
- No runtime acceptance, collision-shape semantics, damage behavior, timing,
  animation-rate, or rendering behavior was tested or inferred.
