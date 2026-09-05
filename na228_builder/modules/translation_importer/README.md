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

Canonical imports validate complete structured message families. Active
`split_br` and `join_br_parts` rows sharing a donor reference must use one
consistent full template and cover every `<br>` part exactly once. Missing,
duplicate, or out-of-range parts fail before materialization.

The official `donor` is the default executable translation. User-authored
`prefix` is prepended to the resolved text, while `replacement` is reserved for
a direct user edit that overrides the donor before transforms are applied.
Agents follow the
[modding policy](../../../docs/policies/modding.md#builder-binary-and-donor-changes).
The importer normalizes fullwidth ASCII-compatible characters in resolved
output while preserving exact CP932 source guards. When an official donor uses
positional tokens such as `%1` for a clean NA2 runtime-format string, the importer
preserves the corresponding guarded `printf` token such as `%s`; captured
runtime values are never embedded into the translation.

It does not choose inline versus external placement and does not write game
payloads. Canonical rows store pointer sites as combined `reference_refs` and
generate patch-log reasons from their mapping IDs instead of carrying historical
version labels. The active mapping package and its review history live under
`@builder/patches/localization/strings/`.

## Invokes

- `string_patcher` as a derived consumer of the validated translation artifact.
  It has no feature-owned directory or file-backed interface.
