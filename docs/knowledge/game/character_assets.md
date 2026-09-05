# Character asset tables

This document records the retail game's character-indexed CCS filename tables
and the resident code that turns those identifiers into loaded containers. It
does not own the general CCS runtime or the disc-wide file inventory.

## Research coverage

- **Assigned scope:** Base-game character asset filename tables, their numeric
  indices and archive relationships, and the resident or battle consumers that
  select, load, resolve, and release those assets.
- **Exploration depth:** The first static pass confirmed the retail boot ELF,
  reconstructed the four adjacent filename-table families, and traced the
  shared match setup and per-fighter load paths that reference them. Individual
  index mappings and downstream object consumers are not yet exhaustive.
- **Confirmed coverage:** Four fixed-width filename pools and their parallel
  pointer tables are present in the boot ELF. Three families are selected
  together for both fighters by `FUN_001E1530`; `FUN_001E80F0` feeds the two
  body families and the `3PCT` family into the resident CCS find/load/queue
  services.
- **Unresolved or untested:** Complete ID-to-filename mappings, all null slots,
  the exact roles of the `3EYE` and `3PCT` families, every table caller, object
  names consumed from the selected containers, release ordering, and the two
  historical data-range identities remain incomplete.
- **Deliberate exclusions and overlap:** General CCS parsing, lookup, and
  lifetime belong to [Resident CCS runtime](files/ccs_runtime.md); the shallow
  disc-wide family inventory belongs to [Disc and archive file
  inventory](files/disc_files.md). Character-select presentation and character
  identity semantics belong to their existing domain documents.
- **Evidence limitations:** Findings are static observations from the maintained
  read-only Ghidra analysis. No live-memory trace or gameplay experiment has
  yet established load timing, residency duration, or visible effects. Working
  identities below are descriptive, not recovered original symbols.

## Evidence and address conventions

The clean resident identity and address conversion follow
[Retail game file identities](files/file_identities.md). Addresses below are
resident addresses from the maintained read-only analysis.

## Character-indexed filename families

The boot ELF stores adjacent pools of 16-byte, NUL-terminated lowercase CCS
basenames. Each observed name has the form below, where `???` is a three-byte
character code:

| Family | String-pool runtime range | Pointer-table base | Direct resident references |
| --- | ---: | ---: | --- |
| `2???bod1.ccs` | `0x00401C48..0x004020E7` | `DAT_004020F0` / `0x004020F0` | `FUN_001E1530`, `FUN_001E80F0`, `FUN_00354640` |
| `1???bod1.ccs` | `0x00402268..0x00402707` | `DAT_00402710` / `0x00402710` | `FUN_001E1530`, `FUN_001E80F0`, `FUN_00354640`, `FUN_00358250` |
| `3???3eye.ccs` | `0x00402888..0x00402D27` | `DAT_00402D30` / `0x00402D30` | `FUN_001E1530`, `FUN_001E90F0`, `FUN_001E9180` |
| `3???3pct.ccs` | begins `0x00402EA8` | `DAT_00403350` / `0x00403350` | `FUN_001E80F0`, `FUN_001E93C0`, `FUN_00202640` |

**Observation:** The first three string pools each occupy `0x4A0` bytes and
therefore contain 74 fixed-width names. Their pointer tables begin eight bytes
after their respective pools. Index zero is null, while the first non-null
pointer is at `base + 4`; adjacent-family spacing makes each pointer table
`0x178` bytes, or 94 pointer slots indexed `0..93`. Null entries are interleaved
with populated entries, so a valid numeric character ID is not by itself proof
that every asset family exists for that ID.

**Observation:** The four pools use the same ordered character-code sequence
where their strings have been inspected. Examples include `nrt`, `ssk`, `roc`,
`gar`, and the late additions `ymt`, `sai`, and `ssw`. The leading digit and
suffix change by family while the middle three-byte code remains stable.

**Inference (high confidence):** The pointer-table index is the resident
character identifier. This follows from direct indexing by the selected fighter
values in `FUN_001E1530` and by the per-fighter character field in
`FUN_001E80F0`; the observed 94-slot `0..93` extent also matches the retail
character-ID domain. A complete row-by-row mapping still requires an explicit
table audit.

## Selection and loading consumers

### `FUN_001E1530` — publish six match asset selections

`FUN_001E1530(uint fighter_1, uint fighter_2)` clears bit `0x100` from both
arguments, multiplies each result by four, and indexes the `2BOD1`, `1BOD1`,
and `3EYE` pointer tables. It writes the resulting six filename pointers to
runtime `0x006B26F0..0x006B2704` as three family pairs.

The function then visits all three families for both fighters. For each selected
basename it:

1. calls `FUN_001AA450` (`ccs_find_container`), storing the returned container
   pointer at runtime `0x006B26D0..0x006B26E4`; and
2. packs filename bytes 1, 2, and 3 into a 24-bit character code stored at
   runtime `0x006B2710..0x006B2724`.

**Observation:** There is no null check between table lookup and reading the
selected filename. Callers must therefore supply an index populated in all
three tables after the `0x100` flag is removed. The container lookup itself may
return null; that result is retained in the six-pointer publication block.

### `FUN_001E80F0` — per-fighter conditional load/queue path

For player slots 1 and 2, `FUN_001E80F0` reads the fighter character ID from a
`0x28`-byte selection record and conditionally builds resource paths according
to a bit mask. Mask bit `0x01` selects `DAT_00402710` (`1BOD1`), bit `0x02`
selects `DAT_004020F0` (`2BOD1`), and bit `0x10` selects
`DAT_00403350` (`3PCT`). Each constructed path is checked through
`FUN_001AA450`; the function then either calls blocking
`FUN_00116DE0` (`ccs_load_if_absent`) or queues it through `FUN_001CF9E0`
(`ccs_enqueue_unique_load`), depending on its queue-mode argument and current
residency.

The function stores newly returned load/container handles in per-player fields
separate from the path buffers. Other mask bits construct support and shared
resource paths through different helpers rather than through these four static
character tables.

## Unresolved historical data ranges

The two historical ELF-file leads map as follows:

| File offset | Runtime address | Current observation |
| ---: | ---: | --- |
| `0x00494EFC` | `0x00594DFC` | Begins a repeated binary record sequence containing floats, halfwords, bit fields, and pointers to runtime `0x006031F0`; MCP reports no exact xref to this start. |
| `0x0049AF8C` | `0x0059AE8C` | Begins a closely matching record sequence whose early records contain character value `0x005D`; MCP reports no exact xref to this start. |

The former “Sai-lion” and “Sasuke-Chidori” labels are not established by the
visible bytes or exact-address xrefs. They remain hypotheses pending discovery
of the containing table boundaries, indexing function, and runtime consumer.
