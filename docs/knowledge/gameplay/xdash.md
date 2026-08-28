# X-dash knowledge

## Action states and chakra-cost implementation

The immutable `xdash` recording supplied on 2026-08-15 contains one idle
marker followed by three markers from the same Player 1 X-dash. Player 1 is
Kakashi, character ID `70`; Player 2 is Sai, character ID `92`. In all four
states, Kakashi's fighter pointer is `0x00E369A0`, normalized HP at fighter
`+0x6C` is `0.5`, and chakra at fighter `+0x70` is `15.0`. The unmodified move
therefore consumes no chakra.

The idle marker has major action state `0` at fighter `+0x18E` and action index
`0` at `+0x190`. Markers 2 through 4 have major action state `8` and action
index `0x13`; their phase field at `+0x192` is respectively `0`, `1`, and `2`.
Marker-free tracing later established that phase `0` is cancellable
preparation, a persisted phase `1` is dash movement, and phase `2` is the hit
transition. Phase `1` can be written transiently during the final cancellation
update, so the phase write alone is not a safe charge boundary.

The selected action record is
`fighter[+0xA54] + 0x13 * 0x54`. In both loaded character tables, record
`+0x10` is `0x00000002`, record `+0x1C` is `0x02000011`, and the native float
cost at record `+0x20` is `0.0`. `FUN_00239530` selects only action index
`0x13` for the corresponding input-mask branch. After the action is accepted,
`FUN_0023a9a0` loads the native cost at EE `0x0023AAF0`, runs the native
subtraction and zero clamp at `0x0023AC00..0x0023AC20`, then calls
`FUN_00217e40(fighter, 8, action_index, mode)` at `0x0023AE84` to enter the
observed state.

Hooking the cost load at `0x0023AAF0` was runtime-proven to deduct during phase
`0` and was rejected because that preparation can still be cancelled. The
first replacement hook instead used the direct setter's loaded store at EE
`0x0071EF00`, `BTL.BIN` file offset `0x6B000`, to charge on phase `0` to phase
`1`. The Ghidra export labels that instruction `0x0071EEC0`; loaded BTL code is
`0x40` higher than those labels because of the module header mapping.

The marker-free `xdash-polish` recording then established that the phase-`1`
write can occur before cancellation processing finishes. Its three X-dash
attempts produced these runtime sequences against the exact Latest development
image:

- completed dash: phase `0` to `1` to `2`, with chakra `15.0` to `14.0`;
- earlier cancel: phase `0` to major action `7`, action `0x64`, with chakra
  remaining `14.0`;
- final-frame cancel: persistent phase `0` to major action `7`, action `0x64`,
  while chakra still fell from `14.0` to `13.0`.

The final cancel proves that the direct phase-`1` setter can run transiently
inside an update before the cancel replaces the action in that same update.
Charging there is therefore too early even when phase `1` is never externally
observable for a full frame.

The first phase-`2` implementation hooked only loaded EE `0x0071F244`,
`BTL.BIN` file offset `0x6B344`, one of seven duplicated stores in
`FUN_0071f120`. The
development build contained that hook, but a manual runtime check established
that it did not deduct on the live X-dash path. Routing all centralized phase
writers through the same phase-`1` to phase-`2` guard made the completed dash
deduct, but the marker-free replay ended at `13.0` after the final cancel even
though both cancel episodes were externally observable only in phase `0` and
exited with `14.0`. Phase `2`, like phase `1`, can therefore occur transiently
inside the cancellation update and is not by itself proof that movement began.

An end-of-update implementation next replaced the call to
`FUN_00238540(fighter)` at EE `0x0024DCB0`, ELF file offset `0x14DDB0`. It
preserved that native call and charged only when phase `2` remained at the end
of the complete fighter update. The `dev` worker replay of `xdash-polish` used
live manager `0x00CA25D0` and Player 1 fighter `0x00E366A0` and produced:

- completed dash: phases `0`, `1`, and initial `2` remained at `15.0`; the
  post-update check then changed phase-`2` chakra to `14.0`;
- earlier cancel: phase `0` exited to major action `7`, action `0x64`, at
  `14.0`;
- final-frame cancel: phase `0` exited to major action `7`, action `0x64`, at
  `14.0`;
- end of recording: chakra remained `14.0`.

