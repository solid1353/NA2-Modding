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

Static tracing now resolves the ROFS/data-ready side of that barrier. Startup
mounts `DATA.CVM` as `VOL`, loads the root directory synchronously, and creates
the `Load ROFS_Data` worker at `FUN_001BD970`. The worker recursively loads the
20 child directories described by `GZLIST.TXT` and sets `0x006074A0` only after
their metadata is ready. It does not preload the 2,310 CCS payloads. The mount,
tree layout, retry behavior, and path-routing contract are documented in
[Resident file and archive services](files/runtime_services.md).

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
| `+0x00..+0x3F` | Four `0x10`-byte record descriptors, detailed below. |
| `+0x40` | Memory-card port. |
| `+0x44` | Record index. |
| `+0x48` | Requested worker operation. |
| `+0x4C` | Detailed status. |
| `+0x50` | Result class. |
| `+0x54` | Save/Load mode hint; `1` is load mode. |
| `+0x58` | Latest lower-level card classification. |
| `+0x5C` | Worker thread handle. |

Each `0x10`-byte record descriptor has this layout:

| Descriptor offset | Meaning |
| ---: | --- |
| `+0x00` | Occupancy; nonzero means that record exists. |
| `+0x01` | Native descriptor class, validated as `0..4` for occupied records. |
| `+0x02` | Stored checksum for the corresponding `0x2400`-byte save record. |
| `+0x04` | Play time in 30 Hz ticks. |
| `+0x08` | Reserved byte from the memory-card modification timestamp. |
| `+0x09` | Saved second. |
| `+0x0A` | Saved minute. |
| `+0x0B` | Saved hour. |
| `+0x0C` | Saved day. |
| `+0x0D` | Saved month. |
| `+0x0E` | Saved year as a little-endian `u16`. |

`FUN_001c2c80` finds the record's `dataNN` entry in the native 64-byte
memory-card directory table and copies that entry's eight-byte modification
timestamp at table offsets `+0x08..+0x0F` into descriptor offsets
`+0x08..+0x0F`. The project's local PS2SDK `libmc.h` identifies those bytes as
reserved, second, minute, hour, day, month, and little-endian year. The native
record-list renderer `FUN_001e6370` independently consumes descriptor day,
month, and year, and converts the play-time field using 108,000 ticks per hour,
1,800 per minute, and 30 per second. Its overflow display is `999:59:59`.
Consequently, the complete play time and saved date/time are already available
after the existing scan; reading them requires no additional memory-card
operation.

Memory-card directory timestamps use the PS2 clock's fixed JST (`UTC+9`)
representation. They are not already local time. The PS2SDK conversion contract
applies `configured timezone - 540 minutes`, plus the configured daylight-saving
hour. The game links `GetOsdConfigParam` at `0x0015DD90`; timezone is its signed
11-bit field at bits `21..31`, while configuration version is bits `13..15`.
Version zero is the early-Japanese fallback and therefore remains at `UTC+9`.
For later configurations, syscall `0x6F` (`GetOsdConfigParam2`) exposes the
daylight-saving flag through bit `4` of parameter byte one.

User runtime evidence at `UTC+3` showed the unconverted defect directly: a save
made around `11/08/2026 19:20` was displayed as `12/08/2026 01:20`, exactly the
six-hour difference between JST and `UTC+3`. The notification therefore converts
the directory timestamp to the currently configured PS2 timezone before storing
its packed display date and time, including minute offsets, daylight saving,
month/year rollover, and leap years. It does not alter the memory card or the
save payload.

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
failure cases before the first-record decision. Classifier result `2` is the
unformatted-card case: it is returned for PS2 card type `2` with format flag
`0`, as well as when a following memory-card operation reports native result
`-2`. The load-mode worker maps it to status `0x28`:

