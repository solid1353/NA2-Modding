# Narutimate Accel v2.28 Modding

A scripted modding and reverse-engineering workspace for the PlayStation 2
project *Narutimate Accel v2.28*, based on *Naruto Shippuuden: Narutimate Accel
2*. The project targets PCSX2 and the original game formats; it is not a native
PC port.

| | |
|---|---|
| Project serial | `SLOP-NA228` |
| Project boot ELF | `SLOP_NA2.28` |
| Source serial | `SLPS-25837` |
| Platform | PlayStation 2 |

## Project scope

The project combines four related areas:

- English text and UI-texture translation through generated, validated patch
  tables and fixed-size source-derived official donor-container imports.
- GF4/GF4C font-resource and renderer reverse engineering.
- Gameplay and default-setting changes through named binary-patcher modules, with PNACH retained for stable resident-ELF/runtime behavior and carefully bounded temporary hypotheses. On-demand overlays such as `BTL.BIN` and `ETC.BIN` are tested through file patches and ISO rebuilds, not unguarded fixed-address cheats.
- Scripted profile composition, ISO verification, on-demand PNACH CRC aliasing,
  annotated reproducible checkpoints, and GitHub releases.

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
- [Release process](docs/RELEASE_PROCESS.md) defines the self-contained Windows
  EXE, its validation gates, and GitHub publication workflow.

Component-specific documentation stays with its component, including the
[translation importer](na2_patcher/modules/translation_importer/README.md) and the
[binary patcher module](na2_patcher/modules/binary_patcher/README.md), plus the
[string patcher module](na2_patcher/modules/string_patcher/README.md) and the
[texture patcher module](na2_patcher/modules/texture_patcher/README.md).

Install the pinned patcher dependency before building the current profile:

```powershell
python -m pip install -r na2_patcher/requirements.txt
```
