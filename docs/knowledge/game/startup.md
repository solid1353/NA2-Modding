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

The early-loading implementation replaces the splash-update call at file
offset `0xE11A0` with generated C. On its first invocation it initializes the
loading systems, synchronously opens the existing loading resource with
`0x001FFC30(-1, 0)`, and starts the screen with `0x002005B0(0, 1)`. Each later
startup frame calls `0x00203C50` and returns splash completion, leaving both
required loader checks and their cleanup path intact.

The native progress-query call in this path is guarded at file offset
`0x1002B8` (clean bytes `B8 3E 07 0C`). Its generated-C replacement returns
`0.0f` only while main startup state `0` is active, then delegates to
`0x001CFAE0`. This displays the native loading screen immediately at `0%`,
hands progress back to the ordinary main-menu loader after the real transition
begins, and avoids inventing a second loading UI.

Together with the enabled opening skip, the intended sequence is native loading
screen during the boot wait, native loading/menu transition, then main menu.
Confidence is high for the static function roles and supplied-state boundaries;
the exact visible timing and handoff remain pending integrated user runtime
validation.
