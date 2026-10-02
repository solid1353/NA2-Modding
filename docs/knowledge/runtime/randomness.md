# Resident randomness

This document records the resident random-number facilities in retail NA2
(`SLPS-25837`) and the way `BTL.BIN` consumes them. It is a static
reverse-engineering result for the clean `SLPS_258.37`; it does not assign
gameplay meaning where the caller only establishes data flow.

## Research coverage

- **Assigned scope:** the resident random-number state and algorithms, their
seed/reset lifecycle and wrappers, and direct use of that surface by `BTL.BIN`,
with representative non-damage callers sufficient to establish semantics.
- **Exploration depth:**
  - Resident coverage is exhaustive for the three identified shared streams and
    their known entry points: `FUN_0017b780`, `FUN_0017b798`,
    `FUN_0017fd90`, and `FUN_00180060..FUN_00180560`. Their direct xrefs, exact
    state addresses, initializer/setter paths, clean-image values, instruction
    constants, wrapper branches, and MT-word consumption were traced. Clean ELF
    bytes were checked for the initialized tag/index, LCG state, twist table,
    zero-fill boundary, and complete MT state layout. This is not a claim that
    every caller-owned small recurrence elsewhere in the resident executable is
    an additional member of this shared RNG surface.
  - Direct BTL-import coverage is exhaustive for aligned absolute `jal` opcodes
    targeting those entry points across the complete clean `BTL.BIN`. Decoded
    listing calls and raw opcode words were counted separately. All 193 wrapper
    opcodes omitted by Ghidra were assigned to 92 undefined spans and each span
    received a static-entry audit. All 11 physical LCG-output opcodes were also
    classified: three camera-table selectors, six 42-vector selectors, and two
    coherent blocks with no static incoming edge. The bounded audit establishes
    direct imports of the known surface; it cannot exclude a dynamically
    computed target that leaves no literal, construction sequence, or listing
    xref.
  - Wrapper depth is exhaustive at the callee level. Integer range and bias,
    signed float scaling, zero fast paths, the central-band remap, exceptional
    argument behavior visible in assembly, and conditional draw counts are
    documented. The software double/float packers were traced separately from
    EE hardware conversion and its fixed rounding behavior.
    For Ghidra-omitted BTL calls, argument sources were completely
    inventoried for all 94 bounded, 70 signed-scaled, and ten central-remap
    opcodes; immediate uses were classified for both low-31 and all 17 raw-word
    opcodes. Higher-level semantics of the hundreds of decoded resident and BTL
    callers were sampled rather than exhaustively named.
  - Lifecycle and deterministic-analysis coverage includes both resident reset
    callers, the update-counter seed source, the lazy-manager second reset, all
    32 cold reset selectors, MT untempering/recovery, LCG forward/rewind/skip,
    the exhaustive 65,536-state cycle decomposition of the 16-bit recurrence,
    and the repeated direct-reset selector attractors. The 42-entry resident
    vector table used by BTL was checked byte-for-byte, including its geometry
    and selector bias.
    MT recovery from an arbitrary offset was checked with predictive rolling
    states against every one of the 624 first-block capture offsets, separately
    from reconstruction of the physical resident array and index.
  - Caller-reduction coverage compares unsigned XOR reduction, low-bit selection,
    and absolute signed remainder using instruction bytes. The complete
    two-side distance helper and its direct selector call were traced; the
    equal-distance branch consumes one MT word, while unequal distances consume
    none. AI record eligibility and target eligibility remain with their owners.
    The tone-shade animator's constructor, vtable and full update body separate
    local timing from the global LCG. The complete resident shuffled-ID producer,
    its filters, allocator caller and list/random consumer bound draw counts.
    All three 12-attempt effect-construction bodies were compared, including
    allocation gates, direct stream consumption and an overwritten MT result.
    Bounded resident/BTL/ETC searches did not recover the tone-shade
    animator's dispatch or period writer.
    Complete raw-only construction and callback bodies established selector,
    registration, model-validity and post-draw visual gates. The remaining
    table-loaded central-remap site was reduced to two fixed parameter pairs
    through its sole recovered direct caller.

- **Confirmed coverage:** the independence of the MT, LCG, and
persistent 16-bit states; the coordinated but asymmetric reset; exact generator
constants and wrapper formulas; physical resident/BTL call counts; reachable
raw-only BTL imports versus the two static LCG orphans; representative loading,
render-jitter, tone-shade, camera-table, vector, shuffle, parity, and effect
consumers; distinct caller-owned modulo reductions and conditional two-side
tie selection; direct construction/callback draw bounds and their recovered
gates; and the shared generator state needed to reproduce outputs.

