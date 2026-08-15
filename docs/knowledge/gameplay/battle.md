# Battle behavior knowledge

This document owns unresolved and established leads about battle behavior that
do not belong to a narrower gameplay subsystem.

## Practice starting-HP selector

Practice Settings stores its native HP selection as an integer enum: `0` is
Normal/full, `1` is Half, and `2` is Almost/critical. In the immutable menu
savestates `SLOP-NA228 (7DB97F53).01.p2s` through `.03.p2s`, the only aligned
32-bit location following that `0/1/2` pattern is EE `0x00EAFC8C`, inside the
allocator block at `0x00EAFC10` offset `+0x7C`.

The paired post-selection Practice savestates `.04.p2s` through `.06.p2s`
prove that the enum is consumed by battle setup for both fighters. Their live
fighter `float32` HP at fighter `+0x6C` is respectively `1.0`, `0.5`, and the
float32 representation of `0.1`. P1's captured fighter was at `0x00E36DA0`
and P2's at `0x00E44BF0`; the values were identical for both sides in each
state.

Clean `SLPS_258.37` function `FUN_001e7a80` initializes three Practice settings
blocks and is also reused by the native reset paths. At runtime `0x001E7AE8`
(ELF offset `0xE7BE8`) it executes `sb zero,1(a0)` followed by `li t1,2`; the
next instruction stores `t1` to settings byte `+2`. Settings byte `+1` is
therefore the native starting-HP enum. The QoL variants retain those eight
clean bytes for full HP, store the function's existing constant `a1 == 1` for
half HP, or reorder the existing `li t1,2` before storing `t1` to byte `+1`
for critical HP. All variants preserve the next native store of `2` to byte
`+2` and require the exact clean eight-byte guard.

The evidence source was clean `SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`, plus
the six copied savestates. State SHA-256 values, in slot order, were
`7FF50D4BF622BF24CC5FB460544D4B322E17E9A36285A391844D4471441EB460`,
`0241AD14603EE6E051A2AA7A0A5DFE099323D0FDE2FA2523914A0FB82D524B9E`,
`749603808FF9CE7ECA8C13CCDC57396B3CE3BF67B9735A2E57A6FA72247FCC40`,
`AC9FA2A7D922684C1B4517A2048F297CD607B7DC8BAC641949F4EE0DC69AF820`,
`7D1379E12316124B64EE83CED270799BFEC846C6D499552E7A0FD48D3C5776E3`,
and `4B873D93C9591978348717B89296B75926EA682874A16F6EC569228321524A54`.

## Direct Practice bootstrap

The deterministic recording `bootstrap.p2m2`, SHA-256
`AA4330C0A32381BE52FE135298AED92A526825D93E9BA126E8D9645D62987B87`,
was replayed against the verified Manual ISO with SHA-256
`FCF132A7E626A8B85A4767E53569A7A98E3A04EBEC073F4AD412A67CAE4D5A23`.
Its eight ordered markers establish a baseline menu/battle pair, two distinct
active awakenings, a different Player 1 menu/battle pair, and a different
support menu/battle pair. The captured matchups were Tsunade with Shizune
versus Naruto with Sakura, Jiraiya with Shizune versus the fixed opponent, and
Tsunade with Yamato versus the fixed opponent.

The global at EE `0x00607600` points to the manager. Comparing the marker
states confirms the following selection fields:

| Manager field | Meaning |
| ---: | --- |
| `+0x4C` | Player 1 current character ID |
| `+0x68` | Player 1 current support ID |
| `+0x74` | Player 2 current character ID |
| `+0x90` | Player 2 current support ID |
| `+0x98` | stage ID byte; Practice used `6` |
| `+0xC8` | Player 1 match-start character ID |
| `+0xE4` | Player 1 match-start support ID |
| `+0xF0` | Player 2 match-start character ID |
| `+0x10C` | Player 2 match-start support ID |
| `+0xDE4` | Player 1 live-fighter pointer |
| `+0xDE8` | Player 2 live-fighter pointer |

