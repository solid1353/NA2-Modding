# Battle mechanics resume handoff

## Task

- Workstream: Logic
- Task: Make substitution cost selective and retain the supporting character-ID,
  overlay, and character-data work completed during the investigation.
- Paused by: `zxc` on 2026-08-10.

## Stash

- Name: `On master: zxc Logic - Battle mechanics - 2026-08-10`
- Reference at pause time: `stash@{0}`
- Commit: `41e7e76e29683a24cbcd73eb6afe60c5d32ef967`
- Restore: `git stash apply stash@{0}`

After applying it, verify all paths listed below are present before dropping the
stash. If another stash has since been created, resolve the named stash by its
message or commit instead of assuming it is still `stash@{0}`.

## Stashed task-owned paths

- `src/battle_logic/substitution_cost.c`
- `src/battle_logic/character_id_overlay.c`
- `na228_builder/catalog/battle_logic.modcat`
- `na228_builder/catalog/implementation/injections.json`
- `na228_builder/configurations/base.json`
- `na228_builder/configurations/development.json`
- `tests/builder/test_catalog.py`
- `tests/builder/test_configuration.py`
- `tests/injection/test_injection_tools.py`
- `resources/character_data.tsv`
- `docs/knowledge/gameplay/README.md`
- `docs/knowledge/gameplay/battle.md`
- `docs/knowledge/gameplay/character_ids.md`
- `docs/knowledge/gameplay/substitution.md`

## Current state

- The substitution-cost hook selects cost `2` for Naruto ID 57 and cost `4`
  for Sakura ID 58, with the configured scalar as the fallback for every other
  ID. Native subtraction and clamping remain intact.
- The user reported that the per-character substitution behavior works in the
  supplied Practice matchups.
- The Character Select overlay renders live P1/P2 IDs. Its latest candidate is
  black, centered, with P2 below P1. Rendering was observed before the final
  layout adjustment; the centered stacked layout has not been explicitly
  runtime-confirmed by the user.
- `resources/character_data.tsv` is the single canonical character table. It
  contains 74 unique named entries and the fields `character`, `id`,
  `default_hp`, `durability_parameter`, `incoming_damage_multiplier`,
  `record_address`, `offense_multiplier`, `health_recovery_multiplier`, and
  `chakra_recovery_multiplier`.
- Default HP is neutral effective HP derived from the executable's static
  durability parameter, not a literal per-character full-gauge value. Naruto
  is `90.909091`; Sakura is `83.333333`.
- Confirmed character-record offsets and consumers are documented in
  `docs/knowledge/gameplay/battle.md`. Character identity evidence is in
  `docs/knowledge/gameplay/character_ids.md`.
- No implementation commit or push exists. Normal-mode commit setting is
  `c off`; game/runtime patches still require `ver` before commit and push.

## Validation state

- `na228 build -d` completed successfully and validated the composed current
  development configuration without staging an ISO.
- The character table was checked against clean `SLPS_258.37`: 74 rows, nine
  columns, unique names and IDs, and all record-derived values matched.
- Old `character_ids.tsv` and `character_base_hp.tsv` filenames and references
  were removed.
- `git diff --check` passed for the task-owned changes.
- The user reported the selective substitution behavior works.
- The final centered/stacked overlay layout remains runtime-unverified.

## Remaining work

1. Apply the named stash and verify all 14 paths were recovered before dropping
   it.
2. Recheck the final overlay source and obtain user runtime confirmation of the
   centered black P1/P2 layout.
3. Reconcile `docs/knowledge/gameplay/substitution.md` with the user's runtime
   confirmation so it does not continue describing proven behavior as an
   untested candidate.
4. Review the complete task-owned diff and any final validation evidence.
5. Wait for `ver` before committing and pushing the game/runtime patch and its
   associated resource, tests, and knowledge documentation.

## Blockers

No technical blocker is known. Completion is paused by explicit `zxc` and the
remaining runtime-acceptance/`ver` boundary.
