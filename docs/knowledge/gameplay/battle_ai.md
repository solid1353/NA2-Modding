# Battle AI

This document owns reverse-engineering knowledge about the clean NA2 battle AI:
controller ownership, lifecycle, configuration, target and spatial inputs, action
selection, state dispatch, logical-input synthesis, direct action queues, and
random-number use. State names and physical button meanings are deliberately not
invented where the binary only establishes raw IDs or masks.

The findings below are static unless explicitly described otherwise. The main
evidence is clean `BTL.BIN`, SHA-256
`56FD042740221E3CC91417194F147142799D51FE70642273F4E97BD389D5D63C`,
and clean `SLPS_258.37`, SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`.

## Research coverage

- **Assigned scope:** the clean NA2 battle AI in `BTL.BIN`: controller
ownership, decision/action dispatch, difficulty and configuration inputs,
primary and alternate target selection, state transitions, directly
established RNG use, and lifecycle boundaries. Resident `SLPS_258.37` was
followed only where needed to prove the BTL caller, settings accessors, random
generator, command bridge, and direct-action queue consumers.
- **Exploration depth:** coverage depth is mixed and is stated explicitly:

  **Exhaustive within a bounded asset or range:** all 43 entries of the action
  dispatcher table at live `0x008C3810`; all direct clean-BTL writes to the
  state word in the corrected full-file text; all 12 direct calls to the
  action-record selector and all 14 direct calls to resident queue
  `FUN_0021D380`; all aligned calls to the two resident RNG wrappers in the
  live AI cluster `0x006F0000..0x00706500` (167 total); all 40 parameters in
  each of the six selectable Strength rows; the contiguous unselectable
  seventh row; the full `10 x 40` secondary modifier matrix; the six-row
  ten-step phase table; the 96-entry per-character pair table; and the aligned
  resident scan that found 74 analogous calls to the shared AI tick.
  **Bounded structural tracing:** main tick
  `D/L/F 00704D00/00704D40/50E40`, initializer
  `00705D30/00705D70/51E70`, target refresh and spatial classifier, route
  planner and alternate-target producers/consumers, settings loader/apply and
  COM toggle, representative resident wrapper `FUN_00250DA0`, generic
  fighter-list scheduler `FUN_0024FD80`, command bridge `FUN_00217320`, and
  queue admission/consumption from `FUN_0021D250` through `FUN_0023A390`.
  These paths were followed through their relevant callers, fields, and side
  effects, but not every branch in every large decision helper was assigned a
  behavioral meaning.
  **Sampled or semantic-only coverage:** one representative character wrapper
  was decoded in detail while the other 73 call sites were counted and checked
  structurally; large reaction helpers were decoded far enough to establish
  state writes, profile consumers, RNG sites, target/route effects, and direct
  action queues, but most move-specific intent remains unnamed.

- **Confirmed coverage:** the overlay's `0x40` address skew;
resident virtual-method ownership and same-update command consumption; the two
static AI slots and their cross-side initialization behavior; native Practice
settings and six Strength profiles; deterministic primary-opponent binding;
ordered, random-gated alternate target sources; the complete dispatcher and
direct constructor map; selector, resident queue, and four-category queue
lifecycle; the continue-screen modifier input; and the shared resident
MT19937-derived RNG, phase cursors, tables, and audited AI call sites.

- **Unresolved or untested:** player-facing
names for most raw states and action-record classes; exhaustive semantics for
every branch of the large decision/reaction helpers; the role of the seventh
profile row and profile parameters 24 and 31; the external or indirect caller
of settings apply; exact labels for continue-result values and the session
mode that bypasses the secondary modifier; and whether early-return paths can
expose a stale controller triple at runtime. These are recorded as negatives or
hypotheses rather than inferred names.

- **Deliberate exclusions and overlap:** Adventure, substitution and its bar, damage
formulas/scaling, 60-FPS or timing work, widescreen/camera projection, media,
and localization. Shared command-mask meanings were taken only from the
existing `action_commands.md` evidence; this document does not take ownership
of that command system or of broader battle facts already owned by
`battle.md`.

- **Evidence limitations:** behavioral validation was static against the hashed clean files. The corrected
full-file import, raw aligned instruction scans, loader mapping, and clean
savestate mapping were cross-checked, but no AI runtime trace, live field watch,
input replay, or probability experiment was run. Consequently execution order,
addresses, direct calls, tables, and static side effects are high-confidence;
player-facing intent and timing-sensitive runtime consequences remain bounded
by the limitations above.

## Address convention and corrected overlay mapping

The complete 2,237,184-byte (`0x222300`) MWo3 file is retained in live memory at
its header base. Its header reports:

| Header field | Value |
| --- | ---: |
| magic | `MWo3` |
| load base | `0x006B3F00` |
| text length | `0x001DB6C0` |
| data length | `0x00046C00` |
| BSS length | `0x00006E80` |

The preserved Ghidra import omitted the `0x40`-byte header but placed the first
payload byte at `0x006B3F00`. It therefore displays every file-backed byte and
function `0x40` below its live address. This was independently established from
the clean loader and a clean savestate, and a disposable full-file Ghidra import
at the correct base recovered coherent function boundaries and call graphs.

This document uses these abbreviations:

- `D`: address in the preserved Ghidra/export baseline.
- `L`: live EE address.
- `F`: byte offset in clean `BTL.BIN`.

For file-backed BTL bytes:

```text
L = D + 0x40
F = L - 0x006B3F00
  = D - 0x006B3F00 + 0x40
