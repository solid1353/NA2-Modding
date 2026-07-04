# NA2 BTL Translation Task For ChatGPT

You are translating BTL.BIN text for Naruto Shippuuden: Narutimate Accel 2 (PS2), Japanese to English.

Use `btl_strings_for_chatgpt.tsv` as input. Return the same TSV rows with `proposed_translation` and optional `notes` filled in. Do not change `id`, `file`, `offset_hex`, `old_slot_capacity_bytes`, `source_japanese`, or `previous_release_english`.

## Translation Goal

Retranslate from `source_japanese`. The previous release English is only a reference and may be distorted because it was squeezed into tiny original slots. Prefer natural, clear game UI English over literal translation.

## Style

- Use concise fighting-game/menu/help text.
- Preserve Naruto/game terms consistently: Chakra, Ninjutsu, Ultimate, Support, Substitution, Awakening, Practice, Command.
- Avoid overly long prose. These strings often appear in menus, help bars, battle UI, or tutorials.
- If a line is a help/instruction sentence, make it readable and direct.
- If a line is a label, keep it short.

## Encoding / Text Rules

- Target encoding is CP932 / Shift-JIS.
- Visible translated Latin letters and digits must always be fullwidth: `ＡＢＣ１２３`. This is mandatory; we are extending/relocating BTL specifically to afford fullwidth text.
- ASCII control tags must remain ASCII if used.
- Source ruby tags like `<r漢字|かな>` are annotations for reading Japanese. Usually translate their meaning into plain English; do not blindly copy Japanese ruby tags into English.
- Preserve meaningful control tags such as color tags if they appear and are needed.
- Do not use characters outside CP932.
- Do not invent markup.
- Newlines may be represented as actual line breaks only if clearly needed; otherwise keep one line.

## Binary Context

Do not worry about the old slot byte capacity as a hard limit. We have proven BTL string relocation:

- Runtime base: `0x006B3F00`
- Runtime pointer formula: `runtime = 0x006B3F00 + file_offset`
- BTL pointer patching works.
- Appended BTL heap works when header field `0x10` is expanded.
- Old slot capacity is provided only to show why the previous translation may be abbreviated.

Still keep translations reasonably concise, but do not use halfwidth ASCII for visible English just to save bytes. We will validate CP932 byte length and total appended heap usage later.

## Output Requirements

Return a TSV, not prose.
Fill:

- `proposed_translation`: your best English translation.
- `notes`: blank unless there is uncertainty, a pun/name nuance, or the previous release English seems wrong.

Do not add extra columns.
Do not omit rows.