The confirmed IDs are Tsunade `0x54`, Jiraiya `0x53`, Naruto `0x39`, Shizune
support `0x1A`, Yamato support `0x1F`, and Sakura support `0x01`.

`FUN_001e9980` owns the outer manager state at `+0x08` and mode/substate at
`+0x0C`. After successful Continue startup, clean runtime `0x001E9AF8`
(ELF `0xE9BF8`) writes state `4`, substate `1`; substate `3` instead calls
`FUN_001ea940`, which constructs the Practice controller with
`FUN_001ec300(2)`. The bootstrap changes only this successful-Continue block
to store substate `3`.

The Practice controller at global `0x00607620` dispatches through
`FUN_001ec960`. States `1` through `6` perform native resource preparation.
State `7` normally calls `FUN_001ed450` to construct Character Select. State
`9` normally constructs the final VS/Practice Settings screen, then stores the
stage, calls `FUN_002005b0(1, 0)`, and enters state `10`. The bootstrap hook at
runtime `0x001ECA2C` (ELF `0xECB2C`) replaces only the state-`7` call: it writes
the current and match-start identity fields, fixes the opponent and stage,
sets the native three-frame countdown, calls `FUN_002005b0(1, 0)`, and enters
state `10`. States `10` through `15` remain native, including both fighters'
construction and stage loading.

In the baseline battle marker the live fighter's effect container at fighter
`+0x8C4` was empty and `u16` field `+0x8E8` was `0xFFFF`. The two status markers
contained one effect and changed `+0x8E8` to `0x57` and `0x22`, respectively;
their visible HUD abbreviations were `Nin.` and `Reg.`. `0x57` belongs to
Tsunade's fighter-controller effect set. `0x22` is carried only by her Ultimate
Jutsu record `191` and is applied as a post-Ultimate-Jutsu regeneration effect.
When the `0x22` object is destroyed, its dedicated destructor `FUN_003037c0`
hard-codes a call to `FUN_00305c30` for effect `0x23`. The immutable slot-1
savestate for CRC `5999E2B0` captured that successor as Tsunade's sole live
effect: its node ID at `+0x68` and fighter `+0x8E8` were both `0x23`. No other
effect destructor applies a successor. All three effects are valid starting
states for the bootstrap, but their native sources express different ownership
and entry paths rather than three global awakening categories.

### Native effect ownership and entry paths

The fighter-controller association lists are the 94 eight-byte entries at
runtime `0x005C1D30` in clean `SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`.
The second word is the count. A zero count means no associated controller
effect; a count of one stores the ID inline in the first word; larger counts use
the first word as a pointer to a `u16` ID array. The table's consumers are the
fighter awakening controller: `FUN_0020cf40` tests associated active effects,
`FUN_0020d690` validates and applies a selected class-`7` Ultimate-Jutsu effect,
`FUN_0020d910` chooses a controller effect when a character-specific condition
fires, and `FUN_0020ddc0` handles associated-effect state and removal. Table
membership does not establish an activation route. Sai's `0x62` and Naruto's
`0x72`, for example, are table members but are entered only through Ultimate
Jutsu paths.

Ultimate Jutsu metadata is independently owned. The per-character record lists
begin at runtime `0x005ACFB0`; each selected record indexes one of 223
`0x14`-byte entries at `0x005AEC40`, whose `u16` field `+0x0E` is the requested
post-move effect ID or `0xFFFF`. `FUN_00372b10` reads that field. For cinematic
Ultimate Jutsu, `FUN_0035e360` stores the selected record's effect in
`DAT_00604310`, and `FUN_0024ed40` obtains it through `FUN_0036c1e0` after the
move and applies it through `FUN_00307690`. Class-`7` records instead feed the
same field through fighter `+0x18A` to `FUN_0020d690`. Both paths ultimately use
the shared effect engine.

