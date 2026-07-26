# T-ID from-scratch string-translation rebuild

This is the current execution and validation policy for rebuilding the
Localization translation table. The accepted `mappings.tsv` remains unchanged
and continues to drive normal builds while the replacement is built beside it.
Its rows, translations, and donor claims are reference material, not presumed
correct coverage.

## Parallel-table boundary

The translation importer owns three adjacent inputs:

- `mappings.tsv`: the unchanged accepted table used by normal builds;
- `rebuild.tsv`: the complete stable-`T#` candidate inventory and sole input
  used by worker-only mapping-ID builds;
- `replacement.tsv`: the encountered-only translation replacement under
  construction.

`rebuild.tsv` does not inherit executable translations. Its rows retain only
exact clean NA2 source text/location, mode/capacity, a provisional screen
context, and optional legacy `M` IDs for lookup. `donor`, `donor_ref`, `prefix`,
`replacement`, `display_basis`, transforms, pointer references, and parent
relationships begin empty. A legacy ID locates reference material; it does not
prove donor correspondence.

The 16 columns keep human-editable text first and engine details afterward:

`id`, `display_context`, `source`, `donor`, `prefix`, `replacement`,
`display_basis`, `source_ref`, `donor_ref`, `mode`, `capacity`, `transform`,
`arguments`, `reference_refs`, `parent_mapping_id`, `legacy_ids`

`display_context` is a provisional navigation hint until `display_basis` is
filled from the new evidence pass. A blank basis therefore means candidate,
not validated. `legacy_ids` is an optional comma-separated lookup field.

`replacement.tsv` uses the exact 16-column `mappings.tsv` schema:

`id`, `enabled`, `display_context`, `source`, `donor`, `prefix`,
`replacement`, `display_basis`, `source_ref`, `donor_ref`, `mode`,
`capacity`, `transform`, `arguments`, `reference_refs`, `parent_mapping_id`

Only encountered `T#` rows are admitted. The initial evidence pass copied the
exact guarded source fields from `rebuild.tsv` and recorded concrete display
metadata. The first executable pass now contains 567 enabled rows. Of those,
564 use the unique accepted-table row with the same exact `source_ref` as the
donor/transform starting point. T2042 rewrites its accepted parent ID from
`M0810` to the replacement-table ID `T2011`. Three paired-screen corrections
override incorrect reference relationships: T1956 uses `Off` at
`NUN5_SLES@0x513EF8`, T1957 uses `On` at `NUN5_SLES@0x513EFC`, and T2158 uses
`Warning` at `NUN5_SLES@0x513F38`. These relationships are the
reference-derived starting point for English runtime validation, not a claim
that the final donor audit is complete. The diagnostic inventory and normal
build behavior remain unchanged.

Rows that split one `<br>`-delimited renderer message are admitted as a
complete structural family even when only one line supplied the visible ID.
The save-progress family therefore contains T2011, T2041, and T2042, covering
all four message parts; the overwrite-confirmation family contains T2014 and
T2015. Replacement composition fails closed when any active `split_br` or
`join_br_parts` family has missing, duplicate, out-of-range, or inconsistent
parts. This prevents an externalized first line from falling through to the
next unrelated resident-payload string.

The initial inventory combines the pre-rebuild v40 reference with the accepted
table, deduplicates aliases that point to the same clean source slot, and adds
the independently found Battle HUD `MAX` source. It contains 2,173 distinct
source slots with permanent IDs `T1` through `T2173`. The table is sorted by
`display_context`, then clean source location, except that the four guarded
5-byte slots must occupy the first four rows so their complete identifiers
fit. The physical row number and identifier number are identical: the first
data row is `T1`, the second is `T2`, and so on.

Canonical initial `rebuild.tsv` SHA-256:
`EA6D79AF9A955180498E93783E0F70AB9439E34B195806991D400686D79BD71C`.

The accepted `mappings.tsv` remains 2,052 rows and SHA-256
`7601F834646C374F3E89087724726AAE78E9A87A46A5F936CC5C776C4E60C0B6`.

