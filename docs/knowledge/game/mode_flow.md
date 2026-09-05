# Resident front-end and mode flow

This note maps the resident `SLPS_258.37` controller from the opening/title
loop through Mode Select and the BTL/ETC handoff boundary. It deliberately
stops at the overlay interface: overlay loading internals and overlay-local
gameplay/UI behavior are not covered.

Adventure is out of scope and is omitted from the dispatcher, result, and
overlay-selector tables below. Only table shapes that also govern BTL/ETC are
retained. Save/load UI, layout, media, localization, timing, and PCSX2 behavior
are also out of scope.

## Research coverage

- **Assigned scope:** the clean resident `SLPS_258.37` front-end controller,
  from the opening/title handoff through New Game/Continue preparation, Mode
  Select, in-scope BTL modes 2/3, ETC modes 5/6, resident mode 7, the overlay
  handoff interface, and resident return/result routing. Persistent mode/state
  globals and callback dispatch were included where their roles could be
  proven.
- **Exploration depth:** overall coverage is **bounded**, not global
  or overlay-exhaustive. Within the resident boundary, the top-level switches
  and direct state/result writers were exhaustively enumerated for
  `FUN_001e0ee0`, `FUN_001e9980`, `FUN_001e9c00`, `FUN_001e9eb0`,
  `FUN_001ea240`, the selector chain `FUN_001f3d10`, `FUN_001f3dc0`,
  `FUN_001f4360`, `FUN_001f45b0`, `FUN_001f4680`, the BTL wrappers
  `FUN_001ea8c0`/`FUN_001ea940`, and the ETC/resident wrappers
  `FUN_001ec300`, `FUN_001ec690`, `FUN_001ec7a0`, `FUN_001ec890`, and
  `FUN_001ec960`. The resident callback subset at `FUN_003839e0`,
  `FUN_00383db0`, `FUN_00384570`, `FUN_003845d0`, `FUN_00384620`,
  `FUN_00384690`, `FUN_00384700`, `FUN_00384720`, `FUN_00384760`,
  `FUN_003849c0`, `FUN_00384cd0`, `FUN_00384d70`, `FUN_00384de0`, and
  `FUN_003854f0` was followed only through the state transitions relevant to
  this scope. Title functions `FUN_001de840`/`FUN_001df690` and subordinate
  allocators/helpers were **sampled** only far enough to prove their controller
  contracts. Direct clean-binary anchors checked included result table
  `0x005D51D0`, filename table `0x004049E0`, default bindings `0x005C06A0`,
  BTL process table `0x005D9F98`, remembered slot `0x006045E0`, and the two
  resident hook seams documented below.
- **Confirmed coverage:** the nested controller phases and result
  contracts; title-to-manager boundary; manager fields and object lifetimes;
  numeric Mode Select mapping, input priority, confirmation/back routing,
  remembered-slot behavior, allocator/failure edges, and unsupported states;
  the synchronous selector/cache contract; BTL type/process selection, hook
  and return convergence; ETC Collection plus resident Options creation,
  teardown, and return behavior; and the resulting patch surfaces and
  lifetime constraints.
- **Unresolved or untested:** original source names for stripped
  fields; the semantic roles of `0x006077AC` and BTL process offset `+0x10`;
  allocation-failure and malformed-state behavior at runtime; loader failure
  semantics; overlay-local BTL/ETC behavior beyond the fixed handoff calls; and
  dynamic confirmation of the static control-flow model.
- **Deliberate exclusions and overlap:** the excluded third
  mode/overlay, Save/Load child UI, overlay binary-loading internals, and deeper
  battle, stage, outcome, support, pause, and profile-serialization mechanics
  belong outside this note or to the linked canonical documents. Layout and
  widescreen work, media, localization, timing, and PCSX2 are also excluded.
- **Evidence limitations:** evidence is static against the exact clean ELF identity
  and the Ghidra 12.1.2 C/listing exports. Direct bytes, tables, calls, and
  state/result writers were cross-checked, but no emulator/game execution,
  injected hook, forced allocation failure, corrupted state, or modified
  overlay was exercised. Addresses and resident control flow therefore have
  stronger support than user-facing semantic labels that depend on stock order
  or existing canonical runtime evidence.

## Evidence and conventions

The observations below come from static inspection of the clean resident ELF.
Its identity and address conversion follow
[Standard game file identities](files/file_identities.md). The
decompiler and listing are the Ghidra 12.1.2 exports under
`@disassembly/NA2/exports/SLPS_258.37/`; later BSS globals have runtime
addresses but no corresponding file bytes.

The executable is stripped. Names such as `FUN_001e9980` and
`DAT_005d51d0` are Ghidra labels, not recovered source identifiers. Literal
RTTI/type strings such as `ccGbtlProcess` are identified separately as original
names preserved in the binary.

Unless marked otherwise, a statement is a direct static observation with high
confidence. “Inference” identifies a role derived from call order or state
transitions. No new runtime validation was performed for this note. Two field
names below explicitly reuse existing runtime evidence from
[Practice-mode architecture](../gameplay/practice_mode.md), and the
synchronous overlay-call contract is cross-checked against the established
[overlay ABI](../runtime/overlay_abi.md).

## Controller hierarchy

The resident flow has three nested levels:

```text
FUN_001e0ee0 outer loop
  state 2: opening controller
  state 3: title controller
  state 4: persistent front-end/profile manager (FUN_001e9980)
             manager phase 2/3: New Game / Continue preparation
             manager phase 4: callback dispatch by manager +0x0C
               mode 1: resident Mode Select
               modes 2/3: BTL handoff
               modes 5/6: ETC handoff
               mode 7: resident Options controller
```

The outer loop is not a callback table. The manager's `+0x0C` field is the
actual high-level mode callback selector.

### Resident globals used by this flow

These addresses are resident globals; object lifetimes differ even though the
pointer slots themselves survive overlay replacement.

| Runtime address | Ghidra label/alias | Proven role |
| ---: | --- | --- |
| `0x006045E0` | `DAT_006045e0`, `uGpffff9bf0` | Signed halfword containing remembered physical Mode Select slot |
| `0x006073FC` | `iGpffffca0c`, `iRam006073fc` | Pointer to the `0x530`-byte system/input context containing controller-port records 0 and 1, `0x78` bytes apart |
| `0x006075C0` | `piGpffffcbd0` | Pointer to eight-byte outer opening/title/front-end state |
| `0x006075C4` | `iGpffffcbd4` | Pointer to `0x48`-byte title controller |
| `0x006075F8` | `uRam006075f8` | Pointer to the outer loop's `0x2400`-byte live profile/save object; borrowed by manager `+0x04` |
| `0x00607600` | `iGpffffcc10`, `iRam00607600` | Pointer to persistent `0xDF8` front-end/profile manager |
| `0x00607608` | `uRam00607608` | In-process vibration-mask cache copied into a new live profile and copied back at manager teardown |
| `0x0060760C` | `puGpffffcc1c`, `piGpffffcc1c` | Pointer to shared `0x14`-byte per-callback transient state |
| `0x00607610` | `iGpffffcc20` | Pointer to `0xD4`-byte Mode Select controller |
| `0x00607614` | `iGpffffcc24` | Pointer to mode-6 ETC handoff object |
| `0x00607618` | `iGpffffcc28` | Pointer to mode-5 ETC handoff object |
| `0x0060761C` | `iGpffffcc2c` | Pointer to mode-7 resident object |
| `0x00607620` | `iRam00607620` | Pointer to shared `0x44`-byte BTL process |
| `0x00607624` | `iGpffffcc34` | Pointer to a shared `0x28`-byte resident gate controller used by Continue and Mode Select back routing |
| `0x00607670` | `uRam00607670`, `iGpffffcc80` | Resident BTL route code; accessors `FUN_001ec270/001ec280`, with value 7 converging on the front-end return path |
| `0x006077AC` | `uGpffffcdbc` | Auxiliary word cleared by Mode Select back; wider semantic role unknown |

