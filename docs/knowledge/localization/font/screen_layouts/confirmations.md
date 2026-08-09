# Confirmation Font layouts

Font-owned layout evidence for Battle, Practice, Mode Select, and Collection confirmation screens. The grouped findings were established on 2026-07-24.

## Battle quit-confirmation ss4 callers

Clean NA2 BTL bytes and the task-owned ss4 state identify two distinct modal
draw calls. The clean BTL file uses `0x006B3F00 + file offset`:

- file `0x1C4048` / runtime `0x00877F48` is
  `800D0E0C00000000`, the native `jal 0x00383600` Yes/No list
  plus NOP;
- file `0x1C407C` / clean runtime `0x00877F7C` is
  `6C090E0C00000000`, the native `jal 0x003825B0` body draw
  plus NOP.

Earlier retained working notes named BTL `0x1C4008`/`0x1C403C` and ELF
`0x283814`/`0x283960`; direct clean-file guards prove those locations are one
displaced block early. Inside `0x00383600`, the exact selected and unselected
calls are instead ELF files `0x283914` and `0x283A60`, guarded by
`54E40D0C00000000` and `88E60D0C00000000`.

The modal object owns its Yes/No widget at `+0x110` and body widget at
`+0x114`. The list descriptor starts at X/Y `50/24`, uses row extra `12`, and
therefore draws its second row at Y `56`. Retained NUN5 measurements map Yes
to `(64.5,31.5)` and No to `(68.5,49)`. Because either row may be selected,
the smallest exact design scopes the complete list call, then adapts the two
shared inner calls only while that scope is active. The active word is saved
and restored, so nested drawing remains safe; both inner adapters are native
tail calls for every other screen.

The body helper builds its native record at X/Y `48/20`. NUN5 evidence retains
Y `12`; the accepted width table measures the Free Battle first line through
`and` as `420`, while adding `return` reaches `483`. A 420-unit, two-line
greedy wrapper therefore selects the observed break without storing an
authored newline in any canonical mapping. The adapter copies at most 255 source bytes to its
own stack, inserts newline bytes only into that draw-time copy, publishes the
v2 session around the native UI draw, and then discards the copy. Confidence
is **high** for offsets, guards, ABIs, isolation, and mapping neutrality.

Fresh post-change pairs cover all four Battle/Practice and Game
Mode/Character Select combinations. Every Current body starts at screenshot
X `101`, while every NUN5 body starts at X `72`; both first lines start at Y
`381`. Because the renderer uses the adapter's X directly inside the same
modal origin, the shared correction changes its local X from `48` to `19` and
leaves Y `12` unchanged. The same evidence exposes a separate dynamic
text-assembly defect: Battle says `Free Battle`, connective text is duplicated,
and the Japanese destination tail remains. String Translation corrected that
independent assembly in `277ecc1` by splitting the mode head, connective,
destination, and terminator; no canonical mapping gained an authored newline.
The user verified the combined fresh-build result across all four
Battle/Practice and Game Mode/Character Select combinations on 2026-07-27.
The shared quit-confirmation layer is therefore **runtime-proven** with high
confidence.


## Mode Select Return to Title confirmation caller

The 2026-07-29 remade ss1 pair isolates a second consumer of the accepted
C-owned Yes/No mapper. NA2 `FUN_00385C00` draws the confirmation sentence
through dedicated body renderer `FUN_003825B0` at boot-ELF file `0x285E68` /
runtime `0x00385D68`, then draws the live choice object `+0xCC` through
`FUN_00383600` at file `0x285E98` / runtime `0x00385D98`. The body call's
clean eight-byte guard is `6C090E0C00000000`; the choice call's is
`800D0E0C00000000`.

The earlier classification of object `+0xD0` as the visible body was wrong.
Live object inspection while the prompt was visible found its list empty.
Tracing forward identified `FUN_003825B0` as the first actual consumer: it
builds a four-word draw record from constants `DAT_005B1810` X `24` and
`DAT_005B1814` Y `16`, then calls native UI draw `FUN_00379A20`. This explains
why changes to the shared unselected-list adapter had no visible effect.

