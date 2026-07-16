# NA2 Modding review candidate

This archive contains a modified `NA2-Modding-master/` tree for Codex review. No game binaries or source-media files were added or modified.

## Changes

1. **Atomic ISO build/promotion**
   - Builds to `build/Current.iso.building` in the final output directory.
   - Deletes the temporary ISO on caught failure.
   - Preserves the previous `build/Current.iso` until full patching, verification, and log creation succeed.
   - Promotes the verified ISO with same-directory `os.replace()`.

2. **Size preservation enforced by default**
   - Payloads that change an ISO file size now fail before the ISO copy begins.
   - Legacy relocation remains available only with explicit `-AllowSizeChanges` / `--allow-size-changes`.

3. **Profile hash semantics repaired**
   - Enabled modules are hash-enforced; disabled WIP modules no longer block the active build merely because their contents changed.
   - Raw-binary hashes now cover canonical executable inputs only: the five package TSVs plus blobs referenced by `blob_path`.
   - Adjacent READMEs and authoring tools no longer invalidate a profile.
   - Current font/menu-input pins were regenerated with the new canonical hashing rule.

4. **Current-profile intent corrected**
   - `ELF-M008` remains present and runtime-proven but is documented as intentionally disabled WIP.
   - The current profile enables font m01 and translation m03/v33 only.
   - Documentation no longer claims that this profile reproduces the older verified ISO snapshot containing `ELF-M008`.

5. **PNACH actualization hardened**
   - Existing CRC aliases are verified to be symbolic links to the canonical PNACH.
   - Incorrect or dangling aliases are replaced.
   - A real file occupying the required alias path is preserved and causes a hard failure instead of being trusted or overwritten.
   - The final alias is verified after creation/replacement.

6. **Duplicate PNACH actualization removed**
   - Bare `na2` builds with `-SkipActualize` in stage 1.
   - Stage 2 actualizes once for the completed ISO and then launches PCSX2.

7. **Project rules clarified**
   - `.agents/` is explicitly protected as cross-install/Codex handoff infrastructure.
   - `[S]` shortenings are explicitly documented as authorized, traceable fit exceptions.

8. **Tests expanded**
   - Atomic success/failure behavior.
   - Size-change detection.
   - Disabled-module hash behavior.
   - Raw-binary hashes ignore documentation and include referenced blobs.
   - Current enabled profile pins match the tracked inputs.

## Validation performed here

- `python -m unittest discover -s na2_patcher/tests -v`: **17 tests passed**.
- `python -m compileall -q na2_patcher scripts`: passed.
- All three raw-binary patch-set directories loaded successfully with the repository engine.
- `git diff --no-index --check` reported no whitespace errors.

## Not validated here

- PowerShell execution, because PowerShell was unavailable in the container.
- A full 1.9 GB ISO build, because the ignored source media was not included in the uploaded archive.
- Runtime behavior in PCSX2.

## Suggested Codex review

1. Review the changed PowerShell parameter forwarding and PNACH-link logic.
2. Run the Python tests locally.
3. Run bare `na2` and confirm only one PNACH actualization occurs.
4. Confirm the new build excludes `ELF-M008` as intended.
5. Force a build failure after the temporary ISO is created and verify:
   - `build/Current.iso` remains unchanged;
   - `build/Current.iso.building` is removed.
6. Confirm a normal build promotes the temporary ISO and leaves no `.building` file.
7. Review whether disabled modules should require their input path to remain present; their hash is intentionally not enforced.
