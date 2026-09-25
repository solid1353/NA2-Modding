# Confirmation Font layouts

## Research coverage

- **Assigned scope:** compare clean NA2 and NUN5 Battle, Mode Select, Collection, and memory-card confirmation text layout.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected, including the NA2 memory-card body loop and window constructor,
  the NUN5 paragraph and choice draw chains, and both games' 48-entry
  save-message tables.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** feature hooks and behavior belong to
  [Font](../../../../features/localization/font.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase. The memory-card comparison includes one supplied NUN5
  create-data confirmation; other states have static coverage only.

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
minus `12`, independently of the body loop. `FUN_001E70B0` and
`FUN_001E7130` draw their fixed Save/Return-to-title questions directly through
`FUN_003821D0`, outside that fragment loop.

### Panel closing

`FUN_001E3F20` controller states `8`, `9`, and `10` call `FUN_001E5C30`
until the visible lower and upper panels have closed. That helper requests
`FUN_00381930(window, 8)` for each open panel, waits for `FUN_00381FC0`
to report it closed, and only then clears UI visibility bytes `+0` and `+3`.
`FUN_00381930` sets window animation state `2` and both duration counters to
`8`; the ordinary UI draw `FUN_001E5BA0` continues updating each visible
window through `FUN_00380B60` during the close.

State `9` then resets the worker through `FUN_001E1D20`, starts the optional
outer transition through `FUN_001E5730`, and advances to state `11`. State
`11` returns result `1` after that transition finishes, or immediately when
the controller has no outer transition. State `8` instead returns `2` in
Load mode or reinitializes the Save question in Save mode.

### Message boundaries

The upper-slot renderer `FUN_001E6370` uses the date draw record for an empty
slot. Its empty branch at `0x001E6770..0x001E6784` loads the label through
`0x0060302C`, clears the time text through the empty string at `0x00603038`,
and gives the label the row's Y plus `18`. The selected branch adds UI
`+0x18` to its X, approaching `-24`, before drawing the shadow and foreground.
Each draw advances that offset by one third of the remaining distance and
snaps it to `-24` when the step is smaller than one unit. The all-empty Load
case skips selected-row movement; Save retains it for the selected empty row.
The empty branch does not compute a centered position from the window bounds.

`FUN_001E34D0` indexes the message-pointer table at `0x006B2730` by status.
`FUN_001E5B20` publishes that pointer at UI `+0x40`. A message can contain
multiple adjacent NUL-terminated fragments. For example, status `0x0C` begins
at ELF file `0x3043C0`; its create-data question follows at `0x304407`.
The absent-card start prompt at `0x3046A0` and insufficient-space start prompt
at `0x3047F0` each contain six fragments. The ordinary lower-window caller `FUN_001E5BA0` passes four fragments.
The separate startup check `FUN_001E74E0` calls `FUN_001E7530(object, 7)`
for statuses `0x24..0x27`. That renderer reads the message at object `+0x0C`
and draws up to seven fragments from `(50,100)`, spaced by `30`, without
the lower window. Its choices use Y `316` (selected foreground `314`).
The six-fragment startup strings therefore do not establish a lower-window
truncation bug.

`FUN_001E3120` advances unformatted-card notice `0x0A` to format question
`0x0B` after acknowledgement. It likewise separates insufficient-space warning
`0x08` from the required-space explanation `0x09`. Status `0x0C` instead
contains both the absent-data statement and the create-data question in one
state. NUN5 combines some of the former notices into one paragraph, so message
counts alone do not identify lost text.

The shared Yes/No records at `0x005C0660/0x005C0670` use local Y `80`
in the lower panel. The startup renderer replaces that Y before drawing.
The fixed Save/Return body calls are at `0x001E7104/0x001E7184`.

Other distinct native entries include the wrong-card-type warning at file
`0x303A80`, ordinary load failure at `0x303ED0`, and save failure at
`0x304010`. Their statuses are `0x07`, `0x14`, and `0x19` respectively.

### NUN5 memory-card paragraph

`FUN_001EB950` publishes the selected message at UI `+0x44`.
`FUN_001EB9D0` calls `FUN_001EBEE0`, which draws the complete NUL-terminated
message through `FUN_003937D0`, with a five-line limit and height `85`.
Its zero-origin draw record at `0x00419AA0` selects indexed color `15`.
The same function dispatches Yes/No separately through `FUN_00392920`.

The supplied create-data confirmation has lower window `(8,230,496,144)`,
border widths `8/8`, and text insets `16/12` at window `+0x68/+0x6A`.
`FUN_003937D0` computes width as window width minus `16` and twice the
horizontal inset: `448` here. It forwards that width and the explicit height
to `FUN_00387E80` / `FUN_00387EC0`. The latter copies the message, processes
line breaks, wraps it, and adjusts wrapping when the line limit is exceeded
before the final bounded text draw. This is a paragraph path rather than
NA2's fixed-spacing fragment loop.

The paragraph caller passes horizontal/vertical alignment `0/0` to
`FUN_0018B1B0`: the text is left/top aligned. Its vertical fitting helper
`FUN_0018CAE0` measures the complete block and reduces vertical scale only
when that block exceeds the supplied height; short paragraphs keep their
native advance.

For Yes/No, `FUN_00392920` builds one styled string with five ordinary spaces
between the labels (`gp-0x6520`, address `0x006119D0`). It forwards alignment
`2/2` through `FUN_00392A90` and `FUN_00387C10`: center horizontally and align
to the bottom vertically. The available rectangle is the window size minus
`16` and twice the corresponding text inset: `448x104` here, starting at
`(16,12)`. With a 20-unit text height the choice origin is Y `96`, not the
un-padded interior bottom. Selected-label shadow/color markup does not change
the group alignment.

The English table at `0x006C6890`, selected by `FUN_003D3800`, has 48
entries. Status `0x0C` points to the complete create-data prompt at
`0x0091D3A0`, corresponding to `TEXTENG.BIN` file `0x296A0`. Its body
contains both the absent-data statement and create-data question. The saved
wrapped copy retains both, and the screenshot shows four body lines above
Yes/No. These observations establish this state and the shared drawing
mechanism, not the appearance of every error or transition.
