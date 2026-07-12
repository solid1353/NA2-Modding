# NA2 Translation Package Builder v14

Builder-only package. Extract `translation_package_builder/` into the NA2 project root.

The builder creates one `NA2_APPLY__TRANSLATION__<timestamp>.tsv` in the selected output directory. The TSV columns are exactly:

`path\toffset\texpected_hex\treplacement_hex\tsource_text\treplacement_text`

Readable text patches populate `source_text` and `replacement_text`. Binary-only patches leave both fields empty.

The builder does not include or modify `na2.ps1` or any project-level helper scripts.
