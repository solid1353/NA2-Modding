# Battle-entity ownership and lifecycle

This document maps the clean NA2 v2.28 resident/`BTL.BIN` ownership path for
the two primary fighters and the battle objects created with them. It covers
allocation, registries, lookup, side mapping, removal, and destruction. It does
not assign gameplay meanings to fields merely because they sit in a fighter or
battle object, and it does not cover Adventure.

`side 0` means Player 1 and `side 1` means Player 2/COM below. A selected
support ID is configuration; it is not itself a pointer to a live object.

## Research coverage

- **Assigned scope:** the clean NA2 `BTL.BIN` fighter/battle-entity ownership
model: manager and registry roots, Player 1/Player 2/support/entity slot
mapping, create/initialize/remove/destroy paths, active or linked flags, lookup
contracts, parent/child ownership, stable proven fields, and resident-file to
runtime-overlay address mapping. The only canonical output owned by this lane
was this document.
- **Exploration depth:** coverage was deep but not globally exhaustive. The investigation followed the
complete resident setup/teardown chain through `FUN_001E9980`,
`FUN_001EC3B0`, `FUN_001EF330`, `FUN_001EEFD0`, and the surrounding support
lifecycle calls at `FUN_001EC7A0`, `FUN_001EDB00`, `FUN_001EDD10`, and
`FUN_001EC890`. Bounded BTL audits covered the four-registry hub and generic
intrusive-list family at live `0x00709240..0x00709F40`; registry-A creation,
transition, and lookup helpers at live `0x006D5640..0x006D59D0`; the primary
fighter/control creation and lookup paths; transient-manager construction,
list ownership, lookup, insertion, removal, and deferred-child paths centered
on live `0x00729890`, `0x0072B190..0x0072B9B0`, and
`0x007343A0..0x00736080`; and the dynamic-support owner/factory/common-base
family at live `0x00885210..0x00887FD0`. The support selector dispatcher was
decoded across every case below its `0x44` cutoff, while specialization audits
were bounded to their construction/destruction shape and two proven
support-to-transient lineage sites rather than every class-specific behavior.
The resident character table at `0x005A2900..0x005A2BF0` was mechanically
counted as 94 eight-byte entries, but the 74 distinct nonnull concrete factory
entrypoints were not all individually audited.

  Several searches were exhaustive within a defined static artifact: all 25
decoded BTL direct references to global support owner `0x00607888`; direct
BTL call sites to the common transient creator and side-resolution helpers;
direct decoded calls to the primary-fighter creator and resident publication
lookups; and every address row in the exact BTL map against
`live = 0x006B3F00 + raw` and `export = live - 0x40`. These scans establish
direct-reference coverage only; computed calls, data-driven dispatch, and code
not recovered as instructions are not implied absent.

- **Confirmed coverage:** the three independent lifetime
roots, exact side-slot formulas, hub/container/node layouts, startup graph and
borrowed cross-links, primary/control lookup behavior, coordinator-owned versus
borrowed fields, registry-A current-node mechanics, transient actor serial and
linked-state contracts, deferred manager-owned children, support fixed-slot
publication and removal, generation/counter namespaces, selector-driven class
allocation, common support ownership, callback-enable flags, and non-owning
support-lineage tokens.
- **Unresolved or untested:** original semantic
names for registry A and the shared node, the meaning of registry-A key
`+0xA8`, support selectors and per-side scalar records, ownership of common
support words `+0x80..+0x90`, the middle support counter's nonzero writer, the
full concrete primary-fighter factory/destructor universe, indirect creation
or registry-mutation routes not exposed by direct-call scans, and whether
last-match lookup behavior is an intentional duplicate policy.
- **Deliberate exclusions and overlap:** Adventure was deliberately excluded, as were damage formulas, substitution,
60-FPS/timing/animation work, widescreen/camera, media, localization, AI
decision logic, and status-effect semantics. Fields touching those areas were
followed only far enough to prove an ownership, identity, publication, or
  lifetime edge.
- **Evidence limitations:** validation was static and read-only against the identified clean
ELF/BTL assets and maintained exports. No runtime capture or execution test was
performed, so runtime-only mutation, allocator-failure behavior in practice,
and data-dependent indirect paths remain unverified unless explicitly stated
as static control flow.

## Evidence identity and address conventions

The static evidence is the clean extracted game:

| Input | Size | SHA-256 |
| --- | ---: | --- |
| `PRG/BTL.BIN` | `2,237,184` (`0x222300`) | `56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C` |
| `SLPS_258.37` | `5,273,256` | `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF` |

The `MWo3` header and loader mapping are established separately in
[NA2 MWo3 overlay ABI](../runtime/overlay_abi.md). They are essential here:

```text
BTL live address = 0x006B3F00 + raw BTL file offset
preserved Ghidra/export address = BTL live address - 0x40
BTL live address = preserved Ghidra/export address + 0x40
```

The complete `0x40`-byte header remains live at `0x006B3F00`. The preserved
Ghidra import omitted that header and mapped payload bytes `0x40` low. Encoded
absolute pointers and `jal` targets inside the overlay are already **live**
addresses. Consequently, those targets can make Ghidra create a symbol at the
live numeric address even though the displayed payload at that address is
actually the target's code `0x40` bytes late. Such a symbol is not a reliable
function boundary.

