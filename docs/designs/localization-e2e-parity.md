# Localization E2E Parity

Status: scope refinement

## Scope

This document records the visual differences currently observed between NUN5
and NA228 in these E2E suites:

- `menus`
- `ninja_song`
- `practice`

The review covered all 7 published diff-grid pages in those suites together
with their pair and blend grids. The findings describe their current baseline
captures and do not yet prescribe an implementation.

## Accepted differences and review exclusions

The following differences are intentional and are not defects:

- NA228's non-collapsed font height;
- NA228's font shading;
- ordinary replay timing differences in fighter positions and background
  animation.

Vertical pixel-edge differences attributable only to the accepted font height
are therefore excluded. Ninja Song's animated patterned panel and title-logo
phase are also excluded unless later evidence establishes a static placement
error.

## Cross-suite finding

Font metrics and origins are not consistently matched across the affected text
renderers. The mismatch is not one uniform screen-wide offset:

- some strings start at the correct coordinate but accumulate a horizontal
  width difference;
- some renderer families start one to three pixels left or right of NUN5;
- long strings expose advance differences that are nearly invisible on short
  labels;
- centered choices inherit width or centering differences even when their
  surrounding UI is aligned.

This behavior appeared in all three baseline suites, but its magnitude and
direction vary by renderer family.

## Menus

### Confirmed differences

- Battle Settings labels are approximately two pixels to the right of NUN5.
- Pause-menu and confirmation text is generally one to two pixels to the right.
- `Yes` and `No` have slightly different widths or centering from NUN5.
- Long status text has an advance mismatch. In the current captures,
  `Battle Settings returned to defaults.` begins at the matching origin but
  ends approximately seven pixels farther right.

The Character Select return prompt and the main game-mode list are already
substantially aligned, so the remaining mismatch must not be treated as a
single offset applied indiscriminately to every menu string.

### Confirmed matches

- The reviewed translations match NUN5.
- No UI-texture placement mismatch was found.

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

## Ninja Song

### Confirmed content differences

- Objective 6 is missing NUN5's `timer` and `counts` counter labels. NUN5 places
  those labels between the second operand and the equals sign; NA228 leaves the
  area empty.
- Objective 9 has an extra percent sign. NA228 displays
  `1 * 100 % = 100`, while NUN5 displays `1 * 100 = 100`.

### Confirmed layout differences

- Objective text begins approximately two pixels to the right of NUN5.
- Text width or advances produce different line breaks:
  - objective 5 breaks after `Extra Hit` in NUN5 but after `Extra` in NA228;
  - objective 14 is one line in NUN5 and two lines in NA228;
  - objective 16 is one line in NUN5 and two lines in NA228.
- The extra wrapped lines alter the vertical composition and leave three
  captured scroll positions visibly out of parity with NUN5.

### Confirmed matches

- Apart from the missing counter labels and extra percent sign, the reviewed
  objective wording matches NUN5.
- No static UI-texture placement mismatch has been established.

## Remaining scope to refine

Before implementing the remaining suites, refine these decisions:

1. Confirm that every recorded one-to-three-pixel horizontal origin difference
   in Menus and Practice is in scope, while the accepted vertical height and
   shading remain unchanged.
2. Decide whether the target is exact NUN5 horizontal metrics for every listed
   renderer family or only exact wrapping and visible placement at the reviewed
   strings.
3. Confirm that Ninja Song must reproduce NUN5's line breaks and consequent
   scroll composition exactly despite retaining NA228's non-collapsed font
   height.
4. Confirm that the Ninja Song counter labels and removal of the percent sign
   are required content corrections.
