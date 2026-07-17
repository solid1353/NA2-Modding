# Archived scripts

Files here are unsupported, reference-only implementations retained for possible
future research. They are not part of the normal project workflow.

`replace_iso_file_same_size.ps1` directly modifies an ISO without profile hashes,
declarative patch records, or build verification. Do not execute it without an
explicit task-specific review and user approval. Normal ISO changes belong in a
hash-pinned `na2_patcher` module.