For example, the hub constructor begins at raw `0x055340`, is live at
`0x00709240`, and its bytes appear at preserved-export `0x00709200`. Resident
`FUN_001EF330` calls `0x00709240`, not `FUN_00709200` as a runtime address.
The generic node constructor begins at raw `0x055BA0`, live `0x00709AA0`, and
displayed `0x00709A60`; Ghidra also creates a misleading `FUN_00709AA0` at an
interior instruction because overlay calls encode the live target. All BTL
addresses in this document are live addresses unless explicitly labeled
`raw` or `export`. Resident ELF addresses have no `0x40` correction.

## Ownership model

The resident manager is an alias surface. Three other roots own live objects:
the battle-state object owns a small BTL hub, a global transient manager owns a
singly linked actor family, and a separate global support manager owns at most
one fielded support object per side.

```text
resident global 0x00607600
`- manager (0xDF8 bytes)
   |- +0xDE4 / +0xDE8  borrowed aliases to primary fighters
   `- +0xDF0 / +0xDF4  borrowed aliases to per-side control nodes

resident global 0x00607604
`- battle-state object (0x38 bytes)
   |- +0x14  borrowed alias to the selected registry-A root node
   `- +0x18  owning pointer to the 0x10-byte BTL hub
      |- +0x00  owning pointer to registry A
      |- +0x04  owning pointer to the per-side control registry
      |- +0x08  owning pointer to the fighter registry
      `- +0x0C  owning pointer to the shared-match registry

resident global 0x00607654
`- borrowed mirror of battle-state +0x18

resident global 0x00607820
`- transient-actor manager (0xD0 bytes)
   `- +0x14..+0x18  owning singly linked actor chain

resident global 0x00607888
`- dynamic-support manager (0x24 bytes)
   |- +0x04  owning side-0 support-object slot
   |- +0x08  owning side-1 support-object slot
   `- +0x14  embedded generation-ID allocator
```

The ownership classification follows the destructors, not the pointer graph:

- `FUN_001EEFD0` clears the manager aliases, calls the hub destructor, and
  clears battle-state `+0x18` and global `0x00607654`.
- Live BTL `0x00709280` destroys all four containers through their virtual
  destructor at container-vtable `+0x08`, nulls every hub field, and then frees
  the hub when requested.
- Each container destructor reaches live `0x00709F40`, which unlinks and
  virtual-destructs every node.
- Fighter/control/root/shared pointers linked at node `+0x20..+0x28` are
  cross-references. The linker at live `0x00709480` never transfers them to a
  distinct owner, and teardown does not free through those fields.

This produces an exact destruction order: registry A, per-side controls,
fighters, then shared-match nodes. Manager aliases are invalidated before that
node destruction begins.

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
| `+0xDEC` | `0` | reserved/zero control alias |
| `+0xDF0` | `1` | side-0 / Player-1 control node |
| `+0xDF4` | `2` | side-1 / Player-2 control node |

The usable mapping is therefore `array[side + 1]`. The index-zero entries are
not support slots. They remain zero in the creation path.

Configuration and runtime pointers use different strides. The exact side
formulas are:

| Value | Side-indexed manager address |
| --- | --- |
| selected primary character ID | `manager + 0x4C + side * 0x28` |
| selected support ID | `manager + 0x68 + side * 0x28` |
| published primary-fighter alias | `manager + 0xDE4 + side * 4` |
| published control-node alias | `manager + 0xDF0 + side * 4` |

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
clear or republish manager `+0xDE4/+0xDE8`. A patch that manually removes an
aliased primary fighter must therefore update the alias itself; registry
membership alone does not make a stale borrowed pointer safe.

### Battle-state and hub publication

Resident `FUN_001EC3B0` allocates a `0x38`-byte battle-state object, calls
`FUN_001EEC80`, publishes it at `0x00607604`, and calls `FUN_001EF330`.
The relevant `FUN_001EF330` path is:

1. Allocate `0x10` bytes when battle-state `+0x18` is null.
2. Call live BTL `0x00709240`, the hub constructor.
3. Store the hub at battle-state `+0x18` and global `0x00607654`.
4. Call live BTL `0x00709480` to create and cross-link the initial nodes.
5. Resolve sides `0` and `1` through live `0x00709800` and publish the results
   at manager `+0xDF0/+0xDF4`.
6. Resolve sides `0` and `1` through live `0x007099C0` and publish the results
   at manager `+0xDE4/+0xDE8`.
7. Call live `0x007096E0` and store its registry-A result at battle-state
   `+0x14`.
8. Call live `0x007095E0`, which invokes node virtual slot `+0x0C` across all
   four registries.

Resident `FUN_001EECD0` calls `FUN_001EEFD0`, resets the outer object, and frees
it when requested. `FUN_001EEFD0` destroys other resident-owned battle
subsystems first, zeros all six manager-array entries, calls live BTL
`0x00709280(hub, 1)`, then clears the state and global hub pointers. The
manager never frees a fighter or control node directly.

## Hub and registry construction

Live `0x00709240` zeros hub `+0x00/+0x04/+0x08/+0x0C` and calls live
`0x007092E0`, which builds:

