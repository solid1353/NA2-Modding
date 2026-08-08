# Font runtime migration and composition

## 2026-07-24 weight and spacing refinement

### 2026-07-25 confirmed Load-screen helper erasure

The user captured a state after the game froze while entering the Load screen.
The source was read from
`@pcsx2_stable/sstates/SLOP-NA228 (682CC5FB).01.p2s`, copied without modifying
the user library to
`work/Font/inputs/sstates/load_freeze/user/SLOP-NA228 (682CC5FB).01.p2s`,
and has SHA-256
`67B9329411667E32211B4FAA319ADCF3EF255362FD26C8DF70AFA475D8937644`.
Its embedded screenshot shows the two Load-screen panels before any text was
drawn.

Offline comparison against the same-CRC pre-Load state
`work/Font/artifacts/load_freeze/crash_state/pre_load_same_crc.p2s`, SHA-256
`B20EF54A12952C0A30BD2907E2FD9B6B1B98961620E72658A62B2B2BC7001E0F`,
establishes the failure:

- the pre-Load state matches 19 of the 20 exact canonical Font ELF edits; its
  only mismatch is the separately initialized scale word at runtime
  `0x0060737C`;
- the frozen state still matches all permanent hooks and ordinary ELF edits,
  but all six injected helper/trampoline edits are entirely zero:
  `font_layout_wrappers_01..04`, `font_controls_auto_fit_10`, and
  `font_renderer_metrics_01`;
- the frozen state's zero run is exactly
  `0x003D3DB6..0x003D5D30`, 8,058 bytes, which is the whole clean-file
  common-zero interval containing every new helper;
- the UI scratch record at `0x003FAD20..0x003FAD60` is also zero, but no
  scratch corruption is needed to explain the freeze.

The permanent UI, selected-choice, ordinary-space, and newline hooks therefore
survive while their destinations at `0x003D3E00..0x003D4388` disappear. A
hook entering that range executes zeros instead of a returning helper, which
explains the blank Load screen and hang. Confidence is **high**: the
same-CRC before/after states distinguish transition-time erasure from an ISO
that never contained the blobs.

This rejects the helper interval as persistent executable storage. Do not
reuse it or select another boot-settled zero cave by sampling alone. The
matched renderer formulas and layout decisions remained valid and were
relocated through the shared resident payload as described below.


### 2026-07-25 resident relocation and regression

All executable Font helpers and trampolines are now feature-owned
`runtime_injector` fragments linked by the shared payload builder into
`PRG/228.BIN`. The feature declares symbols and relocations but no payload
offsets or final runtime addresses. The UI helper also replaces the former
global scratch record with a 64-byte call-local stack frame, so neither code
nor transient wrapper state depends on the erased ELF interval.

The canonical resident-only link at load base `0x008F3D00` places the nine
Font fragments in `0x008F3D50..0x008F42A0`. The complete profile then appends
its external-string fragments in the same shared image. Eight guarded boot-ELF
hooks target these symbols:

- ordinary space and newline at file offsets `0x893EC` and `0x88704`;
- normal right-edge, inline-markup half-space, and ordinary glyph advance at
  `0x88070`, `0x88B7C`, and `0x897D8`;
- the Controls wrapper at `0x288848`;
- selected-choice and shared-UI wrappers at `0x279250` and `0x279B20`.

The horizontal-scale fragment has three intentional entrypoints. The normal
right-edge hook targets the fragment start, the inline-markup half-space hook
targets `+0x18`, and ordinary glyph advance targets `+0x2C`. An initial
resident link incorrectly sent all three hooks to the fragment start. Runtime
bisection proved the first two hook families independently safe and isolated
the third as the crash trigger. Restoring addends `0x18` and `0x2C` fixed the
failure; canonical tests decode all three linked jump targets so this mistake
cannot recur.

Historical accepted states contain the old complete payload and cannot safely
receive a newly built whole-profile image at the same address: doing so
overwrites live external strings and unrelated state. For the relocation
regression, a Font-only 1,440-byte test image was linked after the old payload
at runtime `0x008F4500`, and only the eight exact Font hooks were converted.
This preserved every old string address while exercising the new helpers. A
broader state conversion was rejected after proving that nominal ELF file
offset `0x2F79F4` contains mutable live data in a running state and therefore
must not be treated as an immutable boot constant.

