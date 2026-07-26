# Rendering

File-backed changes to NA2's rendering behavior.

## ELF-R001: Native 16:9 horizontal scale

The known-working PCSX2 widescreen patch for the current build writes
`0x3F400000` (`0.75f`) to `0x00B0AA04`. Savestate pointer scans identify that
address as offset `0x274` of the primary renderer reached through the global
wrapper at `0x00609160`; its renderer pointer is stored at `0x0060919C`.

The absolute heap address changes whenever the resident-payload reservation
changes. `ELF-R001` therefore patches the primary-wrapper initialization
sequence at runtime address `0x001060D4` (ELF offset `0x61D4`). Immediately
after `FUN_0010A1D0` returns, it loads the renderer from the stable wrapper
pointer and stores `0x3F400000` at renderer offset `0x274`. Secondary rendering
states and the vertical scale at `0x278` remain unchanged.

`ELF-R001` is runtime-proven and disabled by default. The emulator output
aspect remains a separate PCSX2 setting.

## Binary patcher

The downstream module is `binary_patcher`.