| Hub field | Allocation | Constructor | Proven registry contents at initial creation |
| ---: | ---: | --- | --- |
| `+0x00` | `0x18` | live BTL `0x006D5640` | one specialized registry-A/root node |
| `+0x04` | `0x10` | live BTL `0x006F0F90` | two side control nodes |
| `+0x08` | `0x34` | resident `FUN_0024E0B0` | two primary fighter nodes |
| `+0x0C` | `0x10` | live BTL `0x00709150` | one shared-match node |

All four inherit the generic list prefix described below. Their virtual
destructors all clear owned nodes through live `0x00709F40`; the larger
fighter registry and specialized registry A also destroy their own additional
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
`+0x18/+0x1C/+0x20`. The constructor invokes it with state `1`.
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

Live `0x00709480` creates the initial graph in this order:

| Result | Creator | Allocation/initializer | Owning registry |
| --- | --- | --- | --- |
| registry-A root | `0x00709660` | `0x006DDE10` allocates `0x1D0`, then `0x006D6800` initializes it | hub `+0x00` |
| control side 0 | `0x00709780(hub, 0)` | allocates `0xC0`, calls `0x006EF4E0` | hub `+0x04` |
| control side 1 | `0x00709780(hub, 1)` | allocates `0xC0`, calls `0x006EF4E0` | hub `+0x04` |
| fighter side 0 | `0x00709860(hub, 0)` | character factory dispatch | hub `+0x08` |
| fighter side 1 | `0x00709860(hub, 1)` | character factory dispatch | hub `+0x08` |
| shared-match node | `0x00709A20` | allocates `0x90`, calls `0x007087A0` | hub `+0x0C` |

Each successful creator appends its result to the owning registry. Allocation
failure leaves that result null and the linker conditionally omits affected
cross-references.

This construction path assumes that its small structural allocations succeed;
it is not a transactional or generally OOM-safe graph builder. Live
`0x007092E0` attempts all four registry allocations independently and publishes
each result, including null. The registry-A creator checks its registry before
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
| fighter 0 `+0x28` | shared-match node |
| fighter 1 `+0x28` | shared-match node |
| control 0 `+0x20` | fighter 0 |
| control 1 `+0x20` | fighter 1 |
| control 0 `+0x24` | fighter 1 |
| control 1 `+0x24` | fighter 0 |
| registry-A root `+0x20` | fighter 0 |
| registry-A root `+0x24` | fighter 1 |

The reciprocal fighter `+0x20` relation agrees with the live-capture evidence
in [Character identity in battle](character_ids.md). The ownership proof is
stronger than field shape: all of these targets are ultimately destroyed by
their own registry, not by the referring node.

The shared-match node demonstrates nested ownership without changing that
conclusion. Its live constructor `0x007087A0` constructs an embedded generic
container at node `+0x60`, allocates an owned `0xAD0`-byte subobject and stores
it at `+0x70`, and initializes both. Its destructor at live `0x007088A0`
destroys/frees `+0x70`, clears the embedded list through `0x00709F40`, then
calls the generic node destructor. Fighter `+0x28` is still only a reference
to this independently registry-owned parent object. The original semantic name
of the shared object is not established.

## Primary-fighter factory and lookup

Live `0x00709860(hub, side)` computes `(side + 1) * 0x28` and reads the
manager's selected character ID from `+0x4C` for side 0 or `+0x74` for side 1.
It builds the common fighter descriptor and dispatches through the first word
of the eight-byte entry at resident `0x005A2900 + character_id * 8`. There is
no BTL-local character-ID bounds check before that indirect call. Entry zero's
factory word is null; entry one begins with factory `0x00250C00`.

The inspected character factories allocate their concrete fighter size and
call resident `FUN_002145D0` followed by `FUN_002151E0`. The common base
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
Concrete character destructors inspected in the factory family chain into this
common destructor. Neither the manager alias nor fighter cross-references are
used as owners during this chain.

On success, live `0x00709860` appends the concrete fighter to hub `+0x08`.
Live `0x007099C0(hub, side)` then:

- traverses that registry from `head` through node `+0x1C`;
- compares `(node_u8(+0x60) & 1)` with `side`;
- keeps scanning after a match and returns the **last** matching node; and
- returns null if none matches.

It does not test generic node flag byte `+0x00`. The resident setup calls it
once for each side and publishes the returned aliases at manager
`+0xDE4/+0xDE8`.

## Per-side control registry

Live `0x00709780` allocates a `0xC0` node, calls live `0x006EF4E0(node, side)`,
and appends the result to hub `+0x04`. The constructor calls the generic node
constructor, installs its own vtable, initializes owned storage, and calls
live `0x006EF600` for side binding.

The stable side-binding fields are:

| Control-node field | Proven value/role |
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

## Registry-A current-node semantics

The `0x18`-byte container at hub `+0x00` extends the generic list prefix with:

| Registry-A field | Proven behavior |
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
- live `0x007096E0(hub)` returns the last registry-A node whose generic-base
  word `+0x10` is zero. `0x00709660` explicitly writes zero there when the
  initial insertion makes the registry count one, and resident setup stores
  the lookup result at battle-state `+0x14`.

