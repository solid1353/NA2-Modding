# Battle damage

Native character durability, effective HP, combo state, and damage-calculation
paths in clean NA2.

## Research coverage

- **Assigned scope:** how accepted combo hits reach the
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
- **Deliberate exclusions and overlap:** combo-damage design belongs to
  [`combo_damage_scaling.md`](../../designs/combo_damage_scaling.md). Collision,
  stage data, Practice selection, starting HP, awakening, support, and status
  are separate research scopes and were not re-investigated here.
- **Evidence limitations:** static conclusions use the read-only clean resident
  ELF identified in
  [Standard game file identities](../game/files/file_identities.md); there
  is no original game source. Runtime conclusions are bounded to the
  named deterministic Practice sequence and transient probes. Captured heap addresses are allocation-specific,
  marker snapshots observe selected frames rather than every intermediate
  state, and static reachability alone is not evidence that an unobserved
  caller executes in ordinary play.

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

Evidence was extracted from the clean resident ELF identified above and checked
against the copied fighter records in both immutable Practice captures. Record
addresses in the resource table are EE virtual addresses.

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

The maintained
[deterministic controller stream](../../../pcsx2_files/input_recordings/damage_scaling.p2m2)
contains 3,619 input frames and 13 actionable rising edges of the `L3+R3`
marker chord. Its Practice setup selects Sakura (ID `58`), No Support
(`0x25`), and no starting effect.

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

The stream has 3,620 records of 36 bytes, including the format's all-zero frame
zero. Controller 2 remains neutral; Controller 1's analog bytes remain centered
and every pressure-capable digital press has the corresponding full-pressure
byte. The actionable input is reproduced by these inclusive frame runs; all
buttons not named for a frame are released and all unlisted frames are neutral
except for overlaps among the listed runs:

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

Synchronized screenshots and runtime memory establish this timeline:

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

### Damage caller coverage

The runtime-confirmed main call for this movie is from
`FUN_002346b0` to `FUN_00224e30` at runtime `0x00234A80`, ELF offset
`0x134B80`, using the established `runtime = ELF offset + 0xFFF00` mapping.
Clean `SLPS_258.37` contains instruction bytes `8C93080C` there, the
little-endian encoding of `jal FUN_00224e30`.

`FUN_00224e30` is shared by ten static call sites. Their bounded roles and the
movie's observed call counts are:

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

`FUN_00225050` is broader still and loses the attack flags and
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
  plus a runtime call-site trace before their paths can be included or
excluded. The fixed `0.04` sibling is at runtime `0x00231634`, ELF offset
`0x131734`, with the same clean `jal` bytes `8C93080C`. A general
  complete ordinary/contact coverage claim must include it after a natural
  positive capture; otherwise coverage remains limited to the two paths
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

A stage-only control loaded slot 7 and traced runtime `0x00231634` across all
13 checkpoints. It found 395 active environment primitives, including two with
runtime flags `0x40959595`, the orientation-augmented form of the authored
`0x00959595`; the call count remained zero.

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

A focused trace of runtime `0x00228D18` recorded zero calls while the HP
timeline matched the synchronized baseline.

A positive-control replay then redirected all ten clean calculator call sites
through one resident logger and retained native behavior.
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
active instrumentation and positive counts rule out a code-cache artifact: runtime
`0x00228D18` is conclusively uninvoked by this movie, while `0x00234A80` is its
observed normal-string main path. Events 7 through 9 occur around the later
reset demonstrations; their exact relationship to marker timing requires the
focused call-boundary state probe rather than inference from equal marker HP.

The focused replay then hooked only runtime `0x00234A80` and `0x00231698` and
logged each call before and after the original calculator.
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

Across all 13 checkpoints, the focused trace matched baseline HP and native
current/record counts. It preserved calculator behavior while establishing the
input state, native return value, manager ownership, and reset behavior at the
exact call boundary.

All static claims above come from the same read-only clean resident ELF.
The combo object layout, reset sequence, HP timeline, main and secondary damage
call sites, and hit-index formula are additionally runtime-confirmed by
synchronized replays. Coverage outside this Sakura normal string remains open.