All ten matched Font states then loaded and rendered without a guest pause or
crash. The accepted Practice, Controls, character-return, and Collection
layouts were retained. Three apparent capture differences were reproduced by
loading the untouched original states under the same task clone: the blank 2P
Controls label column, the one-line Practice confirmation-body rerender, and
the no-memory-card state advancing to the Japanese safety screen. They are
state-resume behavior, not resident-code regressions.

A fresh canonical worker ISO independently survived entry from a current-build
title state into the real Load menu with the actual integrated `PRG/228.BIN`.
The final isolated ISO has SHA-256
`1390892232BFB3F90F4F069F6CB268271ED553FFE016608652ED989256F05DF5`
and boot CRC `D64F4AC7`; its 2,960-byte resident payload has SHA-256
`3874853A22B597E8B035041BB439EC6AB0F1A53B8808C9A4FC2C9522B11A2693`
and spans runtime `0x008F3D00..0x008F4890`. Five seconds after a recorded
Cross confirmation, the captured Load screen contains all three save rows,
dates, play times, and the instruction panel. PCSX2 reported no TLB miss,
guest crash, or unexpected pause before the recording reached its configured
frame limit. This proves that the replacement code remains resident across the
transition that erased the old ELF cave.

The integrated build record is
`work/Font/logs/builds/20260725_090026_130_pid29660/`; the fresh title state,
Cross recording, and Load capture are under
`work/Font/artifacts/load_freeze/resident_relocation/final_runtime/`. A state
captured after the old hook had already entered erased code cannot be repaired
by applying the new hooks after load; execution must start before that
transition.

The ten converted captures and the untouched-state controls are retained under
`work/Font/artifacts/load_freeze/resident_regression/` for comparison while the
remaining caller families are implemented.


### 2026-07-28 accepted remaining-layout C migration

The remaining v2 behavioral layout implementation can be expressed as ordinary
EE C without changing its canonical payload symbols or guarded game hooks.
The candidate compiles Pause Controls, Quit scope/choice mapping, native
measurement and greedy wrapping, Quit/Special Controls body construction, and
Practice mixed text/icon flow into relocatable runtime-injector fragments.
Native renderer tail calls, live-register entry capture, and the five
displaced-instruction hooks remain small assembly bridges because they encode
game-specific ABIs rather than layout policy.

Manual disassembly established a reusable EE compiler ABI requirement: this
toolchain passes integer arguments five and six in `t0` and `t1`. A first shim
draft incorrectly used caller-stack slots; it was rejected before canonical
generation. The corrected selected-Pause bridge leaves the live color in
`t0`, while the Practice bridge moves its secondary object into `t0` and the
native Y float bits into `t1`.

The accepted implementation contains 49 v2 fragments in 5,924 bytes, SHA-256
`7F021178787EA9A845EED8AE348B731345C3459BF1AF29D48CA02B26E84D5F28`.
The separate 188-byte numeric formatter is unchanged. Static evidence covers
compiler extraction, supported relocations, exact exported-symbol closure,
session/frame offset assertions, bounded buffers, package loading, and the
combined feature hash. The normal build promoted Current CRC `12369AA2`; the
user manually regressed every affected caller family and reported `no diff`.
Only after that explicit acceptance were permanent tests updated. They protect
the relocatable C and native-ABI safety contracts without freezing compiler
hashes or old assembly layouts; focused tests pass 11/11 and the full builder
suite passes 201/201.


## 2026-08-02 Font 3 global layout overhaul

The Font 3 overhaul moves layout ownership from individual visible rows to
structural renderer families in `src/localization/font/font_v2_core.c`. Thin
caller adapters retain each native ABI and container, while the shared session
owns proportional measurement, shrink-only fitting, centered origins,
line-count-aware wrapping, renderer state, and cleanup. No displayed string,
pointer mapping, objective prose, marker, unit, or fallback label is created or
rewritten by this work.

The retained global selected-style dispatcher is the foundation: it keeps the
base/shadow geometry stable and overlays the selected pass instead of applying
NA2's state-dependent replacement movement. Renderer families are bounded
last-mile geometry adapters on top of that fix. They correct the individual
container origins, widths, wrapping, and ABIs that a global draw-state change
cannot infer.

