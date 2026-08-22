# Character Select Font layouts

Font-owned layout evidence for Character Select confirmation and player-mode rows. The initial grouped findings were established on 2026-07-24; later evidence dates are recorded with their sections.

## Character Select modal selected row, return body, and choice list

The refreshed 2026-07-29 ss5-ss7 pairs isolate two main-ELF callers inside
the Character Select modal family, and the replacement 2026-07-30 ss1 pair
isolates its remaining return-confirmation list caller:

- file `0x2BC984` / runtime `0x003BC884`, guarded by
  `84090E0C00000000`, draws only the selected row in the five-row
  `Back to Game Mode Screen` modal;
- file `0x2BCAAC` / runtime `0x003BC9AC`, guarded by
  `800D0E0C00000000`, draws the complete top Yes/No list for the return
  confirmation;
- file `0x2BCB54` / runtime `0x003BCA54`, guarded by
  `C4080E0C00000000`, draws only the `Return to Game Mode Screen?`
  confirmation body.

The 2026-08-22 Menus suite supersedes the earlier per-string positioning
candidate. The row loop in clean NA2 main-ELF `FUN_003BC780` supplies Y `8`,
`32`, `56`, `80`, and `120` before the selected call at file `0x2BC984` or the
ordinary call at file `0x2BC9BC`. Both existing C adapters preserve the first
four structural Y rows and map the footer to Y `114`; an already-adjusted
historical input Y `115` follows the same footer branch.

Both draw states now measure the live string and center it in one local
`(8, *, 240, 20)` shrink-only box. The selected native helper accepts integer
X, so its adapter truncates the measured centered X; the ordinary helper keeps
the centered float. This replaces the former per-string X table `81.75`,
`73.375`, `72.375`, `63.5`, `3.5` and removes the selected-footer-only Y
special case without adding another hook.

Menus page 1 captures selected rows 2 through 5, and page 2 captures selected
row 1. Their NA228/NUN5 red-ink bounds are exact at 640x480:

- row 1: `(272..367,177..190)`;
- row 2: `(260..378,207..220)`;
- row 3: `(259..380,237..250)`;
- row 4: `(248..391,267..280)`;
- footer: `(172..468,309..322)`.

The ordinary row origins and footer bounds use the same center contract. At a
dark-gray threshold, the only horizontal edge variation is the left edge of
ordinary `COM vs. 2P` (`259` in NUN5, `260` in NA228); the selected form has
exact bounds, so this is a glyph-raster edge rather than a row-origin offset.
The extra bottom edge on the ordinary fourth row is the intentional
non-collapsed NA228 glyph height. The user accepted this centered family
through `ver` on 2026-08-22.

NUN5 telemetry for the confirmation body is box `(8,8,368,24)`, horizontal
policy `2` (center), vertical policy `1`, and incoming scale `1`. A first C
candidate applied only those box dimensions while retaining NA2's existing
primary/direct renderer setup. It fit, but its letters stayed visibly smaller
and narrower than NUN5. That negative result proves that box math alone does
not select the expected glyph presentation.

The accepted sequence selects the secondary renderer through
`FUN_00186510(renderer,1)`, restores renderer fields `+0x28/+0x2C`, sets the
draw context from the modal object at `+0x74` through `FUN_001866D0`, then
uses the resident v2 measurement to compute the centered left edge inside the
368-unit box. The final callback draws from that prepared left edge through
native left draw `0x00379040`. Calling the native centered primitive instead
is rejected here: it remeasures with obsolete state and shifts the otherwise
correct result left.

For the exact accepted string, both NUN5 and NA2.28 black-ink bounds are
`(151,328)-(484,341)`; dark-pixel counts are `1209` and `1202`. The retained
comparison is
`@work/Font/artifacts/priority3/ss7-secondary-renderer-left-edge-comparison.png`.
The user accepted that lower confirmation body as good enough on 2026-07-30.

The same replacement-batch ss1 proves that the body remains correct while the
native top Yes/No list does not share NUN5's relative placement. Redirecting
only file `0x2BCAAC` to the existing
`v2_quit_choices_scope` reuses the already-proven Yes
`(64.5,31.5)` and No `(68.5,49)` map without introducing another C formula or
assembly fragment. A hidden direct-PINE trial loaded the supplied ss1,
installed only that guarded call, and produced a native 640x480 capture. The
modal boxes have different absolute X positions between games, but both
Current rows then have the same X/Y offsets from their respective modal
origins as NUN5. The accepted lower body remains unchanged. This selector
result was accepted with the complete Menus result on 2026-08-22.

Confidence is **verified** for the three call sites, renderer selection,
coordinate contracts, caller isolation, and supplied-state behavior. User
acceptance covers the complete modal family.


## Character Select ordinary-row metric session

Evidence date: 2026-07-30.

Supplemental ss1 reopens only the five-row player-mode list inside
main-ELF `FUN_003BC780`. NA2 draws its selected entry through
`FUN_00382610` at runtime `0x003BC884` and every ordinary entry through
`FUN_00382470` at runtime `0x003BC8BC` (ELF file `0x2BC9BC`, clean guard
`1C090E0C00000000`). NUN5 homolog `FUN_003CF3F0` instead routes both states
through one `FUN_00393210` helper, with native local Y values `0`, `24`, `48`,
`72`, and `106`.

The selected and ordinary hooks both enter the same 240-unit metric session.
The 2026-08-22 Menus evidence above proves that the durable contract is shared
measurement and centering, not a fixed correction or a table of positions for
the current five English strings. The selected renderer, ordinary renderer,
and confirmation callers remain independently scoped. Confidence is high; the
refreshed five-row list was accepted on 2026-08-22.
