# Localization

`features.localization` selects one language and its matching components.
English (`"en"`) selects `localization.en`, combining font, numeric formatting,
UI textures and layout, regional input, string replacements, and NUN5 disc
identity. Japanese (`"jp"`) retains the native localization and NA2 disc
identity. Mod-authored text uses the selected language column separately.
Japanese remains experimental; see the [known UI issues](localization/ui_textures.md#known-jp-issues).

Language patches reuse components through `includes` in
`@builder/patches/localization/localization.json`. A future language adds a
literal catalog branch, a translated mod-string column, and a patch combining
shared components with its own strings and texture inputs. Adding a mod-string
column alone does not supply matching fonts or graphical assets.

Component contracts:

- [Translation importer](localization/translation_importer.md): retail string replacements.
- [Mod strings](localization/mod_strings.md): mod-authored text and numeric formatting.
- [Font](localization/font.md): glyph rendering and fitting.
- [UI textures](localization/ui_textures.md): graphical assets and Japanese compatibility.
- [UI integration](localization/ui_layout.md): matching layout and runtime changes.
- [Regional input](localization/regional_input.md): button conventions.
- [Disc identity](disc_identity.md): language-dependent boot identity.

[Release packaging](../runbooks/release.md) includes resources for all available
languages, regardless of the packaged default.