The original meaning of key `+0xA8` and of the root-selector word `+0x10` is
not established. Their comparison and current-node mechanics are established.

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
| `+0x10` | `s32` | `-1`; specialized by registry A |
| `+0x14` | pointer | base callback/data pointer `0x00604B60`, replaceable by subclasses |
| `+0x18` | pointer | previous intrusive-list node |
| `+0x1C` | pointer | next intrusive-list node |
| `+0x20..+0x2C` | four pointers | zero; subclass cross-reference slots |
| `+0x40..+0x4C` | 16 bytes | zero |
| `+0x50` | pointer | node vtable |

Live `0x00709B60` restores the base vtable, clears marker `+0x02`, and frees
the node when requested.

The generic maintenance passes are:

| Live function | Raw | Export bytes | Effect |
| --- | ---: | ---: | --- |
| `0x00709BF0` | `0x055CF0` | `0x00709BB0` | call each node's vtable slot `+0x0C` |
| `0x00709C70` | `0x055D70` | `0x00709C30` | update/remove pass described below |
| `0x00709D60` | `0x055E60` | `0x00709D20` | call each node's vtable slot `+0x14` |
| `0x00709DE0` | `0x055EE0` | `0x00709DA0` | call each node's vtable slot `+0x18` |

Live `0x00709C70` saves `next` before operating on a node. If node flag byte
`+0x00` bit 0 is set, it immediately unlinks and destroys that node. Otherwise
it calls node virtual slot `+0x10`; a nonzero return also unlinks and destroys
the node. Bit 0 therefore means **remove on the next container maintenance
pass**. A clear bit proves only that this immediate removal request is absent;
it does not by itself prove every higher-level meaning of “active.”

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
manager head. Unlike support generation allocation, this serial allocator has
no decoded collision avoidance at 32-bit wrap; if duplicates ever coexist,
live `0x00735F90` returns the first linked match.

### Factory, descriptor, and side mapping

Live `0x00736080` is the common create-and-link wrapper. It accepts only
selector `0` or `1`; any other value returns null. It computes
`stored_side = selector ^ 1`, calls class factory live `0x00729890`, calls
initializer live `0x0072B1F0`, installs initial transform/state through virtual
slot `+0x54`, and finally links the actor into the global manager. A mechanical
scan finds 87 direct BTL calls to this wrapper.

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
fourth argument is the inverted `stored_side`, so the wrapper's second
argument must not be mislabeled as the stored owner side.

Three small live helpers resolve the stored affiliation tag:

| Live helper | Raw | Input `node + 0x8A` | Result |
| --- | ---: | --- | --- |
| `0x00734130` | `0x080230` | `0` / `1` / other | opposite side `1` / `0` / `-1` |
| `0x00734160` | `0x080260` | `0` / `1` / other | opponent fighter at manager `+0xDE8` / `+0xDE4` / null |
| `0x007341A0` | `0x0802A0` | `0` / `1` / other | own fighter at manager `+0xDE4` / `+0xDE8` / null |

A mechanical scan of decoded direct BTL calls finds 34 calls to
`0x00734130`, 52 to `0x00734160`, and 50 to `0x007341A0`; those are reference
counts, not a claim that every decoded caller was exercised. This is a common
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

The resident manager fields `+0x68/+0x90` are the selected support IDs for
sides 0/1, as established in [Battle behavior knowledge](battle.md). The
corresponding derived implementation selector is at
`manager + 0x6C + side * 0x28`. None is consumed by the initial graph creator:

- live `0x00709860` reads only manager `+0x4C/+0x74`, the selected **primary
  character** IDs;
- live `0x00709480` creates exactly two primary fighters, two side-control
  nodes, one registry-A node, and one shared-match node; and
- resident `FUN_001EF330` publishes only primary-fighter and control aliases in
  the two three-entry manager arrays.

The fields also have a configuration-only normalization path. Resident
`FUN_001FE540` copies the two primary IDs and two support IDs from a setup
record, swapping the two source pairs together when its side-order byte is
nonzero. In a separate setup path, resident `FUN_001F2AC0` writes a selected
primary ID at manager `+0x74` and writes `0x26` at the paired side-1 support
field `+0x90`.

The true live entry `0x00886250` (preserved export label
`FUN_00886210`) later loops over the two `0x28`-byte side records. Whenever
`manager + 0x68 + side * 0x28` equals `0x26`, it calls live
`0x00885C30(primary_id, 0)`, truncates the result to a byte, and writes that
resolved value back to the same support-ID field. The function maps the
resolved support/primary pair to a byte and stores it at the paired `+0x6C`
implementation-selector field. Thus `0x26` is a configuration sentinel
resolved from the primary selection; it is not an entity pointer, list index,
or persistent runtime slot. Values `0x24` and `0x25` also receive special-case
treatment elsewhere, but this ownership pass did not establish domain names
for any of the three sentinels.

### Separate owner and exact side slots

The dynamic support owner is global `0x00607888` (`$gp - 0x3168`), independent
of both the hub and transient-actor manager. Resident `FUN_001EC7A0`, after
selecting BTL, calls live `0x00885210`. That function resets support-side global
counters, virtual-destroys any previous owner, allocates `0x24` bytes, calls
live constructor `0x00886CB0`, and publishes the result. Resident
`FUN_001EC890` calls live `0x00885290`, which virtual-destroys this owner and
clears the global.

The stable manager layout is:

