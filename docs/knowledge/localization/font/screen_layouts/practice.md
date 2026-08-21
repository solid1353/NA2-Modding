# Practice Font layouts

Font-owned layout evidence for Practice explanations and Practice Settings.

## Practice explanation mixed-text wrapping

Bounded NA2/NUN5 BTL comparison identifies the Practice explanation loop as a
separate caller family from the title draw immediately before it. NA2 reaches
the loop at BTL file `0x1C4BA0` / runtime `0x00878AA0`; NUN5 instead assembles
one bounded mixed text/tag string, installs a call-local metric/draw callback
pair for controller tokens, and passes the complete result through its wrapping
renderer.

The v2 adapter follows that broad caller logic rather than patching individual
rows. It builds a single 512-byte buffer from the caller's text and token
records, word-wraps it with the accepted proportional metric table, and uses a
364-by-48 box at X `39.2` and caller Y plus `21.2`. The glyph height is 28 and
the independent line advance is 14. The line-count field is zero, meaning
unlimited: the supplied NUN5 `ss3` Flee row proves that this nominal 48-unit
box legitimately carries three explanation lines, so the earlier two-line cap
was rejected before promotion.

The callback map preserves all 13 Practice controller tokens. D-pad directions,
Circle, Triangle, Square, Cross, plus, L1, R1, L2, and R2 use NA2's native icon
table and native draw helper; the adapter selects the caller's primary or
secondary icon object exactly as the original path does and applies the
NUN5-proven per-token Y offsets. Metric and draw callbacks, both icon objects,
renderer tracking, horizontal scale, and the prior active session are restored
after every call.

Supplied Practice slots 2-7 were converted with exact source hashes and guarded
memory edits because a savestate restores its captured BTL overlay and resident
RAM over the worker ISO. The converted task-owned states and manifests are
under
`@work/Font/artifacts/autofit_v2/practice_explanations/`. Hidden 640x480
captures show:

- `ss2`: the Manual Linked Attack explanation wraps to two lines;
- `ss3`: Flee wraps to three lines with D-pad, plus, and Cross intact;
- `ss4`: substitution, recovery, and extra-hit rows retain shoulder, face,
  D-pad, and plus icons;
- `ss5`: Circle and D-pad rows align; Current `Charge` versus NUN5
  `Charge Chakra` is a separate text-mapping difference;
- `ss6`: movement rows preserve D-pad, plus, and Cross alignment;
- `ss7`: Shadowblur wraps to two lines while Circle, shoulder, D-pad, and plus
  icons remain aligned.

Across all six pairs, wrapping, line spacing, X/Y placement, and inline-icon
alignment match the NUN5 reference. Separate Controls and Command Chart
captures retain their accepted label and title behavior. The blank 2P Controls
column reproduced from the untouched source state and remains known
state-resume behavior rather than a renderer regression.

The isolated worker ISO has SHA-256
`D624C39F0132FF5ED3BA4D60E99B78113AF85805D3870B072643B9400CC2B10B`
and boot CRC `A85C52F7`. Its 7,536-byte resident payload ends at `0x008F5A70`
and has SHA-256
`47EF54100642B25366FADF4A0D5C12B7255D3CF89456BD3F3DB5ACB056ED1101`.
The generated 4,084-byte v2 asset has SHA-256
`382AD202C1225326B59832BECE7A8AE61A2A69870B18B17D1F606B6C5152BE90`.
Deterministic fragment and relocation tables have SHA-256
`22F728E0C5E4AE279F8DE719636E1301CAB482891DDE6FAECA3BEDEE96D7EC84`
and
`CB45E870106EF9E95C29947922BEC5F4CC640DBCE044CC2AA9AEC8F60BA703C4`.
The grouped comparison sheets are
`@work/Font/artifacts/autofit_v2/practice_explanations/report/practice-explanations-02-04.png`
and
`@work/Font/artifacts/autofit_v2/practice_explanations/report/practice-explanations-05-07.png`.
The family is runtime-proven and enabled; the grids still await user
acceptance before work begins on another caller family.

Commit `e906ce0` placed the complete helper block at runtime
`0x003D3E00..0x003D4388` (file `0x2D3F00..0x2D4488`) inside the larger
common-zero interval `0x003D3DB6..0x003D5D30`. That interval is zero in the
clean ELF and was zero in all 16 states then sampled. A disposable ISO marker
audit also proved that markers at its start, middle, and end survive after a
fixed five-second boot settle. PINE becomes ready while the large boot ELF is
still being copied, so immediate reads of high file-offset caves can
transiently return zero and are not valid placement evidence. The later
Load-screen evidence below proves that boot-settle and sampled-screen survival
were nevertheless insufficient: the game clears this whole interval during a
transition that the original regression did not cover. Runtime scratch was
placed in the independently state-zero range `0x003FAD18..0x003FAE44`.

A full ten-state guarded regression covered Practice pause, Controls, Command
Chart, command explanation, Practice settings, Practice quit, character
return, Collection quit, Collection movie, and the no-memory-card prompt.
Controls and the wrapper-owned Practice/confirmation families retained their
matched results. Command explanation, Collection movie, and no-memory-card
overflow were separate unresolved caller families at that historical
boundary; their unchanged defects were not regressions from this port. The
later dedicated Collection Movie-list work resolves that family as documented
above. Confidence is **high** for the shared
measurement formula, hook boundaries, caller guards, and matched horizontal
result. That regression did not cover entry into Save/Load and therefore did
not establish persistent ownership of the helper interval.


## Practice Settings left-column completion

Evidence date: 2026-08-02.

The paired 2026-07-31 Practice Settings inputs are retained under
`@work/Font/inputs/sstates/batches/2026-07-31-practice-settings-ss1/` and
`@work/Font/inputs/sstates/batches/2026-07-31-practice-settings-ss3/`, with
matching extracted screenshots and provenance in their sibling input trees.
The ss1 state selects `Attack`; ss3 selects `Extra Hit Counter`.

Both pairs established one template-level left-column origin error across
selected and ordinary labels, not unique row defects. The overhaul now routes
the exact Practice heading and loop label callers through shared page formulas
while keeping the right value and explanation families separate. The final
main replay includes the corrected page without a large position, width, wrap,
or style discrepancy.
