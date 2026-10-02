# Practice input recording and playback

This document records provisional research for an in-game Practice dummy input
recorder. No recorder or playback feature has been implemented. The inspected
retail code provides a per-side input-history and command-translation boundary;
direct gameplay readers also bypass that history. A complete recorder would
need to supply those readers at their own consumption boundaries. The inspected
paths do not establish an existing recording-slot or playback system.

## Research coverage

- **Assigned scope:** Research an IN-GAME Practice dummy input recording/playback feature, including input sampling/injection boundaries, per-side ownership, recording slots and useful playback/loop/randomization options, reset/stop lifetime, reproducibility limits and timing/RNG dependencies.
- **Exploration depth:** Static coverage of the history constructor/update,
  normalization, relative-angle calculation, translation, both-side cross-links,
  Practice status bridge, phase scheduler, fighter synthesis/AI/consumption order,
  direct contest/BTL input readers, command-history destruction, session
  reconstruction, ordered direction matching, and shared RNG wrappers. Slot,
  playback, storage, UI, and transition choices are assessed provisionally.
- **Confirmed coverage:** Native sample and side contracts, AI suppression and
  overwrite points, separate history/fighter/contest scheduling, known direct
  publication readers, destruction/rebinding boundaries, and shared random-state
  dependencies are established.
- **Unresolved or untested:** Full direct-reader scheduling coverage, playback
  lifetime, allocation budget, controls, loop/reset semantics, and synchronization
  between sample clocks remain unresolved. No implementation-ready full-recorder
  hook is established. Input playback alone does not establish identical results.
- **Deliberate exclusions and overlap:** Implemented Practice behavior remains
  owned by [Practice](../practice.md). Retail input and matcher contracts belong to
  [Controller input](../../knowledge/runtime/controller_input.md) and
  [Action commands](../../knowledge/gameplay/action_commands.md); native dummy
  policies belong to [Practice-mode knowledge](../../knowledge/gameplay/practice_mode.md).
- **Evidence limitations:** Findings are static. The preserved BTL import omits
  the `0x40`-byte header and contains incomplete function boundaries and xrefs;
  encoded overlay operands are live addresses. No native recorder has been
  proven, and absence from the inspected paths is not a whole-program proof.

## Evidence conventions and foundations

The evidence is unmodified NA2 v2.28 `SLPS_258.37` and `PRG/BTL.BIN`, identified
in [Retail game file identities](../../knowledge/game/files/file_identities.md).
Resident addresses below are live. BTL tables distinguish live address, preserved
Ghidra address, and complete-file offset, including the MWo3 header. GhidrAssist
read-only decompilation, disassembly, vtable reads, and raw bytes were used. The
normalizer and allocator have truncated defined boundaries; their complete
instruction ranges were corroborated through `get_data_at` without changing
the maintained analysis.

