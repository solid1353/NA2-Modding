# EE runtime lifetimes

Lifetime and ownership evidence for overlays, stacks, and the visible hot-reload hook.

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
