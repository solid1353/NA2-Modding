# Narutimate Accel v2.28 Modding

A scripted modding and reverse-engineering workspace for the PlayStation 2
project *Narutimate Accel v2.28*, based on *Naruto Shippuuden: Narutimate Accel
2*. The project targets PCSX2 and the original game formats; it is not a native
PC port.

| | |
|---|---|
| Project serial | `SLPS-22228` |
| Project boot ELF | `SLPS_222.28` |
| Source serial | `SLPS-25837` |
| Platform | PlayStation 2 |

## Project scope

The project combines four related areas:

- English text and UI-texture translation through generated, validated patch
  tables and fixed-size official donor-container imports.
- GF4/GF4C font-resource and renderer reverse engineering.
- Gameplay and default-setting changes through named raw-binary modules, with PNACH retained for stable resident-ELF/runtime behavior and carefully bounded temporary hypotheses. On-demand overlays such as `BTL.BIN` and `ETC.BIN` are tested through file patches and ISO rebuilds, not unguarded fixed-address cheats.
- Scripted profile composition, ISO verification, CRC actualization, annotated
  reproducible checkpoints, and frozen releases.

Work is organized as reproducible, versioned artifacts. The detailed lifecycle
and directory boundaries are defined in the agent instructions and project
context rather than repeated here.

## Documentation

- [Agent instructions](AGENTS.md) define the non-negotiable workspace and safety
  rules.
- [Project context](docs/PROJECT_CONTEXT.md) records verified local state,
  directory roles, and established workflows.
- [Project paths](docs/PROJECT_PATHS.md) documents the single path manifest,
  logical root notation, and migration procedure.
- [Logging and retention](docs/LOGGING.md) defines bounded execution logs and
  promotion of reusable findings.
- [Knowledge index](docs/knowledge/README.md) preserves confirmed findings and
  evidence that must outlive disposable logs.
- [Tasks](TASKS.md) contains concrete active plans and queued work.
- [Hypotheses](docs/HYPOTHESES.md) preserves rejected experiments and unresolved
  reverse-engineering leads.

Component-specific documentation stays with its component, including the
[translation module](na2_patcher/modules/translation/README.md) and the
[raw binary module](na2_patcher/modules/raw_binary/README.md), plus the
[UI texture module](na2_patcher/modules/ui_textures/README.md).
