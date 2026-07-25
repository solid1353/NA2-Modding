# Rendering

File-backed changes to NA2's rendering behavior.

## ELF-R001: Native 16:9 horizontal scale

Clean NA2 initializes its persistent `0x2C0`-byte rendering state in
`FUN_0010F2E0`. At runtime address `0x0010F3E8` (ELF offset `0xF4E8`), the
initializer loads `1.0f` into `f16`. `FUN_0010F430` preserves that value in
`f18`, derives the independent `256.0f` and `192.0f` viewport-center fields,
and calls `FUN_0010E460`; `FUN_0010ECC0` then stores `f18` at rendering-state
offset `0x274`.

The official PCSX2 widescreen cheat overwrites that same field after allocation
with `0.75f`. Its absolute heap address changes whenever the resident-payload
reservation changes. `ELF-R001` instead changes the initializer's guarded
`lui v0,0x3F80` instruction to `lui v0,0x3F40`, producing `0.75f` through the
normal rendering-state pointer without depending on heap placement.

The emulator output aspect remains a separate PCSX2 setting. The canonical
PNACH contains no widescreen memory write or aspect directive.

## Binary patcher

The downstream module is `binary_patcher`.
