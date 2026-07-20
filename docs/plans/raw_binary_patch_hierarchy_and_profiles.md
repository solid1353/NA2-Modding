# Binary-patcher patch hierarchy and profile-driven workflows

## Objective

The active build hierarchy is:

```text
Profile
└── Feature
    └── Module selection
        ├── native/all selection for non-binary-patcher modules
        └── binary-patcher module / patch set
            └── selected group or patch
                └── patch
                    └── edit
```

A binary-patcher module instance and its patch set are the same compositional node
in this hierarchy. `module_id` and the package manifest's `package_id` remain
technically distinct so a profile can pin and reuse package content without
making its build-level identity part of the package format.

## Profile schema v2

Profiles use two normalized tables in addition to their manifest and roots:

- `features.tsv` enables reusable feature packages and pins each package's
  declarative input hash.
- `modules.tsv` declares ordered module instances, their engine type, input,
  hash pin, and reason.

Feature selections do not live in profiles. Every reusable package under
`na2_patcher/features/<feature_id>/` owns a `manifest.tsv` and ordered
`selections.tsv`. The consuming profile supplies the stable module instances
named by those selections and independently pins their executable inputs.

For binary-patcher modules, a selection row is conceptually
`(module_id, selection_kind, selection_id)`, where `selection_kind` may be
`group` or `patch`. A feature may contain both kinds, repeated selections are
preserved, and overlapping selections are not deduplicated. Every selection
therefore keeps its own provenance in plans and logs.

Current feature packages deliberately use only group selections for binary-patcher
modules. Direct patch selection is supported by the feature schema and engine
for future isolated features and tests, but no current feature package selects
a patch ID.

Non-binary-patcher modules retain their existing semantics: `all` selects the complete
module and `native` carries the module's native selector, such as a translation
target. They do not need group catalogs merely to participate in features.

An enabled feature must select at least one module input. A disabled feature may
be empty, which permits reserved features such as Rendering without inventing
placeholder content.

## Binary-patcher schema v2

Every binary-patcher package has exactly five canonical control tables:

- `manifest.tsv`
- `targets.tsv`
- `groups.tsv`
- `patches.tsv`
- `edits.tsv`

`groups.tsv` declares the package's selectable group catalog. Every patch must
name one declared group, and every edit must name one declared patch. Empty
packages are valid, but a declared group must contain at least one patch and a
declared patch must contain at least one edit.

Schema v1 is removed from the live engine. `relations.tsv` is also removed:
patch dependencies and declared patch conflicts are not part of the current
model. Edits that must always apply together belong to one atomic patch. A
future schema can add explicit relations when a concrete need establishes the
right semantics.

## Selection and conflict validation

Group selection expands to all patches in deterministic package order. Patch
selection expands only the named patch. Expansion preserves every selection
instance, including repeated and overlapping group/patch selections.

After all active selections are materialized as concrete ordered edits, the
compositor simulates them in memory before creating the `.building` ISO:

- if the current bytes match the edit guard, apply the replacement;
- if the replacement is already present, record `already_satisfied`;
- if an edit's guard matches bytes written by an earlier edit, apply it as a
  valid ordered chain;
- otherwise fail as a real selected-edit conflict.

This validates the actual composed result instead of trying to infer conflicts
from overlapping ranges or selection metadata. Overlap itself is legal.

## Current canonical groups

The feature packages enabled by the current profile select these binary-patcher
groups:

- Font: `glyph_data`, `auto_fit`, `alignment`
- Menu input: `battle_ui`, `front_end`, `etc_ui`, `battle_results`
- QoL: `startup`, `practice`, `mode_select`
- Battle logic: `combat_rules`
- String patcher (delegated to `binary_patcher`): `identity`
- UI translation code: `battle_ui`, `front_end`, `shop`

Testing remains a disabled feature with its `substitution` group available for
controlled use. Rendering is a disabled, completely empty reserved package. It
contains no aspect-ratio placeholder and no font content; Font remains a
separate feature and package. Retired `font_m01` and `font_elf_history` active
package directories are not recreated, while their useful historical evidence
remains under `docs/knowledge/font/history/`.

QoL's former bundle rows are split into independent atomic patches while
preserving their exact edits:

- Startup: Skip CC2 intro; Skip opening
- Practice: Voice off; Support off; Command display off; Simple display off
- Mode select: Remove Adventure

## Reproducibility and logs

The profile pins every enabled feature package and active module input by
deterministic hash. Feature hashes cover only `manifest.tsv` and
`selections.tsv`; binary-patcher hashes cover the five canonical control tables
plus referenced blobs, while string-patcher hashes cover only its semantic
`strings.tsv`. Adjacent documentation and engine code are excluded.

Profile-run logs record enabled features, every feature-selection occurrence,
module identity and hash, selected group/patch provenance, expanded patch/edit
instances, and each edit outcome. The normal bare `na2` workflow continues to
load `na2_patcher/profiles/current/`; this migration adds no public profile
selection flag.

## Migration proof

Before migration, a deterministic v1 baseline captured six enabled binary-patcher modules,
92 selected patches, and 256 selected edits. After migration, the group-only
current feature packages expand to 95 patch instances and the same 256 edit
instances; the patch-instance count increases only because the two QoL bundles
became seven independent patches. Exact target paths, offsets, guards,
replacement bytes, lengths, and ordering remain equivalent.

Validation is intentionally file- and memory-backed only for this task. It
loads every package, loads the complete current profile, composes all enabled
modules in memory, and runs the Python suite. It does not build an ISO or launch
PCSX2.

## Acceptance criteria

- Profile schema v2 enables and hash-pins reusable feature packages without
  storing feature selections in the profile.
- Binary-patcher schema v2 represents package -> group -> patch -> edit.
- Current feature packages use binary-patcher group selections only.
- Direct binary-patcher patch selection remains supported for future profiles/tests.
- Overlapping and repeated selections retain provenance and are validated by
  deterministic ordered edit simulation rather than deduplication.
- `relations.tsv` and live schema v1 support are removed.
- Rendering is empty and Font is separate.
- Existing current-profile binary edit bytes remain unchanged.
- No source, release artifact, ISO, or binary is modified manually.