| Offset | Type | Proven role |
| ---: | --- | --- |
| `+0x00` | pointer | owner vtable |
| `+0x04` | pointer | owning side-0 / Player-1 support-object slot |
| `+0x08` | pointer | owning side-1 / Player-2 support-object slot |
| `+0x0C..+0x11` | two 3-byte side records | configuration/control bytes detailed below; not pointers or occupancy |
| `+0x14` | embedded object | generation-ID allocator vtable |
| `+0x18` | `u32` | next support-object generation ID, initialized to `1` |
| `+0x1C` | `u8` | allocator wrap/reuse marker, initialized to zero |
| `+0x20` | `u8` | manager-local one-shot latch, initialized to one and cleared by the main pass |

Each side record is `owner + 0x0C + side * 3`:

| Record byte | Initialization | Proven later writer/use |
| ---: | ---: | --- |
| `+0x00` | `0` | live `0x00886250` writes one of the paired results from live `0x00885CE0`; support setup code reads it as a signed control value |
| `+0x01` | `1` | explicit getter live `0x00882630` and setter live `0x00882670`; multiple support specializations gate behavior on equality with `1` |
| `+0x02` | `0` | live `0x00886250` writes a signed result from the `0x008D1BB0` mapping table, with local default `2` |

The original meanings of these three values are unresolved, but their storage
class is not: they are per-side scalar state. Getter/setter and normalization
do not follow them as addresses, and support presence remains solely
`owner + 0x04 + side * 4 != 0`.

Live `0x00886950` allocates a generation value for each new support object and
live `0x008872E0` stores it at object `+0x120`. Before wrap it advances the
`+0x18` sequence directly; in reuse mode it compares candidates against the
two currently slotted objects' `+0x120` values. The field is therefore a
numeric generation ID, not a pointer to the manager or the other support.

The allocator contract is exact. Its input object is the embedded owner region
at `+0x14`: embedded `+0x04` is the current candidate and embedded `+0x08` is
the reuse marker. With the marker clear, live `0x00886950` returns the current
candidate and increments it. When the candidate is `0xFFFFFFFF`, it returns
that value, sets the reuse marker, resets the stored candidate to zero, and
immediately advances the next candidate to one. With reuse active, it compares the
candidate with an array containing the two current slot generations (zero for
an empty slot), advances past collisions, and returns the first free value.
This namespace is independent of side and of the transient manager's `+0x8C`
actor serials.

BTL also keeps a separate two-by-three array of signed 16-bit counters at
`0x008DCE90 + side * 6`. Live `0x00886BB0` zeros all six values. The first
halfword is incremented once after each successful new support allocation and
is returned by live `0x00886C20(side)`; slot destruction does not decrement it,
so it is a cumulative creation counter since the most recent reset, not current
occupancy. Live `0x00886C60(side, delta)` adds a signed delta to the third
halfword. The middle halfword is reset on the audited path, but no domain name
or direct nonzero writer was established. None of these counters is an object
pointer or generation ID.

### Request, class creation, and repeated calls

