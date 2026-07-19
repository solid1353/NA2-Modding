# Clean-source Font patch set

This package starts from verified clean NA2 inputs. It does not use
`font_m01`, reconstructed font data, or the failed semantic-NUN5 palette
experiment as an implementation parent. `DATA/GF4.BIN` and `DATA/GF4C.BIN`
remain byte-identical to clean NA2.

Two independent components are enabled by default:

- `font_controls_auto_fit` reproduces NUN5's shrink-only 128-unit Controls
  behavior at the one applicable call family. Clean NA2 plain-ASCII width is
  `9.5 * byte_count + 1`; strings below 14 bytes retain scale `1.0`, so
  `Linked Attack` remains full width, while the 19-byte official
  `Ultimate Jutsu Prep` label is fitted and centered. The final `OFF` row
  continues through the untouched ordinary renderer call. A measured local
  overflow center correction and two-unit row-origin correction match the
  NUN5-relative horizontal center and the Controls box baseline without
  changing another screen.
- `font_modal_alignment` uses five measured local X values plus corrected
  local Y values for the character-select `Back to Game Mode Screen` modal.
  Its selected-path compensation prevents the shadow draw from shifting ink.

The components occupy non-overlapping clean zero ranges and are separately
selectable. Auto-fit owns the Controls helper, three local horizontal renderer
helpers, one scale word, their hooks, and the local row-origin edit. Modal
alignment owns only its five-value table and three call-site edits. The
remaining cave padding stays zero, and scale is restored to `1.0` immediately
after each fitted draw.

The disabled `font_vertical_quad_height` component is retained only as exact
negative evidence. Runtime review proved that its `0x88064` edit made the
clean descriptor render as a 28x28 quad, stretching X and Y by 16.7 percent
without changing logical measurement and visibly damaging outlines. Its
`runtime_failed` state prevents normal application.

Exact offsets, guards, replacement bytes, and reasons are recorded in
`edits.tsv`. The derivation and guarded runtime-write generator are retained
under `work/Font/analysis/controls_autofit/`; canonical evidence and matched
measurements are in `docs/knowledge/font/README.md`.
