# Legacy Package History

Normal builds now use hash-pinned modules from `na2_patcher/profiles/current/`.
This folder no longer contains active build inputs. The current profile reads
font m01 from its frozen milestone, and prior packages remain available through
Git history after retirement.

- Use unique filenames and never overwrite an older package. When a package has
  a `vNN` version, place it after the `YYYYMMDD_HHMMSS` timestamp.
- Imported archives may be staged here temporarily, but they must be normalized
  into module data and retired after validation rather than becoming build inputs.
- Builder ZIP installation and generated translation TSVs are no longer part of
  normal builds.
- Copy explicitly accepted frozen references to `milestones/packages/`; ordinary
  package history stays here.
