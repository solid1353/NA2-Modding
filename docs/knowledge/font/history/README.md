# Historical Font patch records

This directory preserves inert declarative records for superseded Font
experiments. They are research evidence, not selectable binary-patcher patch sets,
and the current profile does not consume them.

- `font_m01/` reconstructs the former m01 baseline and the rejected semantic
  NUN5 palette experiment for byte-level audit.
- `font_elf_history/` records the retired m01/m02 and v22/v23 ELF experiments,
  including negative runtime results that must not be repeated blindly.

The active implementation is `na2_patcher/modules/binary_patcher/patch_sets/font/`.
Retain these records only as compact knowledge inputs; generated binaries,
candidate ISOs, screenshots, and apply logs do not belong here.
