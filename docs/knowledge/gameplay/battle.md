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

In the baseline battle marker the live fighter's effect container at
fighter `+0x8C4` was empty and `u16` field `+0x8E8` was `0xFFFF`. The two
awakening markers contained one effect and changed `+0x8E8` to `0x57` and
`0x22`, respectively; their visible HUD abbreviations were `Nin.` and `Reg.`.
These are character-specific native IDs, not two global awakening categories.
`FUN_003047c0` validates the complete native ID domain `0..0x89`; the bootstrap
therefore accepts `none` or one numeric ID in that range and passes it through
unchanged.
`FUN_00305c30(fighter, effect_id, -1, 1)` is the native high-level effect
entry: it validates the effect category, resolves the default parameter,
constructs the effect through `FUN_00305270`, performs native side effects,
and writes the active effect ID to fighter `+0x8E8`. The hook at runtime
`0x001ECACC` (ELF `0xECBCC`) retains `FUN_001edb70`, then invokes this entry
once after the Player 1 fighter exists. It retries until `+0x8E8` confirms the
requested ID and resets its one-shot state whenever a new bootstrap reaches
controller state `7`.

The implementation deliberately leaves starting HP to the independently
verified native Practice enum described above. It uses neither savestates nor
input recordings at runtime; those artifacts are evidence and regression
inputs only.

Candidate validation replayed the same eight-marker recording against two
isolated worker builds. With the test configuration (`p1: 84`, `support: 26`,
`awakening: none`), every marker was already in the live Practice battle;
marker `0001` had manager state `4`, substate `3`, both configured current and
match-start identities, live character `84`, HP `0.5`, and active effect
`0xFFFF`. A second build with `awakening: 0x22` reached the same state with
effect `0x22` active at marker `0001`, visibly reported as `Reg.`. Later marker
effects followed the recording's gameplay inputs rather than being forced back
to `0x22`, confirming that the bootstrap applies only the initial active state.

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
