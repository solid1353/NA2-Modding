# Feature packages

Feature packages define reusable user-facing composition choices independently
of profiles. Each package contains:

- `manifest.tsv`: feature identity, name, and description.
- `selections.tsv`: ordered module selections owned by the feature.

Profiles enable and hash-pin feature packages while separately defining and
hash-pinning the module instances those selections reference. Current
binary-patcher feature packages select groups only. Direct patch selection remains
available for isolated future features without changing the profile format.

Feature hashes cover only `manifest.tsv` and `selections.tsv`; adjacent
documentation and schemas are not executable feature inputs.
