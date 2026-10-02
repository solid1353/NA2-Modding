# Survival controller, courses, and rankings

This document records the retail NA2 (`SLPS-25837`) Survival battle
controller: its two controller modes, the 25 finite courses, how results enter
the saved time and win rankings, how Records displays them, and the finite
course result path that produces the Ultimate difficulty unlock. The resident
controller identifies itself with Shift-JIS literal `サバイバル戦闘`
(Survival Battle) at `0x00404AF0`.

## Research coverage

- **Assigned scope:** Survival controller construction and modes 4/5, the
  BTL course table, ranking insertion and display, Records navigation, the
  win-ranking row selector, and the finite-course result controller that
  writes difficulty progress word `0x6A`.
- **Exploration depth:**
  - The complete 25-entry BTL course table and its name strings, the
    controller row setter, both ranking renderers and the Records selector
    bounds were decoded.
  - Controller construction, ordinary battle update, continuation, result
    handoff and Records navigation were followed for row-index preservation;
    the resident, BTL and ETC programs were searched for direct calls to the
    row setter.
  - The finite-course result wrapper, its course controller descriptor, its
    state-0 confirm handler, the `0x6A` producer and its immediate caller,
    course and group admission helpers, the state-6 final-result text and the
    event-5 sound request were read, with instruction bytes covering split
    function bodies.
- **Confirmed coverage:** Mode 5 is the finite course path and fills the
  25-row cumulative-time ranking; mode 4 is the randomized win-streak path and
  uses win-ranking row 0. All 25 course names, groups, battle counts and
  counter increments are established. Records exposes all 25 time rows and
  only win row 0. Acknowledging an eligible result for course index 24 writes
  word `0x6A = 1`, and the state-6 text announces the Ultimate difficulty tier.
- **Unresolved or untested:** The meaning and producer of win-ranking row 1;
  other producers of word `0x6A`; the spoken words of the event-5 sound
  request; indirect or inlined row writers.
