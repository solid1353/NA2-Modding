# Durable Project Knowledge

This directory is the long-term record for established reverse-engineering
and game-behavior knowledge that would otherwise be lost when operational
logs are cleaned. Record unresolved hypotheses as explicitly labelled sections
in the relevant domain-owned document rather than organizing documents by
evidence type.

## What belongs here

Promote information here, or into the closest module-owned evidence file, when it would prevent future agents from repeating investigation. Examples include:

- confirmed or strongly supported subroutine roles, callers, callees, state fields, and state-machine behavior;
- runtime test matrices and negative results that constrain later work;
- stable binary, archive, and media layouts;
- gameplay behavior linked to a reproducible patch or observation;
- enough provenance to distinguish direct observation from static-analysis inference.

Module-specific machine-readable evidence should stay beside its module. Repository-wide explanations and evidence that do not belong to one patch module live under `docs/knowledge/`.

Removed architectures and experiments with continuing negative value are
condensed in [`retired_approaches.md`](retired_approaches.md). Do not distribute
retirement histories through current component documentation.

## Promotion policy

Before deleting or rolling operational logs:

1. Inspect them for reusable subroutine, data-layout, state-machine, gameplay, address, call-relationship, and negative-result evidence.
2. Promote the durable facts and the minimum evidence needed to interpret them.
3. Record the game/version, observation or test date, method/tool, confidence, and original repository-relative or configured-root provenance.
4. Label facts as observed, inferred, or unresolved. Do not turn an inference into a confirmed claim during promotion.
5. Reference canonical patch IDs and module evidence instead of duplicating full patch definitions.
6. Keep large raw inventories only when their contents are themselves reusable reference data. Do not preserve ordinary transcripts, repeated build output, incidental hashes, or redundant copies.
7. Verify the promoted copy before removing its operational source.

Use configured-root notation such as `@source/...`, `@logs/...`, and `@pcsx2_files/...`; never persist machine-specific absolute paths.

Operational logs remain disposable after their durable findings are promoted. Git history can recover retired tracked artifacts, but ignored operational logs are gone once deleted.

## Current domains

- [`game/`](game/README.md): disc identity, startup behavior, character assets,
  and the canonical human-readable game-file and media-layout references.
- [`runtime/`](runtime/README.md): EE address-space, allocator,
  overlay-lifetime, injection-capacity, and menu-input runtime findings.
- [`rendering/`](rendering/README.md): proper-widescreen requirements,
  NUN6 implementation evidence, NA2 donor-site mapping, and validation plan.
- [`gameplay/`](gameplay/README.md): battle behavior, substitution, and
  topic-local unresolved leads.
- [`localization/`](localization/README.md): translation, string placement, UI
  draw paths, character-facing assets, and font research.

Keep this index shallow. Add a subdirectory when a technical domain has several
related records; organize them by technical domain rather than the task or chat
that discovered them. The knowledge remains canonical and topic-owned.
