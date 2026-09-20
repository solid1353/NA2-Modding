# Battle Results rematch

Implementation candidate, pending user acceptance.

`features.general.battle_results_rematch` adds **Circle Rematch** at the left
of the Free Battle results summary footer. It is enabled in the base
configuration. Cross Next and Square Display details retain their existing
actions. Rematch becomes actionable at the summary's native acceptance point;
the details page retains its own controls.

Circle finishes the displayed result through the native acceptance and fade
sequence, then starts the same matchup again. The completed match remains in
the session win/loss/draw score and winner streak. Rematch does not add the
outcome again. Characters, costumes, jutsu, supports, stage, and the current
battle rules are retained. The ordinary per-battle health, timer, and metric
initialization runs for the new battle.

## Implementation

`general.battle_results_rematch` owns the runtime hooks, label asset, and
payload under `na228_builder/patches/general/`. The feature is scoped to the
Free Battle manager and its current result object. Its input and presentation
target the localized base configuration's Cross Next mapping and English UI
assets.

The prompt follows [Mode Select's Mod prompt](../mod_settings.md):

- `rematch_label.png` is a 96-by-24 indexed image with black lettering and a
  cream outline. Its indices use the bundled `TEX_xninka` palette.
- Construction copies the label into the transparent rectangle `(0,0,96,24)`
  of the loaded results atlas and re-uploads that texture. The builder embeds
  the vertically flipped pixels in the shared resident payload.
- `vs.ccs` is borrowed if already loaded, or queued alongside the native
  results resources in outer state 18. The native resource fence completes
  before the results entrance starts; summary initialization only looks up
  the loaded archive and creates the badge sprite.
- That sprite draws the Circle badge from `TEX_vs_t01`, rectangle
  `(5,233,22,22)`. The label samples `(8,0,80,24)`, including its full outline.
  The badge is centered at `(137,356)` and the label at
  `(192,356)` in the summary footer context, relative to Next's X anchor.
  The badge-to-text gap is four units; the Rematch-to-Next gap is 22 units,
  matching the existing Next-to-Display-details gap. Existing actions stay put.
- The native Next draw is wrapped to append the badge and label. The badge
  batch is finalized immediately. The existing label sprite holds one
  rectangle, so its Display details batch is finalized before submitting
  Rematch; the results renderer then finalizes Rematch normally. Cleanup
  releases the badge before the native results contexts, and releases the VS
  archive only when this prompt queued it.

The native acceptance predicate remains the first check. A fresh Circle press
from the result's selected controller requests Rematch only on the summary.
Native acceptance performs its ordinary result commit and fade exactly once.

After the result presentation closes, the native state-3 reset runs. Its
selection clear is followed by restoration of the setup saved before the last
battle, from manager `+0x9C..+0x117` to `+0x20..+0x9B`. States 4 and 5 retain
their normal resource loading. At state 6, after the native transition is
ready, Rematch closes the transition and enters state 10 with the normal
three-count delay. States 10 onward perform battle loading and construction.
The session counter initialization in state 2 is never revisited.

The relevant retail ownership and state transitions are documented in
[match outcomes](../../knowledge/gameplay/match_outcomes.md). The patch adds
resident payload bytes and guarded ELF/BTL call replacements; it leaves the
source archive and existing binary sizes intact.

## Label asset

`na228_builder/patches/general/rematch_label.png` renders the complete word as
one coherent wordmark. Its proportions and baseline match the native Next and
Display details prompts, while its continuous cream edge matches the Mod
prompt, including the inner letter openings.

The 96-by-24 indexed image uses the bundled `XNINKA` palette, with beige RGB in
transparent edge pixels for texture filtering. Its full outline fits the
existing `(8,0,80,24)` sampled rectangle. Normal builds consume the checked-in
PNG directly.
