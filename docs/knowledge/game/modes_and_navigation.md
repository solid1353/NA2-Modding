# Modes and menu navigation

This document is the runtime map of the retail game's in-scope menus: Mode
Select, Free Battle and Practice setup and pause menus, Options, and
Collection. It records what each visited entry and control does, as observed
by navigating the menus with a loaded save. It is not an exhaustive claim
about every unlock state or battle mechanic.

## Research coverage

- **Assigned scope:** map the retail mode and menu structure by navigating the
  in-scope menus at runtime and record what each visited entry and control
  does. General combat-system reverse engineering is outside this document.
- **Exploration depth:** the Mode Select loop was cycled end to end. Practice
  was followed through team selection, its complete 17-row settings view, a
  playable battle, and every pause entry. Free Battle was followed through
  setup and a playable round in both 1P-versus-COM and joined-Player-2 forms,
  including their distinct pause menus. Options was traversed across every
  root entry, and the Difficulty range plus its Reset behavior was tested.
  Collection was traversed through its three roots, Naruto's visible detail
  categories, and the visible Movie and Music lists, but not exhaustively
  across every character or media item.
- **Confirmed coverage:** common menu actions, the in-scope Mode Select
  entries, Free Battle character/team, stage, versus, settings, ready, battle,
  and pause flow, Practice setup, settings, battle, and pause flow, Options
  controller/screen/music/difficulty behavior, and the visible Collection
  structure and Naruto subviews. Every runtime claim is tied to a stable
  post-input frame or visible response.
- **Unresolved or untested:** post-round Free Battle results; alternate
  team/settings combinations; most setting value domains and Defaults actions;
  whether Options Reset affects anything besides Difficulty; complete
  Collection contents and media playback; runtime confirmation of the retail
  button assignments, including the Customize Jutsu button on the Free Battle
  versus screen; the support-selection row and Linked Mode window; Practice's
  initial settings values; and which stages and Collection entries are
  available at specific retail progress states.
- **Deliberate exclusions and overlap:** substitution timing, defender control,
  and incoming-definition evidence belong to
  [Substitution](../gameplay/characters/substitution.md) and are not duplicated here.
  Static menu constructors and command-ID owners remain in `mode_flow.md`,
  `practice_mode.md`, and `pause_and_replay.md`; Character Select states
  belong to `character_select.md`. This document links those owners only where
  they explain a runtime observation. Mode Select entries outside project scope
  are not covered.
- **Evidence limitations:** observations were made by navigating a modified,
  English-localized development image with a loaded memory-card save, not the
  unmodified retail disc, and memory-card writes were discarded. Observations
  that depended on that image's changes were removed; the button assignments
  given here come from static retail evidence in the linked documents. The
  remaining observations assume the image left those screens unchanged, which
  was not verified screen by screen. Labels are the English text that image
  displayed; the retail disc displays Japanese text. Content availability did
  not come from a retail save, so stage and Collection lists show which entries
  exist and their order, not when they become available. Static IDs cited from
  neighboring documents were not independently re-derived here, and menu and
  battle code were not exhaustively inspected.

## Observation conditions

Each observation is a freshly rendered frame after a complete DualShock 2
state was applied for an exact number of frames.

Menu transitions impose an input lock. A button state sent before the next
menu becomes interactive can be ignored even though the transition has
finished visually. Findings below therefore come only from a visible response
or a stable post-input frame.

## Common menu controls

