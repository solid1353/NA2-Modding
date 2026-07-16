# Hypotheses Archive

Use this file for old patch candidates, failed experiments, unverified addresses, and leads that should not clutter active PNACH/build files.

## GF4 Font Rendering Handoff

Status: paused after v23 and ready to resume only in the dedicated GF4 task after rereading this handoff and the preserved disassembly. Do not generate another GF4 package before that review.

### Current visual state

- The latest tested build used `NA2_APPLY__FONT__20260713_084649__v23__un5_ascii_zero_tracking.zip` plus the v25-generated translation TSV.
- v23 changed the NA2 ELF instruction at file offset `0x866E0` from `80 BF 02 3C` (`-1.0`) to `00 00 02 3C` (`0.0`) to mimic UN5 ASCII tracking.
- The user observed no meaningful visual change from that experiment. The Controls menu still shows oversized/chunky English, inconsistent spacing, and long entries clipped at the right edge.
- Final comparison screenshot: `logs/font/20260713_095523__v23__no_visible_change.png`.
- The one-off v23 builder script was retired to project trash. Its patch log remains under `logs/font/`; the reproducible test ZIP was retired from the workspace and remains available through Git history.
- The last `na2` log that built v23 is `logs/na2/na2_20260713_095820_889_pid33216.log`; `logs/na2/latest.log` mirrors it.

### Preserved milestones

- `milestones/packages/NA2_MILESTONE__FONT__m01__20260712_052042__un5_14x20_clean_coverage.zip`
- `milestones/packages/NA2_MILESTONE__FONT__m02__20260712_054105__un5_14x20_aligned_metrics.zip`

These are frozen reference packages, not proof that all rendering problems are solved.

### Confirmed observations

- NA2 and UN5 `GF4C.BIN` are both 104 bytes but are not byte-identical: they diverge from offset `0x28` onward. v22/v23 packages use the UN5 variant. The functional significance remains unproven.
- Replacing NA2 GF4 with exact UN5 GF4, padded or unpadded, produces proper broad spacing but patchy glyph rendering and can break PNACH behavior. Do not repeat that swap as a new hypothesis.
- v22 (`NA2_APPLY__FONT__20260713_042221__v22__un5_ascii_metrics_cell_and_palette.zip`) was clean/non-patchy and closer to UN5, but glyphs could touch/overlap and long text still clipped.
- v23's zero-tracking ELF change did not visibly improve v22. It changed only one NA2 ASCII-initialization field and was not a full UN5 renderer initialization port.
- The remaining work is at least three separate problems: glyph appearance, positioning/advance behavior, and missing UN5-style auto-fit/squish for text that exceeds a box.

### Disassembly leads

- Reuse the preserved projects/exports under `disassembly/NA2` and `disassembly/UN5`; do not disassemble either ELF from scratch.
- NA2 ASCII setup lead: `FUN_00186510`.
- UN5 counterpart: `FUN_001878e0`.
- UN5 boxed auto-fit leads: `FUN_00389df0` and `FUN_0018b1b0`.
- NA2 menu lead: `FUN_003885b0`, which calls `FUN_00379240` and appears to center/draw without the corresponding 128-pixel auto-fit path.
- A full UN5 text-renderer transplant is unsafe. Continue with small, proven renderer-logic comparisons and script-generated patches only.

## ETC Text Budget Tests

### Collection quit prompt padding

Status: active test, pending in-game check.

- File: `PRG/ETC.BIN`
- Offset: `0x24F50`
- Previous polished text: `Ｑｕｉｔ？`
- Test text: `Quit Collection Menu?`
- Reason: this slot is null-terminated and has zero padding through `0x24F97`, before the next visible string begins at `0x24F98`.
- The former working binaries, patch table, and patch record were retired from
  `work/` in recoverable trash batch `20260715_172049`.


## PNACH Candidates

### Disable RPS (old)

Status: archived, replaced by current `[Disable RPS]` section in `cheats/SLPS-25837_C0659AD1.pnach`.

```ini
// [Disable RPS (old)]
// author=solid1353
// patch=1,EE,202457C8,extended,1000007A
```

### Disable extra hit (old)

Status: archived, replaced by current `[Disable extra hit with aura punishment]` section in `cheats/SLPS-25837_C0659AD1.pnach`.

```ini
// [Disable extra hit (old)]
// author=solid1353
// patch=1,EE,20241F40,extended,100000AA
```
