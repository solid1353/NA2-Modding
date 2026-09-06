# Work directories and task artifacts

## Ownership and placement

- Before using a task work root, resolve the current exact chat title from
  Codex. Use only `@work/<exact chat title>/`. Treat every other `@work` path
  as read-only except for input moves required by this policy.
  Set `NA228_TASK_WORK_ROOT` to the task root before maintained
  commands create temporary files.
- Never use a system temporary directory or write outside repositories
  configured for the current task.
- Write authorized project changes to their canonical project paths and
  maintained workflow outputs to their configured repository paths.
- Write task-owned generated records below `@work/<exact chat title>/logs/`.
- Copy changing external inputs to `@work/<exact chat title>/inputs/` before relying on them.
- New savestates are stored in Workshop's `@pcsx2_savestates/`.
  Before inspecting a savestate supplied for the task, move it to
  `@work/<exact chat title>/inputs/` instead of copying it.
- Before inspecting an input-recording baseline, move it from
  `@work/captures/<recording>/<game>/` to
  `@work/<exact chat title>/inputs/captures/<recording>/<game>/`.
  Treat its contents as read-only.
- Before completion, remove disposable task artifacts and apply applicable
  [research](research.md) retention rules.
