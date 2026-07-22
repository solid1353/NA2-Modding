# UI Translation

Canonical documentation landing page for the `UI Translation` workstream.

## Workstream policy

- The user delegates the technical approach to this workstream, while
  consequential decisions must be discussed.
- Keep the approach reproducible and evidence-driven.
- The workstream owns UI textures and the binary rectangle or placement logic
  needed to display them. Text content and font spacing are out of scope.
- Use `work/UI translation/` as the mutable task workspace.
- Before presenting any screen correction as final, provide a paired screenshot
  of the NUN5 reference and the corrected NA2 result at matching screen state.
  Inspect the entire pair for regressions, not only the targeted defect, and
  explicitly account for every material remaining difference. A corrected NA2
  screenshot by itself is insufficient final evidence.
- Continue correcting the current screen mismatches until every listed issue is
  fixed. Maintain the current mismatched-savestate-pair list under
  `work/UI translation/`, preserve each pair while its entry remains open, and
  remove both the savestate pair and its entry only after the user confirms that
  screen is fixed. After substantive work, present every remaining entry with
  its paired NUN5 and current corrected-NA2 screenshots; question-only replies
  do not trigger that presentation.
- Whenever visual validation would help during an active correction, present
  the matching NUN5 and current corrected-NA2 screenshot pair while continuing
  the work. If the user is available, incorporate their visual feedback into
  the next iteration; do not block progress waiting for that feedback.
- Format each paired presentation as a compact `Current visual checkpoint`:
  show the current corrected NA2 result first and the NUN5 reference second,
  then state what is accepted and every material difference that remains.

Global source, path, tool-safety, testing, and cleanup rules remain in
`AGENTS.md` and are not duplicated here.

## Documents

- [Active plan and working context](plan.md)
- [Battle UI knowledge](../../knowledge/battle_ui.md)
- [Collection UI knowledge](../../knowledge/collection_ui.md)
- [Stage-select UI knowledge](../../knowledge/stage_select_ui.md)
