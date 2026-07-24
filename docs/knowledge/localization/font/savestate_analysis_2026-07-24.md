# Font savestate comparison, 2026-07-24

## Inputs and method

The user supplied ten timestamp-matched NUN5/NA2 savestate pairs under
`@user_savestates/translation/font/`. All 20 files are valid PCSX2 ZIP
savestates with 640x480 `Screenshot.png` entries. Their combined size is
212,606,648 bytes.

The source library remained untouched. Exact copies, hashes, embedded
screenshots, paired presentation images, and measurement tables are retained
under:

- `@work/Font/inputs/sstates/translation/font/`;
- `@work/Font/artifacts/savestate_analysis/manifest.tsv`;
- `@work/Font/artifacts/savestate_analysis/screenshots/`;
- `@work/Font/artifacts/savestate_analysis/pairs/`;
- `@work/Font/artifacts/savestate_analysis/measurements/`.

The extraction reused
`scripts/research/ui_translation/ui_runtime.py::extract_embedded_screenshot`.
The task-local preparation and measurement scripts are under
`@work/Font/analysis/savestate_pairs/`. Measurements used Pillow 12.2.0 and
NumPy 2.3.5 from the bundled Codex workspace runtime. Dark-ink bounds use a
fixed luminance/chroma mask on tight, manually verified text crops. This is
suitable for matched relative measurements, not a replacement for renderer
metrics recovered from code.

## Pair inventory and visible result

| Slot | Screen | NUN5 behavior | Current NA2 behavior | Classification |
|---|---|---|---|---|
| 01 | Practice pause list | Long `Back to Game Mode Screen` fits | Same label clips at the right panel edge | glyph advances and missing fit |
| 02 | Control Settings | `Ultimate Jutsu Prep` fits; `Linked Attack` stays full width | Same fit decisions; all main rows fit | existing Controls fit path passes |
| 03 | Command Chart | Long move name fits | Long move name clips at the right edge | glyph advances and missing fit |
| 04 | Practice command explanation | Long descriptions wrap to subsequent lines | Descriptions remain on one line and clip | missing wrapping/layout |
| 05 | Practice Settings | Main rows fit and use the NUN5 row origin | Main rows fit but sit at a different local origin | call-local positioning |
| 06 | Quit Practice confirmation | Question wraps to two complete lines; choices are centered and evenly spaced | Question clips on one line; choices are left-shifted and too far apart vertically | missing wrapping plus shared modal positioning |
| 07 | Character-select return confirmation | Short question fits; choices are centered and evenly spaced | Short question fits; choices have the same modal-position defect as Slot 06 | shared modal positioning |
| 08 | Collection quit confirmation | Short question fits; choices are centered and evenly spaced | Short question fits; choices have the same modal-position defect as Slots 06-07 | shared modal positioning |
| 09 | Collection Movie list | Four long entries wrap, producing eleven visible list lines | No long entry wraps; several lines clip, producing seven visible lines | missing list wrapping/layout |
| 10 | No-memory-card prompt | Prompt wraps into six complete lines | Only three unwrapped, right-clipped lines are visible | missing system-prompt wrapping/layout |

The Slot 05 help bar is a scrolling line captured at different animation
positions and is not a valid alignment comparison. Slot 02's help bar has the
same limitation. Slots 01-10 contain no Save/Load screen, so fullwidth
Shift-JIS Save/Load digits were not measured. They remain outside the
halfwidth-Latin weight target.

## Font and metric measurements

Twenty identical black-text samples were measured across Slots 01, 02, 05, 08,
and 09. The median current-NA2 difference from NUN5 is:

- visible width: -2 pixels;
- visible height: -2 pixels;
- dark-ink pixel count: 0.850782x;
- dark-ink density inside the visible bounds: 1.018280x.

Therefore the current font is not a uniform bold enlargement. It is normally
shorter, often slightly narrower, and marginally denser inside that smaller
box. That denser compact shape explains the heavier visual impression, while
the lower total ink count follows from the reduced height.

The width error is string-dependent rather than one global scale:

- `Back to Character Select` is 282 pixels in current NA2 versus 266 in NUN5,
  a +16-pixel error;
- `Substitution Jutsu` is 200 versus 183, a +17-pixel error;
- `Linked Attack` is 149 versus 149 in Practice Settings and 149 versus 150
  in Control Settings;
- common short labels are usually 2-5 pixels narrower in current NA2.

This combination proves that a single global scale or tracking adjustment
cannot establish parity. Per-glyph advances, spaces, and/or the metric rows
used by these callers differ in composition-dependent ways.

Vertical placement is also caller-specific:

- Slot 01 list text centers are consistently 3 pixels lower in current NA2;
- Slot 02 Control Settings centers are about 1.5-2 pixels higher;
- Slot 05 Practice Settings centers are about 1.5-2.5 pixels higher, while
  their horizontal centers are 7.5-10 pixels farther right for ordinary rows.

A global X or Y correction would improve one family by damaging another.

## Repeated generic-modal defect

Slots 06, 07, and 08 reproduce the same choice layout exactly. The measurements
below are stable across all three:

| Choice | NUN5 center | Current NA2 center | Current delta |
|---|---:|---:|---:|
| `Yes` | approximately (317.5, 137.0) | approximately (299.5, 127.5) | (-18, -9.5) |
| `No` | (318.0, 162.0) | (295.0, 170.5) | (-23, +8.5) |

NUN5's choice-center separation is 25 pixels vertically; current NA2's is 43
pixels. The identical failure on three unrelated screens is evidence for one
shared modal renderer or shared modal constants, not three content-specific
row adjustments.

## Conclusions

The ten pairs expose at least seven distinct text-layout contexts:

1. Practice pause list;
2. Control Settings boxed labels;
3. command-chart and Practice explanatory text;
4. Practice Settings rows;
5. generic confirmation modal choices and body text;
6. Collection Movie list;
7. no-memory-card system prompt.

Only the Control Settings boxed-fit behavior is proven correct in this sample:
`Ultimate Jutsu Prep` fits while `Linked Attack` remains full width. Short
strings fitting in Slots 05, 07, and 08 do not prove those callers have
auto-fit.

Making the raster font visually closer to NUN5 remains useful, but it cannot
solve the missing line wrapping in Slots 04, 06, 09, and 10. A perfect raster
may also make the borderline single-line cases in Slots 01 and 03 fit, but
those cases must be remeasured after the metric change rather than assumed.

The implementation order supported by this evidence is:

1. refine the halfwidth-Latin raster and metric rows against NUN5;
2. remeasure every matched string without retaining speculative row-by-row
   moves;
3. fix the shared generic-modal choice layout once;
4. reproduce NUN5 wrapping/boxed behavior in each confirmed caller family,
   reusing a shared helper where disassembly proves the callers share one;
5. rerun all ten pairs and add a dedicated Save/Load pair only for regression
   coverage, not as a Latin-weight target.

Follow-up on 2026-07-24 completed step 1: the canonical secondary-only
descriptor-height path restored the intended 24x28 presentation while
retaining the accepted NUN5-derived raster, metrics, spacing, bearings, and
Controls fit. The user accepted the font itself as almost pixel-for-pixel.
The remaining steps are per-caller positioning, wrapping, and auto-fit work.

Confidence is high for the visual bounds, repeated modal coordinates, and
presence or absence of wrapping. Confidence is medium for the exact internal
ownership of the seven caller families until the corresponding call sites are
matched in the preserved NA2/NUN5 disassembly.
