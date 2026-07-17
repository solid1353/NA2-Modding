# NA2 Binary Analysis Scope

This record classifies the known NA2 disc artifacts by the minimum useful
analysis level and defines the reusable workflow for later reverse-engineering
tasks. It is based on the preserved outer-ISO, `DATA.CVM`, and AFS inventories,
artifact signatures inspected on 2026-07-18, existing module evidence, and the
preserved NA2 Ghidra materials.

The machine-readable classification is in
`docs/knowledge/binary_analysis_inventory.tsv`. A classification is the default
starting point, not a claim that every byte in an artifact has the same role.
For example, a string-only change in the boot ELF can remain data-oriented even
though the boot ELF warrants a full-program analysis project.

## Decision

- `SLPS_258.37` is the only current full-program disassembly candidate. Create
  or restore its maintained analysis under `@work/NA2/analysis/`; source trees
  contain original binaries only and must never contain Ghidra projects.
- `PRG/BTL.BIN`, `PRG/ETC.BIN`, and `PRG/ADV.BIN` are members of the same
  `MWo3` EE overlay family. They contain code and data but load on demand, so
  create baseline Ghidra programs now, then keep manual analysis tied to a
  concrete question.
- `MODULES/CRI_ADXI.IRX`, `MODULES/SNDBASE.IRX`, and `MODULES/MODULES.BIN` are
  IOP ELF/IRX executables. The current NA2, NUN5, and NUN6 copies are byte-identical,
  so create one reusable baseline Ghidra program for each and deepen the analysis
  only when an audio, streaming, or IOP behavior requires it.
- `MODULES/IOPRP300.IMG` is a `RESET`/`ROMDIR` IOP image. Inspect its container
  structure first and analyze an individual contained executable only when a
  task identifies one.
- Fonts, graphics, CCS resources, sound tables, archives, movies, configuration
  files, and placeholders require format-aware data inspection rather than
  disassembly unless execution evidence proves otherwise.

NUN6 A35 is a Brazilian mod derived from NUN5, not an official sequel. Its
analysis value is specifically as a feature donor: compare its executable and
overlay changes against NUN5, identify implemented modifications, and preserve
portable behavior that may later be ported to NA2.

Therefore the follow-up Ghidra task should create or restore a maintained NA2
boot-ELF project, create baseline programs for the three NA2 EE overlays and
three shared IOP executables, and create corresponding executable baselines for
NUN5 and NUN6.
The task lists the directly signature-confirmed ELF and `MWo3` files for each
game; it does not include resource files merely because they use `.BIN` names.

## Canonical disassembly inputs

- NA2: `@source/NA2.iso.files/SLPS_258.37`, plus `PRG/ADV.BIN`,
  `PRG/BTL.BIN`, and `PRG/ETC.BIN` below the same tree.
- NUN5: `@source/NUN5.iso.files/SLES_556.05`, plus `PRG/ADV.BIN`,
  `PRG/BTL.BIN`, `PRG/ETC.BIN`, `PRG/TEXTENG.BIN`, `PRG/TEXTFRN.BIN`,
  `PRG/TEXTGER.BIN`, `PRG/TEXTITA.BIN`, and `PRG/TEXTSPA.BIN`.
- NUN6 A35: `@source/NUN6 A35.iso.files/SLUS_556.06`, plus `PRG/ADV.BIN`,
  `PRG/BTL.BIN`, `PRG/ETC.BIN`, `PRG/MOD.BIN`, and `PRG/TEXTBRA.BIN`.
- Shared identical IOP inputs (analyze the NA2 copy once):
  `@source/NA2.iso.files/MODULES/CRI_ADXI.IRX`,
  `@source/NA2.iso.files/MODULES/MODULES.BIN`, and
  `@source/NA2.iso.files/MODULES/SNDBASE.IRX`.

All current paths above were confirmed after the 2026-07-18 recursive source
extraction. Keep Ghidra projects and exports under each target's
`@work/<target>/analysis/` tree; the inputs remain read-only.

## Signature evidence

The classification uses direct signatures rather than filename extensions
alone:

- `SLPS_258.37` begins with an ELF header for the Emotion Engine.
- The three `PRG/*.BIN` files begin with `MWo3`; their shared family and existing
  targeted MIPS evidence establish them as raw loadable EE overlays.
- Both `.IRX` files and `MODULES.BIN` begin with ELF headers using the Sony IOP
  IRX type. The `.BIN` suffix does not make `MODULES.BIN` ordinary data.
- `IOPRP300.IMG` begins with `RESET` and `ROMDIR` records.
- `DATA.CVM`, AFS files, and PSS files have `CVMH`, `AFS`, and MPEG/PSS
  signatures respectively.
- `SNDDATA.BIN` is sectioned sound data beginning with `IECS` records.
- `OUT1M.BIN` is exactly 1 MiB of zero bytes in the preserved NA2 source.
- `FLIST.DIR` and `SYSTEM.CNF` are small textual metadata files.

The existing `DATA.CVM` inventory contains 2,310 CCS files, one 61,440-byte
`ICON.BIN`, and one text file. Treat those as format families; do not create
thousands of nominal disassembly targets. A CCS member remains data-only unless
a later task proves that a specific section contains executed bytecode.

## Analysis levels

### Full existing program analysis

Use a full-program project only when all of the following make it materially
useful:

