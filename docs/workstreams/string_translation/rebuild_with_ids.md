# T-ID from-scratch string-translation rebuild

This is the current execution and validation policy for the rebuilt
Localization translation table. The screenshot-confirmed T-ID table has been
promoted to canonical `mappings.tsv` and now drives normal builds. Legacy
translations and donor claims remain reference material, not presumed correct
coverage.

## Canonical and retained-work boundary

The translation importer owns one canonical input:

- `mappings.tsv`: the canonical screenshot-confirmed translation table used by
  normal builds.

The completed diagnostic inventory is retained outside the feature at
`work/String translation/artifacts/diagnostic-rebuild/rebuild.tsv`. It does
not participate in profile hashing or normal composition. Its rows retain only
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

`mappings.tsv` uses this 16-column schema:

`id`, `enabled`, `display_context`, `source`, `donor`, `prefix`,
`replacement`, `display_basis`, `source_ref`, `donor_ref`, `mode`,
`capacity`, `transform`, `arguments`, `reference_refs`, `parent_mapping_id`

Only encountered `T#` rows and structurally proven character-family rows were
admitted. The first screenshot pass contributed 567 enabled rows and the
second contributed 185. The character-specific exception then admitted the
remaining 1,041 Command Chart move-name rows from the verified 74-table
command-record family. A subsequent missing-row audit admitted another 260
policy-supported rows: 53 directly seen rows, 10 structurally inferred
siblings, and 197 character-family rows. Canonical mappings therefore initially
contained 2,053 unique enabled rows. Exact guarded source fields came from the retained
diagnostic inventory, while concrete display metadata records whether each row was
seen directly, inferred from a captured selector/help family, or admitted
under the character-specific exception. Subsequent paired acceptance added 25
Ninja Song fields, the Figure Items / Dioramas Shop tutorial, and the locked
Movie-title placeholder, bringing the current table to 2,080 enabled rows.
The first-pass corpus contains 172
hash-verified paired captures; the second contains 93.

Of the initial 2,053 rows, 2,040 began from the unique legacy row with the same exact
`source_ref`. T2042 uses canonical parent `T2011`; T2045 and T2050 likewise use
canonical parents `T2043` and `T2048`.
Three paired-screen corrections override incorrect reference relationships:
T1956 uses `Off` at `NUN5_SLES@0x513EF8`, T1957 uses `On` at
`NUN5_SLES@0x513EFC`, and T2158 uses `Warning` at
`NUN5_SLES@0x513F38`.

The complete Command Chart move-name family contains 1,055 rows: the 14
previously captured Naruto rows plus 1,041 additional rows that include
Naruto's missing moves and the rest of the roster. Every move retains its
complete official donor and a blank user `replacement`. Of the complete
family, 1,049 fit inline and six use their existing guarded pointer references
for build-time external placement; no move is shortened.

Six Difficulty-family rows are matched by meaning rather than row position:
T27 `Simple`, T1983 `Easy`, T28 `Normal`, T1984 `Hard`, and T29 `Insane` use
the exact five-string NUN5 block at `0x514218` through `0x514238`; T50 uses
`Difficulty` at `NUN5_TEXTENG@0xF880`. T50's full label is linked through the
exact pointer at `NA2_BTL@0x20A264`. NA2's extra `Ultimate` difficulty has no
NUN5 counterpart.

T24 reuses the official Jump-mode help text. Paired screens correct T637 to
`Hidden Leaf Village`, T638 to `Hidden Leaf Gate`, T744 to `Faint Unease`, and
T767 to `Silent Confidence`. The paired Practice ss5 comparison corrects T1920
to the complete displayed title `Charge Chakra`; because its retained official
donor is only `Charge`, the complete title is stored as an override. T30 is the
sole row without a trustworthy NUN5 donor: its user-authored `Ultimate`
replacement is externalized through
`NA2_BTL@0x209CB4`. Donor-backed rows otherwise leave `replacement` blank and
execute independently validated official donor text. T1958, T2027, and T2033
retain the established Cross-confirm overrides.

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

Retained diagnostic `rebuild.tsv` SHA-256:
`EA6D79AF9A955180498E93783E0F70AB9439E34B195806991D400686D79BD71C`.

Canonical `mappings.tsv` contains 2,080 rows and SHA-256
`607622129FAD96E919E6CC7542F2FCEA69006D45A203A1867473AA1EBDF68073`.

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

Normal translation composition imports and executes only canonical
`mappings.tsv` rows. The feature integrity hash covers that table, not the
retained diagnostic inventory. An explicit worker-only diagnostic build is
still available: its wrapper passes the task-local `rebuild.tsv` path
explicitly, validates every exact source byte against clean NA2, and replaces
the source with its `T#` identifier. It does not resolve donor text, apply the
game-title translation policy, externalize strings, or edit either table.

Build the diagnostic ISO with:

```powershell
& scripts/research/translation/build_mapping_ids.ps1 `
  -OutputIso 'work/String translation/build/mapping-ids.iso'
```

The output is a verified worker ISO. It never promotes or rotates Current,
Previous, or Candidate.

## Canonical English build

Normal profile builds import only enabled rows from canonical `mappings.tsv`.
There is no separate replacement table or replacement-only display mode.
The task-local `rebuild.tsv` remains independent and is read only when the
explicit mapping-ID worker wrapper supplies its path.

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
Add it with the next permanent ID in the retained task-local `rebuild.tsv`; do
not renumber the existing inventory. Add it to `mappings.tsv` only after its
diagnostic ID is visibly confirmed.

## Admission rule

A diagnostic row enters canonical `mappings.tsv` only under one of
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
`mappings.tsv`. Diagnostic display is evidence collection, not permission to
translate every binary string.

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
or placement markers. T30 demonstrates this rule: full `Ultimate` is linked
externally because it does not fit the original slot.

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
   IDs are entered into `mappings.tsv` with exact display context;
4. inference audit: selector/help and character-family expansions are checked
   against clean NA2 structure and NUN5 reference ordering;
5. donor audit: every admitted donor begins at a real NUN5 string boundary,
   matches the observed field, preserves placeholders/markup, and obeys case
   and fullwidth-to-ASCII policy;
6. English build: only admitted rows are composed, with deterministic inline
   or external placement and all source/pointer guards;
7. runtime acceptance: every supplied semantic screen group is captured again
   in English and reported as grouped NUN5-left/rebuilt-NA2-right comparisons.

The canonical cutover is complete. Remaining work is English runtime acceptance
and evidence-backed correction of any displayed mismatch.
