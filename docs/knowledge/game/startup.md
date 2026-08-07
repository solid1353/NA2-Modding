# Startup sequence

## Splash controller

Game: NA2.28 boot ELF `SLPS_258.37`. Investigation date: 2026-08-05.

The resident function at `0x001E0390` constructs four splash objects using,
in order, `TEX_logo_notice_pss`, `TEX_logo_bn_pss`, `TEX_logo_b_pss`, and
`TEX_logo_adx_pss`. The controller update at `0x001E0980` advances those four
objects. Its caller at `0x001E11A0` treats return value `1` as completion,
destroys the splash controller through the normal cleanup path, and continues
the main startup state machine toward the title animation.

Six user-supplied NA2.28 savestates with CRC `FDAFF23A` establish the runtime
boundary:

| State | Visible phase | Main startup state | Splash index |
| --- | --- | ---: | ---: |
| ss1 | notice/warning | 0 | 0 |
| ss2 | Bandai Namco | 0 | 1 |
| ss3 | Bandai | 0 | 2 |
| ss4 | CRIWARE | 0 | 3 |
| ss5 | title animation | 3 | controller absent |
| ss6 | interactive title screen | 3 | controller absent |

The main-state pointer is stored at EE address `0x006075C0`; the splash-pointer
slot is at `0x006075DC`. Across ss1-ss4, the same splash object is present and
its halfword index at object offset `+0x10` advances from `0` through `3`.
Across ss5-ss6, the splash pointer is null and the main state is `3`.

`0x001DE6F0` is the native post-splash sequence dispatcher. In the original
order it runs after the four splashes and before the title. Patch `ELF-Q001`
retains its proven branch past the CyberConnect2 intro.

Calling `0x001DE6F0` from the main-state-0 loader loop is a rejected approach.
Runtime testing showed that the dispatcher resets its sequence state after the
opening completes or is skipped, so the next loader-loop iteration starts the
opening again. Starting it before the normal audio and streaming prerequisites
are ready also caused first-playback stutter and loud white noise. The current
implementation therefore skips the opening instead of invoking it from the
startup loader loop.

## Direct main-menu transition

A second user-supplied batch from NA2.28 CRC `D5AA705B` establishes the native
post-Start path:

| State | Visible phase | Loader flags | Main state/substate | Menu controller phase/mode |
| --- | --- | --- | --- | --- |
| ss1 | black startup wait | `0 / 0` | `0 / 0` | absent |
| ss2 | immediately after Start | `1 / 1` | `4 / 1` | `1 / 0` |
| ss3 | main-menu loading | `1 / 1` | `4 / 1` | `2 / 0` |
| ss4 | usable main menu | `1 / 1` | `4 / 1` | `4 / 1` |

The startup loop requires three simultaneous completion values: the splash
controller result, the ROFS/data-ready byte at `0x006074A0`, and byte `+0x1C`
of the startup-resource object referenced at `0x0060755C`. Bypassing only the
splash controller therefore exposes the remaining asynchronous loading as a
black screen without materially reducing total boot time. Those two resource
checks must remain because the main-menu controller consumes the initialized
data.

After all three values are ready, the native code writes state `2` at virtual
address `0x001E12CC` (file offset `0xE12CC`). The current patch changes that
assignment to state `3`, bypassing the opening path. The title dispatcher at
virtual address `0x001E1340` (file offset `0xE1340`) normally calls
`0x001DE840`; return value `1` is the accepted-Start result. The patch changes
bytes `10 7A 07 0C` to `01 00 02 24`, returning that result immediately. The
unchanged caller then writes main state `4` and substate `1`, matching ss2-ss4,
and the native menu controller advances through its loading phases to the usable
main menu.

## Automatic first-save investigation boundary

Base-NA2 savestates for `SLPS-25837` CRC `C0659AD1` preserve the native startup
sequence: `ss1` title screen, `ss2` load list, `ss3` first save loaded, and
`ss4` main menu. In base `ss2`, the shared Save/Load controller at global
`0x00607624` is allocated at `0x00C42820`; its state at `+0x08` is `4`, its
selected record at `+0x04` is `0`, and its child at `+0x24` is `0x00C428C0`
with mode `1` at child offset `+0x08`. The same controller advances to state
`3` in `ss3` and is released by `ss4`.

Current NA2.28 savestates for CRC `6E79CD2E` establish the direct-startup path:

| State | Visible phase | Data-ready byte `0x006074A0` | Main state/substate | Menu phase/mode | Save/Load controller `0x00607624` |
| --- | --- | ---: | --- | --- | --- |
| ss1 | custom startup loader | `0` | `0 / 0` | absent | absent |
| ss2 | usable main menu | `1` | `4 / 1` | `4 / 1` | absent |

