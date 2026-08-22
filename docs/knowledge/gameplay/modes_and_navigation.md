# NA228 Modes and Menu Navigation

This document records the menu structure and visible behavior established by
directly navigating the current NA228 development image on 2026-08-20. It is a
state-specific map of the loaded save and build, not an exhaustive claim about
every retail unlock or battle mechanic.

## Research coverage

- **Assigned scope:** establish the visible NA228 mode/menu map by directly
  navigating the verified development image, document what each exposed entry
  and control does, and exercise PCSX2's deployed deterministic controller-step
  path while doing so. This task owns runtime navigation evidence, not general
  combat-system reverse engineering.
- **Exploration depth:** the four-entry Mode Select loop was cycled end
  to end. Practice was followed through default team selection, its complete
  loaded 17-row settings view, a playable battle, and every pause entry. Free
  Battle was followed through setup and a playable round in both 1P-versus-COM
  and joined-Player-2 forms, including their distinct pause menus. Options was
  traversed across every root entry, and the complete five-value Difficulty
  range plus its Reset behavior was tested. Collection was traversed through
  its three roots, Naruto's visible detail categories, and the loaded Movie and
  Music lists, but not exhaustively across every character or media item.
- **Confirmed coverage:** the document records common menu inputs, save-state
  presentation, the four visible top-level modes, Free Battle character/team,
  stage, versus, settings, ready, battle, and pause flow, Practice setup,
  settings, battle, and pause flow, Options controller/screen/music/difficulty
  behavior, and the visible Collection structure and Naruto subviews. Every
  runtime claim is tied to a stable post-input frame or visible response from
  the cited evidence set.
- **Unresolved or untested:** post-round Free Battle results; the full
  24-stage roster; alternate team/settings combinations; most setting value
  domains and Defaults actions; whether Options Reset affects anything besides
  Difficulty; and complete unlock-dependent Collection contents and media
  playback.
- **Deliberate exclusions and overlap:** substitution timing, defender control,
  and incoming-definition telemetry belong to the separate Substitution task
  and are not duplicated here. Static menu constructors and command-ID owners
  remain in `mode_flow.md`, `practice_mode.md`, and `pause_and_replay.md`; this
  document links those owners only where they explain a runtime observation.
  PCSX2 protocol implementation and audit work remained with the PCSX2 task;
  no emulator source change was requested from this task.
- **Evidence limitations:** results are specific to one verified NA228 dev ISO, the
  supplied PNACH, and the loaded memory-card state, with card writes discarded.
  Unlock-dependent absence is not proof that content cannot exist. Static IDs
  cited from neighboring canonical documents were not independently
  re-derived here, and this task performed no exhaustive source/decompilation
  pass over menu or battle code.

## Observation scope and provenance

- ISO:
  `@cache/isos/3A56428FA33E28F627941875ACC4E8097D292464A04DE3FF6A1868CF2CEC2170.iso`,
  SHA-256
  `3A56428FA33E28F627941875ACC4E8097D292464A04DE3FF6A1868CF2CEC2170`.
- Build record: `@logs/na228/builds/20260818_093258_855_pid23636` using the
  `dev` configuration.
- Runtime identity: boot ELF `SLOP_NA2.28`, serial `SLOP-NA228`, CRC
  `19DCC5DA`.
- PCSX2:
  `@pcsx2_dev/pcsx2-qtx64-avx2-dev.exe`, embedded version
  `v2.7.505-42-gf351798d9`, full commit
  `f351798d9f28b5b425231d8edaef09f3109eecf6`, SHA-256
  `6E11A60CAE7555B9015E6B834089B3118410B366B13CDC8783FB2F8CD37BB8DC`.
- Runtime inputs: `@pcsx2_files/games/NA228/NA228.pnach` and
  `@pcsx2_files/games/NA228/NA228.ps2`. PCSX2 used read-only settings and
  discarded memory-card writes.
- Interaction used PCSX2's PINE controller-agent commands to apply complete
  DualShock 2 states and advance an exact number of frames while the VM was
  paused. Every cited screenshot was requested through PCSX2 and rendered by
  advancing a fresh frame.
- The deployed step command installs controller states before frame advance,
  reapplies them after each host-input poll, and validates the exact unsigned
  frame-count delta. This run used bounded steps. Each CLI command opened a
  fresh socket and closed it on completion, triggering controller-override
  cleanup after every command.
- Curated screenshots are retained in
  `@work/Document NA228 game functionality/evidence/`. The stable PINE client
  used for the run is retained in the adjacent `inputs/` directory.

