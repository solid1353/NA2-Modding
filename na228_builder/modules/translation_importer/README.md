# Translation importer engine

This reusable engine reads the feature-owned canonical `mappings.tsv`,
validates the clean NA2 targets and the table's folded pointer inventory, and
produces one in-memory translation artifact. `source_ref` and `donor_ref`
identify the paired NA2 and NUN5 locations; `source` and `donor` retain their
decoded text together. Every executable row also declares a concrete
`display_context` and one or more `display_basis` entries beginning with
`seen:`, `e2e:`, `inferred:`, or `character:`. Multiple entries are separated
by `|`. `e2e:<suite-name>` records each exact maintained suite that exercised a
row, including every proven suite for shared strings. The engine rejects rows
without that evidence metadata and rejects a declared `source` that differs
from the clean target bytes.

Canonical `mappings.tsv` contains the completed screenshot-confirmed rebuild
plus the explicit character-family exception. Its cumulative first two passes
contribute 751 rows, the verified 74-table Command Chart family contributes
another 1,041, the missing-row audit adds 234 policy-supported rows—53 directly
seen, 10 structurally inferred, and 171 character-family rows—the paired
Ninja Song passes add 25 displayed numeric/status/bonus fields. The paired
ss7 Movie pass adds the locked-title placeholder.
T2042, T2045, and T2050 use parents in the canonical `T#`
namespace. Paired screenshots independently correct T1956 to `Off`, T1957 to
`On`, T2158 to `Warning`, T637 to `Hidden Leaf Village`, T638 to `Hidden Leaf
Gate`, T744 to `Faint Unease`, T767 to `Silent Confidence`, and T1920 to the
exact `Charge Chakra` donor at `NUN5_TEXTENG@0xFB8`; the separate T1926
Command Chart row retains `Charge` at `NUN5_SLES@0x513EB0`. Six
Difficulty-family rows are matched by meaning rather than table position.
T24 deliberately reuses the official Jump-mode help text. T30 imports the exact
`Ultimate` donor at `NUN5_TEXTENG@0xF208` and externalizes it through the
validated pointer at `NA2_BTL@0x209CB4`. T2191–T2193 use the explicit
`empty` transform because the NA2 Ninja Song result renderer reserves only one
Japanese-counter field before its fixed equals sign and even compact Latin
counters overlap that symbol. T2194 uses `escape_literal_percent` to materialize
`100%% Health bonus` from the exact `100% Health bonus` donor for NA2's
printf-style path. T2195–T2198 use `normalize_formula_symbol` to materialize the
ss7–9-confirmed ASCII `*`, `=`, `.`, and `%` formula family while retaining the
raw NUN5 symbols. T2200 replaces the ss7-confirmed six-fullwidth-question-mark Movie lock
placeholder with the official three-ASCII-question-mark form. The paired
Battle/Practice quit-confirmation states establish the native assembly as
T63/T64 mode head + T66 connective + one short destination slot + T67
terminator. T63 and T64 therefore resolve only through donor placeholder `%1`;
T2201 and T2202 translate the previously missing short destination slots from
the official NUN5 `Character Select` and `Game Mode Select` strings.
T2203/T2204 convert the remade-ss1 Special Controls modal's two fullwidth
Shift-JIS slots to the official NUN5 ASCII `ON`/`OFF` strings. Other
donor-backed rows execute official donor text directly. NUN5's paired `@...@`
quotation convention and semantic `<iconOK>` confirm token are normalized
centrally to ASCII quotation marks and NA2's `<iconCROSS>` token. Every current
canonical row leaves `replacement` blank. Normal builds import this table
directly.

Canonical imports validate complete structured message families. Active
`split_br` and `join_br_parts` rows sharing a donor reference must use one
consistent full template and cover every `<br>` part exactly once. Missing,
duplicate, or out-of-range parts fail before materialization.

The official `donor` is the default executable translation. User-authored
`prefix` is prepended to the resolved text, while `replacement` is reserved for
a direct user edit that overrides the donor before transforms are applied.
Agents follow the
[modding policy](../../../docs/policies/modding.md#binary-and-donor-changes).
The importer normalizes fullwidth ASCII-compatible characters in resolved
output while preserving exact CP932 source guards. When an official donor uses
positional tokens such as `%1` for a clean NA2 runtime-format string, the importer
preserves the corresponding guarded `printf` token such as `%s`; captured
runtime values are never embedded into the translation.

It does not choose inline versus external placement and does not write game
payloads. Canonical rows store pointer sites as combined `reference_refs` and
generate patch-log reasons from their mapping IDs instead of carrying historical
version labels. The active mapping package and its review history live under
`@builder/localization/translation_importer/`.

## Invokes

- `string_patcher` as a derived consumer of the validated translation artifact.
  No feature-owned string-patcher directory is required when there are no local
  string declarations.
