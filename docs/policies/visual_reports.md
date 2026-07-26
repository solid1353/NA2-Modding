# Visual and task-report policy

## Accepted screenshot grid

- Screenshot comparisons are delivered as composed report-grid images, not as
  separate screenshots, file links, or internal tool previews.
- Every grid has `NUN5 reference` on the left and `Current NA2`/NA2.28 on the
  right.
- Every case occupies one row. Above the paired screenshots, show the game
  section, slot/case, status, and a concise finding or question.
- A grid may label a case `user verified` or `user accepted` only after the
  user explicitly confirms that exact displayed result. Until then, use a
  distinct factual status such as `implemented`, `agent validated`, or
  `awaiting user verification`; a matching comparison does not accept itself.
- Use a dark, low-glare background with light text for the report frame,
  headers, and metadata. Do not tint or otherwise alter the source screenshots.
- A grid may contain one row, but never only one screenshot.
- Larger reports split grids under visible game-section and screen-semantic
  headings and state the covered slots. Multiple chunks of the same semantic
  group remain under one shared heading; never present the report as an
  unsectioned image sequence. Emit the composed grids as actual conversation
  images visible to the user.
- A request for a report or grid requires immediate delivery of the actual
  composed grid images. Text-only status, promises to deliver, paths, links,
  and internal previews do not satisfy the request. Attach an existing current
  grid immediately; regenerate it first only when its imagery or metadata is
  stale.
- `view_image`, `Viewed an image`, and similar inspection-tool calls are
  internal inspection only and never deliver an image to the user. Deliver
  each grid in a user-facing commentary or permitted final message as an actual
  image attachment or an image embed using its absolute path, for example
  `![Grid](<D:\absolute path\grid.png>)`. Do not claim delivery or continue
  work until that message containing the visible grid has been sent. If it
  fails to render, retry the image delivery rather than performing more
  internal image views.
- When newer user evidence changes a case's slot, status, or remaining defect,
  regenerate the canonical grid from the retained task-owned inputs before
  reporting the update. Stale grid imagery or metadata is not an updated
  report.

## Completed selected-task report

For completed `TASKS.md` work, report:

- Files read.
- Files created or modified.
- Whether originals remained untouched.
- Scripts and commands used.
- Relevant sizes.
- Uncertainties.

This task report format does not apply to small direct changes.
