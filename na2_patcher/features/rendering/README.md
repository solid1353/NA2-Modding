# Rendering

File-backed changes to NA2's rendering behavior.

## ELF-R001: Native 16:9 horizontal scale

Clean NA2 constructs its primary renderer through the global wrapper at
`0x00609160`. `FUN_0010A1D0` stores the resulting renderer pointer at wrapper
offset `0x3C`, or `0x0060919C`. In the current build that pointer resolves to
heap object `0x00B0A790`, making its horizontal-scale field
`0x00B0A790 + 0x274 = 0x00B0AA04`.

The official PCSX2 widescreen cheat overwrites that same field after allocation
with `0.75f`. Its absolute heap address changes whenever the resident-payload
reservation changes.

`ELF-R001` patches the primary-wrapper initialization sequence at runtime
address `0x001060D4` (ELF offset `0x61D4`). Immediately after
`FUN_0010A1D0` returns, the sequence loads the renderer from the stable wrapper
pointer and stores `0x3F400000` at renderer offset `0x274`. It leaves every
secondary rendering state and the vertical scale at `0x278` untouched.

The previous replacement of the shared rendering-state writer was too broad:
it forced `0.75f` into secondary viewports as well as the primary renderer.

The emulator output aspect remains a separate PCSX2 setting. The file-backed
patch does not depend on a PNACH memory write.

## Binary patcher

The downstream module is `binary_patcher`.
