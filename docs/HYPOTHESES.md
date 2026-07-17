# Hypotheses Archive

Use this file for old patch candidates, failed experiments, unverified addresses, and leads that should not clutter active PNACH/build files.

## GF4 Font Rendering Handoff

Status: paused after v23. Confirmed observations, the exact patch record, and the final comparison screenshot are preserved in `docs/knowledge/font/README.md`; canonical accepted and historical patch data remain under `na2_patcher/modules/raw_binary/patch_sets/`. Review those records and the preserved disassembly before proposing another experiment.

The unresolved work remains at least three separate problems: glyph appearance, positioning/advance behavior, and missing UN5-style auto-fit/squish for text that exceeds a box.

### Disassembly leads

- Reuse the preserved projects/exports under `@source/NA2_disassembly` and `@source/UN5_disassembly`; do not disassemble either ELF from scratch.
- NA2 ASCII setup lead: `FUN_00186510`.
- UN5 counterpart: `FUN_001878e0`.
- UN5 boxed auto-fit leads: `FUN_00389df0` and `FUN_0018b1b0`.
- NA2 menu lead: `FUN_003885b0`, which calls `FUN_00379240` and appears to center/draw without the corresponding 128-pixel auto-fit path.
- A full UN5 text-renderer transplant is unsafe. Continue with small, proven renderer-logic comparisons and script-generated patches only.
