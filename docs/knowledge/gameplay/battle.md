# Battle behavior knowledge

This document owns unresolved and established leads about battle behavior that
do not belong to a narrower gameplay subsystem.

## Research coverage

- **Assigned scope:** this task determines how accepted combo hits reach the
  native damage calculator, which native state supplies the hit index, whether
  configurable per-hit scaling can be inserted without replacing combo
  bookkeeping, and what deterministic input evidence is needed to implement
  and validate it. The primary reproduction is `damage_scaling.p2m2` with
  Sakura in Practice row 9.
- **Exploration depth:** within the exact clean NA2.28 executable
  and this reproduction, the investigation statically classified every one of
  the ten clean calls to `FUN_00224e30`, traced the native combo owner,
  pending-hit producer/consumer, timer/reset behavior, and response/contact
  branch, and audited all 24 clean stage archives for the relevant collision
  flag.
- **Confirmed coverage:** runtime work replayed all 13 checkpoints with an all-caller logger, a
  focused call-boundary probe, an unmodified-behavior control, the proposed
  `0.10`-decay/`0.30`-floor curve, and an `S08` stage control. It confirms the
  active main and secondary `.02` call paths, the
  `max(1, current + max(pending, 0))` hit index, hits one through five and
  native reset, preservation of native combo fields, scaled HP and HUD
  consumption, and the complete 3,620-record controller stream. The static
  `.04` contact path and its post-damage callback are structurally mapped, and
  `S08` is confirmed as the only clean stage containing authored environment
  triangles with the required `0x400` flag.
- **Unresolved or untested:** no natural runtime event has yet entered the
  `.04` contact call at `0x00231634`; the `S08` control proves the resource is
  present but the existing side-0 movie never reaches its upper/side-1 flagged
  geometry or qualifying response states. The five-hit recording does not
  exercise the eight-hit `0.30` floor boundary. Coverage is also still open for
  other characters, guard outcomes, throws, projectiles, specials, linked or
  support attacks, transformations, and any caller dormant in this movie.
- **Deliberate exclusions and overlap:** this research does not implement the
  production builder/configuration feature, invent a replacement combo timer,
  alter collision or stage data, or activate the separate dormant character
  `damage_multiplier` proposal. Practice bootstrap, starting HP, awakening,
  support, status, and other battle sections in this shared document are prior
  or parallel scopes and were not re-investigated for damage scaling.
- **Evidence limitations:** static conclusions use the read-only clean
  `SLPS_258.37` export and executable with SHA-256
  `20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`;
  there is no original game source. Runtime conclusions are bounded to the
  verified Manual cache, the exact Practice PNACH/bootstrap, and the named
  movie and transient probes. Captured heap addresses are allocation-specific,
  marker snapshots observe selected frames rather than every intermediate
  state, and static reachability alone is not evidence that an unobserved
  caller executes in ordinary play.

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
stage, calls `FUN_002005b0(1, 0)`, and enters state `10`. The NA2.28 PNACH leaves
the clean state-`7` call at runtime `0x001ECA2C` intact and replaces its
`FUN_001ed450` callee instead. That wrapper writes the current and match-start
identity fields, fixes the opponent and stage, sets the native three-frame
countdown, calls `FUN_002005b0(1, 0)`, and enters state `10`. States `10`
through `15` remain native, including both fighters' construction and stage
loading.

Read-only call-reference inspection establishes that clean `FUN_001ed450` is
owned only by this Practice state-`7` path. It begins at `0x001ED450`; the next
native function begins at `0x001ED6C0`, leaving `0x270` bytes for a transport
that intentionally bypasses Character Select. The PNACH uses a contiguous
selection/battle wrapper through `0x001ED5F8`, mutable one-shot state at
`0x001ED5FC`, and three configuration slots at `0x001ED600..0x001ED608`
supplied only by process-local inline PNACH lines. It
patches the clean state-`15` call at `0x001ECACC` from `FUN_001edb70` to the
battle wrapper at `0x001ED4CC`; that wrapper calls `FUN_001edb70` first. No
write reaches the next native function.

`@repository/launch_profiles/practice/NA228.pnach` owns the complete NA2.28 bootstrap,
while `@repository/launch_profiles/practice/NUN5.pnach` owns its separately ported startup and bootstrap
code at `0x003D0C60..0x003D0FF8`. The normal
`-l practice <case-id>` launch-profile selector maps `practice` to
`@repository/launch_profiles/practice/`, resolves one stable `case_id`
case-insensitively from `movesets.tsv`, and passes a different three-line
character/support/awakening address set to each selected game. A `-rev` case
adds the native half-HP initializer write as a fourth line:
`0x001E7AE8 = 0xA0850001` for
NA228 or `0x001ED8D8 = 0xA0850001` for NUN5. It neither rewrites a profile nor
creates a generated PNACH. Clean NA2 is not a supported launcher target.

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

Character-specific runtime application is another source. Naruto's callback
table at runtime `0x004D56D0` contains `FUN_00299100` at `+0x04`. When Naruto's
HP field at fighter `+0x6C` is at or below `0.15`, effect `0x39` is absent, the
fighter is eligible, and the active mode permits it, that callback applies
`0x39` through `FUN_00305c30`. This direct low-HP path is separate from Naruto's
Ultimate-Jutsu-only `0x72` transformation, so both IDs are compatible active
states for Naruto.

There is no exhaustive native `character -> possible active effects` table.
The `character_data.tsv` `awakening_ids` column records the useful test-matrix
union: the
controller-table IDs, every non-`0xFFFF` effect in that character's
Ultimate-Jutsu records, hard-coded effects applied when transformed forms are
constructed directly, character-specific direct applications, and the sole
hard-coded successor `0x23`. It declares character compatibility, not how an
effect is normally entered.
`FUN_003047c0` classifies the broader native effect domain `0..0x89`, but that
global range does not establish character compatibility. The Practice profile
passes the selected Practice `movesets.tsv` case's awakening through unchanged,
using `none` for no starting awakening. It does not read the character table or
expand cases; the fixed moveset matrix owns the character-specific
combinations.

