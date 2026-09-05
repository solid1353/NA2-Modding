# Substitution Knowledge

This document records the confirmed substitution-cost mechanism and durable
findings from the substitution-reliability investigations. It preserves the
established behavior, tested negative results, and control-flow boundary so they
are not investigated again without new evidence.

## Research coverage

- **Assigned scope:** this investigation covers native substitution cost,
  reliability, timing, reset, and HUD ownership. It also records the emulator
  control used to exercise the game without input recordings.

- **Exploration depth:** static coverage is exhaustive within the identified
  reliability surface: the complete control flow of `FUN_00229130`, all four
  direct clean-ELF call sites, its input-history, eligibility, response,
  resource, flag-conversion, and RNG paths, and the separate temporary-effect-
  ID-`9` route were traced. All 74 primary and four structurally proven
  auxiliary action-table owners were enumerated: 3,444 records in total,
  including all 1,065 admitted Command Chart mappings and their 1,110 record
  instances. Exact mapping multiplicity and mixed-profile titles were checked,
  and a targeted direct-writer audit identified the six records whose live
  timing can be replaced by fighter callbacks. Coverage outside those bounded
  tables, calls, and writers was gap-oriented rather than a whole-program
  semantic classification.

- **Confirmed coverage:** the signed `+0x1A` timing semantics, positive history
  windows, exact negative modulo probabilities, `+0x10` zero-to-negative
  conversion, earlier `+0x14` rejection flags, response whitelist, guard-edge
  and age requirements, resource checks, owner/index recovery, and Command
  Chart name join are established. The document distinguishes deterministic
  window admission from guaranteed substitution and records the narrow per-
  record, runtime-writer, all-table, and central-normalization control choices.
  The no-recording runtime foundation is also covered: the 18-byte DS2 state
  contract, PINE set/step/get/release operations, exact-frame stepping evidence,
  neutralization behavior, catalog-to-live telemetry, and one autonomous Naruto
  attack plus defender guard-edge probe. The native battle clock, battle reset
  seam, support-gauge renderer, fill palette, shared top-HUD layout, and failed
  custom-HUD placement and tint experiments are also established.

- **Unresolved or untested:** the gameplay roles and predicate reachability of 298
  exceptional unnamed records remain unclassified. The negative-timing
  probabilities have not been measured as runtime distributions, every named,
  auxiliary, and callback-mutated record has not been exercised in battle, and
  the full gameplay meaning of the live tier fields used by some timing writers
  remains only partially resolved. Callback cadence, complete
  new-battle reset coverage, cinematic clock suppression, COM behavior at zero
  resource, and final HUD composition remain unconfirmed at runtime.

- **Deliberate exclusions and overlap:** the already established substitution-cost
  mechanism is retained only to separate cost from reliability. Hit-response,
  status-effect, controller-input, and action-command internals remain with
  their own canonical documents except where a direct substitution gate
  required the connection. Item ID `9` is not conflated with temporary effect
  ID `9`; only the latter's Kurenai-specific substitution route is in scope.
  Practice/free-battle navigation, broad legacy dispatcher hacks, recordings,
  and implementation of the three known PCSX2 lifecycle hardening items were
  deliberately excluded.

- **Evidence limitations:** static conclusions use the hash-pinned clean
  `SLPS_258.37`, raw bytes, and preserved read-only Ghidra exports; `FUN_*`
  names are local generated labels, and a table entry does not itself prove
  gameplay reachability. The catalog represents clean templates plus the six
  confirmed direct timing-writer families, not every possible indirect live
  mutation. The runtime evidence is a bounded Practice sample whose defender
  was CPU-controlled, not a roster-wide campaign; it used neither an input
  recording nor a runtime memory patch. Agent experiments additionally require
  an already paused, agent-capable PCSX2 build and remain subject to the
  documented in-flight-step, PINE-reload, and legacy-packet lifecycle caveats.
  The HUD color branches and one-call reset coverage remain statically
  established rather than runtime-confirmed.

## Stable references

- Target: *Naruto Shippuuden: Narutimate Accel 2*, `SLPS-25837`, boot ELF
  `SLPS_258.37`.
- Clean source and address convention:
  [Standard game file identities](../game/files/file_identities.md).
- Historical NA2 decompiler/Ghidra evidence remains available through Git
  history. Restore reusable analysis only under `@disassembly/NA2/`.
- Native substitution-cost site: ELF offset `0x1299BC` (legacy evidence ID
  `ELF-S001`).

Function names below are Ghidra-generated names for the NA2 boot ELF and are stable only within the preserved analysis project.

## Substitution-cost mechanism

Clean bytes and the maintained Ghidra export confirmed this mechanism. At EE
address `0x202298BC` / ELF file offset `0x1299BC`,
`FUN_002297d0` contains `lui v0, 0x3F80`, represented by little-endian
instruction bytes `80 3F 02 3C`. The function moves the resulting float32
`1.0` to `f0`, subtracts it from the object's `+0x70` float field, and clamps
the result to zero.

Quarter-step costs from 0 through 15 have exact IEEE-754 float32 encodings whose
low 16 bits are zero. The existing `lui` can therefore represent every value in
that stepped range by changing only its immediate while preserving its opcode
and destination register.

| Cost | LUI immediate | Complete instruction bytes |
| ---: | ---: | --- |
| 1 | `0x3F80` | `803F023C` |
| 3 | `0x4040` | `4040023C` |
| 5 | `0x40A0` | `A040023C` |
| 15 | `0x4170` | `7041023C` |

The historical 16-bit PNACH experiment changed the immediate bytes from
`80 3F` to `40 40`, making the decrement cost `3`; that result is
runtime-proven. The clean instruction supplies native cost `1.0`.

The instruction site, float encoding, and decrement mechanism are confirmed,
not hypotheses. Cost `3` is runtime-proven. Substitution cost is not the
substitution-reliability gate.

## Native gauge and HUD boundaries

### HP, battle-clock, and reset ownership

Normalized HP is stored at `fighter+0x6C`. The shared fighter-update path
contains a native call at raw `0x14DB8C..0x14DB93`; immediately afterward,
`fighter+0x20C` is checked as the actor hit-stop/pause counter. Sampling HP at
this cadence is idempotent when HP is unchanged, but the seam is not an
independent recovery clock.

