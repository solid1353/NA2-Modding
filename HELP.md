# NA2.28

## Launch

### `na228`

Build or reuse base, then launch it.

### `na228 <token> [token]`

Launch one or two games through Workshop.

- Token: `<source>[w] | [b]<config>[w]`
- `b` — Build or reuse before launch
- `w [C path|plan]` — Watch

#### Modes

- `-l <profile> [args]` — Use a configured launch profile

#### Options

Other Workshop launch arguments are accepted; see `ws help`.

#### Available values

- Sources: {{SOURCES}}
- Configurations: {{CONFIGURATIONS}}
- Profiles: {{PROFILES}}

## Build

### `na228 build <config>`

Build or reuse a configuration without launching.

## Unit tests

### `na228 test`

Run unit tests.

## E2E

### `na228 e2e <all|suite [args...] ...>`

Run selected suites.

### `na228 e2e create <all|suite [args...] ...> [-noref]`

Rebuild selected suites with a NUN5 reference by default.

### `na228 e2e delete <all|suite [args...] ...>`

Delete capture history.

### `na228 e2e rename <suite> <new-suite>`

Rename a recording-backed suite and its capture history.

### `na228 e2e commit [-p]`

Commit captures.

#### Suite arguments

Generated suites accept a row or range: `8` or `8-18`.

#### Options

- `-noref` — Do not use a NUN5 reference when creating suites
- `-p` — Preserve capture commits when committing

## Release

### `na228 release [version]`

Publish a GitHub release.

## Help

### `na228 help`

Show this help.
