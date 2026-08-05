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

Patch `ELF-Q009` changes the call at boot-ELF file offset `0xE11A0`, virtual
address `0x001E11A0`, from bytes `60 82 07 0C` (`jal 0x001E0980`) to
`BC 79 07 0C` (`jal 0x001DE6F0`). The startup loop therefore advances the
native opening-sequence state machine instead of the four-logo controller while
preserving the caller's loader checks and splash cleanup.

`0x001DE6F0` is the native post-splash sequence dispatcher. In the original
order it runs after the four splashes and before the title. Patch `ELF-Q001`
retains its proven branch past the CyberConnect2 intro. Patch `ELF-Q005` is
disabled, so the dispatcher calls the native sequence object with selector `2`,
the established opening path. Because the dispatcher is now updated from main
startup state `0`, opening playback can overlap the ROFS/data and startup-
resource loads rather than beginning only after them. Skipping the opening with
Start does not bypass those loader checks; if they are still incomplete, the
screen remains black until they finish before the direct main-menu transition.

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
address `0x001E12CC` (file offset `0xE12CC`). `ELF-Q009` changes bytes
`02 00 03 24` (`addiu v1, zero, 2`) to `03 00 03 24`, selecting title-input
state `3` without running the title-animation state. The title-input dispatcher
at virtual address `0x001E1340` (file offset `0xE1340`) normally calls
`0x001DE840`; return value `1` is the accepted-Start result. The patch changes
bytes `10 7A 07 0C` to `01 00 02 24`, returning that result immediately. The
unchanged caller then writes main state `4` and substate `1`, matching ss2-ss4,
and the native menu controller advances through its loading phases to the
usable main menu.

Confidence is high: function/resource ownership and control flow are statically
established, and both supplied state batches establish the splash, loader,
title, and post-Start boundaries. Integrated runtime behavior remains
unverified until the user runs a build containing `ELF-Q009`.
