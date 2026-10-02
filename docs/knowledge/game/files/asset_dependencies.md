# Asset dependency graphs

This document records dependency edges in retail NA2 (`SLPS-25837`), separating
authored record references, parser resolution, and files selected by loaders.
None of these static graphs alone establishes simultaneous runtime residency.

## Research coverage

- **Assigned scope:** Retail resource dependency closures: cross-container
  records, shared skeleton/model/effect dependencies, loader-selected
  fighter/jutsu/stage combinations, and missing-reference behavior.
- **Exploration depth:**
  - All directory rows in 1,094 battle-related retail files; the selected
    startup/battle caller chains; 24 stage paths, 184 cinematic rows and
    twelve opponent-override entries; the resident matcher, resolver,
    finalizer and unload invalidation; and the eight typed dependency routes
    through their relevant consumers.
  - All nine per-side resource slots with their request, adoption, cache-reset,
    masked-release and pending-side-release helpers and established resident
    callers.
  - The complete skill-1 selected set: its authored-key closure, main-file
    object section, 48 compositions with 388 children, complete object and
    frame sections, 242 provider model definitions, material leaves, matrix
    indexes and 68 shadow-model links; playback binding, participant
    replacement, duplicate-provider selection and the battle/Collection
    admission callsites.
  - Selected `2TEWCHA1` and `2HKGCHA1` effect leaves through their
    texture/palette definitions, and the subtype-four shadow-model route.
  - Raw bytes corroborate overlay operands, selector arguments, the ten-row
    support gate, three locally filled texture rows, and the release helpers'
    alias checks.
- **Confirmed coverage:** Authored keys, parser links and selected file requests
  are distinct; locally filled sampling/break-texture rows invalidate a
  directory-only missing-resource count; shared skeleton/model/effect paths
  and consumer-specific missing behavior are established; selected load,
  adoption and release states are bounded. Deferred requests do not adopt
  existing containers; the later adoption pass fills missing handles. Full
  release clears matching manager aliases, while pending-side release retains
  resources used by the other side. All default/override cinematic paths were
  checked for physical availability.
  Descriptor collection, composition child construction, and draw-cache use
  have different requirements and missing-resource boundaries.
  Both candidate board chains have equal compared payload content after local
  record-ID normalization; their provider/lifetime identity remains separate.
  The selected skill-1 children, parent links, body geometry, material leaves,
  shadow inputs and streamed target IDs have bounded typed closure. Undefined
  local frame targets are separate from external-file dependencies. Neither
  absent-path skill appears in the battle caller's 223-record input domain.
- **Unresolved or untested:** Complete typed closures for every retail
  combination, all locally filled or renamed directory rows, actual
  simultaneous residency, and retail reachability of skill rows 0x9A/0xA0.
  Actual defender replacement/appearance resources and their name-to-matrix
  binding remain dependent on the selected fighter. Later handling of the
  stream's initially empty local targets and the Collection viewer's permitted
  skill values are not fully established by the inspected caller paths.
- **Deliberate exclusions and overlap:** Lookup and resource lifetime belong to
  [CCS runtime](ccs_runtime.md), payload types to
  [CCS object types](ccs_object_types.md), filename/selector inventories to
  [Character assets](../character_assets.md), the 3EYE presentation family to
  [End-demo presentation](../../gameplay/modes/end_demo_presentation.md), and
  gameplay selection semantics to their linked owners. This document owns relationships between those
  resources, not their full inventories or gameplay behavior.
- **Evidence limitations:** Evidence is static. Published-directory matching
  does not prove that a provider was selected, parsed successfully, materialized,
  or retained for a particular battle. The corpus excludes other disc
  families; its candidate counts are byte-key comparisons before typed parsing,
  not a whole-disc failure census. Incomplete import boundaries and xrefs do
  not support whole-program negative claims.

## Evidence and ownership

