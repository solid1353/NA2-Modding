# Music override

NA228 uses existing music from `SOUND.AFS/000`: Mode Select selects track 62,
and Character Select selects track 68. The build does not copy, replace, or
rebuild any audio archive.

The resident audio-command dispatcher has separate entries for Mode Select and
Character Select. Each entry passes its configured track to one shared injected
selector. The selector preserves the native behavior: it leaves an already
active matching track alone, otherwise stops channel 0 before selecting the new
track through the native streamed-audio functions. Track 68 has no ADX loop
block. While Character Select remains active, its native update call is wrapped
to inspect the streamed-audio state. The audio engine enters state 5 only after
the final buffered samples drain; the wrapper then restarts track 68 through
the ordinary stop/select sequence. The selection and every restart set BGM
channel 0 to native gain `-40`. That gain is scaled from the user's global
volume through the native formula, so it neither replaces nor bypasses the
Options volume.

The selection call replacements are at boot-ELF file offsets `0xD38D8` and
`0xD395C`; their adjacent guarded immediate replacements supply track IDs 62
and 68. The Character Select update replacement at `0xED73C` owns the end-of-
track restart. Other tracks retain their native playback and gain behavior. The
`features.general.music_override` catalog setting selects the patch and is
enabled in the base configuration.

Native selector evidence is maintained in
[Audio and video replacement](../knowledge/game/files/audio_video_replacement.md#resident-menu-music-selection).