```

The payload begins at `L 0x006B3F40`; the file-backed image ends and BSS begins
at `L 0x008D6200`. Absolute pointers and `j`/`jal` operands encoded inside BTL
already contain live addresses. The preserved importer consequently resolves an
intra-BTL absolute target against bytes `0x40` too late. The true preserved byte
entry is encoded target minus `0x40`. Resident `SLPS_258.37` addresses and
absolute BSS addresses are already live and must not receive this correction.

This distinction is essential. For example, the instruction at `D 0x00705320`
encodes a call to live `0x006FB840`. Its true callee bytes are the prologue of
preserved `FUN_006FB800` at `D 0x006FB800`; the preserved export instead labels
the continuation at `D 0x006FB840` as the callee.

## Principal function map

`Preserved symbol` means the symbol present at the real byte entry in the
original export. “Continuation label” records a misleading symbol produced at
the encoded live address by the skewed import.

| Role | Preserved symbol or entry | D | L | F |
| --- | --- | ---: | ---: | ---: |
| target-position source selector | `FUN_006F1DB0` | `0x006F1DB0` | `0x006F1DF0` | `0x3DEF0` |
| action-record selector | `FUN_006F2B40` | `0x006F2B40` | `0x006F2B80` | `0x3EC80` |
| ten-step RNG phase gate | `FUN_006F3100` | `0x006F3100` | `0x006F3140` | `0x3F240` |
| route/path planner | `FUN_006F3770` | `0x006F3770` | `0x006F37B0` | `0x3F8B0` |
| neutral/reset helper | unnamed true entry; false continuation `FUN_006F3F80` | `0x006F3F40` | `0x006F3F80` | `0x40080` |
| 43-state action dispatcher | `FUN_006FB800` | `0x006FB800` | `0x006FB840` | `0x47940` |
| spatial classifier | `FUN_00702E20` | `0x00702E20` | `0x00702E60` | `0x4EF60` |
| main per-fighter AI tick | `FUN_00704D00` | `0x00704D00` | `0x00704D40` | `0x50E40` |
| AI initializer | `FUN_00705D30`; false continuation `FUN_00705D70` | `0x00705D30` | `0x00705D70` | `0x51E70` |
| self/opponent refresh | unnamed true entry; false continuation `FUN_00706350` | `0x00706310` | `0x00706350` | `0x52450` |
| settings-object loader | `FUN_00880F70`; false continuation `FUN_00880FB0` | `0x00880F70` | `0x00880FB0` | `0x1CD0B0` |
| settings apply | `FUN_00881160` | `0x00881160` | `0x008811A0` | `0x1CD2A0` |
| COM controller toggle | `FUN_008813B0`; false continuation `FUN_008813F0` | `0x008813B0` | `0x008813F0` | `0x1CD4F0` |
| profile UI bound helper | `FUN_00881950` | `0x00881950` | `0x00881990` | `0x1CDA90` |

## Controller ownership and lifecycle

The AI is called by resident per-character fighter wrappers rather than by a
BTL-internal caller. Representative resident `FUN_00250DA0` is installed in a
fighter-class vtable at `0x005DB18C`. Its exact control flow is:

- `0x00250DA8`: load `u16 fighter+0x60`;
- `0x00250DAC..0x00250DB0`: extract `((value >> 5) & 0xF)`;
- `0x00250DB4`: skip the AI call when that nibble is zero;
- `0x00250DBC` (SLPS file `0x150EBC`): `jal 0x00704D40`, preserving the
  fighter pointer in `a0`.

An aligned scan of clean `SLPS_258.37` finds exactly 74 direct `jal` instructions
to `L 0x00704D40` in analogous character wrappers. This broad fan-in establishes
the true ownership boundary: controller nibble zero is the human/no-AI path;
any nonzero value invokes the shared BTL AI tick.

The generic caller is resident fighter-list update `FUN_0024FD80` (runtime
`0x0024FD80`, SLPS file `0x14FE80`). For each eligible fighter it loads the
vtable from fighter `+0x50`, loads method slot `+0x1C`, and executes `jalr` at
runtime `0x00250094` (file `0x150194`) with the fighter in `a0`. Eligibility at
that point requires fighter byte `+0x00` bit 1 and `s32 fighter+0x20C <= 0`.
Representative `FUN_00250DA0` occupies exactly that vtable slot and always
returns zero after its conditional AI call.

The scheduler then makes a second eligible-fighter pass. It calls resident
`FUN_00217320` at `0x0025011C` to copy command-controller
`+0xAC/+0xB0/+0xB4` into fighter `+0x338/+0x33C/+0x340`, followed by the
ordinary input consumers. Thus the BTL AI tick synthesizes this update's
command triple before the resident bridge consumes it; there is no extra-frame
queue at this ownership boundary. `FUN_0024FD80` itself is called by resident
`FUN_002504B0` at `0x00250658` (file `0x150758`).

The bridge is also the first resident arbitration boundary. Fighter byte
`+0x61` bit `0x80` or byte `+0x62` bit 0 makes it zero all three fighter-side
outputs and halfword `+0x98A` instead of copying. After a normal copy, if the
mask contains both `0x00001000` and `0x01000000`, it clears `0x01000000`.
Consequently BTL output is proposed input, not an unconditional action; the
resident fighter state can suppress it and this specific mask conflict is
resolved before later consumers.

The settings path controls that nibble:

1. `FUN_00880EF0` (`D/L/F 00880EF0/00880F30/1CD030`) calls the true settings
   loader at call site `D/L/F 00880F38/00880F78/1CD078`.
2. `FUN_00880F70` fills and normalizes 17 settings-object fields from `+0x6C`
   through `+0xAC` to their count-table ranges. The AI-facing subset is:

   | Object field | Manager key | Native setting | Values |
   | ---: | ---: | --- | --- |
   | `+0x90` | `0x0C` | Status | Manual, COM, Stand, Jump, Double-jump (`0..4`) |
   | `+0x94` | `0x0B` | Strength | Easiest, Easy, Normal, Hard, Very hard, Ultimate (`0..5`) |
   | `+0x98` | `0x0D` | Attack | No, Single, Combo, Projectile, High Speed Move, Ultimate Jutsu, Jutsu (`0..6`) |
   | `+0x9C` | `0x0E` | Guard | No, Use (`0..1`) |
   | `+0xA0` | `0x0F` | Move | Stay, Follow (`0..1`) |
   | `+0xA8` | `0x12` | Linked Attack | Don't use, Normal, frequent/random (`0..2`) |
   | `+0xAC` | `0x10` | Extra Hit Counter | Normal, Always return (`0..1`) |

   These ranges come from the clean count table at live `0x008D18C0`
   (actual bytes at `D/F 008D1880/21D9C0`). The omitted rows are outside this
   document's AI scope.
3. `FUN_00881160` writes those fields with resident `FUN_001F59F0`, rereads
   normalized key `0x0B`, and passes a force flag when requested `+0x94` differs
   from the normalized stored value. Its calls to the toggle are at
   `D 0x00881310` and `D 0x0088132C`.
4. `FUN_008813B0` chooses the controlled fighter. `manager+0x18 == 0` selects
   index 2 and `manager+0xDE8`; a nonzero value selects index 1 and
   `manager+0xDE4`. It mirrors `Status != Manual` into bit 1 at
   `manager + 0x20 + index*0x28`.
5. Manual clears bits 5..8 of fighter `u16 +0x60` with `& 0xFE1F`. Every
   non-Manual Status installs controller kind 1 with `| 0x20` and calls the
   initializer when the old nibble was zero or the force flag is nonzero. A
   null fighter still gets the manager flag update but no initializer call.

The initializer call is at `D/L/F 00881490/008814D0/1CD5D0` and targets live
`0x00705D70`. Selecting Manual does not clear the static AI state and calls no
destructor or free routine. The next Manual fighter tick simply stops entering
the AI; selecting a non-Manual Status again initializes when the controller
nibble was zero.

No direct BTL caller of `FUN_00881160` was found. Its caller is external or
indirect. No heap allocation, per-AI object constructor, AI destructor, or AI
free path was found: controller state is two static BSS slots.

## Per-side state block

The slots are live BSS and have no file offsets:

```text
side 0: 0x008D6590
side 1: 0x008D6770
stride: 0x1E0
```

The tick chooses the slot from fighter `+0x60` bit 0. Confirmed fields are:

| Offset | Width | Established use |
| ---: | ---: | --- |
| `+0x00` | `f32` | synthesized movement magnitude; copied to command controller `+0xB0` |
| `+0x04` | `f32` | synthesized direction/angle; copied to command controller `+0xB4` |
| `+0x08` | `s16` | refreshed from fighter `+0x326`, the target/facing-side value |
| `+0x0C` | `f32` | refreshed from fighter `+0x32C`, planar opponent distance |
| `+0x10` | `u32` | synthesized logical command mask; copied to command controller `+0xAC` |
| `+0x1C` | pointer | controlled fighter (`self`) |
| `+0x20` | pointer | primary opponent selected from manager `+0xDE4/+0xDE8` |
| `+0x24/+0x26` | 2 `s16` | per-character AI values refreshed each tick from live table `0x008C3460 + character_id*4`; `+0x26` gates alternate-target candidates |
| `+0x30` | `s32` | spatial bucket; the main classifier writes `0..5` |
| `+0x34` | `u32` | current dispatcher state ID, valid dispatch range `0..0x2A` |
| `+0x38` | `s32` | countdown initialized to `90` and decremented by the tick |
| `+0x3C` | `u32` | route/path submode, cleared by reset and planner entry |
| `+0x40..+0x4C` | 4 words | cached controlled-fighter position from the spatial classifier |
| `+0x54` | `s32` | alternate world-object handle; `-1` means absent |
| `+0x58` | `s32` | secondary handle/ID; initialized and reset to `-1` |
| `+0x5C` | `s32` | selector used by target-position source mode 2; initialized to `-1` |
| `+0x68` | `u32` | target-position source mode (`0`, `1`, or `2`) |
| `+0x80/+0x84` | `s32` | initialized from fighter `+0x9F6`; later used in route/platform logic |
| `+0x90` | byte | decision/request-occupied latch; set beside many state transitions, but not equivalent to `state != 0` |
| `+0x94..+0x10C` | 31 `u32` | countdown/cooldown bank; every nonzero entry is decremented each tick |
| `+0xB4` | `s32` | randomized initialization timer, `150 + rand(0..120)` |
| `+0x104` | `s32` | initialized to `120` |
| `+0x110` | `s32` | retry countdown used by state 27; an invalid mode-2 point seeds it to `30` |
| `+0x114/+0x118` | `s32` | initialized to `90` and `60`; both are decremented when nonzero |
| `+0x128` | `s32` | special-action cooldown produced by the action selector and decremented by tick |
| `+0x144/+0x148` | `s32` | mode-2 near/far target deadlines, seeded to `30/210` by its constructor |
| `+0x160..+0x1AF` | 40 `s16` | selected behavior-profile parameters |
| `+0x1B0` | `s32` | first usable fighter action slot among slots 4..9, or `-1` |
| `+0x1B4/+0x1B8/+0x1BC` | `s32` | ten-step RNG phase cursors, initialized to `-1` |

The corrected initializer proves these writes for both slots before applying a
profile only to the selected side:

- zero: `+0x0C`, `+0x30`, `+0x34`, `+0x3C`, `+0x50`, `+0x60`, `+0x64`,
  `+0x68`, `+0x88`, `+0x8C`, byte `+0x90`, all 31 words `+0x94..+0x10C`,
  `+0x11C`, `+0x120`, byte `+0x124`, bytes `+0x125/+0x126`, `+0x128`,
  `+0x144`, `+0x148`, byte `+0x14C`, byte `+0x14E`, halfword `+0x150`,
  `+0x1D0`, and bytes `+0x1D4/+0x1D5/+0x1D6`;
- `-1`: `+0x54`, `+0x58`, `+0x5C`, `+0x1B4`, `+0x1B8`, `+0x1BC`,
  `+0x1C0`, `+0x1C4`, and `+0x1C8`;
- constants: `+0x38=90`, `+0x104=120`, `+0x114=90`, `+0x118=60`, and
  byte `+0x14D=0xFF`;
- fighter-derived: `+0x80` and `+0x84` receive signed fighter `+0x9F6`;
- randomized: `+0xB4 = 150 + FUN_00180210(120)`;
- in Practice manager mode, `+0xAC` is set to `60` unless setting key `0x0C`
  equals 1.

This is the initializer's write set, not a claim that every unknown field has
been semantically identified. Notably, the per-tick output clear owns
`+0x00/+0x04/+0x10`.

The two-slot reset is a cross-side lifecycle effect. Reinitializing either
fighter clears the transient state, handles, source/route submodes, latches,
and cooldowns listed above in **both** static slots, then copies a new profile only into the
selected fighter's slot. It does not clear the unselected slot's existing
`+0x160..+0x1AF` profile row. Thus forcing one COM setting can interrupt the
other side's in-progress AI state without replacing that side's parameters.

The neutral/reset helper at `D/L/F 006F3F40/006F3F80/40080` performs a smaller
current-side reset. It writes `+0x54=-1`, `+0x58=-1`, `+0x34=0`, byte
`+0x90=0`, `+0x3C=0`, `+0x120=-1`, `+0x04=0`, `+0x10=0`, `+0x00=0`,
`+0x94=0`, `+0x9C=0`, `+0xD8=0`, and bytes `+0x1D4/+0x1D5=0`.

The per-character source is a 96-entry table of two signed halfwords at
`D/L/F 008C3420/008C3460/20F560`, ending immediately before the secondary
modifier matrix. The tick indexes it directly with fighter character ID
`+0x68` and performs no local bounds check. In the clean table `+0x24` ranges
from 0 through 3 and participates in state/region reaction choices;
`+0x26` ranges from 0 through 90 and is used only as the inclusive-100-roll
threshold in the mode-1 and mode-2 alternate-target searches described below.

## Main tick and output boundary

`FUN_00704D00` first selects current and opposite side indices from fighter
`+0x60` bit 0. It then:

1. returns immediately if outer-graph global `0x00607654` is null;
2. calls resident `FUN_00216820`, which returns the value reached through
   `0x00607654 -> +0x08 -> +0x14`; a nonzero value resets the current AI slot
   and returns;
3. when request latch `+0x90==1` but state `+0x34==0`, resets the inconsistent
   slot and continues;
4. refreshes self, opponent, facing-side, and planar-distance fields;
5. returns unless fighter byte `+0x61` bit `0x08` is set for both self and
   opponent, or when resident `FUN_001EC290()` reports the nonzero
   timeout/end-reason marker at `0x00607674`;
6. decrements the state countdowns and cooldown bank;
7. hot-reloads the base profile in Practice mode when manager key `0x0B`
   changes;
8. clears `+0x00`, `+0x04`, and `+0x10`;
9. runs the spatial classifier and scans fighter action slots 4..9;
10. runs the decision stages, state dispatcher, and post-dispatch reactions;
11. commits the logical output triple to the fighter's command controller.

The returns in steps 1, 2, and 5 branch to the epilogue before both the output
clear and final command-controller stores. Step 2 clears the internal slot via
the reset helper first; the null-graph, inactive-fighter, and terminal-marker
paths do not. Static code does not establish whether another subsystem clears
the already-stored command-controller triple on those paths.

The principal decision-call sequence in corrected live naming is:

```text
FUN_00702E60                     spatial classifier
FUN_006FFEC0
FUN_00703170 / FUN_00703A70      mode-dependent
FUN_00703D20
FUN_006FDF30
FUN_006FF410                     one mode path
  or FUN_006FE720 + FUN_006FEAC0 another mode path
