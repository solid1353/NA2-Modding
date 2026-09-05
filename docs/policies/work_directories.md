# Work directories and task artifacts

## Ownership and placement

- Before using a task work root, resolve the current exact chat title from
  Codex. Use only `@work/<exact chat title>/`, treat every other `@work` path
  as read-only, and set `NA228_TASK_WORK_ROOT` to that root before maintained
  commands create temporary files.
- Never use a system temporary directory or write outside repositories
  configured for the current task.
- Write authorized project changes to their canonical project paths and
  maintained workflow outputs to their configured repository paths.
- Copy changing external inputs to `@work/<exact chat title>/inputs/` before relying on them.
- Input-recording baselines under `@work/captures/<recording>/<game>/` are
  read-only.
- Before completion, remove disposable task artifacts and apply applicable
  [research](research.md) retention rules.

## Logs and retention

- Write bounded shared workflow logs below `@logs/`, generated task records
  below `@task_logs/<exact chat title>/`, and task-local build or runtime logs
  below `@work/<exact chat title>/logs/`. Do not write files directly in
  `@logs/` or `@task_logs/`.
- Persist only repository-relative paths or configured aliases, never
  machine-specific absolute paths.
- Record only the inputs, selected configuration, result, validation, timing,
  and failure detail needed to reproduce or diagnose the operation.
- Generated logs are ignored by Git and disposable. Before completion, delete
  task-owned logs and resulting empty directories. Retain a log only when an
  existing tracked document already names a concrete future use and
  regeneration is expensive or impractical.
- Large inventories may remain only when they prevent expensive rediscovery.
