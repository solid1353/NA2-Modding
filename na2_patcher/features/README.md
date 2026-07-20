# Feature packages

Feature packages define reusable declarative capabilities independently of
profiles. Each package contains:

- `manifest.tsv`: feature identity, name, and description.
- `selections.tsv`: ordered module selections owned by the feature.
- one root `README.md`: all feature and module-specific documentation.
- module-named subdirectories: canonical declarative inputs interpreted by the
  reusable engines under `na2_patcher/modules/`.

Profiles enable and hash-pin feature packages while separately defining and
hash-pinning the module instances those selections reference. Current
binary-patcher feature packages select groups only. Direct patch selection remains
available for isolated future features without changing the profile format.

Feature hashes cover only `manifest.tsv` and `selections.tsv`. Each active
module input is pinned separately by the profile, so feature-owned declarations
remain reproducible without making documentation executable input.