A rejected `ELF-Q010` candidate patched runtime `0x001E5008` (ELF file
`0xE5108`) to force record zero and enter the native mode-1 load operation.
The bytes were confirmed present in the tested Latest ISO, but the user observed
no automatic load. The current states show why: the direct startup path reaches
the main menu without allocating the shared Save/Load controller, so changing
that controller cannot implement startup loading. This is a **high-confidence
negative result**. A future candidate must instead locate the native first-save
operation within the title/startup path bypassed at `0x001E1340`; its exact
integration point remains unresolved.

## Early native loading screen

A third user-supplied NA2.28 batch from CRC `C9AB0A4F` narrows the transition
from the startup wait to the native main-menu loader:

| State | Visible phase | Main state/substate | Menu phase/mode | Loading controller |
| --- | --- | --- | --- | --- |
| ss1 | black startup frame | `0 / 0` | `2 / 0` | active, `34.44%` |
| ss2 | opening movie | `2 / 0` | absent | absent |
| ss3 | black transition | `4 / 1` | `1 / 0` | created, inactive, `0%` |
| ss4 | native loading screen | `4 / 1` | `2 / 0` | active, `34.44%` |
| ss5 | usable main menu | `4 / 1` | `4 / 1` | reset, `100%` |

The ss1 embedded screenshot and its captured EE memory are from slightly
different frame boundaries: the image is black while memory already contains
an active loading controller. It establishes controller availability but not
the exact first visible frame.

The menu controller pointer is stored at `0x00607600`, its subcontroller at
`0x0060760C`, the selected loading resource at `0x00607698`/`0x0060769C`, the
loading-screen controller at `0x006076A0`, and its progress flag/value at
`0x006076A4`/`0x006076A8`.

Function `0x001E9C00` is the native main-menu-load subcontroller. It advances
through resource preparation, opens a `loadingXX.ccs` resource through
`0x001FFC30`, begins the loading screen through `0x002005B0`, waits for its
completion, and hands control to the usable menu. `0x00203B50` initializes the
loading systems, `0x00203C50` updates and draws them each frame,
`0x002006C0` stores progress, and `0x001CFAE0` is the native progress query.

Calling the native loading-system functions during startup state `0` is a
rejected approach. Candidate commit `adbaf92f` initialized `0x00203B50`, opened
the standard loading resource through `0x001FFC30`, began the screen through
`0x002005B0`, and updated it through `0x00203C50`. The integrated result remained
black for the full wait. The menu-loading presentation therefore depends on
resources or state that are unavailable before the startup loaders finish.

The replacement candidate reuses the boot splash path, which is already proven
visible during that wait. The call at file offset `0xE11A0` receives the splash
controller in `a0`. Generated C invokes the original update until its object
list exists, then holds controller state `1` and draw index `0` while returning
completion to the unchanged startup loop. The loop still waits for both real
resource-completion values.

The original sprite draw call at file offset `0xE11E0` (clean bytes
`38 80 07 0C`) is redirected to a generated-C counter draw. The first version
suppressed the logo sprite and called the ordinary native text renderer at
`0x00379040`. User ss1 from integrated CRC `D5AA8F48` captured a black frame,
while linked state at `0x008F8668` contained frame count `344` and percentage
`5`. This proves that the replacement draw hook and timer ran, but the ordinary
font path produced no visible pixels during this boot phase.

The replacement no longer depends on font or menu resources. From the same
draw call it first invokes the native primitive setup and then uses the active
render-context pointer at `0x0060745C`, matching the established solid-rectangle
sequence. Its functions are setup
`0x001830A0`, color conversion `0x00182A20`, vertex submission `0x001822B0`,
and flush `0x00182F50`. It draws two seven-segment digits, a primitive percent
sign, and a progress bar.

The first solid-primitive integration in `cbc19dfe` called setup once and
submitted every rectangle before one final flush. User ss1 showed that primitive
type `5` joined the separate rectangles into one triangle strip, creating large
diagonal wedges. The corrected renderer mirrors the known solid-rectangle
function `0x0019FD20`: every segment and bar rectangle performs its own setup,
color, four-vertex submission, and flush. At 30 FPS, the displayed value maps
750 frames to the user's measured 25-second full load and caps at `99%`; it is
only an estimate and never substitutes for real loader completion. This draw
hook is also the presentation boundary where a custom loading-screen background
can be added later without changing loader control flow.

Together with the enabled opening skip, the intended sequence is the timed
loading counter during the boot wait, native menu transition, then main menu.
Confidence is high for the control flow, clean instruction guards, triangle-strip
failure localization, and corrected independent-rectangle sequence. Its final
appearance and pacing remain pending integrated user runtime validation.
