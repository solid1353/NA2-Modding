# Battle-session and stage lifecycle

Static ownership, construction, linking, teardown, and update-cadence evidence
for the BTL overlay. This deliberately does not assign AI, status-effect, match-outcome,
Practice, or Adventure semantics to the structural objects.

The clean BTL input and its address conversion are defined in
[Standard game file identities](../game/files/file_identities.md). Its
internal name is `BTL_product.bin`.

## Research coverage

- **Assigned scope:** structural BTL match-session ownership: resident entry
layering, root and outer-graph construction, fixed child allocation, actor/side
linkage, stage-owner/controller binding, update cadence, and the matching destruction order.
- **Exploration depth:** the resident setup/teardown call sites and every direct BTL call to the root
initializer, graph build/broadcast family, and constructor-only stage-owner
reset were enumerated in the clean images. Fixed allocations, field links,
side-paired arrays, vtable destruction edges, the 24-entry stage path table,
and the otherwise indirect stage-owner destructor chain were traced through
their complete scoped bodies. This is exhaustive for those direct-call and
fixed-table boundaries, not for every virtual phase callback or semantic role
inside the child objects.
- **Confirmed coverage:** resident entry layering, root and outer-graph
  construction, fixed child allocation, actor/side linkage,
  stage-owner/controller binding, nominal fighter-update cadence, and reverse destruction order are established
  within the direct-call and fixed-table boundaries.
- **Unresolved or untested:** the original names of most root children, the meaning and writers of root byte
`+0x21`, and any indirect per-round reset remain unresolved.
- **Deliberate exclusions and overlap:** AI, statuses, outcomes, Practice,
  per-round gameplay, and Adventure were deliberately excluded.
- **Evidence limitations:** no runtime allocation trace, stage swap, round
transition, or teardown capture was performed. Consequently the ownership
and address relationships are strong static results, while round-level
reachability beyond the documented match-session boundary remains unproven.

## Battle update cadence

Native battle gameplay advances fighter updates at 30 Hz at nominal speed.
PCSX2 can report 60 VPS while the game still advances those fighter updates at
30 Hz; emulator turbo changes their wall-clock rate without changing the
gameplay cadence expressed in updates.

## Address map

| Role | Export | Live | File offset |
| --- | ---: | ---: | ---: |
| `mwo3_entry` | `0x006B3F40` | `0x006B3F80` | `0x80` |
| root constructor | `0x006B4140` | `0x006B4180` | `0x280` |
| root embedded-member constructor | `0x006B41A0` | `0x006B41E0` | `0x2E0` |
| root destructor | `0x006B41F0` | `0x006B4230` | `0x330` |
| root one-time initialization | `0x006B44A0` | `0x006B44E0` | `0x5E0` |
| outer graph constructor | `0x00709200` | `0x00709240` | `0x55340` |
| outer graph destructor | `0x00709240` | `0x00709280` | `0x55380` |
| graph build/link | `0x00709440` | `0x00709480` | `0x55580` |
| graph lifecycle broadcast | `0x007095A0` | `0x007095E0` | `0x556E0` |
| stage-owner factory | `0x007099E0` | `0x00709A20` | `0x55B20` |
| stage-owner constructor | `0x00708760` | `0x007087A0` | `0x548A0` |
| stage-owner destructor | `0x00708860` | `0x007088A0` | `0x549A0` |
| constructor-only owner reset | `0x007089E0` | `0x00708A20` | `0x54B20` |
| controller global registration | `0x006C1A00` | `0x006C1A40` | `0xDB40` |
| stage select/controller setup | `0x006C1A10` | `0x006C1A50` | `0xDB50` |
| controller zero-initialization | `0x006C2890` | `0x006C28D0` | `0xE9D0` |
| stage global cleanup | `0x006C2960` | `0x006C29A0` | `0xEAA0` |
| controller deep cleanup | `0x006C29A0` | `0x006C29E0` | `0xEAE0` |
| stage path table | `0x008909D0` | `0x00890A10` | `0x1DCB10` |

The preserved symbol near the stage factory is shifted into the wrong body;
the raw prologue begins at export `0x007099E0`.

## Resident ownership and entry layering

Resident global `0x00607604` points to a `0x38`-byte battle session.
`mwo3_entry` loads that session and returns `*(session + 0x30)`, or zero when
there is no session. The return value is the `0x70`-byte BTL root itself, not
its embedded queue. The shared queue/task member is another `+0x30` inside the
root. Resident `FUN_001FD850` confirms this layering by calling the live entry
and then reading returned-root field `+0x1C`.

`FUN_001EC3B0` allocates the session, initializes it through `FUN_001EEC80`,
stores the global, and enters `FUN_001EF330`. Destruction travels through
`FUN_001EECD0 -> FUN_001EEFD0`, clears fields, and frees the session.

## Fixed construction order

`FUN_001EF330` first creates a `0x10`-byte outer graph at session `+0x18`,
publishes it at global `0x00607654`, calls live `0x00709480` to build it, and
then calls live `0x007095E0`. The graph owns four pointers at `+0`, `+4`, `+8`,
and `+0xC`, whose containers are allocated as `0x18`, `0x10`, `0x34`, and
`0x10` bytes.