- **Deliberate exclusions and overlap:** Record offsets of the ranking tables,
  their fresh seeding, and the byte-bank counter writer belong to
  [Save-data record format and lifecycle](../../game/save_data.md#fresh-profile-initialization)
  and [Battle-result counters](../../game/save_data.md#battle-result-counters-in-the-byte-bank-at-0x2100).
  Consumers of word `0x6A` belong to
  [Content availability](../../game/content_availability.md#progress-gates) and
  [Practice mode](practice_mode.md#row-availability). Shared outcome and
  battle-number transitions belong to
  [Match outcomes](../session/match_outcomes.md#higher-level-sequence-counter-and-result-8-continuation);
  audio playback belongs to [Battle audio](../session/battle_audio.md).
- **Evidence limitations:** All findings are static reads of the clean
  resident ELF and BTL/ETC overlays. Indexed cross-references omit several
  direct BTL calls, so those calls were established from instruction bytes;
  direct-call searches do not exclude indirect or inlined access. English
  course names are translations, not recovered retail strings.

## Evidence and address conventions

Inputs and address conversion follow
[Retail game file identities](../../game/files/file_identities.md#address-conventions).
BTL addresses are given as export/live pairs, export first.

## Controller modes and ranking insertion

The controller's result path gives the saved Survival tables bounded
semantics:

- `FUN_001f24b0` (`0x001F24B0`), called by `FUN_001f27b0`, inserts the current
  character and a cumulative metric into the first block in ascending order
  for controller mode 5, but only while global eligibility value
  `0x00607670` is 1; otherwise it returns `-2` without changing the table.
  Lower is better and ties insert ahead. The metric is cumulative whole
  elapsed seconds. Battle timer `FUN_001eba80` maintains a
  Q8.24 elapsed value at `0x006B28D8`, adds fixed delta `0x00044444`
  (approximately 1/60 second) per active update, and caps its integer part at
  99. After a win, `FUN_001f2e70` adds `max(0, timer >> 24)` to the controller
  metric. `FUN_001f0b10` compares the same integer-second value with 31 and 61,
  establishing the game's at-most-30/at-most-60-second conditions. The saved
  entry is therefore a finite Survival course cumulative-time record. All 25
  course-to-row mappings are established below.
- `FUN_001f2630` (`0x001F2630`), also called by `FUN_001f27b0`, inserts the
  current character and `controller + 4 - 1` into the second block in
  descending order for controller mode 4. The counter starts at 1 and advances
  after wins, establishing a Survival completed-win/streak record. Its observed
  native path uses row 0; the second allocated row's meaning remains unresolved.

Both insertion functions take their row index verbatim from
`controller + 0x10`. The resident routine at `0x001F22C0` writes its second
argument to that word and its third argument to `controller + 0x30`. BTL calls
it at export/live `0x006EED4C/0x006EED8C` with the selected course index and a
pointer into the 20-byte course table at live `0x00896370`; its alternate path
at export/live `0x006EED68/0x006EEDA8` supplies row zero and a null pointer.
The constructor call immediately before this, export/live
`0x006EECF4/0x006EED34`, passes mode 4 when the selected node's word `+0x0C`
is 1, and mode 5 otherwise. Node value 0 selects the course-table path; node
value 1 selects row zero with no fixed course. The mode-4 initializer constructs
the randomized opponent list, whereas mode 5 reads the selected course's fixed
three-byte opponent entries through `controller + 0x30`.

## Course table

The first ranking block's rows are exactly the 25 course IDs, not character
IDs or arbitrary categories. The BTL course table occupies live
`0x00896370..0x00896563` (complete-file offsets `0x1E2470..0x1E2663`), with
25 records of `0x14` bytes. Each record's byte `+0x00` equals its row index,
byte `+0x01` groups the course in the selector, halfword `+0x08` is its battle
count, and word `+0x10` points to its native name. The name strings span live
`0x00896010..0x0089636C`. Ruby markup is omitted in the transcription below;
the English names are translations of the observed Japanese text.

The last column gives the byte-bank index and signed increment used by result
kinds 0/4 in the
[battle-result counter processor](../../game/save_data.md#battle-result-counters-in-the-byte-bank-at-0x2100).
Those values come from course record `+0x0A/+0x0C`; repeated counter IDs are
table data, so these counters are not one independent flag per course. The
counter IDs below are hexadecimal.

| Save row | Native course name | English meaning | Battles | Counter increment |
| ---: | --- | --- | ---: | --- |
| 0 | 忍者学校 | Ninja Academy | 2 | `0x0B` += 3 |
| 1 | 下忍ランクＡ | Genin Rank A | 3 | `0x01` += 3 |
| 2 | 下忍ランクＢ | Genin Rank B | 3 | `0x00` += 3 |
| 3 | 下忍ランクＣ | Genin Rank C | 3 | `0x04` += 2 |
| 4 | 下忍ランクＤ | Genin Rank D | 3 | `0x08` += 3 |
| 5 | 砂の三姉弟 | Three Sand Siblings | 3 | `0x07` += 3 |
| 6 | 霧の刺客 | Mist Assassins | 2 | `0x0D` += 3 |
| 7 | 新紅班 | New Kurenai Team | 3 | `0x05` += 3 |
| 8 | 新アスマ班 | New Asuma Team | 3 | `0x0F` += 3 |
| 9 | 新ガイ班 | New Guy Team | 3 | `0x09` += 3 |
| 10 | 新カカシ班 | New Kakashi Team | 3 | `0x13` += 3 |
| 11 | 上忍ランクＡ | Jonin Rank A | 3 | `0x02` += 3 |
| 12 | 上忍ランクＢ | Jonin Rank B | 4 | `0x00` += 3 |
| 13 | 砂の強者 | Sand's Strong Fighters | 5 | `0x0A` += 3 |
| 14 | 音の五人衆 | Sound Five | 5 | `0x0C` += 3 |
| 15 | 邪なる者 | Evil Ones | 3 | `0x06` += 2 |
| 16 | 伝説の三忍 | Legendary Sannin | 3 | `0x11` += 3 |
| 17 | “暁” | Akatsuki | 5 | `0x10` += 3 |
| 18 | 火影たち | Hokage | 5 | `0x0E` += 3 |
| 19 | 特別対戦 | Special Match | 5 | `0x14` += 3 |
| 20 | 金髪五人衆 | Five Blond Fighters | 5 | `0x12` += 5 |
| 21 | 傀儡軍団 | Puppet Army | 5 | `0x04` += 3 |
| 22 | 木ノ葉先生 | Leaf Teachers | 5 | `0x13` += 5 |
| 23 | 血継限界 | Kekkei Genkai | 5 | `0x06` += 3 |
| 24 | 高みの者たち | Those at the Top | 5 | `0x15` += 3 |

The battle counts also equal the 25 reset factors at `0x005C0710` recorded in
[Fresh-profile initialization](../../game/save_data.md#fresh-profile-initialization),
independently connecting each seed time to its course length.

## Ranking display and Records navigation

BTL's first-block ranking draw calls `FUN_001f7400` at export/live
`0x006E9670/0x006E96B0` for slots 0 through 2 using its selected row word
`+0x10`; its win-ranking draw independently calls `FUN_001f7470` at
export/live `0x006E8F54/0x006E8F94` for the same three slot indices. This
establishes separate saved time and win lists rather than one table
interpreted in two ways.

The on-record pairs remain two signed 32-bit words, and insertion compares the
full 32-bit metric. Both BTL display helpers nevertheless load character ID
and metric with signed `lh` at pair offsets `+0/+4`: the win renderer at
export/live `0x006E8DA4/0x006E8DE4` and `0x006E8DD0/0x006E8E10`, and the time
renderer at `0x006E94B4/0x006E94F4` and `0x006E94E0/0x006E9520`. Consequently
their displayed values are only the signed low halfwords; display does not
validate or represent the full stored 32-bit range.

Win-ranking row 0 is the native `壮絶サバイバル` list. Its BTL draw passes the
name at live `0x00897860` to the header renderer at export/live
`0x006E8FF4/0x006E9034`. The Records controller starts both ranking row words
at zero (`0x006E9BA0/0x006E9BE0` and `0x006E9BA8/0x006E9BE8`, export/live).
Its input dispatcher `FUN_006e9d80` permits only index 0 for the win list:
export/live `0x006E9E44/0x006E9E84` calls the shared row selector with maximum
zero. The time-list branch at `0x006E9E74/0x006E9EB4` instead supplies maximum
`0x18`, allowing all 25 time rows. The native mode-4 creation path also assigns
row zero. Thus this bounded Records/result path does not expose, name, or
produce win-ranking row 1. Its allocation and seeded values alone do not
establish a second playable Survival submode.

## Win-row producer and ordinary-controller lifetime

The ordinary battle controller's lifetime preserves the row word set at
creation. Constructor `FUN_001F1F30` explicitly clears the row word at
`0x001F1F40`. Initializer `FUN_001F1F70` assigns the mode and opponent list
but does not change that word. The complete short setter at `0x001F22C0` is
`sw a1, 0x10(a0); sw a2, 0x30(a0); jr ra; nop`
(`100085AC 300086AC 0800E003 00000000`); it is not a defined function in the
preserved analysis. Its only direct `jal` matches in the resident, BTL, and
ETC programs are the two BTL creation sites described above: mode-4 creation
explicitly passes zero, while finite mode-5 creation passes the selected
course row.

The enclosing BTL acceptance helper at export/live
`0x006EEBF0/0x006EEC30` admits node kinds 0 and 1 to this Survival constructor
and routes kind 2 to a different constructor. Instruction bytes
`0x006EEBF0..0x006EED8F` supply both the caller branches and the continuation
after allocation that the preserved constructor decompilation omits. Resident
`FUN_001F2E70` changes the battle number, cumulative time, and completion
states, but preserves this controller's row word through ordinary wins,
continuation, and result entry. Result initializer `FUN_001F27B0` forwards it
unchanged to both ranking insertion and the BTL result setter. Win insertion
`FUN_001F2630` requires mode 4 at `0x001F2664..0x001F267C` and obtains the
same row at every getter/setter call; it does not derive row 1 from battle
number, character, difficulty, or result state.

The win-result setter at export/live `0x006EE1D0/0x006EE210` copies that row
to its result controller `+0x4C` and then the ranking child's `+0x10`
(`0x006EE20C..0x006EE21C` export). This is a separate presentation object,
not a write back into the Survival controller or saved row selector. Records
creates its own win/time ranking children and explicitly sets both row words
to zero. Its shared row-navigation code decrements/increments `+0x10` and
wraps to the supplied maximum/zero (`0x006E8974..0x006E89CC` export); with
maximum zero in the win branch, either direction retains row zero.

**Bounded conclusion:** the inspected construction, continuation, result, and
Records paths supply no native row-1 producer or selector. An independently
seeded, checksum-covered row exists, but its contents do not establish a
reachable player-facing ranking. An uninspected indirect or inlined producer
is still possible; no whole-game non-use claim is made.

BTL calls to `0x001F1E80` at export `0x006EECF4` and to `0x001F7400` at
export `0x006E9670` are absent from the indexed cross-references, so the
absence of indexed references is not evidence that a save accessor has no
direct callers.

## Finite-course result admission

**Observation, high confidence:** resident `FUN_001f27b0` creates the finite
course result owner only for battle-controller mode 5. It calls
`FUN_001f24b0`, constructs the BTL result wrapper through live `0x006EE0C0`
with argument 1, and passes the selected course ID and ranking result to live
`0x006EE2C0` at resident `0x001F2878`. The BTL setter at export/live
`0x006EE280/0x006EE2C0` copies those arguments to the result controller's
`+0x48` and `+0x0C`. Mode 4 instead constructs the other result owner and
does not route into this course producer.

`FUN_001f24b0` returns `-2` when the battle-route word at `0x00607670` is
not 1. On route 1 it returns a ranking slot `0..2` or `-1` when the elapsed
time misses the saved top three. The `0x6A` producer's immediate caller
rejects only `-2`, so obtaining a top-three time is not required. This is a
result-route gate, not a test of the saved difficulty option.
The result-code meanings and enclosing wrapper's post-battle lifetime belong
to [Match outcomes](../session/match_outcomes.md#higher-level-sequence-counter-and-result-8-continuation).

The result wrapper allocates a `0x68`-byte course controller and assigns its
descriptor `0x005DDC30` to `+0x38` at BTL export/live
`0x006EE140/0x006EE180`. The descriptor contains live callbacks
`0x006ED550`, `0x006EC4F0`, `0x006EC240`, and `0x006EC070` at offsets
`+0x08`, `+0x0C`, `+0x10`, and `+0x14`. Its type-name chain leads to exact
retail string `ccTimAtkResult` at live `0x008980D0`. This internal name does
not change the player-facing Survival identification established by the
resident controller and course strings.

Update at export/live `0x006ED7E0/0x006ED820` dispatches state `+0x08`
through the seven-word table at live `0x008C2E90`. State 0 targets live
`0x006ED86C` (export `0x006ED82C`), which calls live `0x006EC7F0`.
That handler first requires its presentation object `+0x20` to be ready,
then accepts edge-input mask `0x20` from the manager's selected controller
port. Only an accepted input invokes live `0x006EC6F0`, the producer
admission described below. Instruction bytes `0x006ED7E0..0x006EDB33` and
`0x006EC7B0..0x006EC8F7` recover the switch and the taken confirm branch
omitted by the decompiler. In particular, `li v1,1` at export `0x006EC824`
bypasses the false path at `0x006EC830`. The result wrapper owns this
controller until resident `FUN_001f2920` finishes and destroys it through
live `0x006EDF70`.

## Difficulty-word producer

**Observation, high confidence:** the complete BTL routine at export/live
`0x006EC570/0x006EC5B0` updates saved word `0x6C` with bit
`1 << (controller[+0x48] & 0x1F)`. If that controller index is at least
`0x18`, it writes `FUN_001f7750(manager, 0x6A, 1)`, sends event 5 through
live `0x006EA410`, and returns 6. The decisive call is export/live
`0x006EC5D0/0x006EC610`, bytes `D4 DD 07 0C`; its preceding argument loads
are `a1 = 0x6A`, `a2 = 1`. Instruction bytes `0x006EC570..0x006EC6A3`
establish the complete routine because Ghidra splits it at `0x006EC5B0`.

For an index below `0x18`, it compares adjacent records' byte `+1` in the
25-record course table above. A changed group sets the corresponding bit of
word `0x6B`, emits event 4, and returns 5; an unchanged group emits event 3
and returns 4. The table's group bytes are:

```text
indices  0.. 5: 0
indices  6..10: 1
indices 11..15: 2
indices 16..19: 3
indices 20..24: 4
```

The immediate caller at export/live `0x006EC6B0/0x006EC6F0` declines this
producer when controller `+0x0C == -2`, saved word `0x6A == 1`, or the current
index's word-`0x6C` bit is already set. Otherwise it calls the producer,
stores its nonzero return in controller `+0x08`, and dispatches the controller
callback at descriptor `+0x14`. The complete caller bytes
`0x006EC6B0..0x006EC7AB` establish these conditions despite another split
function boundary. This caller tests exactly 1, whereas the difficulty menus
accept any nonzero saved value.

BTL has four direct calls to `FUN_001f7750` and ETC none; other writers,
inlined writes, and indirect calls remain possible.

**Inference, high confidence:** in the native 25-course domain, index 24 is
the sole course index satisfying the producer's `index >= 0x18` comparison.
Its record at live `0x00896550` names `高みの者たち` (Those at the Top),
has group byte 4 and five battles. Thus acknowledging an eligible result for
that finite Survival course sets difficulty word `0x6A`, provided it is not
already exactly 1 and word `0x6C` does not already contain the course bit.

The earlier native admission has two separate gates. `FUN_006e0a30` accepts
a selected group only when its bit in word `0x6B` is set. Entry helper
`FUN_006e04b0`, called at export/live `0x006E0488/0x006E04C8`, ORs bit 0
into that word without clearing later group bits. Within the selected group,
`FUN_006e0cc0` admits course 0 directly; every other course `i` requires bit
`i - 1` in word `0x6C`. Its decisive read/shift bytes are export
`0x006E0D14..0x006E0D38`. The result producer enables the **next** group's
word-`0x6B` bit at boundaries 5, 10, 15, and 19; the byte loaded into `s1` at
export `0x006EC620` comes from the next record. This distinguishes group
admission from per-course completion.

**Inference, high confidence:** starting from the freshly cleared word banks,
ordinary course confirmation and accepted result acknowledgement advance
through `0..24` in order. The final writer itself checks only its current
index and local result gates, so arbitrary non-native stored bit patterns are
not evidence that it verifies all earlier course bits at once.

## Final-result text and event 5

The state-6 draw branch at export/live `0x006EDDCC/0x006EDE0C` emits the
seven entries of the pointer table at live `0x00897D20`, including two blank
separators. Shift-JIS bytes at export `0x00897AA0..0x00897CD6` establish
the final-result wording. With only ruby/color markup removed, its mode label
is `「究極連激戦」全クリア報酬！`; the mode title's ruby is
`ナルティメットれんげきせん`. The difficulty announcement is
`最も手強い難易度の「究極」が追加されました！`, preceded by a reference to
`「フリーバトル」などの「難易度設定」`. Thus the retail message explicitly
announces the Ultimate difficulty tier for Free Battle and other difficulty
settings. This is exact display evidence for the finite course mode and unlock
event; the English course name above is a translation, not a recovered English
retail string.

Event 5 from the writer is a sound request, not an established dialog ID.
Live `0x006EA410` dispatches through the table at live `0x008C2E40`;
entry 5 points to live `0x006EA47C`, which supplies sound index `0x25` to
live `0x006EE6A0`. That helper calls resident `FUN_001d6010(0x4E, 0x25, 0)`.
The resident wrapper selects category 2, and its descriptor at `0x003FDFC0`
contains bank `0x62`, variant 1, and count `0x47`. This establishes the exact
audio request but not its spoken words. The displayed text is established
independently by the state-6 renderer above.
