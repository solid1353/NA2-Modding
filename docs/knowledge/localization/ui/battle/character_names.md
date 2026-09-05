# Battle HUD character-name renderer

Binary identities and address conventions are defined in the
[Standard game file identities](../../../game/files/file_identities.md).

## Research coverage

- **Assigned scope:** Native Battle HUD character-name positioning, renderer
  ownership, coordinate anchors, and the live destination register.
- **Exploration depth:** The 74 populated E2E character cells were compared
  between NA2 and NUN5, both renderer homologs and their coordinate loads were
  traced, and one NA2 runtime capture checked the destination register.
- **Confirmed coverage:** The mirrored 20-output-pixel difference, 16-unit
  logical anchor difference, NA2 and NUN5 renderer locations, native X/Y loads,
  and the requirement to preserve `v1` across an inserted call are established.
- **Unresolved or untested:** No additional unresolved question is recorded for
  this bounded renderer path.
- **Deliberate exclusions and overlap:** Binary mapping conventions belong to
  [Standard game file identities](../../../game/files/file_identities.md);
  unrelated character-specific data and font metrics are excluded by the
  observed shared-anchor result.
- **Evidence limitations:** Position evidence is bounded to the 640-pixel E2E
  captures, and register preservation is supported by one runtime capture of
  the native renderer.

## Screen evidence

The `characters/idle` E2E baseline contains 74 populated character cells. In
every cell, NA2 v2.28 places the Player 1 name exactly 20 output pixels to the
right of NUN5 and the Player 2 name exactly 20 output pixels to the left. At the
640-pixel capture width, that symmetric difference corresponds to 16 units in
the game's 512-unit logical coordinate system. This identifies a shared
mirrored anchor rather than character-specific data or font metrics.

## Renderer and X anchor

NA2 renders these names through the function at BTL file offset `0x67F20`,
runtime `0x0071BE20`, which the header-omitting Ghidra project labels
`FUN_0071bde0`. The NUN5 homolog is at file offset `0x6B0C0`, runtime
`0x00731DC0`, and Ghidra label `FUN_00731d80`. The renderer applies its X anchor
as:

```text
left:  x = base_x + local_x
right: x = base_x - local_x - rendered_width
```

The native X load is the isolated `lui/lwc1` pair at complete NA2 BTL file
range `0x67F54..0x67F5B`, clean bytes `8C00023CD84240C4`. It reads runtime
address `0x008C42D8`, BTL file offset `0x2103D8`, whose value is `90.0`. NUN5
reads runtime address `0x008DC8F8`, file offset `0x215BF8`, whose value is
`74.0`.

## Y path and live register

The native NA2 Y load is the `lui/lwc1` pair at BTL file range
`0x67F60..0x67F67`, clean bytes `8C00023CDC4240C4`. The following pair at
`0x67F68..0x67F6F`, clean bytes `820001460C00A290`, multiplies Y by the layout
scale and loads the side byte.

A runtime capture confirmed that the
native renderer loads its name destination into `v1` before the coordinate
loads and stores X and Y through that pointer afterward. Any inserted call
between those operations must therefore preserve `v1`.
