# Startup sequence

## Splash controller

Game: NA2.28 boot ELF `SLPS_258.37`. Investigation dates: 2026-08-05 through
2026-08-11.

The clean ELF used for the current trace is 5,273,256 bytes with SHA-256
`20C0A40D70EA412CD431993A2E189B37ECB6054D63AE93BE545470016E1627AF`.
Its executable load segment maps file offset `0x100` to EE virtual address
`0x00100000`, so an ELF code file offset maps to virtual address
`file offset + 0x000FFF00`. File offsets and virtual addresses below are kept
distinct according to that mapping.

The resident function at `0x001E0390` constructs four splash objects using,
in order, `TEX_logo_notice_pss`, `TEX_logo_bn_pss`, `TEX_logo_b_pss`, and
`TEX_logo_adx_pss`. The controller update at `0x001E0980` advances those four
objects. Its caller at virtual address `0x001E10A0` (file offset `0xE11A0`)
treats return value `1` as completion, destroys the splash controller through
the normal cleanup path, and continues the main startup state machine toward
the title animation.

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
address `0x001E11CC` (file offset `0xE12CC`). The current patch changes that
assignment to state `3`, bypassing the opening path. The title dispatcher at
virtual address `0x001E1240` (file offset `0xE1340`) normally calls
`0x001DE840`. Return value `1` is New Game and return value `2` is Continue;
the unchanged caller writes main state `4` and the matching substate. The
previous candidate changed bytes `10 7A 07 0C` to `01 00 02 24`, selecting New
Game and therefore skipping the load controller. The accepted patch uses
`02 00 02 24` instead, selecting Continue without constructing or displaying
the title controller.

## Continue and the shared Save/Load controller

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
negative result**.

Static tracing resolves the title/startup integration point. Native title
result `2` makes `FUN_001e9980` select its state-`3` Continue subcontroller
`FUN_001e9eb0`. Title result `1` selects the New Game subcontroller and never
allocates the shared Save/Load parent.

Continue allocates a `0x28`-byte parent and initializes it through
`FUN_001e3db0`. That constructor resets the parent through `FUN_001e3ec0`,
starts the global memory-card worker through `FUN_001e1ca0(worker, 2)`, and
allocates a `0x44`-byte UI child at parent offset `+0x24`. Continue then calls
`FUN_001e3f00(parent, 1)` at virtual address `0x001E9F84` (file offset
`0xEA084`) once per frame. The wrapper delegates to the full visible controller
`FUN_001e3f20` and has this return contract:

| Result | Continue behavior |
| ---: | --- |
| `0` | Keep updating and draw the Save/Load child through the call at virtual `0x001E9FD0` (file `0xEA0D0`). |
| `1` | Record a loaded-save success, destroy the controller, and start the normal main-menu loader. |
| `2` | Record a no-load result and destroy the controller. The guarded edit at virtual `0x001E9FB8` (file `0xEA0B8`) maps this result to the same successful menu continuation instead of returning `-1`. |

The controller destructor `FUN_001e3e20` stops the worker, frees the UI child,
resets the parent, and frees it. After a successful load, Continue retains the
normal resource loader and the native save-dependent setup calls
`FUN_001076c0`, `FUN_001e36c0`, and `FUN_001f4030`; the automatic branch does
not reproduce or bypass that post-load work.

The global worker pointer is stored at EE address `0x006075F4` (`gp-0x33FC`).
The worker thread runs `FUN_001e2140`; its relevant layout is:

| Offset | Meaning |
| ---: | --- |
| `+0x00..+0x3F` | Four `0x10`-byte record descriptors; byte zero of each descriptor is nonzero when that record exists. |
| `+0x40` | Memory-card port. |
| `+0x44` | Record index. |
| `+0x48` | Requested worker operation. |
| `+0x4C` | Detailed status. |
| `+0x50` | Result class. |
| `+0x54` | Save/Load mode hint; `1` is load mode. |
| `+0x58` | Latest lower-level card classification. |
| `+0x5C` | Worker thread handle. |

The normal load path first writes load mode `1`, calls `FUN_001e1d80`, and
performs the native preparation call `FUN_001d9600(0)`. It scans a card through
`FUN_001e1da0(worker, port)`, requests one record through
`FUN_001e1e10(worker, record)`, and resolves the resulting confirmation through
`FUN_001e3120(worker, decision)`. Decision `1` changes status `0x10` into worker
operation `6`, which reads `0x2400` bytes, verifies the stored checksum, and
copies the loaded profile into the live save object before reporting success.

## Visible first-record branch

The confirmed visible branch combines Continue with the guarded first-record
dispatch at virtual `0x001E5008` (file `0xE5108`). The dispatch sets record zero
before the list update, calls `FUN_001e1e10` in load mode, branches to the
unchanged native save operation in other modes, and rejoins the controller's
normal post-operation states. It ends before the independent guarded edit at
virtual `0x001E5040` (file `0xE5140`).

Two user-supplied NA2.28 savestates from CRC `7E79CCB3` establish the current
load-confirmation loop. Slot 1 captures the initial `Load this data? Yes / No`
modal; slot 2 captures the same modal after choosing No. Their embedded
screenshots are byte-identical. Both states contain the same active controller
graph: main state `3`, Continue state `1` with result `0`, Save/Load state `6`
with record `0`, modal result `0`, and memory-card operation `1` with status
`0x10`, result type `3`, and record `0`.

