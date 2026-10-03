# Battle damage

Native character durability, effective HP, combo hit index, and
damage-calculation paths in retail NA2 (`SLPS-25837`).

## Research coverage

- **Assigned scope:** native HP and durability arithmetic, the character-record
  fields with damage consumers, the shared calculator `FUN_00224e30` and HP
  application `FUN_00225050`, the combo hit index at damage boundaries, and the
  resident and overlay callers that supply raw damage, flags, and gates.
- **Exploration depth:**
  - All ten resident calls to the calculator are statically classified, with
    complete calculator, application, effect-fold, raw-sample,
    signed-HP-adjustment, and counter-digit bodies.
  - Direct-call byte searches cover `BTL.BIN` and `ETC.BIN`; all fifteen BTL
    calls to `FUN_002333A0` are classified by raw input, target, source, and
    record argument, together with the initialization and exact-address
    lifetime of their shared record and raw float.
  - Skill-owned arithmetic is traced for `ccSkillFOR000` and
    `ccSkillANB000`; the other BTL callers are bounded to their call sites.
  - One deterministic Practice normal string (Sakura against Naruto) was
    observed at runtime at its damage boundaries.
- **Confirmed coverage:** the calculator's per-flag factors, order, precision
  boundaries, and clamp; temporary-effect folds; Handicap; HP application,
  knockout, and the Practice floor; ordinary and guarded-hit gates and the
  half-chip selector; attack-record resolution; calculator-bypassing effect HP
  changes; the Rock Lee, Sasori/Hiruko, and object-hit direct-damage paths; the
  BTL source-retaining wrapper and its fifteen callers; FOR and ANB multiplier
  gates; and the Ultimate Jutsu and counter-only calls. At runtime, the
  observed string confirms the ordinary attack-record and fixed `0.02`
  contact-stage paths, their raw/flag values, the combo hit-index formula, and
  exact agreement between native results and HP.
- **Unresolved or untested:**
  - Runtime execution of the fixed `0.04` contact branch, guarded-hit damage,
    Handicap, temporary-effect factors, and every direct-damage path.
  - Other characters and damage categories: throws, projectiles, Jutsu,
    Ultimate Jutsu, support, status, and transformations.
  - Class joins for nine BTL call sites and player-facing move names for the
    seven joined skill classes.
  - Complete alias mutation and lifetime of the shared retained record,
    skill-object reuse outside the inspected spawn route, advancement of the
    shared-float event counter `+0x14A`, and later FPU rounding-control
    lifetime.
