# NUN6 battle reference

The analyzed [NUN6 A35 source](../source.md#source-identity) provides
comparative implementation evidence from its resident executable, `BTL.BIN`,
and `MOD.BIN`. The BTL and MOD disassembly omits each file's `0x40` header, so
live addresses are displayed addresses plus `0x40`; resident addresses below
are live addresses.

## Ultimate Jutsu contest

NUN6 retains a disabled contest-type `0` path in homologs `FUN_00369200`,
`FUN_003789B0`, and `FUN_00377F20`. This corroborates the no-object behavior
used by NA228's `no_contest` setting, although NA228 retains its own native
contest lifecycle rather than copying this path.

## Support

Resident `FUN_00240330` checks input, active-slot presence, fighter
`+0xB00/+0xB10`, and a global gate before requesting support. Its empty-slot
threshold block at `0x00240414` jumps to live MOD `0x00947834` (display
`0x009477F4`). That trampoline rejects a nonzero fighter byte `+0xB64`;
otherwise it loads gauge `+0x74` and returns to the comparison using
`0x3F800000` (`1.0`). The meaning of `+0xB64` is unresolved. Active
re-requests bypass this threshold in the inspected resident routine.

The active drain is resident `FUN_00240720`. Its subtraction constant at
`0x00240738..0x00240740` is `0x3B839930`, approximately
`0.0040160641074180603`. Its upper clamp at `0x002407E8` is `0x3DCC0000`,
exactly `0.099609375`. The first active update from a full gauge therefore
reduces it to that cap; later active updates subtract the constant until zero.
Slot presence selects active drain rather than inactive recharge. Resident
`FUN_00240600` separately uses approximately
`0.0010027608 * recharge_multiplier` for inactive recharge.

The common introduction routine at live BTL `0x008A6B40` (display
`FUN_008A6B00`) prepares the summon position and animation. At display
`0x008A6D30..0x008A6D40`, animation completion invokes virtual `+0x48` with
state `1`. The state-`1` handler at live `0x008A6DA0` (display
`FUN_008A6D60`) uses the same request-latch shape as NA2: side-record selector
`1` calls live `0x008A7960` to set halfword `+0xE8 = 3`. That substate
approaches the opponent when outside its range, or calls virtual `+0x48` with
state `2` when its range/condition check passes. These bytes do not prove a
direct, unconditional transition from creation to attack.

In NA2, the corresponding introduction setup reaches its position helper at
live `0x00889A70` (display `0x00889A30`), and the common state transition at
live `0x00889540` prepares attack animation/state for reason `2`. State `1`
approaches through the `+0xE8 == 3` arm at display `0x0088A530` and requests
reason `2` at `0x0088A5C0`. The common transition and subclass overrides are
the native attack-initialization interface; assigning only state bytes would
bypass it.

Two NUN5/NUN6 comparison sites were rejected for NA2. At exported BTL address
`0x00791858`, NUN5 calls a helper with bytes `54491E0C` while NUN6 uses a NOP;
the NA2 structural homolog at file offset `0xC5A5C` (`0x0077991C`, clean bytes
`54E91D0C`) does not consume the manual support call. The adjacent NA2 call at
file offset `0xC5E64` (`0x00779D24`, clean bytes `20E81D0C`) operates on combat
object flags rather than live input and also does not consume that call.

Recognized fragments were disassembled directly; raw bytes supplied the
missing MOD trampoline and internal blocks not represented as complete
functions. These findings have no NUN6 runtime confirmation and do not
establish visible timing or every specialized support's behavior.