The running battle controller calls its countdown accumulator only after
scheduler suppression has been recomputed and the battle-state gates pass. At
virtual `0x001F11B8` / raw ELF `0x0F12B8`, it calls
`FUN_001EBA80(0x006B28D0)`. Timer flags have distinct native roles:

| Mask | Native meaning |
| ---: | --- |
| `0x01` | scheduler suppression |
| `0x02` | countdown freeze, including Unlimited battle time |
| `0x04` | expired or terminal timer state |

System-context byte `+0x01` is the display-count increment; native battle uses
`2`. System-context `+0x194` is the engine-update ordinal incremented by
`FUN_001081B0`; zero is valid and the counter can wrap. `FUN_00307230` is a
status-effect scalar used by chakra regeneration, not a time source.

`FUN_001EF330`, virtual `0x001EF330` / raw ELF `0x0EF430`, constructs the
battle graph when controller `+0x18` is null and publishes fighter pointers at
manager `+0xDE4/+0xDE8`. Teardown clears those fields, destroys the bundle, and
nulls the controller pointer. The call at virtual `0x001EF41C` / raw
`0x0EF51C` occurs after both fighters are published and is a candidate
once-per-new-battle observation seam; one-call coverage remains unconfirmed.


### Native HUD ownership

The per-side support-gauge wrapper first calls its native update, tests byte
`+0x0A`, and calls `TEX_xgauge` only when that byte is nonzero. The
complete-file update and draw calls are BTL `0x69380/0x69398`; exported
addresses are `0x0071D240/0x0071D258`.

| Controller field | Native role |
| ---: | --- |
| `+0x00` | side index |
| `+0x04` | fighter pointer |
| `+0x0A` | visibility state |
| `+0x0B` | fill/animation state |
| `+0x0C` | normalized support fill |
| `+0x10` | prior fill |
| `+0x18` | primary support-gauge render object |

The native update copies fighter support value `+0x74` into controller
`+0x0C`. The draw scales a 64-unit foreground by that value. Its side bases are
`120.0/392.0` with shared Y `340.0`. The red marker is fixed at half bar: the
fill begins at `20.0`, spans `64.0`, and the marker uses `52.0`.

At Ghidra `0x0071CF5C..0x0071CF60`, `lui v0,0x40` followed by
`ld a0,-0x4038(v0)` reads resident `0x003FBFC8`: the load displacement is
signed, so the effective address is `0x00400000 - 0x4038`. Clean ELF bytes
there are `80 80 80 80 00 00 00 00`. The packing sequence through Ghidra
`0x0071CF9C` uses only the first three bytes as RGB `(0x80,0x80,0x80)` and
preserves the sprite's Q field; it does not copy the fourth byte to alpha.
This neutral tint preserves the marker texture's own color.

The marker calls resident rectangle helper `0x0037BC40`. Its scaled counterpart
`0x0037BD00` changes destination dimensions and centering using the supplied
scales. Both set the same source rectangle/mode, preserve RGB and alpha, and
submit through `0x001CC350`; neither supplies a different marker tint or
texture. These helper bodies and the resident color bytes were checked through
GhidrAssist.

The fill tint is selected independently from the marker. In normal controller
state (`+0x0A == 1`), the update assigns color index `+0x0B` from the half-gauge
eligibility result and the full-gauge comparison:

| Fill condition | Index | Native RGB tint |
| --- | ---: | --- |
| Below `0.5` | `0` | `(0x1E, 0x64, 0x78)` |
| At least `0.5`, below `1.0` | `1` | `(0x7F, 0x50, 0x32)` |
| At least `1.0` | `2` | `(0x7F, 0x78, 0x32)` |

Controller state `+0x0A == 2` overrides the indexed tint with
`(0x7F, 0x00, 0x00)`. The four packed colors are at live BTL `0x00899DD0`,
Ghidra `0x00899D90`, complete-file `0x1E5ED0`:
`1E 64 78 FF 7F 50 32 FF 7F 78 32 FF 7F 00 00 FF`.
The draw loads this palette at Ghidra `0x0071CD5C..0x0071CD88`, selects by
`+0x0B` at `0x0071CE44..0x0071CE94`, and applies the state-2 override at
`0x0071CE98..0x0071CEDC` before committing the fill sprite.
Before the foreground, Ghidra `0x0071CD90..0x0071CE40` draws the full-width
inner background with RGB `(0x7F,0x7F,0x7F)`. Palette packing changes only RGB;
the sprite retains its existing alpha and Q.

The update's threshold helper is live BTL `0x0071C970`, Ghidra `0x0071C930`.
It calls resident `0x002381E0`, which returns whether fighter `+0x74` is at
least `0.5`; the update then compares controller `+0x0C` with `1.0` to choose
index `1` or `2`. These instructions and palette bytes were read through
GhidrAssist. The resident helper lacks a defined Ghidra function, so its
comparison was checked from the MCP byte view at `0x002381E0..0x00238208`.

The per-side top-HUD dispatcher begins at BTL raw `0x673E0`. Parent byte
`+0x54` gates all child draws. Its primary child layout stores X, Y, scale, and
side at `+0x00/+0x04/+0x08/+0x0C`; both the HP/chakra and character-name
renderers consume those fields. Slide and Ultimate-Jutsu shake are shared
parent transforms, not component-local state.

The character-name renderer begins at BTL raw `0x67F20`.
`0x67F60..0x67F67` loads its Y anchor, and `0x67F68..0x67F6F` performs native
Y-scale multiplication and loads the side byte.

### Gauge HUD experiments

Drawing the custom gauge from the BTL `0x69380` support-controller update hook
did not follow the top-HUD lifecycle: it remained visible while ordinary Jutsu
hid HP and chakra, then disappeared while Ultimate Jutsu retained the ordinary
top HUD. Moving the draw below the parent visibility gate fixed visibility, but
fixed coordinates still failed to follow the shared slide-off and
Ultimate-Jutsu shake.

A raw 1244x933 capture measured the first test frame at `x=197..399,
y=147..181`; the normalized reference was approximately `x=198..401,
y=113..148`. After the first vertical correction, another capture placed the
frame 4–5 pixels above the reference and the name about 13 pixels above it. The
pair measured roughly 2.43 pixels per bar unit and 2.5 pixels per name-anchor
unit. These captures constrain placement but do not validate the current HUD
offsets.

