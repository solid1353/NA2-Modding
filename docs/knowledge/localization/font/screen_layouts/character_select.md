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

The selected-row adapter uses a 240-by-20, single-line, shrink-only box at the
caller's Y and five local units to the right of its incoming X. The original
declarative selected-delay-slot compensation is removed because the symbolic
eight-byte hook replaces that call and delay slot atomically. The final ss5
red-ink bounds are `x=170..466`, exactly matching NUN5. The supplied ss6
isolation comparison proves that the selected hook does not select the adjacent
ordinary-row family.

The 2026-08-03 `font/main` captures 50 and 51 isolate the structural fifth row
in both draw states. Capture 51's ordinary black ink is two output pixels below
NUN5, whereas capture 50 proves the selected footer already has the correct
vertical phase. The accepted final row origins are Y `8`, `32`, `56`, `80`, and
`115`; the selected adapter applies its existing footer-only `-1` correction,
preserving final selected Y `114`, while the ordinary adapter consumes Y `115`
directly.

The row loop in clean NA2 main-ELF `FUN_003BC780` supplies Y `8`, `32`, `56`,
`80`, and `120` before the selected call at file `0x2BC984` or the ordinary call
at file `0x2BC9BC`. Both existing C adapters now translate those native values
to the accepted X table `81.75`, `73.375`, `72.375`, `63.5`, `3.5` and the five
accepted Y values. They also accept an already-adjusted Y `115` from historical
states. The former fixed-ELF producer replacement and X table are therefore
retired without adding another hook. Confidence is high: clean-ELF disassembly
identifies both consumers, compiled-fragment tests require every accepted
coordinate in both adapters, and captures 50 and 51 independently expose the
two final renderer phases. Runtime validation of the storage refactor remains
for the user; the visible coordinate contract itself is unchanged.

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
result is agent-validated and awaits explicit user acceptance.

Confidence is **verified** for the three call sites, renderer selection,
coordinate contracts, caller isolation, and supplied-state behavior. User
acceptance currently covers the lower confirmation body, not the new top
selector result.


## Character Select ordinary-row metric session

Evidence date: 2026-07-30.

Supplemental ss1 reopens only the five-row player-mode list inside
main-ELF `FUN_003BC780`. NA2 draws its selected entry through
`FUN_00382610` at runtime `0x003BC884` and every ordinary entry through
`FUN_00382470` at runtime `0x003BC8BC` (ELF file `0x2BC9BC`, clean guard
`1C090E0C00000000`). NUN5 homolog `FUN_003CF3F0` instead routes both states
through one `FUN_00393210` helper, with native local Y values `0`, `24`, `48`,
`72`, and `106`.

The existing selected hook already enters the accepted 240-unit v2 metric
session and applies a five-local-unit X correction. Ordinary rows bypassed that
session, so their Y bounds were already exact but their visible widths were
eight or nine pixels too large and their left edges were six pixels too far
left. A second caller-specific C entry now gives only the ordinary draw the
same metric session and X correction, then returns through the original
ordinary callback. It does not alter the row table, selected renderer, or
confirmation callers.

At 640x480, the three ordinary comparison rows now have exact NUN5 bounds:
`(259..377,206..219)`, `(257..379,236..249)`, and
`(246..390,266..279)`. The selected first row remains on its prior accepted
path. This proves that the discrepancy was session selection rather than
per-row Y drift or a need for individual scale constants. Confidence is high;
explicit user acceptance of the refreshed five-row list remains pending.
