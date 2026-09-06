# Confirmation Font layouts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Battle, Mode Select, and Collection confirmation text layout, and identify NA2's memory-card message layout.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected, including the complete NA2 memory-card body loop and window constructor.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase.

## Battle quit-confirmation callers

Clean NA2 BTL bytes and runtime state identify two distinct modal
draw calls. The clean BTL file uses `0x006B3F00 + file offset`:

- file `0x1C4048` / runtime `0x00877F48` is
  `800D0E0C00000000`, the native `jal 0x00383600` Yes/No list
  plus NOP;
- file `0x1C407C` / clean runtime `0x00877F7C` is
  `6C090E0C00000000`, the native `jal 0x003825B0` body draw
  plus NOP.

The modal object owns its Yes/No widget at `+0x110` and body widget at
`+0x114`. The list descriptor starts at X/Y `50/24`, uses row extra `12`, and
therefore draws its second row at Y `56`. NUN5 measurements map Yes to
`(64.5,31.5)` and No to `(68.5,49)`.

## Mode Select Return to Title confirmation caller

The earlier classification of object `+0xD0` as the visible body was wrong.
Live object inspection while the prompt was visible found its list empty.
Tracing forward identified `FUN_003825B0` as the first actual consumer: it
builds a four-word draw record from constants `DAT_005B1810` X `24` and
`DAT_005B1814` Y `16`, then calls native UI draw `FUN_00379A20`.

## Collection exit-confirmation body and choice list

- clean address `0x006C6540`, file `0x12680`, calls the ordinary body renderer
  for object `+4`; its eight-byte guard is `6C090E0C00000000`;
- clean address `0x006C6560`, file `0x126A0`, calls the complete choice-list
  renderer for object `+8`; its guard is `800D0E0C00000000`;
- the render-state path repeats the body draw at clean address `0x006C8788`,
  file `0x148C8`, with the same `6C090E0C00000000` native-call guard.

## NA2 memory-card message body

`FUN_001E57B0` constructs the lower message window at `(18,235)` with size
`476x130`. `FUN_00382110` derives its inner size by subtracting twice the
signed border widths at window `+0x30/+0x32` from size `+0x0C/+0x10`.

`FUN_001E5BA0` calls `FUN_001E6060(controller, 4)`. The latter checks the
window at controller `+0x1C` and the body-enabled byte at `+1`, then reads
the message sequence at `+0x40`. Its draw record at `0x004049B0` supplies
local X/Y `22/18` and indexed color `15`.

The loop at `0x001E6174..0x001E61DC` draws each NUL-terminated fragment
through `FUN_003821D0`, advances past its terminator, and adds `30` to Y.
It does not perform paragraph wrapping. `FUN_003821D0` retains window
visibility and bounds checks before delegating to `FUN_00379A20` with the
window's drawing object and context. Selector handling begins separately
at `0x001E61F0`.

`FUN_001E5DC0` places the Next widget using the same window's inner height
minus `12`, independently of the body loop. These findings cover the NA2
memory-card body; no NUN5 counterpart was traced for this section.