An early marker-color experiment used dark-red RGB `(0x12,0,0)` from an
incorrectly decoded address. The signed load displacement instead resolves to
the native neutral tint `(0x80,0x80,0x80)`.

Static evidence does not establish callback cadence, complete new-battle reset
coverage, cinematic clock suppression, COM behavior at zero resource, or final
HUD composition. Those remain runtime-validation questions.

## Runtime tests that did not improve reliability

Three temporary EE branch edits were tested and then disabled:

| EE address | Test | Result | Durable conclusion |
| --- | --- | --- | --- |
| `0x201917A8`, `0x20191C80` | Force the internal `0x800` action-flag consumer path | Black screen | These branches protect packet/action setup. Do not bypass them without a narrow, proven context guard. |
| `0x20190FEC` | Ignore the `0.0078125` impact threshold | No difference | The small-impact threshold in `FUN_00190f40` was not the observed reliability gate. |
| `0x20190FD4` | Allow the primary action path outside mode bits `== 3` | No difference | The mode-bit gate near this address was not the observed reliability gate. |

The first test appears to call `FUN_001921c0` with invalid context. These results constrain future work; they do not prove that the affected code is irrelevant in every state.

## Confirmed substitution-reliability gate

Static tracing identified `FUN_00229130` at boot-ELF virtual
address `0x00229130` / file offset `0x129230` as the substitution acceptance
predicate. The boot ELF has exactly four physical calls to it, at
`0x0021F7D8`, `0x0021F81C`, `0x00220B28`, and `0x00220CE4`. The nearby
addresses `0x0021F7F4`, `0x0021F838`, `0x00220B44`, and `0x00220D18` are the
four resulting calls to `FUN_002297D0`, the confirmed resource-decrement and
substitution-transition function; they are not predicate call sites.

| Caller/branch | Predicate arguments that vary | Commit after success |
| --- | --- | --- |
| `FUN_0021F610`, temporary-effect-9 attempt | selector `0` with response `6`, or selector `5` with `FUN_00231C60` response; resource validation `0` | `FUN_002297D0(fighter, 0x211, 0)` at `0x0021F7F4` |
| `FUN_0021F610`, ordinary/fallback attempt | same definition, selector, and response; resource validation `1` | `FUN_002297D0(fighter, 0x11, 1)` at `0x0021F838` |
| `FUN_002209A0`, dispatcher branch `param_2 == 2` | selector `5`; `FUN_00231C60` response; resource validation `1` | `FUN_002297D0(fighter, 0x41, 1)` at `0x00220B44` |
| `FUN_002209A0`, dispatcher branch `param_2 == 1` | selector `5`; `FUN_00231C60` response; resource validation `1` | `FUN_002297D0(fighter, 0x21, 1)` at `0x00220D18` |

Every one of those four commits requires a nonzero result from its immediately
preceding predicate call. `FUN_00236C70` has a separate fifth physical commit
call at `0x00236D74` for item/status ID `9`; as documented below, that path does
not call the predicate. The four clean predicate call sites pass selector `0`
or `5`, never `8`; the predicate's selector-`8` rejection is therefore a
defensive/general gate rather than an active choice at those direct stock
callers. This establishes the predicate as the shared upstream reliability
gate for the ordinary hit-dispatch routes without conflating the separate item
commit.

### Input path and history

The BTL input translator `FUN_006efd80` builds a logical action mask at input
object `+0xAC`. `FUN_00217320` copies that mask to fighter `+0x338`, the analog
magnitude at input `+0xB0` to fighter `+0x33C`, and the directional value at
input `+0xB4` to fighter `+0x340`. The two configurable physical guard bindings
are input-map entries 6 and 7, stored at input object `+0x74` and `+0x76`.
Either binding sets logical action bit `0x10000000`.

The input object also owns a circular history:

| Input-object field | Meaning |
| --- | --- |
| `+0x94` | pointer to `0x18`-byte input-history records |
| `+0x9C` | current record index |
| `+0xA0` | record count |

The resident code calls BTL accessor live address `0x006EF7F0` to resolve map
entries 6 and 7. The accessor reads the signed halfword at
`input + 0x68 + index * 2`, proving that these calls read exactly `+0x74` and
`+0x76`. It then calls the BTL history-search helper at live `0x006EFAC0`.
The clean BTL body reads the current index at `+0x9C`, applies the caller's zero
record skip, wraps through the count at `+0xA0`, and tests the requested number
of records while decrementing and wrapping after each test. Each substitution
call requests history word 1 at record `+0x04`, subset matching, no mask
filter, and the current record plus the normalized number of earlier records.
This proves that substitution consumes buffered physical guard input; it is
not based only on the current logical mask at fighter `+0x338`.

Fighter signed halfword `+0x95C` separately counts consecutive guard-held
frames. The acceptance predicate rejects when that count is 16 or greater.
Holding guard indefinitely is therefore not equivalent to repeatedly offering
a fresh substitution input.

### Per-attack timing byte

The selected attack/hit definition's signed byte at `+0x1A` controls the input
window. `FUN_00229130` transforms it as follows before searching both guard
bindings:

| Effective `+0x1A` | Behavior |
| ---: | --- |
| `0` | current input-history record only |
| `1` | current record plus 1 earlier record |
| `2` | current record plus 2 earlier records |
| `3` | current record plus 3 earlier records |
| `4..127` | clamped to `3` |
| negative `-n` | first require one specific modulo result out of `2n + 1`, then search only the current record |

The negative branch uses `(fighter[+0x88] XOR 0x80000000) % (2n + 1)` and
accepts only remainder `2n`. `fighter[+0x88]` is not an opaque hit counter:
`FUN_0024c440` writes one raw 32-bit MT19937 result from `FUN_001801e0` there
once per fighter update, immediately before `FUN_00224970` and
`FUN_0021ba20` reach hit/substitution processing. `FUN_0024fd80` invokes that
update once for every linked fighter object. Multiple predicate calls during
the same fighter update therefore reuse the same word, including the two calls
made by `FUN_0021f610`; the predicate itself draws no new word. See
[Runtime randomness](../runtime/randomness.md) for the generator evidence.

