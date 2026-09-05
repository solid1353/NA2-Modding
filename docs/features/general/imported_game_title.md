# Imported game title

`general.replace_imported_game_title` replaces the imported NUN5 title
`Naruto Shippuden: Ultimate Ninja 5` with root `settings.title` before the
string patcher decides which strings stay inline and which use linked external
storage. Its catalog definition guards the known six mappings and seven total
occurrences. Setting it to `false` leaves the imported title unchanged. It is
independent of the settings under `features.memory_card`.
