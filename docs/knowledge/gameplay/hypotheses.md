# Gameplay hypotheses

These are unverified historical leads retained because they identify concrete
addresses or functions. The labels and effects must be re-established from
current disassembly or runtime evidence before implementation.

## Substitution cost variant

Historical notes record EE `0x202298BC` / ELF file `0x1299BC` value `0x4040`
as 3/15 and `0x40A0` as 5/15. The 3/15 form is preserved as disabled,
runtime-proven patch `ELF-S001`; see
[`../localization/substitution.md`](../localization/substitution.md). The 5/15
form has not been revalidated.

## Extra-hit branch lead

A historical one-branch candidate exists at EE `0x20241F40`, labelled “extra
hit.” Its instruction change remains recoverable from Git history, but the
label and runtime effect are unproven and must not be conflated with the
accepted `ELF-B002` battle-logic patch.

## Jutsu-name display lead

An old note near EE `0x001F64A4` proposes forcing part or all of `v0` to zero in
a branch delay slot. The intended bit or byte and the affected screen behavior
are unspecified.

## Ultimate-Jutsu chakra leads

Historical notes point to ELF file `0x1492B0` for level-scaled chakra
subtraction and `FUN_002254a0` for shared chakra addition. Recheck the preserved
disassembly before assigning either role or designing a patch.
