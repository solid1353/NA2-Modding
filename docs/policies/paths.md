# Path configuration

## Configuration contract

- Workshop owns shared path configuration and source-game identities. NA2
  imports that configuration and defines only project-specific paths and
  settings.
- Workshop must not depend on NA2. NA2 may override an imported entry only by
  defining the same name in its own manifest.
- Roots and files use repository-relative paths or `@root/child` references.
  Resolve each manifest relative to its own directory, never the caller's
  working directory.
- Loaders inject `repository`; manifests do not define it.
- Define parent roots before entries derived from them and keep related entries
  together.
- `existence_deferred_roots` contains only generated roots that may be absent
  while loading the manifest.
- Runtime consumers resolve configured paths through a maintained loader; do
  not hard-code their backing paths.
- Each registered game's alias-owned PCSX2 bundle must exist in exactly one
  configured `pcsx2_files` root.

## Changes and validation

Move canonical content first, then update its manifest name and every consumer
in the same change. Delete retired names and logic without compatibility
handling.

For NA2 path changes, run:

```powershell
& { . .\scripts\lib\paths.ps1; Get-Na2Paths | Out-Null }
& .\scripts\lib\run_python.ps1 `
  -PackageSet builder `
  -Module unittest `
  -NoBytecode `
  -ArgumentList @('discover', '-s', 'tests/na228_builder', '-p', 'test_paths.py')
```

For Workshop path changes, run its affected tests or the full
`tests/run.ps1` suite.
