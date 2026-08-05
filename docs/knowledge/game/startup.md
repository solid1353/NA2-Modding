# Startup sequence

## Splash controller

Game: NA2.28 boot ELF `SLPS_258.37`. Investigation date: 2026-08-05.

The resident function at `0x001E0390` constructs four splash objects using,
in order, `TEX_logo_notice_pss`, `TEX_logo_bn_pss`, `TEX_logo_b_pss`, and
`TEX_logo_adx_pss`. The controller update at `0x001E0980` advances those four
objects. Its caller at `0x001E10A0` treats return value `1` as completion,
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
address `0x001E10A0`, from bytes `60 82 07 0C` (`jal 0x001E0980`) to
`01 00 02 24` (`addiu v0, zero, 1`). This reports immediate completion without
skipping the caller's cleanup or the native title-animation initialization.

Confidence is high: function/resource ownership and control flow are statically
established, and the supplied state memories establish the boundary before and
after the controller. Integrated runtime behavior remains unverified until the
user runs a build containing `ELF-Q009`.
