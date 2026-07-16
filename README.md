# Naruto Shippuuden: Narutimate Accel 2 Modding

A scripted modding and reverse-engineering workspace for the PlayStation 2 game
*Naruto Shippuuden: Narutimate Accel 2*. The project targets PCSX2 and the
original game formats; it is not a native PC port.

| | |
|---|---|
| Game serial | `SLPS-25837` |
| Boot ELF | `SLPS_258.37` |
| Platform | PlayStation 2 |

## Project scope

The project combines four related areas:

- English translation through generated, validated patch tables.
- GF4/GF4C font-resource and renderer reverse engineering.
- Gameplay and default-setting changes through named raw-binary modules, with PNACH retained for stable resident-ELF/runtime behavior and carefully bounded temporary hypotheses. On-demand overlays such as `BTL.BIN` and `ETC.BIN` are tested through file patches and ISO rebuilds, not unguarded fixed-address cheats.
- Scripted package composition, ISO verification, CRC actualization, and frozen
  milestone releases.

Work is organized as reproducible, versioned artifacts. The detailed lifecycle
and directory boundaries are defined in the agent instructions and project
context rather than repeated here.

## Documentation

- [Agent instructions](AGENTS.md) define the non-negotiable workspace and safety
  rules.
- [Project context](docs/PROJECT_CONTEXT.md) records verified local state,
  directory roles, and established workflows.
- [Tasks](docs/TASKS.md) contains concrete active plans and queued work.
- [Hypotheses](docs/HYPOTHESES.md) preserves rejected experiments and unresolved
  reverse-engineering leads.
- [Release files](docs/RELEASE_FILES.md) defines the current frozen release
  contents.

Component-specific documentation stays with its component, including the
[translation module](na2_patcher/modules/translation/README.md) and the
[raw binary module](na2_patcher/modules/raw_binary/README.md).