The existing scoped choice hook reuses Yes `(64.5,31.5)` and No
`(68.5,49)`; the user verified that normal-build top-selector result on
2026-07-29. The bounded body hook reuses the native-body C adapter only when
its exact text is `Return to Title Screen?`, selects a 420-by-40 one-line box
at local `(24,12)`, activates the accepted tracking-zero/plain-space state,
and applies no glyph scale. It deliberately leaves the Collection choice
scope inactive. In fresh 1750-by-1313 native screenshots, NUN5 body ink is
X `194..909`, Y `1042..1078`; unpatched NA2 is X `194..933`, Y
`1056..1091`; the runtime-injected result is X `194..909`, Y `1042..1078`.
Pixel counts are 6,049 versus 6,005, consistent with the small retained raster
difference while geometry is exact. The user verified the exact live body
result on 2026-07-31. Confidence is **verified** for the consumer, guard,
coordinates, and runtime geometry.


## Collection exit-confirmation body and choice list

The replacement 2026-07-30 ss7 pair isolates the Collection exit prompt in
clean NA2 `PRG/ETC.BIN` (200,448 bytes, SHA-256
`8FF3C6E1ED5CE2B093B0934C898C40D1CEEA0C20778C49CDA5591AAD02375C74`).
The retained Ghidra export identifies two body-draw paths and one bounded
choice-list path:

- clean address `0x006C6540`, file `0x12680`, calls the ordinary body renderer
  for object `+4`; its eight-byte guard is `6C090E0C00000000`;
- clean address `0x006C6560`, file `0x126A0`, calls the complete choice-list
  renderer for object `+8`; its guard is `800D0E0C00000000`;
- the render-state path repeats the body draw at clean address `0x006C8788`,
  file `0x148C8`, with the same `6C090E0C00000000` native-call guard.

The live ETC overlay includes a `0x40`-byte runtime header, placing the first
owner pair at `0x006C6580`/`0x006C65A0` and the render-state body call at
`0x006C87C8`. Editing only the first body hook left the visible prompt
pixel-identical. Exact live inspection then proved that `0x006C87C8` still
contained the native call; redirecting that second consumer through the same
C adapter moved the visible body immediately. Canonical edits therefore keep
both guarded body calls.

Normalized 640-by-480 captures measure Current's body ink at Y `386..401`
versus NUN5 `381..396`, with the same X origin. Current's selected Yes is at
X `282..317`, Y `123..136`, versus NUN5 X `299..336`, Y `131..144`;
Current's No is at X `284..306`, Y `166..178`, versus NUN5 X `306..334`,
Y `156..168`. Draw telemetry identifies the native Collection inputs as Yes
text `0x00604570` at local `(50,24)` and No text `0x00604568` at local
`(50,56)`. Their Y values are exactly the source keys already handled by the
accepted scoped mapper, whose retained targets are Yes `(64.5,31.5)` and No
`(68.5,49)`. Collection therefore needs no new choice formula.

The bounded implementation routes both body calls through one C adapter using
the native UI-draw ABI, local origin `(24.8,12)`, native horizontal scale, a
400-by-60 box, 20-unit line height, and a two-line limit. It preserves the
literal separator between differently colored words. The choice call scopes
the existing mapper with Collection-local Yes `(64.2,29.85)` and No
`(68.1,48.2)` targets. Every other ETC body/list caller and ordinary Yes/No
list remains native.

At the final 1769-by-1327 live-edit capture, scaled NUN5 black ink targets
X `196..680`, Y `1054..1096`; NA2.28 matches those bounds exactly. Scaled NUN5
red ink targets approximately X `350..649`, Y `1052..1090`; NA2.28 measures
X `350..648`, Y `1053..1089`. The user verified the exact live result on
2026-07-31. Status is **runtime-proven** with verified confidence.