Comparing the controller and Ultimate-Jutsu sources for all 74 named characters
yields 42 character/effect pairs found only in the controller table, 34 present
in both sources, and 22 found only in Ultimate-Jutsu records. Ten characters
have no controller-table entry but do have Ultimate-Jutsu effects. Hard-coded
transformed-form initialization is a third source. `FUN_00372d00` maps effects
`0x68..0x71` to transformed character IDs `0x2F..0x38` and also maps `0x72` to
`0x49` and `0x73` to `0x4B`; `FUN_0035b3b0` requests the mapped form through
`FUN_001ec5e0`. During fighter construction, `FUN_00305ff0` applies those same
12 character/effect mappings directly. Eleven of those pairs duplicate entries
already found in the other sources. Sasori (Puppet) `0x4B -> 0x73` is the only
pair supplied solely by this constructor mapping. Thus a base character's
Ultimate-Jutsu record can own the transition while the transformed character's
constructor or controller entry owns the resulting active form.

There is no exhaustive native `character -> possible active effects` table.
The builder's `awakening_ids` column is the union needed by the bootstrap: the
controller-table IDs, every non-`0xFFFF` effect in that character's
Ultimate-Jutsu records, hard-coded effects applied when transformed forms are
constructed directly, and the sole hard-coded successor `0x23`. It declares
character compatibility, not how an effect is normally entered.
`FUN_003047c0` classifies the broader native effect domain `0..0x89`, but that
global range does not establish character compatibility. The bootstrap accepts
`none` or one ID from the selected Player 1 row and passes that ID through
unchanged.

`FUN_00305c30(fighter, effect_id, -1, 1)` is the native high-level effect
entry: it validates the effect category, resolves the default parameter,
constructs the effect through `FUN_00305270`, performs native side effects,
and writes the active effect ID to fighter `+0x8E8`. The hook at runtime
`0x001ECACC` (ELF `0xECBCC`) retains `FUN_001edb70`, then invokes this entry
once after the Player 1 fighter exists. It retries until `+0x8E8` confirms the
requested ID and resets its one-shot state whenever a new bootstrap reaches
controller state `7`.

An active effect and the fighter controller's awakened state are distinct.
`FUN_0020d910` applies the effect chosen by the condition-driven controller,
sets fighter `+0x63` bit `0x20`, and runs the native transition sequence through
`FUN_00223360`, `FUN_00223140`, and, outside the alternate battle mode,
`FUN_001d87c0` and `FUN_00334ff0`. Applying Tsunade's `0x57` through
`FUN_00305c30` alone demonstrated the distinction: the effect container was
populated, but the base moveset remained and the controller could activate the
same awakening again.

The per-character trigger descriptor is the four-byte table at runtime
`0x005C1B50`; its flags are the halfword at `+0x02`. In `FUN_0020e280`, trigger
bits `1..5` feed `FUN_0020d910`, bit `0` describes an already-active or
constructor-owned form, and bit `6` instead feeds the exact selected class-`7`
Ultimate-Jutsu effect through `FUN_0020d690`. Combining bits `1..5` with the
association lists identifies 38 clean-start character/effect pairs that use
`FUN_0020d910`. Most select the association list's first ID. Hinata `0x50`,
Shizune `0x55`, Kurenai `0x57`, and Yamato `0x5B` select the second ID when no
effect is active. This distinction excludes table members such as Naruto
`0x72` and Sai `0x62` whose native entry is not the condition-driven path.

Before evaluating any of those controller conditions, `FUN_0020e280` reads the
controller-gate pointer at `0x00607834`. A zero state byte at gate `+0x10` is
normalized to `-1`; while the signed state has any other value, an existing
nonzero `+0x63` bit `0x20` is cleared. The bootstrap therefore identifies the
configured effect's exact clean-start route from those two native tables. For
one of the 38 condition-driven pairs it waits until the gate is absent or its
state is `0`/`0xFF`, then calls `FUN_0020d910`; effects owned by the other native
routes continue through the raw high-level effect entry.

