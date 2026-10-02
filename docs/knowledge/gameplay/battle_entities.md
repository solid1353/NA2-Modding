# Battle-entity ownership and lifecycle

This document maps the retail NA2 (`SLPS-25837`) resident/`BTL.BIN` ownership
path for the two primary fighters and the battle objects created with them. It
covers allocation, registries, lookup, side mapping, removal, and destruction.
It does not assign gameplay meanings to fields merely because they sit in a
fighter or battle object, and it does not cover Adventure.

`side 0` means Player 1 and `side 1` means Player 2/COM below. A selected
support ID is configuration; it is not itself a pointer to a live object.

## Research coverage

- **Assigned scope:** the retail NA2 `BTL.BIN` fighter/battle-entity ownership
  model: manager and registry roots, Player 1/Player 2/support/entity slot
  mapping, create/initialize/remove/destroy paths, active or linked flags,
  lookup contracts, parent/child ownership, stable proven fields, and
  resident-file to runtime-overlay address mapping.
- **Exploration depth:** static and deep but not globally exhaustive. The
  resident setup/teardown chain (`FUN_001E9980`, `FUN_001EC3B0`,
  `FUN_001EF330`, `FUN_001EEFD0`) and the surrounding support lifecycle calls
  were followed completely. Bounded BTL audits covered the hub and generic
  intrusive-list family (live `0x00709240..0x00709F40`), the `ccCameraCtrl`
  helpers (`0x006D5640..0x006D59D0`), primary fighter/`ccCommand` creation and
  lookup, the transient-actor manager (`0x00729890`,
  `0x0072B190..0x0072B9B0`, `0x007343A0..0x00736080`), and the dynamic-support
  owner, factory, and common base (`0x00885210..0x00887FD0`). Every support
  factory case below `0x44` was decoded; specializations were read only for
  construction/destruction shape and two support-to-transient lineage sites.
  All 94 rows of the resident character table and all 74 distinct factories,
  constructors, final vtables, and deleting destructors were read. Direct-
  reference scans were exhaustive for global `0x00607888` (25 BTL references),
  the transient creator and side resolvers, the primary-fighter creator and
  resident publication lookups, and the 74 concrete constructors. Coordinator
  state 3 was followed into `FUN_0024E960`; the `ccSkillHNW001`,
  `ccSkillTYO000B`, `ccSkillFOR000`, and `ccSkillANB000` skill actors were
  read for class identity, factory admission, and destruction, and the
  shared-float skill callers for class identity only.
- **Confirmed coverage:** the three independent lifetime roots, exact
  side-slot formulas, hub/container/node layouts and the generic node pass
  contract, startup graph and borrowed cross-links, primary/`ccCommand` lookup
  behavior, coordinator-owned versus borrowed fields, `ccCameraCtrl`
  current-node mechanics, transient actor serial and linked-state contracts,
  deferred manager-owned children, support fixed-slot publication and removal,
  the generation allocator and counter namespaces, selector-driven class
  allocation, the complete table-selected fighter destructor chain and common
  fighter-owned children, common support ownership and borrowed animation
  pointers, side-record storage roles, callback-enable flags as ownership
  gates, non-owning support-lineage tokens, the coordinator timeout-marker
  branch, and the traced skill actors' allocation, authored spawn route,
  local state machine (`ccSkillHNW001`), and destructor edges.
- **Unresolved or untested:** indirect creation or registry-mutation routes
  not expressed as static direct references; the generic-base root selector
  word `+0x10` beyond its observed startup use; the domain names of support
  sentinels `0x24/0x25/0x26`; class-specific support behavior; the meaning of
  transient-actor byte `+0x206`; whether the fighter/`ccCommand` last-match
  scans express an intended duplicate policy; original coordinator state
  names; and the complete subordinate and base destruction lifetime of
  the skill actors, including other skill entrypoints.
- **Deliberate exclusions and overlap:** Adventure, damage formulas,
  substitution, frame pacing, animation, media, localization, AI decision
  logic, and status-effect semantics; fields touching those areas were
  followed only far enough to prove an ownership, identity, publication, or
  lifetime edge. Camera computation belongs to
  [Battle camera](battle_camera.md); support behavior (request gates, gauge,
  counters, scheduled passes, disable) to
  [Battle support mechanics](support_mechanics.md); session construction,
  per-update scheduling, and teardown order to
  [Battle lifecycle](battle_lifecycle.md); class-specific fighter methods to
  [Character action callbacks](character_action_callbacks.md); skill-actor
  damage arithmetic to [Damage](damage.md), combo contribution to
  [Combo accounting](combo_accounting.md), interaction records to
  [Collision](collision.md), and the `ccSkillCtrl` service to
  [Battle auxiliary services](battle_auxiliary_services.md).
- **Evidence limitations:** static, read-only analysis of the identified
  retail ELF and BTL images; it establishes no observed execution,
  allocator-failure behavior, or complete census of computed or data-driven
  control flow.

## Evidence identity and address conventions