### Allocation lifetimes

- `FUN_001e0ee0` allocates the eight-byte outer object and the `0x2400`-byte
  live profile object once before entering its non-returning state loop. The
  latter is initialized through `FUN_001e34f0` and published at `0x006075F8`.
- The `0x48`-byte title controller exists only while `FUN_001de840` is active;
  a nonzero title result destroys it before returning to the outer loop.
- The `0xDF8` manager is persistent across Mode Select, BTL, ETC, and Options
  callbacks, but not across a return to title. Manager phase 5 destroys it and
  clears `0x00607600`; the borrowed live-profile object remains owned by the
  outer loop.
- The shared `0x14`-byte transient and the Mode Select/BTL/ETC/Options objects
  are narrower callback-lifetime allocations whose terminal paths clear their
  respective global pointer slots.
- Manager destruction is not a callback-object sweep. `FUN_001f42b0` does not
  clear the shared transient or mode/gate globals at `0x0060760C..0x00607624`;
  each clean callback owns those allocations and clears its own slots.

The clean wrappers do not share a uniform allocation-failure contract:

- `FUN_001de840` is defensive for its top-level title allocation: if the
  `0x48`-byte allocation fails, it skips update/presentation, returns 0, and
  retries on a later invocation.
- The mode-2/3 BTL wrappers likewise call `FUN_001ec960` only when
  `FUN_001ec300` returned a non-null process; a failed `0x44`-byte allocation
  leaves the global null and is retried.
- By contrast, the outer eight-byte state, its `0x2400`-byte live profile, the
  `0xDF8` manager, every shared `0x14`-byte callback transient, the `0xD4`
  Mode Select controller, and the shared back gate are dereferenced or passed
  to an immediate dereferencing callee without a recovery branch after
  allocation.
- Even after the manager allocation succeeds, `FUN_001f4360` assumes its
  internal `+0xDD4` (`0x40` bytes) and `+0xDD8` (`0x98` bytes) allocations
  succeed: it dereferences each result unconditionally. The optional
  `+0xDDC` allocation is different; its later BTL handoff checks for null.
- Collection and Options can pass a null mode object to their
  overlay/resident poll entry after allocation failure. This establishes the
  wrapper boundary only; no assumption is made about whether those callees
  tolerate null.

The resident front end therefore assumes allocator success at most controller
construction boundaries. The title and shared BTL process are the two proven
top-level retry exceptions in the flow analyzed here.

## Outer opening/title/front-end loop

`FUN_001e0ee0` allocates an eight-byte outer state object and stores its pointer
at runtime global `0x006075C0` (Ghidra `piGpffffcbd0`). Native startup places
the object in state 2 before the loop reaches the title path. The prerequisite
startup gates are documented separately in [startup.md](startup.md).

| Outer object field | Observed use |
| --- | --- |
| `+0x00` | Outer state: 2 opening, 3 title, 4 front end |
| `+0x04` | Title result retained for manager initialization: 1 or 2 |

The loop's proven transitions are:

| Outer state | Callee and call site | Result | Transition |
| --- | --- | --- | --- |
| 2 | `FUN_001de6f0` | `1` | state 3 |
| 3 | `FUN_001de840` at `0x001E1240` | `-1` | state 2 |
| 3 | `FUN_001de840` at `0x001E1240` | `1` or `2` | store result at `+0x04`, state 4 |
| 4 | `FUN_001e9980` at `0x001E12D0` | `1` | state 3 |
| 4 | `FUN_001e9980` at `0x001E12D0` | `2` | state 2 |

The state-4 caller contains the result-2 branch, but the inspected clean
`FUN_001e9980` implementation only constructs return values 0 and 1. No
resident producer of return 2 was found in that function.

### Title controller result contract

`FUN_001de840` owns a `0x48`-byte title controller through global
`0x006075C4` (`iGpffffcbd4`):

1. It allocates and initializes the object with `FUN_001de900`.
2. It updates it through `FUN_001df690`.
3. While the update returns 0 it calls `FUN_001dfab0` for presentation.
4. A nonzero result destroys the object with `FUN_001de970` and is returned to
   the outer loop.

The title object's relevant fields are:

| Field | Observed use |
| --- | --- |
| `+0x00` | Internal title state |
| `+0x08` | Terminal result |
| `+0x0C` | Current two-item selection, initialized to 1 and clamped to 0 or 1 |
| `+0x10` | Transition handle |

`FUN_001df140` changes `+0x0C` with input masks `0x1000` and `0x4000`.
These are native Up and Down; a newly pressed native Circle or Start
(`0x0020` or `0x0800`) stores `selection + 1` at `+0x08`. Consequently, the
title result is exactly 1 for item 0 and 2 for item 1. Existing title-flow
evidence identifies these as New Game and Continue respectively. State 9 of
`FUN_001df690` returns this field. The masks and names follow the resident map
in [controller_input.md](../runtime/controller_input.md), not a host/emulator
binding.

The active decoder is non-wrapping: Up at item 0 remains 0 and Down at item 1
remains 1. Its nested tests give simultaneous-input priority Up, then Down,
then Circle/Start confirmation. Native Cross is not a direct title back action
in `FUN_001df140`. The state dispatcher calls that decoder at `0x001DF8B0`.
Because `FUN_001deed0` initializes selection `+0x0C` to 1 when called at
`0x001DF798`, the clean title controller initially points at Continue.

A separate title path stores `-1`, which restarts the opening/title
cycle through outer state 2. More precisely, `FUN_001df690` stores `-1` only
when its state-5 transition handle completes, then advances through states 8
and 9 to return it; `FUN_001df140` itself never produces `-1`. Thus the
opening restart is an internal title-transition result, not a third item or a
direct back-button result.

## Persistent front-end/profile manager

`FUN_001e9980` is the resident front-end dispatcher. On first entry it:

1. allocates `0xDF8` bytes;
2. initializes the object with `FUN_001f4200`;
3. stores it at global `0x00607600`;
4. calls `FUN_001f45b0`, which establishes BTL as the initial overlay choice.

Ghidra emits both `iGpffffcc10` and `iRam00607600` for the global at
`0x00607600`; they are overlapping labels for the same pointer. The object also
contains the live profile state used elsewhere, so “front-end manager” and
“profile manager” refer to the same persistent allocation here.

### Manager fields used by mode flow

| Field | Initialization / use | Confidence |
| --- | --- | --- |
| `+0x04` | Live profile pointer copied from resident global `0x006075F8` | High |
| `+0x08` | Main phase; initialized to 1 | High |
| `+0x0C` | Mode callback ID; initialized to 0 | High |
| `+0x10` | Cached overlay selector index; initialized to `-1`, then set to 0 by `FUN_001f45b0` | High |
| `+0x14` | Resident BTL pause-owner state: 0 normally, 1 while the owned start-menu path is active | High; detailed consumers are documented elsewhere |
| `+0x18` | Zero-based confirming controller-port index; initialized to 0, then copied by an accepted Mode Select confirmation (`0` or `1`) | High |
| `+0x4C` | Player 1 current character ID; Mode Select initialization writes 1 | High; field name is independently runtime-proven |
| `+0x74` | Player 2 current character ID; Mode Select initialization writes 2 | High; field name is independently runtime-proven |
| `+0xDDC` | Owned pointer to an optional `0x4C`-byte resident battle-condition subsystem | High; later outcome semantics are documented elsewhere |