The implementation deliberately leaves starting HP to the independently
verified native Practice enum described above. It uses neither savestates nor
input recordings at runtime; those artifacts are evidence and regression
inputs only.

Candidate validation replayed the same eight-marker recording against two
isolated worker builds. With the test configuration (`p1: 84`, `support: 26`,
`awakening: none`), every marker was already in the live Practice battle;
marker `0001` had manager state `4`, substate `3`, both configured current and
match-start identities, live character `84`, HP `0.5`, and active effect
`0xFFFF`. A second diagnostic build directly encoded raw effect `0x22` and
reached the same state with `Reg.` active at marker `0001`. Later marker effects
followed the recording's gameplay inputs rather than being forced back to
`0x22`, confirming that the bootstrap applies only the initial active state.
That diagnostic established the native application path. The character-aware
configuration accepts Tsunade's `0x22`, chained `0x23`, and controller-owned
`0x57` from their confirmed native sources.

The generalized controller route was replayed independently with Player 1
Rock Lee (`67`) and configured effect `0x44`. In retained capture
`work/QoL/captures/bootstrap/controller-awakening-generalized-v1`, marker
`0001` was in live Practice manager state/substate `4/3`, the fighter's sole
effect was `0x44`, fighter `+0x8E8` was `0x44`, and fighter `+0x63` had native
awakened bit `0x20` set. Later recording inputs removed and reapplied the effect
without the bootstrap forcing it back, preserving one-shot behavior. This
confirms the `FUN_0020d910` route on a non-Tsunade condition-driven character.

## Ultimate Jutsu input-contest controller

The clean NA2 `BTL.BIN`, SHA-256
`56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`,
contains the battle-side controller for the Ultimate Jutsu input contest. Its
file header loads the complete file at runtime base `0x006B3F00`; the preserved
Ghidra export maps file offset `0x40` to that base, so its displayed addresses
are `0x40` below the live addresses.

The visible contest interface is owned by the resident Ultimate Jutsu factory,
not by a BTL draw function. In state `1`, BTL sign-extends the selected contest
type into `t0` and calls resident `FUN_0035CF00`. That routine forwards the type
through `FUN_0036C120` to `FUN_0036B6D0`: type `1` randomizes among contest
implementations, types `2` through `6` allocate their respective contest
objects, and type `0` matches no allocation branch. With type `0`, the meter,
prompts, and result-message object therefore never exists. NUN6 A35 retains the
same disabled-type path in homologs `FUN_00369200`, `FUN_003789B0`, and
`FUN_00377F20`. The NA2 port replaces the final sign extension at clean BTL
file offset `0xB61F8`, exported `0x0076A0B8` and live `0x0076A0F8`, with a zero
value for `t0`.

Input handling is independent of interface-object creation. In contest state
`1`, the controller calls resident press-state accessor `FUN_001D99B0(1, 0)` at
exported `0x00769F54` to latch a press into inner field `+0x3A`, then calls the
same accessor at exported `0x0076A1B0` while waiting for release. These are live
addresses `0x00769F94` and `0x0076A1F0`, at clean BTL file offsets `0xB6094`
and `0xB62F0`. Returning zero at both call sites blocks the recorded input
without changing the rest of the controller state machine.

The wrapper's flags byte at `+0x10` only gates its auxiliary inner-object
pointers. Setting both bits did not change the visible contest interface. An
early return at BTL file offset `0x17E0` also had no effect because that xcombo
renderer belongs to the command-list interface, and returning from the
controller render entry at `0xB69E0` likewise left the contest interface
visible. These replayed negatives exclude all three as owners of this UI.