## Stable diagnostic IDs

- IDs are `T1`, `T2`, `T3`, ... with no zero padding.
- IDs increase by one in physical row order.
- Once assigned, an ID is never recycled or renumbered.
- A future candidate is appended as the next unused number; stable ID order
  takes precedence over re-sorting an already published table.
- Ordinary slots display the complete ID including `T`.
- Sequence fragments display `.1`, `.2`, ... suffixes.
- The four guarded 5-byte slots are the only initial ordering exception and
  use `T1` through `T4`. Every other initial row follows
  `display_context`/source order.
- A future candidate that cannot fit its next stable ID fails closed. The tool
  must not silently strip the prefix, reuse an ID, or renumber existing rows.

Synchronize or verify the inventory with:

```powershell
python scripts/research/translation/sync_rebuild.py
python scripts/research/translation/sync_rebuild.py --check
```

Synchronization preserves every existing rebuild row and stable ID, merges
only legacy-ID lookup metadata, and appends missing known candidates.

## Diagnostic mapping-ID build

Normal translation composition imports and executes only accepted
`mappings.tsv` rows and remains behaviorally unchanged. The feature integrity
hash still covers both adjacent tables. An explicit worker-only diagnostic
build imports every row from `rebuild.tsv`, validates its exact source bytes
against clean NA2, and replaces the source with its `T#` identifier. It does
not resolve donor text, apply the game-title translation policy, externalize
strings, or edit either table.

Build the diagnostic ISO with:

```powershell
& scripts/research/translation/build_mapping_ids.ps1 `
  -OutputIso 'work/String translation/build/mapping-ids.iso'
```

The output is a verified worker ISO. It never promotes or rotates Current,
Previous, or Candidate.

## Cumulative replacement build

Build the separate cumulative translation ISO with:

```powershell
& scripts/research/translation/build_replacement.ps1 `
  -OutputIso 'work/String translation/build/replacement.iso'
```

Launch that cumulative ISO beside NUN5 with:

```powershell
na replacement nun5
```

This is also a verified worker build. It imports only enabled rows from
`replacement.tsv`; it never falls back to accepted `mappings.tsv`, never
changes the complete diagnostic inventory, and never promotes or rotates
Current, Previous, or Candidate. Each completed translation pass therefore
accumulates in one independently testable image.

During this rebuild pass, the user-facing `na` pair launcher accepts the
diagnostic `rebuild` image:

```powershell
na rebuild nun5
```

`na` continues accepting any ordered combination of its registered ISO
selectors; existing selectors and zero-argument behavior remain unchanged.
`rebuild` resolves to `work/String translation/build/mapping-ids.iso` and fails
closed when that worker artifact does not exist.

The user navigates the diagnostic build and stores ordinary PCSX2 screenshots
in the emulator screenshots directory. No new savestates are required for the
ID pass. When invoked after capture, the String translation task copies only
the needed screenshots into its work directory with repository-relative
provenance.

If a visible Japanese string has no `T#`, it is a newly discovered candidate.
Add it with the next permanent ID in `rebuild.tsv`; do not renumber the
existing inventory. Add it to `replacement.tsv` only after its diagnostic ID
is visibly confirmed.

## Admission rule

A diagnostic row enters `replacement.tsv` only under one of
these bases:

1. `seen`: its diagnostic `T#` appears in a supplied PCSX2 screenshot;
2. `inferred`: an observed screen proves the containing selector or
   running-help family, while clean NA2 structure and the NUN5 reference prove
   the unshown siblings' ordering and correspondence;
3. `character`: it belongs to a structurally proven character-specific family
   whose individual runtime capture would be disproportionately expensive.

The character exception includes proven families such as character and variant
names, Ultimate Jutsu names, command-chart move names, figures, and voice
entries. Adjacency alone is insufficient.

Rows never confirmed to display remain candidates only and are not copied into
`replacement.tsv`. Diagnostic replacement is evidence
collection, not permission to translate every binary string.

Every admitted row must contain:

