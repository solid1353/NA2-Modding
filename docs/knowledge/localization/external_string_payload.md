# External localization payloads

Research on the official NUN5 localization files and the native NA2 loader and
memory layout.

## Research coverage

- **Assigned scope:** determine the structure and loading behavior of official
  external localization payloads and whether NA2 exposes a compatible native
  loading boundary.
- **Exploration depth:** the complete donor files, their MWO3 headers, aligned
  pointer words, loader call paths, destination tables, and structural memory
  boundaries were inspected.
- **Confirmed coverage:** NUN5 localization files are indexed MWO3 data images,
  and NA2's generic PRG loader can load an MWO3 image into a table-selected
  destination.
- **Unresolved or untested:** the remaining 80 in-range NUN5 words and the
  behavior of malformed or missing files beyond the observed retry path.
- **Deliberate exclusions and overlap:** NA228 string selection belongs to
  [Compact external strings](../../features/localization/external_strings.md);
  shared payload placement belongs to
  [Runtime injection](../../features/runtime_injection/implementation.md).
- **Evidence limitations:** donor precedent establishes compatible mechanisms,
  not direct ABI compatibility with NA2 or acceptance of a particular mod
  payload.

## NUN5 `TEXTENG.BIN`

The official NUN5 donor is not a flat string pool. It mixes zero-terminated
English strings with absolute in-image pointer tables that index whole strings
and, in some cases, interior fragments. The strings cover character and move
names, menus, prompts, battle and Practice help, conditions, collection text,
story prose, and Save/Load messages. They use an ASCII-compatible Western
single-byte encoding with markup such as `<br>` and `<color...>`.

The preserved Ghidra import identifies zero functions and zero instructions.
An aligned scan of the clean `0x30D00`-byte donor found 3,697 words in its own
loaded-address range. Of those, 3,617 point exactly to 2,990 distinct printable,
zero-terminated string starts. The remaining 80 words were not classified.
This establishes structured localization data with extensive internal indexing,
not executable code or merely concatenated text.

## Evidence

The clean NA2 and NUN5 inputs are identified in
[Standard game file identities](../game/files/file_identities.md).

The investigation used the preserved Ghidra projects and exports plus aligned
little-endian pointer scans and direct binary inspection. `ADV.BIN` was not
needed for these findings.

## NUN5 donor behavior

NUN5 ships `TEXTENG.BIN`, `TEXTFRN.BIN`, `TEXTGER.BIN`, `TEXTITA.BIN`, and
`TEXTSPA.BIN`. Its boot ELF selects a language, loads the corresponding file at
`0x008F3D00`, and exposes language-indexed string accessors.

- `FUN_003d3e50` maps the system language and begins localization loading.
- `FUN_003d3ef0` loads the selected `TEXT*.BIN` at `0x008F3D00`.
- `FUN_003d4000`, `FUN_003d4040`, and `FUN_003d4110` set, reload, and read the
  language.
- `FUN_001e6b20` invokes localization loading during construction.
- `FUN_00100300` is the MWO3 loader.

The filename block begins at runtime `0x005BB228`, its pointer table at
`0x005BB280`, and its path prefix at `0x005BB298`.

## MWO3 address convention

MWO3 files begin with a `MWo3` header. Raw file offset maps to
`load_base + file_offset`; the first `0x40` bytes are the in-memory header. Some
Ghidra imports instead map file offset `0x40` to the displayed load base, making
their displayed code labels `0x40` lower than the raw-memory formula.

## Native NA2 loader and memory boundary

`FUN_001be7f0(slot, filename)` reads the destination from the table at runtime
`0x006029C0`, constructs `cdrom0:\\PRG\\<filename>`, reads the file, and passes
the loaded MWO3 image to `FUN_00100270` for cache maintenance, BSS clearing, and
constructor processing. The clean destination table has slot 0 = `0x00100000`,
slot 1 = `0x006B3F00`, and zeroes thereafter.

The loader has no observed slot bounds check and retries failed reads. A
missing, misnamed, or truncated external file may therefore hang rather than
fail cleanly.

The clean ELF describes the resident image through `0x006B3F00`, mutually
exclusive overlays ending no later than `0x008DD080`, and a final zero-size
marker at `0x008DD080`. Four instruction pairs construct that boundary:

| ELF file offsets | Runtime purpose |
| --- | --- |
| `0x00000220`, `0x00000228` | startup boundary reference at `0x00100120` |
| `0x000002D0`, `0x000002D8` | startup boundary reference at `0x001001D0` |
| `0x0001885C`, `0x00018860` | heap-size calculation in `FUN_00118730` |
| `0x004D6908`, `0x004D690C` | upper-memory marker write near `0x005D6800` |

The same boundary also appears in program-header words at `0xBC` and `0xC0`, a
literal pointer at `0x2F79F4`, and a section-header address at `0x50763C`.
Any extension must account for all of these materializations rather than only
the program header.
