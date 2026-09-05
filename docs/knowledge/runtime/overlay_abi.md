# NA2 MWo3 overlay ABI

Static clean-binary evidence for the resident runtime overlay loader and the
clean `BTL.BIN` / `ETC.BIN` images in NA2 v2.28. In this document, **common**
means proven in both of those scoped images and in this resident executable;
it does not claim that every CyberConnect2 or Metrowerks `MWo3` variant has the
same contract. The other NA2 overlay image is deliberately outside this
analysis.

## Research coverage

- **Assigned scope:** this work was limited to the reusable file/runtime ABI of
the clean NA2 v2.28 resident `SLPS_258.37`, `PRG/BTL.BIN`, and `PRG/ETC.BIN`:
header layout, placement and clearing, constructor behavior, fixed-address
resident/overlay linkage, selection/cache/lifetime behavior, and the exact
resident loader path. It did not attempt a general vendor-format specification.

- **Exploration depth:** full-file identity/size checks covered the clean
BTL range `0x000000-0x222300` and clean ETC range `0x000000-0x030F00`.
Targeted raw byte/R5900 inspection covered their headers, span boundaries,
constructor/tail regions, and the specific calls, entries, and pointer chains
cited below, plus the resident ELF/program metadata and bytes needed by the
recovered functions and tables. Preserved Ghidra C/listing exports for all
three inputs were used for decoded-instruction censuses and call-graph
discovery; key address-sensitive conclusions were checked against raw
disassembly because the preserved overlay imports omit the first `0x40` bytes.

Coverage depth was deliberately mixed:

  **Exhaustive within the scoped clean files:** all 0x40-byte header words and
  exact span arithmetic; the complete BTL constructor pointer interval at raw
  `0x222280-0x2222A4` and all nine targets; ETC's empty interval; file tails;
  all decoded direct `jal` targets, decoded `jalr` sites, and decoded
  `$gp`-relative references in both overlay listings. The listing-wide resident
  scan exhaustively found direct calls to the loader, post-read initializer,
  and selector within decoded code, and direct resident `jal` targets in the
  two scoped overlay reservations.
  **Exhaustive for the recovered load/select chain:** `FUN_001BE7F0`, path
  helper `FUN_001BE110`, post-read `FUN_00100270`, constructor walker
  `FUN_00119A90`, selector `FUN_001F3D10`, restore helper `FUN_001F45B0`,
  destination table `0x006029C0-0x00602A00`, and filename table
  `0x004049E0-0x004049EC` were traced through all branches visible in the clean
  executable. Manager bootstrap/reset functions `FUN_001E9980`,
  `FUN_001F4200`, `FUN_001F4360`, and `FUN_001F4680`, plus the CD/DVD-readiness
  gate through `FUN_00105FC0`, `FUN_00107F80`, `FUN_001086C0`, and
  `FUN_00173328`, were bounded extensions of that chain.
  **Bounded application-lifetime tracing:** the five scoped selector callsites
  and the Collection and selected BTL setup/teardown paths were traced
  far enough to prove ordering and the contracts listed below. This was not a
  semantic audit of every BTL/ETC routine or every resident mode state.
  **Sampled ABI recovery:** typed calling-convention examples, full-width
  callee-save behavior, absolute initialized-data pointer chains, and selected
  shared-address entry bytes were raw-verified samples. The numerical
  call/reference censuses are complete for decoded listings, but semantic names
  and prototypes were recovered only where caller/callee evidence was strong.

- **Confirmed coverage:** the evidence establishes the common
header meanings; fixed load base and full-file mapping; exact text/data/BSS
layouts; absence of runtime relocation/import/export resolution; inherited
resident `$gp`; constructor-only automatic entry; lack of a generic exit hook;
exact retry, cache-publication, and stale-tail behavior; fixed-address direct
and indirect call conventions; image-specific application entry/cleanup
contracts; and the minimum runtime identity guards for the clean BTL and ETC
images.

- **Unresolved or untested:** remaining work includes original vendor field and
type names, other `MWo3` versions, kind values outside the two scoped images,
precise linker-section composition, complete typed prototypes and semantics for
the fixed-address surface, dynamic targets for indirect calls, the higher-level
synchronization invariant that prevents replacement during execution, and
cleanup paths beyond the representative state machines. No claim of exhaustive
semantic coverage is made for the resident, BTL, or ETC programs as a whole.

- **Deliberate exclusions and overlap:** the other NA2 overlay and Adventure behavior were
excluded, as were widescreen, media, timing, substitution, and damage scopes.
Mode-flow details were followed only where they prove overlay ownership or
lifetime; adjacent gameplay/UI findings belong to their scoped canonical
records. Geometric residence inside BTL's larger address range was never used
alone to assign an outgoing call to BTL.

- **Evidence limitations:** this is primarily static clean-binary evidence. No new
runtime injection, concurrent-load experiment, malformed-file experiment, or
hardware/PCSX2 execution was performed for this record. Ghidra-decoded
censuses omit code the importer marked as data, notably BTL's late constructor
routines; those known routines were disassembled separately but no claim is
made that every executable data-span byte was discovered. Static race and
failure-mode descriptions identify reachable instruction behavior, not an
observed retail failure.

## Result

The reusable NA2 contract is small and unusually unforgiving:

- The resident loader reads the **complete raw file, including its 0x40-byte
  header**, to the fixed destination `0x006B3F00`.
- Raw file offset `x` is therefore live EE address `0x006B3F00 + x`.
- The clean files are already linked for that address. The resident does no
  relocation, import lookup, export lookup, magic validation, or base
  validation.
- Header offsets `0x0C`, `0x10`, and `0x14` are text, data, and BSS byte counts.
  Offset `0x10` is **not** a relocation-stream size.
- The only format-level automatic entry hook is the half-open constructor
  pointer interval in header words `+0x18` and `+0x1C`.
- There is no format-level exit/destructor hook in the header or loader.
  Ordinary mode paths perform cleanup they know about before selecting a new
  image; the loader itself will overwrite the shared slot without invoking it.
- Resident/overlay calls are a statically linked, fixed-address ABI. Both sides
  use direct `jal`, indirect `jalr`, absolute 32-bit pointers, and the resident
  `$gp` value.
- The word at `+0x04` is a useful overlay identity (`1` for clean BTL, `3` for
  clean ETC), but the loader itself never checks it.

Consequently, a safe consumer must identify the current image before using any
overlay address. Magic alone is insufficient because both images share it and
the same base.

## Inputs and identity

The resident, BTL, and 200,448-byte (`0x30F00`) ETC inputs follow
[Standard game file identities](../game/files/file_identities.md).

The resident ELF is stripped: its `.symtab` contains zero entries and its
`.strtab` is empty. Names such as `FUN_001BE7F0`, `SUB_001CC350`, and
`mwo3_entry` below are preserved Ghidra/project labels, not original program
symbols. Recognized SDK names such as `FlushCache` and literal product strings
are the exceptions. The two original header labels are `BTL_product.bin` and
`ETC_product.bin`.

The resident ELF's first `PT_LOAD` maps file `0x100` to EE `0x00100000`, has
file size `0x507380`, and has memory size `0x5B3F00`, ending exactly at the
overlay base. Its zero-file-size overlay reservations include these two scoped
layouts at the same base:

