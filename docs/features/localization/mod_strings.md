# Mod strings

`na228_builder/resources/mod_strings.tsv` owns all text written for the mod:
settings labels, help, option names, submenu headings, reset messages,
Character Select labels, startup notices, the save settings reset notice, and
rewrites of retail strings. Its columns are `id`, `en`, and `jp`.
`features.localization` selects the language column. Official donor
translations remain in the [translation importer](translation_importer.md).
Text drawn into texture images remains with its graphical assets.

A [translation mapping](translation_importer.md) row with a `mod_string` ID
hands its retail string to that mod string in every language. The builder
guards the retail text, finds its pointer words from `reference_refs` or by
scanning the clean binaries for aligned pointers, and redirects each one to the
mod string; the importer skips the row. In these strings, `\n` separates the
retail message parts and the `{title}` field inserts the product title.

Python consumers use `message(id, **arguments)`. Named placeholders allow a
translation to reorder values and include translated labels in a complete
sentence. Native templates use `{0}` for one formatted value and literal `\n`
for the native dialog's separate lines. The builder encodes `{0}` as a control
byte before embedding it; the bounded native formatter inserts the value and
converts line breaks to NUL separators.

`patches/localization/mod_strings.py` resolves Python text and supplies only
native strings referenced by selected payloads or hooks. Native symbol names
start with `mod_text_`, with each dot in the ID represented by two underscores.
English uses CP1252; Japanese uses CP932. Missing IDs, missing selected-language
text, and mismatched Python template arguments fail composition. Payload
resource declarations include the table in build fingerprints and release
packages. No runtime language table or language switch is installed.

Mod-owned numeric text uses fullwidth digits and numeric punctuation in
Japanese. Python encoding covers menu values and numbers in translated text
while preserving renderer tags. Native templates use the same character
mapping for inserted numbers, dates, times, and percentages. The builder embeds
the selected language's number glyph map and handicap pairs only when a payload
references them. English keeps its existing numeric characters. Native output
buffers allow for Japanese's two-byte characters.

Character Select measures non-ASCII custom support names through the native
renderer before applying its existing text box. Japanese menu help uses the
native help setter. English retains the selected English font layout.

See [Localization](../localization.md) for adding a language and its matching
components.
