# Font renderer metrics and spacing

Clean NA2 and NUN5 secondary-font geometry, tracking, spacing, measurement, and
selected-row behavior.

## Research coverage

- **Assigned scope:** explain the measurable NA2/NUN5 differences in glyph
  height, advance, spaces, fitted labels, and selected-row position.
- **Exploration depth:** the clean initializers, metric decoder, glyph emitter,
  string renderer, selected-row helpers, and representative Controls labels
  were compared statically and through bounded runtime probes.
- **Confirmed coverage:** output-height handling, native selected-row offset,
  tracking and plain-space formulas, boxed-width reconstruction, and
  leading-bearing scaling are established.
- **Unresolved or untested:** exact reconstruction of every NUN5 measurement
  path outside the examined secondary-font callers.
- **Deliberate exclusions and overlap:** current NA228 renderer changes belong
  to [Font](../../../features/localization/font.md); asset and screen-specific
  findings remain in neighboring documents.
- **Evidence limitations:** representative labels establish the documented
  formulas but do not prove identical behavior for every markup or vertical
  writing path.

## Glyph geometry

NA2 `FUN_00187CC0` computes the normal quad at
`0x00187F64..0x00187F7C` by loading descriptor field `+0x0C` for both axes:

```c
right  = x + descriptor->output_width;
bottom = y + descriptor->output_width;
```

NUN5 `FUN_001891A0` instead uses width for X and height for Y, each multiplied
by its axis scale. A 24x28 secondary descriptor is therefore presented as
24x24 by NA2 and 24x28 by NUN5. Changing NA2's shared width load from 24 to 28
produces 28x28 and damages horizontal geometry; the cross-game difference is
specifically secondary vertical extent.

The compared donor cells do not become heavier when mapped through clean NA2's
palette. Across 85 cells and 23,800 source samples, alpha mass changes by a
ratio of `0.993762`, making it fractionally lighter. The observed height deficit
comes from quad geometry, not palette weight.

## Native selected-row offset

NA2 `FUN_00379040` draws the gray shade at the caller origin, then draws the red
foreground one local X unit left and two local Y units up. NUN5
`FUN_00389B30` enables shadow state and draws the foreground without changing
the input geometry. The selected-row jump is therefore native NA2 behavior,
not a font metric or caller-position defect.

## Tracking and ordinary spaces

NA2 `FUN_00186510` initializes secondary tracking to `-1.0` at context `+0x3C`.
NUN5 `FUN_001878E0` initializes tracking to `0.0`, scale X/Y to `1.0`, and extra
spacing to `0.0`.

NA2's horizontal plain-space branch at `0x001892C0..0x00189300` advances the
14-unit secondary cell by 13 units. NUN5's branch at
`0x0018A3CC..0x0018A434` computes:

```c
x += scale_x * (extra_spacing + cell_width + tracking - 6.0f);
```

At the native secondary values, NUN5 advances a plain space by eight units.
NUN5's zero tracking adds half a unit per visible glyph relative to NA2, while
its narrower spaces compensate most of that expansion. The inline-markup
half-space path at NA2 `0x00188A20..0x00188A84` is a different branch and does
not control ordinary spaces.

## Boxed measurement and leading bearings

With secondary tracking zero, NA2's trimmed visible-glyph widths match NUN5.
The remaining ordinary-space difference gives the equivalent NUN5 width:

```text
NA2 width at zero tracking - 6 * ordinary ASCII space count
```

For `Ultimate Jutsu Prep`, NA2 returns 190; subtracting 12 for two spaces gives
NUN5's exact logical width 178 and shrink scale `128 / 178 = 0.7191011236`.

A separate difference affects fitted glyph origins. NA2's semantic metric
decoder at `0x0018731C` subtracts the leading bearing directly, whereas NUN5's
secondary loader at `0x001887B0..0x001887D8` performs:

```c
x -= leading_bearing * scale_x;
```

The missing horizontal multiply explains the fitted-label origin and span
difference without implicating raster data, palette, or the width formula.
Vertical and alternate-glyph paths are separate.

## Rejected isolated changes

Changing only secondary tracking from `-1.0` to `0.0` leaves spacing and boxed
measurement inconsistent; tracking must be considered with the ordinary-space
and fit paths. Applying only NUN5's `128 / measured_width` threshold to the NA2
legacy measurement path also makes different fit decisions, including
incorrectly shrinking `Linked Attack`. Neither isolated change represents the
NUN5 renderer contract.
