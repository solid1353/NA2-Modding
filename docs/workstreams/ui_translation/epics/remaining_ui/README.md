# Remaining UI Translation epic

Current report snapshot: 2026-07-26.

Every grid shows the official NUN5 reference on the left and Current NA2.28 on
the right.

## Remaining subtasks

1. Battle Results screen 2: labels, title, footer, and moving clouds are fixed;
   the red rank text remains vertically misregistered inside the stamp. A
   screen-space Y trial was disproven and reverted; resume at the loaded
   texture/CLUT binding or cached GS packet.
2. Character Items transition: the shared resident-renderer correction is
   implemented and agent-validated across the five paired phases; explicit
   user verification remains pending.

## User-accepted completed cases

- Cross/Triangle labels: every preserved pair (original slots 1-5 and newer
  slots 1-3) was explicitly confirmed fixed by the user on 2026-07-26.

## Report grids

### Battle results

![Battle Results screen 2](02-battle-results-2.png)

### Character items

![Character Items transition, slots 1-3](03-items-slots-1-3.png)

![Character Items transition, slots 4-5](04-items-slots-4-5.png)
