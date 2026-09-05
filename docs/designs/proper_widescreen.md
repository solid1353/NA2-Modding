# Proper widescreen

Status: Draft

The NUN6 comparison and mapped NA2 candidates are in the
[NUN6 widescreen reference](../features/nun6/rendering/widescreen.md).

## Contract

Proper widescreen means Hor+ 16:9 rather than stretched 4:3 or a crop that
loses vertical scene content.

| Layer | Required result |
| --- | --- |
| Output | Present the frame as 16:9 separately from game-memory geometry. |
| 3D projection | Gain horizontal field of view while retaining vertical composition. |
| Full-bleed 2D | Extend intended fades, masks, and backdrops to both new edges. |
| Bounded 2D | Preserve HUD, menu, text, prompt, and logo proportions and place them deliberately. |
| Cameras and effects | Keep culling, particles, shadows, cutscenes, and special cameras correct in the newly visible area. |
| Video | Give FMVs an explicit pillarbox, crop, or replacement policy instead of stretching them. |

## Implementation direction

- Replace the broad shared-writer patch with a persistent primary-renderer
  scope proven across renderer refreshes and state transitions.
- Treat primary 3D scale, the base 2D transform, transformed-2D counter-scale,
  full-bleed rectangles, bounded UI, cameras, effects, and media as separate
  layers.
- Use reference-mod full-bleed sites only after identifying their NA2 draw
  purpose and confirming the result at runtime.
- Do not copy reference-mod code or state whose lifetime and ownership are not
  established for NA2.

## Validation

Run with PCSX2's 16:9 presentation enabled and emulator widescreen cheats
disabled. Trace the primary renderer's scale and 2D matrices across boot,
menus, overlays, battle, cutscenes, and return transitions. Test each candidate
coefficient and draw cohort independently.

Compare matched 4:3 and 16:9 captures across boot, menus, selection screens,
battle and Practice, ADV, Collection, effects, transitions, and every FMV
class. Accept a site only when it adds intended horizontal coverage, preserves
vertical composition and bounded-element proportions, fills required edges,
and introduces no newly visible garbage or premature culling.

## Open decisions

- Primary-renderer scope across state transitions.
- Final horizontal scale and screen-space transform.
- Which mapped draw sites require full-bleed expansion or bounded placement.
- Camera, culling, and effect changes required by the wider view.