| Physical/data case | Worker outcome in load mode | Automatic outcome |
| --- | --- | --- |
| No memory card in port zero | status `5`, result `2` | Enter main menu without loading. |
| Non-PS2/wrong card type | status `7`, result `2` | Enter main menu without loading. |
| Unformatted PS2 card | status `0x28`, result `1` | Enter main menu without loading. |
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

### NUN5 E2E reference port

The NUN5 reference game is `SLES-55605`, CRC `C071D4C1`. Its clean
5,340,912-byte boot ELF has SHA-256
`20A43677397731A2A20899336D1165ACE5B436906B9B89BE90FB10F4558DD19D`.
The executable load segment maps file offset `0x180` to EE virtual address
`0x00100000`, so its file offsets use `virtual address - 0x000FFE80`; this is
different from NA2's `0x100`-based mapping.

NUN5's splash controller `FUN_001e6500` embeds the language selector before its
logo sequence. Runtime `0x001E65D0` is the only caller of selector update
`FUN_003d0c60`. Language index `0` is English: `FUN_003d4000(0)` stores it at
`0x00611C10`, and the caller subsequently runs the unchanged selector cleanup
`FUN_003d09c0` and `FUN_003d4040`, which loads `TEXTENG.BIN`. The E2E PNACH
therefore replaces the selector entry with an equivalent direct store of zero
and return value `1`. The branch at runtime `0x001E6620` is then removed after
the normal text load and logo construction, so the controller takes its native
empty-sequence completion path without activating or drawing a logo. Its normal
destructor still owns the allocated objects.

The post-loader and Continue control flow is structurally homologous to NA2:

| NUN5 role | Symbol/address | Established behavior |
| --- | --- | --- |
| Required-loader completion | `0x001E6DB4` | Native state `2` enters the movie path; state `3` enters the title dispatcher. |
| Title dispatch | `0x001E6E28`, `FUN_001e4480` | Result `2` selects Continue. |
| Continue controller | `FUN_001efe60` | Allocates the native `0x28`-byte Save/Load parent, consumes results `1`/`2`, performs cleanup, and retains the native post-load setup and main-menu loader. |
| Save/Load update | `0x001EFEDC`, `FUN_001e9d00(parent, 1)` | Per-frame visible load-mode update replaced by the silent driver. |
| No-load result | `0x001EFEFC` | Native `-1` abort is changed to zero so result `2` continues to the menu without loaded data. |
| Save/Load draw | `0x001F0174`, `FUN_001eb500` | No-op while the silent operation is pending. |

The global worker pointer is `0x00617CF4`. NUN5 retains the same `0x60`-byte
worker layout and relevant status/result contract as NA2. Its matching helper
functions are `FUN_001e7a00` for the load-mode preamble,
`FUN_001deef0(0)` for load preparation, `FUN_001e7a20(worker, 0)` for the
port-zero scan, `FUN_001e7a90(worker, 0)` for record-zero load, and
`FUN_001e8e60(worker, 1)` for confirmation as Yes. The silent driver therefore
uses the same four phases and accepted pairs documented above: scan `1/0`,
confirmation `0x10/3`, read progress `0x11/4` or `0x12/4`, and verified load
completion `0x13/1`. Every other terminal outcome returns Continue result `2`;
busy status `4` retains the native unbounded wait.

The language-selector function occupies runtime
`0x003D0C60..0x003D0FFF` and has no caller other than `0x001E65D0`. Once its
entry returns immediately, its tail is unreachable. The PNACH places the
448-byte silent driver at `0x003D0C80..0x003D0E3F`, within that function only.
The complete 928-byte clean function range has SHA-256
`9C287ED44C52EA0821AAC95F469E08BEF2C56CC107558E11A39DE5E04317FF6E`;
the linked driver has SHA-256
`0701F97F71AE8F021005C722F49C585026D3F353F65F45392F871847FD387468`.
Every emitted word in the PNACH retains its decoded MIPS instruction as an
inline comment.

