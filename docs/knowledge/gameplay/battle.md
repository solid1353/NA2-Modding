# Battle behavior knowledge

This document owns unresolved and established leads about battle behavior that
do not belong to a narrower gameplay subsystem.

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