For a uniformly selected 32-bit word, the exact pass fraction for raw timing
`-n` is
`floor(2^32 / (2n + 1)) / 2^32`: `-1` is
`1431655765 / 4294967296`, `-2` is
`858993459 / 4294967296`, and `-3` is
`613566756 / 4294967296`. These are respectively just below the convenient
nominal values `1/3`, `1/5`, and `1/7`. The modulo gate is confirmed from clean
instructions `0x002295C8..0x00229604`; live attack trials can still be
correlated by fighter-update scheduling and by other consumers of the shared
MT stream, so an observed short run need not look independent.

Attack flags `0x000C0000` at definition `+0x10` are a special case: when the
timing byte is zero, the predicate changes it to `-1`, producing the same
modulo-three gate and a current-record-only input check. That conversion is at
`0x002295A4..0x002295C4`.

After normalizing the timing byte, the predicate rejects a guard held for at
least 16 frames at `0x00229620`, then searches binding 6 at
`0x00229638..0x00229670` and binding 7 at
`0x00229678..0x002296AC`.

### Negative guard-age sentinel and temporary-effect ID 9

There is one confirmed route around the attack timing and input-history tests.
After the ordinary eligibility checks, a negative fighter `+0x95C` value jumps
directly to the predicate's final optional resource gate when the `+0xC74`
object's state is `0`. States `1` and `2` take the same shortcut only when the
fighter does **not** currently carry temporary-effect ID `9`. This shortcut
skips timing normalization, the MT modulo test, the 16-frame held limit, and
both guard-history searches. It also branches before the ordinary
player-controlled-mode rejection, so a negative sentinel can admit a CPU-mode
fighter. It does not skip the earlier fighter-state, response, `+0xC74`, or
definition-flag checks, and a caller requesting normal validation still runs
the final resource/state checks.

`FUN_00307610` establishes effect ID `9` by walking the fighter's linked
temporary-effect list at `+0x8C8` for `+0x8C4` entries and comparing each
entry's `+0x68` word with `9`. At the start of `FUN_0024c440`, before the new
MT word and hit processing, `FUN_003059b0` calls that scan and writes `-2` to
fighter `+0x95C` through `FUN_00229b70` whenever effect `9` is present.

`FUN_0021f610` gives this effect a second special behavior. When effect `9` is
present, it first calls the predicate with resource validation disabled and,
on success, commits `FUN_002297d0(..., 0x211, 0)`, which does not deduct
substitution resource. Only if that attempt fails does it make the ordinary
resource-validating call. Consequently effect `9` can produce an automatic,
free substitution when the negative-sentinel shortcut is available, or a free
timing/input-gated substitution when it is not. The producer and player-facing
name are not generic attack metadata. The only direct temporary-effect-`9`
producer found in the clean boot ELF is Kurenai's awakened controller callback.

Kurenai metadata at runtime `0x0057FD20` stores `0x0057ACE0` at `+0x1C`. That
character-specific callback vector stores `FUN_002F2D70` at `+0x04`.
`FUN_002F2D70` itself rejects every live character ID except Kurenai `0x57`.
Outside its internal state-`6` exclusion, it watches fighter `+0x63` bit
`0x20`, which the awakening controller independently establishes as its
awakened marker. On a `0 -> 1` edge it calls
`FUN_00305C30(fighter, 9, 9999)`; on a `1 -> 0` edge it calls
`FUN_00305510(fighter, 9)`; and it records the last marker value at fighter
`+0x5626`. Thus the free/automatic route is a Kurenai-awakening exception. The
literal `9999` argument is proven, but its unit is not assigned here. The
callback does not distinguish Kurenai's associated effects `0x5B` and `0x5C`,
so this evidence does not justify attaching the exception to only one named
awakening variant.

Do not conflate that temporary-effect ID with item/status ID `9` merely because
the numbers match. Item handler `FUN_00236C70` receives a selected item/status
ID. Its ID-`9` branch, after its own state and current-definition
`+0x10:0x00000200` guard, calls `FUN_002297D0(fighter, 2, 0)` directly. It does
not call `FUN_00229130`, does not inspect attack `+0x1A`, does not search guard
history, and does not charge the normal resource. The surrounding
`FUN_002366F0` route requires the item-use logical action and an available item
from the item manager before making that call. This is a separate free
item/status substitution, outside any per-attack reliability control.

### Attack-record ownership and clean-ELF inventory

The timing byte is file-backed character action data, not a transient field
invented by the hit handler. `FUN_002151e0` initializes each fighter from its
character metadata as follows:

| Character metadata | Fighter field | Meaning |
| ---: | ---: | --- |
| `+0x28` | `+0xA38` | action-record count |
| `+0x2C` | `+0xA54`, `+0xA58`, initially `+0xA4C` | primary action-record base |
| `+0x30` when nonzero | same fields | optional replacement action-record base |

`FUN_00238a70` stores the selected signed action index at fighter `+0xA3C` and
computes `fighter[+0xA4C] = fighter[+0xA54] + index * 0x54`. Each action record
is therefore `0x54` bytes, and a selected definition can be mapped back to an
owner and index with `(definition - owner_base) / 0x54`. An incoming definition
at the defender's `+0xE50` or `+0xE54` normally maps against the attacker's
table, not the defender's.

For the clean boot ELF, every character row currently catalogued in
`@resources/character_data.tsv` has a zero optional base at metadata `+0x30` and
uses the primary base at `+0x2C`. The exact timing-byte virtual address for
record index `i` is:

```text
character[+0x2C] + i * 0x54 + 0x1A
```

Resident file offsets use the canonical conversion linked above. A virtual
address must not be mistaken for its file offset.

A complete read-only scan of the 74 primary-roster tables in
`@resources/character_data.tsv` found 3,428 action records with these raw timing
values:

| Raw `+0x1A` | Record count | Predicate policy |
| ---: | ---: | --- |
| `-3` | 6 | nominal `1/7`, current record only |
| `-2` | 30 | nominal `1/5`, current record only |
| `-1` | 319 | nominal `1/3`, current record only |
| `0` | 2,794 | deterministic current record, except the flag conversion below |
| `1` | 261 | deterministic current plus one earlier record |
| `2` | 18 | deterministic current plus two earlier records |