| Runtime | ELF file offset | Clean word | Candidate word/effect |
| ---: | ---: | ---: | --- |
| `0x001E6620` | `0xE67A0` | `1440004C` | `00000000`: do not enter logo playback. |
| `0x001E6DB4` | `0xE6F34` | `24030002` | `24030003`: enter title state after the required loaders. |
| `0x001E6E28` | `0xE6FA8` | `0C079120` | `24020002`: select Continue without title input. |
| `0x001EFEDC` | `0xF005C` | `0C07A740` | `0C0F4320`: call the silent driver at `0x003D0C80`. |
| `0x001EFEFC` | `0xF007C` | `2402FFFF` | `0000102D`: map no-load to normal menu continuation. |
| `0x001F0174` | `0xF02F4` | `0C07AD40` | `00000000`: suppress the visible Save/Load child. |
| `0x003D0C60` | `0x2D0DE0` | `27BDFFB0` | Begin the English-selector stub; the driver starts at `0x003D0C80`. |

This E2E-focused port deliberately omits NA228's custom boot progress display,
savedata notification, and output-specific payload system. The user confirmed
that the PNACH startup path works at runtime on 2026-08-11. The exact
memory-card and save-data case exercised during that verification was not
recorded.

### Main-menu savedata notification seam

The usable menu is the established controller state/mode `4/1`. The native font
path provides `FUN_00378f50(x, y, text, rgba)` for one colored string and
`FUN_003798e0(text, 0)` for its horizontal extent. Nominal-speed runtime timing
of the visibility-gated candidate showed that a `737,280,000`-tick threshold
lasted 2.5 seconds, establishing an effective EE coprocessor Count rate of
294,912,000 ticks per second. Unsigned elapsed-Count arithmetic therefore uses
2,949,120,000 ticks for the requested ten-second display interval and remains
valid across counter wraparound.

Outer menu state/mode `4/1` is not itself the first visible Mode Select frame.
`FUN_001ea240` owns a second controller through global pointer `0x0060760C`.
Its states `0..3` allocate and prepare resources; only state `4` updates the
Mode Select object and draws it through `FUN_00385c00`. User runtime testing at
nominal speed found that a timer started from outer `4/1` left the notification
visible for only about one second. The corrected visibility gate therefore
requires both outer `4/1` and inner state `4`, starting the ten-second interval
on the first drawable Mode Select state rather than during its preparation.

The first notification candidate wrapped the `FUN_00203c50` call made by
`FUN_001e9980` at runtime `0x001E9BAC` (ELF offset `0xE9CAC`). User `ss1` from
CRC `3755A284` proves that the automatic load, outcome publication, timer, text
formatting, and draw wrapper all ran: its injected state contains outcome `1`,
play time `0x349` ticks, date `2026-08-11`, and time `23:10`, and its embedded
screenshot contains `Save data loaded.` and `Play Time 0:00:28`. However, that
call site inherits Mode Select's bottom-body text context. The notification was
therefore drawn at the bottom-right and its third line was clipped below the
screen. This is a confirmed unsuitable presentation seam, not a savedata-load
or outcome-capture failure.

`FUN_00108490` establishes the global end-of-frame renderer context through
`FUN_001866d0(renderer, frame + 0x150)`, calls `FUN_0018b8e0`, then executes the
reserved hot-reload no-op and flushes through `FUN_00186000`. The call to
`FUN_0018b8e0` is at runtime `0x00108598` (ELF offset `0x8698`, clean instruction
`38 2E 06 0C`). This is a valid native drawing phase, but it is not a valid
resident-payload hook: it runs during initial boot, before `228.BIN` has been
loaded.

User `ss1` from CRC `375B83A8` proves the resulting launch failure. The hook at
runtime `0x00108598` had already been replaced by `08 E3 23 0C`, targeting the
notification wrapper at `0x008F8C20`, while that target and the rest of the
`228.BIN` load range were still zero. The EE then executed zero words through
the unloaded reservation and trapped when the data word at EPC `0x00940124`
decoded as a trap instruction; the saved Cause value is `0x34`. The embedded
screenshot is black. This rejects every unconditional boot-wide hook from the
main ELF into the resident payload, even when its renderer phase is otherwise
correct. The reserved hot-reload no-op at runtime `0x001085A0` remains untouched.

