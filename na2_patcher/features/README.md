# Feature packages

Feature packages define reusable declarative capabilities independently of
profiles. Each package contains:

- `manifest.tsv`: feature identity, name, and description.
- one root `README.md`: all feature and module-specific documentation.
- module-named subdirectories: canonical declarative inputs interpreted by the
  reusable engines under `na2_patcher/modules/`.

Profiles enable and hash-pin feature packages while separately defining and
hash-pinning their module instances. A module belongs to the one feature whose
directory contains its input, and the first subdirectory must match the module
engine type. Enabling a feature enables every module input it owns.

Feature hashes cover only `manifest.tsv`. Each active module input is pinned
separately by the profile, so feature-owned declarations remain reproducible
without making documentation executable input.
