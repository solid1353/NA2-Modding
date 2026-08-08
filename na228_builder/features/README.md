# Feature-owned files

The selectable feature hierarchy and all migrated binary/runtime executable data live in [`../catalog.json`](../catalog.json). Feature directories no longer encode selectable structure or internal engine boundaries.

Feature directories contain only files that cannot live inline in the catalog:

- catalog-referenced assets under `assets/`;
- feature-local TSV inputs for engines not yet migrated, currently translation and texture import;
- no binary-patcher or runtime-injector data directories.

Catalog-only features do not have directories. Documentation lives under
[`../../docs/features/`](../../docs/features/README.md) and is not a builder input.

[`targets.tsv`](targets.tsv) is the one shared verified target registry. Catalog edits and hooks reference its target IDs.

Configurations under [`../configurations/`](../configurations/) mirror the catalog's selectable keys exactly and own all enablement. Internal engine invocation and ordering are derived by the builder and do not appear in either catalog or configurations.