- the artifact is executable code with a sufficiently established ISA, load
  model, and address mapping;
- work repeatedly crosses unrelated functions or subsystems;
- global callers, callees, references, types, or data flow are required;
- the resulting project will be reused and maintained rather than discarded.

For NA2 this applies only to `SLPS_258.37`. Reuse a maintained project under
`@work/NA2/analysis/` once one exists. Historical decompiler exports and
listings are supporting views available through Git history, not canonical
source material. Prior work established that exporting all undefined data
produces an oversized, low-value artifact.

### Targeted disassembly

Use targeted analysis when the question concerns a known patch offset, string
reference, input mask, branch, state field, caller/callee slice, or a small
function family. It is the default for raw overlays and IOP modules because:

- their load address and lifetime may be contextual;
- unrelated code does not improve a narrow investigation;
- exact file-offset evidence is safer to preserve than a speculative global
  function map;
- the existing range, call, address-reference, and Ghidra-export comparison
  tools already cover the common needs.

A targeted classification does not mean postponing the Ghidra import. Create
and preserve a correctly configured baseline program in advance; keep function
naming, typing, and control/data-flow investigation focused until a concrete
task justifies broader manual analysis.

Escalate a targeted artifact to a maintained full project only after repeated
work demonstrates a need for stable global cross-references or types and the
artifact's load/relocation model has been established.

### Data-only inspection

Start with data/layout inspection for archives, media, tables, resources,
configuration, and unknown binary formats without execution evidence. Prefer a
format parser, inventory, structure comparison, string/encoding analysis, or
cross-game member comparison. Do not feed a large archive or media stream to a
disassembler merely because it has a `.BIN` suffix.

If a data artifact contains an embedded executable with a recognized boundary,
extract or copy only that component outside `@source/` and classify the
component separately.

## Minimum reusable workflow

1. **State the question.** Name the observed behavior, target game/version, and
   evidence that points to an artifact, function, address, string, or format.
   Do not begin with an instruction to disassemble everything.
2. **Reuse existing knowledge.** Check `docs/knowledge/`, module-local evidence,
   `docs/HYPOTHESES.md`, current patch definitions, preserved exports, and
   `work/<target>/analysis/` before creating another analysis workspace.
3. **Identify the exact input.** Record the configured-root path, size, content
   hash, signature/format, and whether the file is an original, extraction,
   baseline copy, or modified copy. Keep `@source/` untouched.
4. **Establish the load model before addresses.** Record ISA and endianness,
   resident versus on-demand lifetime, known load base, relocation behavior,
   and the proven formula between file offsets and runtime addresses. If these
   are unknown, keep conclusions file-offset based.
5. **Choose the smallest sufficient level.** Use data inspection first for
   structured resources, a targeted code slice for a narrow executable
   question, and a full maintained project only when the escalation criteria
   above are satisfied.
6. **Create working material outside the source root.** Copy the required
   baseline or preserved analysis to `work/<target>/base/` or
   `work/<target>/analysis/`. Put experiments in `work/<target>/mod/` or a
   task-specific `work/temp/` folder. Never let Ghidra locks, caches, exports,
   probes, or scripts write under `@source/`.
7. **Preserve the minimum evidence.** Record tool/version, import settings,
   function or range boundaries, callers/callees or references used, byte and
   address mapping, comparison source, confidence, and useful negative results.
   Prefer focused exports over whole-program dumps.
8. **Patch through the canonical module.** Guard original bytes or hashes,
   preserve sizes unless separately authorized, record every binary edit, and
   keep permanent file-backed changes out of PNACH.
9. **Test according to lifetime.** A stable boot-ELF hypothesis may use a
   temporary disabled PNACH candidate. An on-demand overlay such as `BTL.BIN`
   or `ETC.BIN` must be tested through a file patch and rebuilt ISO unless a
   proven load-state/signature guard exists.
10. **Promote the result.** Put confirmed reusable behavior and mappings in
    `docs/knowledge/` or module-local evidence; put unresolved interpretations
    in `docs/HYPOTHESES.md`. Remove disposable exports and experiments after
    their durable information is preserved.

## Existing reusable analysis

- Historical NA2 boot-ELF Ghidra material and focused exports remain available
  through Git history. Restore useful evidence only into `@work/NA2/analysis/`;
  never recreate analysis work under `@source/`.
- `scripts/research/menu_input/`: range disassembler, direct-call finder,
  address-reference finder, MIPS mask analyzer, and Ghidra-export comparison
  helpers for targeted EE work.
- `na2_patcher/modules/raw_binary/patch_sets/menu_input/`: reusable overlay and
  boot-ELF function maps, exact edits, provenance, and runtime tests.
- `docs/knowledge/substitution.md`, `docs/knowledge/menu_input.md`, and
  `docs/knowledge/font/`: established analysis boundaries and negative results
  that should not be rediscovered.
- `docs/knowledge/media/`: canonical outer-ISO, CVM, and AFS inventories for
  data/layout work.

## Limits of this audit

This task inspected signatures, inventories, preserved analysis, scripts, and
canonical patch evidence. It did not run Ghidra, disassemble a new range,
re-extract source media, modify a binary, build an ISO, or launch PCSX2. The
classification should be revisited when the unpacking task reveals a genuinely
new executable family or when runtime evidence proves that a data-classified
member contains executed code.
