A “hook” is a small MIPS patch at an instruction the game already executes. It replaces that instruction with a jump or function call into our compiled C code.

The PS2 never runs C directly:

```text
C source → EE MIPS compiler → relocatable code fragments
         → assigned RAM addresses → original game instruction patched with j/jal
```

| | Font | Hot reload |
|---|---|---|
| Code location | Persistent `PRG/228.BIN` payload | Temporary development RAM |
| Address range | Starts at `0x008F3D00` | `0x008F0000–0x008F3D00` |
| Installation | ISO builder | PINE memory writes |
| Lifetime | Loaded whenever the built game starts | Lost when the VM resets/reloads |
| Hook targets | Specific ELF/BTL/ETC rendering calls | Existing Font entries plus visible reload-message hook |

### Font

1. The build compiles the registered files under `src/localization/font/` using the PS2 EE C compiler.

2. The compiler output is split into named fragments such as:

   - `v2_measure`
   - `v2_controls_adapter`
   - `v2_collection_list_entry`

3. The payload builder places all selected fragments inside `PRG/228.BIN`, beginning at `0x008F3D00`, and resolves calls between them.

4. The boot ELF is patched so its constructor passes through a small loader at `0x00607314`. That loader:

   - loads `PRG/228.BIN`;
   - calls its initialization entrypoint;
   - resumes the original game constructor.

5. Catalog `hooks` identify exact game call sites and the payload symbols they should invoke. After final addresses are known, the builder creates actual MIPS `j` or `jal` instructions.

For example, the Controls draw at ELF file offset `0x288848` originally calls the native text renderer. The build replaces it with:

```text
jal v2_controls_adapter
nop
```

The C adapter changes measurement/layout, calls the native renderer as needed, and returns to the original game code.

Some hooks use `j` because the C function replaces a displaced instruction block and continues elsewhere. Others use `jal` because the C function behaves like an ordinary callable function.

### Hot reload

Hot reload does not rebuild the ISO. The watcher:

1. Detects a changed registered C source.
2. Compiles it into EE MIPS.
3. Links it into the reserved development range `0x008F0000–0x008F3D00`.
4. Pauses PCSX2 through PINE.
5. Writes the new code into that range.
6. Redirects the corresponding resident Font entry to the temporary version with:

```text
j temporary_C_entry
nop
```

Existing Font call sites still call their normal resident symbol at `0x008F3D00+`; that symbol immediately jumps to the hot-reloaded copy. This avoids rewriting every Font caller.

The applier then reads the writes back, clears PCSX2’s translated-code cache, and resumes the game.

It also replaces the native no-op call at `0x001085A0` with a call to `project.hot_reload_message`. That function uses the game’s native text renderer at `0x00379040` to display:

```text
HOT RELOAD HH:mm:ss
```

for 300 frames.

So the concise distinction is:

- Font production hooking: C is stored in `228.BIN`; game-file call sites point to it in the patched image.
- Font hot reload: the resident Font entry temporarily jumps to a newer C copy written through PINE.
- Reload message: a separate end-of-frame hook proves the new memory transaction occurred visibly.