Exactly 148 of the raw-zero records have `+0x10 & 0x000C0000 != 0`, so their
effective timing is `-1`. The stock tables contain no raw timing `3` or value
above `3`. These are record counts, not a claim that every record is a distinct
reachable attack; dummies, transitions, and non-damaging actions share the same
table format.

In those primary tables, the separate predicate-level `+0x14` rejection flags
occur on 109 records:
91 contain `0x00008000`, and 18 contain both `0x00008000` and `0x02000000`;
no clean primary-table record contains only `0x02000000`. Ninety-three of the
109 have an admitted Command Chart title. Eighty-four also have exceptional
timing: 83 resolve to effective `-1` and one to effective `-3`. Those 84 are a
particularly important false lead for timing-only edits: the predicate rejects
their flags before reading `+0x1A`, so changing the timing byte has no native
effect. Examples include Naruto's `Naruto Uzumaki Combo Attack`, Kakashi's
`Lightning Blade Drop`, and Kurenai's `Genjutsu: Mirage`. Catalog membership
still does not prove that every internal record reaches the hit path.

Clean authored response byte `+0x2C` uses values `0x00..0x1E` plus `0xFF`;
none of the 74 primary tables uses authored `0x1F..0x27`. The response function
supports a broader domain because context, callbacks, and repeat-hit handling
can replace the authored result dynamically.

The record's pointer at `+0x08` joins this inventory to the canonical
translation importer's Command Chart titles. A mapping's exact
`reference_refs` record-field offset takes precedence for shared source text;
otherwise the pointed-to clean-ELF string offset joins to `source_ref`. Of the
1,065 Command Chart mappings, 1,057 mapping IDs occur in the 74 primary tables
and name 1,102 record instances because some titles are deliberately shared
between forms or characters.

Four additional clean-ELF fighter-metadata blocks have the same count at
`+0x28`, action base at `+0x2C`, zero optional base at `+0x30`, and `0x54`-byte
record layout, but their IDs are deliberately absent from the primary roster
catalog. Each owns four records:

| Catalog scope | Metadata | ID | Count | Action base |
| --- | ---: | ---: | ---: | ---: |
| auxiliary | `0x0059C7A0` | `0x1A` | 4 | `0x0059C630` |
| auxiliary | `0x0059CF80` | `0x1D` | 4 | `0x0059CE10` |
| auxiliary | `0x0059D750` | `0x1E` | 4 | `0x0059D5E0` |
| auxiliary | `0x0059DF20` | `0x1F` | 4 | `0x0059DDB0` |

These are evidence-backed auxiliary fighter IDs, not inferred player-facing
owner names. Their eight named records account for every Command Chart mapping
outside the primary tables:

| Auxiliary ID/index | Command Chart title | Timing address | `+0x10` | `+0x14` block subset | Stock effective policy |
| --- | --- | ---: | ---: | ---: | --- |
| `0x1A/1` | Ninja Hound Summoning | `0x0059C69E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1A/3` | Demon Wind Bomb | `0x0059C746` | `0x00080000` | `0` | exact modulo-three gate |
| `0x1D/1` | Double Last Resort | `0x0059CE7E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1D/3` | Swirling Sand Rasengan | `0x0059CF26` | `0x00080000` | `0` | exact modulo-three gate |
| `0x1E/1` | Kachofuketsu | `0x0059D64E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1E/3` | Fragment of a Legend | `0x0059D6F6` | `0x00080000` | `0` | exact modulo-three gate |
| `0x1F/1` | Dazzling Battle: Beast Scroll Replicas | `0x0059DE1E` | `0x00040000` | `0` | exact modulo-three gate |
| `0x1F/3` | Temple of Nirvana Technique | `0x0059DEC6` | `0x00080000` | `0x00008000` | rejected before timing |

All eight have raw timing zero. Their `+0x10` conversion flags make the
effective timing `-1`; therefore the seven without a block bit use the exact
`1431655765 / 4294967296` current-record gate when all other eligibility
conditions pass. All eight use authored response selector `0x0F`, whose normal
grounded/other results `0x36/0x37` are both inside the predicate whitelist.
Temple of Nirvana Technique is different: `+0x14 & 0x00008000` rejects it
before timing is read, so changing only its `+0x1A` byte cannot enable native
substitution. Reachability of each auxiliary record through a particular
gameplay setup remains a runtime question; the table ownership, fields, and
Command Chart identities are static facts.

Including these four tables gives 78 metadata owners and 3,444 records. The
combined raw counts are `-3: 6`, `-2: 30`, `-1: 319`, `0: 2810`, `1: 261`,
and `2: 18`; the combined effective counts are `-3: 6`, `-2: 30`, `-1: 475`,
`0: 2654`, `1: 261`, and `2: 18`. The flag conversion affects 156 records.
There are 790 exceptional records: 492 named and 298 unnamed. The block totals
become 110 records, split as 92 with `0x00008000` and 18 with
`0x02008000`; 94 are named and 85 also have exceptional timing. All 1,065
Command Chart mapping IDs now resolve, naming 1,110 record instances. An absent
title means only that the internal record has no admitted Command Chart name;
it must not be given a move name by analogy.

The 1,110 named instances divide by effective timing and predicate-block state
as follows. A blocked count means the listed timing is present in data but is
not consulted by the native predicate:

| Effective timing | Unblocked named instances | Blocked named instances |
| ---: | ---: | ---: |
| `-3` | 3 | 1 |
| `-2` | 24 | 0 |
| `-1` | 252 | 84 |
| `0` | 609 | 9 |
| `1` | 115 | 0 |
| `2` | 13 | 0 |

A displayed title is not always a unique executable attack record. Of the
1,065 mapping IDs, 1,022 name one record, 41 name two, and two name three. Only
six IDs have different reliability profiles among their instances, but those
six make a title-only patch selector unsafe:

