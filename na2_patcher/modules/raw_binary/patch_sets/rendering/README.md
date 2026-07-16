# Rendering

This ordinary raw-binary patch set is the former PNACH `Rendering` section.
`patches.tsv` contains the cheat and `edits.tsv` contains its subcheat. The
confirmed widescreen cheat remains disabled through `default_enabled=0`.

Its `ee_write` operation records a runtime EE-memory write rather than pretending
that address `0x00AF3694` is a file offset. The raw-binary PNACH renderer emits
this subcheat into the canonical PNACH during actualization.