| Image | Reserved `PT_LOAD` base | Memory size | End |
| --- | ---: | ---: | ---: |
| BTL | `0x006B3F00` | `0x229180` | `0x008DD080` |
| ETC | `0x006B3F00` | `0x030F00` | `0x006E4E00` |

These are zero-based program-header entries 1 and 3. Both are `PT_LOAD`
records at ELF file offset `0x507480`, have `p_filesz = 0`, flags `RWE`, and
alignment `0x80`; their respective `p_memsz` values are the sizes above. The
intervening reservation is outside this document's scope.

## File, runtime, and preserved-Ghidra addresses

Shared BTL address conversion follows
[Standard game file identities](../game/files/file_identities.md). The same
header-omitting import convention applies to the scoped ETC project. Encoded
pointers and `j`/`jal` targets inside either file are already runtime addresses.

The complete-file read to destination slot 1 proves this mapping without a
runtime-capture assumption. It is independently consistent with every decoded
absolute pointer and branch target sampled in both clean files, including the
constructor entries and resident-to-overlay call targets below.

The shift also explains a common disassembly trap. Clean BTL stores constructor
target `0x008D3400`; its bytes begin at raw `0x21F500`, while the header-skipped
Ghidra import displays those bytes at `0x008D33C0`. Similarly, a direct internal
BTL call at raw `0x2BC` encodes target `0x006B44E0`, whose target bytes begin at
raw `0x5E0`. A Ghidra label at displayed `0x006B44E0` is attached to bytes
`0x40` later than that live target. Use raw offsets plus the full-file runtime
formula when validating any call target.

This can produce a plausible but false decompilation, not just a cosmetic
label shift. Live BTL `0x007190D0` calls live `0x007194B0`, whose raw code
initializes 28 records. The preserved decompiler resolves `FUN_007194B0` at
displayed `0x007194B0`, which is raw live `0x007194F0`, the return tail, and
therefore reports a no-op. The actual `0x007194B0` callee bytes appear at
displayed `0x00719470`. For encoded absolute calls, trust the encoded live
target, convert it back to raw, and inspect those bytes; do not trust a
same-number function label in the header-skipped project.

The same defect affects data XREFs and recovered switch tables:

- BTL raw `0x1F3EC0` / live `0x008A7DC0` contains absolute word
  `0x008CC3C0`. Its real target is raw `0x2184C0`, a `u16` table beginning
  `0,1,2,3,4,5`. The preserved listing displays the source at `0x008A7D80`
  and attaches the target name `PTR_DAT_008CC3C0` to raw `0x218500`, whose
  table instead begins `0x00A0,0x00A1`; that target is exactly `0x40` late.
- ETC raw `0x30BE0` / live `0x006E4AE0` contains `0x006E4AD8`; the word at
  that real target, raw `0x30BD8`, is `0x006E2FA0`, which points to the string
  `ccHomeIspBase`. The preserved listing displays the source at `0x006E4AA0`
  and misclassifies `0x006E4AD8` as a switch case. It has again resolved the
  live numeric pointer against a display address rather than raw `target -
  0x006B3F00`.

These chains are also direct evidence that initialized data, not only code and
constructor entries, embeds final absolute addresses.

## Common 0x40-byte header

All integers are little-endian `u32` values. The semantic names are recovered
from the clean layouts and loader behavior, not vendor documentation.

| Offset | Size | Recovered meaning | Resident loader use | Confidence |
| ---: | ---: | --- | --- | --- |
| `0x00` | `4` | ASCII magic `MWo3` (`0x336F574D` as a little-endian word) | None; not validated | High |
| `0x04` | `4` | Overlay kind/identity | None; BTL=`1`, ETC=`3` | High for values; medium for the original field name |
| `0x08` | `4` | Linked image/header base | None; both store `0x006B3F00` | High |
| `0x0C` | `4` | Text-span byte count beginning at raw `0x40` | None | High |
| `0x10` | `4` | Initialized data-span byte count following text | None | High |
| `0x14` | `4` | BSS byte count following the physical file bytes | Read by `FUN_00100270` | High |
| `0x18` | `4` | Absolute address of first constructor-pointer entry | Read by `FUN_00100270` | High |
| `0x1C` | `4` | Absolute exclusive end of constructor-pointer entries | Read by `FUN_00100270` | High |
| `0x20` | `0x20` | NUL-terminated, zero-padded product label | None | High |

For both clean images:

```text
physical_file_size = 0x40 + text_size + data_size
file_backed_end     = load_base + physical_file_size
effective_end       = file_backed_end + bss_size
```

The loader obtains `physical_file_size` with `lseek`; it does not calculate or
cross-check it from the header. It also clears BSS at
`destination + bytes_read`, not at an address calculated from the text/data
words. The equations are properties of the valid clean images, not validation
performed by the game.

The text/data words identify linker spans, not EE page permissions. The EE
reservation is RWE, and BTL has executable constructor functions late in the
nominal data span.

This also exposes a preserved-analysis limitation. Workshop script
`PrepareMwo3.java` splits the imported block at the supplied text length and
marks the second block non-executable. Ghidra therefore represents BTL's late
constructor targets as data and does not recover their functions or calls.
Their instruction evidence in this document comes from raw R5900 disassembly
using the full-file runtime mapping, not from the decompiler export.

## Exact clean layouts

| Property | BTL | ETC |
| --- | ---: | ---: |
| Kind (`+0x04`) | `1` | `3` |
| Base (`+0x08`) | `0x006B3F00` | `0x006B3F00` |
| Text size (`+0x0C`) | `0x1DB6C0` | `0x024E40` |
| Data size (`+0x10`) | `0x046C00` | `0x00C080` |
| BSS size (`+0x14`) | `0x006E80` | `0x000000` |
| Constructor begin (`+0x18`) | `0x008D6180` | `0x006E4E00` |
| Constructor end (`+0x1C`) | `0x008D61A4` | `0x006E4E00` |
| Product label (`+0x20`) | `BTL_product.bin` | `ETC_product.bin` |
| File-backed runtime end | `0x008D6200` | `0x006E4E00` |
| Effective end after BSS | `0x008DD080` | `0x006E4E00` |

The segment arithmetic is exact:

```text
BTL: 0x40 + 0x1DB6C0 + 0x46C00 = 0x222300
     0x006B3F00 + 0x222300 + 0x6E80 = 0x008DD080

ETC: 0x40 + 0x24E40 + 0xC080 = 0x30F00
     0x006B3F00 + 0x30F00 = 0x006E4E00
```

Their raw and runtime spans are:

| Image | Span | Raw half-open range | Runtime half-open range |
| --- | --- | --- | --- |
| BTL | Header | `0x000000-0x000040` | `0x006B3F00-0x006B3F40` |
| BTL | Text | `0x000040-0x1DB700` | `0x006B3F40-0x0088F600` |
| BTL | Data | `0x1DB700-0x222300` | `0x0088F600-0x008D6200` |
| BTL | BSS | not file-backed | `0x008D6200-0x008DD080` |
| ETC | Header | `0x000000-0x000040` | `0x006B3F00-0x006B3F40` |
| ETC | Text | `0x000040-0x024E80` | `0x006B3F40-0x006D8D80` |
| ETC | Data | `0x024E80-0x030F00` | `0x006D8D80-0x006E4E00` |