Menu transitions impose an input lock. A button state sent before the next
menu becomes interactive can be ignored even though the transition has
finished visually. Findings below therefore come only from a visible response
or a stable post-input screenshot.

## Common menu controls

| Input | Observed behavior |
| --- | --- |
| D-pad Up/Down | Move between vertical menu entries. Mode Select wraps from the last entry to the first. |
| Cross | Confirm the highlighted entry or setting. |
| Triangle | Back on ordinary menus; Cancel on Screen Settings. |
| Start | Save from Mode Select. The loaded save information remains visible on that screen. |
| Select | Restore defaults on Control, Screen, and Music Settings. |
| L1/R1 | Move between pages in the Collection character grid; zoom the model in/out in the Figure viewer. |

## Mode Select

The loaded state exposed exactly four top-level entries in this cyclic order:

1. Free Battle
2. Practice
3. Collection
4. Options

Six consecutive Down presses established both the order and wraparound. The
initial screen and cycle are preserved as `000_initial.png` through
`006_mode_down_6.png`.

The initial panel reported `Save data loaded`, Play Time `0:00:59`, and saved
timestamp `11/08/2026 19:34`. The footer labels Start as the save action.

| Mode | Behavior established in this run |
| --- | --- |
| Free Battle | Opens character/team selection, a 24-stage selector, battle setup, and a standard timed round. Both 1P-versus-COM and joined-Player-2 paths were entered. |
| Practice | The visible description presents it as the place to practice basic controls and other techniques. It opens a 1P-versus-COM character selector. |
| Collection | Opens the acquired-content browser described below. |
| Options | Opens difficulty, controller, screen, audio, and reset settings. |

The selected Practice checkpoint is `041_practice_selected.png`. A two-frame
Cross state sent after the return transition was missed, while an eight-frame
Cross state was accepted. This establishes a controller-sampling miss rather
than an inaccessible Practice entry.

Resident callback IDs, overlay handoffs, and unlock-driven physical-slot
construction are owned by [`mode_flow.md`](../game/mode_flow.md). This document
owns only the visible runtime navigation and loaded-state behavior.

## Free Battle setup

Free Battle opens a split character selector similar to Practice, with Player
1 on the left and COM on the right. The right side additionally displays
`Press START button to join in!`. Pressing Start on controller slot 1 changes
the right-side role from `COM` to `2P` in place; it does not restart or leave
character select. The initial footer again provides L1 Select Color, Circle
Random, Cross OK, and Triangle Back. Evidence: `070_free_battle_entry.png` and
`084_free_battle_p2_joined.png`.

The default 1P-versus-COM path uses the same four team selections as Practice:
Player 1 main character, Player 1 linked character, COM main character, then
COM linked character. Naruto and linked Sakura were initially selected for
both teams (`071_free_battle_linked_character.png`).

After both teams are confirmed, Free Battle opens Stage Select. The initial
selection was `Hidden Leaf Village`, numbered `1/24`. The screen is a vertical
stage carousel and advertises Circle Random, Cross OK, and Triangle Back.
Evidence: `072_free_battle_vs_confirm.png`.

Confirming the stage opens a `Round 1` versus screen. It shows the complete
teams and a 0-win/0-loss counter for each side. The joined branch labels the
two sides `1P` and `2P` (`086_free_battle_two_player_versus.png`). Its controls
are:

| Input | Versus-screen action |
| --- | --- |
| Square | Battle Settings |
| Circle | Customize Jutsu |
| Cross | OK / start the round |
| Triangle | Back |

Evidence: `073_free_battle_after_stage.png`.

In 1P-versus-COM, Player 1's Cross starts the round. In the joined branch,
each controller must confirm independently: P1 Cross placed a `Battle!` ready
marker only on the left, and 1,200 neutral frames did not advance the screen;
P2 Cross then allowed the battle transition to begin. Evidence:
`087_free_battle_p1_ready_waiting_for_p2.png`.

### Battle Settings

The loaded Battle Settings values were:

| Row | Loaded value |
| --- | --- |
| Time | 99 |
| Difficulty | Normal |
| Items | Normal |
| Chakra | Normal |
| Ultimate Jutsu | Command |
| Handicap | Balanced: five markers on each side |

Select is labelled `Return to Defaults`, Cross accepts, and Triangle backs
out. No value was changed. Evidence: `074_free_battle_settings.png`.

### Customize Jutsu

Customize Jutsu overlays Player 1's two special-move slots on the versus
screen. Naruto's loaded Jutsu 1 was `Naruto Uzumaki Combo Attack`; Jutsu 2 was
`Great Ball Rasengan`. The overlay also displays each slot's
directional-plus-Circle command glyph and horizontal selection arrows. No
selection was changed. Evidence: `075_free_battle_customize_jutsu.png`.