`FUN_00305c30(fighter, effect_id, -1, 1)` is the native high-level effect
entry: it validates the effect category, resolves the default parameter,
constructs the effect through `FUN_00305270`, performs native side effects,
and writes the active effect ID to fighter `+0x8E8`. The PNACH replacement at
runtime `0x001ECACC` (ELF `0xECBCC`) calls a wrapper that retains
`FUN_001edb70`, then applies one configured awakening after the Player 1 fighter
exists. It retries until `+0x8E8` confirms the requested ID and resets its
one-shot state whenever a new bootstrap reaches controller state `7`.

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
association lists identifies 38 clean-start character/effect pairs that reach
`FUN_0020d910` naturally. Most select the association list's first ID. Hinata
`0x50`, Shizune `0x55`, Kurenai `0x57`, and Yamato `0x5B` select the second ID
when no effect is active. This native selection logic does not cover direct
effects such as Naruto `0x39`, and it cannot accept an exact arbitrary ID.

The bootstrap therefore does not use the trigger flags or association table as
a route classifier. After the controller gate at `0x00607834` is absent or has
state `0`/`0xFF`, it preserves the register frame expected by
`FUN_0020d910`, places the fighter and configured effect ID in that function's
native `s2` and `s1` inputs, runs its battle-mode guard `FUN_001fe200`, and
enters the shared transition tail at `0x0020DC40`. That tail calls
`FUN_00305c30` with the exact configured ID, sets fighter `+0x63` bit `0x20`,
and performs the native transition sequence before returning through the
original epilogue at `0x0020DCF8`. Consequently every non-`none` value supplied
as an awakening, including Naruto `0x39`, reaches the complete transition;
there is no raw-effect branch. NUN5 uses the homologous mode guard
`FUN_00204ed0`, transition tail `0x00214CCC`, and epilogue `0x00214DE0`.

Three characters have native work before that shared tail. Deidara `0x41` uses
the complete `FUN_0020d910` entry, and NUN5 uses `FUN_002149e0`, retaining its
character-specific prefix. Taijutsu Chiyo starts with constructor-owned effect
`0x4D`, while her controller association is the sole effect `0x4E`. Her
ordinary-move slots are switched independently by `FUN_002d81b0(fighter, 1)`,
or NUN5 `FUN_002e22f0(fighter, 1)`. The full native entry then removes `0x4D`
through `FUN_00305510`, or NUN5 `FUN_0030fda0`, before applying `0x4E`.
Entering either the shared tail directly or the full native entry without the
moveset helper leaves her base ordinary moves. Both clean boot ELFs encode the
same `0x4E` association at character-table entry `77`: NA2 runtime
`0x005C1F98` / file `0x4C2098`, and NUN5 runtime `0x005C9418` / file
`0x4C9598`.

Gaara's regular `0x3B` additionally requires
`FUN_0029c1e0(fighter, 1)`, or NUN5 `FUN_002a5910(fighter, 1)`, which switches
his ordinary-move slots and model state independently of the active effect.
The process-local Gaara override calls that helper, reconstructs the native
awakening frame, and then enters the same exact-effect transition tail. Focused
NUN5 and NA228 replays both showed `Sand Attack: Crush Burial`, `Sand Attack:
Ruin Burial`, `Sand Attack: Heaven Burial`, and `Fierce Sand Downpour` in place
of the base ordinary moves, plus `Destructive Sand Burial` as the Ultimate
Jutsu. That override does not yet reproduce the native prefix's fighter
`+0x63` bit `0x10` write or its external activation call, so the ordinary
moveset is runtime-confirmed while complete native semantic parity remains
unverified.

Gaara's item awakening is effect `0x3C`. His runtime callback tests it
separately from regular `0x3B`; it does not select the alternate ordinary
moveset. `character_data.tsv` therefore records `0x3B,0x3C` as compatible
active effects, and the moveset matrix records the regular and item cases
separately.

The current 78-row awakening matrix was exhaustively classified against both
games' homologous controller branches. Fifty-nine rows use the ordinary exact
tail. Twelve exact-ID rows bypass prefixes that only select between associated
effects, two Might Guy rows define an initial stage rather than executing the
native already-active stage transition, Taijutsu Chiyo `0x4D` is
constructor-owned, and Gaara `0x3C` is the non-moveset item state. The remaining
three routes are the special cases above: full native entry for Deidara `0x41`,
the Chiyo helper plus full native entry for `0x4E`, and the Gaara helper plus
exact tail for `0x3B`.
Scanning both resident executables' character-specific ordinary-move slot
writers and their callbacks found no further pre-transition helper required by
a configured row. The pre-fix NUN5 capture set covers 77 rows; Gaara `0x3C` is
the sole uncaptured row, and Taijutsu Chiyo `0x4E` is retained as the captured
failure rather than overwritten by this repair. Isolated NUN5 and NA228 replays
after adding Chiyo's helper both showed her alternate ordinary set, beginning
with `Looking Up at the Air`, `Passed Years`, `Falling Bow`, `Cut Off End`, and
`Flying Bird Dance`.

The implementation deliberately leaves starting HP to the independently
verified native Practice enum described above. It uses neither savestates nor
input recordings at runtime; those artifacts are evidence and regression
inputs only.

The earlier resident-C candidate was validated by replaying the same
eight-marker recording against two isolated worker builds. With Player 1 `84`,
support `26`, and no starting awakening, every marker was already in the live
Practice battle;
marker `0001` had manager state `4`, substate `3`, both configured current and
match-start identities, live character `84`, HP `0.5`, and active effect
`0xFFFF`. A second diagnostic build directly encoded raw effect `0x22` and
reached the same state with `Reg.` active at marker `0001`. Later marker effects
followed the recording's gameplay inputs rather than being forced back to
`0x22`, confirming that the bootstrap applies only the initial active state.
That diagnostic established the native application path for Tsunade's `0x22`,
chained `0x23`, and controller-owned `0x57`.

The earlier generalized controller route was replayed independently with Player 1
Rock Lee (`67`) and configured effect `0x44`. In retained capture
`@work/QoL/captures/bootstrap/controller-awakening-generalized-v1`, marker
`0001` was in live Practice manager state/substate `4/3`, the fighter's sole
effect was `0x44`, fighter `+0x8E8` was `0x44`, and fighter `+0x63` had native
awakened bit `0x20` set. Later recording inputs removed and reapplied the effect
without the bootstrap forcing it back, preserving one-shot behavior. This
confirms the shared `FUN_0020d910` transition tail on a non-Tsunade
condition-driven character. The current exact-ID PNACH route has static
verification of both games' clean tail and epilogue instructions, branch and
absolute-jump targets, configuration slots, register-frame contract, and the
`FUN_001ed450` ownership boundary. Runtime confirmation of the generalized
exact-ID entry remains pending.

