# EE runtime lifetimes

Lifetime and ownership evidence for overlays, stacks, retired mode-switch injection, and the visible hot-reload hook.

## Overlay lifetimes and phase-only space

Each loaded overlay begins with `MWo3` at `0x006B3F00`; header word 1 identifies
the kind. The effective ends below come from the binary layout and were matched
against the savestate headers.

| State at overlay base | Kind | Effective end | Temporarily unused before `0x008DD080` |
| --- | ---: | ---: | ---: |
| No overlay | 0 | `0x006B3F00` | `0x229180` (2,265,472 bytes) |
| `BTL.BIN` | 1 | `0x008DD080` | `0x0` |
| `ADV.BIN` | 2 | `0x008C7200` | `0x15E80` (89,728 bytes) |
| `ETC.BIN` | 3 | `0x006E4E00` | `0x1F8280` (2,065,024 bytes) |

This slack is not persistent free memory. A later overlay transition can
overwrite it, and `BTL.BIN` consumes the entire reserved window. It is unsuitable
for unguarded PNACH writes or resident code/data. A phase-local experiment may
use it only when overlay identity, load state, and lifetime are explicitly
guarded.

## Stacks and thread-owned memory

Six resident CRI/ADX thread stacks are statically allocated inside the main ELF:

| Range | Size |
| --- | ---: |
| `0x003D6B20-0x003D7320` | `0x800` |
| `0x003D7320-0x003D8320` | `0x1000` |
| `0x003D8320-0x003D9320` | `0x1000` |
| `0x003D9320-0x003DA320` | `0x1000` |
| `0x003DA320-0x003DC320` | `0x2000` |
| `0x003DC320-0x003DE320` | `0x2000` |

The corresponding creation paths are `FUN_0012E6B0` through
`FUN_0012E9B8`. Separately, `FUN_001CFE50` enforces a requested dynamic-thread
stack minimum of `0x800`, adds `0x400`, and obtains the backing memory through
the game allocator before `CreateThread`. These stacks therefore contribute to
ordinary heap occupancy and have thread-specific lifetimes.

The `0x01FF6000-0x02000000` tail is outside that allocator and changed across
the captures. Register-level ownership of every byte was not established, but
its observed use and position make the conservative classification clear:
leave it to the system/stack runtime.

## Retired Injection Lab mode-switch lifetime

The retired Lab's generic mode installed a recurring call at runtime
`0x001D0578`, while production mode redirects one resident `228.BIN` entry to
the fixed dispatcher at `0x008F0000`. Removing the PNACH restores the file on
disk but cannot undo either write already applied to EE memory.

The 2026-07-29 generic-to-production trial proved the resulting hazard. The
same PCSX2 session first activated the generic dispatcher, removed its PNACH,
then installed production entry `v2_controls_adapter`
without restarting Current. Production repointed the dispatcher while the
old generic per-frame call remained live. That stale call invoked the Font
entry with unrelated registers, including `a0 = 0x7`, producing repeated
loads from address `0x7` at hot-linked PC `0x008F01A0`
(`v2_measure + 0x58`) and cascading native renderer TLB
misses at `0x001858D0` and `0x001896E8`.

This was a lifecycle conflict, not a different Font ABI or bad C compilation:

- the guarded production caller at `0x00388748` loads the text pointer into
  `a0`, style into `a1`, and centers into `f12`/`f13`;
- the banked controls fragment matched the exact resident fragment byte for
  byte except its expected relocated call to `adapter_call`; and
- the first invalid access began only after production reused the dispatcher
  in the still-running generic session.

This was a Lab/PNACH lifecycle hazard. The maintained direct-PINE transaction
does not install recurring cheat writes, share a dispatcher between modes, or
maintain install/remove state. Exact caller guards still determine whether a
candidate is compatible with the current runtime state.

## Visible hot-reload smoke hook

The maintained project hot-reload message uses the native ordinary text draw at
runtime `0x00379040` to display the watcher-generated `HOT RELOAD HH:mm:ss`
label at the top-left for 300 rendered frames after every direct-PINE apply.
Its frame counter lives in the injected zero-fill range, so each apply resets
the visible interval without log inspection.

The smoke caller is the native no-op call at runtime `0x001085A0` inside
`FUN_00108490`. The game establishes its renderer context before this point,
and flushes the renderer afterward. Clean Current bytes are
`A021040C00000000` (`jal 0x00108680; nop`); the injected manifest replaces only
that pair with `jal project.hot_reload_message; nop`.

The earlier `0x001D0578` hook belongs to a scheduler-thread wakeup path and is
not a valid drawing phase. A session that already contains that old hook must
be restarted or have a clean compatible savestate loaded once before applying
the visible-marker build. Confidence is **high** for the clean bytes, native
draw address, and placement within the renderer-finalization path; the marker's
exact appearance remains user-runtime validation.