Static tracing identifies the loop mechanism. In Save/Load state `6`, modal
result `2` (No) closes the confirmation and writes state `4` at runtime
`0x001E5474` (file offset `0xE5574`). The first-record edit replaces state `4`'s
record-list dispatch with an immediate load-confirmation dispatch, so the next
update reconstructs the same modal. The correction changes the clean
`li v0,4` instruction (`04 00 02 24`) to `li v0,8` (`08 00 02 24`), routing No
through the native Save/Load completion path. At runtime `0x001E9FB8` (file
offset `0xEA0B8`), it also changes the Continue result immediate from `-1`
(`FF FF 02 24`) to `1` (`01 00 02 24`) so the unchanged Continue success path
enters the main menu without loaded save data. User runtime validation
confirmed the integrated behavior of this visible branch.

## Silent automatic first-save branch

The automatic branch replaces only the per-frame call to
`FUN_001e3f00(parent, 1)` at virtual `0x001E9F84` (file `0xEA084`) with a small
generated-C state machine. Continue still owns allocation, result handling,
cleanup, the post-load save setup, and the main-menu loader. The injected state
machine uses the otherwise bypassed parent state word at `+0x08`; construction
and destruction already initialize and reset that word.

The state machine follows the worker's native operations rather than reading or
copying save data itself:

| Phase | Native operation and accepted result | Automatic action |
| --- | --- | --- |
| Initialize | Worker created by `FUN_001e3db0` | Set load mode `1`, call `FUN_001e1d80`, run `FUN_001d9600(0)`, and start a port-zero scan with `FUN_001e1da0`. |
| Scan | Busy is status/result `4/0`; success is `1/0` | Wait while busy. On success, require record descriptor zero to be occupied and request record zero through `FUN_001e1e10`. Any other terminal status, or an empty first descriptor, returns no-load result `2`. |
| Confirm | Busy is `4/0`; ready is `0x10/3` | Wait while busy, then resolve the native confirmation internally as Yes through `FUN_001e3120(worker, 1)`. Any other terminal status returns `2`. |
| Load | Busy is `4/0`; native read progress is `0x11/4` or `0x12/4`; success is `0x13/1` | Wait through the native read. Return loaded-save result `1` only after the worker has verified and copied the save. Any other terminal status returns `2`. |

The lower-level classifier `FUN_001c20a0` and the worker provide explicit
failure cases before the first-record decision:

| Physical/data case | Worker outcome in load mode | Automatic outcome |
| --- | --- | --- |
| No memory card in port zero | status `5`, result `2` | Enter main menu without loading. |
| Non-PS2/wrong card type | status `7`, result `2` | Enter main menu without loading. |
| Unformatted or not-ready PS2 card | status `0x28`, result `1` | Enter main menu without loading. |
| No game directory or insufficient directory capacity | status `0x29`, result `1` | Enter main menu without loading. |
| Game directory exists but record zero is absent | scan success `1/0`, descriptor zero byte `0` | Enter main menu without loading. |
| Record-zero read or checksum failure; card changes during the operation; any other non-success terminal status | status/result other than the accepted pairs above | Enter main menu without loading. |
| Valid record zero | load success `0x13/1` | Continue with the native loaded save and its normal settings application. |

The draw call at virtual `0x001E9FD0` (file `0xEA0D0`) is independently replaced
with a no-op in the automatic branch. The native UI child may still be allocated
and freed, but its Load list, card messages, confirmations, and acknowledgment
screens are never drawn. The title and startup patches already enter Continue
without showing the title, so the first user-visible screen after the boot
loading presentation remains the main-menu loading screen.

There is deliberately no synthetic timeout: while an operation is in one of its
documented busy states, the branch preserves the native worker's blocking
contract instead of guessing that a slow valid card has failed. Every native
terminal outcome other than verified record-zero success takes the no-load menu
path. `qol.save_load.display_only_first_save` remains independent; it controls
the visible Save/Load interface and is not used by the silent state machine.

The function boundaries, clean instruction guards, global pointer, worker
layout, status transitions, card classifications, checksum/copy completion, and
Continue cleanup/post-load paths are high-confidence static findings from the
clean ELF. Full development build `20260811_054948_801_pid12700` succeeded, and
user runtime validation on 2026-08-11 confirmed the integrated automatic
behavior: a valid first save is loaded silently before the main menu, while the
no-load path reaches the main menu without input or visible Save/Load UI. The
individual physical-card rows above remain the statically established native
outcome mapping unless separately exercised at runtime.

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
visible during that wait. The call at virtual address `0x001E10A0` (file offset
`0xE11A0`) receives the splash controller in `a0`. Generated C invokes the
original update until its object
list exists, then holds controller state `1` and draw index `0` while returning
completion to the unchanged startup loop. The loop still waits for both real
resource-completion values.

The original sprite draw call at virtual address `0x001E10E0` (file offset
`0xE11E0`, clean bytes `38 80 07 0C`) is redirected to a generated-C counter
draw. The first version
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