The observed setup sequence is therefore:

```text
Mode Select
  -> 1P main character
  -> 1P linked character
  -> COM main character
  -> COM linked character
  -> Stage Select (24 stages)
  -> Round versus screen / optional Battle Settings and Customize Jutsu
  -> battle
```

The joined branch confirms both main characters together, then both linked
characters together, before the same Stage Select. Its versus screen waits for
both players' independent ready confirmations:

```text
Mode Select
  -> joined 1P/2P main-character selection
  -> joined 1P/2P linked-character selection
  -> Stage Select (24 stages)
  -> Round versus screen / both players ready
  -> battle
```

Evidence: `084_free_battle_p2_joined.png`,
`085_free_battle_two_player_linked_select.png`, and
`088_free_battle_two_player_battle.png`.

### Free Battle round and pause menu

The observed round loaded Hidden Leaf Village with full standard HUD and a
countdown that began at 99. The Normal COM attacked during neutral frame
advance, producing the ordinary hit counter and reducing Player 1's health.
Evidence: `076_free_battle_first_stable.png`.

Start opens this six-entry menu in 1P-versus-COM:

| Command ID | Visible entry | Runtime behavior |
| ---: | --- | --- |
| `0` | Controls | Opens Control Settings. |
| `4` | 1P Commands | Opens Player 1's character-specific move list. |
| `1` | Command Chart | Opens the generic battle-control reference. |
| `6` | Simple Display | Opens the instructional-display On/Off selector. |
| `0xA` | Back to Game Mode Screen | Opens a Yes/No dialog asking to quit Battle and return to Game Mode Select. |
| `0xB` | Back to Character Select | Returns toward Free Battle character selection after confirmation. |

In a joined-Player-2 round, the menu inserts `2P Commands` immediately after
`1P Commands`, producing seven entries while leaving the remaining order
unchanged. This directly confirms the optional command-list entry described by
the static Free Battle constructor in
[`pause_and_replay.md`](pause_and_replay.md). Evidence:
`089_free_battle_two_player_pause.png`.

The Game Mode exit dialog initially selects `Yes`. Evidence:
`077_free_battle_pause_menu.png` and
`078_free_battle_game_mode_confirm.png`.

## Practice setup

Practice first opens a split `Select Character` screen with Player 1 on the
left and a COM opponent on the right. Both sides initially selected Naruto in
the observed loaded state. Each side also has a visible Ultimate Jutsu slot.
The footer advertises these controls:

| Input | Character-select action |
| --- | --- |
| L1 | Select Color |
| Circle | Random |
| Cross | OK |
| Triangle | Back |

Evidence: `042_practice_confirm_retry.png`.

The default confirmation path then proceeds in this order:

1. Confirm Player 1's main character. The left panel changes to
   `Linked Character`; Sakura is initially selected. The visible row contains
   a leaf-symbol tile followed by Sakura, Sai, and Gaara
   (`043_practice_after_first_confirm.png`). The semantic meaning of the
   leaf-symbol tile was not tested.
2. Confirm Player 1's linked character. The left team displays `Battle!` and
   focus moves to the COM main-character grid
   (`044_practice_after_linked_confirm.png`).
3. Confirm the COM main character. The right panel changes to the same linked
   character row, again with Sakura initially selected
   (`045_practice_com_linked_select.png`).
4. Confirm the COM linked character. A versus confirmation screen shows both
   complete teams. The observed default matchup was Naruto with linked Sakura
   against COM Naruto with linked Sakura
   (`046_practice_after_com_linked.png`).

The versus confirmation screen advertises Square for `Practice Settings`,
Cross for `OK`, and Triangle for `Back`.

### Practice Settings runtime view

Square opens a 17-row Practice Settings overlay. The values below are the
loaded values observed during this run, not a claim about the Defaults action
or every possible value:

| Section | Row | Loaded value | Runtime presentation |
| --- | --- | --- | --- |
| Player/general | Health | Normal | Active |
| Player/general | Chakra | Normal | Active |
| Player/general | Linked Attack | Normal | Active; this is the Link Gauge control, not the opponent row below |
| Player/general | Ultimate Jutsu | Command | Active |
| Player/general | Linked Mode | Manual | Active |
| Player/general | Items | Normal | Active |
| Player/general | Commands | Off | Active |
| Player/general | Damage | On | Active |
| Player/general | Guide Ninja Sound | Off | Active |
| Opponent Settings | Status | Stand | Active |
| Opponent Settings | Strength | Normal | Dimmed while Status is Stand |
| Opponent Settings | Attack | No | Active |
| Opponent Settings | Guard | No | Active |
| Opponent Settings | Move | Stay | Active |
| Opponent Settings | Substitution Jutsu | Normal | Dimmed while Status is Stand |
| Opponent Settings | Linked Attack | Don't use | Active |
| Opponent Settings | Extra Hit Counter | Normal | Active |

