# Raw-binary patch hierarchy and profile-driven workflows

## Objective

Refactor the raw-binary patch system to represent and enforce this hierarchy:

```text
Profile -> patch set -> group -> patch -> edit
```

This hierarchy describes only the raw-binary branch. `Module` is a broader
build-pipeline concept, not a level in the raw-binary content taxonomy.
Profiles themselves are broader than raw-binary: they define the complete
ordered build composition across raw-binary, translation, UI-texture, disc
identity, and future module types. For a raw-binary profile entry, the selected
content follows the hierarchy above.

## Layer responsibilities

- A profile is a thin, reproducible build or test definition. It selects and
  configures all ordered module invocations, pins every executable input by
  hash, and records the complete accepted build state. Within a raw-binary
  invocation it selects atomic patch IDs.
- A patch set is a cohesive feature domain such as Rendering or QoL.
- A group organizes related patches within a patch set, such as Fonts, Aspect
  Ratio, Startup, or Practice. Groups are organizational and are not initially
  selectable.
- A patch is an atomic selectable feature with its own status, confidence,
  provenance, dependencies, conflicts, and runtime classification.
- An edit is one exact binary operation belonging to a patch, including its
  target, offset, expected bytes or hash, replacement source, length, and
  reason.

## Schema and engine work

The architecture observed during the source task used raw-binary schema v1
with patch-set-local `manifest.tsv`, `targets.tsv`, `patches.tsv`,
`relations.tsv`, and `edits.tsv`. It represented patch set -> patch -> edit and
had no first-class group layer. Treat that as the starting diagnosis, not a
guaranteed-current snapshot; refresh the live engine and schemas before work.

Introduce an explicit group representation, expected to be a patch-set-local
`groups.tsv` plus a required `group_id` in `patches.tsv`, subject to final
inspection and design. Update raw-binary loading, validation, selection,
planning, application, logging, schemas, documentation, and focused tests.

The validator must reject undeclared or duplicate groups, patches without a
valid group, edits without a valid patch, empty patches, invalid relations, and
profile selections that do not name atomic patches. Preserve dependency and
conflict enforcement across patches.

Structural validation cannot decide whether every feature is conceptually
atomic. Existing patch sets therefore require a semantic review during
migration rather than only a mechanical column addition.

## Canonical migration

Migrate the existing raw-binary patch sets without changing their resulting
binary bytes. Preserve exact expected bytes and hashes, target sizes, patch
statuses, confidence, provenance, runtime classifications, disabled history,
relations, edit ordering, and profile hash pins.

The intended Rendering organization is:

```text
Rendering patch set
├── Fonts group
│   ├── Font patch
│   │   └── Accepted current font_m01 GF4/ELF coverage edits
│   ├── Auto-fit patch
│   │   └── Future NUN5-style renderer fitting edits
│   └── Disabled historical font experiment patches
└── Aspect Ratio group
    └── Future aspect-ratio patches
```

The currently separate `font_m01` and `font_elf_history` data should be
consolidated into Rendering while preserving the accepted current state and
appropriate disabled v22/v23 history.

QoL demonstrates why the group layer is needed. Its original PNACH hierarchy
was migrated too literally: cheats became patches and subcheats became edits.
Several independently meaningful features are consequently stored one level
too low. More precisely:

- `ELF-Q001 Intro skips` is semantically a Startup group containing the
  independent Skip CC2 intro and Skip opening patches.
- `ELF-Q002 Practice QoL` is semantically a Practice group containing the
  independent Voice off, Support off, and Command display off patches.
- `ELF-Q003 Simple display off` is already a proper one-edit atomic patch and
  only needs a group assignment.

Five of QoL's six current edit rows are therefore semantically atomic patches
stored one level too low. The intended semantic organization is:

```text
QoL patch set
├── Startup group
│   ├── Skip CC2 intro patch
│   │   └── Exact instruction edit
│   └── Skip opening patch
│       └── Exact instruction edit
└── Practice group
    ├── Voice off by default patch
    │   └── Exact instruction edit
    ├── Support off by default patch
    │   └── Exact instruction edit
    ├── Command display off by default patch
    │   └── Exact instruction edit
    └── Simple display off by default patch
        └── Exact instruction edit
```

The same semantic review must be applied to the other canonical patch sets so
that bundle-like rows become groups where appropriate and atomic features
remain patches. A patch may still contain multiple edits when those edits are
one inseparable feature.

## Profile-driven workflows

Profiles must become the shared entrypoint used by normal builds and controlled
tests rather than passive manifests or data bypassed by scripts:

```text
build or test command
-> select profile
-> verify every ordered module invocation and pinned input
-> for each raw-binary invocation, resolve selected atomic patches
-> validate groups, dependencies, and conflicts
-> generate the complete build or test plan
-> apply each module through its canonical engine
```

Keep `na2_patcher/profiles/current/` as the default accepted build definition.
Allow task-specific or test profiles to exercise isolated modules or
raw-binary patches without modifying the current profile. Such profiles are
reproducible fixtures: they pin every input, verify dependency/conflict
behavior, generate reviewable plans, and support byte/hash comparisons against
the accepted current profile. Groups remain organizational; tests normally
select atomic patch IDs rather than groups.

The original task requested explicit profile selection in the `na2` build-only
and build-and-launch workflows. The current `AGENTS.md` public command contract
allows only bare `na2`, `na2 -c`, `na2 -p`, and `na2 act`, and explicitly
forbids additional public build arguments. This is a live design constraint,
not permission to add another flag. Implementation must either keep explicit
selection internal/test-only or obtain an approved change to the public command
contract. Relevant scripts and tests must still invoke the same profile-driven
planner instead of independently hard-coding patch sets or selections.

Plans and logs must identify the selected profile, resolved patch sets, groups,
patches, and edits. Stale input hashes or invalid selections must fail before
binary modification begins.

## Acceptance criteria

- The raw-binary schema explicitly represents groups and enforces every level
  from patch set through edit.
- Existing canonical patch sets are migrated into semantically correct groups
  and atomic patches.
- Rendering contains Fonts and Aspect Ratio groups with the accepted font state
  and appropriate disabled historical experiments preserved.
- QoL exposes its independently meaningful controls as independently selectable
  patches.
- Profiles select atomic patches and pin all executable inputs by hash.
- Profiles continue to define and order the complete build across every module
  type; raw-binary selection is only one kind of profile entry.
- Normal build and controlled test workflows use the same profile-driven
  planning and application path.
- Controlled tests can select explicit task-specific profiles without changing
  `profiles/current/`; any public `na2` profile-selection interface requires a
  separately approved command-contract change.
- Focused schema, validation, dependency/conflict, selection, planning, and
  profile tests pass.
- The migrated current profile produces the same binary edit plan and output
  bytes as before the refactor.
- No source or release artifact is modified, and no binary is edited manually.

## Execution constraints

Before implementation, refresh live Git and workspace state and inspect the
current raw-binary engine, schemas, patch sets, profiles, scripts, and tests.
Concurrent edits are expected; preserve them and stop on direct overlap. Follow
the selected-task approval gates in `AGENTS.md`. Do not build an ISO or launch
PCSX2 unless runtime work is explicitly added to the task scope.

The source task performed only read-only analysis plus creation of this context
document and its `TASKS.md` link. No hierarchy refactor, schema migration,
profile workflow implementation, binary modification, ISO build, or PCSX2 run
was authorized or started. During that analysis, QoL's canonical tables were
untouched even though engine/profile files had concurrent work elsewhere.

Older handoff instructions named a dated `.agents` context file and
`docs/TASKS.md`; those paths had already drifted when inspected. Inventory the
live `.agents/` directory and use root `TASKS.md`, current documentation, live
Git state, and the user's newest instructions as authority rather than
recreating or assuming the obsolete paths.