FUN_006FB840                     43-state dispatcher
FUN_006FF9C0                     mode-dependent post-dispatch stage
```

The corrected call order is firm. The two formerly unlabelled boundary helpers
can be narrowed structurally without inventing move names:

- Pre-dispatch `D/L/F 006FFE80/006FFEC0/4BFC0` detects two paired transient
  fighter-state patterns: both actors at `+0x190` value `0x5B/0x5C`, or self
  `+0xA3C==0x13` with both actors' `+0x9BA/+0x9BC` equal to 3. When one is
  present and cooldown `+0x104` is zero, an inclusive `0..100` roll below
  profile parameter 25 resets the AI state and ORs logical mask `0x1000`;
  failure sets `+0x104=5`. Outside those patterns, self `+0xB10==2` with an
  expired `+0x104` resets, selects quotient `0..2` from
  `FUN_00180210(29)/10`, and calls resident `FUN_00245D90(self,quotient)`.
  The adjacent `+0xB10==4` path refreshes route-region fields `+0x80/+0x84`.
- Post-dispatch movement/environment correction
  `D/L/F 006FF980/006FF9C0/4BAC0` runs only in ordinary modes or Practice
  Status COM, and only when output direction mask `+0x10 & 3` is nonzero. It
  clears byte `+0x1D6`, scans the same-region object list rooted at the object
  manager's `+0x14`, and predicts self X movement using fighter radius
  `+0x994 * 3` plus an object radius. A predicted overlap can set latch
  `+0x90`, OR mask `0x00010000`, and set `+0x1D6=1`; under the alternate raw
  fighter gates (`+0x998<0`, `+0x1C4>10`) it instead selects state 10 and ORs
  `0x00020000`. A separate object-flag path within distance `900` writes a
  target region to `+0x80`, selects state 8, and sets the latch. This is an
  environmental correction of an already synthesized direction, not primary
  opponent selection.

The mode gates around that sequence are also exact:

- `FUN_006FFEC0` always runs after the classifier/action-slot scan. Resident
  `FUN_00247D30` at runtime/file `00247D30/147E30` is exactly a load of signed
  fighter halfword `+0xB10`; a positive value skips the remaining decision and
  dispatch stages and goes directly to output commit. Because output fields
  were already cleared, only commands synthesized by the prepass can survive
  on this path.
- `FUN_00703170` and `FUN_00703A70` run in non-Practice modes. In Practice
  (`manager+0x0C==3`) they run only for Status COM (`key 0x0C==1`).
- `FUN_00703D20` and `FUN_006FDF30` run on every path that reaches the main
  decision sequence. `FUN_00703D20` itself ends with the sole direct call to
  the Practice-specific stage `D/L/F 00702460/007024A0/4E5A0`, at call site
  `00704CD0/00704D10/50E10`; that stage returns immediately outside Practice
  or for Status COM.
- Practice with scripted Status Stand/Jump/Double-jump (`key 0x0C=2..4`) next
  runs `FUN_006FF410` only. All ordinary modes, and Practice Status COM,
  normally run `FUN_006FE720` then `FUN_006FEAC0`; the one exception is
  Practice Linked Attack frequent/random (`key 0x12==2`), which substitutes
  `FUN_006FF410`.
- The dispatcher then runs. `FUN_006FF9C0` runs after it in ordinary modes and
  for Practice Status COM, but is skipped for scripted Practice Status values.

Exact main-tick call sites are:

```text
callee          D          L          F
FUN_00702E60    0070500C   0070504C   05114C
FUN_006FFEC0    007050B8   007050F8   0511F8
FUN_00703170    00705144   00705184   051284
FUN_00703A70    0070514C   0070518C   05128C
FUN_00703D20    00705154   00705194   051294
FUN_006FDF30    0070515C   0070519C   05129C
FUN_006FF410    007051CC   0070520C   05130C
FUN_006FF410    00705274   007052B4   0513B4
FUN_006FE720    00705284   007052C4   0513C4
FUN_006FEAC0    0070528C   007052CC   0513CC
FUN_006FB840    00705320   00705360   051460
FUN_006FF9C0    00705394   007053D4   0514D4
```

The Practice-only `FUN_007024A0` consumes the scripted-dummy controls directly:
Guard Use (`key 0x0E==1`) gates one state-18 reaction; Move Follow
(`key 0x0F==1`) changes state-5 route retention; Status Stand (`key 0x0C==2`)
has another state-5 retention rule, while Jump/Double-jump (`3/4`) control
state-36 branches and their slot `+0x114` countdown; and any Attack other than
No (`key 0x0D!=0`) enables a state-37 branch paced by slot `+0x118`.

The final output stores are exact:

| Operation | D | L | F |
| --- | ---: | ---: | ---: |
| load `self` from slot `+0x1C` | `0x0070572C` | `0x0070576C` | `0x5186C` |
| load command controller from `self+0x24` | `0x00705730` | `0x00705770` | `0x51870` |
| store slot `+0x10` to controller `+0xAC` | `0x00705738` | `0x00705778` | `0x51878` |
| store slot `+0x00` to controller `+0xB0` | `0x00705740` | `0x00705780` | `0x51880` |
| store slot `+0x04` to controller `+0xB4` | `0x00705748` | `0x00705788` | `0x51888` |

BTL contains the class string `ccCommandCtrl`, and the human command-controller
paths use the same `+0xAC/+0xB0/+0xB4` representation. The AI therefore owns a
logical command source rather than a separate fighter-motion executor. Some AI
paths also queue action-record indices directly through resident
`FUN_0021D380`; the two dispatch mechanisms coexist.

## Primary target and spatial classification

The self/opponent refresh is called from the main tick at
`D/L/F 00704DB8/00704DF8/50EF8`. It writes:

```text
slot+0x08 = *(s16 *)(fighter+0x326)
slot+0x0C = *(f32 *)(fighter+0x32C)
slot+0x1C = fighter
slot+0x20 = manager+0xDE8 when fighter+0x60 bit0 == 0
            manager+0xDE4 when fighter+0x60 bit0 == 1
