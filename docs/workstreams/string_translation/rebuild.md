# From-scratch string-translation rebuild

This is the approved execution and validation policy for rebuilding the
Localization translation table. The existing table is historical reference
material, not presumed executable coverage.

## Selection rule

The new canonical table begins from no executable mappings. A row is admitted
only under one of these bases:

1. `seen`: its diagnostic mapping identifier appears in a supplied PCSX2
   screenshot;
2. `inferred`: an observed screen proves the containing selector or running-help
   table, and the pre-rebuild NA2/NUN5 table retained in Git history proves the
   unshown siblings' ordering and correspondence;
3. `character`: it belongs to a structurally proven character-specific family
   for which individual runtime encounters would be disproportionately
   expensive.

The character exception includes proven families such as character and variant
names, Ultimate Jutsu names, command-chart move names, figures, and voice
entries. Adjacency to one of those families is not sufficient: unrelated
`menus_data` rows require their own display basis.

Every executable row must contain:

- `display_context`: a concise human-readable location, for example
  `Practice Settings > Damage label`;
- `display_basis`: a stable `seen:`, `inferred:`, or `character:` reference.

The importer rejects missing display metadata.
Rows with uncertain display purpose are absent from the executable table and
their clean Japanese bytes remain untouched.

## Reference boundary

The pre-rebuild v40 table is retained only in Git at commit
`14083adac9c24c533a33876a23596c6a92d301ec`, path
`na2_patcher/features/localization/translation_importer/mappings.tsv`. It has
2,177 rows, size 315,221 bytes, and SHA-256
`60DB92F792502AD308B8D821BC4B963B060A113044A420DBAF288A6AB4A940A4`.
It may supply candidate offsets, capacities, official donor references,
transforms, pointer sites, and family patterns. None of those rows is copied
into the fresh table automatically.

The supplied savestate library remains read-only. Its existing NUN5 and clean
NA2 screenshots establish screen meaning and the visible Japanese/official
English relationship. The unmatched Current capture is not evidence for this
rebuild.

## Diagnostic mapping-ID build

Normal builds continue resolving the canonical donor/override text. An explicit
worker-only diagnostic mode instead resolves every active mapping to its stable
mapping identifier before inline/external placement:

- ordinary slots display their full ID, such as `M0842`;
- the few four-character slots display the unambiguous numeric part, such as
  `0562` for `M0562`;
- sequence fragments display a one-based suffix, such as `M0813.1`;
- canonical mappings, profile pins, and normal build output remain unchanged.

Build the diagnostic ISO with:

```powershell
& scripts/research/translation/build_mapping_ids.ps1 `
  -OutputIso 'work/String translation/build/mapping-ids.iso'