The replacement keeps the proven post-load main-menu hook at runtime
`0x001E9BAC`. After retaining `FUN_00203c50`, it saves the renderer's current
context at `+0x6C`, temporarily selects the frame-wide context through
`FUN_001866d0(renderer, frame + 0x150)`, draws the notification, and restores
the saved context. The frame and renderer pointers come from `0x006073FC` and
`0x00607470`; a missing pointer suppresses only the notification. This confines
the resident call to the menu lifetime while replacing the transient
bottom-body context that misplaced the first candidate.

The candidate stores only the classified outcome, timer start, play ticks,
packed date, and packed time. It starts the timer when outer menu `4/1` and
inner Mode Select state `4` are both active, then clears the state after ten
seconds or when the usable menu is left. Current outcome messages use black
text and omit terminal periods.
Successful-load text uses unpadded hours with two-digit minutes and seconds,
followed by the descriptor's timezone-corrected `DD/MM/YYYY HH:MM` modification
time. The user accepted the final placement, duration, presentation, and
timezone-conversion flow on 2026-08-11.

### Early memory-card overlap experiment

An implemented experiment moved the accepted automatic worker's scan and
record-zero load into the startup-resource wait. It retained the worker
operations, accepted status/result pairs, no-load mapping, Continue cleanup,
and post-load save-dependent setup. On 2026-08-11, user runtime testing found
no observable loading-time improvement. The overlap hooks and state were
therefore removed, and automatic loading again starts at Continue. This is a
negative performance result; it does not contradict the static dependency
findings below.

Read-only Ghidra 12.1.2 exports under
`@disassembly/NA2/exports/SLPS_258.37/` establish the dependency
boundary. `FUN_001e0ee0` allocates both the `0x60`-byte memory-card worker at
global `0x006075F4` and the `0x2400`-byte live save object at global
`0x006075F8` before it starts the audio and ROFS tasks. The worker's record-load
case in `FUN_001e2140` allocates a temporary `0x2400`-byte buffer, reads the
record, recomputes and compares its checksum, and copies the validated sections
into that preallocated live object through `FUN_001e30f0`, `FUN_001e2e20`, and
`FUN_001e2c90`. `FUN_001e1e10`, used to request record zero, writes only the
worker's operation, status, result, and record-index fields. For status `0x10`,
`FUN_001e3120(worker, 1)` likewise advances only that worker's operation,
status, and result fields. The pre-controller automatic transition therefore
does not depend on a constructed Save/Load controller, and the record-load path
contains no direct sound-manager call.

Before those tasks are created, startup calls `FUN_001e71b0`, whose
`FUN_001e72e0` child starts the same worker in mode `0` for the native card
environment probe, waits for that probe, and then calls `FUN_001e1d20`.
`FUN_001e1d20` terminates the worker task and clears its handle at offset
`+0x5C`. The tested overlap seam was later, so the experiment restarted an
allocated but stopped worker rather than competing with the probe's worker
task.

The previously unresolved `FUN_001d9600(0)` preparation call is not a
memory-card prerequisite. `FUN_001d9600` delegates only to `FUN_001d9760`,
which gates the sound-manager state byte at offset `+0x186`, calls
`FUN_001d6980` on the sound manager, and resets its current selection at
offset `+0xC0`. The experiment therefore deferred this call until the original
Continue boundary, when the startup audio-ready check had already succeeded,
while allowing the independent card worker to progress earlier.

The experiment used four clean guarded seams:

| Role | Runtime address | ELF offset | Clean instruction |
| --- | ---: | ---: | --- |
| Start the card load immediately before starting the startup audio task | `0x001E1024` | `0xE1124` | `C0 3F 07 0C` (`jal FUN_001cff00`) |
| Advance the automatic phases after each startup-task yield | `0x001E1124` | `0xE1224` | `D0 40 07 0C` (`jal FUN_001d0340`) |
| Reuse the early worker once when the shared Save/Load parent is constructed | `0x001E3DD0` | `0xE3ED0` | `28 87 07 0C` (`jal FUN_001e1ca0`) |
| Consume the overlapped state in Continue | `0x001E9F84` | `0xEA084` | `C0 8F 07 0C` (`jal FUN_001e3f00`) |

A four-byte injected phase word recorded scan, confirmation, load, loaded, or
no-load and one constructor-reuse flag. The begin hook required the native probe
to have left the shared worker with a zero task handle. The startup-yield hook
then drove the same native operations and status transitions as the accepted
late state machine. At Continue, the constructor hook preserved the active
worker instead of creating a duplicate thread, the update hook performed the
deferred sound preparation once, and the controller resumed at the matching
phase. After that one reuse, the injected state was cleared, so later Save/Load
controllers called the native worker constructor normally. If no early state
was established, the accepted late-start implementation remained the fallback.

The worker/save allocation order, direct call graph, hook guards, and absence
of a direct audio dependency in the card operation remain high-confidence
static findings. Runtime testing rejected only the performance hypothesis: the
implemented overlap produced no observable loading-time reduction. The result
does not establish why the overlap was ineffective.

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
color, four-vertex submission, and flush. The displayed value reads the EE
Count register and maps 9,584,640 ticks to each percentage point. Later
nominal-speed notification timing established an effective 294.912 MHz Count
rate, so this historical divisor reaches its `99%` cap after about 3.22 seconds;
the earlier 6.5-second derivation used the rejected half-rate assumption. The
counter never substitutes for real loader completion. This draw hook is also the
presentation boundary where a custom loading-screen background can be added
later without changing loader control flow.

The preceding 195-hook calibration exposed a cadence error. User runtime
observation showed the first visible value near `30%`, followed by visible
updates in four- or five-point steps. The guarded draw call at `0x001E10E0`
runs inside the startup polling loop beginning at `0x001E1064`; the loop then
calls `FUN_001d0340(1)` at `0x001E1124`. That function suspends the current
task through the game's scheduler and is not a VBlank wait. Incrementing the
old counter at the draw hook therefore counted several polling iterations
between presented frames. The Count-register implementation stores the first
tick and derives every later value from elapsed time, so repeated hook calls no
longer accelerate the estimate.

Together with the enabled opening skip, the intended sequence is the timed
loading counter during the boot wait, native menu transition, then main menu.
Confidence is high for the control flow, clean instruction guards, triangle-strip
failure localization, and corrected independent-rectangle sequence. User
runtime validation on 2026-08-11 confirmed the counter presentation, not the
later-rejected half-rate timing derivation. Frame delivery drops during the
later portion of the loading screen, approximately
from `30%` through `99%`, but the time-derived percentage remains correct; the
user accepted that loading-screen presentation characteristic.

## Startup loading-time bottleneck

The enabled startup patches are treated as fixed for this analysis. In
particular, the early loading-screen draw and silent first-save load remain in
place; neither one causes the long startup wait.

The startup-resource task `FUN_001d2570` does not set its completion byte at
object offset `+0x1C` until `FUN_001d9650` returns. That function constructs the
sound manager through `FUN_001d7a30` and then performs eager archive/index
initialization through `FUN_001d6550`. The latter operation is the startup
bottleneck:

1. `FUN_001d6b60` opens, in order, `sound.afs`, `stream.afs`, `rpgvoice.afs`,
   and `plvoice.afs`.
2. `FUN_001d6c70` then loads 13 `sound.afs` index entries, 82 `rpgvoice.afs`
   index entries, and 93 `plvoice.afs` index entries. `stream.afs` has no
   corresponding per-entry loop here.
