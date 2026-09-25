# Mod strings

`na228_builder/resources/mod_strings.tsv` owns text added by the mod: settings
labels, help, option names, submenu headings, reset messages, Character Select
labels, startup notices, and save-upgrade dialogs. Its columns are `id`, `en`,
and `jp`. `features.localization` selects the language column. Retail string
replacements remain in the [translation importer](translation_importer.md).
Text drawn into texture images remains with its graphical assets.

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

A future language needs its own column, translations, and catalog language
choice with the matching font and texture components. Adding a column alone
does not supply those graphical components.