Retail menu handlers accept with Circle and back out with Cross; see
[Mode Select input actions](mode_flow.md#input-actions) and the
[menu-input handler map](../runtime/menu_input/README.md). This document
therefore names those actions Confirm and Back.

| Input | Observed behavior |
| --- | --- |
| D-pad Up/Down | Move between vertical menu entries. Mode Select wraps from the last entry to the first. |
| Confirm | Confirm the highlighted entry or setting. |
| Back | Back on ordinary menus; labelled Cancel on Screen Settings. |
| Start | Save from Mode Select. |
| Select | Restore defaults on Control, Screen, and Music Settings. |
| L1/R1 | Move between pages in the Collection character grid; zoom the model in/out in the Figure viewer. |

## Mode Select

The in-scope entries appear in this physical order:

1. Free Battle
2. Practice
3. Collection
4. Options

Repeated Down presses moved through the entries and wrapped from the last one
back to the first. The footer labels Start as the save action.

| Mode | Observed behavior |
| --- | --- |
| Free Battle | Opens character/team selection, Stage Select, battle setup, and a standard timed round. Both 1P-versus-COM and joined-Player-2 paths were entered. |
| Practice | The visible description presents it as the place to practice basic controls and other techniques. It opens a 1P-versus-COM character selector. |
| Collection | Opens the acquired-content browser described below. |
| Options | Opens difficulty, controller, screen, audio, and reset settings. |

With Practice highlighted, a two-frame Confirm state sent after the return
transition was missed, while an eight-frame Confirm state was accepted. This
establishes a controller-sampling miss rather than an inaccessible Practice
entry.

Resident callback IDs, overlay handoffs, unlock-driven physical-slot
construction, and the complete result table are owned by
[`mode_flow.md`](mode_flow.md#mode-select-result-table). This document owns
only the visible runtime navigation and loaded-state behavior.

## Free Battle setup

Free Battle opens a split character selector similar to Practice, with Player
1 on the left and COM on the right. The right side additionally displays
`Press START button to join in!`. Pressing Start on controller slot 1
changes the right-side role from `COM` to `2P` in place; it does not restart
or leave character select. The footer provides Select Color on L1, Random, OK,
and Back. The retail fighter handler assigns Random to Triangle; see
[Selection state machine](character_select.md#selection-state-machine).

The 1P-versus-COM path uses the same four team selections as Practice: Player
1 main character, Player 1 linked character, COM main character, then COM
linked character. Naruto was initially selected as both main characters.

After both teams are confirmed, Free Battle opens Stage Select. The initial
selection was `Hidden Leaf Village`, numbered `1/24`. The screen is a vertical
stage carousel and advertises Random, OK, and Back.

Confirming the stage opens a `Round 1` versus screen. It shows the complete
teams and a 0-win/0-loss counter for each side. The joined branch labels the
two sides `1P` and `2P`. Square opens Battle Settings; the screen also offers
Customize Jutsu, OK to start the round, and Back.

In 1P-versus-COM, Player 1's confirmation starts the round. In the joined
branch, each controller must confirm independently: Player 1's confirmation
placed a `Battle!` ready marker only on the left, and 1,200 neutral frames did
not advance the screen; Player 2's confirmation then allowed the battle
transition to begin.

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

Select is labelled `Return to Defaults`; Confirm accepts and Back backs out.
No value was changed.

### Customize Jutsu

Customize Jutsu overlays Player 1's two special-move slots on the versus
screen. Naruto's loaded Jutsu 1 was `Naruto Uzumaki Combo Attack`; Jutsu 2 was
`Great Ball Rasengan`. The overlay also displays each slot's
directional-plus-Circle command glyph and horizontal selection arrows. No
selection was changed.

The setup sequence is therefore as follows. In the retail selector, each
linked-character confirmation is followed by a Linked Mode window before that
side is finalized; see
[Selection state machine](character_select.md#selection-state-machine).

```text
Mode Select
  -> 1P main character
  -> 1P linked character
  -> COM main character
  -> COM linked character
  -> Stage Select
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
  -> Stage Select
  -> Round versus screen / both players ready
  -> battle
```

### Free Battle round and pause menu

The observed round loaded Hidden Leaf Village with the standard battle HUD and
a countdown that began at 99. The Normal COM attacked during neutral frame
advance, producing the ordinary hit counter and reducing Player 1's health.

Start opens this six-entry menu in 1P-versus-COM:

| Command ID | Visible entry | Runtime behavior |
| ---: | --- | --- |
| `0` | Controls | Opens Control Settings. |
| `2` or `3` | 1P Commands | Opens Player 1's character-specific move list. |
| `1` | Command Chart | Opens the generic battle-control reference. |
| `6` | Simple Display | Opens the instructional-display On/Off selector. |
| `0xA` | Back to Game Mode Screen | Opens a Yes/No dialog asking to quit Battle and return to Game Mode Select. |
| `0xB` | Back to Character Select | Returns toward Free Battle character selection after confirmation. |

In a joined-Player-2 round, the menu inserts `2P Commands` immediately after
`1P Commands`, producing seven entries while leaving the remaining order
unchanged. This directly confirms the optional command-list entry described by
the static Free Battle constructor in
[`pause_and_replay.md`](../gameplay/session/pause_and_replay.md). The constructor
lists both move-list entries as placeholder `4` and rewrites them to commands
`2` and `3`; see
[Command identities and observed labels](../gameplay/session/pause_and_replay.md#command-identities-and-observed-labels).

The Game Mode exit dialog initially selects `Yes`.

## Practice setup

Practice first opens a split `Select Character` screen with Player 1 on the
left and a COM opponent on the right. Both sides initially selected Naruto in
the observed state. Each side also has a visible Ultimate Jutsu slot. The
footer advertises Select Color on L1, Random, OK, and Back.

The confirmation path then proceeds in this order:

1. Confirm Player 1's main character. The left panel changes to
   `Linked Character`.
2. Finalize Player 1's linked character. The left team displays `Battle!` and
   focus moves to the COM main-character grid.
3. Confirm the COM main character. The right panel changes to its
   `Linked Character` selection.
4. Finalize the COM linked character. A versus confirmation screen shows both
   complete teams.

The versus confirmation screen advertises Square for `Practice Settings`, OK,
and Back.

### Practice Settings runtime view

Square opens a 17-row Practice Settings overlay. With Status at `Stand`, the
static default, rows were presented as follows:

| Section | Row | Runtime presentation |
| --- | --- | --- |
| Player/general | Health | Active |
| Player/general | Chakra | Active |
| Player/general | Linked Attack | Active; this is the Link Gauge control, not the opponent row below |
| Player/general | Ultimate Jutsu | Active |
| Player/general | Linked Mode | Active |
| Player/general | Items | Active |
| Player/general | Commands | Active |
| Player/general | Damage | Active |
| Player/general | Guide Ninja Sound | Active |
| Opponent Settings | Status | Active |
| Opponent Settings | Strength | Dimmed while Status is Stand |
| Opponent Settings | Attack | Active |
| Opponent Settings | Guard | Active |
| Opponent Settings | Move | Active |
| Opponent Settings | Substitution Jutsu | Dimmed while Status is Stand |
| Opponent Settings | Linked Attack | Active |
| Opponent Settings | Extra Hit Counter | Active |

At `Status: Stand`, the UI therefore exposes Attack, Guard, Move, Linked
Attack, and Extra Hit Counter while visibly disabling Strength and
Substitution Jutsu. The row order and availability agree with the static
controller map in
[`practice_mode.md`](../gameplay/modes/practice_mode.md#rows-local-values-and-manager-storage),
which also records each row's values and Defaults.

Select is labelled `Return to Defaults`; Confirm accepts the settings and Back
backs out. No value was changed.

### Entering the Practice battle

Confirm accepted the unchanged settings and returned to the team-versus
screen. Confirming that screen did **not** open a stage selector. It
immediately entered the `Start Battle` transition and loaded a training-field
arena.

The first stable playable frame shows:

- Player 1 Naruto on the left and COM Naruto on the right;
- both health bars full;
- an infinity symbol in place of a round timer;
- the standard character names and bottom item selectors;
- the training field with wooden posts and target dummies in the background.

Thus the Practice path is:

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
[`pause_and_replay.md`](../gameplay/session/pause_and_replay.md) gives this map:

| Command ID | Visible entry | Runtime behavior |
| ---: | --- | --- |
| `0` | Controls | Opens the same two-player Control Settings/remapping screen used by Options. |
| `2` or `3` | 1P Commands | Opens the active Player 1 character's scrollable move notation. For Naruto, the first visible moves were Flying Shadow Rising Attack, Charging Kick, and Clone Jutsu: Head Split. |
| `1` | Command Chart | Opens a generic battle-control reference. It notes that Manual linked attacks require pressing Linked Attack again after the linked move to attack. |
| `6` | Simple Display | Opens an On/Off selector with On initially selected; see [Simple Display selection](../gameplay/session/pause_and_replay.md#simple-display-selection). Its description says it displays the game's special controls. |
| `5` | Practice | Reopens the live 17-row Practice Settings editor. |
| `0xA` | Back to Game Mode Screen | Opens a Yes/No dialog asking to quit Practice and return to Game Mode Select. |
| `0xB` | Back to Character Select | Opens a Yes/No dialog asking to quit Practice and return to Character Select. |

Both exit dialogs initially select `Yes`; Back cancels them.

## Options

The Options root contains:

```text
             Difficulty Settings
       Control Settings   Screen Settings
       Music Settings     Reset
```

Difficulty spans the top of the panel; the other four entries form a
two-by-two directional grid.

### Difficulty

Confirm enters difficulty editing and displays horizontal arrows. Moving Right
and Left in the loaded state established this ordered range:

```text
SIMPLE -> EASY -> NORMAL -> HARD -> INSANE
```

The left arrow is absent at `SIMPLE` and the right arrow is absent at `INSANE`;
additional inputs toward either endpoint did not change the value. A sixth,
Ultimate tier is gated by progress word `0x6A`; see
[Progress gates](content_availability.md#progress-gates).

### Control Settings

The loaded save's mappings were:

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

Player 2 matched the fixed native default, while Player 1 had a
shoulder-permuted assignment. The stored action arrays and their default are
documented in [Save data](save_data.md).

Confirm selects a button or item to change. Select restores the defaults, Back
returns, and Confirm accepts the page.

### Screen Settings

The page shows numeric `X` and `Y` screen-position offsets; both were `0` in
the loaded configuration. The D-pad adjusts position, Select restores the
default, Confirm accepts, and Back is labelled Cancel. No offsets were
changed.

### Music Settings

The page exposes a volume control and an Output Mode selector. Output Mode was
`Stereo`; the alternate label shown by the control is `Mono`. The help text
states that the page changes music, sound-effect, and voice volume. Select
restores defaults, Confirm accepts, and Back returns. No audio setting was
changed.

### Reset

Reset acts immediately, without a confirmation dialog. After deliberately
changing Difficulty from `SIMPLE` to `HARD`, confirming Reset restored the
visible value to `NORMAL`; the help/status line reads
`Difficulty set to default.` This proves the Difficulty reset but does not
establish whether Reset also affects Control, Screen, or Music values.

## Collection

The Collection root has three entries:

1. Characters
2. Movie
3. Music

Confirm opens the highlighted category and Back returns.

### Characters

The character browser is a paged grid. L1 selects the previous page, R1 the
next page, Confirm opens a character, and Back returns. The first visible
page contained 16 entries:

| | | | |
| --- | --- | --- | --- |
| Naruto | Sakura | Sai | Kakashi |
| Neji | Lee | Tenten | Guy |
| Shikamaru | Choji | Ino | Asuma |
| Kiba | Shino | Hinata | Kurenai |

Opening Naruto displayed three categories:

- Figure
- Ultimate Jutsu
- Voice

Figure opens a 3D model viewer. L1 zooms in, R1 zooms out, the left stick moves
the model, the right stick rotates it, and Back returns. Naruto's viewer
also displayed the labels `Right!`, `Shadow Clone Jutsu`, and `Running Wild`.

The visible Naruto Ultimate Jutsu entries were:

- Great Ball Rasengan
- Overflowing Power
- Nine-Tail's Cloak
- Unchanging Relationship

Confirm is labelled `OK` for the highlighted entry and Back returns. The
selected entry was not opened.

The visible Naruto Voice entries were:

- Sadness and Rage
- Naruto's Determination
- Passion
- The Bond Between Us
- Reunion, and then...

Confirm plays the highlighted voice and Back returns.

### Movie

The visible Movie list contained:

1. Reunion Time I
2. Sealing Jutsu: Nine Phantom Dragons
3. People of Endless Darkness
4. Ninja Art: Beast Scroll Replicas
5. Fourth Awakened Mode
6. Reunion Time II
7. Credits

Confirm plays the highlighted movie and Back returns. Playback itself was not
exercised.

### Music

The visible portion of the Music jukebox contained:

1. Hidden Leaf Village
2. Hidden Leaf Gate
3. Five-Seal Barrier Cliff
4. Akatsuki Hideout
5. Foundation's Hideout
6. Tenchi Bridge

Confirm plays the highlighted track and Back returns. This is only the visible
portion of the list; the full track count and playback behavior were not
tested.

## Boundaries of current knowledge

- Free Battle is mapped through playable 1P-versus-COM and joined-Player-2
  Round 1 paths and both pause-menu variants. Post-round results remain
  untested.
- Practice is mapped through its versus confirmation, Practice Settings rows,
  first playable battle frame, and pause menu.
- Only the first visible character page, Naruto's visible detail lists, and the
  visible portions of Movie and Music were recorded. Collection completeness
  depends on save unlocks and was not established.
- No collection media was played and no Free Battle round was completed.