The existing [pause and restart investigation](../../knowledge/gameplay/pause_and_replay.md#replay-result-and-useful-negatives)
found no proven replay capture/playback mechanism in its bounded paths. That
negative does not establish that no such mechanism exists elsewhere.

## Input sampling and injection boundary

### Observed retail path

The native `ccCommand` object belongs to one side. Its `+0x60` stores side `0`
or `1`, `+0x64` points to that side's resident `0x78`-byte pad record, `+0x20`
is its fighter, and `+0x24` is the opposing fighter. The constructor at live
BTL `0x006EF600` allocates a circular array of `0x18`-byte records with capacity
`300 / system_context[+0x01]`. It is a rolling matcher history, not a proven
user-selected recording slot.

| Inspected operation | BTL live | Ghidra | File offset |
| --- | ---: | ---: | ---: |
| History constructor | `0x006EF600` | `0x006EF5C0` | `0x03B700` |
| Advance ring and calculate direction references | `0x006F0A00` | `0x006F09C0` | `0x03CB00` |
| Complete input-object update | `0x006F0EA0` | `0x006F0E60` | `0x03CFA0` |
| Normalize current sample and derive edges | `0x006EF3C0` | `0x006EF380` | `0x03B4C0` |
| Translate current/history input | `0x006EFDC0` | `0x006EFD80` | `0x03BEC0` |
| Practice dummy-status bridge | `0x008813F0` | `0x008813B0` | `0x1CD4F0` |

The complete update advances the current index, copies resident pad held,
pressed, released, left/right stick angles and magnitudes into the new record,
normalizes it against the previous record, then translates it. The relevant
sample fields are:

| History field | Size | Meaning |
| --- | ---: | --- |
| `+0x00` | 4 | Held native pad mask |
| `+0x04/+0x08` | 4 each | Press/release edges recomputed from adjacent held samples |
| `+0x0C/+0x10` | 4 each | Left/right stick angle |
| `+0x14/+0x15` | 1 each | Left/right stick magnitude |
| `+0x16` | 2 | Stride padding; not part of the sample contract |

Normalization applies a left-stick dead zone below `0x40`, remaps `0x40..0x7F`
to `((magnitude - 0x40) * 3) / 2 + 0x20`, retains larger magnitudes, and
reconciles analog direction with digital direction bits `0xF000`. It then
sets `pressed = current & ~previous` and `released = previous & ~current`.
Thus injecting only a pressed mask does not preserve native hold/release or
history matching. Injecting an already normalized sample before this normalizer
can apply the magnitude remap a second time.

The relative-angle updater reads fighter/opponent positions, fighter angle, and
the current camera-derived reference before translation. Reusing the same
physical-direction samples in a different spatial state need not produce the
same relative commands. Full matcher and binding details remain in
[Action commands](../../knowledge/gameplay/action_commands.md#battle-input-object-and-circular-history).

The translator suppresses logical output when the owning fighter's controller
nibble, bits `5..8` of halfword `+0x60`, is nonzero. It clears input-object
`+0xAC/+0xB0/+0xB4` while the ring still advances. The Practice status bridge
chooses the fighter opposite manager `+0x18`: active side `0` selects manager
`+0xDE8`; active side `1` selects `+0xDE4`. Manual clears that nibble, while
non-Manual installs kind `1` and can initialize the AI. Input source and dummy
controller ownership are therefore separate decisions.

Resident `0x00217320` subsequently copies command-object
`+0xAC/+0xB0/+0xB4` to fighter `+0x338/+0x33C/+0x340`. Fighter byte `+0x61`
bit `0x80` or byte `+0x62` bit `0` suppresses the triple. If both logical
`0x00001000` and `0x01000000` are present, it clears the latter. Playback input
would still be subject to these native eligibility and conflict rules.

### Provisional feature choices

A side-local source selection inside the complete input update is the strongest
ordinary fighter-history candidate observed so far. It could sample the
controlled pad during recording and feed stored held/stick values into the
dummy's native history during playback, leaving binding translation, multi-step
matching, and fighter arbitration authoritative. This is feasibility inference,
not a selected hook or accepted design; the direct readers below require
additional coverage.

Two representations remain viable: capture pre-normalization held/stick values
and use the native normalizer on replay, or capture normalized records and replay
after normalization with newly derived edges. These must not be mixed. Recording
the final logical mask alone would omit resident consumers that inspect native
history and would bind the recording to the recorded relative-direction and
binding decisions. Resident `0x0024CDA0` derives held/release behavior through
history matcher live `0x006EFC40`, and `0x0024CCD0` derives repeated-press
behavior through history counter live `0x006EFD90`. Both can modify command
`+0xAC` before the bridge. That proves the final triple is insufficient to
recreate the full native input path without also supplying its history.

### Gameplay input outside that history

Ultimate Jutsu contests consume shared pad publication through resident
`0x0036BF10`, called at `0x001F0918` after the dispatcher's primary phase
registries. First-mask bit `0x0400` and predicate `0x0036B6C0` gate this
separate update. The inspected human readers are:

| Reader | Source | Recording consequence |
| --- | --- | --- |
| Command `0x00362140` | Shared pressed at context `+0x84 + side*0x78` | Retains one decoded command, including while a positive local lockout delays processing; recognized new presses replace it |
| Combo `0x00364170` | Same shared pressed word | Also retains one decoded command; its rearm update can defer processing without clearing the sampled command |
| Timing score `0x00369510` | Same shared pressed word | A positive local lockout skips the read; this differs from Command/Combo retention |
| Turn `0x00364DF0` | Raw polar right-stick output, with left-stick fallback below magnitude `0x20` | Needs the pre-battle-normalization stick source at the contest's own update |

Contest initialization `0x0035E360` copies manager side-record bit `0x02`
into contest CPU bytes `+0x1A/+0x1B`. Changing only the fighter controller
nibble does not update those copied owners. The outer contest gates can skip
sampling even where a local decoded-command latch retains a previous sample.
Full source, gate, and latch evidence belongs to
[Controller input](../../knowledge/runtime/controller_input.md#gameplay-readers-outside-command-history).

Three BTL predicates independently resolve object side `+0x350`, read that
side's configured binding halfword `+0x02` through resident `0x001F3F10`,
and check it against shared pressed. Their human branches are not history
matcher calls:

| Live predicate | Ghidra byte entry | File offset |
| ---: | ---: | ---: |
| `0x00796A50` | `0x00796A10` | `0x0E2B50` |
| `0x007FF520` | `0x007FF4E0` | `0x14B620` |
| `0x00806680` | `0x00806640` | `0x152780` |

Their controlled-state alternatives can read object `+0x13C & 1` instead.
Call-site disassembly at Ghidra `0x007968A8`, `0x007FE124`, and
`0x00805054` confirms that a true result changes class-local counters or a
scalar, respectively `+0x148/+0x14A`, `+0xFF6`, and `+0xFF4`. Clearing
command history alone therefore does not reset all input-dependent state.
The complete enclosing controller roles and registry scheduling remain
unresolved; no character or action names are assigned to these predicates.

Consequently a full recorder needs side-local synthetic input for these
consumers as well as command history, with ownership and progression aligned
to each consuming phase. Consecutive battle held samples cannot always recover
core pressed: intervening polls can replace an edge before the next battle
sample, and battle normalization derives a different edge. Recording raw core
pressed at the relevant consumer step, or retaining a core publication stream
with phase alignment, are candidates requiring further scheduling evidence.
Writing synthetic values into the shared pad record would also expose them to
Start/menu readers, so it does not establish an isolated dummy source.

### Existing control bindings and entry controls

The current [Controls battle input](../controls.md#battle-input) adds binding and
history consumers to the native path. Its
[builder hook map](../controls.md#builder-hook-map) includes BTL file offsets
`0x3C02C`, `0x3B8F0`, `0x3BD40`, `0x3BE90`, and `0x3C6AC`, plus resident
substitution checks. A proposed source injection should preserve those
consumers; replacing the translator wholesale would require reconciling the
existing hooks. No hook composition has been implemented or verified here.

The inspected native Practice menu's
[17-row schema](../../knowledge/gameplay/practice_mode.md#rows-local-values-and-manager-storage)
contains no recording-slot or playback row. Its absence is bounded menu evidence.
No menu extension or entry shortcut is selected. Controls permits rebinding the
available buttons, including those unbound by default, so a recorder cannot
assume a permanently free Select, L3, or R3 button. Menu-based controls or an
explicit shortcut assignment are provisional choices with their own input and
confirmation behavior to define.

## Per-side control ownership

### Observations

Live BTL setup `0x00709480` (Ghidra `0x00709440`, file `0x055580`) constructs
both side inputs and cross-links fighter `+0x24` to its `ccCommand`, command
`+0x20` to its fighter, and command `+0x24` to the other fighter. Resident
`0x001EF330` retains side `0/1` commands at manager `+0xDF0/+0xDF4`, and side
`0/1` fighters at `+0xDE4/+0xDE8`. These zero-based sides must not be confused
with the Practice status bridge's manager slot indices `1/2`.

The manager control-mode setter `0x001F48F0` stores mode at `+0x1C` and changes
bit `0x02` of its two side records at `+0x48/+0x70`:

| Control mode | Side 0 bit | Side 1 bit |
| ---: | ---: | ---: |
| `0` | Clear | Clear |
| `1` | Clear | Set |
| `2` | Set | Clear |
| `3` | Set | Set |

The Practice status bridge additionally changes the dummy fighter controller
nibble. An input-source switch by itself therefore does not change native
controller ownership. The native non-Manual AI runs during a later fighter
pass and writes its logical mask, movement magnitude and angle to the same
command triple. The inspected representative wrapper `0x00250DA0` calls live
BTL `0x00704D40` when the fighter nibble is nonzero; that AI tick's final stores
are at live `0x00705778/0x00705780/0x00705788` (Ghidra
`0x00705738/0x00705740/0x00705748`, file
`0x051878/0x051880/0x051888`). Playback cannot coexist as an independent
writer of that triple without a defined arbitration rule.

### Provisional recording sources

| Option | Benefit | Additional ownership decision |
| --- | --- | --- |
| Record the Manual dummy from its own controller | Reuses the native two-controller side binding | Available only when that controller supplies input; preserve the active player's normal side |
| Temporarily route the active controller to the dummy | Allows authoring a dummy sequence with one controller | Neutralize the active fighter during capture and restore both side sources afterward |
| Record the active fighter, then play it on the dummy | Records through the normal player path | Side/facing transfer and changed spatial references affect physical-direction interpretation |

No source option or shortcut is accepted here. Each needs an explicit source
side, destination side, and temporary control owner. A playback owner can use
the native manual/no-AI path while retaining the selected Practice Status for
restoration, but entering and leaving that ownership must reconcile the manager
flag, fighter nibble, command history, and queued actions. Switching only the
visible Status value would not establish that complete transition.

## Sampling clock and pause boundaries

### Observed ordering

The relevant clocks are distinct:

1. Resident pad polling publishes latest held/edge/repeat/stick data before
   callbacks and tasks. Each poll replaces the prior publication.
2. The battle command phase samples held/sticks into history and recomputes
   edges between consecutive battle samples. It does not retain core repeat or
   every press/release occurring between samples.
3. The fighter phase applies state gates, optional AI synthesis, the resident
   bridge, and action consumers. A sampled history record can exist without
   an eligible fighter consuming it that cycle.
4. Direct gameplay readers consume shared publication under their own gates;
   the contest update runs separately from the history and fighter phases.

The latest-sample lifetime is established in
[Controller input](../../knowledge/runtime/controller_input.md#publication-lifetime-and-consumer-snapshots).
Resident active-session entry `0x001EF8F0` calls mask construction
`0x001F0290`, then dispatcher `0x001F03E0` only when its preceding session
control result is zero. Result `2` skips that dispatcher; results `1/3` complete
the branch. Mask construction combines pause-controller suppression and
session allowed-bit filters, then stores allowed masks at session `+0x02/+0x04`.

The dispatcher's first phase selects command-list owner `+0x04` and calls its
vtable slot `+0x0C` at resident `0x001F051C` when allowed mask `+0x02` includes
`0x0002`, or when auxiliary object's `+0xA50 == 1`. Resident vtable
`0x005DDD10` maps that slot to live BTL `0x006D67E0` (Ghidra `0x006D67A0`,
file `0x0228E0`), which invokes child-update phase live `0x00709C70`
(Ghidra `0x00709C30`, file `0x055D70`). Child vtable `0x005DDD30` maps slot
`+0x10` to the complete input update live `0x006F0EA0`.

The fighter-list owner at `+0x08` runs later in the first phase on mask bit
`0x0004`, with no corresponding `+0xA50` exception. Within resident
`0x0024FD80`, synthesis `0x0024C440` precedes the optional per-character AI
pass; bridge `0x00217320` and input consumers follow it. The AI/bridge passes
require fighter byte `+0x00` bit `1` and signed fighter `+0x20C <= 0`.
Post-translation hold/repeated-press synthesis also reads history earlier in
that routine. These are logical update gates, not measured seconds or a
guarantee of one update per displayed frame.

### Implications for proposed playback

For the ordinary history lane, the strongest timing choice is to index stored
samples by explicitly eligible battle command steps. Display refresh count,
physical pad poll count, and a single aggregate pause flag cannot substitute
for that clock. The command-only `+0xA50` exception needs a deliberate policy:
either represent its samples in the recording, or freeze the recorder cursor
and define the history supplied during it. Blindly freezing only the cursor can
repeatedly inject one sample and still advance native matcher history. Direct
reader progression cannot be inferred from this history clock; its alignment
remains a separate requirement for full coverage.

During a fully suppressed command phase, preserve the cursor and history.
Pause-menu input should remain available through the physical pad publication;
writing synthetic input into the shared pad record would expose it to other
consumers. A side-local source selection avoids that shared publication change.
The exact cut-in classification and pause-mask producers are owned by
[Pause and replay](../../knowledge/gameplay/pause_and_replay.md#selective-update-gating).

The ring capacity uses a construction-time display pacing value, while matcher
windows count history records. Consequently playback at a different input-step
cadence can change both movement duration and recognized sequences. A recording
needs its sample clock recorded or constrained; no automatic speed conversion
has been established. Shared time primitives remain owned by
[Timer primitives](../../knowledge/runtime/timer_primitives.md).

## Recording slots and storage

The native ring overwrites old records when its index wraps and is destroyed
with its command object. It cannot by itself preserve multiple completed clips
or a clip longer than its capacity. A separate bounded in-memory clip buffer is
a feasible storage candidate, but no allocation region, budget, slot count,
maximum length, or persistence lifetime is established here.

For the ordinary raw-held/stick candidate, four held-mask bytes, two four-byte
angles, and two magnitudes total 14 payload bytes; a word-aligned representation
could use 16 bytes. A full native history record occupies 24 bytes. For example,
four 600-sample slots would require 38,400 or 57,600 sample bytes respectively,
before metadata and ownership state. These are arithmetic examples, not proven
available memory or a chosen duration. Core-pressed samples and independent
consumer clocks add information not represented by that ordinary 14-byte
payload; the final full-recorder storage contract remains unresolved.

Provisional slot metadata includes written length, capacity, recorded side,
sample representation, and clock/phase alignment. Playback cursor and current
control owner are separate from completed clip bytes, so one slot can be
selected again without overwriting its data. Replacing a clip immediately when
recording starts, or keeping its previous contents until capture finishes, are
different storage/interaction choices. At capacity, stopping and finalizing a
clip is a simple option; rolling capture would additionally need to establish
the new first sample and its preceding history. No file or save serialization
is proposed by this bounded in-game storage assessment.

## Playback, looping, and selection

These are useful candidate controls rather than accepted player-facing behavior:

| Option | Candidate behavior | Required decision |
| --- | --- | --- |
| Play selected slot once | Advance through its written samples, then stop | End/release transition and return of control ownership |
| Loop selected slot | Restart the same clip after its final sample | Continuous versus isolated history at the seam; optional gap measured in the selected sample clock |
| Choose among enabled slots | Select a nonempty completed clip at each cycle boundary | Uniform or weighted selection, eligible-slot set, and whether immediate repeats are permitted |
| Delay before playback | Supply a defined neutral input before the first clip sample | Delay units and treatment of fighter/contest updates while the ordinary history phase is skipped |
| Reset before a cycle | Request the separately defined position reset, then start | Reset completion and action/history cleanup; relocation alone does not establish an identical starting state |

Selection is between complete clips; changing slots partway through a clip
would create another seam. Empty slots have no recorded samples to play, and
the zero-eligible-slot case needs a defined stopped state. Random selection
does not inherently require a delay or position reset; those are independent
choices with the dependencies above.

The seam affects native input even before any world-state difference. With
edge derivation `pressed = first & ~last`, a button held at both clip end and
clip start produces no new first press in a continuous loop. A neutral gap
creates releases and subsequent new presses, but does not immediately erase
older matcher records. The verified tables at live BTL `0x00898180` and
`0x008981A0` contain two identical pressed-direction steps, each with 16
nearest-match trials. Classifier live `0x006F0650` advances past a matched
record before searching for the older step. Thus qualifying presses on opposite
sides of a loop boundary can combine into a native double-tap command.
The complete matching semantics are owned by
[Action commands](../../knowledge/gameplay/action_commands.md#static-cccommand-records-and-ordered-matching).

A continuous-history loop and a loop initialized with defined prior history
therefore have different input semantics. The feature needs to choose one;
an arbitrary gap is not evidence that every native history consumer is reset.
Native hold/repeated-press synthesis, contest latches, and the direct-reader
class state also require their own transition treatment. No universal clean
loop or reset sequence is established by this research.

## Reset, stop, and object lifetime

### Observed native ownership

The allocator at live BTL `0x00709780` (Ghidra `0x00709740`, file `0x055880`)
allocates a `0xC0`-byte command object, constructs it, and registers it in the
side list. Its preserved function stops at the allocator call; the complete
body through Ghidra `0x007097B0` was read as bytes to confirm construction and
registration. The command destructor at live `0x006EF560`
(Ghidra `0x006EF520`, file `0x03B660`) destroys the history array at `+0x94`
and clears that pointer.

Resident session cleanup `0x001EEFD0` clears manager fighter/command references,
destroys the four-part owner at session `+0x18`, and clears the owner global.
BTL owner cleanup live `0x007093A0` (Ghidra `0x00709360`, file `0x0554A0`)
invokes each controller's destructor. The command-list destructor at live
`0x006F0FD0` reaches list clear live `0x00709F40`; removal live `0x00709EA0`
calls the child destructor through its vtable slot `+0x08`. This closes the
history's destruction chain. Reconstruction at resident `0x001EE500` destroys
the session owner before returning the outer controller to state `13`; later
`0x001EF330` binds newly constructed side inputs/fighters.

Bindings to destroyed fighters, command objects, or rings cannot be retained
as valid across that destruction/reconstruction boundary. Full restart routing
and native resource snapshots belong to
[Pause and replay](../../knowledge/gameplay/pause_and_replay.md#battle-teardown-and-reconstruction).

This destruction evidence does not prove that every borrowed gameplay alias
is cleared by a generic state reset. The bounded
[skill participant release](../../knowledge/gameplay/target_selection.md#skill-participants-and-lock-release)
investigation distinguishes retained pair/input locks from the final native
release path; other interruption paths remain unproved. Stopping clip input
therefore cannot be treated as proof that an ongoing skill has been cancelled
or its participants released. A forced cancellation would need a separately
established transition contract.

### Provisional transition contracts

These transitions need explicit feature behavior; none is implemented:

| Event | Candidate recording/playback consequence | Reason |
| --- | --- | --- |
| Begin recording | Initialize slot length/cursor and choose a defined prior sample/history | A held button at entry and old matcher history can affect the first edge or command |
| Stop recording | Finalize only written samples, then return input ownership | A partly filled buffer is not a complete clip |
| Begin playback | Bind destination by side, establish history policy, claim dummy control | Native AI otherwise suppresses/overwrites the translated sample |
| Stop playback or clip end | Supply a defined release/neutral transition before restoring normal control | Clearing a logical triple alone leaves held history and native action state |
| Pause/settings menu | Suspend progression under the chosen clock; restore or cancel ownership if settings change the dummy controller | Menu confirmation invokes the native status bridge |
| Position reset | Stop or restart the clip only after reset completion, with a defined history/queue reset | Moving the fighter does not rewind its command history or action state |
| Fighter/stage replacement or session exit | Cancel active ownership and invalidate object bindings before teardown | Commands and fighters are destroyed and replaced |

Retaining completed clips across an in-session position reset is a viable
option because clip bytes can have independent ownership. Retention across
session reconstruction requires a separate proven storage lifetime; it is not
provided by the native command ring. Position reset research is owned by
[Practice position reset](practice_position_reset.md). Its bounded findings do
not establish a complete mid-action reset/cancellation path. Playback must not
equate a position write with completed action, lock, hit, and pair-state cleanup.

## Reproducibility and RNG

### Observations

Resident `0x001801E0` delegates to shared PRNG `0x0017FD90`. The generator owns
624 eight-byte EE state slots at `0x00617640..0x006189BF` and index word
`0x00602A28`. The bounded wrapper `0x00180210` takes the absolute bound and
returns an unsigned modulo result `(raw ^ 0x80000000) % (abs(bound) + 1)`.
It advances the same shared state. Seed writer `0x001801A0` writes
`0x00602A20`; initializer `0x00180060` rebuilds the state and advances it
according to low seed bits before writing a new seed. Setting the seed word is
therefore not a snapshot of the current 624-slot stream.

Resident fighter prepass `0x0024C440` calls `0x001801E0` and stores the result
at fighter `+0x88` outside its initial active-fighter branch. Thus the inspected
fighter-list path advances shared RNG even when dummy AI is disabled. AI and
other shared consumers impose additional call-order dependencies; the complete
AI RNG ownership and caller audit belong to
[Battle AI](../../knowledge/gameplay/battle_ai.md#rng-ownership-and-confirmed-uses).

### Feature implications and limits

Input playback can reproduce a stored sample sequence at the chosen boundary.
It does not by itself restore positions, camera reference, fighter action and
hit state, resources, current command history, direct-action queues, contest
latches, direct-reader class state, support, stage objects, timing gates, or
shared RNG state/call order. Each is either read by the inspected paths or
independently owned by the linked gameplay research.
Equal clip bytes therefore do not establish identical resulting actions or
outcomes from different starting states.

Random slot selection that uses the retail shared PRNG would itself consume
gameplay random state and change the next retail result. An independent
feature-local selector is a provisional option for avoiding that additional
consumption, but its storage, seed, selection policy, and reproducibility have
not been accepted. Restoring only `0x00602A20` is not an established deterministic
reset. Restoring the full stream alone would still require matching subsequent
consumer order and starting gameplay state.