| Mapping/title | Distinct stock instances |
| --- | --- |
| T1506 Primary Lotus | Rock Lee `1`: effective `-1`; Might Guy `52`: effective `1` |
| T1507 Dynamic Entry | Rock Lee `3`: effective `-1`; Might Guy `40`: effective `0` |
| T885 Deer Drop | Shikamaru `25`: effective `-1`; classic Shikamaru `25`: effective `1` |
| T867 Sand Burial | Kazekage Gaara `35`: effective `2`, unblocked; classic Gaara `1`: effective `-1`, blocked `0x00008000` |
| T840 Chidori | current Sasuke `3` and classic Sasuke `3`: effective `-1`; Second Stage Sasuke `35`: effective `0` |
| T1141 Windmill | Hanabi `3`: effective `-1`, blocked `0x02008000`; Kimimaro `26`: effective `-1`, unblocked |

Five of these IDs mix timing policies; Sand Burial and Windmill mix blocked and
unblocked records. Ninety mapping IDs have every instance blocked, while 92
have at least one blocked instance. Therefore a product setting described as
“per attack” must identify at least the owner ID plus record index, or expand a
Command Chart mapping to every intended instance and handle each instance's
eligibility separately.

#### Runtime-mutated action records

The clean catalog is an initial/template inventory. Fighter initialization
relocates the selected action table, and `FUN_00217930(fighter, -3)` returns the
current live record. A clean-export audit found six records whose
character-specific callbacks directly write that live record's timing byte.
For the template-reading branches, the source address is exactly
`fighter[+0xB8] + index * 0x54 + 0x1A`, so a guarded file edit changes the
template value but not the callbacks' hard-coded alternatives.

| Owner/index | Title | Stock effective timing | Direct writer and possible live timing |
| --- | --- | ---: | --- |
| Deidara `43` | Giant Bird Clay: Fly | `-3` | `FUN_002B5250`: template, `-1`, or `0` |
| Deidara `44` | Giant Bird Clay: Attack | `-3`, stock blocked | `FUN_002B5250` then `FUN_002B68F0`: template, retained, `-1`, `-2`, `0`, or `2` |
| Deidara `45` | Giant Bird Clay: Thrust | `-3` | `FUN_002B5250`: template, `-1`, or `0` |
| Rock Lee `39` | unnamed internal record | `-3` | `FUN_002BDF80`: template or `0` |
| Might Guy `42` | Friendship Lasso | `0` | `FUN_002C55B0`: stock at tier `<=1`, then `1`, `2`, or `3` from fighter `+0x69B0` |
| Sasori (Hiruko) `30` | Submerged Hand | `-1` | `FUN_002D5320`: template plus `0`, `1`, or `2` from fighter `+0x4E3E` tier |

`FUN_002B5250` also sets or clears predicate block bit `0x00008000` on all
three Deidara records. `FUN_002BDF80` does the same on Rock Lee record `39`.
Thus Giant Bird Clay: Attack's stock block can be cleared at runtime, while the
other three records can become blocked despite an unblocked clean template.
The nearby `0x00080000` mutations in hit callbacks are a different flag and do
not satisfy the predicate's block mask.

For these six records, changing only the clean `+0x1A` byte does not guarantee
one policy in every live state. A state-independent per-record implementation
must normalize after the relevant writer or at the central predicate. Central
timing normalization still intentionally preserves the four dynamic
`0x00008000` eligibility changes; overriding those would be a separate
substitutability-policy change, not a reliability-window change. The catalog
marks all six records, names their writer functions and possible value family,
and reports whether the substitution block bit is also mutated. The live lab
includes the same warning fields whenever it resolves one of these records.

The read-only catalog command reproduces the full join directly from the
hash-pinned clean ELF, `@resources/character_data.tsv`, and the canonical
translation mappings:

```powershell
.\scripts\research\substitution\catalog.ps1 --summary-only
.\scripts\research\substitution\catalog.ps1 --character 70 --exceptional-only
.\scripts\research\substitution\catalog.ps1 --scope auxiliary --format tsv
.\scripts\research\substitution\catalog.ps1 --mapping T867 --format tsv
.\scripts\research\substitution\catalog.ps1 --mapping "Windmill" --format tsv
.\scripts\research\substitution\catalog.ps1 --runtime-mutated-only --format tsv
.\scripts\research\substitution\catalog.ps1 --blocked-only --named-only --format tsv
.\scripts\research\substitution\catalog.ps1 --character "Kakashi Hatake" --exceptional-only --format tsv
```

Every emitted record includes its primary/auxiliary scope, metadata and
character ID, decimal and hexadecimal index, record and timing virtual
addresses, ELF file offsets, `+0x10`/`+0x14` flags, the exact
predicate-blocking flag subset, raw and effective timing, normalized policy,
exact passing/total 32-bit-word counts for negative timing, authored response
selector `+0x2C`, name pointer, and any exact Command Chart mapping ID/title.
`--scope` isolates one ownership family, `--named-only` restricts output to
titled records, `--mapping` selects an exact mapping ID or case-insensitive
exact title, `--blocked-only` selects definitions rejected by either `+0x14`
flag, and `--runtime-mutated-only` isolates callback-owned timing exceptions.
Each mapped row also reports the number of record instances and distinct
reliability profiles owned by its mapping ID. Summary output includes the six
mixed-profile groups with their exact owners, indices, addresses, timings, and
block flags, plus the six known runtime-mutated records and their writers. The
command never writes the ELF or generates a patch.

Kakashi (ID 70) is a concrete example. His metadata selects 48 records at
virtual base `0x00524BF0`. Named record `0x01`, `Lightning Blade Drop` (T1550),
and named record `0x03`, `Lightning Blade` (T1551), contain raw zero with
`0x00040000` and `0x00080000` respectively and therefore become effective
`-1`. Unnamed records `0x17` and `0x18` contain raw `-1`. Unnamed records
`0x23` and `0x2B` and named record `0x2C`, `Back Kick` (T1563), contain `1`;
all other records contain zero. Record `0x17`'s timing byte is virtual
`0x00525396`, ELF file offset `0x425496`. Changing that byte from `0xFF` to
`0` removes the modulo gate while retaining a current-record-only check;
changing it to `3` also provides the maximum four-record human input window.
For records `0x01` and `0x03`, zero is not deterministic because of the flag
conversion, so use a positive value `1..3`.

### Other eligibility gates

Changing the timing byte cannot make an otherwise ineligible hit substitutable.
The same predicate also rejects, among other conditions:

