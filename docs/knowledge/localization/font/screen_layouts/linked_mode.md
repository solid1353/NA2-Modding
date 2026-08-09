# Linked Mode Font layouts

Font-owned layout evidence for the Linked Mode selector and its selected-color ABI.

## Linked Mode center-selector isolation

Evidence date: 2026-07-30.

Replacement-batch ss2 identifies the center-screen `Linked Mode`, `Manual`,
and `Auto` selector as main-ELF `FUN_003B8F40`. This is not the adjacent
five-row character-modal family: trial changes to that family left ss2
unchanged, while three exact writes in `FUN_003B8F40` moved only the visible
center modal.

The title path loads local Y `12.0` at runtime `0x003B8FE0` (ELF file
`0x2B90E0`) before its ordinary renderer call. The choice loop loads base Y
`48.0` at runtime `0x003B90A4` (file `0x2B91A4`) and retains a native
`48 + 26*i` formula. Its selected renderer call is at runtime `0x003B90DC`
and its unselected call is at `0x003B90FC`.

NUN5 homolog `FUN_003CBAF0` uses one selected-state-aware
`FUN_00393210` call with local formula `36 + 22*i`. The helper semantics differ
from NA2's separate selected and ordinary renderers, so copying those two
constants directly is not coordinate-equivalent. Supplemental ss2 with
`Manual` selected supplies both NA2 paths in one frame. The earlier
`44 + 26*i` plus selected-only compensation and later `46 + 20*i` candidate
were intermediate geometry trials and are superseded.

The final bounded formula is `45 + 22*i`, with no selected-only compensation,
and the title remains at local Y `8`. The exact clean guards are title
`4041023C`, interval `D041023C`, and base `4042023C`; replacements are
`0041023C`, `B041023C`, and `3442023C`. Final-red captures 18 and 19 show
selected `Auto` and `Manual` red and aligned with NUN5. No adjacent modal is
changed; explicit user acceptance remains pending.

## Linked Mode selected-color ABI correction

Evidence date: 2026-08-02.

Clean main ELF SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`
proves that the selected Linked Mode call at file `0x2B91DC` supplies exactly
four arguments: `a0=object`, `a1=draw_x`, `a2=draw_y`, and `a3=text`. The
pre-call block at `0x2B91C4..0x2B91D8` never initializes `t0`.

The native callee `FUN_00382610` forwards selected state `1` to
`FUN_00379040`. That state renders the gray pass and then packed red
`0xFF0000D4`. By contrast, the Pause selected callback legitimately receives a
fifth packed-color argument in `t0` before tail-calling `FUN_003827A0`.
Reusing that callback for Linked Mode treated undefined caller-saved `t0` as a
color; the integrated capture exposed the result as blue selected `Auto`.

The bounded correction is deliberately color-only. The existing Linked metric
session, centered `1.05` scale, computed draw origin, title position, shared
choice base, and row interval remain unchanged. The typed Linked entry ignores
incoming `t0` and supplies `0xFF0000D4` to the retained callback. This preserves
the user-reviewed geometry while restoring the native selected red. A future
renderer refactor may instead use a dedicated tail callback to `FUN_00382610`,
but it must first prove byte-equivalent visible geometry; it is not part of
this correction.
