# Ultimate-Jutsu contest behavior

Native Ultimate-Jutsu contest ownership, input, update, and presentation paths
in clean NA2.

## Research coverage

- **Assigned scope:** the battle-side contest object, its common update and
  render dispatchers, contest input calls, and related unresolved chakra leads.
- **Exploration depth:** the clean BTL controller was traced through the
  resident contest factory, common manager dispatch, contest input accessor,
  and candidate presentation owners used by the tested contest path.
- **Confirmed coverage:** contest type `0` allocates no object; allocated
  contests share common update and render dispatchers; the two controller calls
  use input bank `1`, slot `0`; and the renderer is distinct from input and
  lifecycle ownership.
- **Unresolved or untested:** the physical-controller mapping of the logical
  input slot and the individual lifecycle field required by post-contest
  awakening remain unresolved. Historical chakra-address leads are unverified.
- **Deliberate exclusions and overlap:** feature behavior belongs to
  [Battle](../../features/battle.md); general awakening behavior belongs to
  [Awakening](awakening.md); other battle systems are not covered here.
- **Evidence limitations:** static conclusions use the identified clean BTL and
  resident images. Runtime observations cover the tested contest path rather
  than every contest type.

## Contest object and dispatch

The clean BTL image identified in
[Standard game file identities](../game/files/file_identities.md) contains the
battle-side controller for the Ultimate-Jutsu input contest. Addresses below
use the canonical BTL conversion.

In state `1`, BTL sign-extends the selected contest type into `t0` and calls
resident `FUN_0035CF00`. That routine forwards the type through
`FUN_0036C120` to `FUN_0036B6D0`: type `1` randomizes among contest
implementations, types `2` through `6` allocate their respective contest
objects, and type `0` matches no allocation branch.

With no object at resident global `0x00607750`, the main manager cannot invoke
either update dispatcher `FUN_0036BF10` or render dispatcher `FUN_0036BFF0`.
The latter dispatches vtable slot `+0x0C` for every allocated contest type, and
each type's slot draws its meter, prompts, and result. Its sole direct caller
is resident `0x001F0940`, ELF offset `0xF0A40`, with instruction bytes
`FCAF0D0C`.

## Input path

In contest state `1`, the controller calls resident press-state accessor
`FUN_001D99B0(1, 0)` at exported BTL `0x00769F54` to latch a press into inner
field `+0x3A`, then calls the same accessor at exported `0x0076A1B0` while
waiting for release. The live addresses are `0x00769F94` and `0x0076A1F0`, at
BTL file offsets `0xB6094` and `0xB62F0`.

The accessor contains two three-byte input-state banks. Its first argument
selects bank `0` or `1`, and its second indexes slot `0` through `2`. Both
contest calls use bank `1`, slot `0`. This static slice does not establish how
physical controllers map to that logical slot.

The wrapper's flags byte at `+0x10` gates only auxiliary inner-object pointers.
Tests of that byte did not change the visible contest interface. An early
return at BTL file offset `0x17E0` also had no effect because that renderer
belongs to the command-list interface; returning from the controller render
entry at `0xB69E0` likewise left the contest interface visible. These negative
results exclude all three as presentation owners.

## Unresolved chakra leads

Historical notes point to ELF file offset `0x1492B0` for level-scaled chakra
subtraction and `FUN_002254A0` for shared chakra addition. The latter is
confirmed as a general chakra-addition function in [Damage](damage.md), but its
relevance to this Ultimate-Jutsu path and the subtraction-site role must be
rechecked before either is used.