This boundary matters beyond the captured examples. Every row reaching the
same caller family now inherits the same formula, including unseen strings and
characters. Short text stays on its native one-line renderer. Only measured
overflow enters wrapping or shrinking, and selected and ordinary states share
geometry unless the native container has a proven structural footer or modal
state.

This is consistent with the original executables, but it is not a claim that
they contain a literal object named a renderer family. Both NA2 and NUN5 reuse
low-level measurement, font-state, boxed-compositor, and selected-style
routines from multiple callers; screen code supplies the row data, bounds, and
state. The Font 3 layer makes those naturally shared caller groups explicit in
typed C so one proven correction reaches every member without widening the
hook to unrelated consumers.

### Implemented renderer families

- **Controls:** the first eight action labels share one `128`-unit box and one
  raster-phase correction. The vibration row remains on its unrelated native
  caller.
- **Practice Settings:** heading, left labels, compact values, descriptive
  values, and digit-leading values use page-level formulas rather than row
  tables. The explanation path is separate.
- **Battle Settings:** labels and values use Battle-local selected, ordinary,
  and value raster phases. Compact values, numeric values, and `Unlimited`
  retain the shared value container without changing their source text. Battle
  and Practice retain the same structural row model, but their final pixel
  phases are separate because forcing the Practice phase onto Battle produced
  visibly different weight and alignment.
- **Linked Mode:** title Y is `8`; both choices use `45 + 22*i` and one centered
  `1.05` horizontal scale session. Both draw states share placement. The
  selected entry supplies native red `0xFF0000D4` instead of undefined `t0`.
- **Character Select player-mode list:** selected and ordinary rows share one
  bounded metric family. Rows one through four share the normal formula; the
  structurally distinct fifth footer receives one selected-state Y correction.
- **Pause, Special Controls, quit, Character Select confirmation, Collection
  confirmation, and Mode Select confirmation:** each native modal family keeps
  its own container but shares selected/ordinary geometry within that family.
- **Jutsu selector:** all fitting names use one family session at scale `1.0`
  with side-dependent X and one-line Y origins. Only measured overflow enters
  the `186 x 32` two-line compositor and its separate multiline Y/line-step
  geometry, so fitting text is never vertically collapsed.
- **Practice explanations:** one bounded mixed text/icon compositor replaces
  the native per-token loop. One-, two-, and three-line outputs use shared
  line-count Y formulas; native icon callbacks and source strings remain.
- **Command Chart:** the title has one shared X/Y origin correction. Both
  optional relationship fields are composed in a bounded transient buffer and
  drawn once through a `226 x 32` box. Relationship and plain rows select
  structural icon offsets rather than per-row offsets.
- **Collection lists:** the shared ETC list hook classifies narrow Figure move
  rows into the `152`-unit profile and wider relationship/Movie rows into the
  `192`-unit profile. Figure/Music headers share one origin formula and ordinary
  or legacy Ultimate Jutsu headers share another. No character or string
  whitelist is used.
- **Ninja Song arithmetic:** one data-driven renderer reads the native row
  table and covers all fifteen expanded, total-only, and N/A rows.
- **Ninja Song objectives:** one caller hook draws the existing red index,
  existing one-byte marker, and existing prose as independent elements. Prose
  uses one `288`-unit constant for both wrapping and the bounded two-line
  compositor; no text is prefixed or substituted.

### Retired Save confirmation absolute-position fix

The Save confirmation header and choice-position patches are retired. They
copied NUN5-local absolute coordinates into NA2 even though the two games use
different modal dimensions, so those coordinates are not equivalent layout
targets. The two header record edits at ELF files `0x4C0780` and `0x4C0790`,
the initializer hook at `0xE6F8C`, its stack-record adapter, and all supporting
payload declarations are removed. NA2 again owns the modal's native text
positions. The independent global selected-style dispatcher remains active;
no displayed string, color, or Save/Load numeric formatting is changed by this
retirement.

### Runtime and static result