Both scoped files have an additional zero-filled `0x40` bytes at raw
`0x40-0x7F`; their first instructions are at raw `0x80`, live
`0x006B3F80`. That position is a build/link convention, not a field encoded in
the header.

## Resident loader and exact call graph

Resident addresses use the conversion linked above.

| Runtime | ELF file offset | Preserved label / recovered role | Direct callers | Principal callees |
| ---: | ---: | --- | --- | --- |
| `0x00100230` | `0x000330` | `FUN_00100230`, resident constructor bootstrap | Startup | `FUN_00119A90(0x005D9CF0, 0x005D9D40, ...)` |
| `0x00100270` | `0x000370` | `FUN_00100270`, post-read MWo3 initialization | `FUN_001BE7F0` | `FlushCache`, `FUN_0017A5D8`, `FUN_00119A90` |
| `0x00119A90` | `0x019B90` | Constructor-pointer walker | `FUN_00100230`, `FUN_00100270` | Every pointer in `[begin,end)`, then no-op `FUN_0011B0B0` |
| `0x001BE110` | `0x0BE210` | CD path canonicalizer | `FUN_001BE7F0` | none |
| `0x001BE7F0` | `0x0BE8F0` | Synchronous retrying PRG file loader | `FUN_001F3D10`, `FUN_001F45B0` | path helpers, stdio wrappers, `FUN_00100270` |
| `0x001F3D10` | `0x0F3E10` | Overlay selector/cache front end | mode state machines | `FUN_001BE7F0(1, filename)` |
| `0x001F45B0` | `0x0F46B0` | Restore-BTL helper | `FUN_001E9980` | `FUN_001BE7F0(1, "BTL.bin")` |

There are exactly three direct resident calls to `FUN_001BE7F0`: callsites
`0x001F3D60` (ELF file `0x0F3E60`) and `0x001F3D94` (`0x0F3E94`) inside
`FUN_001F3D10`, plus `0x001F45D8` (`0x0F46D8`) inside `FUN_001F45B0`.
All three set `a0=1`, selecting overlay destination slot 1. The only direct
call to post-read `FUN_00100270` is loader callsite `0x001BE970` (ELF file
`0x0BEA70`).

The important helper addresses are:

| Runtime | ELF file offset | Recovered operation |
| ---: | ---: | --- |
| `0x00117000` | `0x017100` | heap/object release used by mode-specific teardown and deleting callbacks |
| `0x00117150` | `0x017250` | heap/object allocation |
| `0x00119220` | `0x019320` | compiler array-destruction helper |
| `0x00119290` | `0x019390` | compiler array-construction helper |
| `0x00119A60` | `0x019B60` | prepend compiler cleanup node to resident list at `0x00609A00` |
| `0x0011B0B0` | `0x01B1B0` | return-zero no-op called after constructor walking |
| `0x0015DF60` | `0x05E060` | recognized SDK `FlushCache`; issues syscall `100` with operation in `a0` |
| `0x0015ED58` | `0x05EE58` | delay current thread; loader passes `200000` while the resident CD/DVD-readiness state is nonzero |
| `0x00163068` | `0x063168` | threaded stdio open wrapper |
| `0x001632F8` | `0x0633F8` | threaded stdio close wrapper |
| `0x00163470` | `0x063570` | threaded stdio lseek wrapper |
| `0x001636B0` | `0x0637B0` | threaded stdio read wrapper |
| `0x0017A5D8` | `0x07A6D8` | optimized `memset` used for BSS |
| `0x0017BF78` | `0x07C078` | append string (`strcat` behavior; decompiler prototype is incomplete) |
| `0x0017C380` | `0x07C480` | copy string (`strcpy` behavior) |

### Destination and filename tables

`FUN_001BE7F0(slot, filename)` reads its destination from runtime
`0x006029C0` (ELF file `0x00502AC0`). The clean table begins:

```text
slot 0 -> 0x00100000
slot 1 -> 0x006B3F00
slots 2..15 -> 0
slot 16 and beyond -> adjacent, unrelated resident data
```

The 16-word region is exactly runtime `0x006029C0-0x00602A00` (ELF file
`0x502AC0-0x502B00`); the next word at `0x00602A00` is unrelated value `1`.
All three direct callers use slot `1`. Slot `0` is dormant in the recovered
path: calling the loader with it would read a PRG file over resident base
`0x00100000`. There is no bounds check on `slot`; slots 2 through 15 select
null, slot 16 selects address `0x00000001`, and later values index still more
unrelated resident data. The table is an internal address array, not a safe
public slot namespace.

`FUN_001F3D10(selector)` indexes the pointer table at runtime `0x004049E0`
(ELF file `0x00304AE0`). The scoped entries are:

| Selector | Filename pointer | String | Result after path normalization |
| ---: | ---: | --- | --- |
| `0` | `0x00603048` | `BTL.bin` | `cdrom0:\PRG\BTL.BIN;1` |
| `2` | `0x00603058` | `ETC.bin` | `cdrom0:\PRG\ETC.BIN;1` |

The intervening selector is outside this document's scope.

For the two scoped images, the selector and header identity are numerically
related but are not the same field: selector `0` loads BTL header kind `1`, and
selector `2` loads ETC header kind `3`. Thus `kind == selector + 1` describes
these two files, but the loader neither computes nor checks that relation; it
must not be treated as a proven generic MWo3 rule.

The selector is not bounds-checked either: `FUN_001F3D10` shifts it left by
two and directly indexes the filename-pointer table. Its scoped callers pass
only `0` or `2`. The table is exactly three pointers at runtime
`0x004049E0-0x004049EC` (ELF file `0x304AE0-0x304AEC`). Selector `3` reads the
following zero word and passes a null filename to the path append; selector
`4` interprets adjacent inline data bytes as a pointer. Negative indices read
before the table. None is a recoverable “unknown selector” result.

`FUN_001F3D10` reloads when the resident manager is absent or when its cached
selector at `manager + 0x10` differs. After a changed-selector load it writes
the new selector back. If the manager pointer is null, the image is loaded but
there is nowhere to record the selector, so another call while it remains null
loads again. The function returns `1` unconditionally after it either observes
a cache hit or the retrying loader eventually returns; it cannot report a
failure. The manager pointer itself is the resident BSS global at `0x00607600`
(`$gp - 0x33F0`).

The cached selector is only the last value requested through this interface;
it is not an observed image identity. A cache hit compares the integer and
returns without reading `MWo3`, kind, base, or any code byte. Replacing or
corrupting the slot through another mechanism while leaving `manager + 0x10`
unchanged can therefore suppress the reload that would otherwise repair it.

Cache publication occurs strictly after the complete load and post-read
initialization: the call at `0x001F3D60` returns before the store to
`manager + 0x10` at `0x001F3D68`. Restore helper `FUN_001F45B0` has the same
order at `0x001F45D8/0x001F45E0`. There is no in-progress selector value or
lock operation in either helper. Consequently, if higher-level mode logic did
allow concurrent selector calls, the cache would continue naming the outgoing
image while its bytes were partly overwritten and its incoming constructors
were running. A concurrent request for that old selector could take the cache
hit and return immediately; another request for the incoming selector could
start a second load. This race is a static possibility, not an observed game
failure, and is another reason the missing higher-level lifetime invariant
matters. The disc-readiness polling inside `FUN_001BE7F0` does not close this
window because cache hits never enter that loader and the selector does not
set the polled state.