- **Unresolved or untested:** live call ordering and frequency,
branch feasibility inside caller-owned paths, the tone-shade animator's actual
virtual dispatch and nondefault period writers, exact hardware arithmetic
low-bit behavior, and player-visible meaning for most unlabeled BTL consumers
were not resolved.
- **Deliberate exclusions and overlap:** Adventure was not inspected. Damage
  interpretation belongs to [Damage](../gameplay/combat/damage.md); substitution to
  [Substitution](../gameplay/characters/substitution.md); save-data serialization to
  [Save data](../game/save_data.md); controller policy to
  [Controller input](controller_input.md); camera policy to
  [Battle camera](../gameplay/session/battle_camera.md), with camera-labelled RNG paths
  here limited to draw, reduction, table, and store behavior; and the tone-shade
  destination block to
  [Battle lifecycle](../gameplay/session/pause_and_replay.md#tone-shade-destination-block).
- **Evidence limitations:** all validation in this note is static or derived from exact recovered
recurrences. Hashes, exhaustive finite-state checks, opcode counts, inverses,
and deterministic vectors were recomputed offline, but none was compared with
a live trace. Static absence of an incoming edge or indirect reference is
therefore reported as such, not as proof that arbitrary runtime code can never
reach it.

## Evidence and scope

The resident and BTL binary identities follow
[Retail game file identities](../game/files/file_identities.md).

The preserved evidence is the Ghidra 12.1.2 `r5900:LE:32:default` projects at
`@disassembly/NA2/exports/SLPS_258.37/` and
`@disassembly/NA2/exports/BTL.BIN/`. Raw bytes from the protected clean ELF
were read only to resolve initialized data and zero-fill boundaries. No
runtime trace was used. Adventure code was not inspected.

Function recovery is incomplete in several BTL spans; raw bytes corroborate
the omitted instructions. Displayed BTL addresses below are preserved Ghidra
addresses, following the
[address conventions](../game/files/file_identities.md#address-conventions).

The ELF `.comment` section identifies `MW MIPS C Compiler (2.4.1.01)` for
`PlayStation2`. Its `.symtab` and `.strtab` section headers both have zero
length, so no source-level RNG names survive in the clean executable. Function
names such as `FUN_0017b780` below are therefore the exact preserved Ghidra
symbols, not recovered original C identifiers. In particular, the 64-bit pair
behaves like a library seed/output API, but static evidence does not justify
asserting original names such as `srand` and `rand`.

The resident code has three related but independent mutable streams:

| Stream | Output function | Mutable state | Reset behavior |
| --- | --- | --- | --- |
| MT19937 | `FUN_0017fd90` and wrappers at `0x001801B0..0x00180350` | 624 low-32-bit words in eight-byte slots at `0x00617640`, plus index `DAT_00602a28` | Rebuilt from a fixed bootstrap by `FUN_00180060`; the incoming tag selects only a discard count from 0 through 31. |
| 64-bit LCG | `FUN_0017b798` | 64-bit word `DAT_003fad10` | Seeded from the complete low 32 bits of the incoming tag by `FUN_00180060`; initialization does not draw from it. |
| 16-bit recurrence | `FUN_00180560` | halfword `0x00607450` (`uRam00607450` in the C export) | Never reset by the resident initializer. `FUN_00180060` advances the existing state 0 through 31 times. |

These streams are coordinated by one initializer, but they are not different
views of one state.

## State and clean-image values

| Address / original symbol | Size | Clean ELF offset | Clean value | Role |
| --- | ---: | ---: | ---: | --- |
| `0x003FAD10`, `DAT_003fad10` | 8 | `0x002FAE10` | `0x0000000000000001` | 64-bit LCG state. `PTR_DAT_003faf58` at `0x003FAF58` contains `0x003FAC68`; the state is that pointed object plus `0xA8`. |
| `0x003FB3D0`, `DAT_003fb3d0` | 8 | `0x002FB4D0` | `0` | MT twist table entry for an even concatenated word. |
| `0x003FB3D8` | 8 | `0x002FB4D8` | `0x000000009908B0DF` | MT twist table entry for an odd concatenated word. |
| `0x00602A20`, `DAT_00602a20` | 4 | `0x00502B20` | `0x00001100` | Current control/tag word. It is an initializer input and is overwritten with an MT output at the end of initialization. |
| `0x00602A24`, `DAT_00602a24` | 4 | `0x00502B24` | `0x00001100` | Snapshot of the tag supplied to the most recent initialization. No resident read was found. |
| `0x00602A28`, `DAT_00602a28` | 4 | `0x00502B28` | `0x00000271` | MT index. `625` is the lazy-bootstrap sentinel; `624` requests a twist before the next output. |
| `0x00607450`, `uRam00607450` | 2 | none (zero-fill) | zero-filled | Persistent 16-bit recurrence state. |
| `0x00617640..0x006189BF` | 624 x 8 | none (zero-fill) | zero-filled | MT state slots. Only each slot's low 32 bits participate. |

The first ELF `PT_LOAD` has file-backed data through `0x0060737F` and
zero-fill from `0x00607380`, proving that both the 16-bit state and MT array
start at zero on a cold process. The seed/tag/index words and LCG state are
file-backed initialized data.

The resident `gp` value resolves to `0x0060A9F0`. Accordingly, the current
tag, prior-tag snapshot, and MT index are `gp-0x7FD0`, `gp-0x7FCC`, and
`gp-0x7FC8`; the 16-bit state is `gp-0x35A0`. These offsets are the forms used
by the resident instructions, while the table above gives their absolute live
addresses.

## Coordinated initialization and reseeding

`FUN_00180060` is a no-argument global initializer. The C export fails to show
the argument on its internal call to `FUN_0017b780`, but assembly loads the
current `DAT_00602a20` value into `a0` and preserves it through that call. Its
exact sequence is:

1. Load `DAT_00602a20` as the incoming 32-bit tag and copy it to
   `DAT_00602a24`.
2. Call `FUN_0017b780(tag)`, replacing the 64-bit LCG state with the
   zero-extended tag.
3. Rebuild all 624 MT slots from fixed value `0x1100` and set the MT index to
   `624`.
4. Let `n = tag & 0x1F`. Repeat `n` times: discard one raw MT output through
   `FUN_001801e0`, then advance the 16-bit stream once through
   `FUN_00180560`.
5. Draw one additional raw MT word and pass it to `FUN_001801a0`, which stores
   it into `DAT_00602a20`.

The initializer therefore consumes `n + 1` MT words, advances the 16-bit
stream `n` times, and consumes no LCG output. Its post-initialization MT index
is `n + 1`. The retained tag is the last MT word consumed, not the input tag.

There are exactly two resident calls to `FUN_00180060`:

- `FUN_001e0ee0` calls `FUN_001801a0(*(root + 0x194))` at `0x001E11AC`, then
  calls `FUN_00180060` at `0x001E11B4`. `FUN_00107f80` initializes that root
  field to zero, and `FUN_001081b0` increments it on each scheduler update
  reached from `FUN_001d0590`. The seed source is therefore a resident update
  counter; no hardware entropy source is visible on this path.
- `FUN_001f4360` calls `FUN_00180060` directly at `0x001F4378`, without first
  replacing the tag. That reset consequently uses whatever
  `DAT_00602a20` currently retains, normally an earlier MT output. This call is
  part of constructor `FUN_001f4200`, reached from `FUN_001e9980` only on its
  null-manager allocation branch; later updates with an existing manager skip
  that construction path.

`FUN_001801a0(value)` by itself is only a four-byte store to
`DAT_00602a20`. It does not touch the MT array or index, the LCG state, or the
16-bit state. Its value affects a stream only if `FUN_00180060` is called
later.

Consequently, when the null-manager construction follows the counter-seeded
reset, the second reset input is the first reset's retained `MT[n]` word and
its selector is `MT[n] & 31`; ordinary MT or LCG draws in between cannot change
that tag. For an update-counter tag of zero, the selector composition is
`0 -> 9`. With no intervening 16-bit calls, the state after those two resets is
retained tag `0x0F96266C`, next MT word `0x0EADC242`, LCG seed
`0x889C77E9`, and 16-bit state `0x8CAF`. This is a static conditional vector,
not evidence that a particular live run takes the allocation path at a fixed
time.

The scheduler call is the physical `jal` at `0x001D05AC`. Inside
`FUN_001081b0`, `0x001081D8` adds one to the 32-bit field and `0x001081DC`
stores it back, so the counter wraps modulo `2^32`. If reset timing is the only
changing input, its MT selector repeats every 32 scheduler updates; the LCG
still receives the full counter and repeats its reset seed only after the
32-bit counter wraps.

## MT19937 core

`FUN_0017fd90` is the resident MT core. The constants and state transitions
identify canonical MT19937 with `N = 624` and `M = 397`:

- upper and lower masks: `0x80000000` and `0x7FFFFFFF`;
- odd-word twist: `0x9908B0DF`;
- tempering shifts: 11, 7, 15, and 18;
- tempering masks: `0x9D2C5680` and `0xEFC60000`.

The code uses 64-bit EE loads, stores, and an eight-byte stride, but masks and
operations constrain the generator to the low 32 bits of every slot. In
32-bit notation, output tempering is:

```text
y  = state[index++]
y ^= y >> 11
y ^= (y << 7)  & 0x9D2C5680
y ^= (y << 15) & 0xEFC60000
y ^= y >> 18
return y
```

When the clean index sentinel is `625`, the core first constructs the 624
state words with this older MT bootstrap form:

```text
s = 0x1100
for i in 0..623:
    state[i]  = s & 0xFFFF0000
    s         = 69069 * s + 1              // modulo 2^64 in the EE code
    state[i] |= (s & 0xFFFF0000) >> 16
    s         = 69069 * s + 1
```

It then performs the ordinary 624-word twist and returns the first tempered
word. `FUN_00180060` performs the same fixed bootstrap explicitly, writes
index `624`, and lets the first following draw perform the twist.

The recovered nonzero state therefore has canonical MT19937 period
`2^19937 - 1` if allowed to run continuously. That long core period should not
be confused with reset diversity: every `FUN_00180060` call discards the
current MT history, rebuilds this one fixed state, and resumes at only one of
32 early offsets selected by the tag.

The exact state range is 4,992 bytes because each 32-bit word occupies a
little-endian eight-byte slot. SHA-256 over the complete
`0x00617640..0x006189BF` layout is:

| State-array point | SHA-256 | First / last low-32-bit words |
| --- | --- | --- |
| Fixed bootstrap, before twist | `FB6C273F74FDD5B4EEE77F35190BD11C4B2DA8BD706EA7F72FB043D967F2BB86` | first `000011EA`; last `5903372E` |
| After the first twist | `6461422553F410D65F4DAC0AF5DA78A93D98BDDCE14DC631E6C8147E1A651008` | first `2B577921`; last `D98F2A34` |

`FUN_00180060` always makes at least the final retained-tag draw, so its
completed state has the post-twist hash for all 32 selectors. Drawing does not
mutate array words until the next twist; the selector cases differ only in
index `n + 1`. These hashes were computed over eight-byte slots with zero upper halves,
matching the actual `sd` layout, not over a packed 2,496-byte word array.

### Recovery from raw MT outputs

The tempering transform is bijective. A practical inverse, with every
intermediate constrained to 32 bits, is:

```text
undo_right(y, shift):
    x = y
    repeat x = y ^ (x >> shift) until x is unchanged
    return x

undo_left(y, shift, mask):
    x = y
    repeat x = y ^ ((x << shift) & mask) until x is unchanged
    return x

untemper(y):
    y = undo_right(y, 18)
    y = undo_left(y, 15, 0xEFC60000)
    y = undo_left(y, 7,  0x9D2C5680)
    y = undo_right(y, 11)
    return y
```

For a capture aligned to MT index zero, untempering 624 consecutive complete
outputs reconstructs all 624 post-twist state words. Store each recovered word
in the low half of its eight-byte slot, zero the upper half, and set the index to
624 to reproduce the state immediately after that capture; the next core call
twists and emits the 625th output. In the clean fixed sequence, untempering
first output `0x889C77E9` gives state word `0x2B577921`; all 624 recovered
slots hash to the documented post-twist SHA-256, and the predicted next output
is `0x9705D2ED`.

Alignment matters for reconstructing the original physical array and index.
A 624-word capture beginning at a nonzero index straddles two resident twisted
arrays, so copying untempered words in capture order does not recreate those
same physical bytes. It does, however, form an equivalent predictive rolling
state: set its index to 624, then the recovered core predicts the next word
and following uninterrupted outputs without knowing the original index.
The distinction is physical state identity versus future output identity.

This follows from the sequential twist recurrence recovered at
`0x0017FE6C..0x0017FFF4`. For the untempered stream `X`, the next word is

```text
X[k+624] = X[k+397]
           ^ ((X[k] & 0x80000000 | X[k+1] & 0x7FFFFFFF) >> 1)
           ^ ((X[k+1] & 1) ? 0x9908B0DF : 0)
```

The second twist loop reads already replaced slots, and the final word reads
the updated slot zero. Thus a window of 624 consecutive untempered words
supplies the same recurrence even when its start differs from the resident
array boundary. In-memory calculation from the exact fixed bootstrap checked
all capture starts `0..623`, predicting 1,024 following words per start:
638,976 comparisons with no mismatch. Representative vectors are:

| First captured output index | First predicted output after 624 captured words |
| ---: | --- |
| 0 | `9705D2ED` |
| 1 | `B115896D` |
| 31 | `08F3A452` |
| 227 | `1AC8818D` |
| 397 | `3556C522` |
| 623 | `8C4AB9A1` |

The capture must contain consecutive complete core outputs, with no missing
draws or coordinated reset. `FUN_001801B0`, bounded results, and float
wrappers discard information; the recovery above requires complete 32-bit
outputs such as those returned by `FUN_001801E0` or the core. The inverse
itself was also checked against all 624 fixed-sequence outputs and 65,571
additional deterministic words with no mismatch. These are static recurrence
calculations, not observed game execution.

### MT wrappers

The original Ghidra symbols and exact consumption behavior are:

| Function | Proven operation | MT words consumed |
| --- | --- | ---: |
| `FUN_001801a0(uint32 value)` | Store only to `DAT_00602a20`; this is a tag setter, not an immediate MT seed routine. | 0 |
| `FUN_001801b0()` | `FUN_0017fd90() & 0x7FFFFFFF`; result is `0..0x7FFFFFFF`. | 1 |
| `FUN_001801e0()` | Return the complete low-32-bit MT bit pattern, sign-extended in the EE return register. | 1 |
| `FUN_00180210(int32 bound)` | Let `m = abs(bound)` using 32-bit `subu`; return `(uint32(word ^ 0x80000000) % (m + 1))` using `divu`. For ordinary nonnegative input the range is inclusive `0..bound`. | 1, including when `bound == 0` |
| `FUN_00180260()` | `float(int32(word)) / 4294967296.0f`; a signed half-unit result, not a `[0,1)` result. | 1 |
| `FUN_001802b0(float scale)` | If `scale == 0`, return positive zero. Otherwise return `float((double)scale * ((double)(int32(word)) / 2147483648.0))`. | 0 for either signed zero; otherwise 1 |
| `FUN_00180350(float A, float B)` | Signed scaled draw with a conditional central-band remap described below. | 0 when `A == 0`; otherwise 1 or 2 |

All eight resident direct calls to `FUN_0017fd90` are accounted for by this
surface: one initial call in each of the six output wrappers, plus the two
conditional second-draw sites inside `FUN_00180350`. No resident or BTL caller
directly bypasses these wrappers to call the MT core.

`FUN_001802b0` implements its scale through the soft-double helper chain
`FUN_00171348` (float to double), `FUN_00171d78` (signed int32 to double),
`FUN_00171ac8` (divide), `FUN_00171840` (multiply), and `FUN_00171f00`
(double to float). `FUN_00180350` inlines that same chain at each possible draw
rather than calling `FUN_001802b0`; this is why its three core call sites and
data-dependent consumption are visible directly in assembly.

`FUN_00180210` is a plain modulo reduction. The `^ 0x80000000` is a
permutation of all 32-bit words and does not remove modulo bias; the result is
unbiased only when `abs(bound) + 1` divides `2^32`. The C export's apparent
no-argument prototype and `extraout_t0` are decompiler errors: assembly moves
`a0` into `t0` before the core call.

More exactly, for `q = abs(bound) + 1`, let
`base = floor(2^32 / q)` and `extra = 2^32 mod q`. Results `0` through
`extra - 1` each have `base + 1` preimages; the remaining results each have
`base`. Thus bounds `1`, `3`, `7`, and any other `2^k - 1` are exact, while
bound `2` gives result zero one additional preimage out of `2^32`.
Negative inputs other than `INT32_MIN` behave like their positive magnitude.
For `INT32_MIN`, word-sized negation wraps to `0x80000000`, so
the divisor is `0x80000001` and the returned range is `0..0x80000000`; no
possible signed 32-bit input produces a zero divisor.

### EE hardware conversion and software packing

The EE FPU has fixed rounding toward zero: FCR31's low two bits are hardwired
to `01`. It does not implement IEEE NaNs, infinities, or denormals; exponent
`255` still describes a finite EE number, while exponent zero describes zero.
The hardware manual also warns that arithmetic can differ from IEEE truncation
in the least significant bit because the FPU omits guard, round, and sticky
bits. Host IEEE arithmetic alone therefore does not prove every returned bit.
These are hardware properties, not an unresolved game-selected rounding mode.
[EE Core User's Manual v6.0, sections 8.1, 8.7 and 8.8](https://docs.alexrp.com/mips/ee.pdf#page=156).

`FUN_00180260` uses hardware `cvt.s.w` at `0x00180280` before division by
`2^32`. Toward-zero conversion maps positive `INT32_MAX` to `2^31 - 128`
(`0x4EFFFFFF`), rather than `2^31`. Its power-of-two quotient is
`0.5 - 2^-25` (`0x3EFFFFFF`); the negative endpoint is exactly `-0.5`.
These derived endpoints exclude conversion rounding upward as a route to
`+0.5`. They are not an independent measurement of the divider's low bits.

The scaled wrappers use software packing instead. `FUN_00171F00` unpacks a
double through `FUN_00171460`, reduces its mantissa at
`0x00171F28..0x00171F44`, and calls `FUN_00171318`, which passes the fields
to `FUN_00171200`. The finite normal path there uses `srl a1,a1,7` at
`0x00171260` and masks the fraction; it has no rounding increment or carry.
Thus the double-to-float conversion discards 29 fraction bits. The intermediate
double packer `FUN_00171388` likewise discards eight working-mantissa bits
with `dsrl` at `0x00171400`; exponents below `-1022` become signed zero.
The float packer flushes exponents below `-126` to signed zero. No FCR31 mode
participates in either packer.

For a positive IEEE-normal `scale`, `FUN_001802B0` therefore retains nominal
support `[-scale, scale)`: the signed integer division by `2^31` is exact in
double, the software product/pack path does not round upward, and final
truncation cannot turn a value below `scale` into `scale`. `INT32_MIN`
reaches `-scale`. Small magnitudes can flush to zero. The remap's subsequent
hardware additions and multiplications remain subject to EE arithmetic,
so this endpoint result for the scaled draw is not a complete bit-level model
of every remapped result.

### Central-band remap

`FUN_00180350(A, B)` uses the same signed scale as `FUN_001802b0`. Its exact
finite-value branch structure is:

```text
if A == 0:
    return +0                         // no draw

x = A * int32(mt()) / 2^31           // first draw
if x < 0:
    if x <= -B:
        return x
    midpoint = -(A + B) / 2
else:
    if x >= B:
        return x
    midpoint = +(A + B) / 2

halfwidth = (A - B) / 2
if halfwidth == 0:
    return midpoint                   // no second draw
return midpoint + halfwidth * int32(mt()) / 2^31
```

For ordinary nonnegative bounds whose midpoint and halfwidth calculations
remain in range, the function chooses a sign and a magnitude between `A` and
`B`; the argument order changes how it gets there:

- If `0 < B < A`, a first value already outside `(-B, B)` is retained;
  otherwise it is remapped on the same sign side. Nominal implementation
  support is `[-A, -B]` union `[B, A)`, and consumption is one or two words.
- If `0 < A < B`, no first value can reach magnitude `B`. The first draw only
  chooses the sign, `halfwidth` is negative, and a mandatory second draw maps
  into nominal support `(-B, -A]` union `(A, B]`. Consumption is exactly two
  words.
- If `A == B != 0`, an interior first result collapses to the same-sign
  endpoint and `halfwidth == 0` suppresses the second draw. If `B == 0` and
  `A != 0`, the first signed-scaled result is returned directly. Both cases
  consume one word.

For unequal positive bounds in an ideal continuous model with independent
uniform draws, the result is uniform across the two signed bands between them.
In the `B < A` case, each
retained outer value starts with density `1 / (2A)` and the remapped
same-sign central mass supplies the balance; in the `B > A` case, each sign
has probability one half and the mandatory second draw is uniform across that
side's band. Finite integer inputs and float rounding make the implementation
a discrete approximation and can alter endpoint inclusion.

Reverse-order use is proven rather than hypothetical. Decoded BTL calls
`0x0085A220` and `0x0085A574` pass `(25.0f, 30.0f)`, while calls
`0x0085A2A0` and `0x0085A5F4` pass `(60.0f, 70.0f)`. Negative bounds and
extreme exponent patterns are not given a range interpretation here. The
finite branch formula does not assign IEEE exceptional-value semantics to EE
comparisons or to the software helper chain.

All ten additional aligned `FUN_00180350` opcodes that Ghidra left in
undefined spans are also instructions in coherent code blocks, rather than
isolated words in data. Each containing span begins as the return fall-through
from a decoded `jal`, and raw disassembly remains instruction-coherent through
the wrapper call. Their arguments are:

| Displayed call | `A` | `B` | Immediate consequence |
| --- | ---: | ---: | --- |
| `0x00758478` | `25.0` | `10.0` | Ordinary `B < A` order. |
| `0x0075C10C` | `10.0` | `25.0` | Reversed order; exactly two draws. |
| `0x0075CC80` | `25.0` | `25.0` | Equal bounds; exactly one draw and an endpoint result. |
| `0x0075CCC4` | `0.18` | `0.25` | Reversed order; exactly two draws. |
| `0x0075DA64` | `13.0` | `17.0` | Reversed order; exactly two draws. |
| `0x0075DAA4` | `55.0` | `70.0` | Reversed order; exactly two draws. |
| `0x0075DAE4` | `3.5` | `5.5` | Reversed order; exactly two draws. |
| `0x007F9168` | binary32 `pi` | `0.10471976` | Ordinary `B < A` order. |
| `0x007F9514` | binary32 `pi` | `0.10471976` | Ordinary `B < A` order. |
| `0x0083DA74` | table-loaded `0.95` or `1.25` | paired `0.75` or `1.05` | Both pairs use `B < A`; see [the two-record producer](#fixed-pairs-in-a-two-record-producer). |

The decimal spellings above round-trip to the exact binary32 values loaded
into `f12` and `f13`. Together with the
decoded sites, these calls establish all 26 physical central-remap opcodes and
show both argument orders, equality, and table-selected bounds in caller code.

## 64-bit LCG stream

`FUN_0017b780(seed)` and `FUN_0017b798()` form a separate seed/output pair.
The export has no recovered source-level names, so the algorithm is described
rather than assigning a library symbol:

```text
FUN_0017b780(seed):
    DAT_003fad10 = uint32(seed)

FUN_0017b798():
    DAT_003fad10 = DAT_003fad10 * 0x5851F42D4C957F2D + 1  // modulo 2^64
    return (DAT_003fad10 >> 32) & 0x7FFFFFFF
```

`FUN_0017b780` has one resident caller, the coordinated initializer at
`0x00180074`. `FUN_0017b798` always advances its 64-bit state and returns an integer
from `0` through `0x7FFFFFFF`.

The LCG transition has full period `2^64`: its increment is odd and its
multiplier is congruent to 1 modulo 4, satisfying the full-period conditions
for a power-of-two modulus. The multiplier's inverse modulo `2^64` is
`0xC097EF87329E28A5`, so a state can be rewound exactly:

```text
previous = (next - 1) * 0xC097EF87329E28A5  // modulo 2^64
```

Multiplying the recovered multiplier and inverse modulo `2^64` gives 1, and
rewinding first state `0x71370215ED71FD01` gives seed `0x0000000000001100`.
The exposed result discards the low 32 state bits and the top bit of the high
word, so exactly `2^33` states share any one exposed value; an output
alone does not identify the state needed for rewind.

Arbitrary draw positions can be reached in logarithmic time by exponentiating
the affine transition. All operations below are modulo `2^64`:

```text
advance(state, count, cur_mul, cur_add):
    acc_mul = 1
    acc_add = 0
    while count != 0:
        if count & 1:
            acc_add = acc_add * cur_mul + cur_add
            acc_mul = acc_mul * cur_mul
        cur_add = (cur_mul + 1) * cur_add
        cur_mul = cur_mul * cur_mul
        count >>= 1
    return acc_mul * state + acc_add
```

For forward skips, initialize `cur_mul = 0x5851F42D4C957F2D` and
`cur_add = 1`. For backward skips, use inverse transition multiplier
`0xC097EF87329E28A5` and addend `0x3F681078CD61D75B` (the two's-complement
value of the negated inverse). As a validation vector, advancing seed
`0x1100` by 1,000 transitions yields state `0xF57A15AC5E49B078`; applying the
backward form for 1,000 transitions returns exactly to `0x1100`.

A defined non-damage consumer is `FUN_0018f410`, associated through the
resident type strings with `ccToneShadeAnimRandom`. At calls `0x0018F444` and
`0x0018F470`, it obtains two consecutive LCG results, divides each by the
single-precision `2^31` constant, and writes them to object fields `+0x34` and
`+0x38` whenever its configured period elapses. This also proves that the LCG
has a separate output consumer rather than only seed-mixing support inside the
MT initializer. Hardware toward-zero conversion maps `0x7FFFFFFF` to
`2^31 - 128`; its quotient by `2^31` is `1 - 2^-24`
(`0x3F7FFFFF`). Conversion therefore does not round a draw up to `1.0`.
The hardware arithmetic qualification above still applies. Its invocation
path is bounded separately below; defining and constructing the object does
not prove that its virtual update runs in every battle state.

### Tone-shade animator timing is not another seed

Raw bytes establish the class association directly: table `0x005D9DD8`
contains RTTI pointer `0x005BF7D8` at `+0`, zero at `+4`, and update pointer
`0x0018F410` at `+8`; RTTI `0x005BF7D8` points to the string
`ccToneShadeAnimRandom` at `0x003FB550`. The constructor `FUN_0018F4B0`
writes that table pointer, counter halfword `+4 = 0`, and period halfword
`+6 = 2`. Its complete 11-instruction body makes no RNG call and does not
write a generator state.

The full update has this exact local contract:

```text
counter = (counter + 1) & 0xFFFF
if counter < period: return             // no LCG draw, no destination write
counter = 0
destination[+0x34] = float(lcg()) / 2^31
destination[+0x38] = float(lcg()) / 2^31
```

`lhu`, `sh`, and `andi 0xFFFF` at `0x0018F424..0x0018F434` prove the
counter's width and unsigned comparison; reset occurs in the first LCG call's
delay slot at `0x0018F448`. Both draws occur before either destination store.
From constructor state, default period two gives zero draws on the first
invocation and two on the second, repeated thereafter. Period zero and one
would draw twice on every invocation; these are consequences of the body,
not evidence that a writer configures those values. No MT or 16-bit stream is
used. The only local state is timing; rebuilding this object does not rewind
the LCG.

Resident `FUN_001EF330` constructs the animator at sequence-object `+0x68C`
only on the null-allocation branch: `0x001EF71C` forms that address and
`0x001EF720` calls the constructor. The adjacent destination block starts at
sequence `+0x650`; initialization through `FUN_0018F590` clears its
`+0x34/+0x38` values. The sequence object is the `0x6C0`-byte pause controller
at `0x00607834`; its allocation and ownership belong to
[Battle lifecycle](../gameplay/session/pause_and_replay.md#tone-shade-destination-block).

Function and address xrefs report no direct reference to `0x0018F410`,
although a literal-byte search finds its update pointer at `0x005D9DE0`
(plus two alias mappings of the same resident bytes). An invocation through
that vtable remains possible. A complete-BTL search of direct `addiu`
encodings for offset `0x68C` and direct `sh` encodings for sequence offsets
`0x690/0x692` found none; each used all four opcode high bytes, with zero
matches. These negatives exclude only those direct-offset forms,
not adjusted pointers, generic virtual dispatch, bulk stores, or another
module. The actual dispatch and any nondefault period writer remain unresolved.

The animator is an eight-byte embedded member of that `0x6C0`-byte object.
Its destination block's construction, publication and teardown, and an
independent writer of destination `+0x34/+0x38` that uses no RNG, belong to
[Battle lifecycle](../gameplay/session/pause_and_replay.md#tone-shade-destination-block).

**Bounded negative.** An aligned instruction audit of displayed BTL
`0x0076A000..0x0076FFFF` (24,576 bytes) checked immediate offsets
`0x650..0x694` in integer address/load/store and scalar float load/store forms.
It found the destination and gate accesses recorded in Battle lifecycle, but
no direct access to
animator bytes `+0x68C..+0x693`. Complete-program searches for all four
`addiu` opcode high bytes with immediate `0x650` recovered
only three sequence-relevant BTL address constructions: initializer
`0x0076EB40`, publisher `0x0076F018`, and writer `0x0076F3F0`. The remaining
BTL match `0x006B4544` is an allocation-size literal for a different root
array. No ETC match occurred. The resident `0x68C` construction search found
the known constructor receiver and an unrelated library diagnostic line
number; its `sh +0x692` searches found none. ETC searches for `addiu +0x68C`
and `sh +0x692` also found none. All these searches used four opcode high
bytes; resident alias mappings and unaligned
byte matches were excluded from instruction counts.

No recovered path passes `destination + 0x3C` or another adjusted pointer to
the animator's slot `+8`. The inspected construction, publication, writer and
teardown family therefore narrows the missing path without proving that the
animator is never invoked. Bulk/adjusted stores and other receiver-producing
code remain outside this bound; no nondefault period value has been established.

## Persistent 16-bit stream

`FUN_00180560` is a one-halfword recurrence:

```text
x = ((state ^ 0x1100) - 0x6553) & 0xFFFF
state = rol16(x, 2)
store state at 0x00607450
return sign_extend16(state)
```

The C export types the return as `ushort`, while assembly sign-extends it;
identified callers mask the low bits, so this prototype difference has no
effect on those uses.

There is no resident setter or reset for `0x00607450`, and the only direct
state accesses are the load/store inside `FUN_00180560`. Besides initializer
warm-up at `0x00180148`, its resident calls are:

- `FUN_0020b000` at `0x0020B470`;
- `FUN_0026bd20` at `0x0026C028`;
- `FUN_003083d0` at `0x00308678`.

Each of the latter calls occurs in a 12-attempt visual/effect construction loop.
The caller masks the result with `7`, passes it through absolute-value helper
`FUN_001771a0`, negates it, and writes `0..-7` to object field `+0x28`. The
absolute-value call is redundant after the mask. No damage behavior is inferred
from these effect-object writes.

### Allocation gates and a consumed but overwritten MT result

Inspection of all three complete bodies distinguishes attempted objects
from direct RNG draws:

| Resident body | Gate before its per-object RNG sequence | Direct calls in each entered sequence |
| --- | --- | --- |
| `FUN_0020B000` | The twelve-attempt branch requires its resolved selector to be zero. Each allocator result is checked before the sequence; a null result skips that attempt's draws. Other selector branches do not contain this sequence. | One raw MT call, four signed-scaled calls, four central-remap calls, one 16-bit call. |
| `FUN_0026BD20` | Twelve attempts; null allocator result branches from `0x0026BE98` to the loop increment at `0x0026C218`, skipping every direct RNG call for that attempt. | One raw MT call, four signed-scaled calls, three central-remap calls, one 16-bit call. |
| `FUN_003083D0` | Twelve iterations with no allocator-result gate before its object writes and direct draws. Counts for a completed invocation require completion of all iterations. | One raw MT call, four signed-scaled calls, three central-remap calls, one 16-bit call. |

Thus the first two bodies make `s` direct 16-bit advances for `s` successful
allocations, `0 <= s <= 12`, rather than advancing twelve times regardless of
allocation. The third makes twelve direct advances if it completes. These
counts concern calls in these bodies; they do not include any nested callee's
other work. None of their native per-object sequences calls the LCG.

The extra central-remap call in `FUN_0020B000` is material to stream alignment
even though its result is overwritten. At `0x0020B4A4` it passes
`(2.0f, 0.25f)` to `FUN_00180350`, multiplies the return by the saved size
at `0x0020B4AC`, and stores to scratch X at `0x0020B4B0`. Instruction
`0x0020B4BC` clears that same X word before any intervening call or load of it.
The draw consumes one or two MT words under the wrapper's ordinary positive
bound rules; the stored X contribution does not survive. This is observed
retail code, not an additional generator or a reason to disregard the draw.

The sole direct caller of `FUN_0026BD20`, `FUN_0026E090`, supplies exact
binary32 size `1.5f` at `0x0026E300..0x0026E30C`. It reaches that call for
its object slots zero/one only when object word `+0x68` bit zero is clear;
another slot can dispatch through `FUN_00308A70` instead. The numeric
classifier cases and gameplay interpretation remain outside this RNG contract.
For that fixed `1.5f` call, internal size becomes `5.25f` and the separate
clamped coefficient is `1.25f`. The raw signed-remainder divisor and added
base come from conversions of exact floats `3.75f` and `12.5f`, respectively.
Instructions `0x0026BE34/0x0026BE48` are both exact word `0x46000024`,
`cvt.w.s f0,f0`. The EE instruction's conversion is fixed toward zero,
unlike the generic MIPS instruction with the same name; Sony's
[EE Core Instruction Set Manual v6.0, p. 356](https://docs.alexrp.com/mips/ee_insns.pdf#page=356)
establishes that distinction. The divisor is therefore three, the base twelve,
and the resulting base plus absolute signed remainder is exactly `12..14`.
The `(5.0f, 1.0f - 5.25f)` central call necessarily returns its first draw:
negative `B = -4.25f` satisfies the early-return comparison on both sign
branches. Of the three central calls, only `(10, 2.5)` and `(64, 16)` can draw
a second word. Each successful allocation consequently consumes 8 through 10
MT words through this body's direct calls, plus one 16-bit advance; the full
twelve-success case consumes 96 through 120 direct MT words and twelve direct
16-bit advances. Those bounds do not assert that every total occurs in a
particular run.

Every operation in the 16-bit update is bijective. One step can be reversed
without a lookup table:

```text
previous = (((ror16(next, 2) + 0x6553) & 0xFFFF) ^ 0x1100)
```

Exhaustively applying the exact recurrence to all 65,536 halfword values gives
11 disjoint cycles with lengths:

```text
43951, 13698, 5447, 1089, 844, 435, 64, 3, 3, 1, 1
```

Using each cycle's smallest state as a reproducible representative, the
length/representative pairs are:

```text
43951/0000  13698/0001  5447/000B  1089/000F  844/0049  435/00BE
64/01A7     3/1FAB      3/51F4     1/9DC4     1/F319
```

Cold state zero is in the 43,951-state cycle. The two fixed points are
`0x9DC4` and `0xF319`. Therefore a cold process never reaches the other ten
cycles through ordinary calls. Any starting halfword in a different cycle
remains there. This cycle result and the inverse were verified
over all 65,536 inputs from the recovered recurrence; they are derived static
results rather than live observations.

The three-bit value actually used by the identified effect callers also has
measurable structure. Over the complete cold cycle, counts for masked results
0 through 7 are respectively:

```text
5492, 5488, 5479, 5532, 5532, 5522, 5457, 5449
```

The masked sequence itself has period 43,951, but only 32 of the 64 possible
adjacent result pairs occur. If `r[t] = state[t] & 7`, then
`bit2(r[t+1]) = 1 - bit0(r[t])`: subtracting odd constant `0x6553` complements
the low bit, and the rotate-left-by-two moves that bit to bit 2. Consecutive
effect-side results are therefore deterministically correlated even though all
eight values occur. The counts and adjacent-pair constraint were checked over
the full cold cycle.

## Direct BTL imports

The clean `BTL.BIN` does not contain one general RNG import relay. Its call
instructions directly encode resident absolute targets, shown as
`func_0x...` in the C export and `SUB_...` in the listing.

The preserved BTL project omits the file's first `0x40` bytes. For a displayed
BTL call-site address `x`, the complete-file offset is
`x - 0x006B3F00 + 0x40` and the archived live call site is `x + 0x40`.
Absolute resident call targets are already live addresses and receive no
adjustment. This is the same convention recorded in the
[MWo3 overlay address mapping](overlay_abi.md#file-runtime-and-preserved-ghidra-addresses).

Direct-call counts are below. The decoded columns count `jal FUN_...`
instructions in the Ghidra listings, not abbreviated XREF headers or C
decompiler occurrences. A separate aligned scan of the complete clean BTL
binary matched the little-endian MIPS word
`0x0C000000 | ((target >> 2) & 0x03FFFFFF)` and found additional exact
`jal target` words inside ranges that Ghidra left undefined. Those raw counts
are physical opcode-word counts, not a claim
that every such word is reachable; the LCG cases are classified below. Every
BTL match is below the identified data start at `0x0088F5C0`, so none is an
accidental word in the exported strings/tables region. The same raw scan
exactly matches every resident decoded count in the table.

| Resident target | Stream / result | Resident decoded `jal` | BTL decoded `jal` | BTL aligned opcode words | Representative BTL displayed / file / live call site |
| --- | --- | ---: | ---: | ---: | --- |
| `FUN_0017b798` | 64-bit LCG, high 31 bits | 3 | 7 | 11 | `0x006DD2EC` / `0x0002942C` / `0x006DD32C` |
| `FUN_001801b0` | MT, low 31 bits | 20 | 2 | 4 | `0x006D663C` / `0x0002277C` / `0x006D667C` |
| `FUN_001801e0` | MT, raw 32 bits | 125 | 39 | 56 | `0x006F2E6C` / `0x0003EFAC` / `0x006F2EAC` |
| `FUN_00180210` | MT, inclusive bounded integer | 290 | 225 | 319 | `0x006C48BC` / `0x000109FC` / `0x006C48FC` |
| `FUN_00180260` | MT, signed half-unit float | 0 | 7 | 7 | `0x007530C8` / `0x0009F208` / `0x00753108` |
| `FUN_001802b0` | MT, signed scaled float | 453 | 173 | 243 | `0x006B6E94` / `0x00002FD4` / `0x006B6ED4` |
| `FUN_00180350` | MT, central-band-remapped float | 61 | 16 | 26 | `0x0075A2F8` / `0x000A6438` / `0x0075A338` |
| `FUN_00180560` | Persistent 16-bit recurrence | 4 | 0 | 0 | none |

There are no direct BTL calls to `FUN_0017b780` (LCG seed),
`FUN_0017fd90` (MT core), `FUN_00180060` (coordinated initializer),
`FUN_001801a0` (tag setter), or `FUN_00180560` (16-bit recurrence). A targeted
search also found no copy of the MT constants or state literals in BTL.
Consequently, the mapped BTL paths consume resident shared state but do not
reseed it through any identified direct import.

Neither resolved listing references nor raw `lui` plus load/store patterns
access the MT tag/index/array, LCG 64-bit word, or 16-bit state directly from BTL.
The raw scan does find five loads of resident runtime anchor
`PTR_DAT_003faf58`, but every one immediately loads field `+0x0C` on a library
error path; none accesses the LCG field at anchor-relative `+0xA8`. Thus no
identified BTL path bypasses the documented output wrappers or direct LCG
output function to mutate RNG state.

No aligned literal pointer to any identified RNG function exists in BTL, and
a raw text scan found no `lui` plus low-half construction of any seed, core,
or wrapper address followed by `jr`/`jalr`. Within this binary, the identified
resident RNG interface is therefore the direct absolute-`jal` surface counted
above, rather than an indirect function table or BTL-local relay.

Both `FUN_001801b0` opcodes omitted from the decoded listing are coherent,
statically reachable consumers. At displayed `0x007531C4`, a decoded `jal`
returns into the raw span; when object `+0x29C` is `-1`, the block stores
`FUN_001801b0() % 3` back to that field. Displayed `0x0076D3FC` lies in switch
case 5 of the function beginning at `0x0076CBC0`; the complete-file jump table
at displayed `0x008CAD60` is addressed as live `0x008CADA0` and its case-5
entry points to live `0x0076D3C0`, displayed `0x0076D380`. When its selector is
not `-1`, the block stores
`((FUN_001801b0() >> 3) % 3) + 3 * (selector - 1)` as a halfword at object
`+0x416`. This accounts for all four physical BTL low-31 call opcodes: two
decoded and two recovered from Ghidra-undefined spans.

All 17 raw-word wrapper opcodes omitted by Ghidra are likewise instructions in
coherent reachable blocks. Most spans begin at the return fall-through from a
decoded call. The four sites in the displayed `0x0079B600..0x0079BA4C` switch
are selected by the 11-entry table addressed at live `0x008CD520`; after the
BTL `-0x40` display correction its entries land at displayed `0x0079B66C`,
`0x0079B740`, `0x0079B7F4`, `0x0079B83C`, `0x0079B8C8`, `0x0079B974`, or the
common exit. Their complete reduction/use grouping is:

| Displayed raw-only call sites | Proven immediate reduction or use |
| --- | --- |
| `0x006F9FC8`, `0x006FA1DC`, `0x006FA3BC`, `0x006FA4D8` | Each computes `uint32(word ^ 0x80000000) % 5` and branches on the result, manually reproducing the bounded wrapper with bound four. |
| `0x00746590` | Tests `word & 1` to select one of two control-flow paths. |
| `0x0079B6E4`, `0x0079B784`, `0x0079B904` | Compute signed `word % 5`, pass it through integer absolute value `FUN_001771a0`, and add 55. |
| `0x0079B740` | Passes `word & 1` through the same absolute-value helper; the absolute operation is redundant. |
| `0x007A0E78` | Retains the word across a call that obtains a dynamic divisor, performs unsigned remainder, takes the absolute value, and truncates it to 16 bits. The divisor's nonzero runtime precondition is not established here. |
| `0x007C6DA4`, `0x007C6DC8` | Two separate `word & 1` draws select two table-pointer offsets. |
| `0x007F901C`, `0x007F941C` | Compute signed `word % 5`, then absolute value, producing `0..4` for subsequent arithmetic. |
| `0x00834B88` | Computes compiler-corrected signed `word % 2`, takes its absolute value, and adds 17. |
| `0x008351D0`, `0x008351FC` | Two successive compiler-corrected signed remainders modulo two are converted to absolute `0` or `1` selectors. |

This accounts for all 56 physical BTL `FUN_001801e0` opcodes: 39 decoded and
17 recovered from undefined spans. It also illustrates why treating the raw
return as unsigned in source-level reasoning is unsafe unless the next
instruction explicitly does so.

The 94 bounded-integer opcodes omitted by Ghidra occupy 62 undefined spans, but
raw backward disassembly recovers the `a0` value source at every call. Eighty-two
use a positive literal:

| Inclusive bound | Raw-only calls | Result cardinality |
| ---: | ---: | ---: |
| 1 | 5 | 2 |
| 2 | 8 | 3 |
| 3 | 7 | 4 |
| 5 | 2 | 6 |
| 10 | 2 | 11 |
| 15 | 5 | 16 |
| 30 | 2 | 31 |
| 50 | 1 | 51 |
| 60 | 9 | 61 |
| 100 | 38 | 101 |
| 150 | 3 | 151 |

The remaining twelve use dynamic bounds:

| Displayed call | Bound source before the call |
| --- | --- |
| `0x006CD834` | Signed byte at caller object `+0x2A`, minus one. |
| `0x006FF000` | Signed halfword at caller object `+0x19C`. |
| `0x006FF7B8` | A runtime value explicitly sign-extended from 16 bits in `s0`. |
| `0x00700100` | Signed halfword loaded from caller-global state. |
| `0x00700B20` | Signed halfword at caller object `+0x19C`, plus one. |
| `0x00730A90` | The block's incoming `a0` value. |
| `0x0074FEFC`, `0x0074FF80` | Word at caller object `+0x2A4`; a preceding branch excludes zero, and the two calls are on alternate paths. |
| `0x007FFBD4` | Runtime word loaded through an object pointer, minus three. |
| `0x0081D3D8` | Unsigned halfword at caller object `+0x1310`; skipped when zero. |
| `0x0081D430` | Unsigned halfword at caller object `+0x1340`; skipped when zero. |
| `0x00826850` | Unsigned halfword at caller object `+0xDE0`; skipped when zero. |

No raw-only bounded call passes a literal zero or negative value. The signed
dynamic sources can still do so if their caller-owned preconditions permit it;
the wrapper then applies the absolute-magnitude behavior documented above. All
94 calls consume one MT word regardless of the eventual bound, and the literal
cardinalities in the table are inclusive rather than the common exclusive
`0..n-1` convention.

The same backward argument trace accounts for all 70 raw-only
`FUN_001802b0` opcodes. Fifty-nine pass fixed positive binary32 scales:

| Exact bits | Round-trip value | Raw-only calls |
| --- | ---: | ---: |
| `0x3C23D70A` | `0.01` | 1 |
| `0x3DCCCCCD` | `0.1` | 2 |
| `0x3E000000` | `0.125` | 1 |
| `0x3E4CCCCD` | `0.2` | 3 |
| `0x3ECCCCCD` | `0.4` | 1 |
| `0x3F060AA4` | `0.52359986` | 1 |
| `0x3F060B41` | `0.5236092` | 1 |
| `0x3F20D97C` | `0.62831855` | 1 |
| `0x3F490FDB` | `0.7853982` | 1 |
| `0x3F800000` | `1.0` | 1 |
| `0x3FC90FDB` | `1.5707964` | 2 |
| `0x40490FDB` | `3.1415927` | 11 |
| `0x40800000` | `4.0` | 1 |
| `0x40A00000` | `5.0` | 2 |
| `0x40C90FDB` | `6.2831855` | 1 |
| `0x41200000` | `10.0` | 4 |
| `0x41700000` | `15.0` | 1 |
| `0x41A00000` | `20.0` | 2 |
| `0x41F00000` | `30.0` | 4 |
| `0x42480000` | `50.0` | 3 |
| `0x428C0000` | `70.0` | 3 |
| `0x42960000` | `75.0` | 1 |
| `0x42C80000` | `100.0` | 4 |
| `0x43160000` | `150.0` | 6 |
| `0x43FA0000` | `500.0` | 1 |

The remaining eleven scales are caller-derived:

| Displayed call | Scale source before the call |
| --- | --- |
| `0x007463C0`, `0x00746458`, `0x007464DC`, `0x00746518` | Four floats loaded from the caller record at `+0x20`, `+0x10`, `+0x14`, and `+0x34`. |
| `0x0074C310`, `0x0074C828` | Product of caller-record floats at `+0x29C` and `+0x2A4`. |
| `0x00753398` | Saved scale selected earlier from a record `+0x10` float or literal `0.1f`. |
| `0x0080F704`, `0x0080F720` | Paired float entries loaded from a caller-built stack table. |
| `0x008350F4` | A helper result, or explicit positive zero on the alternate branch. |
| `0x008351A0` | A separate helper result, or explicit positive zero on the alternate branch. |

No raw-only signed-scaled call passes a literal zero or negative scale. Every
fixed-scale site therefore consumes one MT word. The explicit zero paths at
`0x008350F4` and `0x008351A0` consume none, directly exercising the resident
wrapper's zero fast path; zero or a negative sign is not ruled out for the
other caller-derived scales. The 59 fixed plus 11 dynamic sites account for all
70 physical raw-only opcodes and, with the 173 decoded calls, all 243 physical
BTL `FUN_001802b0` opcodes.

A separate structural-entry audit covered all 193 raw-only opcodes for the
low-31, raw-word, bounded, signed-scaled, and central-remap wrappers together.
They occupy 92 Ghidra-undefined spans. Eighty-eight span starts are exactly the
return address after a decoded `jal` and its delay slot, so ordinary call
return enters them directly. The four exceptions also have explicit incoming
paths:

- the span at displayed `0x006FD890` is selected by outcomes seven and eight
  of the preceding nine-entry dispatch. The table addressed at live
  `0x008C38C0` contains two live `0x006FD8D0` entries, which map back to that
  displayed span start;
- decoded branch `0x00704980` directly targets the span at `0x00704BEC`;
- the span at `0x0076D380` is selected through the case table already
  described for the second raw-only low-31 call;
- the `0x0079B66C..0x0079B9B3` span is entered through the 11-entry switch
  table already described for the raw-word calls.

Thus none of these 92 containing spans is a static orphan. This establishes an
entry edge, not that every internal condition is feasible in every runtime
state, and it does not assign higher-level gameplay meaning to the callers.

The decoded LCG calls include three table selections near the exported
`ccDummyCamera` / `ccCamera01` labels. For example, `FUN_006dcd90` calls at
displayed `0x006DD2EC` and uses `output % table_count + 1` before indexing the
table. Six later calls at displayed `0x00733A10`, `0x00739230`,
`0x0073C21C`, `0x0073E15C`, `0x00741174`, and `0x00741FEC` select one of 42
vectors at `0x003FBC80` and scale/store the result. Ghidra omitted the calls at
`0x0073C21C` and `0x00741174` by splitting their surrounding functions at
undefined spans, but raw disassembly proves normal fall-through from the
preceding instructions. These observations describe labels and data flow only;
they do not claim a player-visible camera policy.

The two remaining aligned LCG opcodes are at displayed `0x0072D050` and
`0x0072D0CC`. Both begin coherent instruction sequences that compute
`((output >> 3) & 0x1800) * pi / 32768.0f` and store the results at object
`+0xE4` or `+0xE8`. However, the preceding decoded code dispatches elsewhere
through an indirect jump, the first sequence branches over the second, and an
aligned scan found no branch, direct jump, or data pointer to either entry.
They are therefore physical import instructions in a statically unreferenced
orphan block, not established runtime consumers.

The complete LCG opcode ledger is:

| Displayed site | Complete-file offset | Archived live site | Static disposition |
| --- | --- | --- | --- |
| `0x006DD2EC` | `0x0002942C` | `0x006DD32C` | Decoded camera-labelled table selector. |
| `0x006DD7F0` | `0x00029930` | `0x006DD830` | Decoded camera-labelled table selector. |
| `0x006DDC58` | `0x00029D98` | `0x006DDC98` | Decoded camera-labelled table selector. |
| `0x0072D050` | `0x00079190` | `0x0072D090` | Raw-only coherent angle-calculation block; no static incoming edge. |
| `0x0072D0CC` | `0x0007920C` | `0x0072D10C` | Raw-only coherent angle-calculation block; no static incoming edge. |
| `0x00733A10` | `0x0007FB50` | `0x00733A50` | Decoded 42-vector selector. |
| `0x00739230` | `0x00085370` | `0x00739270` | Decoded 42-vector selector. |
| `0x0073C21C` | `0x0008835C` | `0x0073C25C` | Raw-only instruction in proven function fall-through; 42-vector selector. |
| `0x0073E15C` | `0x0008A29C` | `0x0073E19C` | Decoded 42-vector selector. |
| `0x00741174` | `0x0008D2B4` | `0x007411B4` | Raw-only instruction in proven function fall-through; 42-vector selector. |
| `0x00741FEC` | `0x0008E12C` | `0x0074202C` | Decoded 42-vector selector. |

### Masked-selector construction family and registration gates

**Observation, high confidence.** The raw-word calls at displayed
`0x007F901C` and `0x007F941C`, and central-remap calls `0x007F9168` and
`0x007F9514`, belong to two complete construction bodies. Ghidra exposes only
their opening instructions; continuous bytes establish displayed
`0x007F8F40..0x007F9350` / live entry `0x007F8F80`, and displayed
`0x007F9360..0x007F965C` / live entry `0x007F93A0`.

Both allocate `0x210` bytes, construct through resident `FUN_0030E770`, and
call `FUN_00308D30(object, 0)` before their RNG sequence. The constructor's
final table `0x005DC830` resolves through RTTI `0x005C81E8` to resident string
`ccEffDrawObj` at `0x005A5BC0`. The registration wrapper returns zero when
its manager global `gp-0x3300`, live `0x006076F0`, is absent; otherwise
`FUN_0030CAE0` checks up to `0x300` manager slots and returns one after
inserting into a free slot, or zero when none is free. The caller's branch
uses that returned value, not just the allocator result.

| Construction body | Direct RNG sequence after nonzero registration return | Completed-body bound |
| --- | --- | --- |
| Displayed `0x007F8F40` | One raw MT word reduced to `abs(int32(word) % 5)`, then one central-remap call with binary32 `(pi, 0.10471976)`. | Fifty attempts. For `s` admitted sequences, `0 <= s <= 50`, direct consumption is `2*s..3*s` MT words. |
| Displayed `0x007F9360` | The same raw reduction and central-remap pair, followed by signed-scaled calls with bits `0x3F060B41` and `0x3F060AA4`. | One attempt; a zero registration return skips all direct draws. An admitted sequence consumes four or five MT words. |

The first body's registration branch at `0x007F8FE8` goes to its loop
increment `0x007F9280`; `slti v1,s1,0x32` at `0x007F9288` bounds fifty
iterations. The second branch at `0x007F93F0` goes to the epilogue at
`0x007F9644`. Its two additional scalar sites are `0x007F95A0` and
`0x007F95C8`; their fixed positive scales each consume one word. Neither
body calls the LCG or 16-bit surface. These are direct-body counts, not a
count for nested allocation, registration, initialization, or later object
updates. `FUN_00308D30` still writes object fields after the manager check,
so this evidence does not establish a safe null-allocation recovery path.

The first body then invokes live BTL `0x007F4000`, displayed
`0x007F3FC0`, three times using consecutive 16-byte records from live table
`0x008B3D80`, displayed `0x008B3D40`. The table's three consumed `float4`s
are `(1.5,1.5,1,1)`, `(1,1,2,1)`, and `(0.2,0.2,3,1)`; its remaining
32 copied bytes are zero. The complete helper
`0x007F3FC0..0x007F4150` constructs/transforms an object and contains no
direct import of the documented RNG surface. These additional objects do
not add direct RNG instructions to the fifty-attempt body.

The full immediate caller family is selected as follows. Addresses in the
table are displayed BTL entries; add `0x40` for live entries.

| Dispatcher | Incoming selector | Construction route |
| --- | --- | --- |
| `0x007F8E10` | `0xF0F0F0` | `0x007F98B0`, then the fifty-attempt `0x007F8F40` body. |
| `0x007F8E10` | `0x202020`, `0xE0A000`, or `0xE0E000` | `0x007F9660`. |
| `0x007F8E10` | Every other value | Fifty-attempt `0x007F8F40` body. |
| `0x007F8EB0` | `0xF0F0F0` | `0x007F9C20`. |
| `0x007F8EB0` | `0x202020`, `0xE0A000`, or `0xE0E000` | `0x007F9950`. |
| `0x007F8EB0` | Every other value | Single-attempt `0x007F9360` body. |

The complete four alternative bodies, displayed `0x007F9660..0x007F9D98`,
were inspected as well. They configure resident emitter/resource helpers and
contain no direct call to the documented RNG surface; their emitter updates
remain owned by [Particle runtime](rendering/particle_runtime.md). This negative does
not exclude nested or later draws. The selector getter at displayed
`0x007F9DA0..0x007F9DB8` returns resident word `0x0061F6E8 & 0x00F0F0F0`.
At displayed `0x007F8418..0x007F8430`, the upstream body stores that result
at receiver `+0x1008` and immediately passes it to the first dispatcher.
That route follows a float comparison result other than `-1.0f`. The second
dispatcher is called at `0x007F7394` with the retained `+0x1008` selector.
Thus each call does not independently resample or reread the selector.

Complete-program direct-`jal` searches found two BTL
sites for live `0x007F8F80`, both inside the first dispatcher, and one for
live `0x007F93A0`, inside the second; resident searches found none. Searches
for the two dispatcher entries each found one BTL caller, the sites above.
These bounds establish the direct static caller family. The broader owner
state and measured invocation frequency remain unresolved; no player-facing
character, move or selector name is inferred from these numeric branches.

### Fixed pairs in a two-record producer

**Observation, high confidence.** The table-loaded central-remap call at
displayed `0x0083DA74` belongs to the complete producer
`0x0083D820..0x0083DEA8`, live entry `0x0083D860`. The producer stores incoming
`a1` as the signed record count at owner `+0xAF4`. When owner `+0xAF0` is
zero, it allocates `count*0x100 + 0x10` bytes and constructs an array with
`0x100`-byte element stride. Existing arrays are reused. The containing C
rendering ends at a returning helper; continuous bytes establish the
loop and its argument loads.

Two eight-byte records at displayed BTL `0x008B7970..0x008B797F`, live
`0x008B79B0..0x008B79BF`, are copied to stack `+0xB0..+0xBF`:

| Record index | `A` bits / value | `B` bits / value | Central-remap words |
| --- | --- | --- | ---: |
| `0` | `0x3F733333` / `0.95f` | `0x3F400000` / `0.75f` | One or two. |
| `1` | `0x3FA00000` / `1.25f` | `0x3F866666` / `1.05f` | One or two. |

Each iteration first calls `FUN_00180210(1)` at displayed `0x0083DA1C`.
Its one-word result selects one of two resource pointers at stack
`+0xC0/+0xC4`; it does not select the remap pair. The loop index selects
the pair through `index*8` at `0x0083DA64..0x0083DA70`. The remapped result
passes through numeric conversion helpers and is stored at record `+0x44`.
The loop increments at `0x0083DDB8` and compares against signed owner
`+0xAF4` at `0x0083DDC0..0x0083DDC8`. These are the producer's only direct
imports of the documented RNG surface.

Complete-program searches for the direct `jal` to live `0x0083D860`
found one BTL site, displayed `0x00849708`, and none in the
resident executable. That caller explicitly loads `a1 = 2` at
`0x008496FC`. A completed call therefore processes the two table records
and consumes four to six MT words directly: one resource-selector word and
one or two remap words per record. This establishes the pair ordering for
the recovered direct route; it does not assume other counts are valid or
exclude a computed indirect call.

The caller's construction branch at displayed `0x00849440` requires owner
word `+0x8 == 0` and signed word `+0x4`, converted to float, equal to `5.0f`.
It then makes three allocation attempts for `0xB50`-byte helper objects.
A zero allocator result skips the producer; successful objects are initialized
before the two-record call. For `s` completed producer calls on this route,
`0 <= s <= 3`, the direct producer contribution is `4*s..6*s` MT words.
The small initializer at displayed `0x0083D760..0x0083D77C` clears the array
pointer and count before these fresh calls. Nested helpers and later record
updates are outside this count; the broader owner lifecycle and player-facing
meaning remain unresolved.

### Guarded dynamic scales in a type-specific callback

**Observation, high confidence.** Displayed BTL `0x00834F60` / live
`0x00834FA0` is the `+0x8C` callback in resident table `0x005E87C0`:
its pointer is at `0x005E884C`. Table RTTI is live BTL `0x008CF0D8`,
displayed `0x008CF098`, whose name pointer resolves to internal class string
`ccSkillSZN000` at displayed `0x008BBA18`. Displayed `0x00873A70..0x00873A78`
loads the table and stores it at receiver `+0x110`. This establishes the
internal type, not a player-facing character or move name.

The complete `0x00834F60..0x008353FC` body has two branches. The first requires
receiver word `+0x10DC == 10` and signed halfword `+0x17A0 == 2`; it updates
local counters and an action record before joining the same random-position
construction used by the other branch. Ghidra's C rendering stops paths at
calls that actually return and displays the scalar arguments as zero. Raw
instruction bytes recover both branches and the following shared contract.
Let `C` be the incoming `a0` receiver, `T` incoming `a1`, and `R` incoming
`a3`. Incoming `a2` is not read by this body.

Define `valid(M)` as `M != 0` and global `0x00607654 != 0`. Missing resident
leaf `0x003083A0..0x003083C8` loads `gp-0x339C` only after checking `a0`
and returns exactly that Boolean. A caller byte is an additional gate before
each leaf call. The two scalar bounds are:

```text
X = valid(T[+0x11C]) && T.byte[+0x189] != 0
      ? T.model[+0xE8] * (0.8f * T.model[+0x2F0]) : +0.0f
Zt = valid(T[+0x11C]) && T.byte[+0x189] != 0
      ? T.model[+0xE4] * (0.3f * T.model[+0x2F0]) : +0.0f
Zc = valid(C[+0x4CC]) && C.byte[+0x539] != 0
      ? C.model[+0xE4] * (0.5f * C.model[+0x2F0]) : +0.0f

x_draw = signed_scaled(X)
z_draw = signed_scaled(Zc + Zt)
position = T[+0x130..+0x13F]
position.x += x_draw
position.z += z_draw
b0 = abs(int32(raw_mt()) % 2)
b1 = abs(int32(raw_mt()) % 2)
if C.word[+0x1800] == 0:
    FUN_00333D10(position, b1, b0 != 0, 2, 0)
```

The multiplication order above follows the six-instruction resident helpers
`FUN_002163C0` and `FUN_002163A0`: multiply the coefficient by model `+0x2F0`
first, then multiply by model `+0xE8` or `+0xE4`. No positivity or nonzero
value is established for those fields. A zero bound suppresses only that
scalar draw. The first branch's raw-only call sites are `0x008350F4`,
`0x008351A0`, `0x008351D0`, and `0x008351FC`; the other branch's matching
sites are `0x00835280`, `0x0083532C`, `0x0083535C`, and `0x00835388`.
Each completed invocation therefore makes exactly two direct raw MT draws
plus zero, one, or two scalar draws. The `+0x1800` visual gate is tested only
after all four calls, at `0x008353B4..0x008353BC`, so it does not save these
draws. Nested work in `FUN_00333D10` is separate from this direct count.

The active-record dispatcher starts at displayed `0x00788BE0` / live
`0x00788C20`. Its two relevant slot calls are displayed `0x00788FB4` and
`0x007892E4`, on branches selected by record signed halfword `+0x56` equal
to zero or one. Both explicitly pass receiver, receiver `+0x21C` pointer,
receiver `+0x200`, and receiver `+0x220` pointer in `a0..a3`. The initial
gate at `0x00788C0C..0x00788C14` requires receiver byte `+0x20C & 1`.
Other eligibility/response checks occur before the slot calls; the full action
and response contract remains with
[Character action callbacks](../gameplay/characters/character_action_callbacks.md) and
[Hit response](../gameplay/combat/hit_response.md). A table entry and these calls
establish static dispatch structure, not feasibility of every class/state pair.

A complete-program search for `lw t9,0x8C(t9)` in resident and
BTL found these two receiver-`+0x110` uses and three BTL calls through a
different object's `+0x50` table. The resident search found none. This is a
bound on that exact instruction form, not an exhaustive indirect-call census.
The neighboring inspected table at `0x005E8AC0` uses live `0x007895F0`
in the same slot; displayed `0x007895B0/0x007895B4` is only `jr ra; nop`.
The random-position body is therefore an explicit type-specific override,
not behavior established for every receiver that reaches the shared slot.

### LCG-selected 42-vector table

The absolute resident table at `0x003FBC80` is exactly 42 consecutive
16-byte `float4` records (672 bytes; clean-ELF file offset `0x002FBD80`;
SHA-256 `692AEB37982E021CA8D08AA14506C723B44948FDC3C6CA8F0BAD927CCEF82C34`).
All 42 xyz triples are distinct, every fourth word is exactly `0x3F800000`
(`1.0f`), and the xyz triples form 21 exact antipodal pairs. Their binary32
xyz norms range from `1.414198183637919` to `1.414214015007019`, close to
`sqrt(2)`; this establishes a nearly common-radius symmetric vector set but
does not establish what the game calls it.

The six physical BTL call sites consume it as follows:

| Displayed call | Index expression | Scale / immediate use |
| --- | --- | --- |
| `0x00733A10` | `output % 42` | `vmulx.xyz` by `4.0f`, followed by xyz vector arithmetic and normalization. |
| `0x00739230` | `(output >> 3) % 42` | `vmulx.xyzw` by `7.5f`, store at object `+0xB0`, then clear `+0xB4` and `+0xBC`. |
| `0x0073C21C` | `(output >> 3) % 42` | `vmulx.xyzw` by `7.5f` and store at object `+0xB0`; Ghidra split the surrounding `FUN_0073c1e0` here. |
| `0x0073E15C` | `(output >> 3) % 42` | `vmulx.xyzw` by `7.5f`, store at object `+0xB0`, then clear `+0xB4` before adding it to another vector. |
| `0x00741174` | `(output >> 3) % 42` | `vmulx.xyzw` by `7.5f`, store at object `+0xB0`, clear `+0xB4`, add to another vector, and normalize xyz into object `+0xF0`. |
| `0x00741FEC` | `(output >> 3) % 42` | `vmulx.xyzw` by `7.5f`, store at object `+0xB0`, add it to another vector, then clear the resulting y word before a later store. |

These selectors use plain remainder and are slightly biased even over the
LCG's complete period. For `output % 42`, the 31-bit output domain divides as
`2^31 = 42 * 51130563 + 2`, so indices 0 and 1 each have one more output value
than the other indices. After `output >> 3`, the quotient domain divides as
`2^28 = 42 * 6391320 + 16`, so indices 0 through 15 each have one more shifted
value than indices 16 through 41. The LCG's full-state cycle visits every
31-bit exposed value equally often, so these are exact full-period counts, not
an assumption of ideal randomness.

The BTL C export appears to call `FUN_00180260` eight times, but the instruction
listing contains seven calls. The eighth C occurrence is overlapping recovery
of the same instruction at displayed `0x00755ED0` in both `FUN_00755e30` and
`FUN_00755e60`. Seven is the physical instruction count.

All seven physical half-unit calls are in four initialization routines. The
mutually exclusive calls `0x007530C8` / `0x00753144` in `FUN_00753070` use
either `base + width * (result + 1) * 0.5` or `(result + 1) * 5` and store at
object `+0x298`. Calls `0x00754514` / `0x00754598` in `FUN_007544e0` use the
same base-plus-width interpolation and store at `+0x294`. When its branch is
taken, `FUN_00755830` calls consecutively at `0x007558A8` and `0x007558F0` to
set `+0x298` with base-plus-width interpolation and `+0x29C` with its unbased
`width * (result + 1) * 0.5` counterpart. Finally, physical call
`0x00755ED0` in `FUN_00755e30` contributes to
`size * 0.6 + size * (result + 1) * 0.19999999` at `+0x330`.

For nominal pre-rounding result support `[-0.5, 0.5)`, the common coefficient
`(result + 1) * 0.5` spans `[0.25, 0.75)`, `(result + 1) * 5` spans
`[2.5, 7.5)`, and the last size coefficient spans approximately
`[0.7, 0.9)`. These caller formulas strongly confirm that the unusual signed
half-unit semantics are intentional; no gameplay role is assigned to the
objects here.

## Representative non-damage MT consumers

The following resident callers establish wrapper semantics without depending
on damage behavior:

- `FUN_001f1d60`, call `0x001F1E00`, builds an accepted-ID array from IDs 1
  through 93, calls
  `FUN_00180210(remaining - 1)`, emits the selected element, swaps the final
  element into its slot, and decrements the count. This is direct evidence that
  the argument is an inclusive upper index and shows sampling without
  replacement.
- `FUN_001ffb30`, calls `0x001FFB6C`, `0x001FFBA8`, and `0x001FFBD8`, uses
  `FUN_001801b0() % 3` or `% 6` to select table entries. Its callee
  `FUN_001ffc30`, call `0x001FFC58`, uses `% 7` when given `-1` and indexes the
  table beginning at `PTR_s_loading00_ccs_005c1470`, then loads the selected
  `loadingXX.ccs` resource. This is definitive randomized loading-asset
  selection.
- `FUN_001f9470`, calls `0x001F94D0` and `0x001F94E4`, draws two
  `FUN_001802b0(3.0f)` results while a transient counter is active and adds
  them independently to render-object coordinate fields `+0x50` and `+0x54`.
  This establishes a signed x/y jitter consumer.
- `FUN_003083d0`, call `0x00308518`, takes the signed raw return from
  `FUN_001801e0`, applies remainder by a positive interval and then absolute
  value, and uses it while constructing each of 12 effect objects. This
  confirms that at least one caller intentionally handles the raw wrapper as a
  signed value rather than assuming a nonnegative 32-bit result.
- `FUN_001de1c0`, call `0x001DE3EC`, uses `FUN_001801b0() & 1` to choose `-1`
  or `+1` only when a spatial-overlap separation length is exactly zero. This
  establishes a direct low-bit/parity use.

These consumers, the `ccToneShadeAnimRandom` LCG consumer, and the three
effect-object 16-bit consumers prove that all three streams are used outside
damage calculation.

## Caller reductions and conditional tie selection

The following are different reductions of a shared MT word, not independent
generators. Counts in this section enumerate all `2^32` input bit patterns;
they do not assert an observed probability, call independence, or a caller's
frequency during play.

### Unsigned XOR reduction and folded signed remainder

The AI action-record selector at displayed `0x006F2B40`, live `0x006F2B80`,
does its final choice at displayed `0x006F2E6C`. Raw bytes
`78 00 06 0C` establish `jal 0x001801E0`; the following `lui`, `xor`,
`divu`, and `mfhi` establish
`uint32(word ^ 0x80000000) % eligible_count`. In particular, `divu` at
displayed `0x006F2E7C` is word `0x0053001B`. The decompiler's signed C `%`
expression does not describe that instruction. For a nonempty list this
selection consumes one MT word, even when the list has only one element.
The empty-list branch returns `-1` before the draw. Filtering can itself draw
through its predicate; this is a count for the final selection only. The
complete filter and follow-on draws belong to
[Battle AI](../gameplay/session/battle_ai.md#action-record-selection-and-direct-queues).

By contrast, the raw-only switch call at displayed `0x0079B6E4` uses signed
`div` at `0x0079B6F0` (word `0x0043001A`) with divisor five, then `mfhi a0`
and `jal 0x001771A0`. The resident absolute-value leaf consists of `bgez`,
`move`, conditional word-sized `subu`, and return. Thus its result is
`abs(int32(word) % 5) + 55`, not unsigned remainder or absolute value before
division. The previously established switch-entry audit supplies the incoming
edge. The same folded signed reduction is present at the other sites grouped
in the raw-word ledger above.

Let `M = 2^31` and positive divisor `m <= M`. The exact preimage count of
folded result zero is
`floor((M - 1)/m) + 1 + floor(M/m)`. For `1 <= r < m`, its count is
`floor((M - 1 - r)/m) + 1 + floor((M - r)/m) + 1`. This follows by counting
nonnegative magnitudes `0..M-1` and negative magnitudes `1..M` separately;
the asymmetry comes from `INT32_MIN` having no positive counterpart.
For the proven divisor-five sites:

| Result `r` | Unsigned XOR remainder by five | Absolute signed remainder by five |
| ---: | ---: | ---: |
| 0 | 858,993,460 | 858,993,459 |
| 1 | 858,993,459 | 858,993,460 |
| 2 | 858,993,459 | 858,993,460 |
| 3 | 858,993,459 | 858,993,459 |
| 4 | 858,993,459 | 858,993,458 |

Both columns sum to `2^32`. Even their per-result bias differs. Divisor two
is a useful special case: `abs(int32(word) % 2)`, `word & 1`, and the
bounded wrapper with argument one all give the same low bit and have
`2^31` preimages per result. This explains their equivalence at the binary
choice sites without generalizing it to divisors three or five.

### Exact-distance two-side tie

The complete helper starts at displayed `0x00709F90`, live `0x00709FD0`,
file `0x560D0`, and ends at displayed `0x0070A068`. Ghidra splits its
instruction listing at `0x00709FD0` and omits the return-from-RNG span
`0x0070A014..0x0070A030`; raw bytes recover that span. The two calls
to resident distance helper `0x001806F0` compare one supplied point against
the two primary-fighter positions. The decisive instructions are:

| Displayed address | Instruction / consequence |
| --- | --- |
| `0x00709FFC` | `c.eq.s f20,f0`: compare the two computed binary32 distances exactly. |
| `0x0070A000` | `bc1f 0x0070A034`: unequal comparison skips the RNG call. |
| `0x0070A008..0x0070A010` | Load bound one, `jal 0x00180210`, delay-slot `nop`: one MT draw on equality. |
| `0x0070A014..0x0070A030` | Return side one for RNG result one, otherwise side zero; both paths skip the distance-order comparison. |
| `0x0070A034..0x0070A050` | `c.lt.s` chooses zero when the first distance is smaller, otherwise one; no draw. |

This is a binary tie only. No candidate reservoir or repeated pairwise
tie-breaking loop occurs in this helper. A byte search for its
absolute live `jal` encoding `F4 27 1C 0C` found one BTL match, displayed
`0x0070B8E0`, live `0x0070B920`, file `0x57A20`. It belongs to the
[separate side-index selector](../gameplay/combat/target_selection.md#separate-side-index-eligibility-selector);
the selector's eligibility and retained side field are owned there. The
helper itself checks whether fighter pointers are null before copying their
positions but still evaluates both stack vectors, so its body alone does not
establish a meaningful null-fighter result. Exact equality of the computed EE
distances establishes the tie branch. IEEE unordered/NaN rules are not used
to interpret this hardware comparison.

### Shuffled IDs versus rejection and separate byte selection

The complete resident `FUN_001F1D60` scans IDs `1..93` through
`FUN_001F7AA0/FUN_001F7BB0`. Their current filter set leaves exactly 74 IDs;
the filter and numeric-ID meaning belong to
[Character IDs](../gameplay/characters/character_ids.md#selector-id-filters).
Its output loop writes one selected halfword at output `+8 + 2*i`, then swaps
the last remaining candidate into the chosen slot. The exact loop at
`0x001F1DF8..0x001F1E48` calls `FUN_00180210` with bounds `73..0` in turn.
It therefore consumes exactly 74 MT words, including the final bound-zero
draw, and emits each accepted ID once. It does not retry a draw or shuffle
the unused terminator. The final stores at `0x001F1E54/0x001F1E58` both write
73: the two leading halfwords are last-index values after generation, not the
initial candidate count 74. `FUN_001F1F70` is the sole direct resident caller
in the xrefs; it allocates and clears `0xC4` bytes and calls this producer
only when its numeric mode argument is four. No player-facing mode name is
assigned here.

The complete `FUN_001F2AC0` has three relevant draw paths:

| Source path in a nonnull manager | MT draws made by this consumer |
| --- | --- |
| Numeric mode five with a nonnull record and its indexed triplet in range | Zero: both ID and later byte come from that record. |
| Existing shuffled list at object `+0x34` | One: the ID is read from the list, then a separate low-31 output is reduced modulo 24 for the byte stored at manager `+0x98` or `+0x9A`. |
| No list, outside the indexed-triplet branch | At least two: repeatedly draw low-31 output modulo 94 until both ID filters pass, then draw the separate modulo-24 byte. Each rejected ID adds one draw; this loop has no iteration cap. |

On the list path, an index above its stored last index wraps modulo
`last_index + 1`, so the generated list can be reused without regeneration.
The separate byte draw still advances the global stream. The zero-manager
entry path returns before all three alternatives. These are complete native
body draw counts, not counts for prior list construction or external callees.
They show that sampling without replacement, rejection sampling, and a
separate attribute draw must not be conflated as one random-character call.

Modulo 94 of the low-31 output has domain division
`2^31 = 94 * 22,845,570 + 68`. Before filtering, residues `0..67` have one
extra preimage. The accepted set contains 50 residues in that group and 24
in `68..93`, so accepting only the filtered residues does not erase the
modulo weighting. This is a static accepted-input multiplicity result;
rejection timing and correlated consecutive MT outputs are not modeled as
independent probability trials.

## Deterministic state implications

The following consequences follow directly from the state and call graph:

- Resetting with tag `t` produces only 32 possible post-reset MT positions,
  selected by `t & 31`. In contrast, the LCG is seeded from all 32 bits of
  `t`.
- For example, tags `0x00000000` and `0x00001100` produce identical MT and
  16-bit reset behavior because both select `n = 0`, but they leave different
  LCG seeds (`0` and `0x1100`).
- Resetting does not make the 16-bit stream a pure function of `t`; its result
  also depends on the pre-reset halfword. A cold process supplies zero, but a
  later reset advances the existing state.
- Reproducing generator outputs across a reset requires the MT array and index,
  `DAT_00602a20` for the future reset tag, LCG 64-bit word `DAT_003fad10`, and
  halfword `0x00607450`. `DAT_00602a24` is useful for observation but is not
  read by resident code.
- A later `FUN_001e0ee0` setter/reset event also depends on the current root
  object's `+0x194` update counter. That upstream field replaces
  `DAT_00602a20` immediately before the reset and therefore supplies both the
  next full LCG seed and the MT low-five-bit selector.
- Resident and BTL callers share the same MT and LCG states. A draw in a
  loading, tone-shade, camera-labelled, or effect path advances the sequence
  seen by every later consumer of that stream.
- Control flow affects MT alignment: zero-scale `FUN_001802b0` consumes no
  word; `FUN_00180350` consumes zero, one, or two; bounded integer calls always
  consume one even when the bound is zero.
- The shared states alone do not determine future call timing. Caller-owned
  counters, branch inputs, allocation results and prior shuffled lists can
  change the order and number of draws.

Derived static vectors for the clean algorithms are:

| Situation | Expected value |
| --- | --- |
| First five fixed-bootstrap MT outputs | `889C77E9`, `C8C10059`, `4F014569`, `3B11BCC1`, `0E34B264` |
| Clean-image tag before any setter | `00001100` (`n = 0`) |
| Tag stored when `FUN_00180060` receives `00001100` | `889C77E9` |
| Next public MT word in that same case | `C8C10059` |
| LCG state after first advance from seed `0x1100` | `71370215ED71FD01` |
| Corresponding first LCG return | `71370215` |
| LCG first state / return after an update-counter seed of zero | `0000000000000001` / `00000000` |
| First four 16-bit states from cold zero | `AEB6`, `698D`, `4CE8`, `E257` |

These vectors were calculated from the exact static recurrences and constants;
they have not yet been checked against a live trace.

### Complete cold reset map

For any incoming tag with low five bits `n`, the fixed MT stream discards
outputs `0..n-1`, stores output `n` as `DAT_00602a20`, and leaves output
`n + 1` for the next public draw. Starting the separate 16-bit stream from its
cold zero value gives this complete reset map. The MT index after initialization
is also `n + 1`.

| `n` | Retained tag `MT[n]` | Next public `MT[n+1]` | Cold 16-bit state after `n` steps |
| ---: | ---: | ---: | ---: |
| 0 | `889C77E9` | `C8C10059` | `0000` |
| 1 | `C8C10059` | `4F014569` | `AEB6` |
| 2 | `4F014569` | `3B11BCC1` | `698D` |
| 3 | `3B11BCC1` | `0E34B264` | `4CE8` |
| 4 | `0E34B264` | `AF349767` | `E257` |
| 5 | `AF349767` | `145102A9` | `3812` |
| 6 | `145102A9` | `7CABC042` | `0EFF` |
| 7 | `7CABC042` | `31EAE5A7` | `EAB2` |
| 8 | `31EAE5A7` | `0F96266C` | `597E` |
| 9 | `0F96266C` | `0EADC242` | `8CAF` |
| 10 | `0EADC242` | `A33A0F84` | `E170` |
| 11 | `A33A0F84` | `BC2AE9C5` | `2C76` |
| 12 | `BC2AE9C5` | `EC3B11E1` | `608F` |
| 13 | `EC3B11E1` | `DF4B14E3` | `30F0` |
| 14 | `DF4B14E3` | `03777F97` | `F276` |
| 15 | `03777F97` | `B845C23A` | `F88D` |
| 16 | `B845C23A` | `171F18C0` | `10EA` |
| 17 | `171F18C0` | `D0089F8C` | `725E` |
| 18 | `D0089F8C` | `17AA3BEE` | `F82F` |
| 19 | `17AA3BEE` | `DFFC5D7A` | `0F72` |
| 20 | `DFFC5D7A` | `ED4F076E` | `E47E` |
| 21 | `ED4F076E` | `1B0B50C8` | `40AE` |
| 22 | `1B0B50C8` | `1CD2D1B6` | `B16F` |
| 23 | `1CD2D1B6` | `891633C1` | `EC70` |
| 24 | `891633C1` | `00ECAD12` | `6076` |
| 25 | `00ECAD12` | `C2AC3908` | `308C` |
| 26 | `C2AC3908` | `169EC52B` | `F0E6` |
| 27 | `169EC52B` | `6F678F68` | `F24D` |
| 28 | `6F678F68` | `EC5B1DA4` | `F7E9` |
| 29 | `EC5B1DA4` | `65B766B7` | `065A` |
| 30 | `65B766B7` | `E7043078` | `C81E` |
| 31 | `E7043078` | `267025AE` | `CF2D` |

Only the MT columns are functions of `n` alone. The LCG state after reset is
the complete incoming 32-bit tag, and a non-cold 16-bit column must be obtained
by advancing that run's existing halfword `n` times.

### Repeated direct-reset attractors

`DAT_00602a20` has only three resident xrefs: two reads inside
`FUN_00180060` and the write in `FUN_001801a0`. Ordinary MT, LCG, and 16-bit
draws do not change it. Therefore, if the direct `FUN_001f4360` reset recurs
without the external counter setter, the next low-five-bit selector is exactly
`MT[n] & 31` from the table above.

The resulting 32-node map has only two attractors:

```text
4 -> 4
2 -> 9 -> 12 -> 5 -> 7 -> 2
```

Starting selectors `4`, `11`, `27`, and `29` reach the fixed point; all other
selectors reach the five-cycle within at most six direct resets. Clean selector
zero goes to 9 on its first reset. The corresponding retained full tag at the
fixed point is `0E34B264`. Around the five-cycle, the full retained tags are:

```text
n=2  -> 4F014569 -> next n=9
n=9  -> 0F96266C -> next n=12
n=12 -> BC2AE9C5 -> next n=5
n=5  -> AF349767 -> next n=7
n=7  -> 7CABC042 -> next n=2
```

This short attractor applies to the reset selector, retained tag, MT position,
and newly seeded LCG. It does not by itself make the complete state repeat:
the 16-bit stream is advanced rather than reset. In a cold-start sequence of
these resets with no other `FUN_00180560` calls, the five-cycle advances that stream
by `9 + 12 + 5 + 7 + 2 = 35` steps per lap. Since 35 is coprime to the cold
cycle length 43,951, the complete reset-state period is `5 * 43951 = 219755`
resets after entering the attractor. On the fixed `n=4` branch it is 43,951
resets. Intervening effect-side 16-bit calls change those complete-state periods
but not the low-tag attractor.

## Confidence and useful negative results

The addresses, initialized bytes, algorithms, decoded instruction counts, raw
aligned opcode counts, xrefs, draw counts, and reset relationships are
high-confidence static findings from the clean instruction listings and ELF
image. The class/resource-backed caller descriptions are also high confidence.
Descriptions of unlabeled BTL tables are deliberately limited to their
observed indexing and stores.

Not established here:

- the exact runtime frequency or ordering of every caller in a particular game
  mode;
- the tone-shade animator's virtual invocation path or a writer that changes
  its default period;
- exact hardware arithmetic low bits across all float callers;
- runtime branch feasibility, frequency, and full higher-level caller semantics
  for the raw-only BTL bounded-integer and signed-scaled paths, despite their
  established static span-entry edges and complete argument ledgers above;
- a gameplay interpretation for the BTL camera-labelled tables or 42-vector
  selections;
- an exhaustive catalogue of every small caller-owned recurrence unrelated to
  these resident shared states.

Useful negatives are that `FUN_001801a0` is not an immediate reseed,
`DAT_00602a24` is never read by resident code, the 16-bit stream has no
resident reset, `FUN_00180260` has no resident call xref (its seven identified
users are in BTL), and BTL has no direct or identified indirect import of the
seed/reset/core entry points and no identified direct RNG-state access.