## Ultimate Jutsu input-contest controller

The clean NA2 `BTL.BIN`, SHA-256
`56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`,
contains the battle-side controller for the Ultimate Jutsu input contest. Its
file header loads the complete file at runtime base `0x006B3F00`; the preserved
Ghidra export maps file offset `0x40` to that base, so its displayed addresses
are `0x40` below the live addresses.

The contest object is owned by the resident Ultimate Jutsu factory, not by a
BTL draw function. In state `1`, BTL sign-extends the selected contest type
into `t0` and calls resident `FUN_0035CF00`. That routine forwards the type
through `FUN_0036C120` to `FUN_0036B6D0`: type `1` randomizes among contest
implementations, types `2` through `6` allocate their respective contest
objects, and type `0` matches no allocation branch. NUN6 retains the same
disabled-type path in homologs `FUN_00369200`, `FUN_003789B0`, and
`FUN_00377F20`.

Type `0` is not a presentation-only mode. With no object at resident global
`0x00607750`, the main manager cannot invoke either the object's update
dispatcher `FUN_0036BF10` or its render dispatcher `FUN_0036BFF0`. The earlier
patch forced type `0` at clean BTL file offset `0xB61F8`, exported
`0x0076A0B8` and live `0x0076A0F8`. The user later established that enabling
that patch prevented post-Ultimate-Jutsu awakening. Static analysis proves
that the patch removed the shared update/lifecycle object, although it does not
isolate which individual omitted lifecycle field causes the awakening failure.

The main manager calls `FUN_0036BF10` under its update mask and
`FUN_0036BFF0` under its render mask. `FUN_0036BFF0` dispatches vtable slot
`+0x0C` for every allocated contest type, and each type's slot is its meter,
prompt, and result renderer. Its sole direct caller is at resident address
`0x001F0940`, clean ELF file offset `0xF0A40`, with instruction bytes
`FCAF0D0C`. The accepted correction replaces only that call with a
NOP. Native contest allocation and `FUN_0036BF10` updates therefore remain in
the execution path while the common contest render dispatch is skipped.

Input handling is independent of interface-object creation. In contest state
`1`, the controller calls resident press-state accessor `FUN_001D99B0(1, 0)` at
exported `0x00769F54` to latch a press into inner field `+0x3A`, then calls the
same accessor at exported `0x0076A1B0` while waiting for release. These are live
addresses `0x00769F94` and `0x0076A1F0`, at clean BTL file offsets `0xB6094`
and `0xB62F0`. Returning zero at both call sites blocks the contest input path
without changing the rest of the controller state machine.

The resident accessor contains two three-byte input-state banks: its first
argument selects bank `0` or `1`, and its second indexes slot `0` through `2`.
Both contest calls use bank `1`, slot `0`. That static slice does not establish
how the contest maps physical controllers onto the logical slot. Runtime
observation after acceptance confirmed that neither Player 1 nor Player 2 input
affects the contest, establishing the both-player behavior while the exact
logical-slot routing remains untraced.

The wrapper's flags byte at `+0x10` only gates its auxiliary inner-object
pointers. Setting both bits did not change the visible contest interface. An
early return at BTL file offset `0x17E0` also had no effect because that xcombo
renderer belongs to the command-list interface, and returning from the
controller render entry at `0xB69E0` likewise left the contest interface
visible. These replayed negatives exclude all three as owners of this UI.

In the earlier development `uj` replay, checkpoints `0004` and `0005` loaded
bytes `21100000`, `21400000`, and `21100000` at the three former live patch
addresses. The active BTL wrapper at `0x00E4C770` referenced inner object
`0x00E9C470`; its input latch `+0x3A` remained zero at both checkpoints.
Screenshots `0003` through `0005` contained no bottom meter or prompts, and
`0006` through `0007` contained no contest result messages. That replay did
not exercise post-UJ awakening and therefore did not validate the removed
resident contest-object lifecycle. User runtime testing of the render-only
correction on 2026-08-21 confirmed that post-UJ awakening occurs, the meter,
prompts, and result messages remain invisible, and both players' inputs remain
blocked.

### Native complete-HUD transition

The retained contest object pointer at resident global `0x00607750` also gives
the complete battle HUD a stable Ultimate-Jutsu lifecycle signal. The accepted
Battle Logic hook at BTL file offset `0x67030` edge-detects that pointer around
the displaced common battlegauge update prologue. On a null-to-non-null edge it
calls resident `0x001F1820(-1)`; on the matching non-null-to-null edge it calls
resident `0x001F1A20(-1)`.

These are the native all-HUD hide and show requests used by ordinary Jutsu.
Consequently the Ultimate-Jutsu path inherits the same HUD translation, timing,
visibility gates, and restoration instead of directly suppressing individual
renderers. Children injected into the battle-HUD hierarchy, including the
independent substitution bar, follow that native transition without a separate
Ultimate-Jutsu condition.

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

The native support-bar draw also chooses its displayed controller button from
the action map. `FUN_0071CAF0` calls `FUN_001F3F10(side + 1)` at live
`0x0071D03C`, then executes `lh a0,0xA(v0)` at live `0x0071D044` / BTL raw
`0x69184`. The clean instruction bytes are `0A004484`; offset `+0x0A` selects
action index `5`, Linked Attack, independently for each player. The current
unaccepted substitution-gauge candidate leaves this entire renderer and all of
its X/Y constants clean. `features.settings.shared.support` independently
suppresses only its outer call at raw `0x69398`.

The first independent-renderer candidate hooked the preceding controller-update
call at raw `0x69380`, called the displaced update once, and drew from that
callback. User runtime testing on 2026-08-27 established that this lifecycle is
not the top-HUD lifecycle: the substitution bar remained visible while ordinary
Jutsu hid HP/chakra, then disappeared while Ultimate Jutsu retained the ordinary
top HUD. The current candidate therefore keeps `0x69380` only as a per-side
cache/update seam for the controller's initialized bar sprite at `+0x18` and
BTL `$gp`.