PCSX2 ran surfaceless for this replay; its process reported no window handle.
That implementation fixed both recorded cancels, but a manual runtime check
established that it was too late: a committed X-dash could be replaced by an
attack state before the final check and therefore escape the deduction.

Tracing forward from the phase writes established the actual distinction. A
task-local logger replaced the direct setter, generic increment, and seven
centralized event stores only in a disposable surfaceless replay. All seven
X-dash-related writes came from the direct setter at loaded EE `0x0071EF00`;
none came from the other eight instrumented stores. The ordered events were:

- completed dash: `0x0023C11C` set phase `0` to `1`, then `0x0023DC34`
  entered phase `2` with transition mode `s2 = 2`;
- earlier cancel: `0x00217F9C` reset phase `0` to `0`, then `0x0023DC34`
  transiently entered phase `2` with transition mode `s2 = 6`;
- final-frame cancel: `0x00217F9C` reset phase `0` to `0`, `0x0023C11C`
  set phase `0` to `1`, then `0x0023DC34` transiently entered phase `2` with
  transition mode `s2 = 6`.

Those events were initially misread as a movement distinction. Runtime testing
showed that the `0x0023DC34` mode-`2` transition deducts only when X-dash hits
the opponent. `FUN_0023d980` is therefore hit-response processing, not the
dash-start path; mode `6` is the cancellation response and mode `2` is the
X-dash hit response.

The actual movement boundary is owned by `FUN_0023c230`. Its internal state at
fighter `+0x9BA` is `1` during cancellable preparation. When the animation
crosses its start threshold, `FUN_0023c0f0` changes `+0x9BA` to `2`, changes
the action phase at `+0x192` to `1`, and installs the movement physics. The
state-`2` branch of `FUN_0023c230` then handles contact and eventually calls
`FUN_0023d980`, which changes the internal state to `3` and the action phase to
`2` for the hit transition.

A hidden, surfaceless replay of the exact `xdash-polish` recording sampled
those fields throughout all three attempts. The completed X-dash persisted as
phase `0` / substate `1` at animation frame `1`, then phase `1` / substate `2`
at frame `10`, while chakra was still `15.0` and position had begun moving. It
reached phase `2` / substate `3` at frame `18`, where the rejected hook reduced
chakra to `14.0`. The earlier and final-frame cancellations both left phase
`0` for major action `7`, action `0x64`, without persisting phase `1` /
substate `2` into another fighter update.

The candidate implementation uses the immediate next fighter-update boundary.
At EE `0x0024DA80`, ELF file offset `0x14DB80`, `FUN_0024da50` normally calls
`FUN_0020e280(fighter)` before native hit and state-interruption handling. The
shim first checks the entering fighter state, then preserves that native call.
It deducts only for major action `8`, action index `0x13`, action phase `1`, and
internal substate `2`. A two-side latch blocks repeat deductions while that
movement state persists and resets outside it. This is the first persisted
state after the final cancellation opportunity and precedes the phase-`2` hit
transition.

A hidden, surfaceless development-worker replay of the exact `xdash-polish`
recording validated this boundary. The completed dash changed from chakra
`15.0` in phase `0` / substate `1` to `14.0` at its first observed phase `1` /
substate `2`; the later phase `2` / substate `3` hit transition remained at
`14.0`. The earlier cancel and the final-frame cancel both exited directly
from phase `0` / substate `1` to major action `7`, action `0x64`, and remained
at `14.0`. PCSX2 reported no window handle during the replay.

The builder-facing cost uses normalized percentage points on `0..100`, while
fighter chakra at `+0x70` retains NA2's native `0..15` scale. The encoder emits
`configured_cost * 15 / 100` as the resident float32 consumed by the accepted
hook. The base configuration uses `6.666666666666667/100`, which emits exactly
`1.0` native chakra and preserves the runtime behavior validated above. A
configured `100/100` emits `15.0` and therefore represents the full native
gauge.

This implementation does not create a minimum-chakra requirement. For action-record
type `0x00000002`, `FUN_00244190` returns before its normal cost-affordability
check. The action can therefore begin below the configured cost, and the
candidate routine clamps the resulting gauge to zero. Rejecting X-dash when chakra
is below the configured cost would require a separate explicit guard.