```

Thus ordinary one-on-one target ownership is deterministic: every tick the AI
independently binds the opposite manager fighter. It does not search a fighter
list, consult reciprocal fighter `+0x20`, or use RNG to choose its primary
fighter target.

Resident `FUN_002174A0(fighter,0)`, called by standard active-fighter update
`FUN_0024C440` at `0x0024C4D0`, establishes the source-field semantics. It keeps
fighter `+0x20` as the reciprocal opponent pointer (falling back to self when
null), writes bearing at `+0x328`, planar distance at `+0x32C`, full 3D distance
at `+0x330`, vertical delta at `+0x334`, and target/facing side at `+0x326`.
The AI's cached `+0x0C` is therefore specifically planar opponent distance.

The spatial classifier at `D/L/F 00702E20/00702E60/4EF60`, called at
`D/L/F 0070500C/0070504C/5114C`, caches current position at slot
`+0x40..+0x4C` and writes slot `+0x30`:

- equal fighter `+0x324` and `+0x9F6` indices: bucket `0` at distance `<=150`,
  `1` at `<=250`, `2` at `<=400`, and `3` above `400`;
- higher or lower target index: bucket `4` or `5`;
- buckets below `3` are forced to `3` when the absolute `+0x38` position
  component difference exceeds `400`.

The facing-correction helper at `D/L/F 006F1B20/006F1B60/3DC60` compares the
primary target and current X coordinates with fighter `+0x98C`. A wrong-facing
right case writes angle `-pi/2`, mask `1`, magnitude `0`; wrong-facing left
writes `+pi/2`, mask `2`, magnitude `0`. These are raw logical mask values, not
yet mapped to named controller buttons.

## Alternate target-position sources and path states

Primary fighter ownership remains fixed, but navigation can request a position
from three sources through slot `+0x68`. Corrected live `FUN_006F1DF0` proves:

- mode `0`: copy four words at primary opponent `+0x30..+0x3C`;
- mode `1`: resolve alternate world-object handle slot `+0x54` through resident
  `FUN_00376610` and `FUN_00375760`;
- mode `2`: look up a record selected by slot `+0x5C` through live BTL
  `FUN_006F1D00` (`D/F 0x006F1CC0/0x3DE00`) and copy its first four words.

Direct calls to this source selector are at
`D/L/F 006F37BC/006F37FC/3F8FC` and
`006F67E8/006F6828/42928`.

Both alternate modes have direct producers:

- live `FUN_006FC480` (`D/F 006FC440/48580`) enumerates resident world-object
  handles, resolves each handle to a position and region, and accepts a
  candidate only after its object/state exclusions, the exact test
  `rand(0..100) < slot+0x26`, and a planar comparison placing the candidate
  closer to self than to the primary opponent. It takes the first candidate in
  enumeration order that passes those tests rather than choosing uniformly
  among all candidates. On success it stores the handle
  at `+0x54`, the candidate vector at `+0x70..+0x7C`, and its region at
  `+0x80`. Its sole direct call is live `0x00701C60` inside
  `FUN_00701BD0` (`D/L/F 00701B90/00701BD0/4DCD0`). That caller requires state
  0/1, an expired slot `+0x94`, and profile-parameter-28 success; it then
  resets, sets active, writes source mode `1` and state `24`, and invokes the
  route planner. State 27 independently calls live `FUN_006FC7F0(120.0)`
  (`D/F 006FC7B0/488F0`), which can populate the same handle/vector/region
  fields before that handler writes mode `1`, state `24`, and plans a route.
- live `FUN_006FCE00` (`D/F 006FCDC0/48F00`) is the direct mode-2 constructor.
  With slot `+0xA8` expired and profile-parameter-0 success, it walks every
  region and both point lists exposed by live `FUN_00708E10/00708E40`. A
  candidate must pass its validity test, the same exact
  `rand(0..100) < slot+0x26` gate, and be closer to self than to the primary
  opponent. It likewise retains the first passing point in region/list order;
  manager stage byte `+0x98==0x16` explicitly excludes region index 0 from one
  of the two point lists. Success resets the slot,
  sets active, source mode `2`, state `26`, stores the flattened point index at
  `+0x5C`, the point at `+0x70..+0x7C`, and its region at `+0x80`, then invokes
  the route planner. Planner success restores state `26` and sets
  `+0x144=30`, `+0x148=210`; no candidate sets `+0xA8=60`. Its sole direct call
  is `D/L/F 00701D54/00701D94/4DE94` in `FUN_00701BD0`, which is itself called
  from the main decision stage at `D/L/F 0070491C/0070495C/50A5C`.

`FUN_006F1D00` enumerates those same two point lists in the same region-first
order and returns the record at flattened index `+0x5C`. This closes the
mode-2 producer/consumer chain; the cached vector is a planning input, while
the flat index is what lets later target refresh find the live record again.

The route planner at `D/L/F 006F3770/006F37B0/3F8B0` clears `+0x3C`, resolves
the requested target source and current actor region, and writes raw dispatcher
states:

- state `3` when actor and target resolve to the same region or a stage-specific
  direct case applies;
- state `4` when distinct regions require route fields to be populated;
- state `5` or `0` when a target/region cannot be resolved, depending on the
  stage and fighter-state gates.

These are structural meanings only and do not imply player-facing move names.

Their consumers establish more precise structural labels. State-3 helper
`D/L/F 006F7E30/006F7E70/43F70` compares actor region with target region
`+0x80`. A region mismatch emits the corresponding vertical/region-transition
logical masks; in the same region it drives left/right movement toward cached
target X at `+0x70`, using output magnitude `1.0` and angle `+/-pi/2`, and
returns to state zero at its distance/height completion gates. State-4 helper
`D/L/F 006F6360/006F63A0/424A0` consumes the planner's segment indices,
segment interpolation, and route phase fields to synthesize traversal input;
when no active segment remains it delegates to the same direct-position helper.
State-5 helper `D/L/F 006F53D0/006F5410/41510` runs that route executor, then
copies the primary opponent's live `+0x30..+0x3C` position to slot
`+0x70..+0x7C` and its `+0x9F6` region to `+0x80`, replans when the route or
region changes, and restores state 5 plus latch `+0x90` on a surviving path.
Thus states 3, 4, and 5 are respectively direct target-point motion,
route-segment traversal, and moving-primary-target route maintenance. Those
are code-level roles, not player-facing action names.

The two alternate-source dispatcher consumers close their lifecycle loops:

- State-24 helper `D/L/F 006F4BD0/006F4C10/40D10` first resolves mode-1
  handle `+0x54`; failure resets immediately. It runs the shared route
  executor, replans against cached target vector `+0x70..+0x7C` and region
  `+0x80` whenever execution returns the dispatcher state to zero or the actor's current route
  region changes, and resets if replanning cannot produce a state. A surviving
  pass explicitly restores state 24. Thus the handle is validated each tick,
  not trusted indefinitely.
- State-26 helper `D/L/F 006F4220/006F4260/40360` re-resolves flattened point
  `+0x5C` through `FUN_006F1D00`. A missing point resets; one invalidated-point
  condition also clears `+0x5C`, selects state 27, seeds retry `+0x110=30`,
  and sets latch `+0x90`. Within planar distance `115` and the target region,
  it enters direct facing/action logic under deadline `+0x144`; a vertical
  separation above `100` can ask resident `FUN_0021DF60` for mask-8 action and
  queue it when no action is pending. Outside that near case, deadline
  `+0x148` expires to reset; otherwise the shared route executor runs and the
  route is rebuilt when its region identity changes. A surviving pass restores
  state 26 and the request latch. The constructor's `+0x144=30` and
  `+0x148=210` writes are therefore active near/far lifetimes, not unexplained
  constants.

## Action-state dispatcher

The dispatcher loads slot `+0x34` at `D 0x006FB828`, rejects values above
`0x2A`, and jumps through a 43-entry table. The table bytes are at
`D/L/F 008C37D0/008C3810/20F910`. Every raw entry is a live handler pointer;
the preserved handler bytes are pointer minus `0x40`.

In the table below, `reset` means live `FUN_006F3F80`; `actor` and `target`
mean slot `+0x1C` and `+0x20`. Masks remain deliberately numeric.

| State | Handler D/L/F | Directly established behavior |
| ---: | --- | --- |
| `0` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `1` | `006FB854/006FB894/47994` | reset when slot `+0xD8` is zero |
| `2` | `006FB9E4/006FBA24/47B24` | call live `FUN_006F6080`: reset if target X is outside its cached region bounds; otherwise spatial buckets 0/1 delegate to `FUN_006F9B20`, buckets 2/3 synthesize left/right movement from facing field `+0x08`, and buckets 4/5 emit masks `0x00080000/0x00100000` |
| `3` | `006FB9F4/006FBA34/47B34` | call live `FUN_006F7E70`, the direct cached-target-position mover |
| `4` | `006FBA04/006FBA44/47B44` | call live `FUN_006F63A0`, the route-segment executor |
| `5` | `006FBA14/006FBA54/47B54` | call live `FUN_006F5410`, the moving-primary-target route maintainer |
| `6` | `006FB87C/006FB8BC/479BC` | when slot `+0x108` is nonzero, OR mask `0x00040000`; depending on actor `+0x63` bit 6 and planar distance versus `400`, either retain or clear slot `+0x94` and `+0xD8` |
| `7` | `006FBA24/006FBA64/47B64` | call live `FUN_006F75E0` |
| `8` | `006FBA34/006FBA74/47B74` | call live `FUN_006F7CE0` |
| `9` | `006FBA44/006FBA84/47B84` | call live `FUN_006FAA50` |
| `10` | `006FBA64/006FBAA4/47BA4` | call live `FUN_006F9180` |
| `11` | `006FBB54/006FBB94/47C94` | call live `FUN_006F9B20` |
| `12` | `006FBB74/006FBBB4/47CB4` | require actor `+0xB00==0`, state halfword `+0x18E==8`, actor `+0xA4C/+0xA50` flag gates; then resident `FUN_0021DDB0(actor)`, otherwise reset |
| `13` | `006FBC70/006FBCB0/47DB0` | switch on actor `+0xB00 & 0xFF00`; `0` resets, and `0x100/0x400/0x1000` reset then call `FUN_0021DDB0(actor)` |
| `14` | `006FB920/006FB960/47A60` | target `+0x18E==6` resets; otherwise query resident `FUN_00230CE0(target,-1)`, reset on success, or OR mask `0x1080` |
| `15` | `006FBA74/006FBAB4/47BB4` | actor `+0x190==0x60` calls live `FUN_006F8810`; `0x5D` emits `0x1000`; otherwise reset |
| `16` | `006FBAE4/006FBB24/47C24` | reset when slot `+0x94` is zero or actor `+0x18E` is 4/5; otherwise emit `0x1000` |
| `17` | `006FBA54/006FBA94/47B94` | call live `FUN_006FB0D0`, a selector/queue path |
| `18` | `006FBB64/006FBBA4/47CA4` | call live `FUN_006FA590` |
| `19` | `006FBBE8/006FBC28/47D28` | actor `+0xB00` high byte zero resets; `0x100/0x400` reset then `FUN_0021DDB0(actor)` |
| `20` | `006FBD3C/006FBD7C/47E7C` | reset unless target `+0x18E==8` or slot byte `+0x124` is nonzero; one Practice-only setting branch is outside this investigation's scope, otherwise resident `FUN_00229B70(actor,-2)` |
| `21` | `006FBEF4/006FBF34/48034` | resident `FUN_00306420(actor,10/11)` success resets; otherwise emit `8`, resetting when slot `+0x94` expires |
| `22` | `006FBFB8/006FBFF8/480F8` | emit `4`, reset when slot `+0x94` expires |
| `23` | `006FBE50/006FBE90/47F90` | resident `FUN_0021DF60(actor,1,0x02000000,-2)` chooses an index; if valid and no action is queued, queue it with `FUN_0021D380` |
| `24` | `006FBFF4/006FC034/48134` | call live `FUN_006F4C10`, which validates the mode-1 handle and maintains/replans its route |
| `25` | `006FC004/006FC044/48144` | call live `FUN_006F4F10` |
| `26` | `006FC1BC/006FC1FC/482FC` | call live `FUN_006F4260`, which refreshes the mode-2 point, enforces near/far deadlines, and maintains/replans its route |
| `27` | `006FC014/006FC054/48154` | decrement slot `+0x110`; on expiry reset, test live `FUN_006FC7F0(120.0)`, and on success set active, source mode 1, state 24, then invoke the route planner |
| `28` | `006FC12C/006FC16C/4826C` | call live `FUN_006F5CB0` |
| `29` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `30` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `31` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `32` | `006FC30C/006FC34C/4844C` | shared return; no action |
| `33` | `006FC170/006FC1B0/482B0` | actor `+0x190==0x5D` emits `0x00010000`; otherwise reset |
| `34` | `006FC13C/006FC17C/4827C` | reset, then emit `0x00010000` |
| `35` | `006FC1CC/006FC20C/4830C` | call live `FUN_006F4080` |
| `36` | `006FC1DC/006FC21C/4831C` | reset, then emit `0x00010000` |
| `37` | `006FC210/006FC250/48350` | call live `FUN_006F95B0`, another selector/queue path |
| `38` | `006FC220/006FC260/48360` | emit `0x20000000`; clear request latch `+0x90` when slot halfword `+0x150==2` |
| `39` | `006FC268/006FC2A8/483A8` | resident `FUN_00229B70(actor,-2)` |
| `40` | `006FC28C/006FC2CC/483CC` | emit `0x10000000` |
| `41` | `006FC2A8/006FC2E8/483E8` | emit `0x01000000` |
| `42` | `006FC2C4/006FC304/48404` | call the action selector with `(distance=0, mask=0, range=1..1, directional gate on)`, then queue the returned index with `FUN_0021D380` |

This table corrects the preserved decompiler's case mapping. Its switch used the
live table address in displayed space and therefore associated cases with bytes
`0x40` too late.

The numeric masks above can be related to the already-established configurable
input translator without assigning move names. With the native default bindings,
`0x00001000` is a newly pressed Circle binding, `0x00010000` Cross,
`0x01000000` Square, `0x20000000` R1, and held L2 or R2 produces the logical
guard bit `0x10000000`. Low bits `4` and `8` are opposite direction sectors;
`0x00040000` is a short-history Cross-plus-direction modifier rather than an
independent button. These mappings come from the shared command-controller
pipeline documented in `action_commands.md`; bindings remain user-configurable.

### Direct state constructors

A handler's presence does not prove that BTL ever selects it. Scanning direct
writes to slot `+0x34` in the corrected clean text gives this constructor map.
Entries are corrected **live** function starts; the global `D=L-0x40` and
`F=L-0x006B3F00` rules give their exact original symbols and file offsets.
Repeated writers inside one function are collapsed.

```text
state  direct BTL writer function(s)
 0     6F37B0 6F3F80 6F6080 6F63A0 6F7E70 6F8810 6F9180 6FAA50
       6FB840 6FDF30 7024A0 703170 704D40 705D70
 1     703170 703D20
 2     none found
 3     6F37B0 6FD970
 4     6F37B0 6F63A0
 5     6F37B0 6F5410 6FEAC0 7004B0 701140 7024A0 703170 703D20
 6     6FD970 6FEAC0 7004B0 701ED0 703D20
 7     700190
 8     6FD2D0 6FF9C0 7004B0 701140 701ED0 703D20
 9     6FAA50 6FB0D0 6FDF30