In the development `uj` replay, checkpoints `0004` and `0005` loaded bytes
`21100000`, `21400000`, and `21100000` at the three live patch addresses. The
active wrapper at `0x00E4C770` referenced inner object `0x00E9C470`; its input
latch `+0x3A` remained zero at both checkpoints. Screenshots `0003` through
`0005` contain no bottom meter or prompts, and `0006` through `0007` contain no
contest result messages. The ordinary top battle HUD remains visible.

## Support field-call and gauge paths

NUN5 and NUN6 expose one exact difference at exported BTL text address
`0x00791858`: NUN5 calls a candidate helper with instruction bytes `54491E0C`,
while NUN6 replaces that call with a NOP. NA2's structural homolog is BTL file
offset `0xC5A5C`, guarded by clean bytes `54E91D0C` and exported at
`0x0077991C`. A first candidate routed that NA2 call to a zero-returning helper.
The `supports2.p2m2` replay still showed Sai in the field at marker `0004`,
proving that this seam does not consume the recorded manual support call.

A second candidate intercepted the adjacent BTL call at file offset `0xC5E64`,
guarded by clean instruction bytes `20E81D0C` and exported at `0x00779D24`.
Static inspection had incorrectly classified its combat-object flags as live
pad masks. The replay again showed Sai in the field at marker `0004`, proving
that this call is also outside the recorded manual support path.

The main executable's `FUN_00238340` is the per-fighter support-button handler.
It checks the native side/mode-dependent `0x20000000` or `0x40000000` input bit,
requires at least half of the support gauge in the normal support mode, and,
when the native battle-state checks accept the request, clears linked-fighter
state byte `+0xB58`. Its only caller is the fighter update's direct call at
runtime `0x0024DCA4`, ELF file offset `0x14DDA4`, guarded by clean instruction
bytes `D0E0080C`. The accepted hook replaces that sole call with a no-op,
leaving selected support data and the separate linked-Jutsu path untouched.

The lower horizontal support bar is drawn by NA2's dedicated `TEX_xgauge`
routine at BTL file offset `0x68BF0`. Its side-dependent X positions are `120.0`
and `392.0`, with Y based at `340.0`. Its caller first updates the gauge
controller, reads state byte `+0x0A`, and makes one direct draw call when that
state is nonzero. The call is at BTL file offset `0x69398`, guarded by clean
instruction bytes `BC721C0C`; the exported Ghidra text address is `0x0071D258`.
Replacing that call with a no-op suppresses the gauge for both players without
altering any other HUD draw.

The `supports2.p2m2` clean baseline records both paths: marker `0001` shows the
gauge for Player 1's selected support while Player 2's No Support side has none;
markers `0002` and `0003` use the selected support in a linked Jutsu; marker
`0004` calls the support into the field. In the third isolated worker replay,
marker `0001` had no support gauge, markers `0002` and `0003` retained Sai in
the linked Jutsu, and marker `0004` contained only Naruto and Kakashi. The user
accepted this runtime behavior on 2026-08-15.

## Character durability and effective base HP

The game does not store a different full-gauge HP value per character. Current
HP is a normalized `float32` at fighter `+0x6C`; full health is `1.0`.
`FUN_00225050` subtracts normalized damage from this field and clamps it at
zero. Fighter construction initializes health through `FUN_00224d10` from the
battle-instance initialization value, which was `1.0` for Naruto and Sakura in
the two Practice captures.

Per-character durability is instead stored in the static character record at
record `+0xC0`. `FUN_002151e0` copies it to fighter `+0x14C` (record word
`0x30`). `FUN_00224e30` reads fighter `+0x14C` when damage flags include bit
`0x2` and converts the clamped durability parameter `d` to an incoming-damage
multiplier `m`:

```text
d = clamp(d, 0.0, 3.0)
m = 2.0 - d                                      when d < 1.5
m = 0.5 - ((d - 1.5) / 1.5) * 0.2              otherwise
```