- disallowed fighter states and an active fighter `+0xB00` object;
- reaction selector `8` and reaction values outside its explicit whitelist;
- attack-definition `+0x14` flags `0x02000000` or `0x00008000`;
- unsupported state of the fighter object at `+0xC74`;
- non-player-controlled fighter modes identified from fighter `+0x60`;
- a separate `FUN_00307480` state gate; and
- resource below `1.0` at fighter `+0x70` when the caller requests normal
  resource validation.

These are eligibility controls, not attack-specific reliability percentages.
Read-only GhidrAssist inspection confirms that `FUN_00229130` compares chakra
with its own `1.0` constant, independently of the `1.0` subtraction in
`FUN_002297D0`. The latter clamps the remaining resource to zero. Altering one
constant therefore does not change the other. The effect-ID-9 route is separate
from this ordinary eligibility and spending pair.

The response test can be stated exactly. The predicate rejects selector
argument `8`, then accepts only response values in this set:

```text
0x06, 0x07,
0x27..0x39,
0x3C..0x41,
0x48..0x59
```

`FUN_00231C60` normally derives that response from attack-record byte `+0x2C`
plus grounded/orientation/current-response context. The ordinary authored
families fall in accepted ranges, but failed contextual queries return
`0x3A/0x3B`, and callbacks or repeat-hit remapping can select other values.
Both `0x3A/0x3B` and `0x42..0x47` are outside the whitelist. Editing `+0x1A`
cannot turn one of those rejected response contexts into an accepted one; that
would be a response-policy change, not a reliability-window change. See
[Hit response](hit_response.md) for the complete `+0x2C` mapping and dynamic
remaps.

## Reliability control choices

The narrowest per-attack control is the selected attack definition's `+0x1A`
byte:

- use `0..3` for deterministic windows of one through four history records;
- use a positive value, not zero, when definition flags `0x000C0000` are set
  and deterministic behavior is required;
- use negative values only when an intentional modulo-based failure rate is
  desired; and
- treat temporary-effect ID `9` as a separate special path because its
  negative-age/free-commit behavior can bypass the selected attack's timing
  policy.

All signed negative byte values are accepted by the arithmetic. For raw
`-n`, where `1 <= n <= 128`, the modulo denominator is the odd number
`2n + 1`, so the byte supplies discrete nominal probabilities from `1/3` down
to `1/257`. Because the implementation tests a 32-bit word modulo a denominator
that generally does not divide `2^32`, use the exact floor formula above when
reproducible rates matter. Positive values above `3` do not create a wider
window: they clamp to the same four-record search as `3`.

The practical control surfaces follow directly from that ownership:

| Desired scope | Narrow control | What remains unchanged |
| --- | --- | --- |
| One non-mutated character action record | Guarded edit of that record's signed `+0x1A` byte | All eligibility, resource, and transition rules |
| One of the six runtime-mutated records | Change its template and every applicable writer, or normalize it after those writers | Other records remain independently selectable; dynamic block flags remain |
| Every action with a stock table entry | Generate guarded edits from the hash-pinned catalog and handle the six writer-owned exceptions | Per-record values remain independently selectable |
| Every attack reaching the predicate | Normalize effective timing inside `FUN_00229130` after flag conversion | Eligibility, held-guard rejection, resource checks, and commit behavior |
| Kurenai awakened exception | Treat effect `9` separately | Ordinary attack timing policy remains independent |

Deterministic timing means deterministic *window admission*, not guaranteed
substitution. A fresh guard edge must still be present in the chosen history
window, guard age must remain below 16, and every eligibility/resource gate
must pass. To offer the broadest stock-compatible deterministic window, use
effective timing `3`; to require an edge on the current input record, use an
effective zero. Raw zero is not effective zero on definitions carrying
`0x000C0000`, so those records require a code-level post-conversion override or
a positive table value.

A global reliability control belongs inside `FUN_00229130`, after the special
`0x000C0000` conversion and before the held-duration check. That boundary
changes only window/probability policy. Forcing the function's final result or
forcing `FUN_002297D0` would also admit ineligible states and is not equivalent.

Per-attack ownership, record sizing, offset calculation, clean-roster value
distribution, and the exact Command Chart name join are now established.
Runtime observation is still required to determine the gameplay role of the
298 exceptional internal records without admitted titles and to prove which
catalogued records actually reach this predicate. Code-level normalization
remains the only convenient control that covers every reaching attack without
a large guarded edit table.

## Agent-driven runtime lab without input recordings

The runtime-control foundation uses PCSX2 PINE protocol version 1 rather than
an input recording. PCSX2 commit
`f351798d9f28b5b425231d8edaef09f3109eecf6` adds four operations:

| Opcode | Operation | Contract |
| ---: | --- | --- |
| `0x16` | set states | install complete 18-byte DualShock 2 states for controlled slots |
| `0x17` | step | atomically install states, advance an exact positive frame count, and return the start/end frame counters |
| `0x18` | get states | report whether each slot is controlled and its effective complete state |
| `0x19` | release | neutralize selected controlled slots, or all slots |

All integers and the normal PINE size prefix are little-endian. Agent requests
start with protocol version `1`. Set/step records are
`{u8 unified_slot, u8 state[18]}`, with one through eight unique connected DS2
slots; get requests contain one through eight slot bytes; release accepts zero
through eight, where zero means all. A successful agent reply begins with
`u32 total_size, u8 status=0, u8 version=1`; standard PINE failure remains
`size=5, status=0xFF`. Step additionally carries a positive `u32` frame count
and replies with `u32 start_frame, u32 end_frame` after the echoed version.

The 18-byte state is recording-compatible DS2 data: two active-low digital
button groups; `RX, RY, LX, LY`; then pressure bytes for
`right,left,up,down,triangle,circle,cross,square,L1,R1,L2,R2`. Neutral is
`FF FF 7F 7F 7F 7F` followed by twelve zero bytes. This full-state contract is
why a step cannot accidentally inherit an omitted button from a previous
request.

Overrides are applied after host input polling. Recording/replay conflicts,
invalid requests, reset, shutdown, disconnect, and aborted stepping fail closed
and neutralize controlled slots. The protocol therefore supports deterministic
paused-frame experiments without leaving a held input behind.