```

The output is a verified worker ISO. It never promotes or rotates Current,
Previous, or Candidate.

The user navigates the diagnostic build and stores ordinary PCSX2 screenshots
in the emulator's screenshots directory. No new savestates are required. The
String translation task copies selected screenshots into
`@work/String translation/inputs/screenshots/` with repository-relative
provenance before relying on them.

## Coverage reconstruction

Visible identifiers are transcribed into a coverage ledger grouped first by
game section and then by screen semantics. Multiple occurrences of one ID are
retained as useful renderer/screen coverage but create only one mapping row.

Hidden selector values and running help are not captured individually. They are
admitted only when:

- an observed identifier proves the visible field or ticker;
- clean NA2 structure proves the complete source table and ordering;
- the archived NUN5 reference proves the corresponding official donor table;
- every sibling has compatible renderer semantics and no unexplained gap,
  sentinel, identifier, or placeholder.

If any of those checks fails, only directly observed members are admitted.

## Text policy

- Preserve exact clean CP932 source text and bytes as binary guards.
- Prefer the exact official NUN5 donor when its meaning matches the NA2 screen.
- Match displayed case.
- Normalize fullwidth Latin letters, digits, punctuation, and the fullwidth
  space to ASCII in resolved English output, not in source guards.
- Preserve required format placeholders, renderer markup, and sequence
  structure.
- Apply the profile-owned `Narutimate Accel v2.28` title policy after import.
- Keep `prefix` and `replacement` as readable user-editable fields; a blank
  replacement uses the donor.
- Derive inline versus external placement at build time. Do not author shortened
  alternatives or placement markers.

## Special evidence

PCSX2's save-state error overlay during a memory-card write is operator UI, not
game text. The saving screen underneath it is a separate game screen and is
validated from ordinary screenshots because that state cannot safely be saved.

NUN5 and NA2 memory-card formatting/data-creation flows do not correspond
screen-for-screen. Each flow is ordered independently, then paired only where
the prompt's meaning and action agree. Debug or placeholder donor text such as
`TestSaveLoadMsgEng5` is not imported as user-facing translation.

## Implemented v43 table

The first diagnostic pass admitted 2,049 executable rows:

- 2,048 evidence-supported rows retained from archived v40;
- one new `M2247` row for the confirmed Battle HUD `MAX` label;
- 124 previously active v40 rows omitted because they have no confirmed display
  location.

The final-acceptance slot-2 pair then proved one of those omissions to be
visible: the Mode Select return confirmation uses `M0549` at
`NA2_SLPS@0x4B1E00`. Version 42 restores only that row with the exact
`NUN5_TEXTENG@0x1C90` donor, `Return to Title Screen?`. It remains distinct
from the lowercase Save/Load `M0804` prompt and the shorter Character Select
`M0557` source.

The paired Shop captures at checkpoints 046 through 049 then exposed one
regional-control mismatch in the admitted table. `M0537` retains its exact
source and official donor, but version 43 places
`Select an item and press <iconCROSS> to buy.` in the user-editable
`replacement` field. This matches the displayed NUN5 Cross glyph and the
runtime-proven NA2 Shop control map where Cross accepts. The unobserved
alternate Shop row `M0530` and the unclassified standalone ELF Circle token
remain untouched.

Every row has a concrete display location and one `seen:`, `inferred:`, or
`character:` basis. There are no disabled, unresolved, shortened, prefixed, or
arbitrary override rows. `M0537` is the single evidence-backed user override.
The table has 2,046 slots and four sequences.

The character-family audit corrected plain Kankuro and the shifted
`Provocation` / `Contrasting Pair` voice titles. The unmatched `通告` voice
title is absent rather than guessed. Exact source validation passes for every
row against clean NA2, and exact donor validation passes for every row against
the referenced NUN5 bytes after fullwidth-ASCII normalization.

Canonical v43 `mappings.tsv` SHA-256:
`46241AC03690FE253E33E4F20B9AB7BA81A5268D738681782D830119F608A2D4`.

## Validation

Static validation must prove:

- exact mapping schema and nonempty display metadata for every executable row;
- unique IDs and guarded source/donor/reference locations;
- no unclassified mappings or placeholder-to-identifier replacements;
- exact format-placeholder and sequence preservation;
- case policy and absence of fullwidth ASCII in resolved English;
- CP1252/CP932 encodability, slot capacity, deterministic external placement,
  and guarded pointer coverage;
- deterministic profile composition with normal and mapping-ID display modes;
- normal-mode parity when diagnostic display is not requested.

Static validation completed on 2026-07-24:

- all 2,050 canonical rows passed exact clean-source and official-donor checks;
- all 2,056 resolved slot/sequence fragments contain no fullwidth
  ASCII-compatible output;
- normal current-profile composition produced 2,287 binary edits and the
  1,776-byte `PRG/228.BIN` documented above;
- mapping-ID composition produced 2,060 inline binary edits and no resident
  payload, because every diagnostic identifier fits its guarded slot;
- the full repository test suite passed 148/148.

Runtime acceptance uses two passes:

1. complete: the diagnostic ISO identified which source rows render on the
   supplied screens;
2. pending final acceptance: the rebuilt English ISO is captured again for
   every supplied semantic screen group.

Final reports use readable grouped grids with NUN5 on the left and rebuilt
Current on the right. Selector/help siblings and character families receive
exhaustive static table validation plus representative renderer coverage; they
do not require one screenshot per value.
