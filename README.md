# Narutimate Accel v2.28 Modding

A scripted modding and reverse-engineering workspace for the PlayStation 2
project *Narutimate Accel v2.28*, based on *Naruto Shippuuden: Narutimate Accel
2*. The project targets PCSX2 and original game formats; it is not a native PC
port.

| | |
|---|---|
| Project serial | `SLOP-NA228` |
| Project boot ELF | `SLOP_NA2.28` |
| Source serial | `SLPS-25837` |
| Platform | PlayStation 2 |

## Project scope

The project combines:

- English text and UI-texture localization through generated, validated patch
  data and source-derived official donor content.
- GF4/GF4C font-resource and renderer reverse engineering.
- Gameplay, rendering, and default-setting changes through reproducible
  file-backed patch modules, with PNACH reserved for stable resident/runtime
  behavior and bounded hypotheses.
- Hash-pinned profile composition, verified ISO assembly, PCSX2-based runtime
  validation, and self-contained release packaging.

Shared source-game, PCSX2, media, input, savestate, and Ghidra tooling lives in
the sibling `UN-Workshop` repository. Workshop owns its public command and
interfaces; this repository owns NA2-specific configuration, composition,
knowledge, tests, and release behavior.

## Documentation

- [Agent entrypoint](AGENTS.md): universal rules and scoped-document routing.
- [Agent commands](docs/AGENT_COMMANDS.md): commands interpreted by project
  agents.
- Policies:
  [interaction](docs/policies/interaction.md),
  [repository](docs/policies/repository.md),
  [coordination](docs/policies/coordination.md),
  [validation](docs/policies/testing.md),
  [modding/source](docs/policies/modding.md), and
  [research/knowledge](docs/policies/research.md).
- Runbooks:
  [runtime testing](docs/runbooks/runtime-testing.md) and
  [source extraction](docs/runbooks/source-extraction.md).
- [Path configuration](docs/PATHS.md) and
  [logging/retention](docs/LOGGING.md).
- [Knowledge index](docs/knowledge/README.md) for durable technical findings.
- [Tasks](TASKS.md), the user's selective coordination and decision tracker.
- [E2E infrastructure](e2e/README.md) and
  [agent E2E review workflow](e2e/AGENT_GUIDE.md).
- [Release process](docs/RELEASE_PROCESS.md).

Component contracts remain near their implementation when proximity matters,
including the [builder](na228_builder/README.md) and reusable module READMEs.
Substantial supporting documentation belongs under `docs/` and is linked from
those local entrypoints.

Install the pinned builder dependency before building the current profile:

```powershell
python -m pip install -r na228_builder/requirements.txt
```