The resident evidence is the retail NA2 (`SLPS-25837`) boot ELF
`SLPS_258.37`. Complete-file identities and overlay address conversion belong
to [Retail game file identities](file_identities.md#address-conventions).
Addresses in the resident executable are EE virtual addresses.

[Resident CCS runtime](ccs_runtime.md) owns lookup, parser publication and
resource lifetime; [CCS object types](ccs_object_types.md) owns typed payload
contracts; [Character asset tables](../character_assets.md) owns complete
fighter and jutsu filename inventories. This document joins those contracts
into dependency paths without repeating their inventories.

## Three different edge layers

| Layer | Edge | What it establishes |
| --- | --- | --- |
| Authored directory | Consumer record to an external namespace/name key | A requested provider identity, independent of a disc filename or load request. |
| Parser/runtime descriptor | Object or composition to another directory record, then its resolved object | The typed relationship the parser retains and a consumer may traverse. |
| Loader selection | Match configuration, skill row or stage index to a CCS path | A file request selected by a specific caller and condition. |

**Observation — authored keys.** Resident `FUN_001AC6C0` reads namespace and
object counts, `0x20` bytes per namespace, and `0x1E` object-name bytes plus a
16-bit namespace index per file record. It builds `0x38`-byte runtime records,
stores the namespace pointer at `+0x20`, and initially sets runtime `+0x2C`
to sentinel `4` (record zero is cleared). A namespace beginning with `#` is
therefore an authored external record, not a request to open a similarly
named CCS file.

**Observation — resolution.** `FUN_001AC610` compares both object name and
namespace text after its first byte. `FUN_001ACFC0` searches the new and
already published directories in both directions and copies matched type
`+0x2A` and object `+0x2C`; it contains no file-loader call. A provider's
secondary `+0x30` is not copied. Provider choice and missing/sentinel behavior
are owned by [Cross-container references](ccs_runtime.md#cross-container-references).

**Observation — subordinate resources.** `FUN_00115BA0` follows a resolved
`0x0100` object to its model, each model part's material, that material's
texture, and the texture's palette. For `0x0E00` it follows the effect's
texture and palette. Its `MDL`, `MAT`, `TEX`, and `CLT` selectors restrict
which resolved resources it collects; null or sentinel `4` intermediates are
skipped. This is a selected consumer path, not an exhaustive transitive walk
of every resource type.

**Inference — closure limits (high confidence).** Counting namespace rows,
matching all external names against files on disc, and enumerating selected
loader paths answer different questions. A usable dependency closure requires
the selected files' provider records and the typed consumer path to agree;
disc presence or a directory-name match alone is insufficient.

## Typed dependency routes

The following resident NA2 parsers and consumers were inspected.
Offsets in this table are relative to the parsed descriptor, except where
explicitly identified as model-part offsets. The full type contracts remain
in [CCS object types](ccs_object_types.md).

| Source | Stored dependency | Selected consumer and boundary |
| --- | --- | --- |
| `0x0100`, `FUN_001B2670` | Parent record `+0x04`, ordinary model record `+0x0C`; version-gated secondary model record `+0x10` | `FUN_00115BA0` collects the ordinary model/material/texture/palette dependencies; `FUN_00196B40` separately materializes the secondary model. These links are record pointers, so they can refer to local records or externally resolved records. |
| `0x0200`, `FUN_001B3450` | Texture record `+0x08` | The model's material path reaches this record before texture/palette collection. |
| `0x0800`, `FUN_001B0C40` | Material record at model `+0x64 + part*0x40`, part count at `+0x5E` | `FUN_00115BA0` traverses each part. Model subtype changes parser consumption; a directory-only graph cannot reconstruct every geometry dependency. |
| `0x0900`, `FUN_001B1560` | Child count `+0x08`, child-record array `+0x0C`, transforms `+0x14` | `FUN_001952F0` resolves each child through `FUN_00116210`, then constructs `0x0100`, `0x0D00` or `0x0E00` children. Container publication precedes this materialization. |
| `0x0A00`, `FUN_001B2800` | Parent record `+0x04`, target record `+0x10` | `FUN_00116210` follows target objects back to their provider records. This wrapper is separate from a namespace beginning with `#`; neither implies an additional file request. |
| `0x0D90`, `FUN_001B1B30` | Child-table pointer `+0x28`, count in low nibble of `+0x2E`, `0x0C`-byte entries with record pointer `+0x04` | `FUN_001AACF0` registers children by their resolved tags `0x0900`, `0x0E00`, or `0x0700`. The parser frees the generator descriptor and sets its runtime pointer to zero when this table has no children. |
| `0x0E00`, `FUN_001B2E50` | Texture record `+0x08` | `FUN_00115BA0` follows texture and palette resources independently of model traversal. |
| `0x2300`, `FUN_001AD240` finalization | Composition children selected from attachment records | A child absent from the target composition (`FUN_0019DC90` returns negative) is omitted from the compact attachment arrays. It is not a generic required-object failure. |

**Observation — missing behavior belongs to the consumer.** The instruction
range `0x001A8F34..0x001A8F50` returns a matched record's `+0x2C` directly;
required lookup traps only when the name is absent. A matched unresolved row
can therefore return `4`. `FUN_00115BA0` checks several downstream pointers
against both zero and `4`; `FUN_00116210` checks the target wrapper's next
object but dereferences the current wrapper without that guard. The generator
consumer dispatches on a child record's tag. There is no single universal
missing-reference outcome, and a merely nonzero lookup is not proof of a
usable resource. Detailed resolver and chain limitations belong to
[Object-name lookup](ccs_runtime.md#object-name-lookup) and
[Type-0x0A00 traversal](ccs_runtime.md#type-0x0a00-traversal).

**Observation — dependency edges have a lifetime.** On provider unload,
`FUN_001A9790` checks surviving `#` records' object back-pointers against the
departing record array and resets matching rows to type zero/runtime `4`.
A later publication can resolve those rows again. This applies to objects
with that back-pointer contract; it does not prove that every secondary cache,
materialized child or exceptional resource representation is repaired.
The invalidation contract remains in
[Cross-container references](ccs_runtime.md#cross-container-references).

### Collection and materialization are separate consumers

**Observation — collection is pattern-selected and deduplicated.** The
resident xref query for `FUN_00115BA0` returns one direct call, at
`0x0019D35C` in `FUN_0019D300`. That caller walks the input's eight-byte
record entries (`+0x18`, count `+0x1C`), builds the supplied name pattern,
and passes its three-character selector to the collector. Instructions and
bytes at `0x0019D320..0x0019D360` confirm the pattern argument retained in
`a1` and selector passed in `a3`, despite the omitted second argument in the
decompiler's `FUN_001163A0` call. Its one resident direct caller,
`FUN_001C67E0`, supplies `MDL_point*` at `0x003FBF78`; the adjacent patterns
are `EXT_point*` and `OBJ_root`. This is a concrete selected path, not evidence
that every loader invokes a universal dependency closure.

`FUN_00115990` appends unique pointer values to an eight-byte-entry vector;
it does not reject zero or sentinel `4`. The collector's initial pattern
match can append the matched record's `+0x2C` before the guarded subordinate
walk. Consequently even this collected vector is not a validation that every
entry is a materialized resource. The resident xref result bounds the direct
caller observation; indirect or unanalyzed callers are not excluded.

**Observation — absent model and absent child take different paths.**
`FUN_001952F0` resolves each composition child through `FUN_00116210` and
constructs only resolved tags `0x0100`, `0x0D00`, and `0x0E00`. An unresolved
record with type zero, or an unsupported resolved tag, takes no constructor
branch. The inspected function does not write that child-array slot in those
cases; it does not itself establish an initialized null child. For a valid
`0x0100` descriptor, `FUN_00196B40` separately reads its model record's
`+0x2C`, maps zero and `4` to no model, clears its model-present flags, and
stores zero at scene-child `+0x94`. A composition child and that child's
model are therefore separate dependency checks. The subsequent
`FUN_00195600` writes a parent pointer through every child-array entry, and
`FUN_00195510` reads every child's tag, without a null-child guard.
Instructions and bytes at `0x00195634..0x00195664` corroborate the unconditional
entry dereference and `+0x80` store. A skipped constructor branch therefore
does not establish safe omission from a composition; the finalized child
array must already contain usable scene children.

**Observation — rendering needs a secondary material cache.**
`FUN_001992A0` builds model-part instances through `FUN_0019A0C0`. The latter
reads the part's material record at part `+0x04`, then copies that record's
`+0x30` into the instance's first word, using zero when the cache is zero.
This differs from `FUN_00115BA0`, which traverses material descriptor
`+0x2C` and its texture record. Cross-container matching copies `+0x2C`
but not `+0x30`, so a descriptor-key closure alone cannot establish the
draw-cache relationship. Cache creation and refresh belong to
[Texture and material runtime](../../runtime/rendering/texture_material_runtime.md);
this observation does not establish a failure in any selected retail set.

**Observation — effect construction requires a ready texture.** Material
binding in `FUN_0019A570` maps a texture record's sentinel `4` to a zero
binding. Effect construction takes a different route: `FUN_001963F0` reads
its texture record's `+0x2C` and passes it directly to `FUN_0019A620`
(`0x00196480..0x0019648C`). That helper skips palette lookup only for zero;
for any other value it calls `FUN_0019E760`, whose complete two-instruction
body is `jr ra; lw v0,0x3C(a0)` (bytes `08 00 E0 03 3C 00 82 8C`). An
unresolved sentinel `4` would therefore be used as a texture pointer and read
at address `0x40`. The later effect draw's zero-texture branch does not cover
that construction path. This establishes a consumer requirement, not an
observed retail failure; the selected effect leaves below have local typed
texture definitions.

**Observation — generator registration is not a missing-object validator.**
`FUN_001AACF0` tests its generator descriptor only for nonzero, then dispatches
child records by tag to `FUN_0034C4A0` (`0x0900`), `FUN_0034C420` (`0x0E00`),
or `FUN_0034C570` (`0x0700`). Those registration helpers store the supplied
descriptor pointer in their generator entry; none checks zero or `4`.
Unrecognized tags take no registration branch, but the loop still calls the
name-derived auxiliary lookup `FUN_001AABC0` on the first child. Its result
is conditional on the entry's name-selector bytes, not a generic child
readiness check. Missing behavior must therefore be assessed at the eventual
consumer, not inferred from registration or a directory match.

### Selected animation-effect leaves

**Observation — two concrete local effect closures.** The `2TEWCHA1` initial
object-section walk covers `0x1B74..0x273C`, ending before the first `0x0700`
animation; the `2HKGCHA1` walk covers `0x2734..0x2F7C` on the same basis.
To inspect the later selected leaves without pretending to decode all
animation tracks, four-byte-aligned header scans were bounded to each file's
object start and decompressed end (`0x10448` and `0x14670`). A candidate
required marker `0xCCCC`, the selected tag, an in-range target ID and matching
directory identity. Each listed effect, texture and palette has one such
definition in that range. Their count-based consumed endpoints were then
checked against the next header. These are independently corroborated typed
leaf paths, not complete file or animation closures.

| Input | Selected typed route, with decompressed block offsets |
| --- | --- |
| `PL/2TEWCHA1.CCS` | Generator row 1, `PGE_ptewcha11_0` (`0x1B74`) -> effect row 2, `EFF_2tewbom0` (`0x9E0C`) -> texture row 164, `TEX_2tewbom0` (`0xC04C`) -> palette row 194, `CLT_2tewbom0` (`0xBC30`). |
| `PL/2TEWCHA1.CCS` | Generator rows 3 and 5, `PGE_ptewcha11_1/2` (`0x1BF8`, `0x1C9C`) -> the same effect row 4, `EFF_2tewbom3` (`0xA040`) -> texture row 171, `TEX_2tewbom3` (`0xD34C`) -> palette row 196, `CLT_2tewbom3` (`0xD2F0`). |
| `PL/2HKGCHA1.CCS` | Effect row 290, `EFF_2hkgwal3` (`0x104E4`) -> texture row 224, `TEX_2hkgwal2` (`0x12634`) -> palette row 292, `CLT_2hkgwal2` (`0x125D8`). |

`PAC_ptewcha11`, row 6 at `0x1D20`, contains exactly three generator entries,
all naming attachment row 8 and auxiliary record zero, and names animation
row 7, `ANM_ptewcha11`. Each generator has one child entry; the middle
generator's two parameter entries do not introduce a second child resource.
Thus this packet references three generator definitions but only two distinct
effect/texture/palette chains. Their child-registration gate is negative
(`-1`) and both name-selector bytes are zero in every child entry, so the
auxiliary name-lookup route introduces no additional resource for these
entries. This is stored sharing; it does not establish how many generator or
effect instances are active at once.

Attachment row 8 is the `0x0A00` wrapper defined at `0x5AEC`; it targets
local row 106, `OBJ_gpos_tew`, whose `0x0100` definition at `0xBC14` has
parent, model and controller IDs zero. This is a concrete authored object
for the model-absence constructor branch described above. The two
effect/texture/palette chains are local definitions; they do not themselves
request another file. The remaining animation targets and shared-skeleton
relationships are outside this leaf closure.

### Model geometry outside the material chain

**Observation — a model can own geometry without a material chain.** The
first nonempty model encountered in the `1NRTBOD1` and `1CMNBOD1` prefix
walks is respectively `MDL_1nrt00t0 shadow10` at `0x2450` and
`MDL_1cmn00t0 shadow10` at `0x26B8`. Both use subtype four and one part.
For that subtype, `FUN_001B0C40` assigns record zero to part `+0x04` and
calls `FUN_0018D740`; that function reads its own vertex/index counts and
builds geometry packets retained at part `+0x34/+0x38` on its successful
path. `FUN_0019A0C0` copies those two fields into the model-part instance
independently of its material-cache read. The collector's material walk sees
record zero's null primary pointer and skips that subordinate route; the
model itself and its generated geometry remain distinct requirements. The
two source blocks each contain 20 vertices and 96 index words; count-based
consumption ends at `0x2674` and `0x28DC`, both followed by a `0x0800` header.
These offsets are decompressed file offsets. The full body-file geometry
and subtype variants have not been closed by the
ordinary model/material/texture/palette walk above.

## Authored directory census

**Observation — bounded corpus.** The following 1,094 retail CCS files were
gzip-decoded in memory from `@source_na2/DATA/DATA.CVM.files/DATA.CVM.iso.files/`.
Every namespace and object-directory row was read, with chunk-2 and array bounds
checked. Keys compare exact bytes up to the first NUL, preserving non-ASCII
name bytes. The census does not walk object blocks using their declared lengths:
those lengths are not uniformly exact, as established in
[Parsing and publication](ccs_runtime.md#parsing-type-dispatch-and-publication).

| Corpus | Files | Directory records, including record zero | Authored `#` records | No other-file non-`#` key candidate | Multiple other-file non-`#` key candidates |
| --- | ---: | ---: | ---: | ---: | ---: |
| `PL/` | 325 | 435,860 | 13,600 | 44 | 262 |
| `CMN/` | 6 | 4,743 | 2 | 2 | 0 |
| `STAGE/` | 24 | 17,940 | 3 | 2 | 0 |
| `STR/` | 383 | 345,246 | 47,279 | 217 | 11,867 |
| `BUDDY/` | 98 | 17,006 | 2,005 | 1 | 55 |
| `PUPPET/` | 46 | 92 | 0 | 0 | 0 |
| `CUTIN/` | 37 | 4,818 | 2,297 | 4 | 453 |
| `3BSC/` | 9 | 27 | 0 | 0 | 0 |
| `3EYE/` | 157 | 19,789 | 4,853 | 266 | 455 |
| `MODENAME/MODE1CMN.CCS` | 1 | 14 | 0 | 0 | 0 |
| Selected root files | 8 | 2,905 | 11 | 11 | 0 |
| **Total** | **1,094** | **848,440** | **70,050** | **547** | **13,092** |

The selected root files are `BATTLEGAUGE.CCS`, `OUGI.CCS`, `STRMCMN.CCS`,
`N_RASH.CCS`, and `N_RASH2.CCS` through `N_RASH5.CCS`. They cover the ordinary
battle paths and one retained adjacent file; this is not the full disc corpus.
The exact disc inventory belongs to [Media layout inventories](media/README.md).

**Limit — these columns are authored-key comparisons.** A candidate is a
different file containing a non-`#` row with the same namespace suffix and
object-name bytes. Neither candidate count predicts a parsed descriptor or
load order. A file may define a `#` row locally in its typed blocks; parsers
may also rename records. Such providers are deliberately not promoted from
directory markers alone. The 547 rows are therefore **not** 547 confirmed
missing runtime resources, and zero authored `#` rows does not establish
freedom from loader, typed-record or code-selected dependencies.

### Locally filled external-marker rows

**Observation — concrete counterexamples.** `FUN_001B3C70` fills the selected
texture row when its current runtime is zero or `4`, without checking the
namespace marker. Its `0x20` flag branch constructs a sampling texture through
`FUN_0019E080`, whose concrete vtable at `0x005D9E70` resolves through
`0x005BF8D8` to `ccSamplingTexChunk`. `FUN_001ACFC0` then replaces the first
namespace byte with space for rows whose runtime is no longer `4`. Thus these
authored `#` rows can be provider definitions after parsing:

| Retail file and directory row | Authored identity | Texture block offset, decompressed | Parser-consumed endpoint |
| --- | --- | ---: | ---: |
| `CMN/EFFECT0X.CCS`, row 2615 | `TEX_sampling00`, `#e\0x\tex\sampling00.bmp` | `0x15E390` | `0x15E3B4`, next tag `0x0300` |
| `CMN/EFFECT0X.CCS`, row 2090 | `TEX_sampling01`, `#e\0x\tex\sampling01.bmp` | `0x15E3B4` | `0x15E3D8`, next tag `0x0400` |
| `STRMCMN.CCS`, row 233 | `TEX_strbreak`, `#e\00\tex\strbreak.bmp` | `0x27D38` | `0x67D5C`, next tag `0x2400` |

The two sampling blocks have flags byte `0x21`, no CLUT or transfer-group
record, and zero pixel dwords. Each consumes `0x24` bytes including its header,
although each declares 57 payload dwords. The `TEX_strbreak` block has flags
`0x01`, CLUT ID zero, transfer-group record 377, and 65,536 pixel dwords;
its consumed length likewise follows its mip counts rather than the declared
65,593 payload dwords. The source headers, IDs, flag bytes, per-level counts
and immediately following headers corroborate the parser paths.

**Observation — shared sampling edge.** `PL/2NWVBOD1.CCS` rows 4721 and
4732, directory offsets `0x264EC` and `0x2664C`, request those two exact
sampling keys. The census found no non-`#` authored providers for those keys,
but `CMN/EFFECT0X.CCS` provides the typed definitions above. Sampling
construction and downstream drawing belong to
[Texture and material runtime](../../runtime/rendering/texture_material_runtime.md).

### Shared skeleton and effect-key examples

| Consumer file | Authored `#` rows | Matching provider set in the inspected corpus |
| --- | ---: | --- |
| `PL/1NRTBOD1.CCS` | 0 | No authored external-marker edge. |
| `PL/2NRTBOD1.CCS` | 34 | `CMN/2CMNBOD1.CCS`. |
| `PL/2NRTCHA0.CCS` | 94 | `CMN/2CMNBOD1.CCS` and `PL/1CMNBOD1.CCS`. |
| `PL/2NRTCHA1.CCS` | 34 | `CMN/2CMNBOD1.CCS`. |
| `CMN/2CMNBOD1.CCS`, `PL/1CMNBOD1.CCS` | 0 each | No authored external-marker edge. |
| `STAGE/S01.CCS` | 0 | No authored external-marker edge. |

These rows corroborate the existing
[Shared skeleton containers](../character_assets.md#shared-skeleton-containers)
contract without treating a shared skeleton as the character's selected model.

**Observation — duplicate authored providers.** `STR/D01_10.CCS` row 18
(`0x80C`) requests `TEX_e00smok04` under `#e\00\tex\e00smok04.bmp`.
Its non-`#` candidate providers are `STR/D01_10E.CCS`, `STR/D03_30E.CCS`,
and `STR/D19_20E.CCS`. Row 476 (`0x414C`) requests `OBJ_e00line03` under
`#e\00\max\e00line03.max` and has ten candidate files. The selected
skill-1 request includes `D01_10E`, not all candidate files. This is why a
file dependency edge is a selected provider relationship rather than the
union of every matching authored key on disc. When several providers are
actually published, traversal/load order matters as described in
[Cross-container references](ccs_runtime.md#cross-container-references).

## Selected load sets

### Common providers and battle preparation

**Observation — startup prerequisites.** Resident `FUN_001E0EE0` calls
`FUN_001E7F50` before its permanent frontend state loop. The latter reads all
five pointers at `0x00404A70..0x00404A83`, checks each through `FUN_001AA450`,
and synchronously loads an absent file through `FUN_00116DE0`. Its paths are
`cmn/cw2.ccs`, `cmn/effect0x.ccs`, `cmn/gauge.ccs`, `cmn/particle.ccs`, and
`cmn/shade.ccs`. This establishes a selected startup provider set including
the sampling definitions above; it is not a measurement of later residency.

**Observation — battle request set.** `FUN_001E9520` selects the three paths
at `0x00404AC0` (`cmn/2cmnbod1.ccs`, `pl/1cmnbod1.ccs`,
`modename/mode1cmn.ccs`), `battlegauge.ccs`, the four BTL common paths
(`shade.ccs`, `gauge.ccs`, `strmcmn.ccs`, `ougi.ccs`), one stage archive,
both sides' conditional paths, and the stage-associated `n_rash` path.
Argument zero loads missing containers synchronously; a nonzero argument
queues them and starts one background load worker after selection. The BTL
four-path table is live `0x008A59E0`, preserved bytes `0x008A59A0`, raw
BTL offset `0x1F1AE0`; its literal pointer values are already live.

The complete setup order and fence ownership belong to
[Resident setup order](../../gameplay/session/battle_lifecycle.md#resident-setup-order).
Logical bare names such as `gauge.ccs` are resolved by
[Resident file services](runtime_services.md#logical-and-explicit-path-routes);
the physical file is `CMN/GAUGE.CCS`. Disc placement and request spelling
must therefore remain separate graph attributes.

### All nine per-side selection slots

`FUN_001E80F0(manager, side, mask, deferred)` handles sides 1 and 2 and
uses `base = manager + side*0x134`. The nine 30-byte path buffers and adopted
container slots are:

| Mask | Path at base | Handle at base | Source and selection condition |
| ---: | ---: | ---: | --- |
| `0x001` | `+0xA3C` | `+0xA18` | `pl/` plus the fighter's `1BOD1` filename. |
| `0x002` | `+0xA5A` | `+0xA1C` | `pl/` plus the fighter's `2BOD1` filename. |
| `0x004` | `+0xA78` | `+0xA20` | `pl/` plus `FUN_00307C60(selection+0x30)` when that selector is greater than 1. |
| `0x008` | `+0xA96` | `+0xA24` | The same provider selector at selection `+0x34`, also greater than 1. |
| `0x010` | `+0xAB4` | `+0xA28` | `3eye/` plus the fighter's `3PCT` filename. |
| `0x020` | `+0xAD2` | `+0xA2C` | BTL live `0x00885580` generates `buddy/2%sbdy.ccs` for a selected support other than `0x24`. |
| `0x040` | `+0xAF0` | `+0xA30` | BTL live `0x008855E0` generates `buddy/2%sbdy%d.ccs` from the secondary support selector; the same support sentinel gate applies. |
| `0x080` | `+0xB0E` | `+0xA34` | BTL live `0x00885660` generates `3bsc/3%s3bsc.ccs` only for an admitted support/fighter combination; the helper scans ten four-byte rows. |
| `0x100` | `+0xB2C` | `+0xA38` | `cutin/1%scutin.ccs` when BTL live `0x00772A20` admits the fighter through its 94-byte availability table. |

The selection record is `manager + side*0x28`; fighter ID is `+0x24`,
the two animation-provider selectors are `+0x30/+0x34`, and the support
fields are `+0x40/+0x44`. Instruction bytes at resident
`0x001E8430..0x001E8454` and `0x001E84D0..0x001E84EC` corroborate the two
selector arguments omitted from the decompiler's call display. Helper body
addresses in the table are live; their preserved bodies are `0x40` lower.
The support format-string operands likewise point to live strings, whose
preserved bytes are at `0x008BF600`, `0x008BF620`, and `0x008BF640`.

Filename tables, the six-selection publication `FUN_001E1530` and the
loading-portrait consumer of the side-2 `3PCT` slot remain in
[Character asset tables](../character_assets.md#selection-and-loading-consumers).

#### Request writes

**Observation:** With queue-mode argument zero, `FUN_001E80F0` directly calls
blocking `FUN_00116DE0` (`ccs_load_if_absent`) for each selected path. With
queue mode nonzero, it checks each constructed path through `FUN_001AA450`:
an absent container is queued through `FUN_001CF9E0`
(`ccs_enqueue_unique_load`), while an already published container goes
through the blocking wrapper instead.

The blocking wrapper returns zero when the named container already exists;
it does not return that container's pointer. A request writes its per-side
handle only for a nonzero return from a new load, and ignores the queue
submission's return. Thus an existing or newly queued resource can have a
stored path but a zero side handle until the later adoption pass. None of
these branches clears a previously stored handle or reports a status to its
caller. The wrapper and queue contracts belong to
[Loading and cancellation](ccs_runtime.md#loading-and-cancellation).

#### Adoption and cache reset

**Observation:** `FUN_001E86C0(manager,side,mask)` visits the selected slots
only for sides 1 and 2. For each zero handle it calls `FUN_001AA450` with the
stored path and retains a nonzero result. It neither issues a load nor
increments a container-use count. The two jutsu slots additionally require
their current selectors at `manager+side*0x28+0x30/+0x34` to exceed 1;
support and cut-in adoption do not repeat the request-time availability gates.
Handle sharing and the release paths below mean that two selected slots need
not represent two independent allocations.

`FUN_001EDA50` waits until `FUN_001CFD70` reports no active queue worker,
clears the retained queue, then adopts mask `0x1FF` for both sides before
advancing to manager state `0x0E`. That establishes the static
request-to-adoption boundary, not successful publication of every requested
file. The preparation sequence belongs to
[Resident setup order](../../gameplay/session/battle_lifecycle.md#resident-setup-order).

`FUN_001E7FE0(manager,side)` nulls all nine handles and empties their path
strings without destroying a container. Side argument `-2` applies that reset
to slots 0, 1 and 2; arguments 1 and 2 reset one side. It is a cache reset,
so its caller must separately arrange any required release.

#### Masked release and shared aliases

**Observation:** `FUN_001E8960(manager,side,mask)` destroys each selected
nonzero handle through `FUN_001A9790(handle,1)`, clears its slot, then clears
matching pointers in both sides' corresponding slots. It does not defer
destruction because the other side has the same pointer. This is alias
invalidation for a full release, rather than a per-side reference-count
decrement. Container destruction and external-record invalidation remain in
[Low-level destruction](ccs_runtime.md#low-level-destruction).

The two jutsu slots form one release group: either mask bit `0x04` or `0x08`
releases **both** `base+0xA20` and `base+0xA24`. After each destruction, both
jutsu slots of both sides are checked for the freed pointer. If the two local
slots held the same pointer, clearing aliases after the first release leaves
the second zero and prevents a second destruction. Instructions
`0x001E8C08..0x001E8D08` establish the `mask & 0x0C` gate and all four
alias comparisons. Other families clear only their corresponding slot across
the two sides; there is no general scan of every manager handle.

#### Pending-side release preserves the other side's resources

**Observation:** `FUN_001E8E20(manager,side,slot)` compares a nonzero handle
with the same slot on the other side. A match leaves the container and the
selected side's slot untouched; otherwise it destroys and clears the selected
slot. Unlike the masked release, this helper preserves an adopted resource
still used by the other side. Its complete body has no internal side or
slot bounds check; the established caller below supplies slots 5, 6 and 7.

`FUN_001E8EE0` chooses side 1 when pending ID `manager+0x50` is nonzero,
otherwise side 2 when `+0x78` is nonzero, and returns if neither is pending.
Its character and jutsu ownership rules differ:

- It passes mask `0x113` to the full-release helper only when the two current
  character IDs differ. That mask covers both body containers, portrait and
  cut-in; equal current IDs retain these resources for the other side.
- It passes support slots 5, 6 and 7 to the single-slot helper, which retains
  exact other-side matches independently of character identity.
- For each jutsu handle, it checks **both** jutsu slots on the other side.
  A match retains the resource. If neither matches, it releases the first
  local handle, then releases the second only when it differs from the
  original first handle. This avoids duplicate destruction when the local
  providers coincide. Instructions `0x001E8FAC..0x001E90CC` corroborate the
  cross-slot checks and retained first-pointer comparison.

Skipped or duplicate handles can remain in the pending side's cache at this
helper's return. Its established state-`0x17` caller, `FUN_001EE1C0`, then
calls `FUN_001E7FE0` for that side before installing its pending identity and
requesting mask `0x1FF`. The reset discards those local aliases while the
other side's adopted pointers remain available. Form-selection gates and
the whole-fighter destruction/construction sequence belong to
[Post-UJ replacement](../../gameplay/characters/awakening.md#static-reconstruction-order).
This resource trace does not establish display timing or an in-place model
swap.

#### Established release callers

**Observation:** `FUN_001E8960` has five established resident direct
callers, each inspected completely. The two global cleanup routines
`FUN_001E9730` and `FUN_001EDEE0` release mask `0x1FF` for side 1 and then
side 2, so the first side's alias clearing prevents releasing a shared pointer
twice. `FUN_001E8EE0` uses the selective rules above. `FUN_001EE500` can fully
release an altered other side before restoring its saved configuration, then
applies pending-side release and requests the new paths. `FUN_001FE920`
releases every changed side before restoring saved configuration and
submitting replacement requests. The latter's decompiler omits queue-mode
argument 4: instructions `0x001FE9F4..0x001FEA18` establish `a3 = 1` at its
`FUN_001E80F0` call.

The established resident callers of the request helper are `FUN_001E9520`,
`FUN_001EE1C0`, `FUN_001EE500` and `FUN_001FE920`; the sole established
single-slot-release caller is `FUN_001E8EE0`. These are resident direct call
edges, not a whole-program exclusion of indirect or overlay calls.
Saved-configuration and form-state semantics remain in
[Manager identity and resource reset](../../gameplay/characters/awakening.md#manager-identity-and-resource-reset)
and [Continuation encounters](../../gameplay/session/battle_lifecycle.md#continuation-encounters-rebuild-the-session).

### Stage-selected edges

**Observation — all 24 entries.** BTL stage acquisition at preserved
`0x006C30C0` / live `0x006C3100` directly indexes the 24-pointer table at
live `0x00890A10`, preserved bytes `0x008909D0`, raw file offset `0x1DCB10`.
The entire table names `stage/s01.ccs` through `stage/s24.ccs`; the routine
looks up the selected container and loads it on a miss. It does not derive
additional file requests from the selected stage's object directory.
Resident `FUN_001E9520` separately requests `FUN_00207E20(stage_slot)`.
That selector's reachable groups are `n_rash.ccs`, `n_rash3.ccs`,
`n_rash4.ccs`, and `n_rash5.ccs`; its retained six-path table has two
unselected entries. Exact slot mapping, archive consumers and release order
belong to [Stage identity and resource mapping](../../gameplay/stages/stages.md#stage-identity-and-resource-mapping).

The 24 stage directories contain only three authored `#` rows: `S03` row 649
at `0x5C0C` and `S18` row 244 at `0x250C` request `TEX_sampling00`; `S04`
row 585 at `0x59EC` requests `TEX_e0xpar03` under
`#e\0x\tex\e0xpar03.bmp`, matching `CMN/EFFECT0X.CCS`. The offsets are
decompressed directory offsets. This small count does not replace the
separate stage-selection, effect-provider and typed-object paths.

### Cinematic request table and bounded closure

**Observation — complete table bounds.** Of the 184 `SINF` rows in
`STRMCMN.CCS`, 151 have no extra path, 28 have one, and five have two. Row
zero has no streamed path; the other 183 rows each have one. `FUN_00357B10`
clears row zero's main-path pointer during initialization. Blob framing,
relocation and request-list flags are owned by
[Request-table source](ccs_runtime.md#request-table-source) and
[Request list](ccs_runtime.md#request-list).

**Observation — concrete selected closure.** Skill row 1 requests main
`str/d01_10e.ccs`, extra `pl/2nrtbod1.ccs`, then stream `str/d01_10.ccs`.
Against that main/extra set and the already selected common and Classic
Naruto body files, all 187 authored external rows in the stream have
matching non-`#` directory keys:

| Candidate provider | Stream rows with matching key |
| --- | ---: |
| `PL/1NRTBOD1.CCS` | 54 |
| `PL/1CMNBOD1.CCS` | 68 |
| `PL/2NRTBOD1.CCS` | 25 |
| `STR/D01_10E.CCS` | 40 |
| `STRMCMN.CCS` | 2 |

These 189 matches cover 187 distinct stream rows. Rows 495 (`0x43AC`,
`OBJ_e00board01_w`) and 503 (`0x44AC`, `OBJ_e00board01_b`) each match both
`D01_10E` and `STRMCMN` under `#e\00\max\e00board01.max`. The directory
matches do not establish which provider wins for the selected load order.

`2NRTBOD1`'s 34 external skeleton rows in turn match `CMN/2CMNBOD1.CCS`.
`D01_10E`, `1NRTBOD1`, and both skeleton providers have no authored external
rows. The common sampling and break-texture definitions are locally filled
as shown above. This closes the inspected **authored-key** relationships for
that selected set; it does not establish all typed materializations or memory
lifetimes. Dynamic character replacement remains a separate consumer:
`FUN_00354640` chooses the `1cmn`/`2cmn` composition, searches the selected
fighter's body containers, and attaches the selected model through
`FUN_00355C70`, as recorded in
[Explicit jutsu-stream body dependencies](../character_assets.md#explicit-jutsu-stream-body-dependencies).

**Observation — typed closure of the selected main provider.** The complete
decompressed object section of `STR/D01_10E.CCS` was walked from `0x2A54` to
tag `5` at `0x64EDC`. It contains 230 definitions: 40 each of `0x0900`,
`0x0100` and `0x0800`, 38 materials, 36 textures, and 36 palettes. All 40
models use subtype zero, flags zero, and one part. Their endpoints were
computed from the resident `FUN_001B0C40 -> FUN_001B0790` part/count path;
texture endpoints use per-level counts, and palette/composition endpoints
use their own counts. Each endpoint was checked against the next header.
No declared-length resynchronization or all-candidate directory graph was
used for this object section.

The 40 skill-1 stream keys that match this file comprise 36 `0x0100` objects
and four textures. Walking only their stored model, part-material,
material-texture and texture-palette links reaches 171 distinct defined
records: 36 objects, 36 models, 35 materials, 32 textures, and 32 palettes.
Every nonzero link on those routes has a correctly typed definition in the
same selected file. All object parent/controller IDs and image-transfer-group
IDs in this file are zero. The 40 additional part bookkeeping rows are
explicitly cleared by the subtype-zero model parser; they are not 40 missing
model definitions. Together with record zero they account for the difference
between the 271 directory rows and 230 definitions.

For example, stream rows 495 and 503 match provider rows 46 and 44,
`OBJ_e00board01_w` and `OBJ_e00board01_b`, at `0x33E8` and `0x311C`.
They link respectively to model rows 51 and 47 at `0x3404` and `0x3138`.
Both model parts use material row 49, `MAT_e00board01`, defined at `0x33CC`;
it links to texture row 50, `TEX_e00white01`, at `0x1BDB0`, and that texture
links to palette row 116, `CLT_e00white01`, at `0x1BD54`. Both models refer
to one local material and texture definition. All offsets in this paragraph
are decompressed file offsets.

These local material definitions enter `FUN_001AD9C0`'s material list, which
constructs their secondary render caches at record `+0x30`. That supplies the
local cache-creation path needed by the model-part consumer described above;
successful allocation and later residency are not established by this static
walk. The two board keys also match `STRMCMN.CCS`, so this result establishes
a complete typed route through `D01_10E` without establishing which duplicate
provider the resolver selects. The selected body, stream-target and attachment
routes are examined separately below; the main-provider chain alone does not
close them.

**Observation — the duplicate board routes have matching content.** The
alternative definitions in `STRMCMN.CCS` were followed independently:
object rows 149/151 at `0x10810`/`0x10ADC` -> model rows 152/156 at
`0x1082C`/`0x10AF8` -> material row 154 at `0x10AC0` -> texture row 155 at
`0x27B14` -> palette row 376 at `0x27AB8`. Each route has the same resource
names and typed links as the `D01_10E` board route. For corresponding black
and white objects, every remaining payload byte matches after removing only
container-local record IDs: object target/parent/model/controller IDs,
model target and its part bookkeeping/material IDs, material target/texture
IDs, texture target/palette/group IDs, and palette target/group IDs. Those
removed dependency IDs were checked by following their named targets; parent,
controller and group IDs are zero in both routes. Model geometry, scalar
parameters, texture pixel words and palette words are therefore equal in
these compared definitions. Their payload lengths are respectively 20, 652,
20, 540 and 84 bytes on both routes.

This narrows the ambiguity for the two board keys: either inspected provider
offers the same compared resource content. It still leaves provider identity,
allocation/cache instances and later lifetime dependent on publication and
selection. The comparison covers these two board chains, not other duplicate
keys or the rest of either container.

### Skill-1 composition and body targets

**Observation — concrete composition children.** In `STR/D01_10.CCS`,
48 `0x0900` definitions occupy `0x7604..0xB5A4`. Their 388 child references
name 388 distinct local records: 368 `0x0A00` wrappers and 20 `0x0100`
objects. Each wrapper has a local typed definition and targets one of 178
distinct imported object records: 52 from `1NRTBOD1`, 65 from `1CMNBOD1`,
25 from `2NRTBOD1`, and 36 from the main provider. These are the object
portion of the 187 external keys closed above; the remaining nine keys
are textures. Repeated wrappers create separate authored child identities
while sharing their target provider. `FUN_001B2800` changes the wrapper's
name prefix from `OBJ` to `EXT`; it does not change its record index or
request another file. The local objects each name a defined `0x0800` model
with zero parts, which `FUN_001B0C40` publishes with a null primary pointer.
Their parent IDs are zero or local object records, and their controller IDs
are zero. Thus the local model-absence branch is intentional stored structure,
not an unclosed material/texture route.

The complete stream object section was walked from `0x7434`
through tag `5` at `0x12060`, with playback beginning at `0x1206C`.
The 48 composition endpoints use their child and transform counts; the
368 wrapper and 20 object endpoints use the version-`0x123` parsers.
Textures at `0xC0E0` and `0xD494` consume through `0xC304` and `0xDCB8`,
respectively, rather than their declared endpoints `0xC3CC` and `0xDD80`.
The other handlers' consumed endpoints agree with their declared endpoints.
No resynchronization search was used in this complete section walk.
Namespace/name matching preserved each byte up to its first NUL; the walk
does not establish successful scene allocation.

**Observation — local parent and metadata routes.** Every nonzero parent
of the 388 children occurs in the same composition's child list. The stream
contains 383 `0x2000` metadata blocks; all of their first and third nullable
record references are zero. The middle reference is nonzero in 53 blocks,
using eleven named `LYR_*` records. All eleven occur in the initial
`0x1700` registry's kind-zero entries, which construct their typed registry
descriptors before the object/wrapper metadata is installed. This is a
local registry dependency, not a material or model link. The complete
stream object section contains no `0x2300` child-attachment parameter block
and no `0x0700` packed animation resource. The general metadata and
attachment contracts remain in [CCS object types](ccs_object_types.md).

**Observation — playback binds child instances.** `FUN_001A0B80` first
creates one 16-byte playback-table entry per directory row, resolving imported
providers through `FUN_001161A0` and taking the resolved record's secondary
pointer. It then constructs each composition through `FUN_001952F0` and
replaces the source child record's table entry with that composition's actual
scene child. Those entries have type `0x0100` and flags `6`: they borrow the
composition-owned child and permit drawing without owning its destruction.
Thus repeated wrappers share provider descriptors but have separate scene
instances. Temporary record `+0x34` associations are cleared after binding;
container `+0x60` retains the playback table. `FUN_001A2520` destroys entries
with ownership bit `0` set and frees the table; borrowed child entries are
released with their owning composition instead.

The streamed `0x0101` consumer `FUN_001B5900` reads the full transform,
alpha and visibility payload before looking up `+0x60[record ID]` through
`FUN_001B56B0`; a null target returns after those reads. This differs from
the nested packed-animation binding described in
[Animation target binding](../../runtime/animation_runtime.md#target-binding-and-transform-application).

**Observation — concrete frame targets.** The frame-command walk begins at
`0x1206C`, covers frame markers 0 through 318, and ends with marker `-1`
at `0x5521A0`, consuming exactly the decompressed file end `0x5521AC`.
All command endpoints computed from the selected handlers' fields agree
with their declared lengths; all target IDs are inside the 883-row directory.
Its 87,566 transform commands address 581 distinct rows: the 368 wrappers,
20 defined objects, and 193 local `OBJ_*` rows 690 through 882 with no
definitions in the object section. Those last rows share the local
`d\01\sss\d01_10.max` namespace suffix and are not additional external keys.
The absence of their definitions must not be counted as 193 missing files.
Their initial playback-table targets are null; later callback substitution
must be distinguished from this initial state.

For example, frame-zero transform commands at `0x146D8`, `0x15C44`, and
`0x17BA0` address body wrappers 204 (`1cmn`), 258 (`1nrt00`), and 338
(`2nrt00`). The second `1nrt` instance uses row 312; the four additional
`2nrt` instances use rows 364, 390, 416 and 442. These are distinct stream
child identities even where their provider body/model records are shared.
The frame walk contains no mesh-position/index replacement commands
`0x0802/0x0803`, so its own playback does not introduce a second stored
geometry dependency through those handlers.

The remaining addressed routes comprise ten locally defined materials,
the local camera/light records, one local `0x1A00`, eight local `0x1B00`
and one local `0x1D00` descriptor. The `0x1801` command instead names the
undefined local `SHD_shadow_buffer` row 689; `FUN_001B57F0`'s null-target
branch uses the play context's default shadow object. Their parameter
contracts belong to [Streamed frame data](ccs_runtime.md#frame-stream).

**Observation — body nodes have typed providers.** Each of the 52, 65 and
25 selected imported body-object keys above has a local `0x0100` definition
in its selected provider. Their parent links remain within that provider's
object set. The concrete body leaves are:

| Selected provider | Body object -> model, with decompressed block offsets | Model route |
| --- | --- | --- |
| `PL/1NRTBOD1.CCS` | Row 54, `OBJ_1nrt00t0 body` (`0x6070`) -> row 189, `MDL_1nrt00t0 body` (`0x608C`) | Subtype 2, 31 parts, 43-byte palette-order list. |
| `PL/2NRTBOD1.CCS` | Row 118, `OBJ_2nrt00t0 body` (`0x1247CC`) -> row 4633, `MDL_2nrt00t0 body` (`0x1247E8`) | Subtype 2, 20 parts, 20-byte palette-order list. |
| `PL/1CMNBOD1.CCS` | Row 67, `OBJ_1cmn00t0 body` (`0x521C`) -> row 190, `MDL_1cmn00t0 body` (`0x5238`) | Subtype 2, one part, one-byte palette-order list. |
| `CMN/2CMNBOD1.CCS` | Row 68, `OBJ_2cmn00t0 body` (`0x63C14`) -> row 1362, `MDL_2cmn00t0 body` (`0x63C30`) | Subtype 3, one property-geometry part, one-byte palette-order list. |

`CMP_1cmn00t0 trall`, provider row 3 at `0x1A4C`, contains 64 child
records; `CMP_2cmn00t0 trall`, provider row 1299 at `0x61464`, contains 34.
Their count-derived endpoints are `0x245C` and `0x619C4`. Every listed
child has a local `0x0100` definition. The 34 shared-skeleton keys imported
by `2NRTBOD1` match the latter composition's 34 typed object definitions.
The selected `2nrt` body nodes themselves are local definitions, so those
shared-skeleton imports must not be substituted for the selected body model.
Model palette ordering and replacement binding remain owned by
[Model and skeleton runtime](../../runtime/rendering/model_runtime.md#packed-geometry-influences-and-matrix-palette)
and [Explicit jutsu-stream body dependencies](../character_assets.md#explicit-jutsu-stream-body-dependencies).

**Observation — selected body geometry and material leaves.** The model
readers' consumed counts close the 242 selected model definitions across
these four providers: 170 subtype-zero models, three subtype-two body models, one
subtype-three body model and 68 subtype-four shadow models. Every computed
endpoint lands on the next marked header. Empty subtype-zero models consume
no part payload. The nonempty ordinary models in `1NRTBOD1` and `1CMNBOD1`
add the eye/mouth material leaves; the selected `2NRTBOD1` and `2CMNBOD1`
subtype-zero models are empty.

For the two Naruto subtype-two bodies, all 31 or 20 parts respectively
reference one body material. The first 30 or 19 parts use the packed rigid
reader `FUN_001AF1F0`; the last part uses `FUN_001AE190`'s weighted reader.
The weighted parts contain 2,628 vertices / 4,382 influence words for `1nrt`
and 976 vertices / 1,457 influence words for `2nrt`. Their influence-group
terminators produce exactly the stored vertex counts. The `1cmn` body's
single rigid part has 24 vertices. The `2cmn` subtype-three part instead uses
`FUN_00181760` and its property-data reader `FUN_00181520`; its six property
headers close at the material block. It must not be decoded as the
subtype-two weighted payload.

| Provider | Body model endpoint / material | Texture -> palette rows | Texture / palette block offsets |
| --- | --- | --- | --- |
| `1NRTBOD1` | `0x236D4`, material 190 | 191 -> 193 | `0x24590` / `0x2393C` |
| `2NRTBOD1` | `0x130F00`, material 4634 | 4635 -> 4642 | `0x142A88` / `0x141E34` |
| `1CMNBOD1` | `0x53C0`, material 191 | 192 -> 194 | `0x627C` / `0x5628` |
| `2CMNBOD1` | `0x63E00`, material 1363 | 1364 -> 1366 | `0x6417C` / `0x64068` |

Following the nonzero model-part dependencies in each provider reaches
respectively 4/3/3, 1/1/1, 4/4/4 and 1/1/1 distinct material/texture/palette
definitions. `1NRTBOD1`'s two eye materials share a texture; `1CMNBOD1`'s
two eye materials use separate textures. Every leaf link has a correctly
typed local definition, and all selected image-transfer-group IDs are zero.
Material endpoints use the version-`0x123` fixed payload; texture endpoints
use each level's stored pixel-word count, and palette endpoints use their
stored colour-word count. All land on the next marked header. These routes
enter the same `FUN_001AD9C0` material-cache construction path as the main
provider. This closes the stored geometry/material routes, without proving
successful allocation or the later replacement matrix binding.

**Observation — selected matrix indexes are bounded by their child sets.**
The two `1nrt` stream body compositions each contain 51 children; the five
`2nrt` body compositions each contain 25. Their 43- and 20-byte palette-order
lists select only indexes inside those arrays. Every stored rigid matrix
selector and weighted influence index is inside its corresponding palette:
`0..42` for `1nrt`, `0..19` for `2nrt`, and `0` for `1cmn`.
The shared `1cmn` and `2cmn` model lists contain the single child indexes
2 and 3, within their respective 64- and 34-child compositions. This closes
the inspected stored index routes; it does not prove the selected nodes'
allocated matrices or a later replacement model's name mapping.

**Observation — participant replacement is a later binding step.** After
the initial play table is constructed, `FUN_0035A070` obtains the defender's
four model descriptors from its shared lookup holder, conditionally creates runtime models,
and rebinds `EXT_1cmn00t0 body/eye1/eye2/mou1` through `FUN_00196620`.
The resident names at `0x005AB710` and `0x005ABFD0..0x005AC020` match the
stream wrappers, whose parser changes `OBJ` to `EXT`. Body rebinding uses
mode 6; the packed-model branch maps the incoming model's composition names
to existing scene children. It installs the replacement at scene target `+0x94`.
The four placeholders' local material routes therefore do not close the
actual defender's chosen body, appearance palette or attachment resources.
The selected fighter must supply those descriptors independently.
Additional replacement geometry through `FUN_00354640 -> FUN_00355C70`
uses the separately materialized `1cmn`/`2cmn` composition and the selected
fighter model. Its selection contract is owned by
[Explicit jutsu-stream body dependencies](../character_assets.md#explicit-jutsu-stream-body-dependencies).
These inspected replacement helpers bind existing scene targets or their
models; they do not create file definitions for rows 690 through 882.

**Observation — shadow links are retained alongside ordinary models.** Each
of these four body/skeleton object sets contains 17 nonzero fourth-record
IDs, covering the named `shadow01` through `shadow17` models. The object
parser stores those IDs at descriptor `+0x10` through `FUN_001B1B00`; zero
remains a null pointer, while a nonzero ID becomes a record pointer. They
are distinct from the object's ordinary model record at `+0x0C` and the
separately attached morph controller at `+0x14`. All 68 selected shadow
definitions use subtype four, one part and record-zero material dependency.
For example, `1NRTBOD1` pelvis row 6 names ordinary empty model row 58 and
shadow-model row 59; the body row 54 separately names skinned model row 189.
The corresponding `1CMN` pelvis uses rows 71/72, the `2NRT` pelvis uses
4564/4565, and the `2CMN` pelvis uses 1302/1303. The subtype-four reader
consumes two counts, six bytes per XYZ vertex with four-byte alignment, and
four bytes per index word. Across these 68 definitions the stored vertex
counts are 8, 12, 16, 20 or 24 and index-word counts are 36, 60, 72, 96 or
120. Every count-derived geometry endpoint lands on the next marked header.
Thus these are complete local shadow-geometry inputs, independently of the
ordinary material chain; generated render packets and later selection are
not established by the static payloads.
Scene-child construction through `FUN_00196B40` materializes a nonzero,
resolved fourth-record model separately at child `+0x9C`; the ordinary model
is at `+0x94`. This connects the stored shadow links to their concrete
secondary model instances without treating the empty ordinary pelvis model
as missing shadow geometry.
The selected shadow renderer's contract belongs to
[Shadow rendering](../../runtime/rendering/shadow_rendering.md).

### Selected provider identity and lifetime

**Observation — ownership follows the selected request.** Skill 1's main and
extra requests have flag `0x1000`, so an already published provider is
borrowed and an absent one is loaded into a one-shot wrapper that is destroyed
when playback ends, as described under
[Request list](ccs_runtime.md#request-list).

**Inference — conditional board selection (high confidence).** Battle setup
requests `STRMCMN` before the selected cinematic request. If `D01_10E` is
absent at that later lookup and is loaded anew, its publication puts it at
the directory-list head (`FUN_001AC8A0`). On that path it precedes the older
common provider when the stream's two duplicate board keys are resolved.
If the main provider was already resident, the selected request does not
publish it again; the request-list order alone therefore does not determine
which duplicate wins. Equal board payload content does not make their
provider records, cache allocations or ownership identical.

`FUN_001A9790` invalidates imported record primary pointers and types when
their provider is removed. The playback table already contains resolved
target/cache pointers; this invalidation loop does not rebuild that table.
Consequently authored-key equality and unload invalidation alone do not prove
that all borrowed scene targets remain valid for a particular playback.

**Observation — physical availability has its own limit.** Every default
main, extra and streamed path for rows 1 through 183 was checked against the
retail extraction. Four paths are absent: row `0x9A` names
`str/d21_10e.ccs` and `str/d21_10.ccs`; row `0xA0` names
`str/d25_30e.ccs` and `str/d25_30.ccs`. All other default paths exist.
The complete opponent-override table's nine path-replacement entries and
their derived `E` files also exist. Its three skill replacements change the
selected row; they do not request their placeholder path. The override rules
are owned by [Opponent-dependent cinematic selection](../../gameplay/characters/ultimate_jutsu_cinematics.md#opponent-dependent-cinematic-selection).

**Unresolved — reachability.** No inspected path establishes that skills
`0x9A` or `0xA0` can be selected by a retail battle configuration. Their
absent default files are a table/availability observation, not evidence of
a player-visible failure. Likewise, the complete typed closure of every
cinematic, fighter and stage combination is not established.

**Observation — bounded request admission for the absent rows.** The battle
presentation's direct call to `FUN_0035CF00` is at BTL Ghidra `0x0076A0CC`
(live `0x0076A10C`). The decompiler truncates the presentation's switch;
instruction bytes `0x00769F9C..0x0076A0D0` establish the continuation. At countdown
85 it obtains the record index from the side manager's `+0x60`, calls
`FUN_00372900` at `0x0076A040`, applies the BTL helper gate and passes the
returned skill in argument `a3` to the constructor. The general gate is
owned by [Skill-play admission](../../gameplay/characters/ultimate_jutsu.md#skill-play-admission).

The resident reverse lookup `FUN_00372990` searches indexes `0..222` in
the 20-byte table at `0x005AEC40`; `FUN_00372900` reads that table's signed
skill halfword at `+0x04`, subject to its classification gate. Reading this
complete 223-record domain, `0x005AEC40..0x005AFDAB`, found no `0x9A` or
`0xA0` in that field. Thus an index in this inspected retail record domain
cannot directly supply either absent-path skill through this battle caller.
This does not prove every manager index valid or exclude a later write to
the table. The ten support replacement skills and twelve opponent overrides
already documented by the gameplay owner also contain neither value.

The other indexed direct call is ETC Ghidra `0x006C0CF0` (live
`0x006C0D30`) in `FUN_006C0AB0`. That caller passes viewer field `+0x1C`
directly as the skill, rather than reading the 223-record table at that
callsite; instructions at `0x006C0CE8..0x006C0CF0` corroborate the argument.
`FUN_006BFFE0` supplies that field from the selected 16-byte viewer-list row
at viewer `+0x210 + selection*0x10`, then applies `FUN_00372840`'s
classification gate before entering the playback-selection state. The
producer and permitted contents of that viewer list remain unclosed here.
The constructor itself performs no upper-bound admission
check before indexing the 24-byte SINF row after opponent replacement.
Consequently the battle-table result is a caller-specific limit, not a
whole-program proof that the two missing rows are unreachable.
