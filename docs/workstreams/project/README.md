# Project

Canonical documentation landing page for the `Project` workstream.

## Workstream policy

- Project architecture and shared scripting are one responsibility. `Project`
  owns repository-wide architecture, shared scripts and automation, builders,
  command wrappers, paths and configuration, shared PCSX2 tooling, release
  tooling, cross-platform deployment, and global restructuring or cleanup.
- Domain-specific scripts remain with their owning workstream until they become
  shared project infrastructure.
- `@pcsx2_files/input_profiles/Comparison.ini` is the only manually edited
  comparison input profile. Regenerate
  `@pcsx2_files/input_profiles/Comparison_NA2.ini` with the maintained
  `act input`; do not edit the generated profile directly.

## Drafts

- [PCSX2 user and workstream workflows](pcsx2_workflows.md)

Global path, source, testing, and cleanup rules remain in `AGENTS.md` and are
not duplicated here.