- `display_context`: the concrete human-readable screen and field;
- `display_basis`: stable `seen:`, `inferred:`, or `character:` provenance;
- exact clean CP932 `source` and `source_ref`;
- independently validated official `donor` and `donor_ref`, or an explicit
  user-authored `replacement`;
- any required prefix, transform, sequence structure, and pointer references.

## Donor validation

The accepted table and pre-rebuild v40 table are lookup aids only. They may
supply candidate offsets, capacities, donor leads, transforms, pointer sites,
and family patterns. They do not prove that an NA2 source slot and NUN5 donor
slot represent the same displayed field.

The Collection Music mismatch proved this boundary: legacy rows `M0361` and
`M0362` pointed inside or at the wrong NUN5 strings even though their clean NA2
source guards were valid. Therefore each admitted `T#` needs an independently
verified screen meaning and donor correspondence. Do not spot-fix those two
legacy rows; rebuild the correspondence in the new table.

Prefer exact official NUN5 text when its meaning matches the observed NA2
field. Match displayed case. Normalize fullwidth Latin letters, digits,
punctuation, and fullwidth spaces to ASCII in resolved English output while
retaining exact CP932 source guards. Preserve format placeholders, renderer
markup, and sequence structure. Apply the profile-owned
`Narutimate Accel v2.28` title policy only in the eventual executable
translation path.

`prefix` and `replacement` remain readable user-editable fields. A blank
replacement uses the independently validated donor. Inline versus external
placement remains a build-time decision; do not author shortened alternatives
or placement markers.

## Screenshot and inference workflow

Screenshots are grouped by game section and screen semantics. Each visible
`T#` is recorded against its exact displayed field. Multiple appearances of
one ID are retained as useful renderer/screen coverage but refer to one source
row.

For every diagnostic NA2 screen that has a corresponding NUN5 screen, capture
both games in the same semantic state. The captures need not be simultaneous:
the NA2 image proves which `T#` rows are displayed, while the matched NUN5
image proves the official English wording, capitalization, line structure, and
control-icon wording. If the games use genuinely different flows, capture each
flow independently and pair only screens whose meaning and action agree.

The user is not required to capture every hidden selector choice or every
running-help variant. Siblings may be inferred only when:

- a visible `T#` proves the field or ticker;
- clean NA2 structure proves the complete source table and ordering;
- NUN5 reference material proves the corresponding official table;
- every sibling has compatible renderer semantics and there is no unexplained
  gap, sentinel, identifier, placeholder, or shifted string boundary.

If those checks fail, admit only directly observed members.

PCSX2 operator overlays and the game screen underneath are separate evidence.
The save-state error overlay during a memory-card write is not game text.
NA2 and NUN5 memory-card formatting/data-creation flows are ordered
independently and paired only where prompt meaning and action agree. The
unmatched Current capture is ignored.

## Validation plan

The rebuild is accepted only after:

1. candidate integrity: contiguous stable `T#` IDs, unique source slots,
   exact clean-source validation, deterministic sorting, no copied donor text,
   and capacity-safe complete diagnostic tokens;
2. diagnostic composition: all candidates compile inline, sequence fragments
   are uniquely readable, no resident payload is introduced, and normal
   composition remains byte-for-byte unchanged;
3. ID capture: every reachable semantic screen group is exercised and visible
   IDs are entered into `replacement.tsv` with exact display context;
4. inference audit: selector/help and character-family expansions are checked
   against clean NA2 structure and NUN5 reference ordering;
5. donor audit: every admitted donor begins at a real NUN5 string boundary,
   matches the observed field, preserves placeholders/markup, and obeys case
   and fullwidth-to-ASCII policy;
6. English build: only admitted rows are composed, with deterministic inline
   or external placement and all source/pointer guards;
7. runtime acceptance: every supplied semantic screen group is captured again
   in English and reported as grouped NUN5-left/rebuilt-NA2-right comparisons.

The accepted `mappings.tsv` is not removed or changed during this process.
Replacing it is a separate final cutover after the new table has passed the
complete validation plan.
