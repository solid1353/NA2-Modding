# Binary-patcher patch hierarchy and profile-driven workflows

## Objective

The active build hierarchy is:

```text
Profile
└── Feature
    └── Module input
        └── patch
            └── edit
```

A module directory and its engine invocation are the same compositional node.
Feature and module identities come from their directories; profiles do not
repeat them.

## Manifest-free profile format

Profiles contain exactly three tables:

- `features.tsv` lists enabled feature IDs in composition order and pins each
  feature's aggregate canonical-input hash.
- `roots.tsv` binds logical clean/donor source IDs.
- `identity.json` declares structured image, memory-card, and game-title policy
  for the final output identity.

The profile ID is its directory name. There is no profile manifest, module
table, enabled flag, module path, module ID, module order, separate module pin,
or prose reason.

Every reusable package under `@features/<feature_id>/` owns one root
`README.md` and module-named subdirectories containing declarative inputs.
Reusable executable engines remain under `na2_patcher/modules/`.

The directories themselves define ownership. Every enabled module input must
be beneath exactly one feature directory, and its first subdirectory must equal
the module engine type. Enabling a feature enables all module inputs it owns.
The feature row order and fixed engine registry derive stable module IDs,
global order, paths, and module hashes. There is no feature-selection table or
duplicated feature-level module catalog.

The composer resolves declared module-artifact dependencies before it closes
all module results into typed file replacements and insertions. It also derives
the guarded `SYSTEM.CNF` and boot-ELF title edits plus the boot-file rename from
`identity.json`. The image assembler then performs the only physical ISO
mutation, mirrors file-tree changes across ISO9660/UDF, and verifies the
complete staged image. There are no patch-to-patch dependencies.

Binary-patcher packages declare their normal composition through
`default_enabled` on each patch. Disabled experimental, failed, or unrelated
patches may remain in the same package for inspection without entering the
normal profile build. Focused CLI commands can still request explicit patch IDs
for research and validation, but this is not part of feature composition.

## Binary-patcher schema v2

Every binary-patcher package has exactly four canonical control tables:

- `targets.tsv`
- `groups.tsv`
- `patches.tsv`
- `edits.tsv`

`groups.tsv` declares the package's organizational group catalog. Every patch must
name one declared group, and every edit must name one declared patch. Empty
packages are valid, but a declared group must contain at least one patch and a
declared patch must contain at least one edit.

Package identity comes from the owning feature/module path; identity manifests
are obsolete. Schema v1 is removed from the live engine. `relations.tsv` is also removed:
patch dependencies and declared patch conflicts are not part of the current
model. Edits that must always apply together belong to one atomic patch. A
future schema can add explicit relations when a concrete need establishes the
right semantics.

## Composition and conflict validation

Each enabled binary-patcher module expands its default-enabled patches in
deterministic package order. After those patches are materialized as concrete
ordered edits, the
compositor simulates them in memory before creating the `.building` ISO:

- if the current bytes match the edit guard, apply the replacement;
- if the replacement is already present, record `already_satisfied`;
- if an edit's guard matches bytes written by an earlier edit, apply it as a
  valid ordered chain;
- otherwise fail as a real composed-edit conflict.

This validates the actual composed result instead of trying to infer conflicts
from overlapping ranges or separate dependency metadata. Overlap itself is legal.

## Current canonical groups

The feature packages enabled by the current profile default-enable patches in
these binary-patcher groups:

- Localization: `glyph_data`, `auto_fit`, `alignment`, `battle_ui`,
  `front_end`, `etc_ui`, `battle_results`, `shop`
- QoL: `startup`, `practice`, `mode_select`
- Battle logic: `battle_logic`
- String patcher (delegated to `binary_patcher`): `identity`, `BTL`, `ETC`, `SLPS`

The generic Testing feature is retired. Its substitution edits produced no
improvement or a black screen, and their durable results remain in
`docs/knowledge/substitution.md`. Future experimental patches belong to their
owning feature, using patch `status` and `confidence` to express maturity and
certainty; a new feature is created only for a coherent capability. Rendering
is a disabled, completely empty reserved package. It contains no aspect-ratio
placeholder and no font content; font patches belong to Localization. Retired
`font_m01` and `font_elf_history` active package directories are not recreated,
while their useful historical evidence remains under
`docs/knowledge/font/history/`.

QoL's former bundle rows are split into independent atomic patches while
preserving their exact edits:

- Startup: Skip CC2 intro; Skip opening
- Practice: Voice off; Support off; Command display off; Simple display off
- Mode select: Remove Adventure

## Reproducibility and logs

The profile pins each enabled feature by one deterministic aggregate hash over
all canonical module inputs. Binary-patcher inputs cover four control tables
plus referenced blobs. String-patcher inputs cover `strings.tsv` only when a
feature owns local declarations. Imported-string consumption is a derived stage
and creates no placeholder directory or file. Translation-importer inputs cover
`mappings.tsv` and `references.tsv`. Adjacent documentation,
engine code, and non-input helpers are excluded.

Profile-run logs record enabled features plus derived module ownership,
identity, order, input hash, patched paths, applied default patch/edit
instances, and each edit outcome. The derived inventory is written as
`module_results.tsv`; it is build evidence, not profile input. The normal bare
`na2` workflow continues to load
`na2_patcher/profiles/current/`.

## Migration proof

Before migration, a deterministic v1 baseline captured six enabled binary-patcher modules,
92 selected patches, and 256 selected edits. After migration, the current
feature packages expand to 95 default patch instances and the same 256 edit
instances; the patch-instance count increases only because the two QoL bundles
became seven independent patches. Exact target paths, offsets, guards,
replacement bytes, lengths, and ordering remain equivalent.

Validation loads every package, derives the complete current profile, composes
all enabled modules in memory, runs the Python suite, and performs one
controlled byte-parity ISO build. It does not launch PCSX2.

## Acceptance criteria

- The manifest-free profile enables and aggregate-hash-pins reusable feature
  packages and derives module ownership from their directories.
- Binary-patcher schema v2 represents package -> group -> patch -> edit.
- Profile module tables, identity manifests, feature selection tables, and
  profile/feature schemas are removed without replacement.
- Normal composition applies each enabled module's default-enabled patches.
- Overlapping patches are validated by deterministic ordered edit simulation
  rather than deduplication.
- `relations.tsv` and live schema v1 support are removed.
- Rendering is empty and Font is separate.
- Existing current-profile binary edit bytes remain unchanged.
- No source, release artifact, ISO, or binary is modified manually.