10     6F5410 6F9B20 6FD970 6FEAC0 6FF9C0 7004B0 701140 703170 703D20
11     6F5410 6F98C0 6FA590 6FDF30 6FEAC0 700190 7004B0 703170
       703A70 703D20 704D40
12     703D20
13     6FF650 (dynamic value selected from actor state flags)
14     703A70
15     703D20
16     6F5410 7004B0
17     6FDF30
18     6FB840 7004B0 701140 7024A0 703D20
19     6FF650 (dynamic value selected from actor state flags)
20     6FDF30 7004B0 701140
21     6FD2D0 701ED0 703D20
22     6F9B20 6FD2D0 700190 703D20
23     7004B0
24     6F4C10 6FB840 701BD0
25     6F5410 6F8810 6F9B20 6FD2D0 6FD970 6FDF30 7004B0 701BD0 703D20
26     6F4260 6FCE00
27     6F4260
28     6F8E50 6FD2D0 7004B0 703170
29     none found
30     none found
31     none found
32     none found
33     703D20
34     6FDF30 6FEAC0 701140
35     703D20
36     7024A0
37     7024A0
38     6FE720
39     6FEAC0
40     6FEAC0
41     6FEAC0
42     6FEAC0
```

`FUN_006FF650` selects state 13 for actor `+0xB00 & 0xFF00` values `0x1000`
or `0x400`, and state 19 for `0x100`, before applying the phase gate. No direct
constant constructor was found for state 2. More strongly, states 29 through
32 have neither a direct constructor nor an active handler in clean BTL; all
four table entries are the shared no-op return. External/aliased writes remain
possible, so state 2 is “untraced,” while 29..32 are best described as
apparently reserved under current static evidence.

## Action-record selection and direct queues

`FUN_006F2B40` scans the controlled fighter's action-record list and builds a
local array of eligible indices. Eligibility includes caller mask, record
range/category byte, distance threshold, fighter-state flags, and
live `FUN_006F26C0(record)` (`D/L/F 006F2680/006F26C0/3E7C0`). The local array
has 128 entries. No eligible record
returns `-1`; otherwise the call at
`D/L/F 006F2E6C/006F2EAC/3EFAC` selects by modulo as:

```text
eligible[(FUN_001801E0() ^ 0x80000000) % eligible_count]
```

The filter inputs are exact:

- it scans `s16 self+0xA38` records through resident
  `FUN_00217930(self,index)`;
- caller mask zero becomes default mask `0x000F000D`;
- caller range zero takes profile parameters 36 and 37 as the inclusive
  minimum/maximum for signed record byte `+0x19`;
- record word `+0x10` must intersect the selected mask;
- record float `+0x34` must be one of the sentinels `-17320.508`/`10000.0`, or
  must be at least the requested distance;
- record word `+0x1C` and signed fighter byte `+0x63` impose a directional
  eligibility gate;
- a nonzero fourth argument adds a 100-unit vertical-separation comparison;
- live `FUN_006F26C0` applies actor/target-state exclusions. In Practice,
  Attack Combo (`key 0x0D==2`) additionally rejects records with mask bits
  `0xF0000` or category zero. Its profile-parameter-15 random gate is skipped
  only for scripted Status Stand/Jump/Double-jump.

These are record-layout and branch facts, not names for the underlying moves.

The function returns the selected action-record index. For specially flagged
mapped actions, it calls live `FUN_00772870` and creates slot `+0x128` as a
percentage of that helper's result. Corrected control flow gives these exact
percentage ranges by spatial bucket:

| slot `+0x30` | bounded RNG | added base | percentage range |
| ---: | ---: | ---: | ---: |
| `0` | `0..30` | `10` | `10..40` |
| `1` | `0..40` | `20` | `20..60` |
| `2` | `0..50` | `30` | `30..80` |
| other | `0..60` | `40` | `40..100` |

The stored value is integer truncation of `mapped_value * percentage / 100`.

An exact raw-JAL scan finds 12 BTL calls to the selector's live entry:

```text
F       D          L          containing path
044E88  006F8D48   006F8D88   state-15 helper
044ED8  006F8D98   006F8DD8   state-15 helper
044F14  006F8DD4   006F8E14   state-15 helper
0457B4  006F9674   006F96B4   state-37 helper
0457D8  006F9698   006F96D8   state-37 helper
0458D4  006F9794   006F97D4   state-37 helper
0458FC  006F97BC   006F97FC   state-37 helper
047438  006FB2F8   006FB338   state-17 helper
047460  006FB320   006FB360   state-17 helper
047824  006FB6E4   006FB724   state-17 helper
048414  006FC2D4   006FC314   state-42 handler
04AFD4  006FEE94   006FEED4   reactive decision stage
```

An exact scan also finds 14 BTL calls to resident queue routine
`FUN_0021D380`:

```text
F       D          L
04077C  006F463C   006F467C
044B10  006F89D0   006F8A10
044C80  006F8B40   006F8B80
044E38  006F8CF8   006F8D38
044EA8  006F8D68   006F8DA8
044EEC  006F8DAC   006F8DEC
044F28  006F8DE8   006F8E28
0457EC  006F96AC   006F96EC
045978  006F9838   006F9878
0474C8  006FB388   006FB3C8
047844  006FB704   006FB744
048024  006FBEE4   006FBF24
048444  006FC304   006FC344
04B03C  006FEEFC   006FEF3C
```

The resident side establishes what “queue” means. `FUN_0021D250` at
runtime/file `0021D250/11D350` is a five-instruction predicate that returns
whether fighter halfword `+0xB34` is not `-1`. The queue reset helper
`FUN_0021D200` at runtime/file `0021D200/11D300` writes `-1` to `+0xB34` and
the four halfwords `+0xB36..+0xB3C`, writes zero to `+0xB3E`, and writes `-1`
to current-action halfword `+0xA3E`.

`FUN_0021D380` itself is resident runtime/file `0021D380/11D480`. It
sign-extends the requested index and rejects a negative value or a value above
fighter halfword `+0xA38`. It also returns zero while fighter byte `+0x61`
bit `0x80` is set, words `+0xB00` or halfword `+0xB10` are nonzero, the global
`0x00607654 -> +0x08 -> +0x14` gate is nonzero, or resident
`FUN_00239E50(fighter,0)` fails. The selected `0x54`-byte record is reached
through fighter pointer `+0xA54`; record word `+0x10` must be nonzero and must
exclude `0x02000000` and `0x0000F000`. Further record/fighter mode checks and
`FUN_00225940` enforce the action's resource requirement before installation.

On its normal success path the routine puts the requested index in `+0xB34`,
follows signed record byte `+0x18` as the next-record link for at most four
records, and writes each index into one of `+0xB36..+0xB3C` selected by signed
record byte `+0x19`; `+0xB3E` is reset to zero. A special fighter-state/record
flag path can instead replace current-action halfword `+0xA3E`. The function
returns one only after one of those installations, and zero on every admission
failure. Therefore state 42's unconditional call is safe when the selector
returns `-1`, and the resident layer remains the final authority even after a
BTL selector has chosen an index.

The queue is consumed by resident `FUN_0021DAE0` at runtime/file
`0021DAE0/11DBE0`. Its sole direct caller is logical-command interpreter
`FUN_0023A390` (`0023A390/13A490`), which has call sites
`00249414/149514` and `0024DB0C/14DC0C`. At the latter, resident bridge
`FUN_00217320` ran immediately before at `0024DAFC/14DBFC`. If queue root
`+0xB34` is not `-1`, `FUN_0023A390` calls the queue consumer and returns zero
instead of interpreting the supplied logical mask. A direct AI action queue
therefore has same-update precedence over the AI's command-mask path.

With phase `+0xB3E==0`, the consumer validates the fighter, starts slot
`+0xB36` through `FUN_0023A9A0(fighter,index,0)`, optionally installs
`+0xB38` as current action `+0xA3E`, and sets phase 2. Whenever `+0xA3E`
later becomes `-1`, it advances through `+0xB3A` and `+0xB3C`, incrementing
the phase. Fighter byte `+0x61` bit `0x80`, a failed admission predicate, an
exhausted/invalid slot, or leaving resident fighter state `+0x18E==8` clears
`+0xB34..+0xB3C`, `+0xB3E`, and `+0xA3E`. This proves the queue is a bounded
four-category action chain rather than an unbounded command FIFO.

State-15 live helper `FUN_006F8810` is representative: after target/context
gates and a no-action-queued test, it selects and queues an action-record index.
Special height branches instead ask resident `FUN_0021DF60` for an index using
masks `0x212`, `0x10A`, or `0x86`, then queue that result.

## Configuration and behavior profiles

Resident `FUN_001F6EA0(manager)` calls `FUN_001F6420(manager,0x0B)` and returns
its `v0` unchanged. The key-`0x0B` handler selects the manager settings block
appropriate to manager mode and returns its byte `+7`. This directly proves
that the BTL initializer's profile index is raw manager key `0x0B`, not a
transformed derivative.

The key is normalized to `0..5`. Count-table entry 10 is live
`0x008D18E8`, displayed bytes `0x008D18A8`, file `0x21D9E8`, and contains `6`.
`FUN_00881950` normally uses maximum `5`, but lowers it to `4` when resident
feature key `0x6A` is unavailable. Profile 5 is therefore unlock-gated.

The initializer indexes the profile table at
`D/L/F 008C31F0/008C3230/20F330` with stride `0x50` and copies 40 signed
16-bit values to slot `+0x160..+0x1AF`. Raw selectable rows, in parameter-index
order `0..39`, are:

```text
profile 0: 50,0,0,240,0,20,0,0,60,10,60,0,0,0,10,0,0,180,180,0,0,0,0,50,0,0,0,0,20,40,0,380,60,240,40,8,0,1,200,30
profile 1: 45,0,0,210,0,30,25,0,40,15,60,0,30,0,30,35,0,150,150,30,0,0,0,15,0,0,0,0,35,55,0,360,45,180,35,6,0,2,170,25
profile 2: 30,0,0,180,0,35,35,25,40,30,70,40,40,0,65,45,0,120,100,40,0,0,0,50,0,35,0,30,40,60,0,300,60,150,35,6,0,3,150,20
profile 3: 20,10,20,150,25,40,35,35,40,40,70,50,60,45,60,55,50,90,100,50,10,0,0,50,0,35,40,40,40,60,3,300,50,120,35,5,0,3,120,15
profile 4: 15,15,20,120,45,50,45,40,40,50,70,60,70,55,70,60,60,80,80,50,25,30,50,50,0,40,45,45,45,65,2,240,40,90,30,5,0,3,110,10
profile 5: 15,20,30,90,60,60,55,50,50,60,80,70,70,60,80,70,70,70,80,70,40,50,70,50,0,50,45,45,50,70,1,180,35,75,20,4,0,3,85,5
```

A seventh contiguous `0x50` row exists after profile 5, but the confirmed
normal key bound cannot select it. Its role is reserved or special and remains
unresolved; it must not be advertised as a seventh ordinary difficulty level.
Its exact location is `D/L/F 008C33D0/008C3410/20F510`, and its raw 40 values
are:

```text
15,30,35,60,80,65,70,60,50,70,90,80,80,70,90,80,80,60,80,80,
60,70,85,50,0,60,50,50,60,80,0,120,30,60,15,4,0,3,60,3
```

An aligned full-file scan found no absolute pointer to any individual profile
row and no code construction of row 6. The only constructions of table base
live `0x008C3230` are at file/live `0x510EC/0x00704FEC` (Practice hot reload)
and `0x52094/0x00705F94` (initializer); both add the accessor-provided index.
Under clean static evidence, therefore, row 6 is data without a confirmed
selector.

### Direct profile-parameter consumers

The following ledger transposes the six selectable rows and records only uses
that are direct in clean BTL text. Function addresses in this table are **live**
addresses from the corrected full-file import. For every reader `L`, the exact
preserved-export/original symbol is `FUN_(L-0x40)` and the file entry is
`F=L-0x006B3F00`; for example, live `FUN_006FCE00` is preserved
`FUN_006FCDC0`, file `0x48F00`. `P0..P5` means profile rows 0 through 5.

Most probability uses compare a profile value with
`FUN_00180210(100)`, whose result is inclusive `0..100`. A branch
`roll < value` accepts exactly the `value` result values `0..value-1` out of
the 101-value output domain; it is not a `value%` test. This document does not
call that an exact `value/101` probability because the wrapper uses modulo and
does not remove modulo bias. The ledger consequently says “0..100 threshold”
rather than “percent.”

| Index | Slot offset | P0/P1/P2/P3/P4/P5 | Direct structural use |
| ---: | ---: | --- | --- |
| 0 | `+0x160` | 50/45/30/20/15/15 | `0..100` gate in `L 0x006FCE00` before its environment-point scan can build a route and enter state 26. |
| 1 | `+0x162` | 0/0/0/10/15/20 | Contextual `0..100` threshold in `L 0x006FDF30`, `0x006FEAC0`, and `0x007004B0`. |
| 2 | `+0x164` | 0/0/0/20/20/30 | In `L 0x00701140`, an action-record scalar adjusts this `0..100` threshold before a transition to state 20. |
| 3 | `+0x166` | 240/210/180/150/120/90 | Countdown seed written to slot `+0x98`, `+0xD4`, or `+0xFC` by reactive paths in `L 0x006FDF30`, `0x006FEAC0`, `0x007004B0`, `0x00701140`, and `0x00703D20`. |
| 4 | `+0x168` | 0/0/0/25/45/60 | `0..100` threshold in `L 0x006FDF30` and `0x00703A70`. |
| 5 | `+0x16A` | 20/30/35/40/50/60 | Contextual probability magnitude in `L 0x006FEAC0`, `0x007004B0`, `0x00701140`, and `0x00703D20`; one `0x007004B0` path passes it to the ten-step phase gate. |
| 6 | `+0x16C` | 0/25/35/35/45/55 | Alternate ten-step phase-gate input in `L 0x007004B0`, selected for particular incoming-action classes. |
| 7 | `+0x16E` | 0/0/25/35/40/50 | Another incoming-action-class phase-gate input in `L 0x007004B0`. |
| 8 | `+0x170` | 60/40/40/40/40/50 | `0..100` threshold in `L 0x006F9B20`, `0x006FB0D0`, `0x006FEAC0`, `0x007004B0`, and `0x00701BD0`. |
| 9 | `+0x172` | 10/15/30/40/50/60 | `0..100` threshold in `L 0x00703A70` before state 14. |
| 10 | `+0x174` | 60/60/70/70/70/80 | `0..100` threshold in `L 0x006FB0D0`, `0x006FDF30`, `0x006FEAC0`, `0x007004B0`, and `0x00703170`. |
| 11 | `+0x176` | 0/0/40/50/60/70 | `L 0x006F33A0` divides it by 10 to select a ten-step pattern row; it is also a direct `0..100` threshold in `L 0x006FF650` and `0x00703D20`. |
| 12 | `+0x178` | 0/30/40/60/70/70 | `L 0x006FF650` writes `100-value` to slot countdown `+0xC0`. |
| 13 | `+0x17A` | 0/0/0/45/55/60 | `0..100` branch in `L 0x00701140` choosing state 10 instead of state 18 for one nearby-action reaction. |
| 14 | `+0x17C` | 10/30/65/60/70/80 | Common `0..100` threshold across `L 0x006F5410`, `0x006FA590`, `0x006FB0D0`, `0x006FDF30`, `0x006FEAC0`, `0x007004B0`, `0x00703170`, `0x00703A70`, and `0x00703D20`. |
| 15 | `+0x17E` | 0/35/45/55/60/70 | Practice-aware eligibility gate in `L 0x006F26C0`; also controls a masked action-family attempt in state-15 helper `L 0x006F8810`. |
| 16 | `+0x180` | 0/0/0/50/60/70 | `0..100` threshold for cached-action reuse in `L 0x006F8810` and another reactive branch in `L 0x006FDF30`. |
| 17 | `+0x182` | 180/150/120/90/80/70 | Reload value for slot countdown `+0x100` in `L 0x006F8810`. |
| 18 | `+0x184` | 180/150/100/100/80/80 | Reload value for slot countdown `+0xB4` in `L 0x006F8810`. |
| 19 | `+0x186` | 0/30/40/50/50/70 | `0..100` threshold in `L 0x00703D20`. |
| 20 | `+0x188` | 0/0/0/10/25/40 | `0..100` threshold in `L 0x006F9B20`, `0x006FD2D0`, `0x00700190`, and `0x00703D20`. |
| 21 | `+0x18A` | 0/0/0/0/30/50 | `0..100` threshold for state 38 in `L 0x006FE720` and for synthesized mask `0x20000000` in `L 0x006FF410`. |
| 22 | `+0x18C` | 0/0/0/0/50/70 | `0..100` threshold in `L 0x006FD970`, `0x006FEAC0`, `0x007004B0`, `0x00701ED0`, and `0x00703D20`. |
| 23 | `+0x18E` | 50/15/50/50/50/50 | `0..100` gate in `L 0x006FD2D0` before a target-side movement/state-8 reaction. |
| 24 | `+0x190` | 0/0/0/0/0/0 | No direct clean-BTL read found. Character flag mask `0x08` still applies its `x1.2` transform here, which is a no-op for all six selectable base rows. |
| 25 | `+0x192` | 0/0/35/35/40/50 | `0..100` gate in `L 0x006FFEC0`; on success that path resets and ORs synthesized mask `0x1000`. |
| 26 | `+0x194` | 0/0/0/40/45/45 | `0..100` gate in `L 0x006F9B20` before state 25 and its route helper. |
| 27 | `+0x196` | 0/0/30/40/45/45 | Post-dispatch `0..100` gate at `D/L/F 00705584/007055C4/516C4`; when the associated object's property has bit `0x100`, success writes `1` to object `+0x13C`. |
| 28 | `+0x198` | 20/35/40/40/45/50 | Widespread `0..100` threshold in `L 0x006F8810`, `0x006FEAC0`, `0x007004B0`, `0x00701BD0`, and `0x00703170`. |
| 29 | `+0x19A` | 40/55/60/60/65/70 | `0..100` gate in `L 0x007004B0`, `0x00701140`, and `0x00703D20`; one success invokes `L 0x006FD970`. |
| 30 | `+0x19C` | 0/0/0/3/2/1 | Inclusive bounded-RNG argument in `L 0x006FEAC0` and `0x007004B0`, used to seed short retry countdowns `+0xFC` and `+0x98`. |
| 31 | `+0x19E` | 380/360/300/300/240/180 | No direct clean-BTL load or absolute reference found. Unlike index 24 it carries meaningful-looking values, so its role is unresolved rather than presumed unused. |
| 32 | `+0x1A0` | 60/45/60/50/40/35 | General countdown seed written to slot `+0x94`, `+0x9C`, or `+0xAC` in `L 0x00703170` and `0x00703D20`. |
| 33 | `+0x1A2` | 240/180/150/120/90/75 | Countdown seed for slot `+0xD4` or `+0xE0` in `L 0x006FEAC0` and `0x007004B0`. |
| 34 | `+0x1A4` | 40/35/35/35/30/20 | State-1 countdown seed at slot `+0xD8` in `L 0x00703170`. |
| 35 | `+0x1A6` | 8/6/6/5/5/4 | In `L 0x006FFD50`, controls a directional randomized interval at slot `+0xE4`; the next value combines this base, `rand(0..base/2)`, and sometimes signed `rand(0..base)`. |
| 36 | `+0x1A8` | 0/0/0/0/0/0 | Default minimum allowed action-record category byte `+0x19` in selector `L 0x006F2B80`. |
| 37 | `+0x1AA` | 1/2/3/3/3/3 | Default maximum allowed action-record category byte `+0x19` in selector `L 0x006F2B80`. |
| 38 | `+0x1AC` | 200/170/150/120/110/85 | In `L 0x006FE720`, seeds slot `+0xF4` to `value + rand(0..value)` before another state-38 evaluation. |
| 39 | `+0x1AE` | 30/25/20/15/10/5 | In `L 0x006FF650`, seeds slot `+0xBC` to `value + rand(0..value)` on one state-19 reaction path. |

The two negative rows above were checked against both corrected decompiler
references and the full clean text disassembly. Index 31 has no direct
`lh/lhu/lw/lwu/ld/lq/lwc1` load using slot offset `0x19E`, and no absolute
formation of live `0x008D672E`; index 24 likewise has no identified profile
consumer. Indexed access through an unrecognized pointer cannot be excluded,
so neither field is assigned a semantic name.

The initializer then applies three other input layers:

- Unless manager mode is 2 or 3, an unidentified BTL predicate returns 1, or
  resident `FUN_001FDC30()` is nonpositive, values `1..10` from that resident
  scalar select rows `0..9` of a 10-by-40 signed-byte percentage matrix at
  `D/L/F 008C35A0/008C35E0/20F6E0`; values at least 11 clamp to row 9. Each
  profile value becomes `value + trunc(value * signed_percent / 100)`.
- Character flag byte `L 0x008C3052 + character_id*4`
  (`D/F 0x008C3012/0x20F152`) applies `x1.2`: mask `0x01` to profile offset
  `+0x20`, mask `0x04` to `+0x10`, and mask `0x08` to `+0x30`.
- The normalizer at `D/L/F 00705770/007057B0/518B0` replaces negative
  selected parameters with exact per-index defaults: `p1=40`, `p2=40`,
  `p5=80`, `p8=90`, `p9=80`, `p10=80`, `p11=80`, `p12=80`, `p14=90`,
  `p15=70`, `p16=70`, and `p18=150`. Other indices are not normalized there.

The secondary matrix is below in parameter-index order `0..39`:

```text
row 0: -3,-5,-6,3,-3,-5,-5,-5,-3,-3,-3,-3,-3,-3,-3,-3,-3,5,5,-3,-3,-8,-10,0,-3,-3,-3,-3,-3,-3,5,3,5,0,0,5,0,0,5,0
row 1: -8,-9,-10,8,-8,-10,-10,-10,-8,-8,-4,-5,-8,-8,-8,-8,-8,10,10,-8,-8,-15,-15,0,-8,-8,-8,-8,-8,-8,8,5,10,5,3,10,0,0,10,5
row 2: -15,-14,-15,12,-12,-15,-15,-15,-10,-12,-8,-10,-10,-12,-12,-12,-12,15,15,-12,-12,-20,-20,-10,-8,-8,-8,-8,-8,-8,12,15,10,10,8,15,0,0,15,10
row 3: -20,-18,-20,18,-18,-20,-20,-20,-15,-16,-13,-14,-14,-18,-18,-18,-18,20,20,-18,-18,-25,-25,-10,-14,-14,-14,-14,-14,-14,18,20,15,15,10,20,0,0,15,15
row 4: -30,-22,-25,25,-25,-25,-35,-35,-20,-20,-18,-18,-18,-25,-25,-25,-25,25,25,-25,-25,-30,-30,-15,-20,-20,-20,-20,-20,-20,20,30,20,15,15,25,0,0,20,20
row 5: -40,-28,-30,30,-30,-30,-35,-35,-25,-24,-24,-20,-20,-30,-30,-30,-30,30,30,-30,-30,-40,-35,-15,-20,-20,-20,-20,-20,-20,25,35,25,20,20,30,0,0,20,25
row 6: -50,-34,-35,35,-35,-35,-40,-40,-25,-28,-28,-24,-24,-35,-35,-35,-35,35,35,-35,-35,-50,-35,-20,-20,-20,-20,-20,-20,-20,30,35,30,25,20,35,0,0,25,30
row 7: -60,-39,-40,40,-40,-40,-45,-45,-30,-32,-30,-28,-28,-40,-40,-40,-40,40,40,-40,-40,-55,-40,-20,-25,-25,-25,-25,-25,-25,35,35,30,30,25,40,0,0,25,35
row 8: -70,-45,-45,45,-45,-45,-45,-45,-30,-36,-30,-32,-32,-45,-45,-45,-45,45,45,-45,-45,-65,-45,-30,-25,-25,-25,-25,-25,-25,40,40,35,35,30,45,0,0,30,40
row 9: -80,-50,-50,50,-50,-50,-50,-50,-35,-40,-30,-35,-35,-50,-50,-50,-50,50,50,-50,-50,-70,-50,-30,-30,-30,-30,-30,-30,-30,45,40,35,35,35,50,0,0,30,45
```

Resident `FUN_001FDC30` is only `lw v0,-0x335C(gp); return`. The clean ELF
`.reginfo` value is `gp=0x0060A9F0`, placing the counter at resident BSS
`0x00607694`; it has no file offset. Its source is the resident continue flow:

- `FUN_001FED10` (runtime/file `001FED10/0FEE10`) allocates a `0x3C`-byte
  object and initializes it through `FUN_001FBA30` (`001FBA30/0FBB30`), whose
  resource lookup is the literal string `"continue"` at runtime/file
  `00406AA0/306BA0`;
- when that object completes, its result word `+0x08` values `0` and `2`
  increment `0x00607694`, while value `1` does not;
- `FUN_001FE300` and `FUN_001FE390` clear the counter during construction and
  teardown of the surrounding resident flow. No other clean resident writes
  were found.

This establishes a continue-screen completion counter whose exact incrementing
choice labels remain unresolved. It is the scalar that chooses the ten
percentage rows above; it is not the ordinary Strength key and should not be
called a global difficulty setting.

The BTL predicate that can bypass this modifier is now structurally bounded as
well. `D/L/F 006EE510/006EE550/3A650` merely returns a BTL global byte. The byte
is set to 1 by `D/L/F 006EED90/006EEDD0/3AED0` when a setup object whose mode
field `+0x0C` equals 2 creates a resident session object; it is cleared by the
mode-2 completion path in `D/L/F 006EEEE0/006EEF20/3B020`. The initializer's
test is at `D/L/F 00706014/00706054/52154`. This proves a session-backed-mode
exclusion but still does not establish a safe player-facing mode name.

In manager mode `+0x0C==3` (Practice), the main tick detects a changed key
`0x0B` and hot-copies the new raw `0x50` row. This hot reload does not rerun the
secondary percentage modifier, character multipliers, normalizer, two-slot
reset, or initializer-only randomized timers.

## RNG ownership and confirmed uses

Resident `FUN_0017FD90` is the core PRNG. Its state and recurrence identify it
as MT19937 with project-specific seeding:

- 624 32-bit algorithm values stored in eight-byte EE slots at resident BSS
  `0x00617640`, indexed by the word at `0x00602A28`;
- the standard 397-word twist offset, high/low masks
  `0x80000000/0x7FFFFFFF`, and odd-word matrix constant `0x9908B0DF` from
  runtime/file `003FB3D0/2FB4D0`;
- the standard output tempering shifts `11,7,15,18` and masks
  `0x9D2C5680/0xEFC60000`;
- the default state-fill path starts from `0x1100` and repeatedly applies
  `value = value * 0x10DCD + 1`, packing successive high halves, rather than
  using MT19937's reference seed-expansion formula.

Resident wrappers are:

```text
FUN_001801E0()      -> raw PRNG value
FUN_00180210(bound) -> (raw ^ 0x80000000) % (abs(bound) + 1)
```

The bounded result is inclusive `0..abs(bound)`. Confirmed AI uses include:

- modulo selection among filtered action records, described above;
- special-action cooldown percentage generation, described above;
- both-slot initialization timer slot `+0xB4 = 150 + rand(0..120)`;
- a ten-step phase gate rather than an independent Bernoulli roll on every
  evaluation;
- a paired-AI branch in the main tick that, under a specific both-controlled,
  both-state-5, differing-region condition, tests `rand(0..100) < 20`, then
  uses `rand(0..1)` to reset one of the two slots. A deadlock/stalemate-breaker
  purpose is plausible but remains a hypothesis.

This state is shared game-wide, not stored per AI side. BTL has no local PRNG
state: every confirmed AI call enters the resident wrappers above, and many
non-AI resident paths call the same wrappers. Resident initializer
`FUN_00180060` has direct call sites at runtime/file
`001E11B4/0E12B4` and `001F4378/0F4478`. The former lies in
`FUN_001E0EE0`, immediately after `FUN_001801A0` loads seed word
`0x00602A20` from the resident global controller's `+0x194`; the latter lies in
manager initializer `FUN_001F4360`. `FUN_00180060` rebuilds all 624 slots,
sets index `0x00602A28` to 624, advances the stream according to low seed bits,
and writes back another raw result as the next seed. Consequently AI results
depend on the shared call order, including intervening non-AI consumers; equal
AI slot contents alone do not imply the same next decision.

An exact aligned-JAL audit of the identified AI cluster from live
`0x006F0000..0x00706500` finds **167** direct RNG-wrapper calls: 10 raw calls to
`FUN_001801E0` and 157 inclusive-bounded calls to `FUN_00180210`. Counts by
corrected live containing function are:

```text
function       raw  bounded    function       raw  bounded
006F26C0         0      1      006F2B80         1      4
006F3140         2      0      006F33A0         2      0
006F4F10         0      1      006F5410         0      4
006F8810         0      3      006F98C0         0      3
006F9B20         4      7      006FA590         0      2
006FB0D0         0      9      006FC480         0      1
006FCE00         0      3      006FD2D0         0      4
006FD970         0      3      006FDF30         0      9
006FE720         0      3      006FEAC0         0     19
006FF410         0      4      006FF650         0      2
006FFD50         0      3      006FFEC0         0      3
00700190         0      4      007004B0         0     14
00701140         0      4      00701BD0         0      2
00701ED0         0      7      00703170         1      5
00703A70         0      5      00703D20         0     23
00704D40         0      4      00705D70         0      1
```

The ten raw call sites and their exact mappings are:

```text
F       D          L          established use
03EFAC  006F2E6C   006F2EAC   modulo eligible-action selection
03F3E8  006F32A8   006F32E8   phase-cursor seed/reseed modulo 10
03F424  006F32E4   006F3324   phase-cursor seed/reseed modulo 10
03F5AC  006F346C   006F34AC   second phase-cursor seed/reseed modulo 10
03F5E8  006F34A8   006F34E8   second phase-cursor seed/reseed modulo 10
046108  006F9FC8   006FA008   five-way behavior branch
04631C  006FA1DC   006FA21C   five-way behavior branch
0464FC  006FA3BC   006FA3FC   five-way behavior branch
046618  006FA4D8   006FA518   five-way behavior branch
04FA58  00703918   00703958   twenty-way branch in `FUN_00703170`
```

All four `FUN_006F9B20` raw results are reduced modulo 5. The
`FUN_00703170` result is reduced modulo 20; cases 0 through 5 take one branch
and the other 14 values take the default branch. This audit also shows that RNG
is pervasive in decision stages even though primary fighter-target ownership
is deterministic.

The ten-step phase helper is `D/L/F 006F3100/006F3140/3F240`. Its sole direct
caller is `D/L/F 00700BC8/00700C08/4CD08` inside
`D/L/F 00700470/007004B0/4C5B0`. It buckets integer input divided by 10, selects
one of cursors `+0x1B4/+0x1B8/+0x1BC`, seeds a `-1` cursor or reseeds at wrap
with raw RNG modulo 10, otherwise advances it deterministically, and reads a
boolean from `D/L/F 008C3190/008C31D0/20F2D0`:

```text
row 0: 0 1 0 0 0 1 0 0 0 0
row 1: 0 1 0 0 0 1 0 1 0 0
row 2: 0 1 0 1 0 1 0 1 0 0
row 3: 0 1 0 0 1 1 0 1 0 1
row 4: 0 1 0 1 1 1 0 1 0 1
row 5: 0 1 1 1 1 1 0 1 0 1
```

Its raw RNG call sites are
`D/L/F 006F32A8/006F32E8/3F3E8` and
`006F32E4/006F3324/3F424`. A positive result contributes to a transition to
raw state `0x12`, sets request latch `+0x90=1`, and timer `+0x94=30`. The exact
action name is unresolved.

A second consumer of the same six-row, ten-column boolean table is
`D/L/F 006F3360/006F33A0/3F4A0`. It takes Strength-profile parameter 11
implicitly rather than a function argument and chooses table row/cursor as:

```text
floor(parameter11 / 10)  table row  cursor
0..1                     0          +0x1B4
2..3                     1          +0x1B4
4..5                     2          +0x1B4
6..7                     4          +0x1B8
8 or greater             5          +0x1BC
```

It seeds, advances, and wraps the cursor exactly like `FUN_006F3140`. Its sole
direct call is `D/L/F 006FF92C/006FF96C/4BA6C` in
`D/L/F 006FF610/006FF650/4B750`, the Extra Hit Counter response selector.
For the Normal setting, response flag families choose candidate state 13 or
19, apply their cooldown/probability gates, and commit the candidate only when
this phase helper's current table cell is nonzero. Practice setting Always
return bypasses the phase helper and commits the candidate immediately after
clearing the corresponding cooldown. Thus the three phase cursors are shared
across at least two distinct reaction-selection paths.

An important corrected negative is preserved `FUN_006F1020`
(`D/L/F 006F1020/006F1060/3D160`): it is not an RNG helper. It maps a target
action-record byte in `-3..3` to floats from `-0.5` through `+0.5`. The skewed
decompiler had incorrectly merged it with a later RNG function.

## Evidence limits, negative results, and hypotheses

Confirmed negative results:

- No BTL ASCII class identifier contains `AI`, `CPU`, `brain`, or `think`;
  identification is structural. Relevant named strings include
  `ccCommandCtrl`, not an AI-specific class name.
- There is no BTL-internal call to the main tick. Resident character wrappers
  own 74 direct calls.
- There is no direct BTL call to the settings-apply entry.
- Ordinary primary-opponent binding performs no search and uses no RNG.
- COM disable performs no state reset, destructor, free, or deallocation.
- No AI heap allocation was identified; the two state blocks are static BSS.
- Physical controller-button names for command-mask bits have not been proven.
- State IDs have not been assigned behavior names beyond direct handler effects.
- This investigation did not execute an AI runtime trace. Runtime field labels
  cited above come from established resident producers or loader/savestate
  mapping, while state transitions and calls come from clean static code.

Useful hypotheses, kept separate from established facts:

- the conditional random reset of one of two AI slots likely prevents a
  two-controller stalemate;
- the seventh contiguous profile row is likely reserved for a special mode or
  inaccessible tier, but no confirmed caller selects it;
- the continue-screen counter drives a progressively stronger signed profile
  adjustment, but whether its design intent is specifically adaptive easing is
  an inference; the exact labels for result values 0/1/2 remain unresolved.