The last captured isolated build used for the main and Collection evidence is
`work/Font 3/build/font-overhaul-final-red.iso`, SHA-256
`39F7EF26AB833559E6AD2EC1905D14599724B259E6066F40085F13DB9F607C09`,
with retained build record
`work/Font 3/logs/builds/20260802_171859_865_pid38392/`. After those captures,
the final source replaced the objective-only `320`-unit wrap threshold with the
same `288`-unit constant used by its render box. That source is not claimed to
be byte-identical to the captured ISO. The latest compose-only result retains
`138` resident symbols, `18,512` payload bytes, and `66` runtime-injector
edits. Deterministic reconstruction reports `104` Font fragments within `108`
compiled/static declarations, and full default-profile composition succeeds
without conflicts.

The synchronized main replay provides valid post-change cases 1-49 under
`work/Font 3/overhaul/comparisons/font-overhaul-final-red-main-1-49-vs-nun5/`.
A severity-first review found no wrong selected color, overflow, bad wrap,
missing label, or large width/position error. Linked `Auto` and `Manual` are red
in both selected captures. The separate Collection replay provides valid cases
1-7 under
`work/Font 3/overhaul/comparisons/font-overhaul-final-red-font2-vs-nun5/`,
covering Sakura Figure, Ultimate Jutsu and Music, Movie rows, and legacy Naruto
Ultimate Jutsu; no large Font defect remains there. Classic Naruto's missing
Figure and Music pages are native content structure, not missing Font output.

The Ninja arithmetic family was runtime-proven in the earlier fresh ss3
injection and redraws continuously after resume. The final six Ninja objective
capture markers are not runtime evidence: that recording desynchronized and
captured Character Select instead. Earlier runs prove older objective
candidates, but their payload differs from the final build. The final objective
implementation therefore remains statically verified until one synchronized
final-build replay is supplied; no stronger claim is retained.

### Preserved regression tooling

Reusable scripts under `scripts/research/localization/` are retained as the
reproducible project surface:

- `replay_font_recording_worker.ps1` runs a recording against the task-owned
  worker and collects marker screenshots without using the shared ISO paths.
- `verify_font_replay_bundle.ps1` and `verify_font_replay_bundle.py` verify the
  copied ISO's boot/resident members, payload hash and size, retained build
  record, symbol map, and required symbol identities before replay.
- `compare_font_capture_sets.ps1` and `compare_font_capture_sets.py` pair exact
  marker IDs and generate full-scale side-by-side images, blends, differences,
  and paged grids.
- `measure_font_capture_regions.ps1` and
  `measure_font_capture_regions.py` measure configured regions without turning
  tiny subpixel differences into automatic defects.
- Controlled isolation uses booleans in a task-selected configuration JSON.
  Its structure must continue to match the catalog exactly; there is no
  separate patch-state script or executable `enabled` field.

Generated ISOs, captures, logs, and comparison products remain task-owned
under `work/Font 3/`; only reusable scripts and canonical findings are tracked.

### Capturing remaining discrepancies

Use two game-specific recordings, one authored for NUN5 and one for NA2, with
the same ordered semantic marker IDs. Never replay one game's `.p2m2` against
the other game. A marker is evidence only when both games are on the same
semantic screen and the text has reached a stable frame; if either replay
diverges, discard that marker and every later marker until synchronization is
re-established. Do not compare a later menu merely because its frame number
happens to match.

Add separate markers for each materially different renderer state: selected
and ordinary rows, shortest and longest available strings, one- and two-line
containers, optional rows, legacy characters with absent sections, and each
distinct modal or page header. Character variation is coverage for one shared
family, not a reason to create character-specific fixes. Place an additional
marker immediately before each risky navigation transition so the first
divergence is localized instead of invalidating an unexplained tail.

The comparison pass should first flag large semantic defects: overflow,
clipping, wrong wrapping, wrong selected color, missing output, or a visibly
wrong origin/width. Only after those are exhausted should exact-scale blends
be used for smaller raster-phase differences. Content differences between
games, animation timing, and absent native sections are recorded but are not
Font defects.

## 2026-07-28 composition-time C cutover

The two accepted Font C units are now compiled during normal
`runtime_injector` package loading. `c_sources.tsv` declares the source and
namespace, `c_imports.tsv` binds its external symbols, and `c_fragments.tsv`
maps extracted object sections to stable payload symbols and global order.
Compiler objects exist only in a temporary directory. Retained native ABI/data
shims are represented directly in `fragments.tsv`; the payload builder links
all normalized fragments into the one final `PRG/228.BIN`.