`FUN_001f4360`, called by the manager constructor, performs the relevant
initial writes: phase 1 at `+0x08`, callback 0 at `+0x0C`, and `-1` at
`+0x10`.

After its constructor initialization to 0, the only direct resident write
found for manager `+0x18` is the accepted Mode Select confirmation in
`FUN_00384760`. No callback-return or Mode Select reconstruction path resets
it, so the confirming port persists until another accepted selection or
manager destruction. Its later consumers establish more than an opaque
argument: several resident paths choose one of two
`0x78`-stride input banks with `manager+0x18`, and the Practice path in
`FUN_003b9f60` maps values 0 and 1 to
`FUN_001f48f0(manager, 1)` and `FUN_001f48f0(manager, 2)` respectively. This
proves the port/side conversion mechanically. Existing runtime evidence
independently identifies `+0x4C/+0x74` as the current Player 1/Player 2
character IDs.

`FUN_001f47c0` is the exact setter for manager `+0x14`, and `FUN_001f4790`
tests it for equality. The manager constructor sets it to 0. During BTL,
`FUN_001ebd90` sets it to 1 while its resident start-menu owner is active and
restores 0 before interpreting the owner's result; result 2 then writes route
code 7. The exact setter call sites are constructor `0x001F43D8`, BTL active
`0x001EBE8C`, and BTL restore `0x001EBF70`; route 7 is passed to
`FUN_001ec270` at `0x001EC044`. The deeper scheduling effects of this field remain canonical in
[pause_and_replay.md](../gameplay/pause_and_replay.md#resident-ownership-and-top-level-result-routing).

### Manager-construction binding side effect

Manager construction also establishes the battle-control mappings used later
by BTL. `FUN_001f4360` calls `FUN_001f3dc0(-1, 0)` at `0x001F4584`, copying
the eight-halfword default at `0x005C06A0` into all three resident `0x10`-byte
banks at `0x006B2B10`, `0x006B2B20`, and `0x006B2B30`. At that point the new
manager has not yet been published at `0x00607600`, so the synchronization
tail of `FUN_001f3dc0` cannot write the live profile.

The file-backed default at ELF offset `0x004C07A0` is:

```text
0010 0020 0040 0080 0004 0008 0001 0002
```

Those are native Triangle, Circle, Cross, Square, L1, R1, L2, and R2 masks.
This 16-byte source is the persistent static patch point; the three
`0x006B2Bxx` destinations are zero-filled resident runtime storage and are
repopulated on each new manager construction.

`FUN_001e9980` then publishes the manager pointer and calls `FUN_001f45b0` at
`0x001E99C4`. That helper copies banks `0x006B2B20/30` into the borrowed live
profile at `+0x12/+0x22`, respectively. The bytes and later synchronization
direction are mapped in [save_data.md](save_data.md), while their consumption
as controller-port battle bindings is established in
[action_commands.md](../gameplay/action_commands.md). This side effect occurs
on every new manager allocation, before the title result is consumed.

### Manager phases

| `+0x08` | Behavior in `FUN_001e9980` |
| --- | --- |
| 1 | Consume the outer title result at `[0x006075C0] + 0x04` |
| 2 | Run New Game preparation through `FUN_001e9c00` |
| 3 | Run Continue preparation through `FUN_001e9eb0` |
| 4 | Dispatch the callback selected by `+0x0C` |
| 5 | Return 1 to the outer loop and destroy the manager |

At phase 1, title result 1 selects phase 2 and title result 2 selects phase 3.
An unrecognized title result falls through to phase 4 / callback 1. Both the
successful New Game and Continue paths set phase 4 and callback 1. A cancelled
Continue path can return `-1`; `FUN_001e9980` converts that into return 1 to the
outer loop. The save/load workflow inside that path was not analyzed.

`FUN_001e9c00` itself constructs only return values 0 and 1, so the generic
manager-side `-1` check in phase 2 is dead for the clean New Game callee.
`FUN_001e9eb0` is the only clean preparation path here that constructs `-1`.

The unrecognized-result fallback is not reachable through the clean outer
composition: outer state 3 enters manager state 4 only for title result 1 or 2.
Likewise, although the manager constructor initializes callback `+0x0C` to 0,
every clean path that reaches manager phase 4 first changes it to 1.

Before `FUN_001e9980` returns nonzero, the manager is gone and global
`0x00607600` is clear. The normal phase-5 path performs that destruction with
`FUN_001f42b0`. Continue cancellation instead destroys and clears the manager
inside `FUN_001e9eb0`; the dispatcher's final null guard then skips a second
destruction. In both teardown paths, `FUN_001f4680` first copies live-profile
byte `manager+0x04 -> +0x10` back to cache byte `0x00607608`, destroys the
owned `+0xDDC` battle-condition object when present, and resets overlay cache
`manager+0x10` to `-1` before the allocation is freed. The vibration-cache
semantics are owned in [save_data.md](save_data.md#fresh-profile-initialization).

The clean ordering prevents cross-lifetime residue: Mode Select back frees its
controller, gate, and transient before manager phase 5 is observed; Continue
cancellation destroys its gate and frees its transient in the same callee that
destroys the manager; BTL/ETC/Options finish their own objects before returning
to Mode Select. An injected early manager phase 5 or direct manager destructor
does not perform those steps. It can leave `0x0060760C..0x00607624` pointing at
old callback state that a later manager/callback will reuse or reinterpret.

## High-level mode callback dispatcher

When manager phase is 4, `FUN_001e9980` switches directly on manager
`+0x0C`:

| Mode ID | Meaning | Callback / dispatch call site | Backing | Proven return to Mode Select |
| ---: | --- | --- | --- | --- |
| 1 | Mode Select / main menu | `FUN_001ea240` at `0x001E9B38` | Resident | N/A |
| 2 | Free Battle | `FUN_001ea8c0` at `0x001E9B48` | BTL, battle type 1 | `FUN_001eeb10` writes mode 1 |
| 3 | Practice | `FUN_001ea940` at `0x001E9B58` | BTL, battle type 2 | `FUN_001eeb10` writes mode 1 |
| 6 | Collection | `FUN_001eb120` at `0x001E9B88` | ETC | callback cleanup writes mode 1 |
| 7 | Options | `FUN_001eb440` at `0x001E9B98` | Resident | callback cleanup writes mode 1 |

The English meanings are corroborated by the stock Mode Select order and the
called subsystems.

All analyzed mode callbacks return by writing 1 to manager `+0x0C`; manager
phase remains 4. Thus returning from a mode does not recreate the profile
manager. It re-enters callback 1 on the next `FUN_001e9980` invocation.

### Numeric-domain crosswalk

The small integers in this flow are not interchangeable. The complete in-scope
mapping is:

| Meaning | Physical Mode Select slot | Result / manager `+0x0C` | Overlay selector / manager `+0x10` | Mode-specific entry value |
| --- | ---: | ---: | ---: | --- |
| Free Battle | 1 | 2 | 0 (BTL) | BTL type 1 |
| Practice | 2 | 3 | 0 (BTL) | BTL type 2 |
| Collection | 5 | 6 | 2 (ETC) | `0x80`-byte ETC object |
| Options | 6 | 7 | 0 retained; no selector call in mode 7 | `0x5C`-byte resident object |

Title results form another namespace: title result 1 means New Game and title
result 2 means Continue, not manager modes 1 and 2. Likewise overlay selector
0/2 indexes the filename table; it is neither a manager mode ID nor an overlay
header-kind value.

## Mode Select result table

The resident mapping table is at runtime `0x005D51D0`, ELF file offset
`0x004D52D0`, Ghidra `DAT_005d51d0`:

| Physical slot | Raw result | UI meaning | Dispatch effect |
| ---: | ---: | --- | --- |
| 1 | 2 | Free Battle | manager mode 2 / BTL type 1 |
| 2 | 3 | Practice | manager mode 3 / BTL type 2 |
| 3 | -1 | Disabled stock slot | Removed from the compact selection list |
| 5 | 6 | Collection | manager mode 6 / ETC |
| 6 | 7 | Options | manager mode 7 / resident |

The table is not the visual selection array itself:

- `FUN_00384690` loops all seven table entries, keeps only entries whose signed
  result is nonnegative, and writes their **physical slot indices** to a compact
  array in the controller.
- In the stock executable the active count is 6.
- `FUN_00384700` converts the selected compact index back to a physical slot.
- `FUN_003845d0` converts that physical slot through `DAT_005d51d0`, but only
  when the controller has reached terminal state 6; otherwise it returns `-1`.

This two-level mapping is important for patches: table values are mode IDs,
whereas the controller, visuals, and remembered selection use physical slots.

### Consequences for result-table edits

- The compact array has capacity for all seven physical slots. Changing a
  negative table entry to a nonnegative value automatically admits that slot;
  no separate active-count constant needs changing.
- The filter validates only the sign. A nonnegative value that is not handled
  by the manager callback switch passes Mode Select confirmation and becomes
  manager `+0x0C`, after which manager phase 4 has no default recovery and
  stalls.
- Changing a table result remaps the callback but does not change the physical
  carousel order or remembered-slot behavior. `0x006045E0` continues to store
  the physical slot rather than the remapped mode ID.
- An all-negative table is not a supported empty-menu encoding.
  `FUN_00384690` can leave active count 0, but `FUN_00384620` still calls
  `FUN_00384720`, which indexes compact entry 0; there is no empty-list guard.
  `FUN_003839e0` does not initialize controller `+0x08..+0x20`, and
  `FUN_00384690` writes only admitted entries, so entry 0 has not been written
  by this construction. It is immediately copied to visual field `+0xBC`, and
  a later confirmation can use the same indeterminate word as an index into
  `DAT_005d51d0`. A deliberately empty menu therefore needs code changes, not
  only seven negative table values.

## Mode Select controller

Mode callback 1 (`FUN_001ea240`) allocates a `0xD4`-byte controller and stores
it at global `0x00607610` (`iGpffffcc20`). The construction call sequence is:

```text
0x001EA41C  FUN_003839e0   clear/initialize owned fields
0x001EA428  FUN_00383db0   construct resources, filter slots, restore selection
              FUN_00384690 build compact physical-slot array
              FUN_00384620 restore preferred physical slot
              FUN_00384570 apply manager-side initialization
```

`FUN_00383aa0` is the matching cleanup routine and is called from
`FUN_001ea240` on accepted selection, back/exit, and final callback cleanup.

### Relevant object fields

| Offset | Size | Observed role |
| ---: | ---: | --- |
| `+0x00` | 4 | Controller state |
| `+0x04` | 4 | Active compact-slot count |
| `+0x08` | 7 x 4 | Compact array of physical slot indices |
| `+0x24` | 4 | Selected compact-array index |
| `+0x28` | 4 | Signed floating carousel displacement |
| `+0x30` | 4 | Combined input mask used for back/save-load actions |
| `+0x34` | 4 | Combined initial/change and delayed-repeat mask; sampled but not read again in this controller path |
| `+0x38` | 4 | Combined directional input mask |
| `+0x3C` | 4 | Controller-port-0 confirm input mask |
| `+0x40` | 4 | Controller-port-1 confirm input mask |
| `+0x44` | 4 | Entry/exit transition handle |
| `+0x48` | 4 | Terminal update result: 1 accept, `-1` back |
| `+0x4C` | 4 | Terminal update-countdown, seeded to 2 |
| `+0x58` | 1 | Input source: 0 direct masks, nonzero scripted target |
| `+0x5C` | 4 | Scripted physical target/action |
| `+0x60` | 4 | Save/load child pointer; branch excluded |
| `+0xBC` | 4 | Last physical slot sent to the selection visual |
| `+0xC0` | 4 | Selection visual child |
| `+0xC4` | 4 | Modal/branch type |

`FUN_00384570` additionally writes manager `+0x4C = 1` and `+0x74 = 2` when
the manager exists. Existing runtime evidence makes these the current Player 1
and Player 2 character IDs. Because `FUN_00384570` runs on every Mode Select
construction, every analyzed return from BTL, ETC, or Options resets those two
current IDs before another mode is accepted; it is not a one-time manager
default.

### Remembered physical slot

Runtime halfword `0x006045E0` (ELF offset `0x005046E0`) is both Ghidra
`DAT_006045e0` and the GP-relative alias `uGpffff9bf0`. Its clean initial value
is `0xFFFF` (`-1` as the signed halfword load used by the constructor).

- `FUN_00384760` writes the accepted **physical slot** here at
  `0x00384840` before starting the exit transition.
- `FUN_00383db0` passes its signed value to `FUN_00384620` on the next Mode
  Select construction.
- `FUN_00384620` selects the matching compact-array entry; if no match exists,
  compact index 0 remains selected.
- The back action restores the global to `0xFFFF` at `0x00384BD4`, so the next
  construction falls back to compact index 0. The adjacent auxiliary-byte
  clear is at `0x00384BD8`.

This is the complete resident “return to the previously selected mode”
mechanism. No mode-specific return code is needed: accepting a slot persists it
before the BTL/ETC handoff, and all analyzed callbacks later write manager mode
1. The halfword is not owned by the manager: `FUN_001f4680` does not clear it.
The clean back path performs the reset explicitly before manager destruction;
forcing some other manager-exit path can therefore leave the remembered slot
for a later manager lifetime.

### Input actions

`FUN_003849c0` is the active-state input dispatcher. It first calls
`FUN_00384de0`, which is an empty function in the clean build, then chooses one
of two decoders:

- direct masks: `FUN_00384cd0` when byte `+0x58` is zero;
- scripted target: `FUN_00384d70` when byte `+0x58` is nonzero.

Before that dispatch, `FUN_003854f0` samples two input banks through runtime
global `0x006073FC` (`iGpffffca0c` / `iRam006073fc`). The global points to the
`0x530`-byte system/input context mapped independently in
[controller_input.md](../runtime/controller_input.md); its embedded side
records are exactly `0x78` bytes apart:

- controller `+0x3C` receives controller port 0's newly-pressed word at
  context `+0x84`;
- controller `+0x40` receives controller port 1's newly-pressed word at
  context `+0xFC`;
- controller `+0x30` receives the bitwise OR of those newly-pressed words;
- controller `+0x38` receives the OR of the parallel words at context
  `+0x80/+0xF8`, which are the two held/current masks.

Thus navigation and back are combined across both controller ports, while
confirmation retains its originating port: action 3 passes 0 to
`FUN_00384760`, action 4 passes 1, and an accepted confirmation copies that
value to manager `+0x18`.
The same field-to-port relationship is independently established by the
Practice path in [practice_mode.md](../gameplay/practice_mode.md). By contrast, the title
controller in `FUN_001df690` supplies `FUN_001df140` only controller port 0's
context-`+0x84` word.

The direct decoder produces these action IDs in the native PS2 mask domain:

| Action | Mask | Native control | Effect |
| ---: | --- | --- | --- |
| 1 | `+0x38 & 0x1000` | Up, either port | Previous compact entry |
| 2 | `+0x38 & 0x4000` | Down, either port | Next compact entry |
| 3 | `+0x3C & 0x20` | Circle, port 0 | Confirm with port index 0 |
| 4 | `+0x40 & 0x20` | Circle, port 1 | Confirm with port index 1 |
| 5 | `+0x30 & 0x40` | Cross, either port | Back/exit |
| 6 | `+0x30 & 0x0800` | Start, either port | Save/load branch; excluded |

The nested tests in `FUN_00384cd0` also establish simultaneous-action
priority: port-0 Circle, port-1 Circle, Cross, Start, Down, then Up. Thus port
0 wins if both ports confirm together, confirm outranks back, and Down wins if
Up and Down are both present.

Action 5 also writes `0xFFFF` to `0x006045E0` and zero to runtime
`0x006077AC` (Ghidra `uGpffffcdbc`; semantic role not established).
No other decompiled reference under the `uGpffffcdbc` label occurs in the
resident C export, so the clear is proven but no resident consumer can yet
name the word. Both clears happen before state 3 decides whether to finish the
exit or resume selection; the resume branch does not restore either global.

The dormant scripted decoder treats target 7 as back and target 8 as the
excluded save/load action. If the target equals the current physical slot it
emits action 3, so an accepted scripted confirmation passes argument 0 and
stores controller port 0 at manager `+0x18`. Otherwise it advances only to the
next compact entry. There is no missing-target guard: a scripted target
filtered out of the compact list can never reach the equality/confirm case.

Clean reachability is narrower than the implemented interface.
`FUN_003839e0` initializes `+0x58` and `+0x5C` to zero, and no direct writer in
the Mode Select controller/callback path makes `+0x58` nonzero. The direct
resident xrefs to global controller pointer `0x00607610` are its allocation,
update, presentation, and cleanup in `FUN_001ea240`. Normal clean flow therefore
always uses `FUN_00384cd0`; the scripted behavior requires an external or
otherwise unresolved mutation.

### Resident pre-dispatch hook seam

The no-op `FUN_00384de0` is an exact pre-decoder extension point:

- active dispatcher `FUN_003849c0` calls it at runtime `0x003849D0`
  (ELF file offset `0x00284AD0`), before reading controller `+0x58`;
- `a0` still contains the Mode Select controller pointer at the call, and the
  callee's return value is ignored;
- the target at runtime `0x00384DE0` (file `0x00284EE0`) is exactly two words,
  `0x03E00008, 0x00000000` (`jr ra; nop`).

The native body therefore has only eight bytes: nontrivial logic needs a
redirect/trampoline, but a replacement can inspect or alter the controller's
sampled masks and scripted-target fields before the unchanged decoder runs.

### Confirmation and terminal result

`FUN_00384760` is the confirmation gate:

1. It resolves the current compact index to a physical slot.
2. A negative mapped result enters modal type 4. This is unreachable through
   the stock compact list because `FUN_00384690` filtered such entries first.
3. Confirm argument 0 is accepted for any enabled slot. Confirm argument 1 is
   accepted immediately for physical slots 1 and 2; the other in-scope slots
   4, 5, and 6 enter a modal path. The omitted slot is not characterized.
4. On an accepted path it stores the confirm argument at manager `+0x18`,
   writes the physical slot to `0x006045E0`, stores terminal result 1 at
   controller `+0x48`, changes controller state to 1, and starts the exit
   transition.

`FUN_003854f0`, called only at `0x001EA438`, owns the controller lifecycle:

| State | Proven role |
| ---: | --- |
| 0 | Wait for entry transition, then enter state 2 |
| 1 | Wait for exit transition, then enter state 6 with countdown `+0x4C = 2` |
| 2 | Active selection; call `FUN_003849c0` |
| 3 | Back/close gate. After `FUN_00382ef0(child, 3)` completes, `FUN_003835c0` either resumes state 2 or commits terminal result `-1` and state 1. |
| 4 | Excluded save/load child path; returns to state 2 |
| 5 | Confirmation/error modal path; returns to state 2 when dismissed |
| 6 | Count down `+0x4C`, then return `+0x48` |

The update returns 0 while active, 1 after an accepted selection, and `-1`
after back/exit. `FUN_001ea240` calls `FUN_003845d0` at `0x001EA46C` only after
the update returned 1, then stores the mapped mode ID in its transient state.

The state-3 decision is mechanically exact even though the child fields lack
source names: it exits only when child halfword `+0x12 != 2` and child word
`+0x18 == 0`; otherwise it returns to active selection. Consequently an
action-5 press is not by itself proof that the controller will return `-1`.

## Mode Select callback and result routing

All front-end callbacks share a `0x14`-byte transient state pointer at runtime
global `0x0060760C` (`puGpffffcc1c` / `piGpffffcc1c`). For callback 1,
`FUN_001ea240` uses transient `+0x00` as its phase and `+0x08` as the selected
mode result. Every allocation initializes `+0x00..+0x0C` to zero and
`+0x10` to `-1`; ETC and resident callbacks reuse `+0x04` as their terminal
countdown.

The exact transient phases are:

| Phase | Proven action |
| ---: | --- |
| 0 | Wait for `FUN_001cfd70() == 0`, reset that transition state, then enter phase 1 |
| 1 | Wait for `FUN_00200670() != 0`, run the resident transition helpers, then enter phase 2 |
| 2 | Wait again for `FUN_001cfd70() == 0`, reset/stage resident state, then enter phase 3 |
| 3 | Call `FUN_001f3d10(0)`, write manager mode 1, stage Mode Select resources, then enter phase 4 |
| 4 | Construct/update the Mode Select controller; convert accepted physical slot through `FUN_003845d0`, or retain `-1` on back; then enter phase 5 |
| 5 | Accepted results advance directly to phase 6; the `-1` result first passes through a resident exit gate |
| 6 | Clean up and route the saved result |

The terminal routing switch copies the analyzed results 2, 3, 5, 6, and 7
verbatim to manager `+0x0C`. Result `-1` instead writes manager phase 5 at
`+0x08`, causing `FUN_001e9980` to return 1 to the outer title state. During
terminal routing, modes 5 and 6 also stage their resident resource groups;
those resource details are not part of this flow map.

The Mode Select controller itself does not survive that terminal routing.
Phase 4 of `FUN_001ea240` destroys it and clears global `0x00607610` as soon as
its update returns 1 or `-1`; the `0x14`-byte transient alone carries the saved
result through phases 5 and 6. Back temporarily owns the separate exit-gate
object at `0x00607624`, which is also destroyed before phase 6.

### Shared Continue/back gate

Global `0x00607624` is not Mode-Select-specific. Both Continue preparation
(`FUN_001e9eb0`) and Mode Select phase 5 lazily allocate `0x28` bytes,
construct it through `FUN_001e3db0`, clear object `+0x20`, and update it
through the effective return value of `FUN_001e3f00`:

| Caller | `FUN_001e3f00` mode argument | Resident interpretation |
| --- | ---: | --- |
| Continue | 1 | Result 1 continues toward Mode Select; result 2 becomes `-1` and returns to title. |
| Mode Select back | 0 | Result 0 keeps the gate active; any nonzero result advances callback phase 5 to phase 6. |

Both paths destroy the object through `FUN_001e3e20` and clear
`0x00607624`. The constructor also owns a `0x44`-byte child at object `+0x24`,
but that child's save/load UI state machine remains deliberately excluded.

Across the clean dispatcher, a callback change is not observed on a later
manager invocation until the shared transient at `0x0060760C` has been freed.
This is an important lifetime invariant because New Game/Continue, Mode Select,
ETC, and Options reuse the same allocation with different phase layouts. Forcing
manager `+0x0C` to another callback in the middle of one of those layouts can
make the new callback reinterpret stale phase fields.

### End-to-end result chains

- Accepting a BTL/ETC slot writes its physical slot to `0x006045E0`, reaches
  Mode Select controller result 1, maps through `DAT_005d51d0`, copies that
  mode ID through transient `+0x08` to manager `+0x0C`, and invokes the matching
  mode callback without recreating the manager.
- Completion of any analyzed BTL/ETC callback writes manager mode 1. The next
  manager invocation reconstructs Mode Select, whose constructor uses
  `0x006045E0` to restore the previously accepted physical slot.
- A committed back exit takes the separate chain: action 5 clears
  `0x006045E0`, controller state 3 produces result `-1`, transient phase 6 writes manager phase 5,
  `FUN_001e9980` returns 1, and the outer object changes from state 4 to title
  state 3.

## Overlay selection boundary

BTL and ETC replace the same runtime overlay region beginning at
`0x006B3F00`. The established effective ranges are
`[0x006B3F00, 0x008DD080)` for BTL and
`[0x006B3F00, 0x006E4E00)` for ETC. This note uses those ranges only to
classify resident handoff targets; their lifetime evidence is maintained in
[runtime_lifetimes.md](../runtime/ee_memory_map/runtime_lifetimes.md).

### Filename table

The resident selector uses a contiguous three-entry pointer table beginning at
runtime `0x004049E0`, ELF offset `0x00304AE0`. Ghidra labels only the first
entry as `PTR_s_BTL.bin_004049e0`; direct byte inspection establishes the two
in-scope entries and the three-entry table shape:

| Selector index | Pointer entry | String address | String |
| ---: | ---: | ---: | --- |
| 0 | `0x004049E0` | `0x00603048` | `BTL.bin` |
| 2 | `0x004049E8` | `0x00603058` | `ETC.bin` |

One excluded overlay entry lies between indices 0 and 2. Its path and selector
behavior are intentionally omitted.

### `FUN_001f3d10`: selection-and-cache interface

`FUN_001f3d10(index)` is the high-level resident boundary used by the front
end:

- if manager `0x00607600` does not exist, it calls
  `FUN_001be7f0(1, filename[index])` and has nowhere to cache the index, so a
  later manager-less call loads again;
- if the manager exists and `index != manager+0x10`, it makes the same call and
  updates manager `+0x10` to `index`;
- if the cached index already matches, it does not issue another request;
- on a cache miss it calls the established synchronous overlay loader; after a
  cache hit or loader return, it always returns 1 and exposes no distinct
  pending or failure status;
- it performs no selector-index bounds check before reading the pointer table.

The constant first argument 1 selects the loader destination whose established
base is `0x006B3F00`. BTL and ETC therefore differ by filename selector but
replace the same runtime region.

The loader implementation itself was intentionally not followed here. The
synchronous call boundary is inherited from the canonical overlay analysis,
not inferred from the unconditional return value alone.

The cache is a logical “last selector requested” value, not an observed overlay
identity. Neither `FUN_001f3d10` nor `FUN_001f45b0` reads the shared overlay
header before accepting selector 0 as a cache hit, and both update the cache
after the loader call without inspecting a loader result. The word therefore
records a completed request at this boundary, not independently verified image
identity or success. Clean flow remains coherent because its overlay changes
pass through these helpers; external replacement of the shared region without
updating manager `+0x10` can suppress the reload that would otherwise repair
the image.

The manager constructor initializes `+0x10` to `-1`. `FUN_001f45b0`, called
immediately after manager allocation at `0x001E99C4`, requests `BTL.bin` and
sets `+0x10` to 0. Callback 1 calls `FUN_001f3d10(0)` again at
`0x001EA368`, so returning from ETC to Mode Select switches back to BTL before
the selection controller is constructed.

### Overlay state across return routing

- Manager construction synchronously selects BTL before it consumes the title
  result or runs New Game/Continue preparation.
- A BTL terminal return leaves BTL selected. Mode Select phase 3 asks for
  selector 0 again, which is normally a cache hit.
- Collection cleans up its ETC-bound object and writes manager mode 1
  without immediately replacing ETC. The next Mode Select callback performs
  only resident work in phases 0 through 2; phase 3 synchronously restores BTL,
  and phase 4 then constructs the selection controller.
- Options never changes the selector. On the normal path it entered from Mode
  Select with BTL already selected, so the phase-3 selector-0 call is again a
  cache hit.
- A return to title destroys the manager and its selector cache but does not
  clear the shared overlay image. On the next front-end entry the new manager
  again starts at selector `-1`; `FUN_001f45b0` reloads BTL even if BTL bytes
  were already resident, because it does not inspect image identity.

## BTL handoff and return

Modes 2 and 3 use a shared `0x44`-byte process at global `0x00607620`
(`iRam00607620` / `piGpffffcc30`). The preserved RTTI string for its resident
process class is `ccGbtlProcess` at `0x00404C10`.

The resident-visible process fields are:

| Offset | Proven use |
| ---: | --- |
| `+0x00` | Internal state dispatched by `FUN_001ec960`; initialized to 0 |
| `+0x10` | Sentinel initialized to `-1`; no later direct read was found in the inspected resident process path |
| `+0x14` | BTL entry type, 1 or 2 |
| `+0x18` | Set to 1 for entry types 1 and 2 |
| `+0x34` | Owned `0x4B4`-byte resident Character Select child used by state 7; cleaned by `FUN_003b9ce0` and freed by `FUN_001ec890` if still present |
| `+0x38` | Owned `0x16C`-byte BTL-bound state-9 selection child; cleaned by live `0x00713B20` and freed by `FUN_001ec890` if still present |
| `+0x3C` | Owned `0x188`-byte BTL result-metric child; constructed/cleared at live `0x007190D0/0x00719500`, cleaned at `0x00719140` |
| `+0x40` | Pointer to process table `0x005D9F98` |

The process table at `0x005D9F98` contains:

| Offset | Raw value | Meaning |
| ---: | ---: | --- |
| `+0x00` | `0x005C0B28` | Pointer to the `ccGbtlProcess` type-name pointer |
| `+0x04` | `0x00000000` | Null entry |
| `+0x08` | `0x001ECBF0` | Default indirect hook: return-zero stub |

The proven resident handoff is:

- `FUN_001ea8c0` requests/gets the process with `FUN_001ec300(1)` at
  `0x001EA8D0` and updates it at `0x001EA8E8` for mode 2.
- `FUN_001ea940` requests/gets it with `FUN_001ec300(2)` at `0x001EA950`
  and updates it at `0x001EA968` for mode 3.
- `FUN_001ec300` allocates the process if absent and calls `FUN_001ec690`.
- `FUN_001ec7a0` selects BTL with `FUN_001f3d10(0)` at `0x001EC7BC`, stores
  the battle type at process `+0x14`, and initializes the BTL-bound side of the
  handoff.
- Both callbacks update through `FUN_001ec960`, but their wrapper conditions
  differ. Mode 2 skips the table callback when the update result is 0, invokes
  `0x001ECBF0` for other nonterminal results, and destroys the process on
  result 3. Mode 3 destroys on result 3 but invokes `0x001ECBF0` for every
  other result, including 0.

`FUN_001ec300(entry_type)` uses its argument only while constructing an absent
process. If global `0x00607620` is already non-null, it returns that allocation
without calling `FUN_001ec690/001ec7a0` and without rewriting process `+0x14`.
Clean routing destroys the process before a later BTL selection, but forcing
manager callback 2 to 3 (or 3 to 2) while the process survives reuses the old
entry type; changing the callback ID alone does not reinitialize the handoff.

The clean target at runtime `0x001ECBF0` (ELF offset `0x000ECCF0`) is not
recognized as a named function in the export. Its complete executable body is
`0x0000102D, 0x03E00008, 0x00000000`: set `v0` to zero, return through `ra`,
then the delay-slot no-op. Both wrappers discard that return value. Their
different call conditions consequently have no observable effect with the
resident-initialized table, though they would matter if the hook target were
replaced.

For a static extension, the replaceable pointer is the single word at table
`+0x08`: runtime `0x005D9FA0`, ELF file offset `0x004DA0A0`. An alternate
target receives the `0x44`-byte process pointer in `a0`; neither wrapper uses
its return value. Mode 2 invokes it only after dispatcher results 1 or 2,
whereas mode 3 also invokes it after result 0. A hook that needs identical
per-invocation coverage in both modes cannot rely on this table entry alone.

### Fixed-address BTL handoff surface

After the synchronous selector-0 call, `FUN_001ec7a0` crosses the fixed-address
BTL interface in this order:

1. If process `+0x3C` is null, allocate `0x188` bytes, call live
   `func_0x007190d0`, and retain the result at `+0x3C`.
2. When `+0x3C` is non-null, call live `func_0x00719500` to clear the BTL
   result-metric child. Its established fields are documented in
   [match_outcomes.md](../gameplay/match_outcomes.md).
3. Call live `func_0x00885210` unconditionally to recreate the two-side support
   manager documented in [support_mechanics.md](../gameplay/support_mechanics.md).
4. If the manager and manager `+0xDDC` are both non-null, pass the `+0xDDC`
   object to `FUN_001fd030` at call site `0x001EC864`. That helper resets the
   object's payload at `+0x08` through `FUN_001fccd0`. The manager constructor
   allocated the `0x4C`-byte object through `FUN_001fcd90`; its later condition
   and outcome semantics are maintained in
   [match_outcomes.md](../gameplay/match_outcomes.md).
5. Write process state 1.

Destruction through `FUN_001ec370 -> FUN_001ec700 -> FUN_001ec890` performs the
matching resident-visible cleanup:

- clean/free the residual Character Select child at `+0x34` through resident
  `FUN_003b9ce0`;
- clean/free the residual state-9 selection child at `+0x38` through live
  `func_0x00713b20`;
- clean/free the result-metric child at `+0x3C` through live
  `func_0x00719140`;
- call live `func_0x00885290` after all three slots are cleared to destroy the
  two-side support manager.

All six fixed targets are inside the established BTL lifetime range. Their
overlay-local implementations are intentionally outside this note.

`FUN_001ec960` first services resident pause/control owner `FUN_001ebd90`, then
dispatches process states 1 through `0x19`. Its complete wrapper-facing return
contract is:

| Return | Condition |
| ---: | --- |
| 0 | A defined nonterminal state's handler left process `+0x00` unchanged |
| 1 | A defined state's handler changed process `+0x00` during the call |
| 2 | Process `+0x00` did not match a defined switch case |
| 3 | Terminal state `0x19` completed its return helper |

In terminal state `0x19` it calls `FUN_001eeb10`. Once the resident transition
is idle, `FUN_001eeb10` writes manager `+0x0C = 1`, restages the Mode Select
resource groups, and returns 1. `FUN_001ec960` then returns 3, so the mode
callback destroys global `0x00607620`. The following manager invocation
therefore re-enters Mode Select.

Two clean in-scope paths write state `0x19` directly:

- state 7 handler `FUN_001ed450` receives `-1` from the resident Character
  Select child, destroys it, and treats that as cancellation back to the menu;
- state `0x12` handler `FUN_001ee060` sees latched battle-route code 7 and
  sends both BTL entry types to state `0x19`.

`FUN_001ebd90`, serviced before every state dispatch, is the resident path
that can latch route code 7 at `0x00607670` through `FUN_001ec270(7)` after
its owned pause/control object returns 2. State-`0x12` handler `FUN_001ee060`
reads the same word directly through the overlapping `iGpffffcc80` label;
other resident consumers use `FUN_001ec280`. The value is not stored in the
`0x44`-byte BTL process.
The exact code table and later battle-outcome branches remain canonical in
[match_outcomes.md](../gameplay/match_outcomes.md) and
[pause_and_replay.md](../gameplay/pause_and_replay.md).

Although `FUN_001ec690` initially clears process state `+0x00` to 0, its
constructor immediately calls `FUN_001ec7a0`, which changes that state to 1.
Thus the default-return-2 path is not the first normal update of a newly
constructed type-1/type-2 process.

This establishes both the BTL entry parameter (1 or 2) and its resident return
contract without relying on overlay-local behavior.

The deeper state meanings are intentionally not duplicated here. Resident
states 1 through 6 prepare resources, states 7 and 9 own selection handoffs,
states 10 through 15 load/construct the battle, and later states tear down or
switch the graph. Their established behavior is maintained in
[Practice-mode architecture](../gameplay/practice_mode.md) and
[stages.md](../gameplay/stages.md); this
note owns only the front-end entry/return boundary and dispatcher contract.

## ETC handoffs and returns

The Collection ETC callback calls `FUN_001f3d10(2)` before entering its
overlay-bound object. Its overlay entry points are listed only as handoff
evidence; their internals were not inspected.

### Mode 6 / Collection

`FUN_001eb120` owns its ETC object through global `0x00607614`
(`iGpffffcc24`):

- select ETC at call site `0x001EB1F0`;
- allocate `0x80` bytes and call overlay-bound entries
  `func_0x006c65c0` and `func_0x006c68f0`;
- poll `func_0x006c8940`;
- on result 1, seed transient `+0x04` to 3 and enter its terminal countdown;
- call `func_0x006c6630`, free the object, clear `0x00607614`, and write
  manager `+0x0C = 1`.

All four `0x006Cxxxx` entry points lie within the established ETC runtime
range.

The Collection callback uses more explicit transient phases:

| Phase | Resident wrapper action |
| ---: | --- |
| 0 | Set phase 1 unconditionally. |
| 1 | Wait for the resident transition to become idle, reset/stage it, select ETC, construct the object, and set phase 3. |
| 2 | Explicitly inert in `FUN_001eb120`; the clean callback never writes this phase. |
| 3 | Poll the object. Exact result 1 writes phase 4 and `+0x04 = 3`; every other result leaves phase 3 unchanged. |
| 4 | Decrement transient `+0x04`. At completion free the transient and ETC object, clear their globals, release/restage resident resources, and write manager mode 1. |

### Mode 7 / Options (resident-only)

`FUN_001eb440` owns a `0x5C`-byte resident object through global
`0x0060761C` (`iGpffffcc2c`). It uses resident functions
`FUN_0038afb0`, `FUN_0038bbf0`, `FUN_0038c5f0`, and `FUN_0038b370`, then
writes manager `+0x0C = 1` after its transient countdown seeded to 3 reaches
the cleanup branch.

No call to `FUN_001f3d10` occurs in this callback. Because Mode Select already
ensured selector index 0, the clean Options path leaves BTL selected.

Its phase 0 waits for the resident transition only when the object must be
constructed. It then updates through `FUN_0038bbf0`; exact result 1 writes
phase 1 and transient `+0x04 = 3`, while every other result calls
`FUN_0038c5f0`. Phase 1 decrements `+0x04`, destroys the object through
`FUN_0038b370`, clears both allocations, and writes manager mode 1.

## Compact call/evidence index

| Function | Sole/relevant caller | Key callees or reads | Proven side effect / result |
| --- | --- | --- | --- |
| `FUN_001de840` | `FUN_001e0ee0` at `0x001E1240` | `FUN_001df690`, `FUN_001dfab0` | Returns title result and destroys title object |
| `FUN_001e9980` | `FUN_001e0ee0` at `0x001E12D0` | In-scope callback cases listed above | Owns manager phases and callback ID |
| `FUN_001f3dc0` | manager constructor at `0x001F4584` | static defaults, three binding banks | Repopulates all resident battle-control bindings |
| `FUN_001f45b0` | manager dispatcher at `0x001E99C4` | BTL filename, binding banks 1/2 | Selects BTL and synchronizes live profile bindings |
| `FUN_001f4680` | manager destructor `FUN_001f42b0` | live profile `+0x10`, manager-owned subobjects | Preserves vibration cache and tears down manager-local state |
| `FUN_001f47c0/001f4790` | manager construction and BTL pause owner | manager `+0x14` | Set/test resident pause-owner state |
| `FUN_001ea240` | mode-1 case at `0x001E9B38` | `FUN_003854f0`, `FUN_003845d0` | Converts controller terminal result to manager mode ID |
| `FUN_00384690` | `FUN_00383db0` | `DAT_005d51d0` | Builds filtered physical-slot array |
| `FUN_00384620` | `FUN_00383db0` | `0x006045E0` argument, `FUN_00384720` | Restores remembered physical slot |
| `FUN_00384760` | `FUN_003849c0` at `0x00384B54/6C` | result table, manager | Persists physical slot and starts accepted exit |
| `FUN_00384de0` | `FUN_003849c0` at `0x003849D0` | none in clean body | Eight-byte no-op called with controller pointer before input decoding |
| `FUN_003854f0` | `FUN_001ea240` at `0x001EA438` | controller state switch | Returns 0, 1, or `-1` |
| `FUN_003845d0` | `FUN_001ea240` at `0x001EA46C` | `FUN_00384700`, result table | Returns mapped mode only in state 6 |
| `FUN_001e3f00/001e3f20` | Continue and Mode Select back gate | shared `0x28`-byte gate | Effective update result drives continue/cancel/back routing |
| `FUN_001f3d10` | Mode Select, BTL process, ETC callbacks | filename table, `FUN_001be7f0` | Synchronously selects/caches overlay index |
| `FUN_001ec300` | mode-2/3 callbacks | `FUN_001ec690` | Owns global `ccGbtlProcess` allocation |
| `FUN_001ec960` | mode-2/3 callbacks | resident state cases 1..`0x19` | Returns 3 after terminal return routing |
| `FUN_001ec270/001ec280` | BTL pause/return control | `0x00607670` | Write/read resident BTL route code; value 7 returns toward Mode Select |
| `FUN_001eeb10` | `FUN_001ec960` state `0x19` | transition/resource helpers | Writes manager mode 1 |
| `FUN_001fd030` | BTL initializer at `0x001EC864` | manager `+0xDDC` | Resets resident battle-condition payload before BTL state 1 |
| `FUN_001eb120` | mode-6 case at `0x001E9B88` | selector 2, `0x006Cxxxx` handoff | ETC Collection lifecycle, then mode 1 |
| `FUN_001eb440` | mode-7 case at `0x001E9B98` | resident `FUN_0038xxxx` object | Options lifecycle, then mode 1 |

## Negative results, limits, and open semantics

- No dynamic execution was used; all findings are static clean-binary evidence.

Unsupported controller states do not share a common recovery policy:

| Owner / field | Unsupported-value behavior |
| --- | --- |
| Outer object `+0x00` | Values outside 2, 3, and 4 run only the common outer services; no state transition is made. |
| Title controller `+0x00` | Values outside 0 through 9 return 0 after common title servicing; the object remains allocated. |
| Manager phase `+0x08` | Values outside 1 through 5 return 0 after common services; the phase is unchanged. |
| Manager callback `+0x0C` in phase 4 | An unhandled ID invokes no callback and leaves phase 4 active. |
| Mode Select controller `+0x00` | Values outside 0 through 6 fall through common visual servicing and return 0; no recovery state is assigned. |
| Shared callback transient `+0x00` | Values outside the active callback's listed cases are inert; reusing the allocation under another callback can reinterpret them. |
| BTL process `+0x00` | Values outside 1 through `0x19`, including 0, return 2. Both BTL wrappers retain the process and invoke its indirect hook rather than destroy it. |

- `FUN_00384de0` is a true no-op in the clean resident build despite being
  called on every active Mode Select update.
- The implemented scripted-target decoder is dormant in clean resident flow:
  its selector byte is initialized to zero and no direct in-scope writer sets
  it nonzero.
- The outer loop handles a hypothetical `FUN_001e9980` return value 2, but no
  such return is constructed by the inspected clean function.
- Manager callback 0 and the phase-1 unrecognized-title fallback are
  structurally present but unreachable in the clean outer/title composition.
- Negative mode-table entries are filtered before normal selection, making the
  negative confirmation branch unreachable without corruption or an alternate
  caller.
- `FUN_001f3d10` is a synchronous selection/cache boundary and always returns
  1; it exposes neither an asynchronous-pending state nor a distinct failure
  result.
- Manager `+0x18` is proven to retain the zero-based controller port that
  confirmed Mode Select; only its original source-level field name remains
  unrecovered.
- The clean `ccGbtlProcess` indirect hook is a return-zero stub and both
  wrappers ignore its return, so their differing hook-call conditions are
  inert unless the process table target is replaced.
- Collection and Options recognize only exact poll/update result 1 as
  completion. Other values remain in their active callback path; no alternate
  terminal route is present in these wrappers.
- Their wrappers also contain no object-allocation failure branch before the
  corresponding update/poll entry receives the global object pointer. A null
  allocation can therefore reach an overlay/resident update entry as null;
  whether an individual callee tolerates that was not assumed.
- Native PS2 button names come from the resident packet-to-mask evidence in
  `controller_input.md`; host/emulator bindings remain out of scope.
- The save/load child branch was not traced beyond its resident presence.
