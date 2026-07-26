# Translation importer engine

This reusable engine reads the feature-owned canonical `mappings.tsv`,
validates the clean NA2 targets and the table's folded pointer inventory, and
produces one in-memory translation artifact. `source_ref` and `donor_ref`
identify the paired NA2 and NUN5 locations; `source` and `donor` retain their
decoded text together. Every executable row also declares a concrete
`display_context` and a `display_basis` beginning with `seen:`, `inferred:`,
or `character:`. The engine rejects rows without that evidence metadata and
rejects a declared `source` that differs from the clean target bytes.

The completed translation-free candidate inventory is retained at
`work/String translation/artifacts/diagnostic-rebuild/rebuild.tsv` for
worker-only mapping-ID builds:
permanent `T1`, `T2`, ... identifiers, exact clean source text and location,
capacity/mode, provisional screen context, and optional legacy `M` IDs for
lookup. It is not module content and is not profile-hashed. The explicit
diagnostic wrapper supplies its path; diagnostic builds import every row and
validate the exact clean source bytes, but ignore all donor/translation fields.

Canonical `mappings.tsv` contains the completed screenshot-confirmed rebuild
plus the explicit character-family exception. Its cumulative first two passes
contribute 752 rows, the verified 74-table Command Chart family contributes
another 1,041, the missing-row audit adds 260 policy-supported rows—53 directly
seen, 10 structurally inferred, and 197 character-family rows—the paired
Ninja Song passes add 25 displayed numeric/status/bonus fields, and the paired
ss1 Shop pass adds the confirmed Figure Items / Dioramas tutorial, for 2,079
enabled rows. T2042, T2045, and T2050 use parents in the canonical `T#`
namespace. Paired screenshots independently correct T1956 to `Off`, T1957 to
`On`, T2158 to `Warning`, T637 to `Hidden Leaf Village`, T638 to `Hidden Leaf
Gate`, T744 to `Faint Unease`, and T767 to `Silent Confidence`. Six
Difficulty-family rows are matched by meaning rather than table position.
T24 deliberately reuses the official Jump-mode help text. T30 is the sole
donorless row: its user-authored `Ultimate` replacement is externalized through
the validated pointer at `NA2_BTL@0x209CB4`. T2191–T2193 use the explicit
`empty` transform because the NA2 Ninja Song result renderer reserves only one
Japanese-counter field before its fixed equals sign and even compact Latin
counters overlap that symbol. T2194 escapes its literal percent as
`100%% Health bonus` for NA2's printf-style path. T2195–T2198 replace the
ss7–9-confirmed static Shift-JIS formula symbols with ASCII `*`, `=`, `.`, and
`%`. Other donor-backed rows
leave `replacement` blank and execute official donor text;
T1958, T2027, and T2033 retain the established Cross-confirm overrides. Normal
builds import this canonical table directly.

Canonical imports validate complete structured message families. Active
`split_br` and `join_br_parts` rows sharing a donor reference must use one
consistent full template and cover every `<br>` part exactly once. Missing,
duplicate, or out-of-range parts fail before materialization.

The official `donor` is the default executable translation. User-authored
`prefix` is prepended to the resolved text, while a nonempty user-authored
`replacement` overrides the donor before transforms are applied. The importer
normalizes fullwidth ASCII-compatible characters in resolved output while
preserving exact CP932 source guards. When an official donor uses positional
tokens such as `%1` for a clean NA2 runtime-format string, the importer
preserves the corresponding guarded `printf` token such as `%s`; captured
runtime values are never embedded into the translation.

It does not choose inline versus external placement and does not write game
payloads. Canonical rows store pointer sites as combined `reference_refs` and
generate patch-log reasons from their mapping IDs instead of carrying historical
version labels. The active mapping package and its review history live under
`na2_patcher/features/localization/translation_importer/`.

## Invokes

- `string_patcher` as a derived consumer of the validated translation artifact.
  No feature-owned string-patcher directory is required when there are no local
  string declarations.
