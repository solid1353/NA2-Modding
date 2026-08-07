# Durable Project Knowledge

This directory is the long-term record for established reverse-engineering
and game-behavior knowledge that would otherwise be lost when operational
logs are cleaned. New unresolved hypotheses belong in topic-local documents beside the
relevant subsystem or research area.

## What belongs here

Promote information here, or into the closest module-owned evidence file, when it would prevent future agents from repeating investigation. Examples include:

- confirmed or strongly supported subroutine roles, callers, callees, state fields, and state-machine behavior;
- runtime test matrices and negative results that constrain later work;
- stable binary, archive, and media layouts;
- gameplay behavior linked to a reproducible patch or observation;
- enough provenance to distinguish direct observation from static-analysis inference.

Module-specific machine-readable evidence should stay beside its module. Repository-wide explanations and evidence that do not belong to one patch module live under `docs/knowledge/`.

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

- `game/`: disc identity and the `game/files/` collection, which contains the
  canonical human-readable game-file map, minimum useful analysis levels, the
  reusable escalation workflow, and exact outer-ISO, `DATA.CVM`, and AFS layout
  inventories.
- `runtime/`: EE address-space, allocator, overlay-lifetime, injection-capacity,
  and menu-input runtime findings.
- `gameplay/`: gameplay-behavior findings and topic-local unresolved leads.
- `localization/`: string placement, substitution, binary evidence, function
  maps, runtime tests, UI draw-path findings, and font research.

Keep this index shallow. Add a subdirectory when a technical domain has several
related records; do not organize records by the workstream that happened to
discover them. Workstream landing pages may link here, but the knowledge remains
canonical and topic-owned.