The retail resident and BTL inputs and their live/raw/display address
conversion are defined in
[Retail game file identities](../game/files/file_identities.md#address-conventions).
All BTL addresses in this document are live addresses unless explicitly
labeled `raw` or `export`; resident addresses have no overlay bias. A preserved
Ghidra `FUN_` label at an encoded live BTL target can be an interior false
start rather than the true function entry.

## Ownership model

The resident manager is an alias surface. Three other roots own live objects:
the battle-state object owns a small BTL hub, a global transient manager owns a
singly linked actor family, and a separate global support manager owns at most
one fielded support object per side.

```text
resident global 0x00607600
`- manager (0xDF8 bytes)
   |- +0xDE4 / +0xDE8  borrowed aliases to primary fighters
   `- +0xDF0 / +0xDF4  borrowed aliases to per-side `ccCommand` nodes

resident global 0x00607604
`- battle-state object (0x38 bytes)
   |- +0x14  borrowed alias to the selected ccCamera01 root node
   `- +0x18  owning pointer to the 0x10-byte BTL hub
      |- +0x00  owning pointer to ccCameraCtrl (camera registry)
      |- +0x04  owning pointer to ccCommandCtrl (per-side control registry)
      |- +0x08  owning pointer to ccPlayerCtrl (fighter registry/coordinator)
      `- +0x0C  owning pointer to ccFieldCtrl (stage registry)

resident global 0x00607654
`- borrowed mirror of battle-state +0x18

resident global 0x00607820
`- transient-actor manager (0xD0 bytes)
   `- +0x14..+0x18  owning singly linked actor chain

resident global 0x00607888
`- ccBuddyAtkCtrl dynamic-support manager (0x24 bytes)
   |- +0x04  owning side-0 support-object slot
   |- +0x08  owning side-1 support-object slot
   `- +0x14  embedded ccBdySerialNo generation-ID allocator
```

The ownership classification follows the destructors, not the pointer graph:

- `FUN_001EEFD0` clears the manager aliases, calls the hub destructor, and
  clears battle-state `+0x18` and global `0x00607654`.
- Live BTL `0x00709280` destroys all four containers through their virtual
  destructor at container-vtable `+0x08`, nulls every hub field, and then frees
  the hub when requested.
- Each container destructor reaches live `0x00709F40`, which unlinks and
  virtual-destructs every node.
- Fighter/`ccCommand`/camera/`ccField` pointers linked at node `+0x20..+0x28`
  are cross-references. The linker at live `0x00709480` never transfers them to
  a distinct owner, and teardown does not free through those fields.

This produces an exact destruction order: `ccCameraCtrl`, `ccCommandCtrl`,
`ccPlayerCtrl`, then `ccFieldCtrl` nodes. Manager aliases are invalidated
before that node destruction begins.

The registry class names come from their RTTI, established in
[Battle lifecycle](battle_lifecycle.md#graph-registries-and-node-contract);
they name structures and do not assign meanings to otherwise unexplained
fields.

## Resident manager and battle-state lifecycle

### Manager allocation and alias slots

Resident `FUN_001E9980` allocates `0xDF8` bytes when global `0x00607600` is
null, calls `FUN_001F4200`, stores the returned manager, and calls
`FUN_001F45B0`. `FUN_001F4200` constructs resident subobjects and then calls
`FUN_001F4360`.

`FUN_001F4360` and teardown `FUN_001F4680` both zero two arrays of three
pointers:

| Manager offset | Logical index | Published meaning |
| ---: | ---: | --- |
| `+0xDE0` | `0` | reserved/zero fighter alias |
| `+0xDE4` | `1` | side-0 / Player-1 primary fighter |
| `+0xDE8` | `2` | side-1 / Player-2 primary fighter |
| `+0xDEC` | `0` | reserved/zero `ccCommand` alias |
| `+0xDF0` | `1` | side-0 / Player-1 `ccCommand` node |
| `+0xDF4` | `2` | side-1 / Player-2 `ccCommand` node |

The usable mapping is therefore `array[side + 1]`. The index-zero entries are
not support slots. They remain zero in the creation path.

Configuration and runtime pointers use different strides. The exact side
formulas are:

| Value | Side-indexed manager address |
| --- | --- |
| selected primary character ID | `manager + 0x4C + side * 0x28` |
| selected support ID | `manager + 0x68 + side * 0x28` |
| published primary-fighter alias | `manager + 0xDE4 + side * 4` |
| published `ccCommand`-node alias | `manager + 0xDF0 + side * 4` |

The first pair is configuration consumed to construct or present a battle;
the second pair is populated only after live objects exist. Resident
`FUN_003769C0(side)` is a strict primary-alias accessor: it returns `+0xDE4`
for side `0`, `+0xDE8` for side `1`, and null for every other value.

The audited direct writers also bound the aliases' lifetime. Resident
`FUN_001F4360`, `FUN_001F4680`, and battle teardown `FUN_001EEFD0` clear them;
resident `FUN_001EF330` is the only direct nonzero publisher found. Direct BTL
references to these manager fields read them rather than replacing them.
Several unrelated resident objects are large enough to have fields at the same
numeric offsets, so an offset-only store such as `FUN_001E3C40` writing its own
argument's `+0xDF0` is not evidence of a manager-alias update.

The alias surface is not self-healing. The only decoded direct calls to the
primary creator live `0x00709860` are the side-0 and side-1 calls in initial
graph construction, and the only resident calls to primary lookup live
`0x007099C0` are the two setup-time publications in `FUN_001EF330`. Generic
unlink live `0x00709EA0` and fighter-specific removal in `FUN_0024FD80` do not
clear or republish manager `+0xDE4/+0xDE8`. Removing a fighter from the registry
therefore does not itself invalidate its published borrowed alias. The alias
and registry-membership lifetimes are separate contracts.

### Battle-state and hub publication

The `0x38`-byte battle-state object at `0x00607604` and its construction order
are owned by [Battle lifecycle](battle_lifecycle.md#session-construction). Its
ownership contract with the hub is:

- When battle-state `+0x18` is null, `FUN_001EF330` allocates `0x10` bytes,
  constructs the hub through live `0x00709240`, and stores the same pointer at
  battle-state `+0x18` (owner) and global `0x00607654` (borrowed mirror).
- Live `0x00709480` then creates and cross-links the initial nodes. The
  `ccCommand` nodes are published at manager `+0xDF0/+0xDF4` (live
  `0x00709800`) before the fighters at `+0xDE4/+0xDE8` (live `0x007099C0`), and
  the `ccCamera01` root returned by live `0x007096E0` is stored at battle-state
  `+0x14` as a borrowed alias.
- Live `0x007095E0` then runs the node-start pass (node slot `+0x0C`) across
  all four registries; see
  [Generic node passes](#generic-node-passes).

During teardown (order in
[Battle lifecycle](battle_lifecycle.md#teardown-order)), `FUN_001EEFD0` zeros
all six manager-array entries before calling live `0x00709280(hub, 1)`, then
clears battle-state `+0x18` and global `0x00607654`. The manager never frees a
fighter or `ccCommand` node directly.

## Hub and registry construction

Live `0x00709240` zeros hub `+0x00/+0x04/+0x08/+0x0C` and calls live
`0x007092E0`, which builds:

| Hub field | Allocation | Constructor | Proven registry contents at initial creation |
| ---: | ---: | --- | --- |
| `+0x00` | `0x18` | live BTL `0x006D5640` | one `ccCamera01` main-camera root node |
| `+0x04` | `0x10` | live BTL `0x006F0F90` | two per-side `ccCommand` nodes |
| `+0x08` | `0x34` | resident `FUN_0024E0B0` | two primary fighter nodes |
| `+0x0C` | `0x10` | live BTL `0x00709150` | one `ccField` node |

All four inherit the generic list prefix described below. Their virtual
destructors all clear owned nodes through live `0x00709F40`; the larger
`ccPlayerCtrl` and `ccCameraCtrl` registries also destroy their own additional
state.

### Derived fighter registry/coordinator

Hub `+0x08` is not only the owning intrusive list for fighters. Resident
`FUN_0024E0B0` derives a `0x34`-byte coordinator from the generic container and
installs resident vtable `0x005D9FC0`:

| Vtable slot | Target | Structural effect |
| ---: | ---: | --- |
| `+0x08` | `FUN_0024E250` | destroy all fighter nodes, then owned auxiliaries |
| `+0x0C` | `FUN_002504B0` | dispatch coordinator state, run fighter processing, then live `0x00709C70` removal maintenance |
| `+0x10` | `FUN_00250690` | call live `0x00709D60` over the fighter list, then derived processing |
| `+0x14` | `FUN_00250800` | call live `0x00709DE0` over the fighter list |

The stable derived fields are:

| Registry field | Proven initialization/ownership |
| ---: | --- |
| `+0x14` | coordinator state selector; initialized to `1` and dispatched for values `0..6` |
| `+0x18/+0x1C/+0x20` | state-local words cleared whenever `FUN_0024E380` installs a new selector |
| `+0x24/+0x28` | borrowed fighter references used by state handlers; never freed by this registry |
| `+0x2C` | owned `0xB0`-byte auxiliary; it in turn owns storage at its `+0x40` |
| `+0x30` | owned `0x3C`-byte auxiliary initialized by `FUN_002068A0` |

`FUN_0024E380(registry, state)` writes `+0x14 = state` and clears
`+0x18/+0x1C/+0x20`. The constructor invokes it with state `1`. Resident
`FUN_00250820` returns `+0x14`, or `-1` when the registry is unavailable.

Other subsystems reach this state word through global `0x00607654` → hub
`+0x08` → `+0x14`. Word `+0x14` is the coordinator state, not a pointer, so a
gate that tests that chain for zero is testing **coordinator state == 0**. The
support request and gauge gates in
[Battle support mechanics](support_mechanics.md#manual-request-gates-and-return-states)
use exactly that test; it is not a support-pointer or fighter-count test.

`FUN_0024E250` first destroys every list node through live `0x00709F40`, then
tears down and frees `+0x30`, then frees the nested allocation and object at
`+0x2C`. It does not destroy through `+0x24/+0x28`. State handlers populate
those two fields either from manager `+0xDE4/+0xDE8` or from an explicit
fighter pair, confirming that they are aliases rather than owners.

Normal coordinator maintenance has two removal mechanisms. During
`FUN_0024FD80`, a fighter with node bit 1 set and fighter field `+0x20C < 1`
is unlinked and virtual-destructed through live `0x00709EA0` when its virtual
slot `+0x1C` returns nonzero. The traversal saves node `+0x1C` before the
destruction. `FUN_002504B0` subsequently calls the generic live
`0x00709C70` pass, which independently removes a node for generic flag bit 0
or a nonzero virtual-`+0x10` result. Fighter removal is therefore not limited
to the generic bit-0 request.

### Coordinator timeout-marker check

Coordinator slot `+0x0C`, `FUN_002504B0`, bounds state `+0x14` below `7`
(instruction bytes through `0x00250688`) and dispatches through the seven-entry
table at `0x005C3050..0x005C306B`. State 3 selects `0x0025050C`, which calls
`FUN_0024E960`.

Within `FUN_0024E960`, a missing borrowed fighter at `+0x24/+0x28` resets
words `+0x14/+0x18/+0x1C/+0x20` and returns. With both pointers
present, only local state `+0x18 == 0` with old counter `+0x1C == 0` reads the
timeout marker through `FUN_001EC290` at `0x0024EA38`. A set marker writes
local state 1 and counter 0 at `0x0024EA50..0x0024EA5C`, then bypasses the
clear-marker branch's participant active-bit clears and calls at
`0x0024EA68..0x0024EAE4`. The marker is not retested on later calls with a
nonzero old counter or local state 1. Local state 0 also has an independent
counter-based advance to state 1, so arrival in state 1 alone does not prove
that the marker was set.

`FUN_0024E380` rewrites `+0x14` and clears `+0x18/+0x1C/+0x20` but keeps the
two borrowed pointers, separating this one-time branch choice from participant
lifetime. Neither
this handler nor `0x002504B0` stores to the marker; its producer and reset
belong to [Match outcomes](match_outcomes.md#terminal-detector-and-classifier).
Original state names and broader participant effects remain unresolved.

### Initial graph creation

Live `0x00709480` creates the initial graph in this order:

| Result | Creator | Allocation/initializer | Owning registry |
| --- | --- | --- | --- |
| `ccCamera01` root | `0x00709660` | `0x006DDE10` allocates `0x1D0`, then `0x006D6800` initializes it | hub `+0x00` |
| control side 0 | `0x00709780(hub, 0)` | allocates `0xC0`, calls `0x006EF4E0` | hub `+0x04` |
| control side 1 | `0x00709780(hub, 1)` | allocates `0xC0`, calls `0x006EF4E0` | hub `+0x04` |
| fighter side 0 | `0x00709860(hub, 0)` | character factory dispatch | hub `+0x08` |
| fighter side 1 | `0x00709860(hub, 1)` | character factory dispatch | hub `+0x08` |
| `ccField` node | `0x00709A20` | allocates `0x90`, calls `0x007087A0` | hub `+0x0C` |

Each successful creator appends its result to the owning registry. Allocation
failure leaves that result null and the linker conditionally omits affected
cross-references.

This construction path assumes that its small structural allocations succeed;
it is not a transactional or generally OOM-safe graph builder. Live
`0x007092E0` attempts all four registry allocations independently and publishes
each result, including null. The `ccCameraCtrl` creator checks its registry before
allocating a node, and the fighter creator skips its character factory when
hub `+0x08` is null. In contrast, the control and shared-node creators guard
their newly allocated node but not the destination registry before calling
append. Resident `FUN_001EF330` likewise publishes the possibly null hub and
immediately calls live `0x00709480`; later fighter lookup live `0x007099C0`
assumes hub `+0x08` is nonnull. There is no decoded rollback or failure return
from initial graph creation. Teardown live `0x007093A0` is independently
null-safe for every registry that did become visible.

### Initial cross-reference graph

After successful construction, live `0x00709480` writes:

| Source field | Target |
| --- | --- |
| fighter 0 `+0x20` | fighter 1 |
| fighter 1 `+0x20` | fighter 0 |
| fighter 0 `+0x24` | control 0 |
| fighter 1 `+0x24` | control 1 |
| fighter 0 `+0x28` | `ccField` node |
| fighter 1 `+0x28` | `ccField` node |
| control 0 `+0x20` | fighter 0 |
| control 1 `+0x20` | fighter 1 |
| control 0 `+0x24` | fighter 1 |
| control 1 `+0x24` | fighter 0 |
| `ccCamera01` root `+0x20` | fighter 0 |
| `ccCamera01` root `+0x24` | fighter 1 |

The reciprocal fighter `+0x20` relation agrees with the runtime observations
in [Character identity in battle](character_ids.md); its later null fallback
and opponent-geometry use are owned by
[Target selection](target_selection.md#paired-opponent-and-geometry-refresh).
The ownership proof is
stronger than field shape: all of these targets are ultimately destroyed by
their own registry, not by the referring node.

The `ccField` node demonstrates nested ownership without changing that
conclusion. Its live constructor `0x007087A0` constructs an embedded generic
container at node `+0x60`, allocates an owned `0xAD0`-byte subobject and stores
it at `+0x70`, and initializes both. Its destructor at live `0x007088A0`
destroys/frees `+0x70`, clears the embedded list through `0x00709F40`, then
calls the generic node destructor. Fighter `+0x28` is still only a reference
to this independently registry-owned parent object. The node's embedded
`ccGameObjCtrl` and `ccBgControl` content belongs to
[Stages](stages.md#live-environment-ownership-and-construction).

## Primary-fighter factory and lookup

Live `0x00709860(hub, side)` computes `(side + 1) * 0x28` and reads the
manager's selected character ID from `+0x4C` for side 0 or `+0x74` for side 1.
It builds the common fighter descriptor and dispatches through the first word
of the eight-byte entry at resident `0x005A2900 + character_id * 8`. There is
no BTL-local character-ID bounds check before that indirect call. Entry zero's
factory word is null; entry one begins with factory `0x00250C00`.

All 74 table-selected concrete constructors call resident `FUN_002145D0`
followed by `FUN_002151E0`, with their class setup between those calls. The common base
constructor calls live generic-node constructor `0x00709AA0`.
`FUN_002151E0` copies the selected character record's identity to fighter
`+0x68` and copies descriptor side bit 0 to fighter byte `+0x60` bit 0. The
remaining bits in that byte have separate meanings and are not side IDs.

Successful `FUN_002151E0` initialization also sets generic node flag byte
`+0x00` bits 1 and 2. For the fighter class, bit 1 has a proven narrower
meaning: virtual update `FUN_0024DA50` runs its main fighter-update body only
when bit 1 is set, and coordinator pass `FUN_0024FD80` likewise selects
bit-1 nodes for several derived operations. `FUN_0024DA50` itself returns
zero, so it does not request removal through the generic virtual-return path.
Thus fighter bit 1 is an initialized/update-enabled gate, while generic bit 0
is the independent remove-and-destroy request. Bit 2's broader role is not
assigned here merely because successful initialization also sets it.

The common fighter destructor is resident `FUN_00214840`. It tears down the
common fighter's owned subobjects and embedded lists, calls live generic-node
destructor `0x00709B60` without deleting through that base call, and finally
frees the complete concrete object when its own delete flag requests it.
Every one of the 74 concrete deleting destructors calls
`FUN_00214840(object, 0)`, then frees the complete allocation through resident
`FUN_00117000` only when its own signed 16-bit delete argument is positive.
The zero base argument prevents a second free. Each also calls common fighter
cleanup `FUN_00215720`; class-specific cleanup can precede or follow that call.
Neither the manager alias nor fighter cross-references are used as owners
during this chain.

On success, live `0x00709860` appends the concrete fighter to hub `+0x08`.
Live `0x007099C0(hub, side)` then:

- traverses that registry from `head` through node `+0x1C`;
- compares `(node_u8(+0x60) & 1)` with `side`;
- keeps scanning after a match and returns the **last** matching node; and
- returns null if none matches.

It does not test generic node flag byte `+0x00`. The resident setup calls it
once for each side and publishes the returned aliases at manager
`+0xDE4/+0xDE8`.

### Complete table-selected concrete lifetime paths

The table has 94 rows, occupies resident `0x005A2900..0x005A2BF0`
(exclusive end), and corresponds to ELF file offsets `0x004A2A00..0x004A2CF0`.
Row 0 is `{0, 0}`. The 93 populated rows select exactly 74 distinct factories;
20 rows share factory `0x00250C00`. Their record differences and selector
eligibility are owned by [Character identity in battle](character_ids.md#character-definition-table).

Every factory allocates the size below through `FUN_00117150`, conditionally
calls its constructor when allocation is nonnull, and returns that object.
Every constructor installs the listed vtable at object `+0x50`. The destructor
column is the exact resident pointer read from that vtable's `+0x08` slot.
All addresses in this table are resident addresses, with no overlay bias.

| Character ID(s) | Factory | Allocation | Constructor | Final vtable | Deleting destructor |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1, 8, 9, 20, 21, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 44, 45, 74, 88 | `0x00250C00` | `0x5980` | `0x00250C50` | `0x005DB170` | `0x00250D20` |
| 2 | `0x00253BD0` | `0x58E0` | `0x00253C20` | `0x005DB120` | `0x00253CE0` |
| 3 | `0x002546C0` | `0x5950` | `0x00254710` | `0x005DB0D0` | `0x00254800` |
| 4 | `0x00255810` | `0x5530` | `0x00255860` | `0x005DB0A0` | `0x00255B60` |
| 5 | `0x00258120` | `0x5890` | `0x00258170` | `0x005DB070` | `0x00258230` |
| 6 | `0x00258E50` | `0x5750` | `0x00258EA0` | `0x005DB020` | `0x00258F90` |
| 7 | `0x0025A420` | `0x56C0` | `0x0025A470` | `0x005DAFF0` | `0x0025A530` |
| 10 | `0x0025AAF0` | `0x5280` | `0x0025AB40` | `0x005DAFC0` | `0x0025AC50` |
| 11 | `0x0025B840` | `0x5670` | `0x0025B890` | `0x005DAF90` | `0x0025B950` |
| 12 | `0x0025CC60` | `0x5270` | `0x0025CCB0` | `0x005DAF40` | `0x0025CD70` |
| 13 | `0x0025D920` | `0x5630` | `0x0025D970` | `0x005DAEF0` | `0x0025DA30` |
| 14 | `0x0025EF70` | `0x5040` | `0x0025EFC0` | `0x005DAEA0` | `0x0025F0B0` |
| 15 | `0x002605F0` | `0x5800` | `0x00260640` | `0x005DAE70` | `0x00260700` |
| 16 | `0x00260F40` | `0x5820` | `0x00260F90` | `0x005DAE40` | `0x00261120` |
| 17 | `0x00263600` | `0x5710` | `0x00263650` | `0x005DADF0` | `0x00263730` |
| 18 | `0x00265AC0` | `0x5380` | `0x00265B10` | `0x005DADC0` | `0x00265CD0` |
| 19 | `0x0026BB50` | `0x56B0` | `0x0026BBA0` | `0x005DAD90` | `0x0026BC60` |
| 22 | `0x0026E500` | `0x57C0` | `0x0026E550` | `0x005DAD60` | `0x0026E610` |
| 34 | `0x0026F7A0` | `0x5270` | `0x0026F7F0` | `0x005DAD30` | `0x0026F8B0` |
| 35 | `0x00270730` | `0x50C0` | `0x00270780` | `0x005DAD00` | `0x00270840` |
| 36 | `0x00271DC0` | `0x4A00` | `0x00271E10` | `0x005DACD0` | `0x00271ED0` |
| 37 | `0x002734D0` | `0x5860` | `0x00273520` | `0x005DACA0` | `0x00273610` |
| 38 | `0x00275320` | `0x58B0` | `0x00275370` | `0x005DAC70` | `0x00275460` |
| 39 | `0x00276AD0` | `0x5D40` | `0x00276B20` | `0x005DAC40` | `0x00276BF0` |
| 40 | `0x002788E0` | `0x5030` | `0x00278930` | `0x005DAC10` | `0x00278A20` |
| 41 | `0x0027AC50` | `0x54E0` | `0x0027ACA0` | `0x005DABE0` | `0x0027AD60` |
| 42 | `0x0027B4D0` | `0x52A0` | `0x0027B520` | `0x005DABB0` | `0x0027B5E0` |
| 43 | `0x0027CED0` | `0x5530` | `0x0027CF20` | `0x005DAB80` | `0x0027CFE0` |
| 46 | `0x0027DAE0` | `0x58A0` | `0x0027DB30` | `0x005DAB50` | `0x0027DBF0` |
| 47 | `0x0027E7C0` | `0x5840` | `0x0027E810` | `0x005DAB20` | `0x0027EA60` |
| 48 | `0x00280D90` | `0x59C0` | `0x00280DE0` | `0x005DAAF0` | `0x00280EF0` |
| 49 | `0x00283230` | `0x5E30` | `0x00283280` | `0x005DAAC0` | `0x00283370` |
| 50 | `0x00285510` | `0x50C0` | `0x00285560` | `0x005DAA90` | `0x00285630` |
| 51 | `0x00286850` | `0x5470` | `0x002868A0` | `0x005DAA60` | `0x002869A0` |
| 52 | `0x00287C50` | `0x5270` | `0x00287CA0` | `0x005DAA30` | `0x00287D60` |
| 53 | `0x00288D10` | `0x4AE0` | `0x00288D60` | `0x005DAA00` | `0x00288E60` |
| 54 | `0x0028BF50` | `0x4B70` | `0x0028BFA0` | `0x005DA9D0` | `0x0028C0A0` |
| 55 | `0x00291580` | `0x5400` | `0x002915D0` | `0x005DA9A0` | `0x002916F0` |
| 56 | `0x00294550` | `0x5690` | `0x002945A0` | `0x005DA970` | `0x00294660` |
| 57 | `0x00295D60` | `0x5B60` | `0x00295DB0` | `0x005DA920` | `0x00295FA0` |
| 58 | `0x0029B050` | `0x5690` | `0x0029B0A0` | `0x005DA8F0` | `0x0029B1D0` |
| 59 | `0x0029BC20` | `0x5CC0` | `0x0029BC70` | `0x005DA8C0` | `0x0029BE80` |
| 60 | `0x0029E990` | `0x5630` | `0x0029E9E0` | `0x005DA890` | `0x0029ECC0` |
| 61 | `0x002A49F0` | `0x5720` | `0x002A4A40` | `0x005DA860` | `0x002A4B90` |
| 62 | `0x002A8DF0` | `0x5D00` | `0x002A8E40` | `0x005DA830` | `0x002A90A0` |
| 63 | `0x002AE9B0` | `0x5140` | `0x002AEA00` | `0x005DA800` | `0x002AEBE0` |
| 64 | `0x002B3790` | `0x5C00` | `0x002B37E0` | `0x005DA7D0` | `0x002B3A00` |
| 65 | `0x002B7240` | `0x5F00` | `0x002B7290` | `0x005DA780` | `0x002B7380` |
| 66 | `0x002B8AE0` | `0x5CC0` | `0x002B8B30` | `0x005DA750` | `0x002B8C80` |
| 67 | `0x002BCC60` | `0x6880` | `0x002BCCB0` | `0x005DA700` | `0x002BD0B0` |
| 68 | `0x002C03A0` | `0x5C70` | `0x002C03F0` | `0x005DA6D0` | `0x002C0530` |
| 69 | `0x002C1BA0` | `0x69C0` | `0x002C1BF0` | `0x005DA680` | `0x002C1E00` |
| 70 | `0x002C6510` | `0x5870` | `0x002C6560` | `0x005DA650` | `0x002C6630` |
| 71 | `0x002C8E70` | `0x5710` | `0x002C8EC0` | `0x005DA600` | `0x002C9030` |
| 72 | `0x002CBC10` | `0x5090` | `0x002CBC60` | `0x005DA5D0` | `0x002CBD20` |
| 73 | `0x002CE550` | `0x5840` | `0x002CE5A0` | `0x005DA5A0` | `0x002CE8C0` |
| 75 | `0x002D2A10` | `0x5660` | `0x002D2A60` | `0x005DA570` | `0x002D2BA0` |
| 76 | `0x002D4280` | `0x4F40` | `0x002D42D0` | `0x005DA540` | `0x002D4410` |
| 77 | `0x002D7D20` | `0x6F60` | `0x002D7D70` | `0x005DA510` | `0x002D7F10` |
| 78 | `0x002DAEA0` | `0x6260` | `0x002DAEF0` | `0x005DA4E0` | `0x002DB030` |
| 79 | `0x002E2A70` | `0x50E0` | `0x002E2AC0` | `0x005DA4B0` | `0x002E2C60` |
| 80 | `0x002E6490` | `0x6230` | `0x002E64E0` | `0x005DA440` | `0x002E6800` |
| 81 | `0x002E8BC0` | `0x6240` | `0x002E8C10` | `0x005DA3D0` | `0x002E8CF0` |
| 82 | `0x002EB3C0` | `0x5D80` | `0x002EB410` | `0x005DA3A0` | `0x002EB530` |
| 83 | `0x002EBEF0` | `0x54C0` | `0x002EBF40` | `0x005DA370` | `0x002EC080` |
| 84 | `0x002EE150` | `0x5950` | `0x002EE1A0` | `0x005DA340` | `0x002EE2B0` |
| 85 | `0x002EFF80` | `0x59F0` | `0x002EFFD0` | `0x005DA310` | `0x002F00D0` |
| 86 | `0x002F0F00` | `0x5750` | `0x002F0F50` | `0x005DA2E0` | `0x002F1060` |
| 87 | `0x002F18E0` | `0x5630` | `0x002F1930` | `0x005DA2B0` | `0x002F1A70` |
| 89 | `0x002F3B40` | `0x5900` | `0x002F3B90` | `0x005DA280` | `0x002F3C60` |
| 90 | `0x002F83B0` | `0x52C0` | `0x002F8400` | `0x005DA250` | `0x002F84F0` |
| 91 | `0x002FB1D0` | `0x5AD0` | `0x002FB220` | `0x005DA1E0` | `0x002FB3E0` |
| 92 | `0x002FD5D0` | `0x5310` | `0x002FD620` | `0x005DA190` | `0x002FD7A0` |
| 93 | `0x00300090` | `0x6200` | `0x003000E0` | `0x005DA140` | `0x003003D0` |

The minimum allocation is `0x4A00` (ID 36); the maximum is `0x6F60`
(ID 77). These are complete concrete allocation sizes, not sizes of the common
fighter prefix or total nested heap consumption.

All 74 constructors set generic node bit 0 when `FUN_002151E0` returns
nonzero, but still return the constructed object. The hub creator appends a
nonnull returned fighter without testing that bit. An initialization error
therefore requests later list removal rather than synchronous factory rollback.
Lookup can still select that linked removal-requested node because it ignores
the flag byte. This is a static failure-path contract; its occurrence during
ordinary play is not established.

Concrete classes can own extra children; their combat methods belong to
[Character action callbacks](character_action_callbacks.md#complete-bounded-classslot-census).
For example, ID 78's constructor `0x002DAEF0` publishes allocated
children at `+0x6254/+0x6258`; destructor `0x002DB030` cleans and frees those
before the common fighter destructor. ID 80's destructor `0x002E6800` cleans
and frees `+0x6210/+0x6214/+0x6218`, two `+0x621C` entries, and two
`+0x6224` entries. ID 92's destructor `0x002FD7A0` similarly cleans
`+0x5300/+0x5304/+0x5308`. These remain children of the concrete fighter;
they are not additional primary slots in the hub or manager alias arrays.

### Common fighter-owned children

The common base table `0x005D9FE0` points through resident RTTI
`0x005C30A8` to string `ccPlayer` at `0x004080C8`. Concrete class tables
replace that base table during construction. All 74 concrete destructors call
both `FUN_00215720` and `FUN_00214840(object, 0)` before their final free.
Those common routines establish the following child lifetimes:

| Fighter region | Storage/ownership | Teardown evidence |
| ---: | --- | --- |
| `+0xE68/+0xE6C/+0xE70/+0xE74` | four optional owning handle slots | `FUN_00215E70` calls `FUN_00199190`, `FUN_001951A0`, `FUN_001B7570`, and `FUN_0018B4C0`, respectively, with delete flag `1`, then nulls each slot |
| `+0x950` | optional allocated list owner and its allocated nodes | `FUN_00215720` follows owner head `+0x04` and node next `+0x18`, releases each optional node `+0x14` handle through `FUN_00199190(..., 1)`, frees nodes and owner, and nulls fighter `+0x950` |
| `+0xB30` | optional allocated owner, its `+0x00` handle, and its child list | `FUN_00215720` follows owner head `+0x10` and child next `+0x0C`, releases child `+0x00` through `FUN_00196990(..., 1)`, frees children, releases owner `+0x00` through `FUN_001B7570(..., 1)`, frees owner, and nulls fighter `+0xB30` |
| `+0x8C4` and nested `+0x8D8` | embedded owning generic lists | constructor `FUN_00304F40` and destructor `FUN_00304F90(..., -1)`; both lists are cleared through live `0x00709F40` without separately freeing embedded storage |
| `+0xBD0/+0xC80/+0xD30` | three embedded arrays, each containing two `0x50`-stride objects | construction through `FUN_00119290` with `FUN_001BEA30`; reverse array teardown through `FUN_00119220` with `FUN_001BEA90` |
| `+0xDD0/+0xDF4/+0xE18` | three embedded resident-managed objects | constructed through `FUN_001DD8D0`; destroyed in reverse order through `FUN_001DD920(..., -1)` |
| `+0xEA4` | embedded derived owning generic container | generic constructor live `0x00709BC0`; `FUN_00214840` clears its nodes through live `0x00709F40`, without a separate container allocation free |

The `+0x950` cleanup also passes node `+0x0C` to
`FUN_00196620(handle, 0, 0, 0)`. That call alone does not establish ownership
of the referenced handle, so it is not classified as another owned child.
`FUN_00215720` additionally releases and clears the per-side global at
`0x006076B8 + side * 4`; its combo-state layout and behavior belong to
[Damage](damage.md#native-combo-owner).

`FUN_002145D0` also constructs an embedded generic node at `+0x7D0` and
seven `0x24`-stride objects at `+0x1B8..+0x290`. `FUN_00214840` calls the
embedded node destructor with `-1`, restores the seven objects' tables, and
calls the outer generic-node destructor with `0`. Embedded addresses are
therefore subobjects of the same fighter allocation, not independent primary
entities or separately freed outer allocations.

### Bounded creation and mutation-route coverage

Resident constructor cross-references for each of the 74 table-selected
classes contain one direct call, from that class's allocating factory. A scan
for all 74 encoded constructor `jal` targets found no matches in BTL. The BTL
factory-table materialization was found in the known hub creator; inspected
resident uses of low immediate `0x2900` with a different high half address
`0x006B2900`, not the character table at `0x005A2900`.

Exact little-endian stored pointers to live generic append `0x00709E60`,
unlink `0x00709EA0`, and primary creator `0x00709860` were absent from both
the resident ELF and BTL memory scans. This closes those exact-address callback
candidates. It does not exclude addresses assembled from other constants,
register-computed calls, or containers reached through indirect data. The known
direct startup route and teardown graph are established; a global absence of
other creation or registry-mutation routes is not.

## `ccCommandCtrl` per-side control registry

Live `0x00709780` allocates a `0xC0` `ccCommand` node, calls live
`0x006EF4E0(node, side)`,
and appends the result to hub `+0x04`. The constructor calls the generic node
constructor, installs its own vtable, initializes owned storage, and calls
live `0x006EF600` for side binding.

The stable side-binding fields are:

| `ccCommand` field | Proven value/role |
| ---: | --- |
| `+0x60` | `u32` side, exactly `0` or `1` in this creation path |
| `+0x64` | pointer to `0x006073FC + side * 0x78 + 0x1C`, a per-side input-state slice |
| `+0x14` | side-specific callback/data pointer: `0x008A8160` or `0x008A8170` |
| `+0x94` | owned allocated storage; freed by the node destructor |

If global input state `0x006073FC` is missing, or its required allocation
fails, `0x006EF600` sets generic flag byte `+0x00` bit 0 so the container's
removal pass will destroy the node. Successful setup sets generic bit 1. That
bit-1 write is a class-specific setup result; it is not the generic container's
removal predicate.

Live `0x00709800(hub, side)` scans hub `+0x04`, compares the full `u32` at node
`+0x60`, and returns the last matching node. Like the fighter lookup, it does
not test generic flag bit 0. Resident setup publishes its two results at
manager `+0xDF0/+0xDF4`. These pointers are control/input-history objects, not
support fighters.

## `ccCameraCtrl` current-node semantics

Hub `+0x00` is the `ccCameraCtrl` camera registry, and its initial `0x1D0`
node is the `ccCamera01` main camera; node key `+0xA8` is the camera's output
object. The camera classes are described in [Battle camera](battle_camera.md).

The `0x18`-byte container at hub `+0x00` extends the generic list prefix with:

| `ccCameraCtrl` field | Proven behavior |
| ---: | --- |
| `+0x10` | current/new node pointer |
| `+0x14` | previous node with the same lookup key, or null |

Live `0x00709660` obtains this registry, creates the initial `0x1D0` node, and
passes it to live `0x006D57A0`. That inserter looks for an existing node whose
`u32 +0xA8` equals the new node's key, clears the old node's class-specific
bit 1 and byte `+0x60`, appends the new node, records old/new at container
`+0x14/+0x10`, and sets new node byte `+0x60 = 1`. Thus byte `+0x60` is a
proven current/active marker for this registry specialization.

The relevant lookups are:

- live `0x006D5900(container, key)` returns the last node whose `+0xA8` equals
  `key`, regardless of its `+0x60` marker;
- live `0x006D5960(container, key, wanted_current)` additionally compares
  node byte `+0x60` with `wanted_current & 1`;
- hub wrapper live `0x00709740(hub, key)` calls `0x006D5960` with
  `wanted_current = 1`; and
- live `0x007096E0(hub)` returns the last `ccCameraCtrl` node whose generic-base
  word `+0x10` is zero. `0x00709660` explicitly writes zero there when the
  initial insertion makes the registry count one, and resident setup stores
  the lookup result at battle-state `+0x14`.

Duplicate camera keys are part of the retail graph: the main camera and the
controller's four slot cameras all use output object `0x00609160`. The four
slot cameras enter through plain append live `0x00709E60` and start with
`+0x60 = 0`. A last-key lookup can therefore return an inactive camera;
filtered lookup and the registry's current pointer are separate interfaces.
Live `0x006D5A50` stores the borrowed output object at node `+0xA8` and an
independently allocated `0x50`-byte engine camera at `+0xA4`. Camera ownership
and switching details belong to [Battle camera](battle_camera.md#camera-classes-and-activation).
The original domain meaning of generic-base selector word `+0x10` remains
unassigned beyond its proven startup/root selection.

## Generic intrusive node and list contracts

### Container prefix

Live `0x00709BC0` initializes the shared container prefix:

| Offset | Type | Meaning |
| ---: | --- | --- |
| `+0x00` | `u32` | node count |
| `+0x04` | pointer | head node |
| `+0x08` | pointer | tail node |
| `+0x0C` | pointer | container vtable |

Live `0x00709E60(container, node)` appends at the tail, writes node
`+0x18 = old_tail` and `+0x1C = null`, repairs head/tail links, and increments
the count.

Live `0x00709EA0(container, node)` splices `node` out through its
`+0x18/+0x1C` links, repairs head/tail, decrements the count, then calls node
virtual destructor slot `+0x08` with delete flag `1`. Live `0x00709F40`
retains each next pointer before repeatedly calling `0x00709EA0`, so a
container owns and destroys all of its linked nodes.

### Node prefix

Live `0x00709AA0` initializes this stable node prefix:

| Offset | Type | Proven initialization/use |
| ---: | --- | --- |
| `+0x00` | flag byte | bits 0, 1, and 2 cleared by the base constructor |
| `+0x02` | `u16` | live marker `0x474F`; cleared by the base destructor |
| `+0x04` | `u32` | zero |
| `+0x08` | `u32` | zero |
| `+0x0C` | `s32` | `-1` |
| `+0x10` | `s32` | `-1`; specialized by `ccCameraCtrl` |
| `+0x14` | pointer | base callback/data pointer `0x00604B60`, replaceable by subclasses |
| `+0x18` | pointer | previous intrusive-list node |
| `+0x1C` | pointer | next intrusive-list node |
| `+0x20..+0x2C` | four pointers | zero; subclass cross-reference slots |
| `+0x40..+0x4C` | 16 bytes | zero |
| `+0x50` | pointer | node vtable |

Live `0x00709B60` restores the base vtable, clears marker `+0x02`, and frees
the node when requested.

### Generic node passes

Every hub registry node carries its vtable at node `+0x50`. The generic
container walkers fix the meaning of five node slots:

| Node slot | Walker (live / raw / export) | Contract |
| ---: | --- | --- |
| `+0x08` | `0x00709EA0` / `0x055FA0` / `0x00709E60`, reached from removal and from container destruction through `0x00709F40` | virtual destructor, called with delete flag `1` after unlink |
| `+0x0C` | `0x00709BF0` / `0x055CF0` / `0x00709BB0` | node start; the hub broadcast `0x007095E0` runs it across all four registries once after initial graph construction |
| `+0x10` | `0x00709C70` / `0x055D70` / `0x00709C30` | phase-1 update; removal rule below |
| `+0x14` | `0x00709D60` / `0x055E60` / `0x00709D20` | phase-2 callback on each node |
| `+0x18` | `0x00709DE0` / `0x055EE0` / `0x00709DA0` | phase-3 callback on each node |

Live `0x00709C70` saves `next` before operating on a node. If node flag byte
`+0x00` bit 0 is set, it immediately unlinks and destroys that node without
calling slot `+0x10`. Otherwise it calls node slot `+0x10`; a nonzero return
also unlinks and destroys the node. Bit 0 therefore means **remove on the next
phase-1 pass**. A clear bit proves only that this immediate removal request is
absent; it does not by itself prove every higher-level meaning of “active.”
Class-specific uses of bits 1 and 2 (for example the fighter's update gate) are
not part of this generic contract.

The registries reach these walkers through container vtable slots `+0x0C`,
`+0x10`, and `+0x14` (phases 1, 2, and 3; container slot `+0x08` is the
registry destructor). `ccCommandCtrl` and `ccFieldCtrl` use the generic thunks
`0x006D67E0`, `0x006D67A0`, and `0x006D67C0` for those three slots;
`ccCameraCtrl` uses `0x006D59D0` for the same phase-1 walk; `ccPlayerCtrl`
overrides all three with its coordinator methods (see
[Derived fighter registry/coordinator](#derived-fighter-registrycoordinator)).
The node-start slot is the empty return `0x006D6770` for `ccCamera`,
`ccDummyCamera`, `ccPMCCamera`, `ccCamera01`, and `ccField`; `ccCommand`
supplies `0x006F0DF0`. When each phase runs during a battle update is owned by
[Battle lifecycle](battle_lifecycle.md#per-update-dispatch).

## Transient-actor manager and side ownership

BTL maintains a second, independent entity owner for a large family of
transient battle actors. Its global pointer is `0x00607820`; this is not one of
the four hub registries and is not an alias in the resident `0x00607600`
manager. Resident `FUN_001EF330` calls live `0x00735E70` after it has created
and published the hub graph. That BTL function allocates `0xD0` bytes, calls
live `0x007343A0`, and publishes the result at `0x00607820`.

Resident `FUN_001EEFD0` calls live `0x00735F30` during teardown. The BTL
teardown destroys every transient actor, destroys the manager's embedded and
pointed-to auxiliaries, frees the `0xD0` manager, and clears `0x00607820`.
This happens before the resident primary-fighter aliases are cleared and
before the hub is destroyed, so transient-actor destructors can still resolve
their owning primary fighter during normal teardown.

The stable ownership prefix of the `0xD0` manager is:

| Offset | Type | Proven role |
| ---: | --- | --- |
| `+0x0C` | `u32` | current number of linked transient actors |
| `+0x10` | `u32` | next serial; incremented on insertion and not decremented on removal |
| `+0x14` | pointer | first actor |
| `+0x18` | pointer | last actor |
| `+0x1C` | pointer | owned `0x08`-byte deferred-child-list owner |
| `+0x20` | `u8` | when nonzero, live `0x00734BA0` skips its actor update/removal pass |
| `+0x21` | `u8` | independently gates a second actor pass |
| `+0x2C` | embedded object | constructed by resident `FUN_001C4470` and destroyed by `FUN_001C4410` |

The actor chain is singly linked. Actor `+0x60` is `next`, byte `+0x86`
records whether the actor is linked, and word `+0x8C` receives the manager's
pre-increment `+0x10` serial. Live `0x00734AD0` unlinks an actor, fixes
head/tail, clears `+0x86`, and decrements manager `+0x0C`; it deliberately does
not decrement the serial source. Base reset live `0x0072B4A0` initializes
`+0x86` to zero, while the final insertion block in live `0x00736080` sets it
to one. Unlink refuses an actor whose marker is already zero and does not clear
the removed actor's `+0x60`, so `+0x86` is the authoritative linked/unlinked
state; `+0x60 != 0` alone is not proof of membership.

Live `0x00734BA0` saves `next` before calling each actor. It first calls common
actor work at live `0x0072C8B0`, then actor vtable slot `+0x44`. A zero result
from that slot causes live `0x00734AD0` followed by virtual destruction through
slot `+0x08`. Live `0x007349C0`, used for whole-manager teardown, removes and
virtual-destroys every actor from tail to head. Thus the `0x00607820` manager,
not the primary fighter or hub list, owns these actor lifetimes.

The two manager pass gates are independent and have exact global setters:

| Manager byte | Processing it suppresses when nonzero | Set helper | Clear helper |
| ---: | --- | ---: | ---: |
| `+0x20` | live `0x00734BA0`: common actor work, virtual `+0x44` keep/remove decision, and deferred-child recycle pass | `0x00735DF0` | `0x00735E10` |
| `+0x21` | live `0x00734D30`: actor virtual `+0x48` pass and a second deferred-child pass | `0x00735E30` | `0x00735E50` |

The second actor pass calls virtual slot `+0x48` only for nodes whose signed
byte `+0x206` is nonzero, then live `0x00708720` visits every deferred child.
The domain meaning of actor `+0x206` is not established. These gates suppress
manager traversal; they do not change `+0x86` membership or unlink actors.
Although this actor family inherits the generic node base, its normal removal
decision is the virtual `+0x44` result above, not generic node flag-byte bit 0.

Object lookup is available in two independent namespaces:

- live `0x00735F90(serial)` scans the global manager from `+0x14` through actor
  `+0x60` and returns the first actor whose `+0x8C` serial matches;
- live `0x00735910(manager,type,side_selector)` returns boolean existence for
  the same type/side predicate;
- live `0x00735990(manager,type,side_selector,cursor)` starts at the head when
  `cursor == 0`, otherwise at `cursor->next`, and returns the next actor whose
  signed `+0x78` type and side-selector mapping match; and
- live `0x00735A30(manager,type,side_selector)` counts the same matches.

The side-selector lookup convention is deliberately inverted from the stored
actor affiliation: actor `+0x8A == 0` matches selector `1`, actor `+0x8A == 1`
matches selector `0`, and any other value matches `-1`. The selector's domain
meaning is not assumed here.

Manager `+0x10` starts at zero. Insertion stores its pre-increment value in
actor `+0x8C`, so serial zero is valid for the first actor. Removal does not
decrement the source, and lookup tests no flag beyond reachability from the
manager head. This serial allocator has no decoded live-serial collision check
at 32-bit wrap; if duplicates ever coexist,
live `0x00735F90` returns the first linked match.

### Factory, descriptor, and side mapping

Live `0x00736080` is the common create-and-link wrapper. It accepts only
selector `0` or `1`; any other value returns null. It computes
`stored_side = selector ^ 1`, calls class factory live `0x00729890`, calls
initializer live `0x0072B1F0`, installs initial transform/state through virtual
slot `+0x54`, and finally links the actor into the global manager. There are
87 decoded direct BTL calls to this wrapper.

After a valid selector, the wrapper does not test the class-factory result for
null before calling the initializer and dereferencing it. This path assumes
allocation/factory success and has no decoded partial-construction rollback.
Publication itself is guarded by byte `+0x86`: an object already marked linked
is not inserted or counted again. A normal new object is appended at the tail,
marked `+0x86 = 1`, assigned the pre-increment serial, and counted; only then is
its optional `+0x70` child registered with manager auxiliary `+0x1C`.

The class factory indexes the descriptor table at `0x008AC910` with a
`0x68`-byte stride. Descriptor byte `+0x02` selects one of 103 decoded class
construction cases; those cases allocate class-dependent sizes and converge
on a common returned actor pointer. The initializer then establishes these
stable fields:

| Actor offset | Type | Proven role |
| ---: | --- | --- |
| `+0x50` | pointer | class vtable |
| `+0x60` | pointer | next actor while linked in the transient manager |
| `+0x74` | pointer | borrowed pointer to the actor's `0x68`-byte static descriptor |
| `+0x78` | `s16` | actor type/descriptor index passed to the initializer |
| `+0x7A` | `s16` | copy of descriptor `+0x00` |
| `+0x86` | `u8` | manager-linked marker |
| `+0x8A` | `s8` | stored actor affiliation side, or `-1` while reset |
| `+0x8C` | `u32` | manager-assigned serial |

Live constructor `0x0072B190` calls the generic node constructor. Reset helper
live `0x0072B4A0` initializes signed byte `+0x8A` to `-1`; initializer live
`0x0072B1F0` stores its fourth argument there. In the common wrapper that
fourth argument is `stored_side = selector ^ 1`, so the wrapper's selector
argument is the inverse of the stored owner side.

Three small live helpers resolve the stored affiliation tag:

| Live helper | Raw | Input `node + 0x8A` | Result |
| --- | ---: | --- | --- |
| `0x00734130` | `0x080230` | `0` / `1` / other | opposite side `1` / `0` / `-1` |
| `0x00734160` | `0x080260` | `0` / `1` / other | opponent fighter at manager `+0xDE8` / `+0xDE4` / null |
| `0x007341A0` | `0x0802A0` | `0` / `1` / other | own fighter at manager `+0xDE4` / `+0xDE8` / null |

Decoded direct BTL calls number 34 to `0x00734130`, 52 to `0x00734160`, and
50 to `0x007341A0`. This is a common
side-owner convention for that actor family. Field `+0x8A` is a side tag, not
a parent pointer, and the manager's primary-fighter aliases supply the actual
ownership context. It is not proven to be universal across every BTL node
class.

### Deferred child ownership

Actor `+0x70` is an optional child handle created only for descriptor child
kinds `1` or `2`. Live `0x0072B1F0` allocates `0x4C` bytes, constructs that
child at live `0x00707350`, stores it at actor `+0x70`, and gives the child a
borrowed pointer at child `+0x2C` to the parent's embedded `+0x180` data. If the
manager's `+0x1C` auxiliary exists, live `0x00736080` registers the child with
live `0x00708570`.

The auxiliary is the actual child owner. Its `+0x00` is a count and `+0x04` is
the newest/head child; child `+0x48` links to the next child. Live
`0x00708480` destroys all registered children and optionally frees the
auxiliary itself.

The parent therefore does not directly free `+0x70`. Both actor unlink live
`0x00734AD0` and base cleanup live `0x0072B9B0` set child byte `+0x00` to `1`
and clear actor `+0x70`. Live auxiliary maintenance `0x00708630` lets that
child drain its internal work; live `0x00707920` advances child state from
`1` to `2` once drained. On a later pass, state `>= 2` makes the auxiliary
unlink and virtual-destroy it. This proves a deferred parent-release / manager-
owned-child relationship rather than immediate recursive ownership.

## Dynamic support-object owner

The resident manager fields `+0x68/+0x90` are the selected support-list IDs for
sides 0/1, and `manager + 0x6C + side * 0x28` is the derived implementation
selector. Their configuration writers, sentinel resolution, and code mapping
are owned by
[Battle support mechanics](support_mechanics.md#setup-and-selected-support).
None is consumed by the initial graph creator:

- live `0x00709860` reads only manager `+0x4C/+0x74`, the selected **primary
  character** IDs;
- live `0x00709480` creates exactly two primary fighters, two `ccCommand`
  nodes, one `ccCamera01` node, and one `ccField` node; and
- resident `FUN_001EF330` publishes only primary-fighter and `ccCommand`
  aliases in the two three-entry manager arrays.

Setup live `0x00886250` replaces a support-ID value of `0x26` with the
resolved support-list ID in that same field and stores the derived selector at
`+0x6C`. Sentinel `0x26` is therefore configuration resolved before battle; it
is not an entity pointer, list index, or persistent runtime slot.

### Separate owner and exact side slots

The dynamic support owner is global `0x00607888` (`$gp - 0x3168`), independent
of both the hub and transient-actor manager. Resident `FUN_001EC7A0`, after
selecting BTL, calls live `0x00885210`. That function resets support-side global
counters, virtual-destroys any previous owner, allocates `0x24` bytes, calls
live constructor `0x00886CB0`, and publishes the result. Resident
`FUN_001EC890` calls live `0x00885290`, which virtual-destroys this owner and
clears the global.

Its retail class is `ccBuddyAtkCtrl`: resident table `0x005FC2C8` points to
live RTTI `0x008D3388`, whose name pointer is live `0x008BFD70`. The
embedded allocator table `0x005FC2D8` similarly points through live
`0x008D3390` to `ccBdySerialNo` at `0x008BFD80`. Primary table slot `+0x08`
is live `0x00886DE0`: it calls `0x00887990(owner, -1)` to destroy and null
both children, restores the embedded table, and frees the outer owner only
when its signed 16-bit delete argument is positive. Resident table/overlay ABI
details belong to [Overlay ABI](../runtime/overlay_abi.md).

The stable manager layout is:

| Offset | Type | Proven role |
| ---: | --- | --- |
| `+0x00` | pointer | owner vtable |
| `+0x04` | pointer | owning side-0 / Player-1 support-object slot |
| `+0x08` | pointer | owning side-1 / Player-2 support-object slot |
| `+0x0C..+0x11` | two 3-byte side records | configuration/control bytes detailed below; not pointers or occupancy |
| `+0x14` | embedded object | `ccBdySerialNo` generation-ID allocator vtable; allocator contract in [Request, class creation, and repeated calls](#request-class-creation-and-repeated-calls) |
| `+0x18` | `u32` | next support-object generation ID (allocator `+0x04`), initialized to `1` |
| `+0x1C` | `u8` | allocator wrap/reuse marker (allocator `+0x08`), initialized to zero |
| `+0x20` | `u8` | manager-local one-shot latch, initialized to one and cleared by the main pass |

The constructor clears both slots and initializes both side records to
`{0, 1, 0}`. No support object is appended to the hub registries or the
`0x00607820` transient-actor chain.

Each side record is `owner + 0x0C + side * 3`:

| Record byte | Initialization | Proven later writer/use |
| ---: | ---: | --- |
| `+0x00` | `0` | support color variant; written by setup live `0x00886250` from color resolver live `0x00885CE0` |
| `+0x01` | `1` | Linked Mode: Manual (`0`) / Auto (`1`), the Practice row-4 setting in [Practice mode](practice_mode.md#rows-local-values-and-manager-storage); getter live `0x00882630`, setter live `0x00882670` |
| `+0x02` | `0` | recharge-rate class; written by setup live `0x00886250` (default `2`); read by resident `FUN_002380C0` to initialize fighter `+0x78` |

These are per-side scalar state; no getter, setter, or normalization path
follows them as addresses. Support presence means the pointer stored at
`owner + 0x04 + side * 4` is nonnull. The color rules, resolved-code and
recharge tables, and each byte's request and gauge effects belong to
[Battle support mechanics](support_mechanics.md#ownership-model). The selected
support-list ID, derived implementation code, three-byte side record, and
live object slot are separate storage and identity domains.

BTL also keeps a separate BSS array of three signed 16-bit counters per side at
`0x008DCE90 + side * 6`, zeroed by live `0x00886BB0`. The first is incremented
after each successful new support allocation and read by live
`0x00886C20(side)` (resident caller `0x00224280`); slot destruction does not
decrement it. The second is incremented inline at live `0x00889850` by the
common reason handler `0x00889540`, which takes the side from support byte
`+0xE4`; an invalid side there reaches an explicit zero-address assertion. The
third is adjusted only through live `0x00886C60(side, delta)`, called from the
lineage path at live `0x00886B3C`. Their meanings and reset conditions belong to
[Battle support mechanics](support_mechanics.md#support-counters-and-notification-suppression).
None is an object pointer, current occupancy count, or generation ID.

### Request, class creation, and repeated calls

Resident manual request handler `FUN_00238340` (gates and return handling in
[Battle support mechanics](support_mechanics.md#manual-request-gates-and-return-states),
including the coordinator-state test described in
[Derived fighter registry/coordinator](#derived-fighter-registrycoordinator))
calls live `0x00885490(fighter_side)`, which follows global `0x00607888` and
calls live `0x008872E0(owner, side)`. The resident function does not allocate;
this BTL call is the class factory and publisher.

For side `0/1`, the factory uses exact slot
`owner + 0x04 + side * 4` and reads the derived class selector from resident
manager `+0x6C + side * 0x28`. If the selector is `>= 0x44`, it returns zero.
The decoded cases allocate class-dependent sizes from `0x510` through `0x540`,
construct a common support-object base and any specialization, store the object
in its side slot, and invoke virtual initializer `+0x1C(selector, side)`. The
new object receives generic node flag-byte bits 1 and 2, receives its generation
ID at `+0x120`, and the request returns `1`.

If the side slot is already occupied, the factory neither appends nor replaces
the object; it returns `2` or `0` from the existing object's virtual `+0x24`
query. Thus this owner implements two fixed **dynamic** side slots, with at
most one fielded support object per side, not a general list and not a pair of
pre-created startup entities.

For a new object, the precise publication order is significant. Every class
allocation is checked before its constructor, but all cases then converge on
the slot store at live `0x008876C8`, which unconditionally stores the result
into the selected owner slot and immediately dereferences its vtable. A null
allocation therefore does not produce a clean request failure; the path
assumes allocation success. With a valid object, the slot becomes visible
**before** virtual initializer `+0x1C` runs, before flag bits 1 and 2 are set,
and before generation `+0x120` is assigned. Generation assignment snapshots
both current slots after this publication (the new constructor-cleared
`+0x120` contributes zero), calls the allocator at live `0x00887778`, stores
the returned ID, and only then increments the side's cumulative creation
counter and returns `1`. No alternate slot or rollback pointer is retained.

The factory branch bodies span live `0x008872E0..0x00887808` (raw
`0x1D33E0..0x1D3908`). The split is structural rather than semantic: all
selectors below `0x44` not named in the table use the default row. “Final
vtable” is the pointer present when the common virtual initializer is invoked;
several small specializations call a broader constructor and then replace its
vtable (intermediate table `0x005FC0C0` is replaced for `0x15..0x17` and
`0x38`). The 14 final tables are resident data at `0x005FBB40..0x005FC2B7`
(ELF file `0x4FBC40..0x4FC3B7`), although their methods point into BTL. The
attack slot `+0x54` and reason slot `+0x48` columns identify the shared or
overriding bodies whose behavior is described in
[Battle support mechanics](support_mechanics.md#factory-variants-and-attack-completion).

| Implementation selector(s) | Allocation | Construction path | Final vtable | Attack slot `+0x54` | Reason slot `+0x48` |
| --- | ---: | --- | ---: | ---: | ---: |
| default in `0x00..0x43` | `0x510` | common live `0x00887A60` | `0x005FC240` | `0x0088A820` | `0x00889540` |
| `0x0A` | `0x520` | live `0x0088DAB0` | `0x005FBD40` | `0x0088DC70` | `0x0088DB00` |
| `0x0C` | `0x510` | common constructor, then vtable replacement | `0x005FBE40` | `0x0088D780` | `0x00889540` |
| `0x11` | `0x510` | common constructor, then vtable replacement | `0x005FBEC0` | `0x0088D680` | `0x00889540` |
| `0x15`, `0x16`, `0x17` | `0x520` | live `0x0088CC60`, then vtable replacement | `0x005FC040` | `0x0088A820` | `0x00889540` |
| `0x19` | `0x530` | live `0x0088E000` | `0x005FBCC0` | `0x0088E0A0` | `0x0088E050` |
| `0x1E` | `0x520` | live `0x0088C890` | `0x005FC1C0` | `0x0088C8E0` | `0x00889540` |
| `0x1F` | `0x510` | common constructor, then vtable replacement | `0x005FC140` | `0x0088A820` | `0x00889540` |
| `0x21` | `0x540` | live `0x0088D2D0` | `0x005FBF40` | `0x0088D320` | `0x0088D640` |
| `0x24` | `0x510` | common constructor, then vtable replacement | `0x005FBDC0` | `0x0088A820` | `0x00889540` |
| `0x2A` | `0x510` | common constructor, then vtable replacement | `0x005FBC40` | `0x0088A820` | `0x00889540` |
| `0x2B` | `0x520` | live `0x0088E460` | `0x005FBBC0` | `0x0088E540` | `0x0088E500` |
| `0x38` | `0x520` | live `0x0088CC60`, then vtable replacement | `0x005FBFC0` | `0x0088A820` | `0x00889540` |
| `0x3F` | `0x530` | live `0x0088E5F0` | `0x005FBB40` | `0x0088E790` | `0x0088E640` |

Generation IDs come from the embedded `ccBdySerialNo` allocator at owner
`+0x14`, live `0x00886950` (raw `0x1D2A50`; no recognized function at export
`0x00886910`). Its only direct call is the request path at live `0x00887778`
(raw `0x1D3878`). Allocator `+0x04` (owner `+0x18`) is the current candidate
and allocator `+0x08` (owner `+0x1C`) is the reuse marker:

- With the marker clear, it returns the current candidate and increments it.
  When the candidate is `0xFFFFFFFF`, it returns that value, sets the reuse
  marker, resets the stored candidate to zero, and the common increment leaves
  the next candidate at `1`.
- With the marker set, it compares the same current candidate with the
  supplied two-entry array of slot generations (zero for an empty slot). A
  non-colliding candidate is returned. A collision rescans the same candidate,
  up to the supplied count plus one, without advancing it, then returns zero.
  Both paths increment the stored candidate exactly once; no alternate free ID
  is searched inside the call.

The comparisons load allocator `+0x04` at live `0x00886990`; the only
candidate stores are the wrap reset at `0x00886A20` and final increment at
`0x00886A2C`. The caller publishes the result at support `+0x120` and still
returns creation success, so zero is a possible published generation and IDs
are not unconditionally unique after wrap. Live `0x00886EB0`, reached from
battle-phase support initialization live `0x008852E0`, resets the allocator to
candidate `1` with the marker clear. This namespace is independent of side and
of the transient manager's `+0x8C` actor serials. No request, gauge,
terminal-state, or slot gate reads object `+0x120` in the audited paths.

The raw prologue computes `side < 0` and `side < 2`, but never branches on
either result. It proceeds to index both the resident `0x28`-stride selector
record and owner side slots with the supplied value. After constructing and
publishing a new object, a later check deliberately stores through address zero
unless side is exactly `0` or `1`; this is a late assertion/crash, not input
validation, because the out-of-range indexing has already occurred. The
factory and its live `0x00885490` wrapper therefore do **not** safely enforce
the documented two-slot domain. The only resident call to the create wrapper,
in `FUN_00238340`, passes `fighter_u8(+0x60) & 1`, which is proven to be `0` or
`1`; that caller-side mask is the safety boundary observed in the normal
creation path.

### Support-object common prefix and removal

Common constructor live `0x00887A60` derives from generic node live
`0x00709AA0`. Common virtual initializer live `0x00887FD0`, directly reused or
called by the inspected specializations, establishes these stable fields:

| Object offset | Type | Proven role |
| ---: | --- | --- |
| `+0x00` | `u8` flags | generic node flags; new support sets bits 1 and 2 |
| `+0x50` | pointer | class vtable |
| `+0x60` | `u8` | derived support implementation selector passed by the owner |
| `+0x6C` | pointer | borrowed already-loaded support archive returned by resident `FUN_001AA4B0` |
| `+0x80..+0x90` | five pointers | borrowed named animation payloads resolved from `+0x6C`, in order `ent`, `nut`, `run`, `act`, `ext` |
| `+0xE4` | `u8` | side `0/1` passed by the owner |
| `+0xF2` | `u8` | owner-observed lifecycle state; value `2` requests final destruction |
| `+0x120` | `u32` | manager-assigned generation ID |
| `+0x134..+0x144` | five pointers | optional owned subobjects, virtual-destroyed by the common destructor |
| `+0x50C` | `u8` flags | constructor clears bits 0..2 and sets bit 3; bit 0 is set through the lineage notification below |

Common destructor live `0x00887D90` also releases owned handles at
`+0x70/+0x74/+0x78`, destroys its embedded constructed arrays, calls generic
node destructor live `0x00709B60`, and optionally frees the complete object.
Those fields are ownership edges; the side slot itself remains the parent that
chooses when to invoke the destructor and clear the pointer.

The construction/destruction symmetry proves more of the common object's
internal ownership without assigning gameplay names:

| Common-object region | Construction | Symmetric teardown |
| ---: | --- | --- |
| `+0x70` | optional `0x120`-byte allocation during initialization | resident `FUN_001B7570(handle, 1)`, then null |
| `+0x74` | optional `0xA0`-byte allocation during initialization | resident `FUN_001951A0(handle, 1)`, then null |
| `+0x78` | optional `0x50`-byte allocation during initialization | resident `FUN_00199190(handle, 1)`, then null |
| `+0x148` plus `+0x170` | embedded owner plus six `0x50`-stride constructed elements | six-element array teardown, then embedded-owner teardown |
| `+0x368` plus `+0x390` | embedded owner plus three `0x50`-stride constructed elements | three-element array teardown, then embedded-owner teardown |
| `+0x48C` plus `+0x4B0` | embedded owner plus one `0x50`-stride constructed element | one-element teardown, then embedded-owner teardown |
| `+0x500` | embedded resident-managed object | resident-managed release/reinitialization path in the common destructor |

The common initializer destroys and nulls a previous `+0x70/+0x74/+0x78`
handle before publishing its replacement. Those are therefore owning slots,
not merely resource aliases. The five `+0x80..+0x90` words are borrowed
animation payloads, not five independently allocated children. The five
`+0x134..+0x144` slots are
different: each nonnull entry is virtual-destroyed through slot `+0x08` and
then nulled.

The constructor clears the five animation words through its loop store at live
`0x00887B94`. The initializer's five-iteration loop at live
`0x008883D0..0x008884A8` builds
`ANM_p%s%s%d` (live string `0x008BF698`), with suffixes from the five-pointer
table at live `0x008BF5B0..0x008BF5C4` (exclusive end). Those pointers select
the resident strings `ent`, `nut`, `run`, `act`, and `ext` at
`0x00605BF0..0x00605C04`. It passes the existing archive `+0x6C` and the
constructed name to resident `FUN_001A8F00` at live call `0x00888484`, then
stores the returned payload at `+0x80 + index * 4` at `0x00888494`.

Resident `FUN_001AA4B0` searches an already-loaded archive list; it does not
allocate or increment a reference in this path. `FUN_001A8F00` searches that
archive's name index and returns the existing CCS object's `+0x2C` payload,
also without allocation or ownership transfer. Its third argument is zero
here, so a missing name reaches an explicit zero-address assertion rather
than an optional-null path. The support object therefore relies on that archive
remaining loaded while it uses these aliases.

A raw word audit across live `0x00887A60..0x0088E980` found only the
constructor clear and initializer lookup loop as stores with these five field
offsets; consumers such as live `0x00889430` pass a selected payload with owned
handle `+0x70` to resident `FUN_001B99B0`. The common destructor frees the
handle, not these payloads. Computed writes outside this bounded family are not
excluded.

**Removal.** The side slot is the only owner of a fielded support object, and
the slot writers are:

| Writer | Effect on the slot |
| --- | --- |
| constructor live `0x00886CB0` | clears both slots |
| factory live `0x008872E0` (store `0x008876C8`) | publishes a new object into an empty slot |
| pass-1 main dispatch live `0x00886ED0` (clear `0x00887160`) | after object virtual `+0x10`, `+0xF2 == 2` virtual-destroys the object through `+0x08` and clears its slot |
| live `0x00887990(owner, side)` | virtual-destroys and nulls one slot, or both for side `-1`; called by owner destructor `0x00886DE0` and by battle reset `0x00886E70` (which keeps the owner allocated) |

The 25 direct BTL references to global `0x00607888` otherwise only read a
side record or slot or dispatch a virtual event to an existing slot; no
alternate slot array or owner exists in that set. Global publication and
clearing remain live `0x00885210/0x00885290`.

Generic flag bits 1 and 2 are callback-enable gates, not slot membership.
Pass 1 rewrites both bits on each occupied slot before dispatch, and explicit
disable live `0x00887830` clears them without destroying the object or clearing
its slot. Because the `+0xF2 == 2` check runs only for objects whose bit 1 is
enabled, a disabled object keeps its slot until a later enabled pass or owner
teardown; owner teardown ignores both bits. Presence queries test only the
nonnull slot (see the [lookup matrix](#lookup-and-identity-contract-matrix)),
so a support remains discoverable until its owner clears the slot. The pass
scheduling, enable predicates, and disable callsites belong to
[Battle support mechanics](support_mechanics.md#scheduled-lifecycle-and-teardown).

### Non-owning support lineage on transient actors

Some support implementations create objects through the independent transient
manager at live `0x00736080`. Two directly decoded creation sites, live
`0x0088B0AC` and `0x0088DA18`, copy support generation `+0x120` into the new
actor's `+0x288` and set actor byte `+0x284 = 1`. The transient base reset at
live `0x0072B4A0` clears both fields. When live `0x00736080` creates an actor
from a nonnull source actor, it copies `+0x284/+0x288` to the new actor, so the
token follows descendants rather than identifying only one transient object.

A later transient-actor path at live `0x0072EB94` checks marker `+0x284`,
resolves a side through live `0x00734130`, and passes actor `+0x288` to live
`0x00886A40(side, token)`. That function never recovers or dereferences the
originating support; it deduplicates the token and can set bit 0 of
`+0x50C` on whichever support **currently** occupies that side slot.

This is a proven cross-manager lineage relation but not an ownership edge: the
actor stores no support pointer, support replacement cannot leave it with a
dangling parent address, and each object remains destroyed by its own manager.
Notification acceptance, the deduplication ring, and the `+0x50C` flag behavior
belong to
[Battle support mechanics](support_mechanics.md#support-counters-and-notification-suppression).

## BTL skill actors

The skill actors whose creation is traced below are allocated by BTL skill
factory live `0x00773C90`; the authored spawn route live `0x00776280` registers each returned actor by
fighter side. Addresses labeled preserved are the export view, live minus
`0x40` ([address conventions](../game/files/file_identities.md#address-conventions)).

### `ccSkillHNW001` skill actor

[Combo accounting](combo_accounting.md#repeated-event-contribution-in-ccskillhnw001)
owns this actor's pending-hit contribution and gate fields;
[Collision](collision.md#ccskillhnw001-interaction-records-and-accepted-event-route)
owns its borrowed interaction records and accepted-event route.

#### Class and retail action identity

Resident table header `0x005E2020` points to BTL RTTI `0x008CE980`
(preserved `0x008CE940`), whose name pointer `0x008BB538` (preserved `0x008BB4F8`) is the
string `ccSkillHNW001`. The table holds update target `0x0085E340` at
resident `0x005E2118`.

Resident character record `0x00558C70` has ID `80`, name pointer
`0x00558C50` containing `２部ヒナタ`, body filename `2hnwbod1.ccs`, action
count `0x34`, and action-array pointer `0x00557B40`. Action index `3`,
record `0x00557C3C`, contains name pointer `0x0043BFA0` and packed
owner/selector word `0x00A10050` (owner ID `80`, selector `161`). The
Shift-JIS name bytes decode as
`<r守護八卦六十四掌|しゅごはっけろくじゅうよんしょう>`, so the retail display
name is **守護八卦六十四掌**. Record contracts belong to
[Character assets](../game/character_assets.md#action-records).

Selector table `0x008CB160` has value `165` at selector `161`
(preserved `0x008CB3A4`). Resource-name table `0x008A7AA0` has pointer `0x008A78A0`
at index `165` (preserved `0x008A7CF4`); the pointed bytes at preserved `0x008A7860` contain
`2hnwcha1.ccs`. Common binding preserved `0x0078E6C0` / live `0x0078E700` uses that
resource index for the required container lookup, stores the container at
actor `+0x1F0`, and stores the index at `+0x56C`. Factory index `165`,
selector `161` and character ID `80` are distinct numeric domains joined by
these tables. The wider map belongs to
[Selector-to-resource mapping](../game/character_assets.md#selector-to-resource-mapping).

#### Factory admission and authored creation

Factory preserved `0x00773C50` / live `0x00773C90` admits an unsigned index below `0xC5`
and dispatches through table `0x008CD1F0` (preserved `0x008CD1B0`). Entry `0xA5`
contains `0x00775A08`, the allocator arm beginning at preserved `0x007759C8`. Bytes
preserved `0x007759C8..0x00775A87` request `0x1180` bytes, call base construction
`0x00785410`, install resident table `0x005E2020` at object `+0x110`,
construct two pairs of `0x50`-byte records at `+0x1020` and `+0x10C0`,
initialize the `+0x1160` reference, and call the returning initializer
`0x0085CE50` (preserved `0x0085CE10`). The allocator's null branch skips this
initialization.

Retail `PL/2HNWCHA1.CCS` is gzip-compressed. Its animation record `70`,
`ANM_phnwcha10`, has a tag-`0x0108` command at decompressed offset `0x4E60`,
after integer marker `1`. The three payload words are record ID `69`
(`OBJ_eff_dummy_hnwcha1`), `0x8003`, and `0x1A5`. The entire nested block
spans `0x2F34..0x4F03` and contains exactly one such event. The five
separately bound records `ANM_phnwcha11a`, `ANM_phnwcha11b`,
`ANM_phnwcha11c`, `ANM_phnwcha12` and `ANM_phnwcha1eff` contain no
tag-`0x0108` events in their complete nested blocks; that absence does not
exclude collision-generated callbacks. Resident parsers `0x001B1470`,
`0x001A29D0`, `0x001A6E00` and `0x001A8C10` corroborate the animation and
event payload structure.
[Animation event delivery](../runtime/animation_runtime.md#packed-command-crossing-and-event-delivery)
owns queue lifetime and marker crossing.

Fighter setup `0x00215950` installs callback `0x002145B0` at player `+0xE8`;
that returning wrapper calls resident `0x00308DC0`. Its final continuation
builds `{fighter,0}` and calls `0x00773C20` (preserved `0x00773BE0`). This bridge
requires event word `+0x04` equal to `0x8003` and unsigned word `+0x08` in
`0x100..0x1C4`. It subtracts `0x100` and calls `0x00776280` with that index,
the fighter, and fighter `+0x20`. Hence authored `0x1A5` selects factory
index `0xA5`. The wrapper at preserved `0x00776240` calls the factory, registers the
returned actor using fighter side `+0x60&1`, and, when nonnull, performs the
common binding with the original index. A marker is an authored stream
position, not evidence of a measured delay after input.

#### Local state machine

State setter preserved `0x0085DDA0` / live `0x0085DDE0` stores the requested state at
`+0x08` and resets local call counter `+0x04`. Its six-entry jump table is
`0x008CDD40` (preserved `0x008CDD00`). The update's separate six-entry table is at
preserved `0x008CDD20..0x008CDD37`; its state-`2` entry contains `0x0085E440`
(preserved `0x0085E400`). These tables and raw continuations
preserved `0x0085DDE8..0x0085E2FF` establish the branches below.

| State | Setter entry | Update branch |
| --- | --- | --- |
| `0` | Selected by activation after its display reset. | Enables byte `+0x150` and the input object's byte `+0x00` when counter `+0x04` equals `5` (preserved `0x0085E340..0x0085E384`). |
| `1`, `2` | Share the animation/child preparation branch. The event receiver requests state `2` only while the old state is below `2` (preserved `0x0085DC78..0x0085DC94`). | State `1` consumes positive `+0x14A` by clearing it and `+0x1172`. State `2` is the counting branch owned by Combo accounting; it also uses old `+0x1170` thresholds `16` and `40` when choosing record halfwords `+0x30/+0x32` or requesting state `3`. |
| `3` | Disables both embedded interaction records and calls local mask helper `0x0085EAE0` with `1`. | Waits until counter `+0x04 >= 10`, then requests state `4` (preserved `0x0085E58C..0x0085E5AC`). |
| `4` | Calls the same helper with `0`, disables the records, then stores `+0x1177=1` (preserved `0x0085E048`). | Requests state `5` when `+0x1176==1`. |
| `5` | Selects the finishing animation, retires admitted child references, disables the input-event object and byte `+0x150` (preserved `0x0085E264..0x0085E280`), and disables both interaction records. It does not clear `+0x1175..+0x1177`. | — |

An accepted event is therefore a concrete producer of the counting state's
entry. Exact-offset searches for `+0x1177` and `+0x1176` each find five
sites: initialization, activation reset, the receiver, the respective state
setter/update use, and the contribution helper. Indexed and differently
formed aliases remain outside that bound. The mask helper's bank requests
belong to [Combo accounting](combo_accounting.md#request-mask-producers-and-retained-values).

#### Resource retention and cleanup

Activation preserved `0x0085D0D8..0x0085D0F7` retains five animation lookup results
at actor `+0xFF0+4*i`, using name pointers at preserved `0x008BA530`. They are
resource pointers, separate from the two constructed child actors and the
generation-checked child references.

Local cleanup preserved `0x0085CEB0` / live `0x0085CEF0` destroys animation player
`+0x1004` through resident `0x001B7570(pointer,1)` and clears the field
(returning continuation preserved `0x0085CED0..0x0085CEDF`). For each of two child
triples at `+0x1008+0x0C*i`, it requires index `0..31` and matching serial
and pointer in one of the owner's two registry banks before invoking child
table `+0x50`, slot `+0x80`. This requests retirement of a valid registered
child rather than freeing a raw retained pointer. The independent `+0x1160`
reference uses resident resolver `0x0030C2E0` before its object's virtual
`+0x18` cleanup. Local destructor preserved `0x008716F0` / live `0x00871730` calls this
cleanup, destroys the two embedded record pairs, invokes base cleanup and
frees the allocation only for a positive destruction flag. These local
retirement edges do not establish the complete subordinate or base
destruction lifetime.

### BTL skill classes on damage paths

These internal skill classes contain BTL direct-damage calls classified in
[Damage](damage.md#all-fifteen-btl-source-retaining-calls), which keeps their
damage arithmetic. Their RTTI names are internal type identities, not
player-facing move names. The `ccSkill` and `ccSkillComboBase` bases and the
`ccSkillCtrl` service belong to
[BTL skill-service callbacks](battle_auxiliary_services.md#btl-skill-service-callbacks-and-ownership);
admission by factory `0x00773C90` and the authored spawn route through
`0x00776280` are described in
[factory admission and authored creation](#factory-admission-and-authored-creation).

#### Shared-float caller classes

The shared-float damage helpers, complete entries preserved `0x0079FD80` and
`0x007D4430`, are reached through two pairs of primary class tables, rather
than identifying one class each:

| Damage helper, preserved call | Calling method / preserved call to helper | Resident table and slot | Exact RTTI name |
| --- | --- | --- | --- |
| `0x0079FD80`, `0x0079FEC8` | `FUN_0079F5B0`, `0x0079FA9C` | `0x005F0C20 + 0x1A0`; `0x005FACC0 + 0x1A0` contain live `0x0079F5F0` | `ccSkillNRW001`; `ccSkillNRT001B` |
| `0x007D4430`, `0x007D4578` | `FUN_007D0A10`, `0x007D10A8` | `0x005F3FF0 + 0xF8`; `0x005E51B0 + 0xF8` contain live `0x007D0A50` | `ccSkillNRV001`; `ccSkillJRW001` |

The exact name joins use live RTTI/name pairs
`0x008CF8D8/0x008BBF78`, `0x008CF8B0/0x008BBF88`,
`0x008CED20/0x008BB7B8`, and `0x008CED48/0x008BB7A8`, respectively.
Constructor bytes at preserved `0x007DDE40..0x007DDE6F` establish that
`ccSkillNRW001` calls the common constructor and then installs its table
and sets byte `+0x1170` to `1`. That common constructor, live
`0x0079DA50`, installs the `ccSkillNRT001B` table at preserved
`0x0079DA28..0x0079DA30`. Preserved
`0x007CF850..0x007CF873` installs the `ccSkillNRV001` table after base
construction; `0x0084D650..0x0084D67F` joins the derived `ccSkillJRW001`
constructor to that common class and its own table. These are internal type
and inheritance joins.

#### `ccSkillTYO000B`

Direct-damage method live `0x007A4F00` is stored in resident table
`0x005F9F20 + 0x1A0`. That table's RTTI/name pair is live
`0x008D0168/0x008BC4C8`, with exact name `ccSkillTYO000B`. Constructor live
`0x007A4CA0`, preserved `0x007A4C60..0x007A4C98`, calls base live
`0x00797250` and installs this table at object `+0x110`. Factory index `31`
points to live allocator `0x007745D8`; preserved `0x00774598..0x007745BB`
requests `0x1110` bytes and calls that constructor on a non-null allocation.
The common selector tables join index `31` to live descriptor `0x008A90A0`
and CCS name `2tyocha0.ccs`.

#### `ccSkillFOR000` allocation and lifetime

Constructor bytes at preserved `0x00804630..0x00804658` install resident
vtable `0x005EB890` at object `+0x110`; vtable slot `+0x100` at `0x005EB990`
contains live update `0x00804E40`. The table's RTTI pointer is live
`0x008CF440`, whose name pointer is live `0x008BBCE8`; bytes at preserved
`0x008CF400` and `0x008BBCA8` join the exact class name.

Preserved allocator bytes `0x00773F9C..0x00773FBB` request `0x1510` bytes
from resident `0x00117150`, test for null, and call the constructor at live
`0x00804670`. A direct-call byte search finds this one constructor call in
BTL. Factory live `0x00773C90` selects this arm only for index `22`: its
197-entry live jump table is `0x008CD1F0`, and entry `22` contains live
allocator destination `0x00773FDC`.

The inspected spawn route, live `0x00776280` (preserved
`0x00776240..0x007762DF`), calls the indexed factory first, registers its
returned object in the primary side slot, and passes it to common initializer
live `0x0078E700`. The initializer writes selector `+0x56C` at preserved
`0x0078E744` and invokes class setup slot `+0x22C` at `0x0078E8A8` or
`0x0078E924`; FOR's slot contains live `0x00804A80`. This route creates a
fresh FOR allocation and then takes its damage snapshot. It supplies no
existing FOR allocation for reconstruction or repeated setup. Other
entrypoints and an arbitrary later setup call are not excluded by this
bounded route.

The destructor is live `0x008047A0`, preserved `0x00804760..0x00804A3F`. It
restores the class table, releases the target link, invokes the linked
fighter's `FUN_0021F980` under its validity gate, cleans the skill's
interaction/effect children, reinstalls base `ccSkill` table `0x005FB4D0`,
and removes the primary registry entry through live
`0x0086F7D0(owner + 0x210, side)`. Its final signed deletion argument
controls whether resident `0x00117000` frees the skill allocation. This body
does not clear fighter `+0x7CC`, reset the shared retained record, or rewrite
the shared raw float, so the skill allocation and the retained record's
storage have distinct lifetimes. The complete byte interval establishes the
cleanup and conditional free. The class's embedded animation players belong to
[the FOR embedded-player pair](../runtime/scene_playback_owners_btl.md#btl-for-embedded-player-pair).

#### `ccSkillANB000` creation and destruction

Resident vtable `0x005EB610` has live method `0x00808200` in slot `+0x1A0`,
RTTI live `0x008CF410`, and name pointer live `0x008BBCC8`; preserved bytes
`0x008CF3D0` and `0x008BBC88` establish the name. Preserved
`0x00807DD4..0x00807DDC` also installs this table at object `+0x110`.

Factory live `0x00773C90` routes indices `3`, `11`, `53`, `89`, and `143`
to five distinct allocator arms, each requesting `0x13C0` bytes and calling
constructor live `0x00807AC0`. The arms are preserved
`0x00773D38`, `0x00773E5C`, `0x00774E20`, `0x00774E98`, and
`0x007750EC`; their corresponding entries in live table `0x008CD1F0`
are the five index joins. Constructor prologue bytes
`0x00807A80..0x00807AA7` call base construction and install resident
table `0x005EB610`. Its continuation initializes the local resource array,
state fields, and effect/interaction children. The shared retained record
is not an embedded member of any of these `0x13C0` allocations.

ANB's setup slot `+0x22C` contains live `0x008085E0`; preserved
`0x008085A0..0x0080870B` selects a separate local resource-name bank for
each of the five selectors and fills its 17-pointer array. Thus one internal
type has five authored variants; their damage multipliers are in
[Damage](damage.md#guard-or-response-skill-contribution), and the embedded
and associated players in
[the ANB player owners](../runtime/scene_playback_owners_btl.md#btl-anb-embedded-and-associated-players).

The destructor is live `0x00807DF0`, preserved `0x00807DB0..0x008081B7`. It
releases both side/target links, restores object activity bits, removes its
two interaction lists and effect children, then reinstalls the base table and
removes the primary registry entry. Selector `143` has additional local
timeline and linked-fighter restoration branches. The final signed deletion
argument controls freeing the skill allocation. This body neither resets the
shared record or raw float nor clears fighter `+0x7CC`. It does not prove that
every later fighter alias is expired when the skill dies. The inspected common
spawn route constructs a fresh object for each of the five factory arms; a
whole-game reuse claim would require other entrypoints and object producers
to be traced.

## Lookup and identity contract matrix

These lookup APIs use distinct namespaces and do not share a universal
“active” test:

| API | Input namespace and selection | Match order / filtering | Invalid or absent result |
| --- | --- | --- | --- |
| resident `FUN_003769C0` | primary-fighter alias by side | direct manager `+0xDE4/+0xDE8`; no node-flag test | null unless side is exactly `0` or `1` |
| live `0x00709800` | `ccCommand` node by full `u32 +0x60` side | last matching hub-list node; no generic-flag test | null when no match |
| live `0x007099C0` | primary fighter by `(u8(+0x60) & 1)` side | last matching hub-list node; no generic-flag test | null when no match |
| live `0x006D5900` | `ccCameraCtrl` node by `u32 +0xA8` key | last key match; ignores current marker | null when no match |
| live `0x006D5960` | `ccCameraCtrl` key plus requested `u8 +0x60` current bit | last key/bit match | null when no match |
| live `0x00709740` | `ccCameraCtrl` current node by key | wrapper over `0x006D5960(..., 1)` | null when no current match |
| live `0x00735F90` | transient actor by `u32 +0x8C` serial | first match reachable from manager head; no separate flag test | null if manager absent or no match |
| live `0x00735990` | next transient actor by `s16 +0x78` type, side-selector mapping, and cursor | first qualifying node after cursor, or from head for null cursor | null when exhausted |
| live `0x00735910` / `0x00735A30` | same transient type/side predicate | boolean existence / total matching count | zero when none |
| live `0x008854D0` | support occupancy by side slot | boolean nonnull slot; ignores flags and lifecycle state | zero if owner absent; side index itself is unchecked |
| live `0x00886750` | support object by side slot | returns the exact slot pointer; ignores flags and lifecycle state | null if owner absent; side index itself is unchecked |

There is no decoded public lookup from support generation `+0x120` back to a
support object. The generation allocator compares its candidate with the two
current values and returns zero on a post-wrap collision; transient descendants
merely copy the value as a lineage token. Code that needs the support object resolves its
current side slot instead. Pointer aliases, transient serials, support
generations, and cumulative support counters must therefore not be substituted
for one another.

## Exact function map

### Resident ELF

| Address / symbol | Direct role and important edges |
| --- | --- |
| `0x001E9980` `FUN_001E9980` | allocate/publish the `0xDF8` manager; calls `FUN_001F4200`, then `FUN_001F45B0` |
| `0x001F4200` `FUN_001F4200` | manager constructor; calls `FUN_001F4360` |
| `0x001F4360` `FUN_001F4360` | initialize manager, including both three-entry alias arrays |
| `0x001F4680` `FUN_001F4680` | manager teardown; clears both alias arrays |
| `0x001EC3B0` `FUN_001EC3B0` | allocate/publish `0x38` battle state; calls `FUN_001EEC80` and `FUN_001EF330` |
| `0x001EC7A0` `FUN_001EC7A0` | outer battle-driver setup; calls live `0x00885210` to replace and publish the dynamic-support owner |
| `0x001EC890` `FUN_001EC890` | outer battle-driver cleanup; calls live `0x00885290` to destroy and clear the dynamic-support owner |
| `0x001EDB00` `FUN_001EDB00` | state transition that constructs battle state, then calls support post-create initializer live `0x008852E0` |
| `0x001EDD10` `FUN_001EDD10` | teardown transition; calls live `0x008853D0` to destroy both slotted supports before later battle-state destruction |
| `0x001EF330` `FUN_001EF330` | construct hub/graph, resolve four side aliases, publish `ccCamera01` root, then create transient-actor manager |
| `0x001EEFD0` `FUN_001EEFD0` | destroy transient-actor manager, invalidate aliases, destroy hub, clear hub pointers |
| `0x001EECD0` `FUN_001EECD0` | outer battle-state destructor; calls `FUN_001EEFD0` |
| `0x001F03E0` `FUN_001F03E0` | master battle phase dispatcher; schedules the three support-owner passes and both transient-actor passes from independent mask bits |
| `0x002145D0` `FUN_002145D0` | common primary-fighter base constructor; calls live BTL `0x00709AA0` |
| `0x00214840` `FUN_00214840` | common fighter destructor/optional final free |
| `0x002151E0` `FUN_002151E0` | common fighter initializer; establishes `+0x68` identity and `+0x60` side bit |
| `0x00215720` `FUN_00215720` | common concrete-fighter cleanup; releases optional owners at `+0x950/+0xB30` and the per-side combo object |
| `0x00215E70` `FUN_00215E70` | release/null the four owning fighter handle slots at `+0xE68..+0xE74` |
| `0x00304F40` `FUN_00304F40` | construct the fighter's embedded two-list owner at `+0x8C4` |
| `0x00304F90` `FUN_00304F90` | clear that owner's two generic lists; optional free applies only to a separately allocated owner |
| `0x0024DA50` `FUN_0024DA50` | fighter virtual update; bit-1 gated and returns zero to list maintenance |
| `0x0024FD80` `FUN_0024FD80` | derived fighter-list processing and removal candidates |
| `0x0024E0B0` `FUN_0024E0B0` | derived fighter-registry/coordinator constructor |
| `0x0024E250` `FUN_0024E250` | fighter-registry destructor; clears nodes and owned auxiliaries |
| `0x0024E380` `FUN_0024E380` | install coordinator state and clear its three state-local words |
| `0x002504B0` `FUN_002504B0` | coordinator-state dispatch plus fighter-list update/removal pass |
| `0x00250690` `FUN_00250690` | fighter-list vtable-`+0x14`/derived processing pass |
| `0x00250800` `FUN_00250800` | fighter-list vtable-`+0x18` pass |
| `0x00250820` `FUN_00250820` | return coordinator `+0x14`, or `-1` when unavailable |
| `0x00238340` `FUN_00238340` | manual support-request handler; applies resident gates, calls create/request wrapper live `0x00885490`, and accepts result `1` or `2`; not itself an instance factory |
| `0x001F2AC0` `FUN_001F2AC0` | setup path that pairs a selected side-1 primary ID with support sentinel `0x26` |
| `0x001FE540` `FUN_001FE540` | copy/swap paired primary and support configuration IDs from a setup record |
| `0x003769C0` `FUN_003769C0` | strict side `0/1` accessor for manager primary-fighter aliases |
| `0x005A2900` | eight-byte character factory/record table base |

### BTL live/raw/export audit

Each row gives the true live entry, the complete-file raw offset, and the
preserved export address where the entry bytes are displayed.

| Live | Raw | Export bytes | Role |
| ---: | ---: | ---: | --- |
| `0x006D5640` | `0x021740` | `0x006D5600` | `ccCameraCtrl` container constructor |
| `0x006D57A0` | `0x0218A0` | `0x006D5760` | `ccCameraCtrl` insert/current replacement |
| `0x006D5900` | `0x021A00` | `0x006D58C0` | `ccCameraCtrl` lookup by `+0xA8` key |
| `0x006D5960` | `0x021A60` | `0x006D5920` | `ccCameraCtrl` key/current lookup |
| `0x006D6800` | `0x022900` | `0x006D67C0` | `ccCameraCtrl` node initializer |
| `0x006DDE10` | `0x029F10` | `0x006DDDD0` | allocate/initialize one `0x1D0` `ccCameraCtrl` node |
| `0x006EF4E0` | `0x03B5E0` | `0x006EF4A0` | `ccCommand` node constructor |
| `0x006EF600` | `0x03B700` | `0x006EF5C0` | bind `ccCommand` node to side/input state |
| `0x006F0F90` | `0x03D090` | `0x006F0F50` | `ccCommandCtrl` registry constructor |
| `0x00707350` | `0x053450` | `0x00707310` | construct an optional transient-actor child |
| `0x00707920` | `0x053A20` | `0x007078E0` | child state/drain test; reports recyclable at state `>= 2` |
| `0x007083D0` | `0x0544D0` | `0x00708390` | construct transient manager's deferred-child-list owner |
| `0x00708480` | `0x054580` | `0x00708440` | destroy all deferred children / optional owner free |
| `0x00708570` | `0x054670` | `0x00708530` | prepend a child to the deferred-child list |
| `0x00708630` | `0x054730` | `0x007085F0` | maintain and recycle deferred children |
| `0x00708720` | `0x054820` | `0x007086E0` | run the deferred children's second pass |
| `0x007087A0` | `0x0548A0` | `0x00708760` | `ccField` node constructor |
| `0x007088A0` | `0x0549A0` | `0x00708860` | `ccField` node destructor |
| `0x00709150` | `0x055250` | `0x00709110` | `ccFieldCtrl` registry constructor |
| `0x007091A0` | `0x0552A0` | `0x00709160` | `ccFieldCtrl` registry destructor |
| `0x00709240` | `0x055340` | `0x00709200` | hub constructor |
| `0x00709280` | `0x055380` | `0x00709240` | hub destructor/free wrapper |
| `0x007092E0` | `0x0553E0` | `0x007092A0` | allocate four registries |
| `0x007093A0` | `0x0554A0` | `0x00709360` | virtual-destroy and null four registries |
| `0x00709480` | `0x055580` | `0x00709440` | create and cross-link initial graph |
| `0x007095E0` | `0x0556E0` | `0x007095A0` | registry-wide vtable-`+0x0C` pass |
| `0x00709660` | `0x055760` | `0x00709620` | create initial `ccCameraCtrl` node |
| `0x007096E0` | `0x0557E0` | `0x007096A0` | `ccCameraCtrl` root selector by node `+0x10 == 0` |
| `0x00709740` | `0x055840` | `0x00709700` | current `ccCameraCtrl` node lookup by key |
| `0x00709780` | `0x055880` | `0x00709740` | create/append one `ccCommand` node |
| `0x00709800` | `0x055900` | `0x007097C0` | find last `ccCommand` node by `u32 +0x60` side |
| `0x00709860` | `0x055960` | `0x00709820` | create/append one primary fighter |
| `0x007099C0` | `0x055AC0` | `0x00709980` | find last fighter by `u8 +0x60` low side bit |
| `0x00709A20` | `0x055B20` | `0x007099E0` | create/append `ccField` node |
| `0x00709AA0` | `0x055BA0` | `0x00709A60` | generic node constructor |
| `0x00709B60` | `0x055C60` | `0x00709B20` | generic node destructor |
| `0x00709BC0` | `0x055CC0` | `0x00709B80` | generic container constructor |
| `0x00709BF0` | `0x055CF0` | `0x00709BB0` | node vtable-`+0x0C` pass |
| `0x00709C70` | `0x055D70` | `0x00709C30` | update/remove pass |
| `0x00709E60` | `0x055F60` | `0x00709E20` | append node |
| `0x00709EA0` | `0x055FA0` | `0x00709E60` | unlink and virtual-destroy node |
| `0x00709F40` | `0x056040` | `0x00709F00` | destroy every node in a container |
| `0x00729890` | `0x075990` | `0x00729850` | descriptor-driven transient-actor class factory |
| `0x0072B190` | `0x077290` | `0x0072B150` | secondary-actor-family base constructor |
| `0x0072B1F0` | `0x0772F0` | `0x0072B1B0` | secondary-actor initializer; writes owner side |
| `0x0072B4A0` | `0x0775A0` | `0x0072B460` | secondary-actor reset; writes owner side `-1` |
| `0x0072B800` | `0x077900` | `0x0072B7C0` | secondary-actor base destructor/free wrapper |
| `0x0072B880` | `0x077980` | `0x0072B840` | release base-owned handles and reset actor |
| `0x0072B9B0` | `0x077AB0` | `0x0072B970` | mark optional child for deferred destruction and clear `+0x70` |
| `0x00734130` | `0x080230` | `0x007340F0` | opposite-side resolver |
| `0x00734160` | `0x080260` | `0x00734120` | opponent-primary-fighter resolver |
| `0x007341A0` | `0x0802A0` | `0x00734160` | own-primary-fighter resolver |
| `0x007343A0` | `0x0804A0` | `0x00734360` | construct the `0xD0` transient-actor manager |
| `0x00734470` | `0x080570` | `0x00734430` | reset manager list, counters, pointers, and pass gates |
| `0x007349C0` | `0x080AC0` | `0x00734980` | destroy all actors and manager-owned auxiliaries |
| `0x00734AD0` | `0x080BD0` | `0x00734A90` | unlink one actor and release its child handle |
| `0x00734BA0` | `0x080CA0` | `0x00734B60` | actor update/removal pass |
| `0x00734D30` | `0x080E30` | `0x00734CF0` | independently gated actor/child second pass |
| `0x00735910` | `0x081A10` | `0x007358D0` | boolean actor existence by type and inverted side selector |
| `0x00735990` | `0x081A90` | `0x00735950` | next actor by type and inverted side selector |
| `0x00735A30` | `0x081B30` | `0x007359F0` | count actors by type and inverted side selector |
| `0x00735DF0` | `0x081EF0` | `0x00735DB0` | set manager first-pass gate `+0x20` |
| `0x00735E10` | `0x081F10` | `0x00735DD0` | clear manager first-pass gate `+0x20` |
| `0x00735E30` | `0x081F30` | `0x00735DF0` | set manager second-pass gate `+0x21` |
| `0x00735E50` | `0x081F50` | `0x00735E10` | clear manager second-pass gate `+0x21` |
| `0x00735E70` | `0x081F70` | `0x00735E30` | allocate/publish transient-actor manager at `0x00607820` |
| `0x00735F30` | `0x082030` | `0x00735EF0` | destroy/free manager and clear `0x00607820` |
| `0x00735F90` | `0x082090` | `0x00735F50` | global actor lookup by `+0x8C` serial |
| `0x00736080` | `0x082180` | `0x00736040` | create, initialize, and link a transient actor |
| `0x00882630` | `0x1CE730` | `0x008825F0` | get one side record's Linked Mode byte `+0x01` |
| `0x00882670` | `0x1CE770` | `0x00882630` | set one side record's Linked Mode byte `+0x01` |
| `0x00885210` | `0x1D1310` | `0x008851D0` | replace and publish the `0x24` dynamic-support owner |
| `0x00885290` | `0x1D1390` | `0x00885250` | destroy the dynamic-support owner and clear global `0x00607888` |
| `0x008852E0` | `0x1D13E0` | `0x008852A0` | post-battle-state support initialization and support-side runtime-array reset |
| `0x008853D0` | `0x1D14D0` | `0x00885390` | destroy both slotted support objects while preserving the owner |
| `0x00885400` | `0x1D1500` | `0x008853C0` | global wrapper for the support main/removal pass |
| `0x00885430` | `0x1D1530` | `0x008853F0` | global wrapper for the support vtable-`+0x14` pass |
| `0x00885460` | `0x1D1560` | `0x00885420` | global wrapper for the support vtable-`+0x18` pass |
| `0x00885490` | `0x1D1590` | `0x00885450` | global side request wrapper; calls class factory/publisher `0x008872E0` |
| `0x008854D0` | `0x1D15D0` | `0x00885490` | global boolean support-slot presence query |
| `0x00885C30` | `0x1D1D30` | `0x00885BF0` | resolve support configuration sentinel from a primary ID |
| `0x00886250` | `0x1D2350` | `0x00886210` | normalize per-side support configuration and derive related setup bytes |
| `0x00886750` | `0x1D2850` | `0x00886710` | global support-object pointer lookup by side slot |
| `0x00886950` | `0x1D2A50` | `0x00886910` | allocate a support-object generation ID; a post-wrap collision with a slotted ID returns zero, then advances the candidate once |
| `0x00886A40` | `0x1D2B40` | `0x00886A00` | consume/deduplicate a transient actor's support-lineage token for one side |
| `0x00886BB0` | `0x1D2CB0` | `0x00886B70` | reset the two three-halfword support counter records |
| `0x00886C20` | `0x1D2D20` | `0x00886BE0` | return one side's cumulative successful-support-creation counter |
| `0x00886C60` | `0x1D2D60` | `0x00886C20` | add a signed delta to one side's third support counter |
| `0x00886CB0` | `0x1D2DB0` | `0x00886C70` | construct the `0x24` dynamic-support owner and embedded generation allocator |
| `0x00886DE0` | `0x1D2EE0` | `0x00886DA0` | destroy both support slots and optionally free the owner |
| `0x00886E70` | `0x1D2F70` | `0x00886E30` | destroy both support slots without freeing the owner |
| `0x00886EB0` | `0x1D2FB0` | `0x00886E70` | reset the embedded generation allocator to candidate `1` with the reuse marker clear |
| `0x00886ED0` | `0x1D2FD0` | `0x00886E90` | support main/removal pass; clears the owner `+0x20` one-shot latch |
| `0x008871A0` | `0x1D32A0` | `0x00887160` | support vtable-`+0x14` pass for slot objects with generic flag bit 2 set |
| `0x00887250` | `0x1D3350` | `0x00887210` | support vtable-`+0x18` pass for slot objects with generic flag bit 1 set |
| `0x008872E0` | `0x1D33E0` | `0x008872A0` | selector-driven support class factory, side-slot publisher, initializer, and generation assignment |
| `0x00887810` | `0x1D3910` | `0x008877D0` | support-slot presence query on an explicit owner and side |
| `0x00887830` | `0x1D3930` | `0x008877F0` | call support virtual `+0x28`, then clear callback-enable bits 1 and 2 without clearing slots |
| `0x00887990` | `0x1D3A90` | `0x00887950` | destroy and null one support slot or both slots for side `-1` |
| `0x00887A60` | `0x1D3B60` | `0x00887A20` | common support-object constructor derived from generic node `0x00709AA0` |
| `0x00887D90` | `0x1D3E90` | `0x00887D50` | common support-object destructor and owned-handle cleanup |
| `0x00887FD0` | `0x1D40D0` | `0x00887F90` | common support-object initializer; writes selector `+0x60` and side `+0xE4` |
| `0x0088C890` | `0x1D8990` | `0x0088C850` | `0x520`-byte support specialization constructor used by selector `0x1E` |
| `0x0088CC60` | `0x1D8D60` | `0x0088CC20` | shared `0x520`-byte support constructor used by selectors `0x15..0x17` and `0x38` |
| `0x0088D2D0` | `0x1D93D0` | `0x0088D290` | `0x540`-byte support specialization constructor used by selector `0x21` |
| `0x0088DAB0` | `0x1D9BB0` | `0x0088DA70` | `0x520`-byte support specialization constructor used by selector `0x0A` |
| `0x0088E000` | `0x1DA100` | `0x0088DFC0` | `0x530`-byte support specialization constructor used by selector `0x19` |
| `0x0088E460` | `0x1DA560` | `0x0088E420` | `0x520`-byte support specialization constructor used by selector `0x2B` |
| `0x0088E5F0` | `0x1DA6F0` | `0x0088E5B0` | `0x530`-byte support specialization constructor used by selector `0x3F` |

## Negative results

These structural readings are excluded by the evidence above:

- manager `+0xDE0/+0xDEC` are reserved zero entries, not entity slot zero;
- manager `+0xDF0/+0xDF4` are per-side `ccCommand` nodes, not support pointers;
- manager `+0xDE4/+0xDE8` are aliases, not owners or a general entity registry;
- `ccPlayerCtrl` `+0x14` is coordinator state, not a support-instance pointer
  or node count;
- support selection fields do not cause support instances to be pre-created by
  live `0x00709480`;
- support sentinel `0x26` is resolved in the configuration field itself and is
  not a live-object handle;
- fielded support objects are not owned by the hub, either manager alias array,
  or the transient-actor list; global `0x00607888` owns exactly the two side
  slots;
- transient actors carrying support generation at `+0x288` do not own or
  retain the originating support; the value is a copied lineage token consumed
  through a deduplication ring;
- the support factory's apparent side-range comparisons do not control a
  branch; its observed resident creator is safe because it passes a masked
  fighter-side bit, not because the BTL factory validates its index;
- generic flag byte bit 1 is not the generic active/removal predicate, and
  support flag bits 1 and 2 are not support-slot membership;
- transient actor `+0x60` is not an authoritative active/linked flag after
  unlink; byte `+0x86` is;
- node `+0x20..+0x28` graph pointers do not establish ownership; and
- a last-key `ccCameraCtrl` lookup does not identify the current camera, because
  retail cameras share output key `0x00609160`.