An exhaustive direct-`jal` scan of the resident found these five scoped selector
calls:

| Caller | Selector callsite | ELF file offset | Image | Nearby identity-sensitive overlay calls |
| --- | ---: | ---: | --- | --- |
| `FUN_001EA240` | `0x001EA368` | `0x0EA468` | BTL | none in the selecting state; it sets `manager + 0x0C = 1` and continues resident setup |
| `FUN_001EB120` | `0x001EB1F0` | `0x0EB2F0` | ETC | `0x006C65C0` at `0x001EB22C`, `0x006C68F0` at `0x001EB238`, `0x006C8940` at `0x001EB258` |
| `FUN_001EC7A0` | `0x001EC7BC` | `0x0EC8BC` | BTL | `0x007190D0` at `0x001EC824`, `0x00719500` at `0x001EC83C`, `0x00885210` at `0x001EC844` |
| `FUN_0038E140` | `0x0038E17C` | `0x28E27C` | BTL | unresolved pre-switch target `0x007D7580` at `0x0038E16C`; BTL `0x006EE810` at `0x0038E200` after selection |
| `FUN_003916D0` | `0x003919E4` | `0x291AE4` | BTL | no immediate direct overlay call; it constructs a resident wrapper around already prepared state |

Resolving the post-selection calls and their paired cleanup calls against the
clean files gives this exact cross-coordinate map:

| Image | Runtime target | Raw-file offset | Preserved Ghidra target | First instruction word |
| --- | ---: | ---: | ---: | ---: |
| BTL | `0x007190D0` | `0x0651D0` | `0x00719090` | `0x27BDFFF0` |
| BTL | `0x00719500` | `0x065600` | `0x007194C0` | `0x27BDFFE0` |
| BTL | `0x00885210` | `0x1D1310` | `0x008851D0` | `0x27BDFFF0` |
| BTL | `0x006EE810` | `0x03A910` | `0x006EE7D0` | `0xAC800000` |
| ETC | `0x006C65C0` | `0x0126C0` | `0x006C6580` | `0xAC800000` |
| ETC | `0x006C6630` | `0x012730` | `0x006C65F0` | `0x27BDFFC0` |
| ETC | `0x006C68F0` | `0x0129F0` | `0x006C68B0` | `0x27BDFFC0` |
| ETC | `0x006C8940` | `0x014A40` | `0x006C8900` | `0x27BDFFE0` |

The raw offsets use `target - 0x006B3F00`; the preserved Ghidra addresses use
`target - 0x40`. The instruction words were read directly from the named clean
image, which independently confirms each listed state-machine call resolves to
code in its selected overlay.

The pre-selector `0x007D7580` call in `FUN_0038E140` must **not** be attributed
to BTL. At the corresponding clean-BTL raw offset `0x123680`, the first word is
`0x04800002` (`bltz $a0,...`), forty bytes into the function whose prologue is
at runtime `0x007D7540`; that path eventually restores a 64-byte frame it did
not allocate when entered at `0x007D7580`. It is therefore not a callable BTL
entry. The resident invokes this address while the prior image is still live,
records its return value, then selects BTL. The prior image's identity and
entrypoint are outside this document's scope. This is direct evidence that a
transition may deliberately call the outgoing overlay before replacement, not
evidence that selection may safely be delayed before a call into the incoming
one.

The separate path `FUN_001E9980` calls `FUN_001F45B0` at `0x001E99C4` (ELF
file `0x0E9AC4`). The helper restores BTL and changes the cached selector to `0`
only when it had been nonzero.

This is also the normal manager bootstrap. When resident global `0x00607600`
is null, `FUN_001E9980` allocates `0xDF8` bytes at `0x001E999C`, calls manager
constructor `FUN_001F4200`, publishes the pointer at `0x001E99BC`, and then
calls `FUN_001F45B0`. Constructor subroutine `FUN_001F4360` stores `-1` at
manager `+0x10` at `0x001F43CC`, so the restore helper necessarily loads BTL
and changes the selector to `0`. The initial BTL state is therefore explicit;
it is not an accidental cache hit on a zero-initialized selector. Allocation
failure is not handled on this path: a null result is still passed to
`FUN_001F45B0`, whose first operation reads `manager + 0x10`.

Clean return routing also separates object lifetime from byte residency.
Collection releases its ETC-owned object and switches the manager back to its
resident Mode Select callback, but it does not immediately replace ETC.
Resident-only phases run first; Mode Select phase 3 calls selector `0` to
restore BTL, and only phase 4 constructs the selection controller. Returning
to title destroys the manager and its cache but likewise does not clear the
overlay bytes. A later manager starts at selector `-1` and reloads BTL even if
BTL happens still to occupy the slot. The broader state sequencing is recorded
in [`../game/mode_flow.md`](../game/mode_flow.md); the ABI point is that
“object cleanup,” “image replacement,” and “cache destruction” are three
distinct events.

The Collection ETC state machine also shows the mode-owned teardown boundary:
`FUN_001EB120` calls ETC cleanup `0x006C6630` at `0x001EB2FC`, then frees its
owner object at `0x001EB308`.

Those calls execute while ETC is still the selected image. They are explicit
knowledge in the owning resident state machines, not callbacks discovered
through the MWo3 header.

### Recovered mode-owned entry and cleanup contracts

These are ordinary fixed-address application interfaces, not MWo3-header
exports. Their ownership makes the required image lifetime especially clear.

The Collection ETC state path in `FUN_001EB120` owns a resident-allocated
`0x80` byte object:

| Runtime target | Contract proven by caller and clean code |
| ---: | --- |
| `0x006C65C0` | `init_fields(object)`: clears dwords `+0x00..+0x2C` and ten pointers at `+0x50..+0x74`; returns no status |
| `0x006C68F0` | `init_resources(object)`: populates the object with resident handles and allocations after the field initializer; returns no status used by the caller |
| `0x006C8940` | `poll(object) -> bool`: returns `1` when internal `0x006C7DA0` reports completion; otherwise calls internal updater `0x006C8290(object)` and returns `0` |
| `0x006C6630` | `release_resources(object)`: releases and zeroes owned pointers at `+0x04..+0x2C`, the nested owner at `+0x78`, and ten polymorphic objects at `+0x50..+0x74` |

The resident calls the two initializers consecutively, polls until it sees
exactly `1`, calls the release routine, and only then frees the `0x80` byte
allocation. The field initializer intentionally does not clear every byte of
the allocation; safety relies on the paired resource initializer and the
fresh-allocation contract, not on treating `0x006C65C0` as a general `memset`.

The BTL path in `FUN_001EC7A0` similarly owns a `0x188` byte allocation:

| Runtime target | Contract proven by caller and clean code |
| ---: | --- |
| `0x007190D0` | `init(object)`: initializes header/owned-pointer fields and 28 records at `+0x14`, stride `0x0C`; each record receives a pointer into the BTL table at `0x008C3DE0` and two zero fields |
| `0x00719500` | `reset_for_context(object)`: clears the two mutable fields in all 28 records, resets object fields `+0x00/+0x04/+0x08`, and, when the resident manager exists, stores the result of resident `0x001F6F60` at `+0x08` |
| `0x00719140` | `release(object)`: releases and zeroes owned pointers at `+0x17C/+0x180/+0x184` and two polymorphic pointers at `+0x164/+0x168` |