3. Every helper starts one ADXF operation and yields one scheduler tick at a
   time until that operation reaches state `3`; only then does the caller begin
   the next operation. The ADXF path uses one global current-operation record,
   including the current ID and state at `0x003D3BC4` and `0x003D3BC8`, so
   simply issuing several requests at once is not a safe parallelization.

The eager phase therefore performs 188 serialized index loads after opening
the four archive roots. The archive-specific index-ID ranges are `0..` for
`sound.afs`, `20..149` for `rpgvoice.afs`, and `150..242` for `plvoice.afs`.
The sound-manager constructor allocates the destination buffers for all of
these entries before `FUN_001d6550` starts loading them, which makes later
selective initialization structurally possible without changing the existing
buffer layout.

Read-only inspection of user-supplied savestates confirms the static trace:

| CRC and state | ROFS ready `0x006074A0` | Audio ready `[*0x0060755C + 0x1C]` | ADXF ID/state | Loading draw state |
| --- | ---: | ---: | --- | --- |
| `FDAFF23A ss1` | `0` | `0` | `6 / 2` | not sampled |
| `0F5E7D97 ss1` | `1` | `0` | `28 / 2` | not sampled |
| `D5AA8F48 ss1` | `1` | `0` | `51 / 2` | frame `344`, displayed `5` |
| `D5AA8F48 ss2` | `1` | `0` | `88 / 2` | frame `488`, displayed `8` |
| `FDAFF23A ss2` | `1` | `0` | `160 / 2` | not sampled |
| `D5AA89FC ss1` | `1` | `0` | `236 / 2` | not sampled |
| `FDAFF23A ss3` | `1` | `0` | `239 / 2` | not sampled |
| `FDAFF23A ss4` | `1` | `1` | `242 / 3` | not sampled |
| `D5AA8B06 ss2` | `1` | `1` | `242 / 3` | not sampled |

The ROFS task has already completed in every intermediate sample after the
earliest one, while the audio task advances through both voice ranges and does
not report ready until the final player-voice entry completes. Consequently:

- the 60-tick yield in the independent ROFS task is not on the critical tail;
- changing the loading-counter pacing cannot shorten startup because that
  counter never supplies either readiness value;
- removing the one-tick yields from the ADXF polling loops would not shorten
  the underlying I/O and could starve the asynchronous worker;
- forcing the audio-ready byte early is invalid because later consumers would
  observe uninitialized archive/index buffers.

NUN5 and NUN6 use the same 60-tick ROFS delay and the same serialized audio
initialization shape. They do not provide a donor implementation that already
solves this bottleneck.

### Voice consumer boundary

`FUN_001d6010` is the resident `rpgvoice.afs` playback wrapper: it forwards to
`FUN_001d97d0` with archive category `2`. An exhaustive direct-call search of
the three exported overlays finds 24 call sites in `ADV.BIN`, no call site in
`ETC.BIN`, and one call site in `BTL.BIN`. The battle call requests bank
`0x4E`; therefore the enabled removal of Adventure mode does **not** make the
entire RPG-voice archive dead. It does make the other 81 eagerly initialized
RPG-voice banks the strongest proven omission candidates, subject to runtime
validation against any unresolved indirect consumer.

Player/battle voice uses archive category `3` through the resident four-slot
voice queue in `FUN_001d2c20`. Its 93-entry table matches the game's
`1..0x5D` character-ID span, which suggests one bank per character identity,
but that exact mapping remains an inference until the queue producer is fully
traced or sampled at runtime. The table cannot be globally omitted because
battle voices remain an enabled, reachable feature.

### Reduction candidates

The evidence supports the following order of work:

1. **Prune unused RPG-voice banks.** Keep the `rpgvoice.afs` root and bank
   `0x4E`, but skip the other 81 index loads while Adventure mode is removed.
   This removes 81 of the 188 serialized index operations (`43.1%`) rather
   than moving them to a later screen. The percentage describes operation
   count, not elapsed time; entry sizes and device latency differ.