The actual per-side top-HUD dispatcher starts at BTL raw `0x673E0`, exported
`FUN_0071B2A0` and live `0x0071B2E0`. It reads parent byte `+0x54` at raw
`0x673F4` and skips all four child draws when that state equals `1`. After that
gate, it loads the primary child from parent `+0x20`; when non-null, raw
`0x67434` calls live `0x0071B720` with clean bytes `C86D1C0C`. The child's
layout pointer is at `+0x00`, and layout byte `+0x0C` is the same side/mirroring
value consumed throughout the primary renderer. That renderer loads live layout
X, Y, and scale from `+0x00`, `+0x04`, and `+0x08`. The name renderer at raw
`0x67F20` consumes the same four layout fields, establishing that the slide and
Ultimate-Jutsu shake are shared parent transforms rather than component-local
state.

The first parent-gated candidate selected the right visibility states but still
drew at fixed screen coordinates. User runtime testing on 2026-08-27 reported
that it did not follow HP/chakra/name as they moved upward off-screen and did
not receive the Ultimate-Jutsu shake. The current wrapper replaces only the
same `jal`, calls the displaced native renderer once, then selects the cached
controller for that accepted HUD side. It derives its base from layout origin
plus mirrored X offset `64.0` and Y offset `38.0`, scales every bar geometry
offset and dimension by layout `+0x08`, and copies primary child sprite alpha
`+0x40` for the draw. Thus visibility, translation, shake, scale, and alpha are
inherited from the common native HUD state rather than duplicated Jutsu or
animation tests.

The independent renderer uses the same outer-frame, marker, and inner-bar
rectangle records that the native support renderer addresses as BTL
`$gp - 0x5CD8`, `$gp - 0x5CD0`, and `$gp - 0x5CC0`, but owns its geometry and
state. The two bar anchors are `64.0/448.0` with shared Y `38.0`; no native
support-controller fill, visibility, button, or decoration state is
repurposed. Runtime confirmation of the corrected slide-off and Ultimate-Jutsu
shake remains pending.

The Battle HUD name renderer at raw `0x67F20` resolves its X anchor before
loading the shared Y anchor through raw `0x67F60..0x67F67`
(`8C00023CDC4240C4`). The substitution feature leaves the complete X path and
the Y load untouched. Its only name-position hook is the immediately following
raw `0x67F68..0x67F6F` pair (`820001460C00A290`): native Y-scale
multiplication followed by the side-byte load. The resident adapter receives
the already loaded Y, preserves the live name destination, layout pointer,
scale, width/height results, and anchor result, and calls a C adjuster. Chakra
and Free return the loaded Y unchanged; Gauge returns `Y + 11.0`. The adapter
then reproduces the displaced multiplication and side-byte load before
rejoining the native branch. The substitution feature therefore owns no X
coordinate, no absolute Y coordinate, and no localization dependency. Runtime
confirmation of the relative-Y path remains pending.

The red marker in the same native draw is not a stock boundary. The clean code
loads `52.0` at live `0x0071CFA0`, while the fill begins at `20.0` and spans
`64.0`; its fixed normalized position is therefore `(52 - 20) / 64 = 0.5`.
The marker's native draw call is live `0x0071CFD0`, BTL raw `0x69110`, guarded
by clean bytes `10EF0D0C` (`jal 0x0037BC40`). The candidate leaves it clean and
uses the native scaled sibling at `0x0037BD00` so the independent marker follows
the common top-HUD scale. Marker X is
`base + mirror * scale * (20 + 64 * executable_cost_fraction)`. The fraction is
published per side from the same rounded meter-count cost used by eligibility
and spending, so the marker describes the actual amount required rather than
an independently rounded configuration value.