The same resident setup then calls no-argument BTL `0x00885210`. It performs an
internal reset, destroys any prior object held in resident global `0x00607888`
(`$gp - 0x3168`), allocates `0x24` bytes through resident `0x00117150`, calls
BTL constructor `0x00886CB0` when allocation succeeds, and stores the new
pointer back in that resident global. Paired resident teardown
`FUN_001EC890` calls `0x00719140`, frees the `0x188` object, and calls BTL
`0x00885290` to destroy and clear the singleton.

A second BTL setup path allocates `0x28` bytes and calls leaf initializer
`0x006EE810`, which clears its defined dword fields plus byte `+0x14`. This
entry executes only after selector `0` has loaded BTL.

### `FUN_001BE7F0`: complete-file read

The loader builds a path in a 128-byte stack buffer by copying the literal at
runtime `0x003FB998` (`cdrom0:\PRG\`), appending the selected filename, then
calling `FUN_001BE110`. That final helper converts `/` to `\`, uppercases ASCII
after the device colon, and adds `;1` when absent.

The pre-operation wait reads resident pointer `0x006073FC` (`$gp - 0x35F4`)
and, when non-null, polls byte `object + 0x504` until it becomes zero. Resident
startup `FUN_00105FC0` allocates this `0x530`-byte core object, and
`FUN_00107F80` initializes `+0x504` to zero. The recovered writer is the
resident pump `FUN_001086C0`, whose states are:

```text
0 -> 1 when the lower-level status reports 1 or 0x20 and byte +0x506 is zero
1 -> 2 unconditionally on the next pump
2 -> 3 when FUN_00173328(1) returns 2
3 -> 4 for FUN_00173890 results 0x12..0x14, otherwise -> 2
4 -> 0 when optional task +0x508 is absent or complete, otherwise -> 2
```

`FUN_00173328` contains the literal `NEW DiskReady Call`, tying this byte to
the CD/DVD readiness/recovery path rather than an inferred generic mutex. The
loader performs the wait before `open` and again before `read`, sleeping for
`200000` each time the state is nonzero. It neither sets nor clears the state
and has no corresponding check that code in the current overlay has stopped
executing. This gate protects disc operations from that resident recovery
state; it is not an overlay-lifetime lock.

The effective control flow is:

```text
destination = destination_table[slot]
cdrom_prefix = literal_at_runtime_0x003FB998
path = canonicalize(cdrom_prefix + filename)

repeat forever:
    wait while resident CD/DVD-readiness state is nonzero
    retry open(path, 1, 0x1FF) until result >= 0
    retry lseek(fd, 0, SEEK_END) until result >= 0  -> expected_size
    retry lseek(fd, 0, SEEK_SET) until result >= 0
    wait while resident CD/DVD-readiness state is nonzero
    retry read(fd, destination, expected_size) until result >= 0 -> bytes_read
    retry close(fd) until result >= 0
    if bytes_read == expected_size:
        FUN_00100270(destination, expected_size)
        return
```

The error retries do not all reopen. A negative `open` result retries `open`;
negative end-seek, rewind-seek, `read`, or `close` results retry that same
operation on the same descriptor. A nonnegative short read is different: the
loader successfully closes the descriptor and restarts at the outer readiness
wait and `open`. None of the negative-result loops calls the delay helper, so a
persistent filesystem error can spin tightly. The `200000` delay occurs only
while the separate resident CD/DVD-readiness state is nonzero.

There is no maximum-size check against the overlay reservation, no MWo3 magic
check, no kind check, no base check, and no text/data consistency check. A
missing, unreadable, repeatedly short, or otherwise failing file can leave this
routine retrying indefinitely; an oversized successful file can overwrite past
the intended slot. The prefix and filename are also copied/appended into a
fixed 128-byte stack buffer without a length argument. The prefix occupies 12
bytes. When the canonicalizer must append `;1`, the longest filename that fits
with the final NUL is therefore 113 bytes; one already ending in `;1` may be
115 bytes. Both scoped built-in filenames are seven bytes, but the loader
interface itself does not enforce either bound.

Direct negative evidence corroborates the complete loader trace. The clean
resident file contains zero occurrences of the little-endian magic bytes
`4D 57 6F 33` and zero decoded `lui 0x336F` / matching `ori 0x574D`
constructions. In the preserved resident export, references to `0x006B3F00`
occur only in ELF program/section metadata, not as code XREFs. This does not
exclude an arbitrary consumer computing a header pointer indirectly, but no
such identity check appears in the recovered selector/loader path.

The retry is not transactional. A nonnegative short read has already replaced
the beginning of the live slot; the loader closes the file and starts another
open/seek/read cycle without restoring the previous image or clearing the
partial one. A zero-length file likewise satisfies `bytes_read ==
expected_size` and reaches `FUN_00100270`, which reads BSS and constructor
metadata from the old slot. The two clean cross-image cases are deterministic:

- a zero-byte BTL request while ETC is resident sees stale BSS size zero and
  equal constructor bounds, leaves ETC bytes untouched, returns success, and
  lets the selector publish BTL index `0`;
- a zero-byte ETC request while BTL is resident sees stale BSS size `0x6E80`,
  clears `0x006B3F00-0x006BAD80`, then reads the now-zeroed constructor bounds
  and lets the selector publish ETC index `2`.

There is no minimum file-size check. Safe operation therefore also depends on
the resident state machine preventing other threads from entering the slot
throughout the entire retry and initialization interval.

### `FUN_00100270`: cache, BSS, constructors

The post-read routine is exactly:

```text
bss_size = *(u32 *)(image + 0x14)
FlushCache(0)
FlushCache(2)
if bss_size != 0:
    memset(image + physical_file_size, 0, bss_size)
run_constructor_range(
    *(u32 *)(image + 0x18),
    *(u32 *)(image + 0x1C)
)
```

`FUN_00119A90(begin, end, 0, 0)` advances by four bytes while `begin < end` and
indirect-calls the address stored in every entry. It does not validate the
range, entry alignment, target address, or nullness. Its final call to
`FUN_0011B0B0(0,0)` is a return-zero no-op in this executable.

The constructor walker does not establish argument registers before `jalr`.
For an overlay load, the first constructor happens to enter with `a0=begin`,
`a1=end`, `a2=0`, and `a3=0`; later constructors inherit caller-saved argument
registers left by the preceding constructor. Those values are not a supported
constructor interface. Constructors must be treated as no-argument routines.

## Relocation, imports, exports, and call convention

### No runtime relocation or symbol records

No relocation/import/export mechanism is present in the scoped runtime path:

- `0x40 + text_size + data_size` consumes each file exactly; there is no
  appended relocation or symbol stream.
- The bytes at the text/data boundary are ordinary initialized payload data
  (`battlegauge` in BTL and `home.ccs` in ETC), not relocation records.
- The loader performs one raw read and the post-read cache/BSS/constructor
  operations above. No code walks fixups or names.
- Header base `+0x08` is informational to this loader. The destination table,
  not the header, chooses where bytes go.
- Constructor bounds and entries are absolute addresses. Internal data
  pointers and `j`/`jal` targets are also already linked absolute addresses.

Changing only the destination table or header base cannot relocate one of
these clean images. A moved image would still call and dereference the original
linked addresses.

### Direct resident-import surface

A census of actual decoded `jal` instructions in the preserved listings gives
the scale of the fixed import ABI:

| Image | Direct `jal` sites targeting resident `0x00100000-0x006B3EFF` | Distinct resident targets | Decoded `jalr` sites |
| --- | ---: | ---: | ---: |
| BTL | `14,591` | `884` | `1,790` |
| ETC | `1,498` | `194` | `20` |

Exactly 149 direct resident targets occur in both decoded images. Thus the
decoded sets contain 735 BTL-only and 45 ETC-only resident targets, with 929
targets in their union. Every direct resident transfer counted here is `jal`;
neither listing contains a decoded direct `j` tail transfer into the resident
range.

These are static instruction sites, each counted once, not dynamic execution
frequencies. `jalr` is listed separately because its runtime target cannot be
classified as resident or overlay from the instruction alone. The census uses
Ghidra-decoded instructions rather than treating arbitrary aligned data words
as code. Consequently, the BTL row excludes executable routines late in the
nominal data span. The header-referenced constructors independently add three
confirmed resident calls there: `0x008D5E44 -> 0x00119290`, `0x008D5EDC ->
0x00119A60`, and `0x008D60F8 -> 0x00119290`.

The highest-density shared targets are:

| Resident target | BTL sites | ETC sites | Recovered role when established |
| ---: | ---: | ---: | --- |
| `0x00117000` | `599` | `95` | heap/object release |
| `0x00117150` | `410` | `61` | heap/object allocation |
| `0x001A8F00` | `333` | `66` | CCS object lookup by `(container, name, miss_policy)` |
| `0x001D7E20` | `222` | `72` | unresolved |
| `0x001BB6F0` | `192` | `61` | unresolved |
| `0x001BB210` | `187` | `60` | unresolved |
| `0x001B99B0` | `230` | `8` | unresolved |
| `0x00180210` | `225` | `7` | MT-backed inclusive bounded-integer reduction |
| `0x00152270` | `212` | `14` | unresolved |
| `0x001B7570` | `121` | `54` | unresolved |

High-density image-specific targets further show that the two images are not
interchangeable clients of a tiny common service table:

| BTL-only target | Sites | ETC-only target | Sites |
| ---: | ---: | ---: | ---: |
| `0x003083A0` | `1,506` | `0x001F70C0` | `52` |
| `0x001DDA50` | `332` | `0x001F54C0` | `21` |
| `0x00171348` | `232` | `0x001F7090` | `13` |
| `0x0016E6F0` | `198` | `0x003808B0` | `11` |
| `0x001DD9D0` | `158` | `0x0037BBD0` | `11` |

These addresses are stripped targets, not recovered original symbols. The
counts are useful when prioritizing resident-service stubs or compatibility
checks, but they do not supply prototypes.

### Indirect dispatch is application ABI, not loader binding

The decoded listings contain `1,790` BTL, `20` ETC, and `1,072` resident
`jalr` sites. Their dynamic destinations cannot be assigned to resident or a
particular overlay statically, so the direct-target tables in this document
are lower bounds on the callable boundary. Nothing in the loader resolves or
patches these sites.

The overlay compiler overwhelmingly funnels indirect calls through `t9`:
`1,788/1,790` BTL sites and all 20 ETC sites use it. The remaining two BTL
sites call through `v0` after indexed function-pointer-table loads. Raw code
shows ordinary object dispatch, for example:

```text
BTL raw 0x0DA2C / live 0x006C192C: lw t9,0(a0)
BTL raw 0x0DA30 / live 0x006C1930: lw t9,0x24(t9)
BTL raw 0x0DA34 / live 0x006C1934: jalr t9

ETC raw 0x1293C / live 0x006C683C: lw t9,8(a0)
ETC raw 0x12940 / live 0x006C6840: lw t9,8(t9)
ETC raw 0x12944 / live 0x006C6844: jalr t9
```

Both examples set `a1=1` immediately before the sequence, matching deleting
or release-style virtual calls seen in teardown. Other slots and object-table
offsets vary. This is not a single import-table layout, and `t9` itself does
not identify ownership; the loaded pointer may name resident code, current
overlay code, or another callback.

It also creates a second lifetime obligation beyond guarding direct calls.
An object or callback table that survives image replacement can retain a
perfectly aligned absolute method pointer into the outgoing image. Mode-owned
objects must therefore be quiesced and released while their defining overlay
is still resident, exactly as the ETC teardown paths above do.

### Overlay to resident

Overlay code imports resident services by their final addresses. Examples from
the clean files are:

| Image | Raw callsite | Live callsite | Encoded operation | Preserved-Ghidra callsite |
| --- | ---: | ---: | --- | ---: |
| BTL | `0x0002AC` | `0x006B41AC` | `jal 0x00119290` | `0x006B416C` |
| ETC | `0x00017C` | `0x006B407C` | `jal 0x001CC350` | `0x006B403C` |

There is no import trampoline or global offset table lookup at those calls.

The resident ELF `.reginfo` supplies `$gp = 0x0060A9F0`, and overlay code uses
that inherited value to access resident globals. Resident startup constructs
the same address with `lui a0,0x61` / `addiu a0,a0,-0x5610` at
`0x00100198/0x001001AC` and executes `move gp,a0` at `0x001001C0`, before any
overlay load. Two direct overlay examples are:

- BTL raw `0x80` / live `0x006B3F80`: `lw v0,-0x33EC(gp)`, resolving to
  resident global `0x00607604`;
- ETC raw `0x220` / live `0x006B4120`: `lw a0,-0x33F0(gp)`, resolving to
  resident global `0x00607600`.

A decoded-instruction census makes this a substantial data ABI:

| Image | `$gp`-based memory references | `$gp`-based address formation | Distinct effective resident addresses | Effective-address span |
| --- | ---: | ---: | ---: | --- |
| BTL | `3,711` | `261` | `733` | `0x00602A60-0x00607888` |
| ETC | `486` | `37` | `88` | `0x00602A60-0x006079C8` |

Only 12 effective addresses occur in both decoded sets; the union contains 809
resident addresses. The busiest shared addresses are:

| Resident address | BTL sites | ETC sites | Recovered role when established |
| ---: | ---: | ---: | --- |
| `0x00607600` | `716` | `100` | overlay-manager pointer used by the selector cache |
| `0x006073F4` | `380` | `57` | unresolved |
| `0x006073FC` | `333` | `14` | resident core-object pointer; its CD/DVD-readiness byte `+0x504` is polled by the loader |
| `0x00607470` | `92` | `19` | unresolved |
| `0x006073D4` | `75` | `14` | unresolved |
| `0x00607464` | `27` | `32` | unresolved |

The decoded text of neither image writes `$gp`; it only consumes the inherited
resident value. BTL's header-referenced constructor code, which is outside the
decoded text span, adds reads of resident `0x00604E8C` and `0x00604E9C` plus
address formation for resident `0x00607870`, and likewise does not replace
`$gp`. There is no overlay-local fallback initializer. Any injected call that
enters an overlay with a different `$gp` can therefore break even when the
target function's explicit arguments are correct. Conversely, an overlay
routine must preserve the resident `$gp` invariant expected by code on both
sides of the call.

### Resident to overlay

The resident likewise issues direct calls to linked overlay addresses. For
example, resident `FUN_001FD850` at callsite `0x001FD954` executes
`jal 0x006B3F80`. That address is valid only under the expected overlay
identity.

The same live address can have unrelated semantics after replacement:

- under BTL, raw `0x80` / live `0x006B3F80` returns zero or a pointer obtained
  from the resident global at `0x00607604`;
- under ETC, raw `0x80` / live `0x006B3F80` begins a multi-argument structure
  setup routine and eventually calls resident `0x001CC350`.

This is stronger than a simple lifetime warning: the address is callable in
both images but with incompatible behavior and signature.

The decoded resident listing contains 1,476 direct `jal` instructions to 424
distinct targets in the overlay reservation. A separate decompiler-expression
census produces 1,474 call expressions to the same 424 targets; the decoded
instruction count is the more direct measure. No decoded resident direct `j`
tail transfer targets the overlay reservation.

The direct calls split sharply at ETC's effective end:

| Target address class | Direct resident sites | Distinct targets |
| --- | ---: | ---: |
| Address exists within both physical image extents, `0x006B3F00-0x006E4DFF` | `101` | `49` |
| BTL-only high reservation, `0x006E4E00-0x008DD07F` | `1,375` | `375` |

The first class is only a shared **address range**; it is not a shared symbol
set. BTL and ETC can implement unrelated functions at the same number, as the
`0x006B3F80` example demonstrates. The busiest fixed targets are:

| Shared-address target | Sites | BTL-only high target | Sites |
| ---: | ---: | ---: | ---: |
| `0x006DBDD0` | `11` | `0x00704D40` | `74` |
| `0x006B5CD0` | `6` | `0x0071EF70` | `63` |
| `0x006B5CE0` | `6` | `0x007664A0` | `52` |
| `0x006C14E0` | `6` | `0x007237F0` | `49` |
| `0x006B4000` | `5` | `0x00765D70` | `31` |

“BTL-only high” is a geometric label within the two scoped clean files: ETC
does not extend that far, while BTL does. It does not prove every resident call
to such a number is intended for BTL. The pre-switch `0x007D7580` call above is
the concrete counterexample: its target belongs to the outgoing image even
though the number lies inside BTL's reservation.

Comparing the clean raw bytes at all 49 resident-called targets in the shared
address range found **zero** with the same first 32-bit word in BTL and ETC;
zero match over the first 16 or 64 bytes. Representative entry words are:

| Live target | BTL first word | ETC first word |
| ---: | ---: | ---: |
| `0x006B3F80` | `0x8F82CC14` | `0x27BDFFF0` |
| `0x006C65C0` | `0x00000000` | `0xAC800000` |

This does not rule out coincidentally similar higher-level behavior elsewhere;
it does prove that none of the resident's 49 direct targets below ETC's end is
a byte-compatible entrypoint common to these clean images. Numeric range
membership is never an adequate identity test.

These are static instruction sites, not original symbols or dynamically
exercised exports. They show that the practical ABI is a broad linked address
surface rather than one dispatcher. They also amplify the stale-tail hazard:
under ETC, an erroneous call to one of the 375 BTL-high targets may reach old
BTL bytes that the smaller load left intact instead of failing immediately.
Apparent success therefore does not prove correct overlay identity.

### Recovered register calling convention

The scoped code uses the Metrowerks EE convention with independent argument
register banks:

- integer, pointer, and other general-register arguments use `a0-a3`, then
  `t0-t3` for arguments five through eight;
- floating-point arguments independently use `f12-f19`;
- additional general-register arguments use eight-byte caller-stack slots:
  the ninth is at incoming `sp + 0`, the tenth at `sp + 8`;
- integer/pointer results use `v0`, while scalar floating results use `f0`;
- stack frames are 16-byte aligned in the inspected code, with R5900
  `sq`/`lq` commonly used for callee-saved registers and `sd`/`ld` for `ra`.

Exact resident evidence includes `FUN_001020E0`, which spills `a0-a3,t0-t3`
at entry `0x001020E8-0x00102104`; `FUN_00127E48`, which reads its ninth and
tenth general arguments from incoming `sp + 0` and `sp + 8`; and
`FUN_0010E460`, which spills `f12-f19` at
`0x0010E47C-0x0010E498` while separately consuming `a0`.

The overlay boundary follows the same rules. BTL constructor callsites set
`t0=2` as the fifth integer argument to resident `FUN_00119290`. ETC raw
`0x80` / live `0x006B3F80` simultaneously consumes `a0-a3` and `f12/f13`:
the general registers carry an output object plus three input pointers, while
the FP registers carry two scalar values. This class-separated allocation is
why preserved decompiler prototypes can appear to reorder mixed integer and FP
parameters; recover prototypes from register use and callsites, not the
decompiler's displayed parameter order alone.

Interposed assembly must preserve the machine width used by the callee-save
sequence, not merely the low 32 bits suggested by a C prototype. For example,
BTL `0x007D72E0` saves `s0-s2` with `sq`, `f20-f23` with `swc1`, and `ra` with
`sd`; its epilogue at `0x007D7514-0x007D7534` restores them with `lq`, `lwc1`,
and `ld`. The full 128-bit contents of a saved EE GPR can therefore be live
across a call. A shim that substitutes `sw/lw` for the observed `sq/lq` can
corrupt upper lanes even if ordinary 32-bit integer tests appear correct.
Neither side reloads `$gp` at the boundary, so preserving its resident value is
part of the same obligation.

A complete typed prototype catalog for the fixed-address surface has not been
recovered.

## Automatic entry and lifetime

### Constructor interval

BTL's constructor interval is a nine-entry array at raw
`0x222280-0x2222A4`, live `0x008D6180-0x008D61A4`. The entries are called in
this exact order after BSS clearing:

| Index | Pointer-entry raw offset | Constructor live target | Target raw offset |
| ---: | ---: | ---: | ---: |
| `0` | `0x222280` | `0x008D3400` | `0x21F500` |
| `1` | `0x222284` | `0x008D5B70` | `0x221C70` |
| `2` | `0x222288` | `0x008D5DF0` | `0x221EF0` |
| `3` | `0x22228C` | `0x008D5E20` | `0x221F20` |
| `4` | `0x222290` | `0x008D5E60` | `0x221F60` |
| `5` | `0x222294` | `0x008D5F00` | `0x222000` |
| `6` | `0x222298` | `0x008D5F40` | `0x222040` |
| `7` | `0x22229C` | `0x008D6000` | `0x222100` |
| `8` | `0x2222A0` | `0x008D6060` | `0x222160` |

These targets are stripped and have no recovered original names. Direct
callee examples include constructor `0x008D5E20 -> 0x00119290` and
`0x008D6000 -> 0x00765C50`. Several entries initialize absolute overlay data;
they are not generic resident callbacks.

Their mechanically verified principal work is:

| Index | Live target | Verified effect |
| ---: | ---: | --- |
| `0` | `0x008D3400` | Large self-contained numeric/static-data initializer; 2,521 instructions through the return delay slot at `0x008D5B60`, with no calls or `$gp` references |
| `1` | `0x008D5B70` | Second self-contained numeric/static-data initializer; 157 instructions through `0x008D5DE0`, with no calls or `$gp` references |
| `2` | `0x008D5DF0` | Calls BTL `0x007064E0` on object `0x008D6A10` |
| `3` | `0x008D5E20` | Calls resident array-construction helper `0x00119290` for two six-byte objects at `0x008D6A60`, using BTL element constructor `0x007139F0` and no element destructor |
| `4` | `0x008D5E60` | Clears `0x70` bytes at `0x008D6A80`, then links a cleanup record at `0x008D6A70` with callback `0x0071A7A0` |
| `5` | `0x008D5F00` | Converts two signed halfwords at `0x008C4324/26` to floats at `0x008C4328/2C` |
| `6` | `0x008D5F40` | Derives additional float constants/state in the `0x008C4340-0x008C43B8` area |
| `7` | `0x008D6000` | Calls BTL float converter `0x00765C50` for `70.0`, `30.0`, and `50.0`, storing results at `0x008C4CA0`, `0x008C4D88`, and `0x008C4D90` |
| `8` | `0x008D6060` | Initializes more BTL globals, constructs two 12-byte objects at `0x008DA9F0` through resident `0x00119290` and BTL `0x007506E0`, and calls BTL `0x00875960` on resident global `0x00607870` |

Resident `FUN_00119290` is a compiler-style array-construction helper: it
calls the supplied element constructor with `(element_address, 1)` for the
requested count and can unwind already-constructed elements through an
optional destructor. The two BTL uses above explicitly pass a null destructor.

The constructor interval ends at raw `0x2222A4`; every remaining byte through
the BTL file end at `0x222300` is zero. There is no adjacent nonzero destructor
array or other tail record for the loader to consume.

ETC stores `begin == end == 0x006E4E00`, so it has no automatic constructor
calls and no pointer entries.

### Raw `0x80` is not an automatic loader hook

The preserved import tooling labels raw `0x80` as `mwo3_entry`, but that label
was supplied by the project target manifest. No header word points to it, and
neither `FUN_001BE7F0` nor `FUN_00100270` calls it. It is simply the first
linked function in both clean images and one of the fixed addresses the
resident may call later.

In BTL its actual application contract is a no-argument root accessor. Live
`0x006B3F80` reads resident session global `0x00607604`, returns zero when that
pointer is null, and otherwise returns the pointer at session `+0x30`.
Resident `FUN_001FD850` calls it at `0x001FD954` and, on a non-null result,
reads returned-root field `+0x1C`. ETC implements a different multi-argument
routine at the same live address: `a0` is an output structure, `a1` points to
four signed halfwords, `a2` and `a3` point to two-float pairs, and `f12/f13`
carry two further scalars. It fills output fields `+0x40..+0x70` and ends by
calling resident `0x001CC350(out, 0, 1)`. Thus even the conventionally named
first function is neither a common signature nor a loader entrypoint.

### Replacement and exit

No generic unload function, destructor interval, or exit pointer is consumed
before `FUN_001BE7F0` overwrites slot 1. Mode-specific resident state machines
destroy their own objects and then select another image, but that cleanup is
not expressed by the MWo3 header.

BTL constructor `0x008D5E60` does call resident `FUN_00119A60`, but this is a
different mechanism. That helper prepends a three-word node to the resident
head at `0x00609A00`:

```text
node + 0x00 = previous_head
node + 0x04 = cleanup_callback
node + 0x08 = object
head        = node
```

For BTL the node is `0x008D6A70`, the callback is BTL `0x0071A7A0`, and the
object is `0x008D6A80`; both node and object lie in BTL BSS. The callback is a
deleting cleanup routine, but neither the overlay loader nor the selector
walks or unlinks this list on replacement. A static instruction-reference scan
of the scoped resident, BTL, and ETC images found only the resident helper's
read/write of `0x00609A00`, not a consumer or reset. This is consistent with
compiler process-lifetime cleanup registration; it is not evidence of an
overlay exit hook.

The distinction matters on reload. Unless some code outside the traced scoped
path resets the head, after the first BTL initialization it points at
`0x008D6A70`. A later BTL load clears that BSS node and registers the same
address again, making `node->previous_head` point to the node itself. Since the
scoped path never consumes the chain, this does not establish an observed
mode-switch failure, but it makes the chain unsafe to reinterpret as an unload
facility.

The loader also does not clear the old image's whole reservation. It overwrites
only the new physical file and clears only the new BSS:

- Loading BTL writes through `0x008D61FF` and clears
  `0x008D6200-0x008DD07F`.
- Loading ETC writes through `0x006E4DFF` and clears no BSS.

After a smaller ETC load, the range `0x006E4E00-0x008DD080` can therefore
retain stale bytes from an earlier BTL lifetime. Those bytes are not ETC slack
that can safely be treated as free persistent memory. See the phase ownership
rules in [`ee_memory_map/runtime_lifetimes.md`](ee_memory_map/runtime_lifetimes.md)
and the reservation map in
[`ee_memory_map/address_space.md`](ee_memory_map/address_space.md).

For a runtime guard, the minimum useful header tuple is:

```text
BTL: *(u32 *)0x006B3F00 == 0x336F574D
     *(u32 *)0x006B3F04 == 1
     *(u32 *)0x006B3F08 == 0x006B3F00

ETC: *(u32 *)0x006B3F00 == 0x336F574D
     *(u32 *)0x006B3F04 == 3
     *(u32 *)0x006B3F08 == 0x006B3F00
```

Code that needs a particular clean build should additionally guard the relevant
instruction/data bytes or external build identity; the header has no hash or
version field. The tuple is only an instantaneous identity check: because the
loader exposes no execution lock, the check and subsequent overlay call must
also occur inside the resident mode's lifetime/synchronization invariant.

## Evidence strength and unknowns

| Finding | Evidence | Confidence |
| --- | --- | --- |
| Full file loads at `0x006B3F00` | Destination table, complete `FUN_001BE7F0` read path, and clean-file absolute references | High |
| Text/data/BSS field meanings | Exact size equations, boundary bytes, ELF reservation sizes, BSS clear routine | High |
| Constructor interval semantics | Direct header reads and indirect-call loop in `FUN_00100270` / `FUN_00119A90` | High |
| No runtime relocation or symbol resolution | Complete loader call path, exact file exhaustion, absolute encoded references | High for this executable and these two images |
| Shared resident `$gp` | ELF `.reginfo` plus GP-relative instructions in both images | High |
| No format-level exit hook | Complete header consumption and loader path | High |
| Broader mode-specific teardown semantics | Only representative state-machine paths traced | Medium |

Still unresolved:

- The vendor's original field/type names and whether other `MWo3` versions add
  fields or relocation conventions.
- The original namespace meaning of kind values beyond the two scoped values.
- The precise linker section composition behind the text/data split; BTL's
  nominal data span demonstrably includes executable initializer code.
- Typed prototypes and semantic names for the complete fixed-address export
  surface.
- The exact synchronization invariant that prevents a mode switch from
  replacing an overlay while another thread is still executing it.
- Any overlay-specific cleanup routines beyond the representative resident
  state machines. None is a generic header-driven exit hook.

Evidence came from raw little-endian header/segment inspection, the resident
ELF program headers and `.reginfo`, direct R5900 disassembly, and the preserved
Ghidra exports under `@disassembly/NA2/exports/`. No source binary or
disassembly artifact was modified.
