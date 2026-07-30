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
- Every grid must represent the real captured output exactly. Grid framing may
  place complete captures on a larger canvas and add labels outside them, but
  it must preserve every source capture at 1:1 pixels. Never resize, resample,
  smooth, stretch, retouch, reconstruct, or crop relevant evidence.
- A panel labeled `Current NA2` or `Current NA2.28` must be an untouched capture
  from the exact integrated build or ISO claimed by the report. Verify and
  retain that build/ISO identity with the capture provenance before creating
  the grid. A capture from another build, a stale runtime state, a development
  injection, a mockup, an expected render, or a reconstructed panel may not
  appear under that label.
- Development-injection output may be shown only when explicitly labeled
  `runtime-injected candidate` or an equally unambiguous candidate status. It
  proves only that candidate's captured runtime appearance; it does not prove
  the integrated ISO result and must not be described as current integrated
  output.
- Desired appearances and mockups may be retained and compared, but only as
  separately labeled targets. Never place them in a result position, label
  them `Current`, or present them as post-change runtime evidence.
- `Agent validated` means the displayed capture itself proves the exact claim
  made by the grid. An integrated-output claim requires a capture from that
  exact integrated build/ISO; compile or link success, direct-injection output,
  unit tests, and captures from another build cannot substitute for it.
- Before delivery, compare each grid panel against its original source capture
  at native resolution. If the grid changes apparent glyph height, width,
  spacing, origin, line breaks, clipping, or any other visible result, the grid
  is invalid and must be regenerated.
- A grid may contain one row, but never only one screenshot.
- Result grids use only actual post-change output evidence for the reported
  implementation. Never place source, donor, baseline, pre-fix, preserved
  input, or expected-reference screenshots in a result position or attach
  their grid beneath a result report in a way that represents them as output.
  If no post-change output exists, state that validation remains pending and
  do not attach an input grid as the result.
- Larger reports split grids under visible game-section and screen-semantic
  headings and state the covered slots. Multiple chunks of the same semantic
  group remain under one shared heading; never present the report as an
  unsectioned image sequence. Emit the composed grids as actual conversation
  images visible to the user.
- A request for a report or grid requires immediate delivery of the actual
  composed grid images. Text-only status, promises to deliver, paths, links,
  and internal previews do not satisfy the request. Attach an existing current
  grid immediately; regenerate it first only when its imagery or metadata is
  stale. Check the current task's recorded report state and expected artifact
  locations before declaring it unavailable. If actual post-change imagery
  does not exist, the next response must instead be `Cannot produce report
  grid: <exact reason>. Missing: <exact post-change input>.` Send that response
  immediately; afterward follow the active work-mode rule. Do not build,
  launch, investigate, or attach input imagery before the response.
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