The `default_hp` column in
[`na228_builder/resources/character_data.tsv`](../../../na228_builder/resources/character_data.tsv) expresses
neutral effective base HP as `100 / m`. This isolates the static durability
parameter; attacker offense and temporary battle-state multipliers are
separate factors in `FUN_00224e30`. The default-HP values are derived balance
values, not literal full-gauge values stored in fighter memory.

The executable has an ID-indexed record-pointer table at EE `0x005A2904`, with
eight bytes per ID. Each first word points to the static character record.
For example, ID 57 points to Naruto's record at `0x004DAD80`, whose durability
parameter is `0.90`; ID 58 points to Sakura's record at `0x004E01B0`, whose
parameter is `0.80`. Naruto therefore has `90.909091` neutral effective HP and
Sakura has `83.333333` on the same scale.

Evidence was extracted from clean `SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`, and
checked against the copied fighter records in both immutable Practice
captures. Record addresses in the resource table are EE virtual addresses.

Record `+0xD4`, copied to fighter `+0x160`, is not base HP. It scales healing
amounts in `FUN_00224df0` and the recovery branch of `FUN_002369d0`. Naruto's
value is `1.0`; Sakura's is `1.1`.

### Confirmed character-record fields

`FUN_002151e0` copies 55 four-byte words from the selected static character
record, record `+0x00..+0xD8`, to fighter `+0x8C..+0x164`. The following copied
fields have confirmed battle consumers:

| Record | Fighter | Confirmed role | Consumer |
| ---: | ---: | --- | --- |
| `+0x00` | `+0x8C`, then `+0x68` | Character ID | `FUN_002151e0` |
| `+0xBC` | `+0x148` | Attacker offense multiplier | `FUN_00224e30`, damage flag `0x1` |
| `+0xC0` | `+0x14C` | Static durability parameter used to derive Default HP | `FUN_00224e30`, damage flag `0x2` |
| `+0xD4` | `+0x160` | Health-recovery multiplier | `FUN_00224df0`, `FUN_002369d0` |
| `+0xD8` | `+0x164` | Chakra-recovery multiplier | `FUN_002369d0` into `FUN_002254a0` |

`FUN_002254a0` is confirmed as chakra addition because it adds to fighter
`+0x70` and caps the value at `15.0`. The `+0x164` recovery path multiplies the
base event amount by the character field and the temporary-effect accumulator
from `FUN_00307230` before calling that chakra-adder.

Naruto and Sakura demonstrate that these are independent balance parameters:

| Character | Offense `+0x148` | Durability `+0x14C` | Health recovery `+0x160` | Chakra recovery `+0x164` | Default HP |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naruto (ID 57) | `1.1` | `0.9` | `1.0` | `1.2` | `90.909091` |
| Sakura (ID 58) | `1.2` | `0.8` | `1.1` | `1.1` | `83.333333` |

The character-instance holder is separate from the static record. Holder
`+0x00` points to the record; holder `+0x1C` supplies initial normalized HP and
holder `+0x20` supplies initial chakra to `FUN_002151e0`. In both Practice
captures those instance values were `1.0` HP and `15.0` chakra for Naruto and
Sakura, confirming that their default durability difference is applied during
damage rather than during full-health initialization.

The remaining copied record fields are character-specific data but are not yet
semantically identified. They must not be assigned gameplay names until a
consumer proves each role.

## Unresolved extra-hit branch lead

A historical one-branch candidate exists at EE `0x20241F40`, labelled “extra
hit.” Its instruction change remains recoverable from Git history, but the
label and runtime effect are unproven and must not be conflated with the
accepted `ELF-B002` battle-logic patch.

## Unresolved Ultimate-Jutsu chakra leads

Historical notes point to ELF file `0x1492B0` for level-scaled chakra
subtraction and `FUN_002254a0` for shared chakra addition. Recheck the preserved
disassembly before assigning either role or designing a patch.