At `Status: Stand`, the UI therefore exposes Attack, Guard, Move, Linked
Attack, and Extra Hit Counter while visibly disabling Strength and
Substitution Jutsu. The row availability agrees with the static controller map
in [`practice_mode.md`](practice_mode.md), while the values above add the
runtime state of this loaded save.

Comparing that static Defaults action with the loaded runtime state identifies
four visible non-defaults: Linked Mode is `Manual` rather than `Auto`, Commands
is `Off` rather than `On`, Guide Ninja Sound is `Off` rather than `On`, and the
opponent Linked Attack is `Don't use` rather than `Normal`. The Defaults action
itself was not invoked.

Select is labelled `Return to Defaults`, Cross accepts the settings, and
Triangle backs out. No value was changed during this pass. Evidence:
`047_practice_settings.png` through `050_practice_settings_bottom.png`.

### Entering the Practice battle

Cross accepted the unchanged settings and returned to the team-versus screen
(`051_practice_settings_accepted.png`). Confirming that screen did **not** open
a stage selector. It immediately entered the `Start Battle` transition
(`052_practice_post_match_confirm.png`) and loaded a training-field arena.

The first stable playable frame (`053_practice_battle_first_stable.png`) shows:

- Player 1 Naruto on the left and COM Naruto on the right;
- both health bars full;
- an infinity symbol in place of a round timer;
- the standard character names, gauges, linked-character indicators, and
  bottom item selectors;
- the training field with wooden posts and target dummies in the background.

Thus the default Practice path is:

```text
Mode Select
  -> 1P main character
  -> 1P linked character
  -> COM main character
  -> COM linked character
  -> team-versus confirmation / optional Practice Settings
  -> Start Battle transition
  -> training-field battle (no stage-choice screen observed)
```

### Practice pause menu

Start opens a seven-entry pause menu. Joining the visible order to the
Practice command-ID sequence established statically in
[`pause_and_replay.md`](pause_and_replay.md) gives this map:

| Command ID | Visible entry | Runtime behavior |
| ---: | --- | --- |
| `0` | Controls | Opens the same two-player Control Settings/remapping screen used by Options. |
| `4` | 1P Commands | Opens the active Player 1 character's scrollable move notation. For Naruto, the first visible moves were Flying Shadow Rising Attack, Charging Kick, and Clone Jutsu: Head Split. |
| `1` | Command Chart | Opens a generic battle-control reference. The first visible page shows Guard as L1 or R1, Linked Attack as R2, and Item Select as L2. It notes that Manual linked attacks require pressing R2 again after the linked move to attack. |
| `6` | Simple Display | Opens an On/Off selector, loaded `ON`. Its description says it displays the game's special controls. |
| `9` | Practice | Reopens the live 17-row Practice Settings editor. |
| `7` | Back to Game Mode Screen | Opens a Yes/No dialog asking to quit Practice and return to Game Mode Select. |
| `0xE` | Back to Character Select | Opens a Yes/No dialog asking to quit Practice and return to Character Select. |

Both exit dialogs initially select `Yes`; Triangle cancels them. Evidence:
`054_practice_pause_menu.png` through
`061_practice_pause_character_select_confirm.png`.

## Options

The stable Options root (`012_options_after_300.png`) contains:

```text
             Difficulty Settings
       Control Settings   Screen Settings
       Music Settings     Reset
```

Difficulty spans the top of the panel; the other four entries form a
two-by-two directional grid.

### Difficulty

Cross enters difficulty editing and displays horizontal arrows. Moving Right
and Left established the complete ordered domain:

```text
SIMPLE -> EASY -> NORMAL -> HARD -> INSANE
```

The left arrow is absent at `SIMPLE` and the right arrow is absent at `INSANE`;
additional inputs toward either endpoint did not change the value. Evidence:
`014_difficulty_hard.png`, `015_difficulty_insane.png`,
`081_options_difficulty_easy.png`, and `082_options_difficulty_min.png`.

Evidence: `014_options_difficulty_open.png`,
`015_options_difficulty_next.png`, and
`016_options_difficulty_cycle.png`.

### Control Settings

The mappings shown in `020_control_settings.png` are:

| Action | Player 1 | Player 2 |
| --- | --- | --- |
| Attack | Circle | Circle |
| Ultimate Jutsu Prep | Triangle | Triangle |
| Item Use | Square | Square |
| Jump | Cross | Cross |
| Guard | L1 and R1 | L2 and R2 |
| Item Select | L2 | L1 |
| Linked Attack | R2 | R1 |
| Vibration | On | On |

Cross selects a button or item to change. Select restores the defaults,
Triangle returns, and Cross accepts the page.

### Screen Settings

The page shows numeric `X` and `Y` screen-position offsets; both were `0` in
the loaded configuration. The D-pad adjusts position, Select restores the
default, Cross accepts, and Triangle cancels. No offsets were changed during
this run. Evidence: `022_screen_settings.png`.

### Music Settings

The page exposes a volume control and an Output Mode selector. Output Mode was
`Stereo`; the alternate label shown by the control is `Mono`. The help text
states that the page changes music, sound-effect, and voice volume. Select
restores defaults, Cross accepts, and Triangle returns. No audio setting was
changed. Evidence: `024_music_settings.png`.

### Reset

Reset acts immediately, without a confirmation dialog. After deliberately
changing Difficulty from `SIMPLE` to `HARD`, pressing Cross on Reset restored
the visible value to `NORMAL`; the help/status line reads
`Difficulty set to default.` This proves the Difficulty reset but does not
establish whether Reset also affects Control, Screen, or Music values. Evidence:
`083_options_reset_from_hard.png` (with the earlier, non-conclusive baseline in
`025_options_reset_prompt.png`).

## Collection

The Collection root (`031_collection_after_chunk.png`) has three entries:

1. Characters
2. Movie
3. Music

Cross opens the highlighted category and Triangle returns.

### Characters

The character browser is a paged grid. L1 selects the previous page, R1 the
next page, Cross opens a character, and Triangle returns. The first visible
page (`032_collection_characters.png`) contained 16 entries:

| | | | |
| --- | --- | --- | --- |
| Naruto | Sakura | Sai | Kakashi |
| Neji | Lee | Tenten | Guy |
| Shikamaru | Choji | Ino | Asuma |
| Kiba | Shino | Hinata | Kurenai |

Opening Naruto displayed three categories
(`033_collection_character_detail.png`):

- Figure
- Ultimate Jutsu
- Voice

Figure opens a 3D model viewer. L1 zooms in, R1 zooms out, the left stick moves
the model, the right stick rotates it, and Triangle returns. Naruto's viewer
also displayed the labels `Right!`, `Shadow Clone Jutsu`, and `Running Wild`.
Evidence: `034_collection_figure_viewer.png`.

The visible Naruto Ultimate Jutsu entries were:

- Great Ball Rasengan
- Overflowing Power
- Nine-Tail's Cloak
- Unchanging Relationship

Cross is labelled `OK` for the highlighted entry and Triangle returns. The
selected entry was not opened in this run. Evidence:
`035_collection_ultimate_jutsu.png`.

The visible Naruto Voice entries were:

- Sadness and Rage
- Naruto's Determination
- Passion
- The Bond Between Us
- Reunion, and then...

Cross plays the highlighted voice and Triangle returns. Evidence:
`036_collection_voice.png`.

### Movie

The visible Movie list (`037_collection_movie.png`) contained:

1. Reunion Time I
2. Sealing Jutsu: Nine Phantom Dragons
3. People of Endless Darkness
4. Ninja Art: Beast Scroll Replicas
5. Fourth Awakened Mode
6. Reunion Time II
7. Credits

Cross plays the highlighted movie and Triangle returns. Playback itself was
not exercised.

### Music

The visible portion of the Music jukebox (`038_collection_music.png`)
contained:

1. Hidden Leaf Village
2. Hidden Leaf Gate
3. Five-Seal Barrier Cliff
4. Akatsuki Hideout
5. Foundation's Hideout
6. Tenchi Bridge

Cross plays the highlighted track and Triangle returns. This is only the
visible portion of the list; the full track count and playback behavior were
not tested.

## Boundaries of current knowledge

- Free Battle is mapped through playable 1P-versus-COM and joined-Player-2
  Round 1 paths and both pause-menu variants. Post-round results remain
  untested.
- Practice is mapped through its default-team versus confirmation, loaded
  Practice Settings, first playable battle frame, and pause menu.
- Only the first visible character page, Naruto's visible detail lists, and the
  visible portions of Movie and Music were recorded. Collection completeness
  depends on save unlocks and was not established.
- No collection media was played and no Free Battle round was completed.
- Several screenshots in the evidence directory intentionally preserve white
  or partially faded transition frames. They demonstrate the transition/input
  timing issue but are not menu-state evidence.