Resident `FUN_00238340`, the per-fighter manual support-request handler, reads
the hub mirror, follows hub `+0x08`, and requires the coordinator state at
registry `+0x14` to be zero. Resident `FUN_00238540`, called immediately after
it, uses the same gate. This is a coordinator-state test, not a support pointer
or fighter-list-count test. Its only direct resident caller is at
`0x0024DCA4`. When the request is accepted, it calls live
`0x00885490(fighter_side)`, which follows global `0x00607888` and calls live
`0x008872E0(owner, side)`. The resident function does not allocate directly;
this BTL call is the class factory and publisher. The related behavioral path
is summarized in [Support field-call and gauge paths](battle.md#support-field-call-and-gauge-paths).

For side `0/1`, the factory uses exact slot
`owner + 0x04 + side * 4` and reads the derived class selector from resident
manager `+0x6C + side * 0x28`. If the selector is `>= 0x44`, it returns zero.
The decoded cases allocate class-dependent sizes from `0x510` through `0x540`,
construct a common support-object base and any specialization, store the object
in its side slot, and invoke virtual initializer `+0x1C(selector, side)`. The
new object receives generic node flag-byte bits 1 and 2, receives its generation
ID at `+0x120`, and the request returns `1`.

If the side slot is already occupied, the factory neither appends nor replaces
the object. It calls the existing object's virtual slot `+0x24`; a nonzero
result makes the request return `2`, and a zero result makes it return `0`.
Resident `FUN_00238340` accepts both `1` and `2`. Thus this owner implements two
fixed **dynamic** side slots, with at most one fielded support object per side,
not a general list and not a pair of pre-created startup entities.

For a new object, the precise publication order is significant. Every class
allocation is checked before its constructor, but all cases then converge on
code that unconditionally stores the result into the selected owner slot and
immediately dereferences its vtable. A null allocation therefore does not
produce a clean request failure; the path assumes allocation success. With a
valid object, the slot becomes visible **before** virtual initializer `+0x1C`
runs, before flag bits 1 and 2 are set, and before generation `+0x120` is
assigned. Generation assignment snapshots both current slots after this
publication (the new constructor-cleared `+0x120` contributes zero), calls live
`0x00886950`, stores the returned ID, and only then increments the side's
cumulative creation counter and returns `1`. No alternate slot or rollback
pointer is retained.

The complete factory split is structural rather than semantic. All selectors
not named in the table but below `0x44` use the default row. “Final vtable” is
the pointer present when the common virtual initializer is invoked; several
small specializations deliberately call a broader constructor and then replace
its vtable.

| Implementation selector(s) | Allocation | Construction path | Final vtable |
| --- | ---: | --- | ---: |
| default in `0x00..0x43` | `0x510` | common live `0x00887A60` | `0x005FC240` |
| `0x0A` | `0x520` | live `0x0088DAB0` | `0x005FBD40` |
| `0x0C` | `0x510` | common constructor, then vtable replacement | `0x005FBE40` |
| `0x11` | `0x510` | common constructor, then vtable replacement | `0x005FBEC0` |
| `0x15`, `0x16`, `0x17` | `0x520` | live `0x0088CC60`, then vtable replacement | `0x005FC040` |
| `0x19` | `0x530` | live `0x0088E000` | `0x005FBCC0` |
| `0x1E` | `0x520` | live `0x0088C890` | `0x005FC1C0` |
| `0x1F` | `0x510` | common constructor, then vtable replacement | `0x005FC140` |
| `0x21` | `0x540` | live `0x0088D2D0` | `0x005FBF40` |
| `0x24` | `0x510` | common constructor, then vtable replacement | `0x005FBDC0` |
| `0x2A` | `0x510` | common constructor, then vtable replacement | `0x005FBC40` |
| `0x2B` | `0x520` | live `0x0088E460` | `0x005FBBC0` |
| `0x38` | `0x520` | live `0x0088CC60`, then vtable replacement | `0x005FBFC0` |
| `0x3F` | `0x530` | live `0x0088E5F0` | `0x005FBB40` |

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
| `+0xE4` | `u8` | side `0/1` passed by the owner |
| `+0xF2` | `u8` | owner-observed lifecycle state; value `2` requests final destruction |
| `+0x120` | `u32` | manager-assigned generation ID |
| `+0x134..+0x144` | five pointers | optional owned subobjects, virtual-destroyed by the common destructor |

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
not merely resource aliases. In contrast, the five `+0x80..+0x90` words are
initialized to null but are not freed by the common destructor; their
ownership status is not promoted here. The five `+0x134..+0x144` slots are
different: each nonnull entry is virtual-destroyed through slot `+0x08` and
then nulled.

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
`0x00886A40(side, token)`. That function does not recover or dereference the
originating support. It deduplicates nonzero tokens in a four-entry ring at
`0x008DCFF0 + side * 0x14`, advances the ring cursor in the fifth word, updates
the third per-side signed counter through `0x00886C60`, and conditionally sets
bit 0 of the **currently slotted** support's byte `+0x50C`. The common support
constructor clears bits 0..2 and sets bit 3 of `+0x50C`.

This is a proven cross-manager lineage relation but not an ownership edge: the
actor stores no support pointer, support replacement cannot leave it with a
dangling parent address, and each object remains destroyed by its own manager.
The original event meaning of the token report and `+0x50C` flags remains
unresolved.

Resident master dispatcher `FUN_001F03E0` routes three support phases through
live wrappers `0x00885400`, `0x00885430`, and `0x00885460`. The resulting owner
passes are:

- live `0x00886ED0` calls object virtual `+0x10` when generic flag bit 1 is set;
  after that call, object `+0xF2 == 2` causes virtual destruction through
  `+0x08` and immediate clearing of the side slot;
- live `0x008871A0` calls virtual `+0x14` only when generic flag bit 2 is set;
  and
- live `0x00887250` calls virtual `+0x18` only when generic flag bit 1 is set.

Bits 1 and 2 are dynamic callback-enable gates, not slot membership. At the
start of the main pass, live `0x00886ED0` derives two booleans and overwrites
both flag bits on **each** occupied side slot before dispatch. Both begin true;
resident primary-fighter-0 fields `+0xB00 != 0` or signed `+0xB10 != 0` clear
both, while additional global battle-mode predicates can clear bit 1 without
necessarily clearing bit 2. The exact gameplay meanings of those external
predicates are outside this ownership map, but the structural result is firm:
both side objects receive the same per-pass enable values, and bit 1 and bit 2
can diverge.

Live `0x00887830(owner)` is a distinct explicit disable operation. For every
occupied slot it first calls object virtual `+0x28`, then clears bits 1 and 2;
it neither destroys the object nor clears the owner slot. Direct resident calls
occur at `0x0023B620` and `0x00245988`. A later main pass may rewrite the bits,
so this operation is not evidence of permanent removal. Also, lifecycle state
`+0xF2 == 2` is checked only inside the bit-1-enabled main-dispatch path. The
authoritative membership predicate remains the nonnull owner slot, and
unconditional owner teardown ignores both enable bits.

Live `0x008854D0(side)` is a boolean presence query and live
`0x00886750(side)` returns the slotted object pointer. Neither tests flag bits
or `+0xF2`, so a support remains discoverable until its owner actually destroys
it and clears the slot. Whole-owner destruction live `0x00886DE0` calls live
`0x00887990(owner, -1)` to virtual-destroy both objects and clear both slots.
A battle reset can do the same without freeing the owner through live
`0x00886E70`. No support object is appended to the hub registries or the
`0x00607820` transient-actor chain.

An exhaustive scan found 25 direct loads/stores of global `0x00607888` in the
decoded BTL image. The additional references either access the 3-byte side
records, read an existing side slot, or dispatch a virtual event to an existing
slot. No alternate slot array or owner was found. Global publication/clearing
remains live `0x00885210/0x00885290`; nonzero side-slot publication remains
live `0x008872E0`; and live `0x00887990` is the corresponding destroy-and-null
writer.

## Lookup and identity contract matrix

These lookup APIs use distinct namespaces and do not share a universal
“active” test:

| API | Input namespace and selection | Match order / filtering | Invalid or absent result |
| --- | --- | --- | --- |
| resident `FUN_003769C0` | primary-fighter alias by side | direct manager `+0xDE4/+0xDE8`; no node-flag test | null unless side is exactly `0` or `1` |
| live `0x00709800` | control node by full `u32 +0x60` side | last matching hub-list node; no generic-flag test | null when no match |
| live `0x007099C0` | primary fighter by `(u8(+0x60) & 1)` side | last matching hub-list node; no generic-flag test | null when no match |
| live `0x006D5900` | registry-A node by `u32 +0xA8` key | last key match; ignores current marker | null when no match |
| live `0x006D5960` | registry-A key plus requested `u8 +0x60` current bit | last key/bit match | null when no match |
| live `0x00709740` | registry-A current node by key | wrapper over `0x006D5960(..., 1)` | null when no current match |
| live `0x00735F90` | transient actor by `u32 +0x8C` serial | first match reachable from manager head; no separate flag test | null if manager absent or no match |
| live `0x00735990` | next transient actor by `s16 +0x78` type, side-selector mapping, and cursor | first qualifying node after cursor, or from head for null cursor | null when exhausted |
| live `0x00735910` / `0x00735A30` | same transient type/side predicate | boolean existence / total matching count | zero when none |
| live `0x008854D0` | support occupancy by side slot | boolean nonnull slot; ignores flags and lifecycle state | zero if owner absent; side index itself is unchecked |
| live `0x00886750` | support object by side slot | returns the exact slot pointer; ignores flags and lifecycle state | null if owner absent; side index itself is unchecked |

There is no decoded public lookup from support generation `+0x120` back to a
support object. The generation allocator compares candidates with the two
current values only to avoid reuse, while transient descendants merely copy
the value as a lineage token. Code that needs the support object resolves its
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
| `0x001EF330` `FUN_001EF330` | construct hub/graph, resolve four side aliases, publish registry-A root, then create transient-actor manager |
| `0x001EEFD0` `FUN_001EEFD0` | destroy transient-actor manager, invalidate aliases, destroy hub, clear hub pointers |
| `0x001EECD0` `FUN_001EECD0` | outer battle-state destructor; calls `FUN_001EEFD0` |
| `0x001F03E0` `FUN_001F03E0` | master battle phase dispatcher; schedules the three support-owner passes and both transient-actor passes from independent mask bits |
| `0x002145D0` `FUN_002145D0` | common primary-fighter base constructor; calls live BTL `0x00709AA0` |
| `0x00214840` `FUN_00214840` | common fighter destructor/optional final free |
| `0x002151E0` `FUN_002151E0` | common fighter initializer; establishes `+0x68` identity and `+0x60` side bit |
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

The table gives the true entry, raw file offset, and where its first byte is
displayed by the preserved header-skipped export. A Ghidra symbol whose name
matches a live numeric target can still be an interior false start.

| Live | Raw | Export bytes | Working role |
| ---: | ---: | ---: | --- |
| `0x006D5640` | `0x021740` | `0x006D5600` | registry-A container constructor |
| `0x006D57A0` | `0x0218A0` | `0x006D5760` | registry-A insert/current replacement |
| `0x006D5900` | `0x021A00` | `0x006D58C0` | registry-A lookup by `+0xA8` key |
| `0x006D5960` | `0x021A60` | `0x006D5920` | registry-A key/current lookup |
| `0x006D6800` | `0x022900` | `0x006D67C0` | registry-A node initializer |
| `0x006DDE10` | `0x029F10` | `0x006DDDD0` | allocate/initialize one `0x1D0` registry-A node |
| `0x006EF4E0` | `0x03B5E0` | `0x006EF4A0` | side-control node constructor |
| `0x006EF600` | `0x03B700` | `0x006EF5C0` | bind control node to side/input state |
| `0x006F0F90` | `0x03D090` | `0x006F0F50` | side-control registry constructor |
| `0x00707350` | `0x053450` | `0x00707310` | construct an optional transient-actor child |
| `0x00707920` | `0x053A20` | `0x007078E0` | child state/drain test; reports recyclable at state `>= 2` |
| `0x007083D0` | `0x0544D0` | `0x00708390` | construct transient manager's deferred-child-list owner |
| `0x00708480` | `0x054580` | `0x00708440` | destroy all deferred children / optional owner free |
| `0x00708570` | `0x054670` | `0x00708530` | prepend a child to the deferred-child list |
| `0x00708630` | `0x054730` | `0x007085F0` | maintain and recycle deferred children |
| `0x00708720` | `0x054820` | `0x007086E0` | run the deferred children's second pass |
| `0x007087A0` | `0x0548A0` | `0x00708760` | shared-match node constructor |
| `0x007088A0` | `0x0549A0` | `0x00708860` | shared-match node destructor |
| `0x00709150` | `0x055250` | `0x00709110` | shared-match registry constructor |
| `0x007091A0` | `0x0552A0` | `0x00709160` | shared-match registry destructor |
| `0x00709240` | `0x055340` | `0x00709200` | hub constructor |
| `0x00709280` | `0x055380` | `0x00709240` | hub destructor/free wrapper |
| `0x007092E0` | `0x0553E0` | `0x007092A0` | allocate four registries |
| `0x007093A0` | `0x0554A0` | `0x00709360` | virtual-destroy and null four registries |
| `0x00709480` | `0x055580` | `0x00709440` | create and cross-link initial graph |
| `0x007095E0` | `0x0556E0` | `0x007095A0` | registry-wide vtable-`+0x0C` pass |
| `0x00709660` | `0x055760` | `0x00709620` | create initial registry-A node |
| `0x007096E0` | `0x0557E0` | `0x007096A0` | registry-A root selector by node `+0x10 == 0` |
| `0x00709740` | `0x055840` | `0x00709700` | current registry-A node lookup by key |
| `0x00709780` | `0x055880` | `0x00709740` | create/append one side-control node |
| `0x00709800` | `0x055900` | `0x007097C0` | find last control node by `u32 +0x60` side |
| `0x00709860` | `0x055960` | `0x00709820` | create/append one primary fighter |
| `0x007099C0` | `0x055AC0` | `0x00709980` | find last fighter by `u8 +0x60` low side bit |
| `0x00709A20` | `0x055B20` | `0x007099E0` | create/append shared-match node |
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
| `0x00882630` | `0x1CE730` | `0x008825F0` | get byte 1 of one dynamic-support owner side record |
| `0x00882670` | `0x1CE770` | `0x00882630` | set byte 1 of one dynamic-support owner side record |
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
| `0x00886950` | `0x1D2A50` | `0x00886910` | allocate a support-object generation ID, avoiding live slot IDs after wrap |
| `0x00886A40` | `0x1D2B40` | `0x00886A00` | consume/deduplicate a transient actor's support-lineage token for one side |
| `0x00886BB0` | `0x1D2CB0` | `0x00886B70` | reset the two three-halfword support counter records |
| `0x00886C20` | `0x1D2D20` | `0x00886BE0` | return one side's cumulative successful-support-creation counter |
| `0x00886C60` | `0x1D2D60` | `0x00886C20` | add a signed delta to one side's third support counter |
| `0x00886CB0` | `0x1D2DB0` | `0x00886C70` | construct the `0x24` dynamic-support owner and embedded generation allocator |
| `0x00886DE0` | `0x1D2EE0` | `0x00886DA0` | destroy both support slots and optionally free the owner |
| `0x00886E70` | `0x1D2F70` | `0x00886E30` | destroy both support slots without freeing the owner |
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

## Confidence, unresolved semantics, and negative results

High-confidence results, backed by direct allocation, stores, traversal, and
destructor edges, are:

- complete-file live mapping and the preserved export's `0x40` bias;
- manager array layout and side-to-slot mapping;
- battle-state ownership of the hub and the hub's ownership of four
  registries;
- primary fighter/control creation, lookup, publication, and destruction;
- fighter-registry coordinator state and auxiliary ownership;
- intrusive-list layouts and container ownership of nodes;
- transient-actor manager ownership, serial lookup, and deferred child
  release;
- dynamic-support manager ownership, exact side slots, selector-driven class
  creation, generation IDs, lookup, three passes, and destruction;
- generic remove-on-pass flag bit 0;
- registry-A current marker `+0x60` and key lookup behavior;
- initial cross-references and their non-owning character; and
- the `+0x8A` side tag, factory-side inversion, and own/opponent
  primary-fighter resolvers for the inspected transient-actor family.

Names such as “hub,” “registry A,” “side control,” and “shared-match node” are
working names. Original class/type names are unavailable. The following remain
unresolved and must not be silently promoted to established structure names:

- the domain meaning of registry-A node key `+0xA8` and selector word `+0x10`;
- the exact gameplay role of the shared-match node;
- the original names and exact gameplay meanings of the support selector
  values and their class specializations; and
- whether “return last match” is a deliberate duplicate policy or simply the
  implementation shape of these small scans.

Negative findings are equally important:

- manager `+0xDE0/+0xDEC` are reserved zero entries, not entity slot zero;
- manager `+0xDF0/+0xDF4` are per-side control nodes, not support pointers;
- manager `+0xDE4/+0xDE8` are aliases, not owners or a general entity registry;
- fighter-registry `+0x14` is coordinator state, not a support-instance pointer
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
- generic flag byte bit 1 is not the generic active/removal predicate;
- transient actor `+0x60` is not an authoritative active/linked flag after
  unlink; byte `+0x86` is;
- node `+0x20..+0x28` graph pointers do not establish ownership; and
- a preserved Ghidra `FUN_00xxxxxx` name at an encoded live BTL target does not
  by itself establish the true function start.

The investigation was static and read-only. Direct R5900 disassembly of the
clean resident ELF and raw BTL image was used to verify every address and
store; the maintained Ghidra C/text exports were supporting cross-reference
views only.
