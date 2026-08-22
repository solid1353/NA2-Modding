# Localization research tools

`measure_font_capture_regions.ps1` compares selected regions from paired
native-resolution PNG capture sets. It measures red, dark, or light ink,
writes `summary.tsv`, and creates side-by-side crops under `1x/` and
`4x_nearest/`. The Python file is its internal imaging implementation.

Inputs are reference and current directories whose PNG names end in numeric
slot IDs, plus a tab-separated region table. A simple table uses `slot`,
`region`, `left`, `top`, `right`, `bottom`, `mask`, and `notes`; separate
reference/current slots, boxes, and masks are also supported.

```powershell
scripts/research/localization/measure_font_capture_regions.ps1 `
  -ReferenceDirectory work/font/inputs/reference `
  -CurrentDirectory work/font/inputs/current `
  -Regions work/font/inputs/regions.tsv `
  -OutputDirectory work/font/artifacts/measurements
```

The tool supports the measurements recorded under
[`docs/knowledge/localization/font/`](../../../docs/knowledge/localization/font/).
It validates image sizes and crop bounds, but color masks are fixed thresholds;
its output is measurement evidence, not an automatic visual-regression verdict.
