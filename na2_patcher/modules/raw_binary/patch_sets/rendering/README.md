# Rendering

This ordinary raw-binary patch set is the former PNACH `Rendering` section.
`patches.tsv` contains the cheat and `edits.tsv` contains its subcheat. The
confirmed widescreen cheat remains disabled through `default_enabled=0`.

Its `ee_write` operation records a runtime EE-memory write rather than pretending
that address `0x00AF3694` is a file offset. It is retained only as inactive
reference data and is not emitted into the canonical PNACH or applied to a file.
