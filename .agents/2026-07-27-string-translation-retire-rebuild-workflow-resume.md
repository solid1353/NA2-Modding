# String Translation: retire rebuild workflow

Date: 2026-07-27

## Objective

Retire the completed mapping-ID/from-scratch rebuild workflow and the obsolete
cumulative replacement worker workflow. Leave concise historical remarks with
an exact Git recovery commit. Preserve canonical translation mappings,
screenshots, savestates, and normal profile composition.

## Task and phase

- Workstream: `String Translation`
- Selected task: `Retire the mapping-ID and cumulative replacement rebuild
  workflows, preserve concise Git recovery notes, and keep canonical mappings
  as the sole translation source of truth.`
- Status: `In Progress`
- Phase: inspection and approved plan complete; implementation not started
- Approval: approved by the user's `qwe`
- Recommended effort: high

## Confirmed decisions

- `na2_patcher/features/localization/translation_importer/mappings.tsv`
  remains the only normal-build translation source of truth.
- Remove live support for mapping-ID rendering rather than merely hiding its
  launcher selector.
- Remove the obsolete `rebuild` and `replacement` pair-launch selectors.
- Delete disposable `mapping-ids.iso`, `replacement.iso`, diagnostic inventory,
  rebuild/replacement diff, and corresponding task logs.
- Preserve screenshot/savestate evidence used by canonical mapping
  `display_basis` values.
- Delete the two large rebuild documents and retain only concise historical
  notes.
- Recovery reference for the complete pre-retirement implementation:
  `9bb1e191a2e523f467f60c63758db2ff1df0b15b`.
- The required script-retirement index entry in `scripts/README.md` must name
  each former script path, the recovery commit, the retirement reason, and the
  maintained replacement.
- Do not build an ISO or operate PCSX2 for this cleanup.

## Completed inspection

Read completely:

- `AGENTS.md`
- `TASKS.md`
- `docs/workstreams/string_translation/README.md`
- both directly linked rebuild documents
- `docs/knowledge/localization/external_string_payload.md`
- `na2_patcher/README.md`
- Localization, translation-importer, and string-patcher READMEs
- applicable interaction, repository, coordination, testing, and modding
  policies
- `scripts/README.md`, `docs/PROJECT_CONTEXT.md`, and `docs/LOGGING.md`

The live diagnostic implementation was traced through:

- `scripts/research/translation/build_mapping_ids.ps1`
- `scripts/research/translation/sync_rebuild.py`
- `scripts/na2/build.ps1`
- `scripts/pcsx2/launch_pair.ps1`
- `na2_patcher/build_profile.py`
- `na2_patcher/module_pipeline.py`
- `na2_patcher/modules/translation_importer/`
- `na2_patcher/modules/string_patcher/`
- focused tests and all documentation references

Verified disposable work artifacts:

- `work/String translation/build/mapping-ids.iso`
- `work/String translation/build/replacement.iso`
- `work/String translation/artifacts/diagnostic-rebuild/`
- `work/String translation/artifacts/rebuild_replacement_diff/`
- `work/String translation/logs/`
- `work/String translation/temp/`

The work tree itself is ignored by Git. Preserve `inputs/`, savestate reports,
paired screenshot evidence, and other evidence still referenced by canonical
mappings.

## Implementation state

No implementation or artifact change is preserved. Two initial code edits were
discarded at the user's request to leave a clean tree. Resume from the committed
architecture and apply the plan below as one coherent change.

## Remaining implementation plan

1. Refresh live `AGENTS.md`, String Translation policy, Git state, and this
   handoff. Preserve any concurrent changes.
2. Finish removing diagnostic-only code:
   - remove rebuild-table parsing and `build_mapping_id_import_plan` from
     `translation_importer`;
   - remove mapping-ID transforms/display modes from `string_patcher`;
   - simplify normal call signatures and annotations;
   - remove diagnostic parameters from `scripts/na2/build.ps1`.
3. Remove obsolete user entry points:
   - delete `build_mapping_ids.ps1` and `sync_rebuild.py`;
   - remove `rebuild` and `replacement` from `launch_pair.ps1`.
4. Remove or rewrite diagnostic-only tests while retaining normal CLI,
   importer, string-patcher, and build coverage.
5. Delete `docs/workstreams/string_translation/rebuild_with_ids.md` and
   `rebuild.md`.
6. Replace active workflow descriptions with concise history/recovery notes in
   the String Translation, Localization, module, project-context, scripts, and
   UI-research documentation. Remove the diagnostic-inventory mandate from
   `docs/policies/modding.md`.
7. Add the required `scripts/README.md` retirement-index entries using recovery
   commit `9bb1e191a2e523f467f60c63758db2ff1df0b15b`. The maintained replacement is
   canonical `mappings.tsv` plus ordinary profile/worker builds.
8. Delete only the disposable work artifacts listed above. Verify every
   resolved deletion target remains under
   `work/String translation/` before recursive removal.
9. Run focused importer/string-patcher/build-profile tests, PowerShell parsing
   for changed scripts, then the full patcher unit suite. Do not build an ISO.
10. Search the repository for stale diagnostic names/options/paths. Refresh
    Git, stage only this workstream's intended files, commit as
    `Codex <codex@agent.invalid>`, push, then delete this handoff in a separate
    committed/pushed cleanup once resumption is established.

## Git state at stop

- Local HEAD:
  `9bb1e191a2e523f467f60c63758db2ff1df0b15b` (`tasks`)
- `origin/master`:
  `7f6bc1db20902f4f4ecca542c1a3e6e748e9e1b8`
- Local branch was one user-authored task-index commit ahead of origin before
  this handoff; Task Coordinator verified it as
  `WORK-970\Andrey Dobrov <avdobrov@alfabank.ru>` changing only `TASKS.md`.
- The handoff commit leaves no uncommitted files.
- Notification state was `muted`; no completion/blocker notification was sent.

## Exact first resume action

Read live rules and this handoff, run
`git status --short --branch`, and begin the diagnostic-only
engine/script removal from the committed architecture.