Graph construction obtains a main object, two side objects, two per-side
battle actors, and one shared stage owner. It establishes these links:

- actor `0` and actor `1` point to each other at `+0x20`;
- both actors point to the stage owner at `+0x28`;
- each actor points to its side object at `+0x24`;
- each side object points to its own actor at `+0x20` and the opponent actor at
  `+0x24`;
- the main object points to actors 0 and 1 at `+0x20` and `+0x24`.

Live `0x007095E0` walks all four containers and dispatches vtable slot `+0x0C`
for each member. Its only resident caller uses it once after graph construction,
so this is a post-build lifecycle broadcast; it is not proven to be a round
reset.

Later in the same setup, resident `0x001EF620` allocates the `0x70`-byte root,
calls live constructor `0x006B4180`, stores it at session `+0x30`, and calls
live `0x006B44E0`. The constructor already called the same initializer; root
byte `+0x20` makes the resident's second call idempotent.

## Root component forest

The root constructor initializes its embedded `+0x30` member through resident
`SUB_00119290(member, 0x006B41E0, 0x0010A0F0, 0x40, 1)`, clears byte `+0x20`,
and enters one-time initialization. The initializer registers the embedded
member and allocates this fixed forest:

| Root field | Allocation | Shape |
| --- | ---: | --- |
| `+0x04` | `0xB10` | two `0x580` objects |
| `+0x00` | `0x98` | two `0x44` objects |
| `+0x08` | `0x650` | two `0x320` objects |
| `+0x14` | `0x28` | singleton |
| `+0x10` | `0xF0` | two `0x70` objects |
| `+0x18` | `0xB0` | two `0x50` objects |
| `+0x0C` | `0x90` | two `0x40` objects |
| `+0x1C` | `0x34` | resident-owned singleton |

Every paired array is immediately registered with side IDs 0 and 1. Public
accessors at live `0x006B3FB0`, `0x006B4000`, `0x006B4050`, and `0x006B40B0`
independently expose arrays with strides `0x44`, `0x50`, `0x580`, and `0x320`.
Initialization ends with `root+0x21 = 0` and `root+0x20 = 1`. The children's
semantic names remain deliberately unresolved.

## Teardown order

Resident `FUN_001EEFD0` destroys session `+0x30` first through live
`0x006B4230(root, 1)` and clears it. The root destructor destroys paired arrays
in field order `+4`, `+0`, `+8`, `+0x10`, `+0x18`, `+0x0C`; destroys and frees
the `+0x14` and `+0x1C` singletons; tears down embedded `root+0x30`; and frees
the root when its signed 16-bit delete flag is positive.

Only afterward does the resident destroy the outer graph at session `+0x18`
through live `0x00709280`, clear that field, and clear global `0x00607654`.
Thus the BTL root dies before the actor/stage ownership graph. The otherwise
indirect stage-owner destructor is proven through graph destruction, stage
container vtable `0x005DDD60`, container cleanup, and stage-owner vtable
`0x005DDD80` to live `0x007088A0`.

## Stage content binding

The stage factory allocates a `0x90`-byte owner, constructs it with fallback
stage ID zero, and inserts it into graph field `+0x0C`. The owner allocates a
`0xAD0`-byte controller, initializes it at live `0x006C28D0`, publishes it
through live `0x006C1A40` to global `0x006077E4`, stores it at owner `+0x70`,
and calls live `0x006C1A50`.

When battle-manager global `0x00607600` exists, the signed stage ID comes from
manager byte `+0x98`; otherwise it uses the constructor fallback. Stage setup
mirrors the ID to manager `+0x98`, a second subsystem `+0x0E` when present, and
controller `+0x0C`. It indexes live table `0x00890A10 + id * 4`, loads the path
through resident `SUB_001AA4B0`, stores the resource handle at controller
`+0x00`, and allocates a `0x150`-byte child at `+0x04`.

The live table contains exactly slots 0 through 23, mapping to
`stage/s01.ccs` through `stage/s24.ccs`. The preserved export's shifted data
mapping makes the encoded live address appear to begin at its `s21` label;
the raw file table begins at offset `0x1DCB10` with the `s01` pointer. There is
no range check before indexing; the caller must constrain the slot.

Owner construction finishes through live `0x00708A20`, which clears owner
fields `+0x74/+0x78`, snapshots controller `+0x10` to `+0x7C`, and clears
`+0x80` and byte `+0x84`. A full direct-JAL scan found this function only in
the constructor, so it is a constructor reset, not a proven per-round reset.

Stage-owner destruction calls controller deep cleanup at live `0x006C29E0`,
then live `0x006C29A0`, which resets the related resident subsystem and clears
global `0x006077E4`. It frees optional controller field `+0xA88`, frees the
controller, clears owner `+0x70`, and tears down the owner's member and base.

## Limits and negative results

- No separate top-level round-reset path was proven. Root initialization,
  graph build/broadcast, and stage-owner clear occur only at match-session
  construction in the direct-call evidence.
- Root byte `+0x21` gates phase callbacks, but no write establishing a
  round-reset transition was found in this cluster.
- The stage-owner destructor is virtual and has no direct JAL caller; its
  container/vtable teardown chain supplies the evidence.
- Findings are static; no runtime validation was performed.
