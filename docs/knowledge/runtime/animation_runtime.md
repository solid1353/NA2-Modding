# Animation runtime

This document records playback and evaluation in retail NA2
(`SLPS-25837`). Addresses below are resident `SLPS_258.37` EE addresses.
Function names are the preserved analysis names; semantic names are working
descriptions. Complete-file identities belong to
[Retail game file identities](../game/files/file_identities.md#address-conventions).

## Research coverage

- **Assigned scope:** Playback and evaluation after parsing: cursor advancement, absolute seeks, looping, interpolation, transform/bone evaluation, blending, restart/stop and event-crossing semantics.
- **Exploration depth:** Resident algorithms only: complete advance, seek, reset, binding, typed evaluator allocation/initialization, transform application, blend construction/evaluation/destruction and queued-event delivery were read in decompilation. Instruction-level corroboration covers cursor branches, curve arithmetic, local-matrix writes, alternate/deferred output and ownership teardown. Neighboring model, timer, scene-owner and generator-action evidence is linked rather than duplicated.
- **Confirmed coverage:** Shared descriptors and per-player work; unsigned 1/256-frame advance, end/clamp/loop ordering, absolute-seek branches including active-blend cancellation, strict segment-crossing rules, linear/cubic/quaternion/color evaluation, sampled-endpoint blending, conditional target reuse, parent-map/local-transform application, queued-event lifetime and reverse encounter order, and distinct rewind/removal operations.
- **Unresolved or untested:** The `0x0104` branch's producer/reachability and scratch-index state; the alternate output format's broader owner; complete consumers of the temporarily cleared seek callback; gameplay meaning of event payload words; producers of player flag `+0xF7 & 0x10`. Exceptional cursor/frame-count/curve-duration inputs and caller guarantees are not established. There is no observed instance state or scheduling frequency for these algorithms.
- **Deliberate exclusions and overlap:** [CCS runtime](../game/files/ccs_runtime.md#animation-track-parsing) owns parsing/container lifecycle; [Character asset tables](../game/character_assets.md#animation-name-and-0x4c-stride-tables) owns selection; [Scene playback callers and owners](scene_playback_owners.md) owns caller inventories; [Model runtime](rendering/model_runtime.md) owns hierarchy/palette construction; [Timer primitives](timer_primitives.md) owns action-frame arithmetic; [Effect-generator commands](effect_generator_commands.md) owns downstream actions/attachments. This document owns animation-player algorithms and their mutable state.
- **Evidence limitations:** Findings are static. Preserved signatures omit arguments, and some instructions are not analyzed as code. Negative xrefs are not whole-program absence proofs. Scheduling frequency and user-visible results are not established by these algorithms alone.

## Descriptor and player separation

**Observation:** `FUN_001B1470` constructs a tag-`0x0700` animation resource.
`FUN_001A29D0` builds its record/track relation table. Runtime binding is a
separate operation in `FUN_001B99B0`, which builds 16-byte per-track entries,
materializes targets, initializes typed evaluator work and resets the cursor.
Parsing layout and tag interpretation remain in the linked CCS document.

| Owner and offset | Contract established by the inspected producer/consumer |
| --- | --- |
| Animation `+0x08` | Owning CCS container. |
| Animation `+0x0C` | Frame count `F`; advance uses terminal position `(F-1)*256`. |
| Animation `+0x14` | Packed command stream start. |
| Animation `+0x18/+0x1C` | Array/count of eight-byte `{record, typed-key descriptor}` pairs. |
| Animation `+0x24` | Halfword relation map; `0xFFFF` represents no matching relation. |
| Animation `+0x28` bit `1` (`0x02`) | Loop policy tested by the player at completion. |
| Player `+0x90` | Bound animation descriptor. |
| Player `+0x94` | Halfword step used by the inspected fighter caller; the advance API itself accepts a full unsigned word. |
| Player `+0x96/+0x98` | Published fraction (`cursor & 255`) / integer frame (`cursor >> 8`). |
| Player `+0xA0` | Embedded reader used for the packed command stream. |
| Player `+0xE0/+0xE8` | Per-advance command-event list / callback used by `FUN_001BB190`. |
| Player `+0xEC` | Unsigned fixed-point cursor. |
| Player `+0xF0` | Next stream boundary returned by command dispatch. |
| Player `+0xF8` | Optional animation-attached generator-action manager. |
| Player `+0xFC` | Per-track runtime entries: target `+0`, resolved record `+4`, type halfword `+8`, flags byte `+0xA`, evaluator work `+0xC`. |
| Player `+0x108` | Bound container, temporarily supplied with this player's reader/table during stream dispatch. |
| Player `+0x114` | Optional blend object; its first word is duration in whole frames. |

**Ownership observation:** `FUN_001B7570` destroys the blend object, tears down
track targets/evaluator work and action-manager state, and destroys the
embedded reader. It does not free the animation descriptor through
`FUN_0019D3A0`; the CCS record destructor owns that resource. A player's cursor
and work therefore cannot be treated as fields of the shared animation.

## Advance and end behavior

**Observation:** `FUN_001BB210(player, delta, alternate_output)` uses unsigned
`old_cursor + delta`. One whole animation frame is `256` units. The API does
not establish a reverse-play contract or overflow guard. At entry it frees
the previous event list (`FUN_001A2990`) and clears player `+0xE0`.

While a blend is active, a cursor below `duration*256` is sent only to
`FUN_001B9480`; the cursor/fraction/frame are published and the call returns
zero. At the duration boundary the blend is destroyed, its duration is
subtracted and only the residual step advances the incoming animation.

Normal evaluation clamps the requested cursor to `(F-1)*256` and removes
overshoot from the delta passed to `FUN_001B8410`. The typed curves receive
that delta even when no integer frame changes. The attached action manager
receives the difference between the old and new integer frames unless player
flag `+0xF7 & 0x04` suppresses it.

When the integer frame changes, the player advances every materialized
`0x0E00` effect by that integer difference, installs its container/table/reader
context and dispatches packed stream commands through `FUN_001B4F80` if the
new frame reaches `+0xF0`. The container reader pointer is restored afterward.
Loop handling is inside this integer-change branch, not a separate unconditional
terminal check.

**Observation:** For a looping descriptor, completion destroys any remaining
blend, resets all typed evaluator work through `FUN_001BB540`, rewinds the
reader to animation `+0x14`, restarts the attached action manager unless
suppressed, clears player `+0xF7` bit `7`, and zeros `+0xF0/+0xEC/+0x96/+0x98`.
The call returns zero. It discards terminal overshoot rather than carrying it
into the next cycle, and does not immediately dispatch the next cycle's frame
zero in this branch. Resetting work/cursor does not reapply frame-zero transforms
here: the target retains the just-written terminal transform until a later
evaluation or another writer changes it.

For a non-looping descriptor, reaching the terminal cursor normally returns
one. Within the integer-change branch, player flag `+0xF7 & 0x10` replaces
that result with `FUN_001BB4F0`:
the action-manager completion result when actions are enabled/present, or one
otherwise. Thus geometric end and action-manager completion are distinct.
A terminal zero-step call skips this replacement and returns the clamp result.
Producers of flag `+0xF7 & 0x10` are not established;
[Support mechanics](../gameplay/characters/support_mechanics.md#animation-result-and-common-state-transitions)
records one owner that consumes this completion result.

**Evidence:** Complete disassembly `0x001BB210..0x001BB4E4`, with clamp at
`0x001BB2C8..0x001BB300`, integer-change gate at `0x001BB334..0x001BB350`,
stream dispatch at `0x001BB398..0x001BB3EC`, and end/loop selection at
`0x001BB3F0..0x001BB4A0`; decompilation of `FUN_001BB4F0`,
`FUN_001BB540`, `FUN_001B99B0` and `FUN_001B7570`.

## Absolute seeks and evaluator reset

**Observation:** `FUN_001BB5C0(player, target, flags)` accepts a target in the
same 1/256-frame units. Without an active blend, a forward target calls
`FUN_001BB210(target-old_cursor, 0)`. A backward target first resets every
typed evaluator, rewinds the packed stream, restarts enabled generator actions,
clears player `+0xF7` bit `7`, zeros the stream boundary and cursor publications,
then calls the same advance API with `target` as its delta. It reconstructs
from zero rather than walking key pointers backward. End clamping and loop
policy still apply because the seek uses normal advance.

An equal target frees and clears `+0xE0`, returns zero, and does not evaluate
curves or dispatch commands. Before these comparisons, an active blend is
destroyed and the comparison origin is set to zero. That branch does not itself
zero the published cursor: in particular, seeking to zero after canceling a
blend takes the equal-target return. For a positive target, it passes that
target as a delta without the backward-reset branch. `FUN_001BB210` still
loads the retained `+0xEC`, so its requested cursor is stored blend cursor plus
target before end/loop handling; typed curves receive the target delta, subject
to terminal clamping. This is the observed instruction contract, not evidence
that canceling a blend fully restarts the player.

Flags bit `0` controls temporary clearing of callback pointer `+0xE8` during
the delegated advance; it is restored afterward. This does not establish
suppression of event-list construction, whose handler does not check `+0xE8`.

**Observation:** `FUN_001BB540` walks all `animation +0x1C` player entries and
calls `FUN_001B7BB0` for each nonnull evaluator allocation. That function resets
every dispatched typed descriptor: `0x0102`, `0x0202`, `0x0503`,
`0x0603/05/07/09`, and `0x1902`. Vector initializer `FUN_001A62B0`, rotation
initializer `FUN_001A4960`, scalar initializer `FUN_001A6900` and packed-color
initializer `FUN_001A6D70` restore initial values, zero local times and reinstall
initial segment pointers. Reset does not allocate new curve data.

**Evidence:** complete seek disassembly `0x001BB5C0..0x001BB6E4`, reset walker
`0x001BB540..0x001BB5BC`, and decompilation of `FUN_001B7BB0` and the four
initializer families.

## Packed command crossing and event delivery

**Observation:** `FUN_001B4F80(container, boundary, target)` reads sequentially
while `boundary <= target`; a `0xFF01` marker replaces `boundary` with its
payload. The next marker beyond the target ends the pass and becomes player
`+0xF0`. Consequently a large forward advance consumes commands at intervening
markers; it does not select only the target's command block. The reader cursor
already points past the last read marker, so the caller's old integer frame is
not a request to replay that frame's block. Packed commands are processed after
typed curve evaluation in `FUN_001BB210`.

Tag `0x0108` calls `FUN_001B69B0(container, current_marker)`, which consumes
three words and allocates a `0x18`-byte event node:

| Event offset | Observed value |
| --- | --- |
| `+0x00` | Previous list head. |
| `+0x04/+0x08` | Second and third payload words, retained unchanged. |
| `+0x0C` | Current integer frame marker. |
| `+0x10` | Runtime target resolved from the first payload word through `FUN_001B56B0`. |
| `+0x14` | Target type halfword returned by `FUN_001B6A80`. |

A nonzero container `+0x64` directs the node to that player's `+0xE0`; otherwise
the stream play context's `+0x0C` owns it. Each node is prepended, so
`FUN_001BB190(player, callback_argument)` traverses the retained events in
reverse encounter order. It invokes `+0xE8(node, callback_argument)` only when
both the callback and list are nonnull. Delivery is a separate call from advance;
the inspected fighter consumer calls it after advance and attachment service.
The following advance clears the old list even for a fractional step, a zero
step or a blend-only step. Repeated callback calls before another advance can
therefore revisit the same nodes; delivery itself does not remove them.

**Inference (high confidence):** a backward seek to a positive target can
recreate earlier packed events because it rewinds then dispatches forward. It
is not a pure pose sample. The current code establishes event payload/order,
not the gameplay meaning of the two retained words.

**Evidence:** `FUN_001B4F80`, `FUN_001BB190`, `FUN_001BB200` and
`FUN_0024D1C0` decompilation; complete event-builder disassembly
`0x001B69B0..0x001B6A7C`. Command payload parsing remains owned by
[CCS streamed playback](../game/files/ccs_runtime.md#frame-stream).

## Typed curve evaluation

**Observation:** `FUN_001B8020` allocates one evaluator block per typed track,
with a `0x10`-byte prefix followed by its channel work areas. The prefix's first
word points to the parsed typed descriptor. Channel modes are packed in the
descriptor's `+0x04` word; the evaluator receives a delta, not an absolute frame.
The source file's compression selections are converted to runtime mode `5`
by `FUN_001A8000`; runtime modes must not be read as the original file selectors.

| Channel | Initializer / evaluator | Mode and work size |
| --- | --- | --- |
| Translation vector | `FUN_001A62B0` / `FUN_001A5DE0` | `0`: zero vector/no work; `1`: borrowed constant pointer (`0x10`); `2`: linear accumulated value and relative time (`0x20`); `4`: cubic control-point cache (`0x50`); `5`: compact vector endpoints and absolute local time (`0x40`). |
| Scale vector -> diagonal matrix | `FUN_001A62B0` / `FUN_001A5AB0` | Identity by default; modes `1/2/4` use the same vector work sizes. This scale evaluator has no mode-`5` branch. |
| Rotation -> matrix | `FUN_001A4960` / `FUN_001A4250` | Identity by default; `1`: constant matrix (`0x40`); `2`: accumulated matrix and relative axis/angle segment (`0x50`); `4`: float quaternion endpoints (`0x50`); `5`: packed quaternion endpoints (`0x50`). |
| Scalar | `FUN_001A6900` / `FUN_001A67D0` | `0`: caller-supplied default; `1`: constant (`0x10`); `2`: linear base/delta with relative time (`0x10`). |
| Packed color word | `FUN_001A6D70` / `FUN_001A6C30` | Modes `1/2`, `0x10` work; endpoint words are converted to RGB vectors before weighted interpolation. |

**Observation — linear curves:** scalar work is `{float base, uint elapsed,
segment_pointer}` in its first 12 bytes. Vector work is `{float XYZ base,
uint elapsed, segment_pointer}`. Each segment contains unsigned fixed-point
duration and value delta (eight bytes for scalar, `0x10` for vector). Advancing
adds the supplied delta to elapsed, consumes whole segments only while
`duration < elapsed`, subtracts their durations and adds their value deltas to
the base. It evaluates the current segment as
`base + segment_delta * (elapsed/duration)`. At equality it retains the current
segment and evaluates its endpoint (`t=1`); it switches on a subsequent positive
step. Scalar `0x001A6810..0x001A68EC` and vector
`0x001A613C..0x001A6260` prove integer time loads/arithmetic, despite the
decompiler's misleading float-pointer casts.

**Observation — cubic vectors:** mode `4` maintains an absolute local cursor
at work `+0x40`, and advances its `0x2C`-byte source-key pointer at `+0x44`
while the next key's whole-frame time times `256` is below that cursor.
For `t=(cursor-start*256)/((end-start)*256)`, both vector and scale evaluators
form the four weights `(1-t)^3`, `3*(1-t)^2*t`, `3*(1-t)*t^2`, `t^3` and
multiply the cached control-point columns by them. This is cubic Bezier
evaluation, not four independently linearly blended values.

**Observation — compact vectors:** mode `5` keeps absolute local time at work
`+0x30`, a halfword time-table pointer at `+0x34` and eight-byte packed-value
pointer at `+0x38`. Crossing an interval advances both pointers, decodes signed
XYZ halfwords using the packed low-nibble power-of-two scale, caches start and
endpoint difference, then linearly interpolates. The time-table values are
whole frames multiplied by `256` during comparison. These compact values are
runtime storage made by the parser, not compressed halfwords read from the
original file.

**Observation — rotations:** mode `2` consumes full relative rotations while
segment duration is below local elapsed, multiplies them into its accumulated
matrix, then applies only `elapsed/duration` of the current axis/angle rotation.
`FUN_0010BF50` constructs a rotation matrix from axis XYZ and angle; this path
does not linearly interpolate three Euler components during evaluation.
Modes `4/5` keep an absolute local cursor at work `+0x40` and a halfword time
pointer at `+0x44`; endpoint storage advances by `0x10` or eight bytes per key.
They flip the destination quaternion when the dot product is negative. Below
dot `0.95` they use sine-weighted quaternion interpolation; otherwise they use
`q0 + t*(q1-q0)`. `FUN_00181020` converts the result to a matrix using
`2/dot(q,q)`, so the matrix conversion accounts for a non-unit result. The
compact route uses the component scales at `0x005BF900` (`1/16384` for XYZ,
approximately `0.0000958738` for W); these are not four identical scales.

**Observation — colors:** mode `2` retains packed endpoint words rather than
adding numeric word deltas. `FUN_0019F380` interprets a zero high byte as RGB
bytes scaled by `1/255`; a nonzero high byte selects its hue/saturation/value
conversion branch. `FUN_0019F2D0` sums the two converted endpoint vectors with
weights `1-t` and `t`. This channel is not integer interpolation of a packed
word and does not establish interpolation of alpha.

**Evidence:** complete disassembly of `FUN_001A4250`
(`0x001A4250..0x001A495C`), `FUN_001A5AB0`
(`0x001A5AB0..0x001A5DDC`), `FUN_001A5DE0`
(`0x001A5DE0..0x001A62A8`) and `FUN_001A67D0`
(`0x001A67D0..0x001A68F4`); decompilation of the corresponding initializers,
size selectors `FUN_001A4CF0/64E0/6960/6DD0`, `FUN_001A8000`,
`FUN_0010BF50`, `FUN_00181020`, and `FUN_0019F2D0/380`; raw scale bytes at
`0x005BF900..0x005BF90F`. Source reading/padding is owned by
[CCS animation-track parsing](../game/files/ccs_runtime.md#animation-track-parsing).

## Animation-to-animation blending

**Observation:** `FUN_001B99B0(player, incoming_animation, blend_frames)` resets
the incoming cursor/stream boundary and builds its target/evaluator table.
A zero third argument destroys any previous blend without constructing one.
A nonzero third argument with a prior animation compares old/new target names
for types `0x0100`, `0x0E00`, `0x0500`, `0x0600` and `0x1900`, through
`FUN_00116740` and `FUN_00116480`. Names are compared after the byte offset
selected by player `+0xF6` (zero when it exceeds the name length). Matching
is by hash and case-sensitive suffix text, not merely row index or pointer.
Matched incoming entries copy the old target handle, record/type and flags.
Later binding still materializes entries whose copied flags have bit `0` set;
retention of the old target is therefore conditional. Both matched and
unmatched entries pass through the remaining composition/ownership binding.

The blend header is `0x0C` bytes: duration word `+0`, count halfword `+4`,
array of blend-item pointers `+8`. `FUN_001B79B0` constructs an item only when
both evaluator pointers are nonnull and the old descriptor is `0x0102`; the
other candidate types do not automatically obtain an interpolation item.
It samples both evaluators with delta zero: the old current pose and incoming
initial pose. It allocates `0x90` bytes and initializes through virtual slot
`+8`; destination descriptor type is not separately checked in this helper.

The installed vtable `0x005D9EB0` has initializer `FUN_001A2E70` at `+8`
and evaluator `FUN_001A2BB0` at `+0x0C`. The initializer retains the target
entry, start position/scale/alpha, their endpoint differences and a quaternion
blend cache. `FUN_001A2F60` extracts quaternions from endpoint matrices, flips
the destination for a negative dot product, and chooses sine-weighted
interpolation below dot `0.95` or normalized linear interpolation otherwise.
Translation, scale and alpha use `start + t*delta`.

`FUN_001B9480` evaluates each nonnull item with
`t=blend_cursor/(blend_frames*256)`, composes its rotation/scale/translation,
and applies it to the bound model or effect node. During that interval
normal typed curves, packed commands and generator-action advancement do not
run: the early return in `FUN_001BB210` holds the incoming animation at its
initial pose while the blend cursor progresses. This is a transition between
sampled endpoints, not two independently running timelines.

`FUN_001B7670` frees every nonnull blend item, frees the pointer array and
optionally frees the header. The retained entry points into the incoming
player table; the interpolation cache contains copied endpoint values rather
than pointers to old evaluator work. Binding releases the old evaluator table
after building the new table and blend cache.

**Evidence:** `FUN_001B99B0`, `FUN_001B9480`, `FUN_001B7670`,
`FUN_001BA9C0`, `FUN_001A2E70`,
`FUN_001A2F60`, `FUN_001A2BB0`, `FUN_00116480/16740/16810`
decompilation; complete blend-item disassembly `0x001B79B0..0x001B7B44`
and vtable words `0x005D9EB0..0x005D9EBF`.

## Target binding and transform application

**Observation:** animation binding can reuse existing composition nodes.
`FUN_001B99B0` first resolves every pair's record and temporarily publishes its
runtime-entry address at record `+0x34`. Existing compositions are supplied
through the player's linked list at `+0xE4`. With player `+0xF7 & 0x02` clear,
their `0x0100` children are bound by that source-record lookup. With the bit
set, incoming `0x0100/0x0E00` records are matched to the supplied composition
children by the same name/hash helpers and `+0xF6` offset used for blending.
The inspected name path has scratch capacity for `0x80` entries; its count
continues growing beyond that storage check, so the body itself does not
establish safe handling of larger inputs. No claim is made that retail inputs
exceed that capacity.

Entry flags at `+0x0A` separate target ownership, parent attachment and draw
submission: bit `0` drives materialization and destruction, bit `1` applies
the animation relation map, and bit `2` enables `FUN_001BB790` submission for
model/effect entries. Borrowed composition targets receive flags `2` or `6`,
not ownership bit `0`. Binding clears the temporary record `+0x34` rows when
it finishes; they are construction context, not permanent animation state.

For each entry with attachment bit `1`, animation `+0x24` selects the parent
entry. `0xFFFF` selects the player node; otherwise binding reads that entry's
target. `FUN_001BA810` stores the parent at target `+0x80`. Model palette and
composition-child construction are owned by
[Model hierarchy and matrix lifetime](rendering/model_runtime.md#composition-hierarchy-and-matrix-lifetime).

**Observation:** the ordinary `0x0102` route in `FUN_001B8410` evaluates
translation, rotation, scale and alpha, using alpha default `1`. For a model
or effect it forms `rotation * scale` through `FUN_0010BA60` /
`FUN_00152020`, then adds the translation vector to the matrix's last column
through `FUN_001B9460` / `FUN_00152270`. `FUN_001B9430` copies the resulting
four columns to target local matrix `+0x40..+0x7F` and sets dirty byte `+0x8D`
to one; `FUN_001B5D20` receives alpha separately. Accumulated bone matrices
are produced by the linked model hierarchy's `parent_world * local` algorithm,
not written independently for every animation curve.

`FUN_001B5D20` stores alpha at target `+0x88`. When target byte `+0x8C` bit
`0` is clear it also writes `+0x84`; otherwise it sets that byte's bit `2`.
This alpha contract is separate from matrix dirty byte `+0x8D`.

A nonnull model target `+0xA0` overrides scale diagonals from that block's
`+0x10/+0x14/+0x18`, and multiplies translation by its `+0x0C`. The same
override exists in the blend application path. Effect application also copies
the evaluated X/Y scale to target `+0xA0/+0xA4` and can request effect restart
through `FUN_001956D0` according to its prior state. The broader effect
lifetime belongs to [Particle runtime](rendering/particle_runtime.md).

### Alternate output and deferred branch

When `alternate_output` is nonzero, a model record found by `FUN_001C7670`
routes its pose to a separate output object instead of the local-node write.
`FUN_001C7360`, `FUN_001C7410` and `FUN_001C7580` lazily allocate
`0x44`-byte rows in channels at output `+0x94/+0x98/+0x9C` and write position,
Euler rotation values and scale diagonals. Rotation mode `2` extracts angles
from the evaluated matrix and converts to degrees; mode `1` uses the source
constant Euler triple; other modes write zero rotation values on this route.
Alpha is routed through output `+0xA0` to `FUN_001C7860`, whose rows have
stride `0x1C`. Missing record matches fall back to ordinary node application.
Normal advance calls `FUN_001C6D80` afterward; blend-only advance returns
before that finalization. The output format's broader owner/use is unresolved.

**Observation / limitation:** `FUN_001B8410` contains a deferred `0x0104`
branch: it queues those entries, evaluates position/rotation after the ordinary
entries, reads two signed indices from scratch `+0x138/+0x13A`, refreshes the
selected targets, composes a transform and applies alpha zero. The inspected
body has no stores establishing those scratch indices. The inspected parser
`FUN_001A6E00` has no `0x0104` dispatch, transform parser `FUN_001A8000`
constructs `0x0102`, and neither evaluator allocator `FUN_001B8020` nor reset
`FUN_001B7BB0` supplies a `0x0104` channel branch. This establishes a code
branch, not a reachable retail track contract. Its producer and valid state
remain unresolved.

**Evidence:** `FUN_001B99B0`, `FUN_001BA810`, `FUN_001B8410`,
`FUN_001B9460`, `FUN_00152270`, `FUN_001C7360/7410/7580`,
`FUN_001A6E00/8000`, `FUN_001B8020/7BB0` decompilation; matrix multiplication
instructions `0x00152020..0x00152060`, local-matrix setter
`0x001B9430..0x001B945C`, alpha setter `0x001B5D20..0x001B5D4C`,
alternate-output path `0x001B8668..0x001B8954`, deferred application
`0x001B9278..0x001B939C`, and alpha row writer
`0x001C7860..0x001C78E4`.

## Restart, hold and removal boundaries

| Operation | Established local contract |
| --- | --- |
| Bind `FUN_001B99B0` | Build new per-track state, reset cursor/stream publications and select the incoming descriptor. It does not run a normal advance at the end of its body. |
| Backward absolute seek / descriptor loop | Reinitialize typed work and rewind commands; restart enabled generator actions before further playback. |
| Terminal non-looping advance | Clamp to the last pose and return completion; retain the descriptor and track table. A subsequent zero-step call still evaluates curves with delta zero and clears the prior events. |
| `FUN_001BC680` | Immediately release generator-action runners through `FUN_001AB8E0`; it does not clear the animation descriptor, track table or cursor. |
| Track-table teardown `FUN_001B7750` | Destroy targets only when entry ownership bit `0` is set; free all evaluator work and the table, then zero player `+0xFC`. It does not clear `+0x90` or rewind the cursor. |
| Player destruction `FUN_001B7570` | Release blend, track state, action manager, event list, material state and reader; free composition-list links without destroying the supplied compositions through that list walker. |

These operations have distinct effects. Owner-controlled holds and explicit
restart selection belong to
[Scene playback owners](scene_playback_owners.md#fighter-animation-ownership).
The separate streamed CCS worker's stop/restart contract belongs to
[Streamed playback](../game/files/ccs_runtime.md#streamed-playback-sp-skill-play).

Generator actions advance by the integer-frame difference in this player,
before packed command dispatch. Their rewind retains generator allocations;
replacement/removal uses separate runner-release paths. The command/gate,
anchor and immediate/deferred release contracts remain in
[Effect-generator commands](effect_generator_commands.md#scheduling-and-owner-gates).
The streamed CCS owner's raw rate argument to the same manager is a different
count contract and must not be inferred from this animation player's `>>8`.

Gameplay frame predicates such as `FUN_00211A20` operate on a distinct
fractional timer block, with previous/current/predicted values and flags;
they are not queries of this player's `+0xEC`. Their arithmetic and consumer
gates belong to [Timer primitives](timer_primitives.md#event-and-interval-predicates).
This separation matters for event consumers: advancing a visual animation
alone does not establish how an action-frame predicate was armed or scheduled.

**Evidence:** `FUN_001B99B0`, `FUN_001BB210`, `FUN_001BB5C0`,
`FUN_001BC680`, `FUN_001B7570`, `FUN_001B7950` and `FUN_00211A20`
decompilation; complete track teardown `0x001B7750..0x001B78FC`.