The deployed development PCSX2 binary supplied the runtime environment.
Post-deployment trials completed synchronous steps of 1, 8, 20, and 120 frames;
every reply satisfied `(end - start) mod 2^32 == requested`, and focused
`PINEAgentControl*` tests passed. Rebuilding an exact commit-identifiable binary
requires regenerating the ignored `svnrev.h` metadata after the commit exists
and relinking; the pre-commit candidate contained the new code but advertised
its parent revision.

Three static lifecycle limitations remain for future PCSX2 hardening:

- the single PINE thread cannot notice a client disconnect until an in-flight
  synchronous step returns;
- reloading PINE settings during such a step can deadlock because CPU-thread
  `Deinitialize()` closes sockets and then joins the PINE thread while that
  thread waits for CPU-thread frame advance/auto-pause; and
- a malformed or failed unrelated legacy opcode does not centrally clear an
  already installed agent override until disconnect.

The maintained lab avoids these edges with bounded steps, no PINE reload while
stepping, agent-only requests, and one command per connection. The minimal
reload repair is to abort and neutralize agent control before `Deinitialize()`
joins, with the step wait predicate observing that abort.

`@pcsx2_scripts/pine.py` owns the protocol client and full-state
encoder. This repository's
`@scripts/research/substitution/agent_lab.ps1` is the maintained entrypoint for
substitution work. With an agent-capable PCSX2 VM already paused, its basic
operations are:

```powershell
.\scripts\research\substitution\agent_lab.ps1 -Port 28014 observe
.\scripts\research\substitution\agent_lab.ps1 -Port 28014 step 1 --pad 0=r2
.\scripts\research\substitution\agent_lab.ps1 -Port 28014 step 1 --pad 0=
.\scripts\research\substitution\agent_lab.ps1 -Port 28014 release
```

`observe` emits JSON for battle-manager state, both fighter pointers, health,
substitution resource, selected candidate definitions and their reliability
fields, each definition's matching Player 1/Player 2 action-record index,
controller mode, action state/phase, current MT word, guard-held duration,
`+0xC74` state, the bounded temporary-effect list and ID-`9` presence, current
logical input, and up to 16 circular input-history records. Live definition
telemetry includes the effective timing/negative-RNG calculation, exact
predicate-block flags, and authored response selector. For every mapped
definition it also joins the hash-pinned clean catalog's character ID, static
record/timing address, stock raw/effective timing and policy, and admitted
Command Chart mapping ID/title. `step` applies the requested complete pad state
for exactly the given frames and then emits the same observation with the
verified PCSX2 frame interval. Sequential invocations can therefore navigate
and measure the game one decision at a time without a prerecorded controller
stream.

This foundation identifies the owning character side and stable record index;
the static catalog resolves any admitted Command Chart name for that pair.
Automatic roster exercise and semantic classification of unnamed internal
records remain runtime dataset tasks. The input, stepping, record identity,
static name join, and relevant telemetry paths no longer need recordings.

### First live autonomous probe

The first no-recording probe used a paused Practice battle. A complete P1
Circle state selected Naruto action record `21`; when
the hit landed, P2 `+0xE54` changed to the relocated P1 record `21`, whose clean
timing is `-1` and whose canonical Command Chart title is `Nindo Attack`. P2
health changed from `1.0` to `0.98` and then regenerated under Practice rules.
This runtime-confirms the incoming-definition owner/index calculation, rather
than merely observing the attacker's current-action pointer.

A complete slot-1 L2 state independently produced newly-pressed native mask
`0x00000001` in the Practice defender's input-history word 1 and the matching
released mask in word 2. The fighter's logical action and `+0x95C` nevertheless
remained zero because this Practice opponent had non-player mode value
`((fighter[+0x60] & 0x1FF) >> 5) == 1`; the suppression behavior matches the
static input and predicate gates. No runtime memory patch was used. The VM was
returned paused at manager state/substate `4/3`, with both
controller slots uncontrolled and neutral.

## Established control flow

### Hit/action dispatcher

`FUN_00190f40(float param_1, undefined8 param_2)` is the main hit/action dispatcher examined in this investigation. Its relevant behavior is:

- the action object at character/object `+0x94` is considered for the primary path;
- mode bits in the byte at `+0xA8` and the scaled-impact threshold can select result bit 1;
- the secondary object at `+0x9C` and another `+0xA8` condition can select result bit 2;
- result bit 1 calls `FUN_001910e0` with the `+0x94` action object;
- result bit 2 calls `FUN_0018cf70` with the `+0x9C` object.

The tested gates in this dispatcher did not explain unreliable substitution input.

### Action packet path

- `FUN_001910e0` consumes copied action flags at scratch `+0x20C`.
- `FUN_00198290` copies the source action object's field at `+0x18` into scratch `+0x20C`.
- `FUN_001921c0` ORs `0x7000` into scratch/packet field `+0x20C` during commit/setup. Forcing its guarding branches caused the black-screen result.

### Action object construction

- `FUN_00196b40` creates the action object stored at character `+0x94` for action/character type `0x100`.
- It allocates `0x50` bytes through `FUN_00117150`, initializes the object with `FUN_001992a0`, and stores the result at `+0x94`.
- `FUN_001992a0` initializes action-object field `+0x18` from action-definition entry `param_2[0x12]`.

Therefore the relevant `0x800` flag originates in selected action-definition data before `FUN_00190f40`; it is not created by the hit dispatcher.

## Investigation boundary and next target

Do not resume by broadly patching `FUN_00190f40` or forcing `FUN_001921c0`
unless new runtime evidence narrows the condition. The earlier unresolved
input-buffer question is now resolved: `FUN_00229130` explicitly searches a
per-fighter input history using attack-specific timing policy.

The next useful work is runtime enumeration, driven with exact paused-frame
input rather than an input recording:

- capture the selected definition pointer, fields `+0x10`, `+0x14`, and
  `+0x1A`, reaction value, fighter `+0x95C`, and predicate result for each
  tested attack;
- measure the empirical distribution for negative timing bytes;
- use the resolved owner/index pairs to assign user-facing move names; and
- choose whether the product control is per-attack data, one global
  deterministic window, or a configurable normalization table.

When exporting listings from the preserved Ghidra project, omit undefined data. A full dump including undefined data was found too large to be useful.