- **Deliberate exclusions and overlap:**
  - [Combo accounting](combo_accounting.md) owns combo ownership, pending and
    accumulated counts, and reset conditions.
  - [Target selection](target_selection.md#accepted-hit-source-boundary) owns
    accepted-hit source provenance; [Hit response](hit_response.md) owns
    response states, paired-hit arbitration, and hit counts;
    [Collision](collision.md#definition-to-runtime-copy) owns BTL record
    construction.
  - [Stage surface attributes](../stages/stage_surface_attributes.md#stage-authored-attribute-distribution)
    owns stage collision flags; [Chakra and guard](chakra_and_guard.md#gain-and-clamp-behavior)
    owns chakra gain; [Support mechanics](../characters/support_mechanics.md#gauge-state-and-availability)
    owns the support gauge; [Match outcomes](../session/match_outcomes.md#terminal-detector-and-classifier)
    owns knockout classification.
  - [Battle entities](../session/battle_entities.md#btl-skill-classes-on-damage-paths)
    owns the skill classes' identities, allocation, and destruction;
    [Character IDs](../characters/character_ids.md) owns character identity;
    [Ultimate Jutsu](../characters/ultimate_jutsu.md#damage) owns cinematic damage amounts;
    [Battle items and status effects](../projectiles_and_items/battle_items_and_status_effects.md#resident-effect-definitions)
    owns effect definitions.
- **Evidence limitations:** static conclusions use the retail resident ELF and
  the `BTL.BIN`/`ETC.BIN` overlays identified in
  [Retail game file identities](../../game/files/file_identities.md); there is no
  original source. Some resident predicates are treated as non-returning by the
  disassembler, so the affected BTL branches rest on instruction bytes. Runtime
  evidence is one Practice string observed at selected checkpoints, and heap
  addresses are allocation-specific. Static reachability is not evidence that a
  caller executes in ordinary play, and EE instruction sequences do not by
  themselves establish every hardware rounding detail or frame-order outcome.

## Character durability and effective base HP

The game does not store a different full-gauge HP value per character. Current
HP is a normalized `float32` at fighter `+0x6C`; full health is `1.0`.
`FUN_00225050` subtracts normalized damage from this field and clamps it at
zero outside Practice; its Practice floor is described below. Fighter
construction initializes health through `FUN_00224d10` from the
battle-instance initialization value described below.

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

On a 100-point scale, neutral effective base HP is `100 / m`. This isolates the
static durability parameter; attacker offense and temporary battle-state
multipliers are separate factors in `FUN_00224e30`. Effective base HP is a
derived balance value, not a literal full-gauge value stored in fighter memory.

The static character record is reached through the ID-indexed
[character-definition table](../characters/character_ids.md#character-definition-table),
whose second word at EE `0x005A2904 + 8 * ID` points to the record. ID 57
points to Naruto's record at `0x004DAD80`, whose durability parameter is
`0.90`; ID 58 points to Sakura's record at `0x004E01B0`, whose parameter is
`0.80`. Naruto therefore has `90.909091` neutral effective HP and Sakura has
`83.333333` on the same scale.

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
| `+0xC0` | `+0x14C` | Static durability parameter used to derive effective base HP | `FUN_00224e30`, damage flag `0x2` |
| `+0xD4` | `+0x160` | Health-recovery multiplier | `FUN_00224df0`, `FUN_002369d0` |
| `+0xD8` | `+0x164` | Chakra-recovery multiplier | `FUN_002369d0` into `FUN_002254a0` |

The chakra adder `FUN_002254a0`, its `15.0` cap, and the `+0x164` recovery
path belong to [chakra gain](chakra_and_guard.md#gain-and-clamp-behavior).

Naruto and Sakura demonstrate that these are independent balance parameters:

| Character | Offense `+0x148` | Durability `+0x14C` | Health recovery `+0x160` | Chakra recovery `+0x164` | Effective base HP |
| --- | ---: | ---: | ---: | ---: | ---: |
| Naruto (ID 57) | `1.1` | `0.9` | `1.0` | `1.2` | `90.909091` |
| Sakura (ID 58) | `1.2` | `0.8` | `1.1` | `1.1` | `83.333333` |

The character-instance holder is separate from the static record. Holder
`+0x00` points to the record; holder `+0x1C` supplies initial normalized HP and
holder `+0x20` supplies initial chakra to `FUN_002151e0`. In Practice those
instance values were observed as `1.0` HP and `15.0` chakra for both Naruto and
Sakura, so their durability difference is applied during damage rather than
during full-health initialization.

The remaining copied record fields remain semantically unidentified.

## Combo hit state and damage path

The following values were observed in a deterministic Practice string of
Sakura (ID 58, No Support, no starting effect) normal attacks against Naruto
(ID 57) on Practice's bootstrap stage. Every calculator event came from the
ordinary attack-record call at `0x00234A80` or the fixed contact-stage call at
`0x00231698`; the other eight calculator call sites were not invoked.

| Event | Visible hit | Call site | Raw | Flags | Current / pending | Hit index | Native damage | Naruto HP / counter after |
| ---: | --- | ---: | ---: | ---: | ---: | ---: | ---: | --- |
| 1 | 1 | `0x00234A80` | `0.02` | `0x133` | `0 / 1` | 1 | `0.0264` | — |
| 2 | 2 | `0x00234A80` | `0.03` | `0x133` | `1 / 1` | 2 | `0.0396` | `0.934000015` / `6.5%` |
| 3 | 3, main | `0x00234A80` | `0.05` | `0x133` | `2 / 1` | 3 | `0.0660` | — |
| 4 | 3, secondary | `0x00231698` | `0.02` | `0x122` | `3 / 0` | 3 | `0.0220` | `0.846000016` / `15.3%` |
| 5 | 4 | `0x00234A80` | `0.02` | `0x133` | `3 / 1` | 4 | `0.0264` | `0.819599986` / `18.0%` |
| 6 | 5 | `0x00234A80` | `0.015` | `0x133` | `4 / 1` | 5 | `0.0198` | `0.799799979` / `20.0%` |
| 7 | Fresh hit after native reset | `0x00234A80` | `0.02` | `0x133` | `0 / 1` | 1 | `0.0264` | `0.973600030` / `2.6%` |
| 8, 9 | Later fresh hits | `0x00234A80` | `0.02` | `0x133` | `0 / 1` | 1 | `0.0264` | — |

The native current count reached five with a zero record. A native reset then
cleared the current count and raised record `+0x36` to five; later hits counted
from one again while the record stayed five. The HP changes agree exactly with
the native results: `0.02 * 1.32 + 0.03 * 1.32 = 0.066`,
`0.05 * 1.32 + 0.02 * 1.10 = 0.088`, `0.02 * 1.32 = 0.0264`, and
`0.015 * 1.32 = 0.0198`. These products match flag `0x133` applying Sakura's
offense `1.2` and Naruto's durability multiplier `1.1`, and flag `0x122`
applying only the durability multiplier. The declining, nonuniform damage
therefore comes from the differing attack records and hit three's secondary
event; the shared calculator has no combo-scaling factor.

### Native combo owner

Each side's combo owner, at `0x006076B8 + 4 * (fighter[+0x60] & 1)`, holds the
signed current count at `+0x34`, the largest completed count at `+0x36`, and a
timer armed for `90`. Accepted hits accumulate in the fighter's signed pending
byte `+0xA45` until the per-update manager consumes them. Ownership, update
order, reset and retention predicates, and every count producer belong to
[Combo accounting](combo_accounting.md#resident-owner-and-update-order),
including [retention and reset](combo_accounting.md#retention-and-reset) and
[explicit and pending updates](combo_accounting.md#explicit-and-pending-updates).

At a damage boundary, the attacker's one-based combo hit index is:

```text
max(1, current_count + max(pending_count, 0))
```

The calculator does not read this value; it is a derived index that numbers
the accepted hits consistently at both observed damage calls. In the observed
string, main attack-record damage ran before the manager consumed the pending
byte, seeing `(current, pending)` values `(0,1)` through `(4,1)`, while the
third hit's secondary damage ran after consumption and saw `(3,0)`. The formula
therefore gives `1, 2, 3, 3, 4, 5`: both damage events of hit three receive
index three without a separate latch or second increment. Every fresh
post-reset call saw `(0,1)` and returned to index one. This is
runtime-confirmed for the ordinary and `0.02` contact-stage paths only.

### Native damage calculation

Two similar consumers, `FUN_00228b50(defender)` and
`FUN_002346b0(defender)`, resolve an active attack record, read normalized
damage from record `+0x24`, and divide by the signed short at record `+0x2E`
when that field is nonzero. Record `+0x2E` is the same value that
[`hit_response.md`](hit_response.md) records as the expected repeat count
copied to fighter `+0xE5C`, so an authored multi-sample hit divides its
`+0x24` total across its samples. Both consumers select native flags `0x133`
or `0x122` from attack-record bits, call
`FUN_00224e30(raw_damage, defender, flags)`, and pass its returned normalized
damage to `FUN_00225050` for bookkeeping, the damage-counter display, HP
subtraction, and the zero clamp. Their state roles differ: `FUN_00228b50` is
called by guarded-hit initializer `FUN_00228760`, while `FUN_002346b0` is the
ordinary hit-response consumer. Only the guarded consumer multiplies raw damage
by the temporary factor from `FUN_003071c0`; the ordinary consumer's
instructions at `0x002349D4..0x00234A94` load record `+0x24`, divide by
`+0x2E`, and pass the result directly to the calculator. The observed Sakura
string used only the ordinary consumer.

For BTL-generated interaction records, the definition-to-runtime copy and
separate construction of damage float `+0x24` belong to
[collision record construction](collision.md#definition-to-runtime-copy).
That construction establishes the damage supplied by the primary and auxiliary
builders. Source-definition `+0x24` is a separate field, not the runtime
damage float consumed here.

Attack records are resolved identically by both consumers: fighter `+0xE54`
first; otherwise `FUN_002179f0` on retained source `+0xE58`, then on `+0xC74`,
only when the respective pointer and its kind word `+0x0C` are nonzero;
otherwise the resident `PL_ATK_DUMMY` record at `0x00407C00`, whose `+0x24`
damage is `0`, `+0x2E` is `1`, and `+0x50` is zero. `FUN_002179f0` accepts only
source objects carrying marker `0x474F` at `+0x02` and selects by source word
`+0x0C`: `0` returns a fighter source's current record `+0xA4C` only while that
fighter is in major state `8`; `1` asks live BTL `0x00734300`; `2` asks live
`0x00886850` with a side argument. Any other or missing result falls back to
the dummy record. These two consumers do not invoke the getter's kind-`0`
fighter branch through their retained-source fallbacks. The writers of
`+0xE58/+0xC74` and the source provenance belong to the
[accepted-hit source boundary](target_selection.md#accepted-hit-source-boundary).

### Calculator formula

The calculator `FUN_00224e30` receives raw damage in `f12`, defender in `a0`,
flags in `a1`, and returns damage in `f0`. Defender `+0x20` points to the
attacker. It does not read the native combo manager or hit count. Each flag bit
enables one multiplicative factor, applied in this order:

| Flag | Factor | Source |
| ---: | --- | --- |
| `0x001` | attacker `+0x148` | Character-record offense multiplier |
| `0x002` | `m(defender +0x14C)` from the durability curve above, then `1.5` more when defender `s16 +0x80` is nonzero | Character-record durability; chakra-reservation class index |
| `0x010` | `A = FUN_00306bd0(attacker)` | Attacker temporary effects |
| `0x020` | `max(0.1, 2.0 - D)` with `D = FUN_00306c80(defender)` | Defender temporary effects |
| `0x100` | attacker `+0x16C` times defender `+0x170` | Handicap |

The result is finally clamped to `[0.0, 1.0]`. Bits `0x004`, `0x008`, `0x040`,
and `0x080` have no consumer in the calculator. The three native flag words in
retail callers are therefore:

- `0x133`: every factor;
- `0x122`: durability/reservation, defender effects, and handicap, but no
  attacker offense and no attacker effects;
- `0x100`: handicap only;
- none of the callers passes a word without `0x100`.

Defender `+0x80` is the signed reservation class index that
[`chakra_and_guard.md`](chakra_and_guard.md) shows is set to `1..3` while a
staged chakra reservation exists and cleared on release. Consequently a
defender holding a reservation takes `1.5` times the `0x2`-enabled damage.
The reservation's player-facing name is not established here.

Both temporary-effect folds walk the fighter's active-effect list
(`+0x8C4` count, `+0x8C8` head, next pointer at node `+0x1C`) and include only
nodes whose countdown `+0x6C` is nonzero:

```text
A = 1 + sum(node[+0x74] - 1)     then clamped to at most 2.0 when A != 1
D = 1 + sum(node[+0x78] - 1)     then clamped to at least 0.25 when D != 1
defender factor = max(0.1, 2.0 - D)
```

Node `+0x74/+0x78` are copied from effect-definition record `+0x14/+0x18`
([`battle_items_and_status_effects.md`](../projectiles_and_items/battle_items_and_status_effects.md#resident-effect-definitions)).
Several concurrent effects therefore add their deviations from `1.0` rather
than multiply. The defender fold is inverted: a node `+0x78` above `1.0`
reduces incoming damage and one below `1.0` increases it, with the combined
incoming factor bounded to `[0.1, 1.75]`. The attacker fold has an upper clamp
of `2.0` and no lower clamp; the calculator's final damage clamp is separate.
Neither fold reads controller bit `fighter +0x63:0x20`, a character ID, or an
awakening-class marker. A contributing node with any nonzero lifetime,
including a negative lifetime, remains eligible. The character-specific
effect-`0x2E` case in
[Awakening](../characters/awakening.md#exact-class-7-uj-entry)
illustrates why the effect list and controller marker cannot be interchanged.

### Arithmetic precision and clamp boundaries

The formula above describes the factors; the executable preserves an explicit
sequence of EE single-precision operations. `FUN_00224E30` has no integer HP
conversion, decimal rounding, or minimum positive damage. Its final
`c.le.S`/`c.lt.S` branches at `0x00225004..0x00225028` cap the calculated
amount at `1.0` and then floor it at `0.0`. This caps each call separately,
before HP subtraction; it does not cap the sum of a multi-event attack or
reduce an overkill event to the target's remaining HP.

The upper durability segment uses immediate bits `0x3E4CCCCC`
(`0.19999998807907104`), rather than the nearest float to decimal `0.2`
(`0x3E4CCCCD`). The two upper segments use `div.S` followed by an
`adda.S`/`msub.S` accumulator sequence at `0x00224EF8..0x00224F50`; their
algebraic simplification or a different coefficient would not preserve this
instruction order. The reservation factor is a separate `mul.S` after
durability, and the two Handicap factors are separate multiplications at
`0x00224FE8..0x00224FF4`; they are not first combined into one multiplier.
These sequences fix the EE operation order; they do not by themselves
establish every hardware rounding outcome.

The raw sample helper `FUN_00217AE0` uses `lh` for record `+0x2E`, converts
that signed integer with `cvt.s.W`, and performs `div.S` at
`0x00217AEC..0x00217B08`. Zero bypasses division; a negative divisor is not
rejected by this helper. There is no allocation of a remainder to the final
sample. Thus division is repeated floating-point damage, not integer damage
split into rounded installments. Authored validity of every divisor is a
separate data question.

Application is another rounding boundary: `FUN_00225050` executes
`sub.S` and stores the resulting HP for each call, at `0x0022516C..0x00225174`
in Practice or `0x002251B8..0x002251C0` otherwise. Practice compares against
the exact word `0x3C23D70A` (`0.009999999776482582`) and writes that word
when the result is at or below it. Outside Practice the zero comparison uses
the stored HP, even when fighter `+0x62` bit `1` suppressed subtraction.
Consequently an already-zero fighter can return knockout for a zero-damage
application; the return is not restricted to the transition from positive HP.

The damage counter and support notification precede HP subtraction. A counted
event receives calculated damage times `100`, including overkill or an event
whose non-Practice HP subtraction is suppressed by bit `1`. The counter is
therefore not a measurement of actual gauge loss. Bit `0` still suppresses the
whole application, and the retained Ultimate Jutsu record flags still suppress
the counter as described below.

### Damage-counter decimal conversion

The counter retains floating-point percentage at object `+0x10` and its
maximum at `+0x14`. Its popup-value helper, live BTL `0x006BB100`, stores the
incoming percentage at popup `+0x10`, multiplies by `10.0`, and converts with
EE `cvt.w.S` before extracting decimal digits into halfwords at
popup `+0x14..+0x1A`. The low digit is the tenths place. Up to four digits
are retained, and the popup's digit count is at least two, including leading
zero for a percentage below `1.0`. There is no `+0.5` bias or decimal-rounded
value written back into the percentage accumulator or HP.

The helper's entry, preserved `0x006BB0C0`, lies outside a mapped function;
its byte interval `0x006BB0C0..0x006BB1FF` establishes the store, multiply,
conversion, signed division-by-ten sequence, and digit-count writes. The
calls at preserved `0x006BBA30..0x006BBA3C` and `0x006BBBB8..0x006BBBC4`
supply maximum and current percentage respectively. The helper does not set
FPU rounding control. The known boot FCSR and its unresolved later lifetime
are documented in
[timer arithmetic limitations](../../runtime/timer_primitives.md#confidence-and-remaining-evidence-limits);
the conversion instruction is not an unconditional truncation or
round-to-nearest claim. The observed `6.5%` display for an HP subtraction of
`0.066` shows that the displayed digits are not the exact HP loss.

### Handicap factors

Fighter `+0x16C` and `+0x170` are initialized to `1.0` by `FUN_00216440`
(called by base fighter initialization at `0x00214CA0`) and rewritten by
`FUN_00216460`, which is called by character configuration `FUN_002151e0` and,
for both live fighters, when the pause flow `FUN_001ebd90` closes with result
`1`. `FUN_00216460` reads setting key `8` through `FUN_001f6e70` and computes:

```text
s = h / 10            for side 0 (fighter +0x60 bit 0 clear)
s = 1 - h / 10        for side 1
f = s * 0.5 - 0.25
fighter +0x16C = 1 + f     outgoing handicap factor
fighter +0x170 = 1 - f     incoming handicap factor
```

The key-`8` accessor case at `0x001F67F8` returns the signed byte at manager
`+0x9F9` (settings pack `+0x9F4`, byte `5`) only when manager `+0x0C` is `2`,
Free Battle; for every other mode it returns the neutral `5`. This is the
Battle Settings Handicap row documented in
[`practice_mode.md`](../modes/practice_mode.md#battle-settings-child). Neutral `5` gives
`1.0` for all four fields. At the extremes the side-0 fighter's outgoing and the
side-1 fighter's incoming factor are both `1.25` (`h = 10`) or `0.75`
(`h = 0`), so a flag-`0x100` hit is multiplied by `(1 + f_attacker) *
(1 - f_defender)`: `1.5625` in the favoured direction and `0.5625` in the
other.

### Damage application

`FUN_00225050(damage, fighter, display)` returns `1` when an admitted
non-Practice call finds HP at or below zero after its conditional subtraction:

1. Fighter byte `+0x62` bit `0` makes the whole call a no-op returning `0`.
2. When `display` is nonzero and the fighter's retained attack record `+0x7CC`
   is null or has none of record `+0x10` bits `0x00100000`, `0x00200000`, or
   `0x00400000`, it adds `damage * 100` to the damage-counter object returned
   by live BTL `0x006B4000(side)` for the **attacker's** side (defender side 0
   selects object 1 and vice versa). Live `0x006BB9A0` ignores non-positive
   values, accumulates the percentage at object `+0x10` with a `999.0` cap,
   and tracks its maximum at `+0x14`.
3. `FUN_00238830(damage, fighter)` receives the calculated damage before HP
   subtraction. Its recipient, gauge clamp, active-support gate, and full-gauge
   notification belong to
   [support gauge state](../characters/support_mechanics.md#gauge-state-and-availability).
4. In Practice (manager `+0x0C == 3`) it subtracts from HP `+0x6C` and raises
   any result at or below `0.01` to exactly `0.01`; it always returns `0`, so
   Practice damage cannot knock out.
5. In every other mode it subtracts only when byte `+0x62` bit `1` is clear.
   If HP is then at or below zero it stores `0`, clears byte `+0x61` bit `3`,
   and returns `1`.

The `+0x61` bit `3` cleared on knockout is the same bit that gates
ordinary-hit damage below, chakra gain, and timed downed recovery. The
attacker-side support-gauge gain is separate: the attack-record consumers call
`FUN_00238950(raw, defender)` with the pre-calculator raw damage, and that
routine adds to the gauge of the fighter at defender `+0x20`.

### Simultaneous hits and knockout boundaries

Damage application changes one fighter's HP/life bit and returns its local
knockout result. It does not latch the match result or prevent another
fighter's damage call. The double-zero classification, first-result latch,
timeout comparison, and possible condition override belong to
[match termination](../session/match_outcomes.md#terminal-detector-and-classifier).
Whether two damage events finish before that detector runs is therefore
material; simultaneous input alone does not establish a double knockout.

The paired-hit resolver's simultaneous-hit path at `0x0021F240..0x0021F2DC`
and its countdown precondition belong to
[hit response](hit_response.md#rehit-suppression). Its damage
consequences are these. `FUN_00221120`, which puts both fighters into ordinary
response `0x5B` or `0x5C`, contains no calculator or HP-subtraction call. The
resolver then passes each opposing record to `FUN_00222A80`, which stores it at
fighter `+0xE54` when it changes and copies its sample count to `+0xE5C`,
subject to its repeated-record gate. It also clears both fighters' ordinary
incoming/outgoing bits before its later per-attacker `FUN_0021F610` branches,
so that accepted-hit helper's pending-combo producer is bypassed for this
arbitrated pair; this does not exclude separate pending-count producers.

Both fighters' ordinary-response damage consumers can therefore read the
opposing record through the existing record-resolution path. The response
states `0x5B/0x5C` have no special shared-damage amount or averaging branch
in `FUN_002346B0`: the ordinary flags, raw sample arithmetic, coordinator
gate, and life-bit gate still apply separately. This establishes the static
route from paired arbitration to ordinary damage, not a guarantee that both
applications occur in every simultaneous contact.

### Ordinary-hit damage gates

`FUN_002346b0` applies damage only when all of these hold:

- defender byte `+0x61` bit `3` is set;
- attack record `+0x10` bit `0x01000000` is clear;
- attack record `+0x14` bit `0x02000000` is clear;
- the defender is not in response `(5, 0x42..0x49)`; those contact-stage
  substates receive their fixed damage from `FUN_002312b0` instead;
- coordinator state `FUN_00250820()` is not `6`;
- the per-sample raw value is nonzero.

It uses `0x133` when record `+0x10 & 0x000C0000` is zero **and** record word
`+0x50` is nonzero; otherwise it uses `0x122`. Therefore attacks with either
`+0x10` bit `0x40000`/`0x80000` or a zero `+0x50` ignore the attacker's
character offense and temporary attack effects.

### Guarded-hit damage

`FUN_00228b50` skips its HP-damage block for record `+0x10` bit `0x01000000`.
Otherwise it computes a guard factor:

```text
base  = 0.5 when attack record +0x14 bit 0x01000000 is set, else 0.0
G     = max(base, FUN_003071c0(attacker))
```

`FUN_003071c0` returns the largest node `+0x90` among the attacker's active
temporary effects, starting from `0.0`; node `+0x90` is effect-definition
record `+0x30`; only nonzero-lifetime nodes participate. When `G` is zero no
guard damage occurs. Otherwise it calls `FUN_00238950` with the per-sample raw
value (`record[+0x24] / record[+0x2E]` when the divisor is nonzero, else
`record[+0x24]`), then applies `G * per_sample_raw` through the calculator with
`0x133` when record
`+0x10 & 0x000C0000` is zero, else `0x122`, unless the coordinator state is
`6`. Unlike the ordinary path it does not test record `+0x50`. Consequently a
blocked ordinary attack deals no HP damage unless its record sets `+0x14` bit
`0x01000000` (half damage) or the attacker has an effect granting a guard
factor; the larger of the two applies. The support-gauge helper precedes the
coordinator/raw-zero gates and receives the raw sample without `G`. The same
routine also updates the guarded-hit count, independently of whether the
HP-damage block ran; that count belongs to [hit count](hit_response.md#hit-count).
This identifies attack flag `0x01000000` in record `+0x14`, left unnamed in
[`chakra_and_guard.md`](chakra_and_guard.md), as the static half-chip-damage
selector.

### Damage caller coverage

The ordinary main call is from `FUN_002346b0` to `FUN_00224e30` at runtime
`0x00234A80`, ELF offset `0x134B80` under the boot-ELF
[address conventions](../../game/files/file_identities.md#address-conventions).
Retail `SLPS_258.37` contains instruction bytes `8C93080C` there, the
little-endian encoding of `jal FUN_00224e30`.

`FUN_00224e30` is shared by ten static call sites. Their bounded roles and the
call counts observed in the Sakura string above are:

| Runtime call | Static owner / role | Observed calls |
| ---: | --- | ---: |
| `0x0022529C` | `FUN_00225230`, generic nonzero-damage wrapper with two resident callers and one BTL caller | 0 |
| `0x002252F4` | `FUN_002252e0`, Ultimate Jutsu cinematic damage with flags `0x100`, called from `FUN_0035b740` | 0 |
| `0x00228D18` | `FUN_00228b50`, guarded-hit attack-record damage | 0 |
| `0x00231634` | `FUN_002312b0`, fixed `0.04` response/contact-stage branch | 0 |
| `0x00231698` | `FUN_002312b0`, fixed `0.02` response/contact-stage branch | 1 |
| `0x002334BC` | `FUN_002333a0`, direct damage retaining source/attack-record evidence, with 15 BTL callers | 0 |
| `0x00234A80` | `FUN_002346b0`, ordinary attack-record damage | 8 |
| `0x00236354` | `FUN_00235c60`, fixed `0.05` in special response/recovery substate `0x61` | 0 |
| `0x0024F00C` | `FUN_0024ed40`, zero-raw state/outcome path | 0 |
| `0x0035B2F8` | `FUN_0035af20`, skill-play completion damage-counter calculation without HP subtraction | 0 |

`FUN_00225050` is called more widely and does not carry the attack flags or
the raw-damage boundary. The fixed call at runtime `0x00231698`, ELF offset
`0x131798`, is the `0.02` branch of `FUN_002312b0`, an initializer used only
for ordinary response substates `0x42..0x49`; a per-state flag can select its
`0.04` branch instead. In the observed string it ran during the third visible
hit while the target's response was still `(5,0x3D)`, and the target
afterwards reached `(5,0x43)`. This matches the documented promotion from the
`0x3C..0x41` launch group into the `0x42..0x47` contact-stage group in
[`hit_response.md`](hit_response.md#response-exits).
It is therefore fixed response/contact-stage damage, not a second accepted
hit; its native damage was `0.022`, separate from the main attack-record
event. The evidence does not assign a visual authoring name such as “wall
splat” to that raw state family. The fixed `0.04` sibling is at runtime
`0x00231634`, ELF offset `0x131734`, with the same `jal` bytes `8C93080C`;
its execution has not been observed.

The sibling's exact static gate is bounded. Target substates `0x42` and `0x43`
select `0.04` when fighter word `+0xBB0` has bit `0x400`; substate `0x44`
tests `+0xBBC`; and substates `0x45..0x47` test `+0xBB4`. If the applicable
bit is clear, and for substates `0x48/0x49`, the initializer uses `0.02`.
After the `0.04` damage branch it may also invoke an object callback through
fighter `+0x28`. This damage choice depends on the target response and
environment flag, not the current combo count.

The `0x400` prerequisite comes from stage collision attributes. Among the 24
retail stage archives, only `S08.CCS` (load slot 7, logical stage 8) has
authored collision triangles whose word includes `0x400`: group 2 of
`HIT_s08are00_hit_s3`, two triangles with word `0x00959595`
([stage-authored attribute distribution](../stages/stage_surface_attributes.md#stage-authored-attribute-distribution)).
Their six authored vertices span approximately `x=-824..-713`,
`y=736..923`, `z=1059..1124`. Practice's bootstrap stage, load slot 6
(`S07.CCS`), has none, so it cannot supply that prerequisite through authored
stage geometry.

## Direct-damage wrappers and character exceptions

Direct damage is separate from ordinary attack-record damage. A complete
byte-pattern search for the direct `jal` encodings found no calls to
`FUN_00224E30` or `FUN_00225050` in either `BTL.BIN` or `ETC.BIN`. BTL instead
calls `FUN_00225230` once and `FUN_002333A0` fifteen times; ETC calls neither.
Neither overlay directly calls `FUN_002252E0`. These are direct-call bounds,
not a claim that indirect calls or undiscovered code cannot exist. Overlay
addresses below are live, preserved, or complete-file offsets under the
[address conventions](../../game/files/file_identities.md#address-conventions).

### Direct signed HP adjustment from effects

`FUN_00306090(delta, bound, fighter)` is an additional resident caller of
`FUN_00225050` that bypasses `FUN_00224E30` entirely. It admits the call only
when fighter `+0x62` bit `0` is clear and `FUN_00244110`,
`FUN_00244130(fighter)`, and `FUN_00244130(fighter[+0x20])` all return zero.
An exact bound of `-1.0` skips its limit adjustment. Otherwise positive
`delta` is shortened to reach the upper bound without lowering existing HP,
and negative `delta` is shortened to reach the lower bound without raising
existing HP. A resulting zero delta does nothing.

Positive deltas call the HP-adder `FUN_00224D10`; negative deltas pass
`-delta` directly to `FUN_00225050` with display argument `0` at
`0x003061E0..0x003061FC`. No offense, durability, reservation, temporary
damage factor, Handicap, or calculator `[0,1]` clamp is applied to that
amount. The application helper still supplies its support notification and
Practice/non-Practice HP rules; the caller ignores its knockout return.
The entry/expiry effect payloads and their supplied bounds belong to
[resident effect definitions](../projectiles_and_items/battle_items_and_status_effects.md#definition-table).
This consumer establishes their signed HP role without assigning item or
status names to every payload.

### Generic wrapper `FUN_00225230`

This wrapper receives raw damage in `f12`, defender in `a0`, and calculator
flags in `a1`. It returns zero without applying damage when coordinator state
is `6` or raw damage is exactly zero. Otherwise it calculates damage at
`0x0022529C` and returns the knockout result of
`FUN_00225050(result, defender, 1)` at `0x002252B0`. It does not resolve an
attack record or update the native pending-hit byte itself.

The three established direct callers are:

| Caller | Call address / complete-file offset | Raw damage and flags | Static gate |
| --- | --- | --- | --- |
| Resident `FUN_002BDF80` | `0x002BF780 / 0x1BF880` | `FUN_00217AE0(attacker, record)`, `0x133` | Fighter ID `0x43` (Rock Lee), major state `8`, action index `0x33`, phase `+0x192 == 0`, secondary timeline event `0xF` after event `0xE` is absent |
| Resident `FUN_002D5320` | `0x002D5590 / 0x1D5690` | constant `0.004` (`0x3B83126F`), `0x133` | Fighter ID `0x4C` (Sasori/Hiruko), major state `8`, action index `0x17`, phase `+0x192 == 1`; this branch also selects response `0x3D` |
| BTL helper `FUN_0072E700` with continuation `FUN_0072E740` | live `0x0072E7F0 / 0x7A8F0`, preserved call `0x0072E7B0` | object `+0x258` times incoming `f12`, then times `0.5` when incoming selector `a2` is nonzero; `0x122` | Registered object with kind word `+0x0C == 1`; object halfword `+0x78 == 0x31` forces raw zero |

The character names follow the numeric IDs in the
[character reference](../characters/character_ids.md). They identify the routine's ID gate,
not a recovered move name. `FUN_00217AE0` reads record `+0x24`, divides by
signed record `+0x2E` when nonzero, and calls `FUN_00238950` before returning
the raw amount. Consequently Rock Lee's extra direct event still has a
pre-calculator support-gauge side effect. The Sasori/Hiruko constant does not
pass through that helper. The raw and applied damage writers' distinct
recipients and gauge gates belong to
[support gauge state](../characters/support_mechanics.md#gauge-state-and-availability).

The entire BTL object-hit helper first requires resident `FUN_00376610()`
to return nonzero. That helper returns a resident global object's word
`+0x20`, or zero when the global pointer is null; the meaning of that word
is not established by this damage path. BTL's input register roles are explicit
at preserved
`0x0072E720..0x0072E72C`: object `a0` is saved in `s2`, struck fighter `a1`
in `s1`, selector `a2` in `s4`, and incoming magnitude `f12` in `f20`.
Preserved `0x0072E784..0x0072E7B4` performs the magnitude/half-factor calculation
and supplies defender `s1` and flags `0x122`. The same hit/result helper then
handles item-code effects, whose separate lifecycle belongs to
[hit-carried direct effects](../projectiles_and_items/battle_items_and_status_effects.md#direct-effect-records-carried-by-hit-objects).
Its damage call therefore covers an object-hit path, rather than only the two
resident character exceptions.

The object-damage getter is live `0x007366B0`; its entry, preserved
`0x00736670`, lies outside a mapped function. It starts with result `0.0`,
requires the object-manager global, a non-null object, and object kind
`+0x0C == 1`, then searches the manager's list at `+0x14` using object next
`+0x60`. Only membership returns object `+0x258`; no item-code damage lookup
is present. Item code `+0x7A` is retained for the later effect mapping instead.

### Source-retaining wrapper `FUN_002333A0`

The register contract is raw `f12`, struck fighter `a0`, source object `a1`,
and retained attack record `a2`. At `0x002333E0..0x00233484`, a non-null source
with marker `0x474F` at `+0x02` can replace fighter `+0x7C8/+0x7CC` and save
fighter `+0x63` bit `7` at `+0x830`, provided both helper gates
`FUN_00221520` and `FUN_00216820` return zero. Source word `+0x0C == 0`
retains the source pointer directly; other kinds are copied through
`FUN_00221460` to fighter `+0x7D0` first. Failing these source gates does not
prevent damage: the independent damage branch at `0x00233488..0x002334D4`
requires only coordinator state other than `6` and nonzero raw damage. It uses
flags `0x122` and display argument `1`.

After that branch, when fighter `+0x61` bit `3` is clear, it calls
`FUN_00216A60` on the struck fighter and on fighter `+0x20`. No native combo
increment is present in this wrapper. Its callers determine the source,
record, and raw amount separately. The retained recovery-source fields and
this cleanup do not establish ordinary response initialization; their response
lifetime belongs to [accepted-hit routing](hit_response.md#accepted-hit-routing).

### All fifteen BTL source-retaining calls

Every direct BTL caller supplies retained record runtime `0x008DAA10` and
source `target[+0x20]`. The target is the caller object/link's saved fighter
pointer (`+0x4CC` in twelve sites, `+0x9D4` in the three guard-sensitive
sites). The retained record is in BTL's zero-cleared BSS; the shared raw
value at runtime `0x008CC490` is file-backed data. The file/BSS boundaries
belong to the [overlay layout](../../runtime/overlay_abi.md#exact-clean-layouts).
Their initialization is established below; the caller bounds do not assign
class or move names.

| Preserved call | Live call / BTL file offset | Raw damage source | Caller context |
| ---: | --- | --- | --- |
| `0x00789890` | `0x007898D0 / 0xD59D0` | record held in `s0`, `+0x24` | record response byte `+0x2C == 0x28` in `FUN_00789630` |
| `0x0079FEC8` | `0x0079FF08 / 0xEC008` | shared runtime `0x008CC490`, initialized to `0.03 / 23` | `FUN_0079FDC0` |
| `0x007A5038` | `0x007A5078 / 0xF1178` | caller record pointer `+0x208`, record `+0x24` | continuation of `FUN_007A4EC0` |
| `0x007AFE24` | `0x007AFE64 / 0xFBF64` | caller `+0xB20 * 0.5` | target guard `+0x95A != 0`; caller `+0x9D8 == 0` |
| `0x007AFEE8` | `0x007AFF28 / 0xFC028` | caller `+0xB20` | target guard `+0x95A == 0`; caller `+0x9D8 == 0` |
| `0x007B0A14` | `0x007B0A54 / 0xFCB54` | caller `+0xB20 * 0.5` | target guard `+0x95A != 0`; caller `+0x9D8 == 0`; its unguarded branch has no corresponding direct-damage call |
| `0x007C2E48` | `0x007C2E88 / 0x10EF88` | caller record pointer `+0x208`, record `+0x24` | continuation of `FUN_007C2CD0` |
| `0x007CDC2C` | `0x007CDC6C / 0x119D6C` | fighter saved at caller `+0x31C`, current record `+0xA4C`, damage `+0x24` | `FUN_007CDB10` |
| `0x007D4578` | `0x007D45B8 / 0x1206B8` | shared runtime `0x008CC490`, initialized to `0.03 / 23` | `FUN_007D4470` |
| `0x007D4FC8` | `0x007D5008 / 0x121108` | caller record pointer `+0x208`, record `+0x24` | continuation of `FUN_007D4E50` |
| `0x007D808C` | `0x007D80CC / 0x1241CC` | fighter saved at caller `+0x31C`, current record `+0xA4C`, damage `+0x24` | `FUN_007D7F70` |
| `0x007DCEF0` | `0x007DCF30 / 0x129030` | fighter saved at caller `+0x31C`, current record `+0xA4C`, damage `+0x24` | `FUN_007DCD00`; a separate emitted record is also assigned descriptor `+0x28 * current-record +0x24` before this call |
| `0x00805210` | `0x00805250 / 0x151350` | caller `+0xFFC`, conditionally halved, times linked current-record `+0x24` | `FUN_00804E00`, primary contribution in byte-`+0xFF0` state `2` |
| `0x00805300` | `0x00805340 / 0x151440` | caller `+0xFF8` | `FUN_00804E00`, second contribution in the same state |
| `0x00808504` | `0x00808544 / 0x154644` | `0.5 * descriptor[+0xF4] * linked current-record[+0x24]` | continuation of `FUN_008081C0`; active when target is guarded or in `(5,0x4F)` |

The shared raw float's file word at offset `0x218590` is initially zero
(preserved data `0x008CC450`). The ninth automatic BTL constructor, live
`0x008D6060`, writes it at live `0x008D6084` (file `0x222184`). Preserved
bytes `0x008D6028..0x008D6047` load float bits `0x3CF5C28F` (`0.03`) into
`f1`, load runtime `0x008CC488` (`23.0`) into `f0`, divide `f1 / f0`, and
store the result to runtime `0x008CC490`. The result is approximately
`0.00130434777`, before flags `0x122` apply. The constructor's automatic
ordering belongs to the [constructor interval](../../runtime/overlay_abi.md#constructor-interval).

The shared record is set up at preserved `0x0077738C..0x007773BB`, which pass
runtime `0x008DAA10` to resident `0x00210B10`, then overwrite record word
`+0x10` with `0x00040000` and bytes `+0x2C/+0x2D` with `0xFF`. Resident bytes
`0x00210B10..0x00210BB7` establish damage `+0x24 == 0`, divisor
`+0x2E == 1`, and `+0x50 == 0`, among the base record defaults. The direct
wrapper receives each caller's explicit `f12` amount independently of this
record's zero damage field.

That setup lies in the `0x3330`-byte BTL owner constructor at live
`0x00777130`, the `ccSkillCtrl` service owned as described in
[BTL skill-service callbacks](../session/battle_auxiliary_services.md#btl-skill-service-callbacks-and-ownership),
so the record is reset on each owner construction, not only by BSS clearing on
overlay load. The sole direct constructor call found in the resident/BTL images
is at live `0x00776AF4`: the surrounding allocator requests `0x3330` bytes,
constructs the non-null result, and stores it at resident `gp - 0x31AC`
(`0x00607844`). The constructor's byte interval through preserved
`0x00777457` joins the record reset to its epilogue. Every execution of that
constructor therefore restores the shared record defaults and flag/response
overrides.

An exact-address search for immediate-low-word pattern `10 AA ?? 24` and full
pointer `10 AA 8D 00` in both images finds 17 BTL low-word candidates: the one
reset, the fifteen listed wrapper arguments, and an unrelated resource-name
pointer to live `0x008BAA10` in `FUN_00860600`, whose `lui 0x008C`
distinguishes it from the record loads' `lui 0x008E`. No full pointer or
matching low-word candidate occurs in the resident image, and no full pointer
occurs in BTL. The fifteen readers only pass the pointer to the wrapper; the
reset is the only writer within this bound. This does not audit every derived
pointer or later mutation through an arbitrary alias.

The raw float has a separate, narrower static lifetime. A BTL search for
immediate bytes `90 C4` finds the two tabled loads, the automatic constructor's
store at preserved `0x008D6044`, and an unaligned match at `0x0077320B`. The
two callers load its value into `f12`; they do not pass its address to another
routine. Owner destruction at live `0x007774A0` cleans registered skills and
owned descriptor/resource allocations but does not write this float or the
shared record. Preserved `0x00776AE0..0x00776B3F` calls that destructor through
owner table `+0x08` with deletion argument `1` and clears global `0x00607844`.
The raw value is thus initialized by the overlay constructor, rather than
recomputed on each skill or owner teardown. This bound does not rule out a
separately constructed alias or an external overlay-memory write.

#### Fighter-held aliases of the shared record

The direct wrapper creates an alias at target fighter `+0x7CC`; it does not
copy the record or its damage field. The source object's separate copy at
`+0x7D0` is not a record copy. Replacement and persistence of this fighter
pointer belong to
[retained recovery-source lifetime](hit_response.md#input-recoveries).
Consequently skill destruction and record-pointer replacement are separate
events; the record is shared BTL storage rather than storage inside a skill.

A resident search for immediate bytes `CC 07` finds 19 canonical matches.
Eighteen are aligned instructions in the fighter bodies below; the remaining
match at `0x003E537A` is unaligned. The inspected consumers are
`FUN_00223450`, `FUN_00225050`, `FUN_0022A890`, `FUN_0022ADD0`,
`FUN_0022B160`, `FUN_00233870`, `FUN_00236E10`, and `FUN_0023B280`.
They read record flags, compare the pointer with `PL_ATK_DUMMYDROP`, or use
non-nullness to admit later fighter/timeline operations. None writes through
the loaded record pointer in its inspected body. The other aligned matches
are initialization and the source/record replacement writers owned by the
linked response document. This bound does not enumerate computed field
addresses or every alias that another routine could retain.

BTL has three `CC 07` matches. The match at preserved `0x007C9C78` loads
a constant float, not a fighter record. The other two are destructor paths
at preserved `0x00812200` and `0x00814B60`: each loads its linked fighter
from object `+0x31C`, admits that fighter through resident `0x003083A0`,
then reads fighter `+0x7CC`. Their decisive intervals
`0x00812230..0x0081238B` and `0x00814B90..0x00814CEB` read record
`+0x10 & 0x000F0000` after object-registry and target-state gates. A true
branch calls an auxiliary object's virtual slot `+0x80`; the retained record
is not supplied as a call argument. Neither interval mutates or frees the
record. The initialized shared flags `0x00040000` satisfy that mask if this
pointer is still retained, but actual execution of these teardown branches
is not established.

#### Shared wrapper and combo-call contracts

The twelve `+0x4CC` sites require caller byte `+0x539` nonzero and resident
predicate `0x003083A0(target)` nonzero. The linked current-record reads use
caller byte `+0x389`, fighter pointer `+0x31C`, and the same predicate. That
predicate, resident bytes `0x003083A0..0x003083C8`, is a simple non-null
argument/non-null `gp - 0x339C` global check returning `0/1` with a real
`jr ra`. It does not validate a marker or dereference the fighter. The
disassembler treats these calls as non-returning and discards their success
branches, so the calls at preserved `0x007A5038`, `0x007C2E48`,
`0x007D4FC8`, and `0x00808504`, and the current-record joins before
`0x007CDC2C`, `0x007D808C`, `0x007DCEF0`, and `0x00805210`, rest on
instruction bytes. They establish instruction behavior, not observed
execution.

All fifteen sites first flush a positive per-side accumulated-hit word at
linked owner `+0x3268 + 4*side` through `FUN_0020C2E0(side, accumulated)`,
then clear it. The twelve object/link sites resolve owner/side through caller
`+0x0C/+0x350`; the three guard-sensitive sites use `+0x68/+0x958`. That
accumulated route belongs to
[Combo accounting](combo_accounting.md#per-side-accumulated-contribution-route),
and the flush inventory and metric publication to
[accepted ninjutsu and combo flushing](../session/battle_statistics.md#accepted-ninjutsu-and-combo-flushing).

The two shared-float callers then add one to the primary fighter's pending
byte `+0xA45` through `FUN_00239230(fighter, 1)` at preserved `0x0079FEE8` and
`0x007D4598`, selecting the fighter through caller side `+0x350` and manager
slot `+0xDE4 + 4*side`
([primary-fighter aliases](../session/battle_entities.md#manager-allocation-and-alias-slots);
[other direct byte producers](combo_accounting.md#other-direct-byte-producers)).
The call order is accumulated-count flush, optional direct damage, then
pending-byte increment; the increment occurs outside `FUN_002333A0`. It does
not queue an `+0xE3C` response request or invoke accepted-hit router
`FUN_002209A0`.

The guard-sensitive sites therefore deal direct half damage through flags
`0x122`, independently of the ordinary guarded-hit consumer's record/effect
chip factor. Guard outcome alone does not identify one calculator path. The
selected class joins are owned by
[Battle entities](../session/battle_entities.md#btl-skill-classes-on-damage-paths); the
FOR/ANB arithmetic is established below. The other class joins and
player-facing move identities remain unresolved.

#### Shared-float helper gate

The routines named `FUN_0079FDC0` and `FUN_007D4470` above are continuations
inside helpers whose complete entries are preserved `0x0079FD80` and
`0x007D4430`. Their calling methods and internal classes
(`ccSkillNRW001`/`ccSkillNRT001B` and `ccSkillNRV001`/`ccSkillJRW001`) are
joined in [shared-float caller classes](../session/battle_entities.md#shared-float-caller-classes).

The complete helper entry requires object pointer `+0x144` nonzero, converts
unsigned halfword `+0x14A` to float, and admits its event when that value is at
least live constant `0x008CC480` (`1.0`). It then clears `+0x14A` before the
combo flush and optional direct-damage branch. Preserved
`0x0079FD80..0x0079FE07` and `0x007D4430..0x007D44B7` establish the gate. The
amount `0.03 / 23` is shared value data, not a damage float read from the
active `+0x208` interaction record. The owner of `+0x14A` advancement and
complete availability of both derived classes remain untraced.

#### Record-damage caller `ccSkillTYO000B`

The direct call at preserved `0x007A5038` belongs to method live `0x007A4F00`
of internal class `ccSkillTYO000B`, factory index `31`
([class join](../session/battle_entities.md#ccskilltyo000b)). The method loads its active
`+0x208` record's `+0x24` at preserved `0x007A4F74..0x007A4F78` and uses the
loaded value unchanged in `f12` at `0x007A5034`. Caller byte `+0x5F4` must be
nonzero before the combo flush and optional wrapper branch; the target still
uses the ordinary `+0x539/+0x4CC` gates above. Complete bytes
`0x007A4EC0..0x007A5063` recover this method. The selected descriptor's `+0x28`
contains float `1.0`, but this authored field alone does not establish the
producer of the active `+0x208` record. That producer and the player-facing
move identity remain open.

### Skill multiplier gates and paired recovery

The two contributions in preserved `FUN_00804E00` belong to internal class
`ccSkillFOR000`, whose vtable slot `+0x100` holds live update `0x00804E40`
([class identity and lifetime](../session/battle_entities.md#ccskillfor000-allocation-and-lifetime)).

Its constructor initializes cumulative value `C = object[+0xFF4]` to
float bits `0x3F19999A` (`0.6`) and step `q = object[+0xFFC]` to
`0x3D149B93` (approximately `0.03628118`). Its setup takes the linked
fighter's then-current attack record damage `R0`, stores `C * R0` at
`+0xFF8`, then divides that stored value by `63.0`. The linked-record getter
has the same object-byte/predicate gates described above. The setup arithmetic
is preserved `0x00804BFC..0x00804C58`; the constructor values are in
`FUN_00804670`. The secondary raw amount is therefore a setup snapshot,
whereas the primary amount reads the linked fighter's current record anew.

Byte-state `+0xFF0 == 2` admits the damage/recovery update while unsigned
counter `+0xFF2 < 64` and resident `0x003737A0()` does not return `1`.
On an admitted update, the control predicate at live `0x00806680` determines
whether the primary contribution occurs. When it returns `1`, the update
first stores `C + q` back to `+0xFF4`, then uses the new `C`:

```text
C <= 1.0:           primary_raw = q * current_record_damage
1.0 < C <= 1.2:     primary_raw = (q * 0.5) * current_record_damage
C > 1.2:            no primary damage or primary recovery call
secondary_raw = object[+0xFF8] = (setup_C * setup_record_damage) / 63.0
```

Both thresholds are stored float constants (`1.2` is `0x3F99999A`). The
instructions at preserved `0x00805094..0x00805108` confirm the first
`C <= 1.2` branch excludes the whole primary contribution. An inner repeated
comparison contains code that would shorten a step exceeding `1.2`, but the
unchanged `C` has already passed the identical outer comparison; that inner
over-limit arm cannot execute on this path. The cumulative value is left above
`1.2` when the outer branch skips the contribution. This is a skill-owned
multiplier gate, with no read of the native combo hit count.

For each contribution it optionally calls `FUN_002333A0(raw, target,
target[+0x20], shared_record)` under the target-object validity gates, then
independently calls `FUN_00224D10(raw * 0.5, linked_fighter, 0, 0)`.
The secondary contribution runs on every admitted update, even when the
primary control predicate is false or its cumulative limit is exceeded.
Preserved `0x008051D4..0x0080532C` establishes both optional damage calls
and their following recovery calls. Counter increment and the later exit
conditions are separate from the primary contribution gate.

Recovery uses half the **raw** contribution; it does not use half the
calculator result or measured target HP loss. The adder performs only its
own bit-`0` and life-bit admission, HP addition, and `1.0` cap. These calls
do not use character recovery field `+0x160` or an effect recovery fold.
Target damage can therefore be suppressed by the direct wrapper's
coordinator gate or the target's application gates while the linked fighter's
recovery call still occurs. No success return ties the two operations
together. This describes the static branch relationship, not ordinary-play
availability of the class or its full object-reuse lifetime.

#### FOR damage-state lifetime

The constructor initializes `C`, `q`, and a zero secondary amount. The setup
body at preserved `0x00804A40..0x00804C7F` recomputes `+0xFF8` from the
then-current `C` and linked attack record; it does not restore `C = 0.6` or
`q`. Repeating this setup on an existing object would therefore take a new
secondary snapshot using its existing cumulative value; this is a static
consequence, not proof of a normal reuse route. The inspected spawn route
creates a fresh allocation before setup.

The local state setter, live `0x008056A0` with real prologue preserved
`0x00805660`, stores the requested byte-state at `+0xFF0`. State `0` clears
`+0xFF2`, and state `3` clears that counter after its release actions, while
state `2` performs entry/descriptor actions without clearing it. None of these
branches resets `C`, `q`, or the secondary snapshot. Preserved
`0x00805660..0x00805DDB` recovers the complete setter. State `0`'s earlier
update can advance the same counter before state `2`; the number of
contribution updates is therefore determined by the counter value on entry,
not unconditionally 64.

### Guard-or-response skill contribution

The preserved `FUN_008081C0` contribution belongs to internal class
`ccSkillANB000`, whose vtable slot `+0x1A0` holds live method `0x00808200`
([creation and destruction](../session/battle_entities.md#ccskillanb000-creation-and-destruction)).

After its initial cleanup, this method admits the damage branch when the
target's signed guard field `+0x95A` is positive, or when the target is in
ordinary response `(5,0x4F)`. It resolves the descriptor from object `+0x56C`
only for index `0..196`, through the first word of the eight-byte table entry
at live `0x008AD8E4 + index*8`. The raw amount is
`(descriptor[+0xF4] * linked_current_record[+0x24]) * 0.5`, using separate
`mul.S` instructions at preserved `0x00808428..0x00808444`. It flushes the
accumulated combo count and optionally calls the same source-retaining wrapper
under the target gates. The guard-or-response choice does not read the
ordinary guarded-hit effect factor `G`; this half amount is then processed
with wrapper flags `0x122`. No corresponding HP-recovery call occurs in
this bounded contribution. Preserved bytes `0x0080824C..0x00808510`
establish the decisive branch and call interval. The method's other
state/effect actions are outside the damage arithmetic, and the internal class
name does not identify its player-facing move.

The descriptor getter uses `lui 0x008B` followed by signed
`addiu -0x271C`, at preserved `0x008083D4..0x008083D8`, so its live base
is **`0x008AD8E4`**. The common initializer uses the same sequence at
`0x0078E828..0x0078E82C`. The pointer table and the actual descriptor
words corroborate this address. The five authored ANB records supply different
multipliers to the same contribution:

| Selector `+0x56C` | Live descriptor | Descriptor `+0xF4` bits / value | Common setup's CCS name |
| ---: | ---: | --- | --- |
| `3` | `0x008A8358` | `0x3F800000` / `1.0` | `2sskcha1.ccs` |
| `11` | `0x008A8688` | `0x3F99999A` / approximately `1.2` | `2kkscha1.ccs` |
| `53` | `0x008A9B84` | `0x3F800000` / `1.0` | `2anbcha0.ccs` |
| `89` | `0x008AA800` | `0x3FACCCCD` / approximately `1.35` | `2ssvcha1.ccs` |
| `143` | `0x008AC208` | `0x3F8CCCCD` / approximately `1.1` | `2kkwcha1.ccs` |

The CCS names come from selector-indexed live table `0x008A7AA0`, consumed
by common initialization at preserved `0x0078E6F4..0x0078E710` before the
class setup. They establish authored resource selection, not a translated
move name. The current selector resolves the damage multiplier on each
contribution rather than through a constructor-time damage snapshot. FOR
selector `22` separately resolves live descriptor `0x008A8B50` and common CCS
name `2orccha0.ccs`; its contribution arithmetic above does not consume that
descriptor's `+0xF4` factor.

### Ultimate Jutsu and damage-counter-only calls

`FUN_002252E0` preserves raw `f12`, supplies flags `0x100` at
`0x002252F0`, calculates at `0x002252F4`, and applies the result with display
argument `1` at `0x00225308`. It lacks the generic wrapper's coordinator-state
and raw-zero gates. Its resident caller `FUN_0035B740` is the cinematic hit
callback; the fraction/remaining-total arithmetic belongs to
[Ultimate Jutsu damage](../characters/ultimate_jutsu.md#damage).

The calculator call in skill-play completion `FUN_0035AF20` at
`0x0035B2F8` also uses `0x100`, but sends `result * 100` only to BTL's damage
counter. There is no adjacent `FUN_00225050` call or HP subtraction. Its branch
is not restricted to Practice mode. The coordinator's state-`6` completion
call at `0x0024F00C` likewise uses `0x100` with raw zero before applying the
result and deciding the post-cinematic effect/KO branch; it does not introduce
another nonzero attack amount.
