# Substitution Reliability Knowledge

This document promotes the durable findings from the 2026-07-05 substitution-reliability investigation. It records tested negative results and the established control-flow boundary so the same hit-processing gates are not investigated again without new evidence.

## Stable references

- Canonical PNACH: `@pcsx2_files/SLPS-25837_C0659AD1.pnach`.
- Historical CRC alias during the investigation: `@pcsx2_files/SLPS-25837_E0F064C5.pnach`. CRC aliases are managed links and are not canonical.
- Historical NA2 decompiler/Ghidra evidence remains available through Git
  history. Restore reusable analysis only under `@analysis/disassembly/NA2/`.
- Reproducible substitution-cost patch: `ELF-S001` in `na2_patcher/modules/raw_binary/patch_sets/battle_logic/`.

Function names below are Ghidra-generated names for the NA2 boot ELF and are stable only within the preserved analysis project.

## Runtime tests that did not improve reliability

Three temporary EE branch edits were tested and then disabled:

| EE address | Test | Result | Durable conclusion |
| --- | --- | --- | --- |
| `0x201917A8`, `0x20191C80` | Force the internal `0x800` action-flag consumer path | Black screen | These branches protect packet/action setup. Do not bypass them without a narrow, proven context guard. |
| `0x20190FEC` | Ignore the `0.0078125` impact threshold | No difference | The small-impact threshold in `FUN_00190f40` was not the observed reliability gate. |
| `0x20190FD4` | Allow the primary action path outside mode bits `== 3` | No difference | The mode-bit gate near this address was not the observed reliability gate. |

The first test appears to call `FUN_001921c0` with invalid context. These results constrain future work; they do not prove that the affected code is irrelevant in every state.

## Known substitution-cost patch

The historical 16-bit PNACH write at EE address `0x202298BC` changes a downstream substitution packet/cost field in `FUN_001c3da0` to `0x4040` (3/15). It affects an already-built packet and is not the reliability gate.

It is preserved as disabled, runtime-proven raw-binary patch `ELF-S001`, which guards boot-ELF file offset `0x1299BC` and replaces `80 3F` with `40 40`. Use the module patch rather than restoring a permanent PNACH write.

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

Do not resume by broadly patching `FUN_00190f40` or forcing `FUN_001921c0` unless new runtime evidence narrows the condition. The next useful comparison is successful substitution versus ignored input before hit processing:

- who reads or queues the substitution input;
- who selects or prepares character action slot `+0x94`;
- selected action object `+0x18` flags;
- character `+0xA8` state bits;
- scratch `+0x20C` after `FUN_00198290`;
- callers and writers around `FUN_00194230`, `FUN_001942f0`, `FUN_00196b40`, and `FUN_00196620`.

The unresolved question is whether the failure occurs in an input buffer/window rather than in downstream action-flag consumption. That remains unresolved, not confirmed.

When exporting listings from the preserved Ghidra project, omit undefined data. A full dump including undefined data was found too large to be useful.
