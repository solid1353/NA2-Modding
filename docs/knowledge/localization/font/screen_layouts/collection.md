# Collection Font layouts

## Research coverage

- **Assigned scope:** compare retail NA2 (`SLPS-25837`) and NUN5 Collection
  lists, plaques, and titles.
- **Exploration depth:** the relevant native callers, records, and coordinates
  were inspected.
- **Confirmed coverage:** the documented owners and cross-game geometry
  differences are established.
- **Unresolved or untested:** callers and states not explicitly covered below.
- **Deliberate exclusions and overlap:** glyph metrics belong to
  [Renderer metrics](../renderer_metrics.md); Collection graphics and prompts
  belong to [Collection UI draw-path analysis](../../ui/collection.md);
  Collection string ownership belongs to
  [NA2 and NUN5 text correspondence](../../translation_importer.md).
- **Evidence limitations:** bounded states do not cover every string or
  animation phase.

## Collection fixed-cadence list wrapping

NUN5 stores the active box width and height in each list structure at
`+0x14/+0x18`. The states prove a 192-by-32 box for Movie titles,
a 152-by-32 box for the move list, and a 192-by-32 box for the
relationship list. Every family uses native X, native Y minus 10, two lines,
and a 16-unit line interval. The outer list retains fixed row cadence; wrapped
titles occupy two lines inside their existing row rather than increasing later
row positions. Exact visible breaks include:

- `Sealing Jutsu: Nine` / `Phantom Dragons`;
- `People of Endless` / `Darkness`;
- `Ninja Art: Beast` / `Scroll Replicas`;
- `Fourth Awakened` / `Mode`;
- `Shadow Clone` / `Jutsu`;
- `Unchanging` / `Relationship`.

## Structural Collection-family completion

Collection uses these relevant list families:

- ordinary characters: Figure, Ultimate Jutsu, and character-specific Music;
- legacy characters: Ultimate Jutsu only;
- Diorama;
- Movie;
- global Music;
- the Characters index where applicable.

Raw NUN5 ETC records are not byte-compatible with NA2: homologous list records
assign different meanings to fields at `+0x14/+0x18` and shift live resource
fields. Only their classification and layout semantics correspond.

## Collection Characters selected-name boxed positioning

NUN5 first remaps the selected record ID before resolving its localized string.
The live record stores ID `24`; NUN5's remap row at
`0x006ED190` maps it to localized row `62`. English row `62` stores
`Granny Chiyo` as its primary pointer and `Granny Chiyo `, with a terminal
space, as the pointer returned to this caller. In NA2, ETC pointer field
`0x25A68` selects the shared Japanese slot at `0x251E0`; the other references
to that slot at `0x281DC`, `0x2AADC`, and `0x2D818` belong to different record
families.

NUN5 `TEXTENG.BIN` offset `0x508` is the primary string and offset `0x518` is
the secondary Collection string with the terminal space. The isolated ETC
pointer field establishes that this distinction belongs to the Characters
selected-name call rather than to every reference to the shared string.

## Collection Figures Diorama boxed titles

The 12 Diorama captures use NA2 exported draw function
`FUN_006BDD70` and NUN5 homolog `FUN_006D0F90`. NA2's title call at ETC file
offset `0xA31C` passes the record origin plus half-extents to the point-centered
`FUN_00379240`. NUN5 instead passes the record origin, Y plus `4.0`, doubled
half-extents, a two-line limit, and the selected title to boxed renderer
`FUN_0038A4F0`. NUN5 boot-ELF data at `gp-0x4470` and `gp-0x446C`
contains half-width `95.0` and half-height `16.0`; the call doubles them before
entering the wrapper. The exact NUN5 title box is therefore `190` by `32`
units, not `200` by `40`.
