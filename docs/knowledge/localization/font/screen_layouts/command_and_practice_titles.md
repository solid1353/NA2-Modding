# Command Chart and Practice title layouts

Shared title-adapter evidence for Command Chart and Practice, including their distinct geometry, common metrics, guarded callers, and validation boundary.

## Command Chart and Practice title boxes

The Command Chart and Practice command-title rows share the same boxed-fit
logic but not the same container geometry. NUN5 wrapper telemetry at caller
`0x003882D0` establishes these separate records:

- Command Chart titles: X `28`, Y `17/117/217`, width `288`, height `20`;
- Practice titles: X `32`, Y `14/114/214`, width `352`, height `20`;
- Practice explanations remain a separate caller family at X `40`, Y
  `42/142/242`, width `364`, height `48`, vertical alignment `1`.

A guarded task-owned NUN5 state probe recorded `FUN_0018ca40`'s live horizontal
denominators before scaling. `Susanoo's Blade` is `142`, `Reverse Halo` is
`115`, and `Fire Style: Phoenix Flower Jutsu @Petal Shower@` is `440`.
Those values exactly equal the sums from the 95-entry packed metric table.
This runtime result rejects both the legacy NA2 results (`135`, `110`, `417`)
and the temporary constant-eight interpretation. The resident helper now
validates plain ASCII once, consumes the shared table, applies the caller's
`box_width / measured_width` factor only on overflow, and restores scale after
the draw.

NA2 reaches the shared UI wrapper at return address `0x00382454`; exact outer
return-address guards distinguish Command Chart `0x0087A930`, Practice title
`0x00878AA0`, and the pre-existing character-body caller. The final current
origins use a common `-0.8` logical-unit visible-ink compensation:
Command Chart X `27.2` with Y offset `-3.8`, and Practice X `31.2` with Y
offset `-6.8`. The width constants remain the exact NUN5 `288` and `352`.

Matched 640x480 captures on worker CRC `D64F4D9F` show:

| Title row | NUN5 ink bounds | Current ink bounds |
| --- | --- | --- |
| Command Chart: `Susanoo's Blade` | `(141,87)-(314,100)` | `(141,87)-(314,99)` |
| Command Chart: `Reverse Halo` | `(141,212)-(279,225)` | `(140,212)-(279,224)` |
| Command Chart: long Petal Shower title | `(141,337)-(488,353)` | `(141,337)-(496,353)` |
| Practice: `Shadowbur Extra Hit` | `(96,83)-(326,96)` | `(96,83)-(325,96)` |
| Practice: `Guard` | `(96,208)-(153,221)` | `(96,208)-(153,221)` |
| Practice: `Linked Attack` | `(96,333)-(245,346)` | `(96,333)-(245,346)` |

The long current title is complete and unclipped. Its eight-pixel right-edge
difference is not a fit error: official NUN5 bytes `0x40` render quote-shaped
glyphs, while the accepted NA2 atlas deliberately preserves literal at-signs.
The occasional one-pixel short-title height or leading-bearing difference is
likewise accepted raster/metric residue, not a container offset. The NUN5
reference screenshot hashes are
`E602195AF1CC4EFD122735DD7F7D08A15ECCC38B88DB1FCF85C5CD966E70E9DE`
and
`983AC7C636C3F5CF47492E87795899592C2B4B50EFA1EE556AC4095052F4CF2E`;
the matched current hashes are
`FE37ABB125396BA6786230A6B580DE4C59EEF20527A4FD5B49B52D98BCC15598`
and
`D10643D42B96D0135C4E25F636EB517042C6ABE28822BEB56DFFD0AE5D084C8F`.
Confidence is **high** for the denominators, caller guards, fit thresholds,
origins, and separation from the unresolved Practice explanation family.

The stage-by-stage v2 reimplementation no longer depends on those retained
outer-return guards. Bounded BTL inspection identifies the actual title-only
draw calls directly. The supplied states independently confirm that the live
MWo3 image begins at `0x006B3F00`, so these file offsets map without the
`-0x40` Ghidra-header adjustment:

- Practice runtime `0x00878A98`, BTL file `0x1C4B98`;
- Command Chart runtime `0x0087A928`, BTL file `0x1C6A28`.

Both sites contain guarded bytes `C4080E0C00000000`, a `jal 0x00382310`
followed by its NOP delay slot. The Practice call occurs before its separate
explanation loop; the Command Chart call precedes two independently guarded
auxiliary-string draws. The v2 implementation therefore redirects only those
two calls to explicit mode entrypoints. Each entrypoint tail-calls one shared
title adapter, which selects the proven geometry above, creates one
single-line shrink-only v2 session, and invokes native `0x00382310` through a
common callback. No Practice explanation or auxiliary Command Chart call is
selected.

The generated v2 resident asset with this adapter is 2,020 bytes and has
SHA-256
`9561B62AAD1E0139B920AED058B2ECB066A9EB7D64092992ECAD60BC1581C8F6`.
Static tests decode both linked BTL hooks, both mode entrypoints, every title
constant, the callback ABI, and the shared-adapter relocations.

The first converted-state capture used the ELF/Ghidra mapping base
`0x006B3EC0` as though it were the live MWo3 base. It therefore wrote each BTL
edit `0x40` bytes too early and produced the hybrid Command word `0x4423D147`
instead of the linked `jal` word `0x0C23D147`. Exact clean context around both
supplied call sites proved that the complete live BTL image begins at
`0x006B3F00`. Corrected guarded states contain `jal 0x008F451C` at
`0x0087A928` and `jal 0x008F48B0` at `0x00878A98`; the failed capture was a
state-conversion error, not a rejected renderer hypothesis.

Hidden task-owned PCSX2 captures on boot CRC `A8A3C4FF` then covered preserved
Command Chart slot 3, all six Practice command slots 2-7, and the accepted
Controls regression. The worker ISO SHA-256 is
`0396D02B559EFC964B05520CC539F074432A57C3796BC1CA3063C3533E32FF1F`;
its 5,488-byte resident payload ends at `0x008F5270` and has SHA-256
`4BD20BE93EA0D0A217A790774C4813863F1F8303FA49117889A6D59D664D097D`.
The corrected Command capture reproduces the prior matched title bounds and
has SHA-256
`FE37ABB125396BA6786230A6B580DE4C59EEF20527A4FD5B49B52D98BCC15598`.
Every Practice page retains the NUN5 title origins while its later explanation
rows remain intentionally unchanged for their separate wrapping family.
Confidence is **high** for the direct hooks, shared adapter, shrink-only
behavior, distinct geometries, state restoration, and separation between
titles and explanations. The user explicitly accepted the Command Chart result
on 2026-07-27. The Practice title result remains agent-validated and awaiting
user acceptance.