2. **Initialize player voices on demand.** Leave their buffers allocated, but
   defer the `plvoice.afs` root and its 93 index loads until a transition before
   the first player-voice consumer. A stronger form would load and cache only
   the banks needed by the selected fighters and supports. Combined with the
   first candidate, this removes or defers 174 of 188 eager boot index loads
   (`92.6%`), leaving the 13 sound entries and the retained RPG battle bank at
   boot. This is the largest plausible startup reduction, but it needs a proven
   safe transition and the exact character-to-bank mapping; otherwise it merely
   moves the same wait to the first battle.
3. **Do not reintroduce the tested memory-card overlap as a loading-time
   optimization.** The experiment used the independent worker boundary above,
   drove the native scan and record-zero load during the startup wait, and
   deferred the sound-only `FUN_001d9600` call until Continue. User runtime
   testing found no observable loading-time reduction. The static separation
   remains useful knowledge, but the performance hypothesis is rejected for
   this implementation and startup path.

Reducing primitive submissions in the enabled loading-screen renderer may save
minor CPU/GS work per frame, but the renderer is not a completion dependency
and is not a meaningful first loading-time target.

The most conservative implementation experiment was candidate 1 alone. The
implemented design instead uses selective, cached initialization for both voice
archives. User timing established the startup reduction; exact per-bank
first-use latency remains unmeasured.

### Selective voice-index implementation seam

The clean resident ELF exposes three guarded call sites used by the full-lazy
implementation:

| Role | Runtime address | ELF offset | Clean instruction |
| --- | ---: | ---: | --- |
| Call eager archive/index initialization from `FUN_001d9650` | `0x001D9660` | `0xD9760` | `54 59 07 0C` (`jal FUN_001d6550`) |
| Play a queued player-voice clip from `FUN_001d2c20` | `0x001D2CA0` | `0xD2DA0` | `F4 65 07 0C` (`jal FUN_001d97d0`) |
| Play an RPG-voice clip from `FUN_001d6010` | `0x001D601C` | `0xD611C` | `F4 65 07 0C` (`jal FUN_001d97d0`) |

The audio-manager pointer is stored at `0x00607558`. Its RPG and player bank
counts are at offsets `+0x704` and `+0x708`; the corresponding index-buffer
pointer arrays begin at `+0x17C` and `+0x40C`, with eight bytes per bank. The
RPG table begins at `0x003FDD50` and its archive handle is the halfword at
`0x00602C4C`; the player table begins at `0x003FDFF0` and uses the halfword at
`0x00602C4E`. Each table record is eight bytes and starts with the ADXF index
ID consumed by `FUN_001d6c70(manager, index_id, archive_handle, bank, buffer)`.

The implemented patch temporarily sets both voice counts to zero,
calls the unchanged `FUN_001d6550`, and then restores the counts. This preserves
all four opened archive roots and the 13 eagerly initialized general-sound
indexes while deferring all 175 voice indexes (`93.1%` of the original 188 boot
index operations). The two playback hooks load the requested bank once, cache
its bit, and then call the unchanged `FUN_001d97d0` with category `2` or `3`.

Because the ADXF initialization path is not safe for concurrent requests, the
patch serializes first-use loads with one process-lifetime EE semaphore.
The resident syscall wrappers are `CreateSema` at `0x0015DCE0`, `SignalSema` at
`0x0015DD00`, and `WaitSema` at `0x0015DD20`; the local PS2SDK `ee_sema_t`
layout is six 32-bit fields (`count`, `max_count`, `init_count`, `wait_threads`,
`attr`, and `option`). If semaphore creation fails, the startup wrapper retains
the complete eager initializer instead of enabling lazy loading. User runtime
timing on 2026-08-11 measured the integrated startup load at about 15 seconds,
10 seconds shorter than the prior 25-second baseline. A subsequent observation
in the current launch setup measured the visible loading screen at about 6-7
seconds. The user accepted the integrated patch on 2026-08-11. That acceptance
did not separately isolate repeated or concurrent first-use voice playback or
measure whether a first-use bank load causes an objectionable hitch.
