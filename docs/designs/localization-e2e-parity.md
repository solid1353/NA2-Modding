# Localization E2E Parity

Status: Jutsus, Menus, and Ninja Song complete; Practice pending

## Scope

This document records the visual differences still to be resolved between NUN5
and NA228 in these E2E suites:

- `practice`

The original review covered all 7 published diff-grid pages across Menus,
Practice, and Ninja Song together with their pair and blend grids. Jutsus,
Menus, and Ninja Song are complete; their durable findings are recorded in the
canonical localization documentation. Practice remains pending here.

## Accepted differences and review exclusions

The following differences are intentional and are not defects:

- NA228's non-collapsed font height;
- NA228's font shading;
- ordinary replay timing differences in fighter positions and background
  animation.

Vertical pixel-edge differences attributable only to the accepted font height
are therefore excluded.

## Cross-suite finding

Font metrics and origins are not consistently matched across the affected text
renderers. The mismatch is not one uniform screen-wide offset:

- some strings start at the correct coordinate but accumulate a horizontal
  width difference;
- some renderer families start one to three pixels left or right of NUN5;
- long strings expose advance differences that are nearly invisible on short
  labels;
- centered choices inherit width or centering differences even when their
  surrounding UI is aligned;
- selected or highlighted lines can behave differently from ordinary lines,
  so every fix must account for both states. The multiple screens captured for
  each menu deliberately cover those state variants.

This behavior appeared in all three baseline suites, but its magnitude and
direction vary by renderer family.

## Practice

### Confirmed differences

- Pause-menu rows are approximately one pixel to the right of NUN5.
- Help-page headings are approximately one to two pixels to the left.
- The Special Controls `ON`/`OFF` choices are approximately three pixels to the
  right, while the accompanying description is approximately two pixels to the
  right.
- Confirmation prose is approximately one pixel to the right.
- Long status and explanatory strings expose advance differences. In the
  current captures, `1P controls restored to defaults.` begins at the matching
  origin but ends approximately 10 pixels farther right.
- The same width divergence is visible in long move explanations, Practice
  Settings labels, and the selected-setting help line.

These observations identify multiple text families with different origins;
they do not support one global Practice offset.

### Confirmed matches

- The reviewed translations match NUN5.
- No UI-texture placement mismatch was found.
- Fighter-position differences in the pair and blend grids are replay timing,
  not Practice UI defects.