The native lower-support marker loads its tint from resident `0x0040BFC8`.
Clean `SLPS_258.37` bytes there are `12 00 00 00 FF FF FF FF`; the native
packing sequence at live `0x0071CF60..0x0071CF9C` resolves that to RGB
`(0x12, 0x00, 0x00)`. Reusing that very dark tint on the independent top-HUD
bar made its cost threshold appear black in user runtime testing. The current
candidate keeps the native marker texture but supplies normal-intensity red
RGB `(0x7F, 0x00, 0x00)` for the independent draw only. The native lower
support renderer and its tint remain unchanged.

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
m = 2.0 - d                                      when d < 1.0
m = 1.0 - ((d - 1.0) / 0.5) * 0.5              when 1.0 <= d < 1.5
m = 0.5 - ((d - 1.5) / 1.5) * 0.2              when d >= 1.5
```

The `default_hp` column in
[`@resources/character_data.tsv`](../../../resources/character_data.tsv) expresses
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

## Combo hit state and damage path

The deterministic movie
[`damage_scaling.p2m2`](../../../pcsx2_files/input_recordings/damage_scaling.p2m2),
SHA-256
`CAE410908B7D9CAFDFFC63178C5F1EACDD57D0565DD285EE15740C6CAF6C85A5`,
declares 3,619 input frames. Its 3,620 serialized 36-byte controller records
include the format's frame-0 placeholder; excluding that placeholder, there are
13 actionable rising edges of the `L3+R3` marker chord. It was created from
power-on with PCSX2 `v2.7.505-41-g667f9e2e0` and zero re-records. The exact
launch provenance recovered from the local shell history was Manual ISO
selector `m`, Practice row `9`, recording `damage_scaling`, and the update
flag, exactly `na m -c practice 9 -r damage_scaling -u`. Practice row 9 selects
Sakura (ID `58`), No Support (`0x25`), and no awakening for Player 1 through:

```text
patch=1,EE,001ED600,word,0000003A
patch=1,EE,001ED604,word,00000025
patch=1,EE,001ED608,word,FFFFFFFF
```

Two negative replays used built-ISO caches
`3A56428FA33E28F627941875ACC4E8097D292464A04DE3FF6A1868CF2CEC2170` and
`DDF776B7DF5A603B7A9DBA72556AAEFE073FB1BA313C01A1ABE62B3B06F77F63`;
both desynchronized into Mode Select. The immediate cause was not inferred
from their current JSON. All 13 states in each failed run retained native bytes
`0C0004AE2900001000000000` at `0x001E9B00` and
`DCB6070C00000000` at `0x001ECACC`; their `0x001ED600` region was native code,
not configured fighter data. All 13 synchronized states instead contained the
Practice bootstrap bytes `03000224290000100C0002AE` and
`33B5070C00000000` at those locations, plus words
`0000003A,00000025,FFFFFFFF` at `0x001ED600`. The failed launches therefore
did not have the recording's required Practice bootstrap/configuration active,
so reaching ordinary Mode Select was expected.

The cached ISOs were also not byte-identical just because the configuration
files looked equivalent later. The Manual and E2E-Test ISOs have the same boot
ELF hash but different `PRG/BTL.BIN` hashes; their build registries record
different build-time localization-input hashes. The Latest ISO additionally
has different boot ELF, `PRG/BTL.BIN`, `PRG/ETC.BIN`, and `PRG/228.BIN`
hashes. That historical binary drift is a separate reproducibility issue; the
missing runtime Practice patch above is the first proven cause of the shared
Mode Select outcome.

The synchronized replay used the immutable Manual cache whose ISO SHA-256 is
`4773DEFAB12C7926980D8D6B7D6505BF5021FE105A5BD411ECFEA6EFA366A5CD`,
`@repository/launch_profiles/practice/NA228.pnach`, read-only emulator settings, and
discarded memory-card writes.

The marker chord is not an input sequencer. Every attack input already exists
in the movie's per-frame controller stream; markers only identify deterministic
frames at which the replay workflow saves a screenshot and state. They are
therefore unnecessary to execute the combo, but materially reduce ambiguity
when correlating a visual hit with memory before and after native updates.

The project's PCSX2 fork can also drive controller input through PINE protocol
version 1. Its agent-control `step` operation atomically installs complete
18-byte DualShock 2 states and advances an exact positive frame count, so a
client can stream an attack sequence as successive state/frame runs. PINE does
not provide one command that accepts an entire authored timeline, and an
English move description still has to be translated into exact presses,
releases, and frame durations. For this investigation, replaying the existing
movie is more reliable because those per-frame states are already serialized;
PINE is appropriate for constructing new isolated cases interactively.

A complete byte-level audit confirms what is available without markers. The
570-byte movie prefix contains format version `1`, emulator
`PCSX2-v2.7.505-41-g667f9e2e0`, game `SLOP-NA228 [?]`, 3,619 declared frames,
zero re-records, and a power-on rather than savestate start. The remaining
130,320 bytes divide exactly into 3,620 records of 36 bytes: one 18-byte state
for each of two controller ports. Record zero is the all-zero placeholder.
Across records 1 through 3,619, Controller 2 is always neutral, Controller 1's
four analog bytes are always centered at `0x7F`, and every pressure-capable
digital press has the matching `0xFF` pressure byte. The actionable input is
therefore reproduced exactly by the following independent inclusive frame
runs; all buttons not named for a frame are released and all unlisted frames
are neutral except for overlaps among the listed runs:

| Control | Inclusive movie-frame runs |
| --- | --- |
| `L3+R3` marker chord | `2673-2680`, `2802-2809`, `2813-2816`, `2828-2833`, `2929-2936`, `2939-2948`, `2950-2953`, `2987-2990`, `3061-3066`, `3171-3176`, `3207-3210`, `3249-3256`, `3502-3506` |
| `Circle` attack | `2751-2757`, `2766-2770`, `2776-2783`, `2789-2792`, `2803-2808`, `2814-2818`, `2827-2831`, `2841-2850`, `2942-2947`, `2955-2967`, `2972-2979`, `2983-2987`, `3025-3028`, `3149-3157`, `3193-3201`, `3239-3245`, `3268-3274` |
| `Cross` | `3461-3466`, `3471-3477`, `3480-3488` |
| `Right` | `2692-2734`, `2770-2866`, `2892-2924`, `3084-3095`, `3117-3124`, `3351-3362`, `3375-3413` |
| `Down` | `2922-3023` |
| `Left` | `3309-3352`, `3362-3376` |

This independent-run form deliberately preserves simultaneous inputs: for
example, the five frames where `Left` and `Right` overlap and the marker/attack
overlaps are not normalized away. Recombining the active controls at every
change boundary yields the movie's exact 18-byte Controller 1 stream and can
be sent as consecutive PINE `step` requests. Removing the `L3+R3` runs leaves
the same movement and attacks, so markers are not required for execution. Full
per-frame game-state inspection still requires stepping the emulator and
reading or capturing the desired consumer after each frame; decoding the
movie alone proves the inputs, not every intermediate animation or memory
state.

The synchronized captures are under
`@work/Battle mechanics/captures/damage_scaling/manual-practice-row9/`. Their
screenshots and `eeMemory.bin` state members establish this timeline:

| Marker | Movie frame | Visible result | Naruto HP | Current / record combo | Timer words `+0x14/+0x18/+0x1C` |
| ---: | ---: | --- | ---: | ---: | --- |
| `0001` | 2673 | Baseline | `1.000000000` | `0 / 0` | `0/0/0` |
| `0002` | 2802 | 2 hits, displayed `6.5%` | `0.934000015` | `2 / 0` | `90/88/87` |
| `0003` | 2813 | Same 2-hit result | `0.934000015` | `2 / 0` | `90/82/81` |
| `0004` | 2828 | Same 2-hit result | `0.934000015` | `2 / 0` | `90/75/74` |
| `0005` | 2929 | 3 hits, displayed `15.3%` | `0.846000016` | `3 / 0` | `90/44/43` |
| `0006` | 2939 | Same 3-hit result | `0.846000016` | `3 / 0` | `90/39/38` |
| `0007` | 2950 | Same 3-hit result | `0.846000016` | `3 / 0` | `90/34/33` |
| `0008` | 2987 | 4 hits, displayed `18.0%` | `0.819599986` | `4 / 0` | `90/79/78` |
| `0009` | 3061 | 5 hits, displayed `20.0%` | `0.799799979` | `5 / 0` | `90/64/63` |
| `0010` | 3171 | Fresh 1-hit attack, displayed `2.6%` | `0.973600030` | `1 / 5` | `90/86/85` |
| `0011` | 3207 | Same 1-hit result | `0.973600030` | `1 / 5` | `90/90/89` |
| `0012` | 3249 | Native current-combo reset | `0.973600030` | `0 / 5` | `90/69/68` |
| `0013` | 3502 | Next hit counted before HP subtraction | `1.000000000` | `1 / 5` | `90/84/83` |

The stable root at EE `0x00607600` pointed to `0x00CA4700`. Its live-fighter
pointers were Sakura at `0x00E36CA0` and Naruto at `0x00E44CE0` in every exact
capture. This is capture-specific allocation evidence; consumers must follow
the pointers rather than embed those allocated addresses.

### Native combo owner

`FUN_0020c270(fighter)` allocates a `0x3C`-byte object, initializes it through
`FUN_0020c320`, and stores its pointer at
`0x006076B8 + 4 * (fighter[+0x60] & 1)`. The two globals at `0x006076B8` and
`0x006076BC` therefore own Player 1 and Player 2's native combo state. The
confirmed object fields are:

| Offset | Type | Confirmed behavior |
| ---: | --- | --- |
| `+0x00` | pointer | Owning fighter |
| `+0x04..+0x0C` | pointers | Lazily resolved BTL-side UI/controller objects |
| `+0x10` | timer object | Armed for `0x5A` (90) by each accepted hit |
| `+0x34` | signed 16-bit | Current active hit count |
| `+0x36` | signed 16-bit | Highest completed combo recorded by this object |

Accepted-hit state first accumulates in the attacker's signed byte at fighter
`+0xA45`. `FUN_00239230(fighter, delta)` adds to that byte.
`FUN_002391d0(fighter, result, flag)` adds one only when `result == 1` and the
flag is nonzero; the collision-resolution path `FUN_0021f610` calls it with
the accepted result and flag `1`. `FUN_00233540` is a second confirmed producer
that can add a hit to the opposing fighter's pending byte.

The per-frame manager routine `FUN_0020c420` consumes a nonzero pending byte,
adds its signed value to current count `+0x34`, arms the timer for 90, clears
fighter `+0xA45`, and triggers the native multi-hit notification after the
count exceeds one. When its timer or battle-state conditions end the combo, it
copies a new record to `+0x36` and clears `+0x34`. `FUN_0020c2e0` and
`FUN_0020cd40` can explicitly adjust or set the current count. This native
owner should be read by a scaling hook; duplicating a separate combo-reset
timer would diverge from native hit acceptance and reset behavior.

The pending byte was zero at all marker snapshots because the manager had
already consumed it, but the focused call-boundary probe below observed both
legal orderings. Main attack-record damage ran before manager consumption:
hits one through five saw `(current, pending)` values `(0,1)`, `(1,1)`,
`(2,1)`, `(3,1)`, and `(4,1)`. The third hit's secondary damage ran after
consumption and saw `(3,0)`. Consequently the synchronous one-based index

```text
max(1, current_count + max(pending_count, 0))
```

produces `1, 2, 3, 3, 4, 5`: both damage events belonging to hit three receive
index three without a separate latch or a second increment. Every observed
fresh post-reset call saw `(0,1)` and therefore returned to index one. This
formula is runtime-confirmed for the two paths exercised by this normal string;
other damage categories still need isolated path classification.

### Native damage calculation

Two similar consumers, `FUN_00228b50(defender)` and
`FUN_002346b0(defender)`, resolve an active attack record, read normalized
damage from record `+0x24`, and divide by the signed short at record `+0x2E`
when that field is nonzero. Both combine that value with a temporary attacker
factor from `FUN_003071c0`, select native flags `0x133` or `0x122` from
attack-record bits, call `FUN_00224e30(raw_damage, defender, flags)`, and pass
its returned normalized damage to `FUN_00225050` for bookkeeping, Practice
damage display, HP subtraction, and the zero clamp. Their state roles differ:
`FUN_00228b50` is called by guarded-hit initializer `FUN_00228760`, while
`FUN_002346b0` is the ordinary hit-response consumer. The recorded Sakura
string used the latter; it did not exercise guarded-hit damage.

The calculator `FUN_00224e30` receives raw damage in `f12`, defender in `a0`,
flags in `a1`, and returns damage in `f0`. Defender `+0x20` points to the
attacker. According to the enabled flag bits it applies attacker offense
`+0x148`, the defender durability curve at `+0x14C`, a `1.5` defender-state
factor, temporary attacker and defender factors, and attacker/defender fields
`+0x16C/+0x170`; it finally clamps the result to `[0, 1]`. It does not read the
native combo manager or hit count.

The positive-control replay below separated the synchronized Sakura string's
calculator inputs. Its first two hits used exact raw values `0.02` and `0.03`
with flags `0x133`. The third visible hit produced two calculator events: the
main attack-record event used raw `0.05` with flags `0x133`, and a secondary
direct event used raw `0.02` with flags `0x122`. Hits four and five used main
raw values `0.02` and `0.015`, both with flags `0x133`. With the factors active
in these events, the native results agree exactly with the HP timeline:
`0.02 * 1.32 + 0.03 * 1.32 = 0.066`,
`0.05 * 1.32 + 0.02 * 1.10 = 0.088`, `0.02 * 1.32 = 0.0264`, and
`0.015 * 1.32 = 0.0198`. The differing attack records and the third hit's
secondary event therefore explain the declining and nonuniform damage. No
additional native combo-scaling factor was found in the shared calculator.

### Candidate implementation seam and coverage limit

The runtime-confirmed main seam for this movie is the call from
`FUN_002346b0` to `FUN_00224e30` at runtime `0x00234A80`, ELF offset
`0x134B80`, using the established `runtime = ELF offset + 0xFFF00` mapping.
Clean `SLPS_258.37` contains instruction bytes `8C93080C` there, the
little-endian encoding of `jal FUN_00224e30`. Replacing only this guarded call
with a same-ABI shim is the narrowest proven main-path candidate: the shim can
multiply raw `f12` by a combo factor and then call the original calculator,
preserving native character factors, temporary state, clamp, display, and HP
subtraction.

Hooking `FUN_00224e30` itself is too broad. Its ten static call sites have the
following bounded dispositions; the movie counts come from the positive-
control replay:

| Runtime call | Static owner / role | Movie calls | Combo-scaling disposition |
| ---: | --- | ---: | --- |
| `0x0022529C` | `FUN_00225230`, generic nonzero-damage wrapper with two resident callers | 0 | Classify its two source actions before inclusion. |
| `0x002252F4` | `FUN_002252e0`, externally supplied raw damage with flags `0x100`, called from `FUN_0035b740` | 0 | Exclude from ordinary-string phase 1. |
| `0x00228D18` | `FUN_00228b50`, guarded-hit attack-record damage | 0 | Exclude unless guard/chip scaling is explicitly desired and recorded. |
| `0x00231634` | `FUN_002312b0`, fixed `0.04` response/contact-stage branch | 0 | Static sibling of the observed branch; validate before claiming complete contact-stage coverage. |
| `0x00231698` | `FUN_002312b0`, fixed `0.02` response/contact-stage branch | 1 | Include for the demonstrated normal-string scope. |
| `0x002334BC` | `FUN_002333a0`, generic direct-damage/effect-provenance wrapper with 15 BTL callers | 0 | Classify each desired source category before inclusion. |
| `0x00234A80` | `FUN_002346b0`, ordinary attack-record damage | 8 | Include for the demonstrated normal-string scope. |
| `0x00236354` | `FUN_00235c60`, fixed `0.05` in special response/recovery substate `0x61` | 0 | Exclude from ordinary-string phase 1. |
| `0x0024F00C` | `FUN_0024ed40`, zero-raw state/outcome path | 0 | Exclude. |
| `0x0035B2F8` | `FUN_0035af20`, calculation for Practice presentation | 0 | Exclude; scaling it would alter display computation independently of HP damage. |

Hooking `FUN_00225050` is broader still and loses the attack flags and
raw-damage boundary. This movie also exercised a secondary
direct call at runtime `0x00231698`, ELF offset `0x131798`, during its third
visible hit. Static control flow identifies it as the `0.02` branch of
`FUN_002312b0`, an initializer used only for ordinary response substates
`0x42..0x49`; a per-state flag can select its `0.04` branch instead. At the
observed call the current response was still `(5,0x3D)`, and the later marker
showed `(5,0x43)`. This matches the independently documented promotion from
the `0x3C..0x41` launch group into the `0x42..0x47` contact-stage group in
[`hit_response.md`](hit_response.md#response-exits-contact-stages-and-downed-handoff).
It is therefore fixed response/contact-stage damage, not a second accepted
hit. Hooking only `0x00234A80` would leave its `0.022` native damage unscaled.
The evidence does not assign a visual authoring name such as “wall splat” to
that raw state family. Jutsu, Ultimate Jutsu, throws, projectiles, supports,
status damage, and scripted/environmental damage require isolated recordings
plus a temporary call-site counter before their paths can be included or
excluded. The fixed `0.04` sibling is at runtime `0x00231634`, ELF offset
`0x131734`, with the same clean `jal` bytes `8C93080C`. A general
ordinary/contact implementation must cover it too after a natural positive
capture; otherwise its public scope must explicitly remain the two paths
demonstrated here.

The sibling's exact static gate is bounded. Target substates `0x42` and `0x43`
select `0.04` when fighter word `+0xBB0` has bit `0x400`; substate `0x44`
tests `+0xBBC`; and substates `0x45..0x47` test `+0xBB4`. If the applicable
bit is clear, and for substates `0x48/0x49`, the initializer uses `0.02`.
After the `0.04` damage branch it may also invoke an object callback through
fighter `+0x28`; intercepting only the calculator call preserves that native
callback. The minimum missing positive case is therefore a natural transition
to `0x42..0x47` with its applicable bit `0x400` set, not an arbitrary
eight-or-more-hit combo.

The `0x400` prerequisite is stage-specific in the clean resources. An in-memory
walk of every `0x0B00` model-linked hit/collision mesh in clean
`STAGE/S01.CCS` through `S24.CCS` validated each section's group count, vertex
count, section length, and triangle divisibility. Only `S08.CCS` contains a
group whose authored primitive flags include `0x400`:
`HIT_s08are00_hit_s3`, group 2, has two triangles and raw flags
`0x00959595`. Their six authored vertices span approximately
`x=-824..-713`, `y=736..923`, `z=1059..1124`. `S08.CCS` is load slot 7 and
logical stage ID 8. By contrast, the Practice bootstrap records load slot 6,
which is `S07.CCS`; that archive has 1,125 collision triangles and no authored
group with bit `0x400`. The synchronized marker-1 runtime walk independently
found exactly 1,125 active environment primitives and zero with bit `0x400`,
joining the loaded runtime geometry to the clean `S07` resource. Replaying the
same attacks on that stage cannot exercise runtime `0x00231634`, regardless of
marker placement or input timing. A natural positive capture must instead use
load slot 7, reach the two flagged `S08` triangles, and produce response target
`0x42..0x47`; merely changing stages does not by itself prove that all three
conditions occurred.

That stage-only control was run against the same verified Manual-cache ISO and
movie with a process-local load-slot-7 override and the 140-byte native-behavior
counter shim at runtime `0x008F0000` (SHA-256
`C0CDCB78868150059CAA9FF1BC5080EA48B900C5E2967729D45198B41D850B40`).
Only runtime `0x00231634` was redirected; the capture is under
`@work/Battle mechanics/captures/damage_scaling/probe-s08-callsite-231634/`.
All 13 states retained the hook and shim, loaded slot 7, and contained exactly
395 active environment primitives. Two had runtime flags `0x40959595`, the
orientation-augmented form of the authored `0x00959595`; the counter remained
zero at every marker. All 13 PNGs validated as 640-by-480 images.

The unchanged input movie did not navigate to those triangles. Both live
fighter position vectors at `+0x30` kept component 1 at zero, and component 2
stayed between 0 and approximately 180, while the flagged authored vertices
occupy component-1 range `736..923` and component-2 range `1059..1124`.
Those coordinates agree with `S08`'s side-1 combo anchors at component 1 `800`
and component 2 `1030`; the movie remained in the lower side-0 region visible
in its screenshots. Naruto's marker substates were only `0`, `0x29`, `0x2B`,
`0x48`, and `0x5D`, never `0x42..0x47`. His `+0xBB0/+0xBB4/+0xBBC` values
were respectively `0`, `0x200060C1`, and `0` at every marker, so none contained
bit `0x400`. The stage-only replay therefore proves resource availability but
not the missing branch. A useful new movie or PINE sequence must first navigate
both fighters naturally into `S08`'s upper/side-1 region, then drive a launch
response into the flagged surface; reusing the side-0 attack timing cannot do
so.

The first guarded counter replay targeted only runtime `0x00228D18`. It placed
the probe in the proven-zero development reservation at `0x008F0000`, left its
mutable counter at `0x008F1000` without a recurring PNACH initializer, and
captured all 13 markers under
`@work/Battle mechanics/captures/damage_scaling/probe-callsite-228d18/`. Every
state contained the redirected `jal` bytes `00C0230C00000000` and the complete
resident probe, while the counter remained zero and the HP timeline matched
the synchronized baseline exactly.

A positive-control replay then redirected all ten clean calculator call sites
through one resident logger and retained native behavior. Its captures are
under
`@work/Battle mechanics/captures/damage_scaling/probe-all-damage-callers/`.
The cumulative invocation counts at markers `0001` through `0013` were
`0, 2, 2, 2, 4, 4, 4, 5, 6, 7, 8, 8, 9`. Eight events came from runtime
`0x00234A80`, one came from runtime `0x00231698`, and the other eight static
sites recorded zero. The exact raw/flags sequence was:

| Event | Raw `f12` | Flags `a1` | Runtime call site |
| ---: | ---: | ---: | ---: |
| 1 | `0.02` | `0x133` | `0x00234A80` |
| 2 | `0.03` | `0x133` | `0x00234A80` |
| 3 | `0.05` | `0x133` | `0x00234A80` |
| 4 | `0.02` | `0x122` | `0x00231698` |
| 5 | `0.02` | `0x133` | `0x00234A80` |
| 6 | `0.015` | `0x133` | `0x00234A80` |
| 7 | `0.02` | `0x133` | `0x00234A80` |
| 8 | `0.02` | `0x133` | `0x00234A80` |
| 9 | `0.02` | `0x133` | `0x00234A80` |

Every event targeted Naruto at capture-specific pointer `0x00E44CE0`. The
resident hook and positive counts rule out a code-cache artifact: runtime
`0x00228D18` is conclusively uninvoked by this movie, while `0x00234A80` is its
observed normal-string main path. Events 7 through 9 occur around the later
reset demonstrations; their exact relationship to marker timing requires the
focused call-boundary state probe rather than inference from equal marker HP.

The focused replay then hooked only runtime `0x00234A80` and `0x00231698` and
logged each call before and after the original calculator. Its captures are
under
`@work/Battle mechanics/captures/damage_scaling/probe-live-damage-state/`.
Every record resolved attacker `0x00E36CA0`, side zero, manager
`0x00E40A90`, and matching manager owner `0x00E36CA0`. The decisive records
were:

| Event | Site | Raw | Current / pending | Hit index | Native result |
| ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | `0x00234A80` | `0.02` | `0 / 1` | 1 | `0.0264` |
| 2 | `0x00234A80` | `0.03` | `1 / 1` | 2 | `0.0396` |
| 3 | `0x00234A80` | `0.05` | `2 / 1` | 3 | `0.0660` |
| 4 | `0x00231698` | `0.02` | `3 / 0` | 3 | `0.0220` |
| 5 | `0x00234A80` | `0.02` | `3 / 1` | 4 | `0.0264` |
| 6 | `0x00234A80` | `0.015` | `4 / 1` | 5 | `0.0198` |
| 7 | `0x00234A80` | `0.02` | `0 / 1` | 1 | `0.0264` |
| 8 | `0x00234A80` | `0.02` | `0 / 1` | 1 | `0.0264` |
| 9 | `0x00234A80` | `0.02` | `0 / 1` | 1 | `0.0264` |

All 13 focused-probe marker snapshots matched the baseline HP and native
current/record counts. The resident shim therefore preserved calculator
behavior while proving the input state, native return value, manager ownership,
and reset behavior at the exact call boundary.

A final transient test shim applied the recommended curve (`0.10` decay,
`0.30` floor) at both proven call sites, then called the original calculator.
Its full captures are under
`@work/Battle mechanics/captures/damage_scaling/probe-scaling-curve/`. The
472-byte resident shim at `0x008F0000` had SHA-256
`213E92686716FAFC1854CE1A88E0090C5F2B5BD9C7171AFD7CCF2FEE67509FED` in
all 13 states, and both call sites contained hook word `0x0C23C000`. The
observed main-event tiers were `100%`, `90%`, `80%`, `70%`, and `60%`; the
secondary response/contact event shared hit three's `80%` tier. Exact native
results changed as follows:

| Accepted hit / event | Scaled raw | Native result |
| --- | ---: | ---: |
| hit 1 main | `0.020000000` | `0.026400000` |
| hit 2 main | `0.026999999` | `0.035639998` |
| hit 3 main | `0.039999999` | `0.052800000` |
| hit 3 contact-stage | `0.015999999` | `0.017599998` |
| hit 4 main | `0.014000000` | `0.018479999` |
| hit 5 main | `0.009000000` | `0.011879999` |

The corresponding HP checkpoints after hits two through five were
`0.937960029`, `0.867560029`, `0.849080026`, and `0.837200046`. Native
current/record counts and timer words at every marker remained identical to
baseline. Practice displayed `6.2%`, `13.2%`, `15.0%`, and `16.2%` at those
checkpoints without a display-specific hook. All three later post-reset calls
computed hit index one and returned the unscaled `0.026400000`. This proves
the two-site, stateless raw-input scaling mechanism for the recorded string and
that the native bookkeeping/display consumer receives the scaled result. The
last-place differences from decimal arithmetic are the observed EE
single-precision operation results and should be retained as runtime
expectations rather than replaced by HUD-rounded values.

A final extraction audit reopened all marker savestates and checked the raw EE
fields rather than relying on HUD text. Each of the baseline, focused-probe,
and scaled runs contained exactly 13 savestates and 13 `640x480` screenshots.
The focused probe matched baseline HP bits, manager pointer, owner pointer,
current/record counts, and timer words at every marker. The scaled run matched
all of those native combo fields while producing the expected scaled HP bits.
The audit also decoded all nine focused and scaled log records, the all-caller
count progression `0,2,2,2,4,4,4,5,6,7,8,8,9`, every hook word, and the
resident-code hash above. All checks passed.

All static claims above come from the read-only clean `SLPS_258.37` export and
binary, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`.
The combo object layout, reset sequence, HP timeline, main and secondary damage
call sites, and hit-index formula are additionally runtime-confirmed by
synchronized replays. Coverage outside this Sakura normal string remains open.

## Unresolved extra-hit branch lead

A historical one-branch candidate exists at EE `0x20241F40`, labelled “extra
hit.” Its instruction change remains recoverable from Git history, but the
label and runtime effect are unproven and must not be conflated with the
accepted `ELF-B002` battle-logic patch.

## Unresolved Ultimate-Jutsu chakra leads

Historical notes point to ELF file `0x1492B0` for level-scaled chakra
subtraction and `FUN_002254a0` for shared chakra addition. Recheck the preserved
disassembly before assigning either role or designing a patch.