This is an architecture-only cutover. Comparison against the preceding
canonical package produced the same 57 fragments, the same 6,480-byte
runtime-injector link with SHA-256
`48621B34B8183866BA2D420B7D6691D110825BE090424E7C44B3A305BF9332FF`,
and the same 7,968-byte complete profile payload with SHA-256
`56748DA8F0D3C2BFE3AC689B1899DBF4EA358D5316DC387F562165CCCDB9C99C`;
the linked memory end remains `0x008F5C20`. The removed aggregate blobs were
therefore redundant build intermediates, not runtime resources. Confidence is
high because equality covers compiled section bytes, relocations, fragment
order, and the final linked payload.

### Secondary metric decoder cutover

The accepted fixed-ELF decoder had two observable entry contracts. The draw
entry received the renderer context in `s3`, secondary cell in `v0`, and
native mode flags in `a2`; it selected the indexed empty primary-map value,
decoded four packed metric nibbles, applied the local horizontal factor only
to the horizontal leading bearing, selected top/bottom metrics for the native
vertical mode, stored trailing trim at context `+0x38`, and rejoined cleanup
at runtime `0x001873B4`. The measurement entry received the current byte
through `s2`, converted printable secondary codes to cells `0..122`, returned
the same expanded four-byte metric row, stored it through `s1`, and rejoined
cleanup at `0x00187B68`.

`font_glyph_metrics.c` now implements both contracts in expandable
`PRG/228.BIN`. The compiled lookup entry is 208 bytes and the draw-application
entry is 328 bytes; neither has an external relocation. Boot-ELF file
`0x87374` now contains only a 24-byte register-setup/link/cleanup hook to
`localization.font.glyph_metric_apply`; file `0x87B60` contains the analogous
24-byte hook to `localization.font.glyph_metric_lookup`. Static composition
places the candidate entries at runtime `0x008F3EE8` and `0x008F3DA0`
respectively, but these addresses are payload-builder results rather than
feature-owned constants. The complete candidate payload is 8,512 bytes,
SHA-256
`81DED6B73DAB6B2B72B52FC158FD7F3C9C4A05CE8654EB1A273C81779AAF6E2D`,
ending at runtime `0x008F5E40`.

The atlas, packed map, descriptor, secondary-cell guard, horizontal scale word,
and secondary-only quad-height path remain unchanged. The pre-generated
decoder and measurement blobs are removed. Static confidence is high from
clean-byte guards, bounded disassembly of both native contexts, compiler
instruction review, and resolved-hook inspection. Runtime status remains
`approved_for_test` until the user verifies representative secondary-font
drawing/fitting and an unaffected primary/fullwidth case.

## 2026-08-03 stable heap boundary and screenshot determinism

A 32-byte zero-filled tail fragment proved that the former exact-end payload
reservation made unrelated Font regression captures depend on resident code
size. The normal 18,512-byte payload ended at `0x008F8550` and produced heap
user base `0x008F8570`; the 18,544-byte probe ended at `0x008F8570` and moved
the user base to `0x008F8590`. Captures 10 and 19 changed only on the 3D
character and pedestal. GS local memory and textures were identical, while EE
render packets, transform-matrix floats, and VU1 XYZ/ST results differed.

The Font renderer was not on this causal path. Heap relocation eventually
changed allocator reuse and the matrix inputs written by the game before VU1;
the exact address-sensitive engine dependency remains unnamed. The systematic
fix is instead in `payload_builder`: `228.BIN` retains its real linked
`memory_end`, while all boot-ELF program headers and heap-boundary constants use
stable `reservation_end = 0x00940100`.

The maintained `na228 e2e -s` gate fingerprints independent normal and 32-byte
padded E2E Test builds, prepares and replays them concurrently through the
shared portable PCSX2 installation, and compares raw PNG
hashes without publishing alternate captures. Only normal captures are
published after the complete run passes.
The verified initial focused proof matched all 58 non-ignored `font/main`
screenshots byte for byte. Seven volatile save-data slots remain governed by
the base suite's existing `ignore.txt`. Reusable probe evidence and comparison scripts are under
`work/Font 3/investigation/heap-boundary-tail-probe/` and
`work/Font 3/investigation/stable-boundary-ab/`.
