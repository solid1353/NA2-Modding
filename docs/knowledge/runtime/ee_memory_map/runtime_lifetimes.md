# EE runtime lifetimes

Native lifetime and ownership evidence for overlays, stacks, and the
high-memory tail.

## Research coverage

- **Assigned scope:** establish which large EE memory ranges are resident,
  overlay-owned, allocator-owned, stack-owned, or otherwise unsafe for fixed
  storage.
- **Exploration depth:** all native overlay kinds, the six static CRI/ADX
  stacks, dynamic-thread allocation, and sampled high-memory states were
  examined.
- **Confirmed coverage:** overlay effective ends, phase-only slack, static
  stack ranges, and dynamic-thread stack ownership are established.
- **Unresolved or untested:** exact byte-level ownership throughout the
  `0x01FF6000..0x02000000` high-memory tail.
- **Deliberate exclusions and overlap:** current payload and hot-reload behavior
  belong to [Runtime injection](../../../features/runtime_injection/implementation.md).
- **Evidence limitations:** observed phase slack is temporary and cannot prove
  that an address remains unused across later transitions.

## Overlay lifetimes and phase-only space

Each loaded overlay begins with `MWo3` at `0x006B3F00`; header word 1 identifies
the kind.

| State at overlay base | Kind | Effective end | Temporarily unused before `0x008DD080` |
| --- | ---: | ---: | ---: |
| No overlay | 0 | `0x006B3F00` | `0x229180` |
| `BTL.BIN` | 1 | `0x008DD080` | `0x0` |
| `ADV.BIN` | 2 | `0x008C7200` | `0x15E80` |
| `ETC.BIN` | 3 | `0x006E4E00` | `0x1F8280` |

This slack is not persistent free memory. A later overlay transition can
overwrite it, and `BTL.BIN` consumes the complete window. A phase-local
experiment must guard overlay identity, load state, and lifetime.

## Stacks and thread-owned memory

Six resident CRI/ADX thread stacks are statically allocated inside the main
ELF:

| Range | Size |
| --- | ---: |
| `0x003D6B20..0x003D7320` | `0x800` |
| `0x003D7320..0x003D8320` | `0x1000` |
| `0x003D8320..0x003D9320` | `0x1000` |
| `0x003D9320..0x003DA320` | `0x1000` |
| `0x003DA320..0x003DC320` | `0x2000` |
| `0x003DC320..0x003DE320` | `0x2000` |

Their creation paths are `FUN_0012E6B0` through `FUN_0012E9B8`.
`FUN_001CFE50` separately enforces a requested dynamic-thread stack minimum of
`0x800`, adds `0x400`, and obtains the backing memory through the game
allocator. Those stacks therefore have thread-specific allocator lifetimes.

The `0x01FF6000..0x02000000` tail is outside the game allocator and changed
across sampled states. Its exact ownership is incomplete, but its position and
observed use establish that it must remain reserved for the system runtime.
