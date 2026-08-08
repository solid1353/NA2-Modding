# Rendering

File-backed changes to NA2's rendering behavior.

## ELF-R001: Native 16:9 horizontal scale

Clean NA2 writes the horizontal and vertical scale fields of its persistent
rendering state through `FUN_0010ECC0`. The original four-instruction routine
stores caller-provided `f12` and `f13` at object offsets `0x274` and `0x278`.

The known-working PCSX2 widescreen patch overwrites the horizontal field after
allocation with `0.75f`. Its absolute heap address changes whenever the
resident-payload reservation changes. Changing only one constructor input was
insufficient because later rendering-state updates can supply the original
scale again.

`ELF-R001` instead replaces `FUN_0010ECC0` at runtime address `0x0010ECC0`
(ELF offset `0xEDC0`). It loads `0x3F400000`, stores it at `object + 0x274`,
and preserves the caller-provided vertical scale at `object + 0x278` in the
return instruction's delay slot. Every write therefore uses the live object
pointer without depending on heap placement.

This is the verified good-enough file-backed implementation. It affects every
call through the shared rendering-state writer.

The guarded implementation lives directly in the `rendering` catalog subtree.
Its release-configuration leaf is currently `false`; internal application uses
the binary-patcher engine without exposing a module in the data model.
