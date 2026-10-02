# Battle statistics

This document records how retail NA2 (`SLPS-25837`) counts battle statistics
and turns them into conditions and a result-screen score: the 28 retail
result-bank metrics and their producers, fighter statistic pairs and the
condition predicates that read them, direct BTL condition-status writers, and
the BTL metric import, tier, and ryo commit. Match termination, result codes,
and the outer state machines that route a battle to scoring belong to
[Match outcomes](match_outcomes.md).

## Research coverage

- **Assigned scope:** the two-side 28-slot result bank and its wrappers; every
  direct bank producer; fighter `+0x4F0` statistic pairs as consumed by
  conditions; the condition evaluator `FUN_00223450`; direct BTL
  condition-status writers; and the result object's import, contribution,
  tier, and accumulator commit.
- **Exploration depth:**
  - Exhaustive within encoded-call searches: all 50 BTL add calls, 19 BTL max
    calls, four resident add calls, two resident set calls, 14 resident
    event-dispatcher calls, and all ten BTL calls to condition writer
    `FUN_001FD850`; all 28 descriptor strings decoded.
  - The full implemented switch in `FUN_00223450` and its configured-list
    caller; producer traces for its fighter fields are bounded to the
    described families.
  - Bounded producer and lifetime traces: fighter pair index 13, the shared
    jutsu-clash controller and one installed callback, all four metric-12
    sites and both metric-19 branches, and both metric-1 producers through
    their callers, record gates, and request lifetime.
  - The BTL result-object import/helper/dispatcher/commit region at raw
    `0x0651D0..0x066480`, its descriptors, bucket tables, tier thresholds, and
    resident accumulator calls.
- **Confirmed coverage:** all retail metric categories, the resident
  selector-to-bank mapping, ordinary versus linked ninjutsu gates, combo
  flush/high-water behavior, support deduplication and combination
  qualification, tool and stage-object credits, Ultimate and afterimage
  credits, inventory-slot snapshot, condition thresholds and terminal
  provenance predicates, the paired-response count and its continuation
  lifetime, selected clash comparison and the `ccSkillKBW001` callback,
  representative prop recipient/repeat rules, the opposite record-flag gates
  of the two Ultimate producers, metric import, tier, and ryo mechanics.
- **Unresolved or untested:**
  - Retail condition menu strings, including a name for paired-response
    condition `0x26`; human-readable tier labels.
  - Every derived jutsu-clash callback override, every authored prop
    configuration and reset sequence, and every computed or indirect bank
    write.
  - A same-activation metric-`1` double credit: the two sites add
    independently but have opposite ordinary record gates, and no transition
    joining them was found.
  - Reachability of result-object state `5`; when the committed ryo value
    reaches the memory card; any unlock or item grant from scoring.
- **Deliberate exclusions and overlap:**
  - Termination, result codes, outer routing, and cleanup belong to
    [Match outcomes](match_outcomes.md).
  - Combo pending/flush ownership belongs to
    [Combo accounting](combo_accounting.md); fighter statistic reset and copy
    to [Hit response](hit_response.md#hit-count) and
    [Battle lifecycle](battle_lifecycle.md#fighter-statistics-across-reconstruction).
  - Substitution, movement, recovery, support, projectile, item, and stage
    behavior stay with their linked owners; result rendering and layout are
    outside this document. Retail metric text is evidence for categories, not
    a localization specification.
- **Evidence limitations:** static evidence only; no PCSX2 runtime trace was
  made, and dynamic confirmation is outstanding. BTL xrefs and function
  boundaries omit significant bodies, so negative conclusions are limited to
  the stated byte and reference scans. Static calls establish per-invocation
  arithmetic and ordering, not scheduler frequency or wall-clock duration.

## Address convention

Resident addresses are ELF virtual addresses; BTL addresses are live unless
prefixed `D` (preserved Ghidra address, live minus `0x40`). Conversions follow
[Retail game file identities](../game/files/file_identities.md#address-conventions).

The BTL result-object entries are:

| Role | Raw file | Live EE | Preserved export | Address note |
| --- | ---: | ---: | ---: | --- |
| Construct result object | `0x0651D0` | `0x007190D0` | bytes at `0x00719090` | Initializes the `0x188`-byte object and its descriptor records |
| Destroy result object internals | `0x065240` | `0x00719140` | bytes at `0x00719100` | Releases the fade, render object, and both result subobjects |
| Create result presentation internals | `0x065390` | `0x00719290` | bytes at `0x00719250` | Called by resident score-setup state `0x13` |
| Clear result-metric object | `0x065600` | `0x00719500` | `FUN_007194C0` | Called directly by resident controller setup and result teardown |
| Import battle metrics | `0x065680` | `0x00719580` | `FUN_00719540` | Called by resident state `0x10` |
| Capped/weighted metric helper | `0x065B60` | `0x00719A60` | bytes at `0x00719A20` | Stores a capped value and descriptor weight times value |
| Threshold-boolean metric helper | `0x065BC0` | `0x00719AC0` | bytes at `0x00719A80` | Stores raw value and a fixed contribution when threshold is met |
| Floor-bucket metric helper | `0x065C00` | `0x00719B00` | bytes at `0x00719AC0` | Selects the last table row whose threshold is not above the value |
| Ceiling-bucket metric helper | `0x065C70` | `0x00719B70` | bytes at `0x00719B30` | Selects the first table row whose threshold is not below the value |
| Read metric contribution | `0x065CE0` | `0x00719BE0` | bytes at `0x00719BA0` | Returns the selected entry's contribution word |
| Finalize 28 contribution values | `0x065D00` | `0x00719C00` | `FUN_00719BC0` | Encoded target is live `0x00719C00` |
| Result-object dispatcher | `0x065E80` | `0x00719D80` | `FUN_00719D40` | Called by resident state `0x14` |
| Initialize total/tier view | `0x065FD0` | `0x00719ED0` | `FUN_00719E90` | Called at raw `0x065F2C` by encoded `jal 0x00719ED0` |
| Accept/commit result points | `0x0663C0` | `0x0071A2C0` | physical export `FUN_0071A280` | Ghidra incorrectly splits its commit block as `FUN_0071A2C0` |
| Commit basic block | `0x066400` | `0x0071A300` | displayed `0x0071A2C0` | Part of the live `0x0071A2C0` function, not a separate live entry |
| Commit-input predicate | `0x066480` | `0x0071A380` | displayed `0x0071A340` | Tests selected-side record bit `0x20` |

Encoded `jal` targets are live addresses: resident `jal 0x00719500` lands on
the prologue at raw `0x065600`, which the preserved export labels
`FUN_007194C0`.

## Battle-statistic producers

### All 28 retail metric labels

Descriptor word `+0x08` in the 28-by-`0x0C` table at live BTL
`0x008C3DE0` points to a Shift-JIS string with ruby markup. The strings below
omit only that pronunciation markup; `%s` is the retail substitution token.
Their live addresses are encoded in the descriptors. The labels establish
gameplay categories; the producer contracts establish what actually counts.

| Index | Retail text | Meaning and source/import distinction | Live string |
| ---: | --- | --- | ---: |
| `0` | 敵は忍術にて攻めるべし | Ninjutsu; accepted actor/projectile events and token-suppressed contact. | `0x00899450` |
| `1` | 敵は奥義にて攻めるべし | Ultimate Jutsu; action-marker and post-Ultimate producers both add. | `0x00899490` |
| `2` | 敵は連係攻撃にて攻めるべし | Linked attacks; deduplicated support notification, sometimes transferred to `25`. | `0x008994C0` |
| `3` | 変わり身にて敵を欺くべし | Substitution; eligible ordinary substitution entry. | `0x00899500` |
| `4` | 追い討ちにて敵を追撃すべし | Extra Hit follow-up; resolved exchange credit. | `0x00899540` |
| `5` | 連続攻撃にて敵を圧倒するべし | Consecutive attacks; accumulated source is replaced by source `17` at import. | `0x00899580` |
| `6` | 特殊忍具を用いて攻めるべし | Special ninja tools; item dispatch and projectile credits. | `0x008995D0` |
| `7` | 敵は素早く排除すべし | Finish quickly; computed remaining whole timer units. | `0x00899610` |
| `8` | 己の体力は温存すべし | Preserve health; selected HP converted to a percentage-like integer. | `0x00899650` |
| `9` | 強者を打ち破るべし | Strong opponent; COM strength plus one, or default `3`. | `0x00899690` |
| `10` | 秘めたる力を解き放つべし | Hidden power; awakening-entry credits. | `0x008996C0` |
| `11` | 挑発を以って敵を刺激すべし | Taunt; accepted animation marker. | `0x00899700` |
| `12` | 壊れ物を破壊すべし | Breakable objects; eligible stage-object interactions. | `0x00899750` |
| `13` | 特殊条件を完遂すべし | Special conditions; finalized subtotal of contributions `14..16`. | `0x00899780` |
| `14` | 敵の奥義を打ち破るべし | Defeat an enemy Ultimate; defender interruption credit. | `0x008997C0` |
| `15` | 術の競り合いにて勝利すべし | Jutsu clash win; actor outcome callback argument `0`. | `0x00899800` |
| `16` | 敵に残影をもって挑むべし | Zanei/afterimage challenge; contest entry. | `0x00899840` |
| `17` | コンボ数%sHitボーナス | Combo-count bonus; high-water value and floor bucket. | `0x00899880` |
| `18` | 所持アイテム%s個ボーナス | Held-item bonus; occupied inventory slots at terminal phase transition. | `0x008998A0` |
| `19` | 背景破壊ボーナス | Background destruction; event count converted to a fixed bonus when positive. | `0x008998D0` |
| `20` | 残影勝利ボーナス | Afterimage victory; winner count converted to a fixed bonus when positive. | `0x00899900` |
| `21` | 奥義ボーナス | Ultimate bonus; source receives `100/200/300`, result is forced to zero. | `0x00899930` |
| `22` | 敵%sカウント以内撃破ボーナス | Fast-finish bonus; elapsed units and ceiling bucket. | `0x00899950` |
| `23` | 体力１００％ボーナス | 100% health bonus; derived from converted HP. | `0x00899990` |
| `24` | キャラクター組み合わせボーナス | Character combination; source qualification flag, result recomputed from `25..27`. | `0x008999C0` |
| `25` | 特殊連係攻撃%sHitボーナス | Special linked attack; imported from source `2` when source `24` is nonzero. | `0x008999F0` |
| `26` | 連係忍術%sHitボーナス | Linked ninjutsu; accepted action identifiers `0xC0..0xC4`. | `0x00899A30` |
| `27` | 連係奥義%sHitボーナス | Linked Ultimate; qualifying post-Ultimate helper. | `0x00899A60` |

### Direct producer inventory and its limits

Exact encoded-call searches of the clean resident executable and BTL image
were paired with raw instruction reads around every result-bank add, set, and
max call. BTL contains 50 direct add sites, 19 direct max sites, and no direct
set site. Its adds comprise 16 calls in eight `0` versus `26` branches,
19 combo-flush calls to `5`, four tool calls to `6`, four breakable-object
calls to `12`, two background calls to `19`, and one each for `0`, `15`,
`2`, `24`, and `27`. All 19 max sites update `17`. The original resident
address range has four direct adds: the event dispatcher, Ultimate interruption
`14`, Ultimate count `1`, and Ultimate reward tally `21`. Its two direct
sets target `17` and `18`. Mirrored resident aliases are not additional
physical producers.

This inventory
is exhaustive for these direct encoded calls in these two images. It does not
exclude computed/indirect calls or differently constructed bank-address stores.

### Resident event selectors and result-bank indices

Resident `FUN_00223360(fighter, event_selector, delta)` translates a fighter
event into a BTL result-bank operation. These selectors are not the result
metric indices. It chooses one-based side `1 + (fighter[+0x60] & 1)` and uses
the ten-entry jump table at resident `0x005C2150..0x005C2177`:

| Event selector | Result-bank metric | Operation |
| ---: | ---: | --- |
| `0` | `0` | Add delta |
| `1` | `3` | Add delta |
| `2` | `4` | Add delta |
| `3` | `17` | Set value |
| `4` | `1` | Add delta |
| `5` | `5` | Add delta |
| `6` | `10` | Add delta |
| `7` | `11` | Add delta |
| `8` | `16` | Add delta |
| `9` | `20` | Add delta |

The raw instructions at resident `0x00223360..0x0022344F` establish the full
mapping. Case `3` reaches `jal 0x00715FD0` at `0x00223428`; the other cases
share `jal 0x00715F90` at `0x00223438`. The caller's delta remains in `a2`.
A selector above `9` reaches that
common call without translation, so range validity is a caller contract.

The 14 physical resident calls establish these events. Selector `0` has no
direct resident caller in this scan.

| Bank metric | Resident call site(s) | Producer contract |
| ---: | --- | --- |
| `3` | `0x00229B3C` | Ordinary substitution entry excludes route bit `0x200` and low-nibble route `2`; it also increments fighter count/max `+0x51C/+0x51E`. [Substitution](substitution.md) owns the routes. |
| `4` | `0x00243FBC`, `0x00243FE0` | `FUN_00243EF0` resolves the `+0xB00` Extra Hit roles. Zero local role credits the opponent; otherwise it credits the local fighter while clearing resolved role bits. [Hit response](extra_hit.md#exchange-state-at-fighter-0xb00) owns the exchange. |
| `17` | `0x0020C6F8`, `0x0020CDEC` | Set current combo only when `FUN_002231D0(fighter,23,current,0)` raises maximum `+0x54E`; its current field is `+0x54C`. Combo-object ownership belongs to [Combo accounting](combo_accounting.md). |
| `1` | `0x0024540C` | Major-`8`, phase-`0` accepted animation marker in `FUN_00245340`; separately updates `+0x514/+0x516` only with the terminal gate clear. [Ultimate producer contracts](#metric-1-entry-cleanup-and-possible-double-credit) recover the caller's record gate. This is not proof of an Ultimate win. |
| `5` | `0x0020C598` | `FUN_0020C420` drains fighter pending byte `+0xA45` into combo object `+0x34`, clears the byte, and adds one when the new combo exceeds one. It does not add the byte's magnitude here. See [Combo accounting](combo_accounting.md#resident-owner-and-update-order). |
| `10` | `0x0020DC7C`, `0x0020E4C0`, `0x0020E6AC` | Awakening-entry tails. [Awakening](awakening.md#already-present-and-constructor-owned-adoption) owns the reconstruction adoption that reads this metric to suppress another entry credit. |
| `11` | `0x00227444` | Major/substate `(0,3)` when `FUN_002275D0` accepts the character-specific taunt marker and `+0x956 == 0`; separately increments `+0x530/+0x532`. |
| `16` | `0x00245D68`, `0x00247B28` | Entry to `(8,0x14)`, initializing afterimage fields `+0xB10/+0xB12` and clearing `+0xB16..+0xB18`. |
| `20` | `0x00246EE4` | Local signed byte `+0xB17` exceeds the opponent's value in `FUN_00246D10`. This winning comparison is distinct from entry metric `16`. |

### Accepted ninjutsu and combo flushing

Eight BTL paths choose between bank `26` and `0`: action identifiers in
inclusive range `0xC0..0xC4` receive linked-ninjutsu credit, other identifiers
ordinary ninjutsu credit. Each adds one. Actor paths read identifier
`+0x56C`, require actor word `+0xFE8 == 0`, and increment that word.
Projectile paths require accepted-contact flag `+0x1D4 & 1` and word
`+0x1D8 == 0`. They either forward credit to the matching primary actor,
using its `+0xFE8` gate, or classify the projectile identifier `+0x90`,
then increment `+0x1D8`. The forwarding branch checks pair identity against
context `+0x70/+0x74`; ownership is not inferred from a class name.
Representative raw branches are live `0x007B9ED0..0x007B9F68` and
`0x00780000..0x00780140`. The projectile initializer at live
`0x0077F2F0` clears `+0x1D4/+0x1D8` (stores `0x0077F3C0/0x0077F3C4`).
The actor initializer fragment clears `+0xFE8` at live `0x00785880`
(Ghidra `0x00785840`, instruction `sw zero,0xFE8(s1)`). No separate
within-activation reopening was identified by the direct field-reference scan.

The combo flush has the same shape at all 19 max sites. It reads a positive
pending word `context +0x3268 + side_zero_based*4`, calls resident
`FUN_0020C2E0(side,count)`, conditionally adds count to bank `5` when
live `0x00706CA0(manager,side)` is nonzero, always max-updates bank `17`,
and clears the pending word. The pending/cumulative words and the predicate
behind the conditional add belong to
[Combo accounting](combo_accounting.md#per-side-accumulated-contribution-route).

The live add-`5`/max-`17` call pairs are:

```text
00778070/00778084 0077FF8C/0077FFA0 00787C1C/00787C30
00789874/00789888 0079FEA8/0079FEBC 007A501C/007A5030
007AFE24/007AFE38 007AFEE8/007AFEFC 007B0A14/007B0A28
007B9FC8/007B9FDC 007C2E2C/007C2E40 007CDC10/007CDC24
007D4558/007D456C 007D4FAC/007D4FC0 007D8070/007D8084
007DCED4/007DCEE8 008051F4/00805208 008052E4/008052F8
008084E8/008084FC
```

Source `5` is an additive tally and source `17` is a high-water value.
Import uses `17` for both weighted metric `5` and bucketed bonus `17`,
so adding source `5` is not the result-screen formula.

### Projectile contact deduplication

Metric `0` includes the common projectile-contact path, rather than simply
counting every update in contact. Live BTL `0x00735B70`, at raw `0x081C70`,
ages four selected-side records and increments metric `0` by one only for a
matching `+0x02/+0x04` token pair whose byte `+0x08` is zero; it then sets
that byte to one. Its metric call is live `0x00735C50` (Ghidra
`0x00735C10`). [Projectile motion and state behavior](projectiles.md)
owns the four-slot record lifecycle and the common contact caller. This
proves token-suppressed contact credit within the labeled ninjutsu category,
not a count of individual damage ticks.

### Ninja tools and stage objects

Metric `6` has four direct BTL adds. The item-dispatch tail at live
`0x00711908` credits one after the applicable `0x51..0x73` code branch;
an individual effect handler's rejection does not remove this tail credit.
The common projectile credit at `0x007342E0` converts object signed byte
`+0x8A` to the opposite one-based side (`0 -> 2`, `1 -> 1`) and requires
the battle manager. Paths `0x0073C754/0x0073D610` use one-shot flags
`+0x2C2 & 4` and `+0x2C8 & 1`. These measured events are not a universal
count of button presses or successful damage. [Battle items and statuses](battle_items_and_status_effects.md)
and [projectiles](projectiles.md) own individual effects and flag lifetimes.

Metric `12` adds at live `0x006C4E98/0x006C5EFC/0x006C6E00/0x006D2868`.
All four inspected paths resolve a category-`0` fighter contact and its attack
record, rejecting record `+0x10 & 0x00F00000`, `+0x10 & 2`, or
`+0x14 & 0x02000000`. They require the battle manager and credit the contacting
fighter's `1 + (+0x60 & 1)` side. The following class-specific gates decide
which accepted contacts count; the bank wrapper supplies no deduplication:

| Concrete retail owner / metric-12 call | Credit and repeat boundary |
| --- | --- |
| `ccBgBreakObjectBattle`, live `0x006C4E98` | Update live `0x006C4AD0` admits contact only while count `+0x34 != +0x38`, playback `+0x180` is nonzero, and the earlier contact predicates permit it. Trigger live `0x006C47B0` increments the count, capped at `99`; credit requires equality with `+0x38` afterward. Intermediate model transitions do not count. Equality excludes the next contact pass until a separate reset reopens it. The `-1` looping threshold cannot equal the ordinary nonnegative count, so that configuration does not credit through this branch. |
| `ccBgBreakObjectBattleAnm`, live `0x006C5EFC` | Update live `0x006C5B60` reaches contact admission only while `+0x48 == 0`. Trigger live `0x006C5800` raises `+0x48`, and the caller credits when it is nonzero. Subsequent updates service the animation/reset path instead of accepting another contact. A completed reset clears `+0x48`, allowing another credit; this is not a once-per-object allocation flag. |
| `ccBgBreakDollBattle`, live `0x006C6E00` | True update prologue `D0x006C6900` first rejects a nonzero byte `+0x190`, decrementing it and returning. Accepted contact sets that byte to `FUN_00180210(60) + 60`, then credits after the configured reaction/spawn path. It counts an admitted contact after cooldown, without the base class's terminal-count comparison. |
| `ccBgBreakObjectBattleChandelier`, live `0x006D2868` | True admission prologue `D0x006D24A0` rejects nonzero `+0x48`, resolves the eligible fighter contact, then credits and writes `+0x340 = 0`, state `+0x2E8 = 1`. Controller live `0x006D2DF0` invokes this admission only in state `0`; states `1/2/3` use other paths. State `3` can return to `0` once `+0x48` clears. Credit therefore belongs to the admitted state transition, rather than every active-state update. |

The decisive instruction windows are
`D0x006C4C58..0x006C4E5C`, `D0x006C5E80..0x006C5EBC`,
`D0x006C692C..0x006C6948`, `D0x006C6C68..0x006C6DC4`,
`D0x006D24C0..0x006D24D8`, `D0x006D27F0..0x006D2838`, and
`D0x006D2DD4..0x006D2E64`. [Stages](stages.md#animated-and-breakable-background-evidence)
owns the factories, authored stage distribution, receiver mechanics, and
reborn/moving-object resets that can reopen the shared base path. Those resets
permit repeated metric credit when the relevant threshold is reached again;
the source metric measures qualifying transitions, not distinct prop identities.
The four direct sites and these representative class routes are established,
but every authored prop configuration and derived reset sequence was not
reconstructed here.

Metric `19` adds at live `0x006CAB20/0x006CAD50`, in the stage-object update
beginning at live `0x006CA8A0`. Its two branches scan primary fighters,
require section `+0x9F6` to match object `+0x184`, and accept major-`5`
response substates `0x42/0x43/0x48` or `0x45/0x46/0x49` at marker zero
under the corresponding object `+0x190` flag. Position comparisons use
object `+0x194/+0x198`. After the transition helper, credit requires
object `+0x34 == +0x38`, hides its render objects, and adds one to the
opposite side from the responding fighter. The responding fighter is not
the credited attacker. [Stages](stages.md) owns authored identities and sections.
Conditions `0x2C..0x2E` consume bank `19` at thresholds `3/5/7`;
result import instead awards one fixed bonus when the selected count is positive.
The update's initial `+0x34 != +0x38` gate and exit after one accepted fighter
prevent repeated credit from the unchanged terminal prop in this method.
Both flag branches converge on the same finite-threshold ownership contract;
they are alternative reaction routes, not two unconditional credits for one
fighter scan. No attacker provenance is resolved beyond the opposite-side
selection. Metric `12` and metric `19` thus use different recipient rules and
different source events despite both consuming stage-object transitions.

### Jutsu-clash outcome selection and callback lifetime

**Observation:** the shared clash resolver is live `0x0077BC00`, whose true
prologue is preserved `0x0077BBC0` (raw `0x0C7D00`), not the continuation
that Ghidra labels `FUN_0077BC00`. It obtains the active actors for sides
`0` and `1` through live `0x00777830(context, side, 0)` and compares signed
halfwords context `+0xA7A/+0xA7C`:

| Counter comparison | Side-0 callback value | Side-1 callback value |
| --- | ---: | ---: |
| `+0xA7A > +0xA7C` | `0` | `1` |
| `+0xA7A < +0xA7C` | `1` | `0` |
| Equal | `2` | `2` |

The calls use each actor's table at `+0x110`, slot `+0x1F8`. Raw evidence
`D0x0077BC44..0x0077BEEC` includes all three comparisons and all six
argument setups. A concrete selection is factory arm
`D0x00775EA8..0x00775ED8`: it allocates `0xFF0` bytes, calls live base
constructor `0x00785410`, and installs resident table `0x005E0900` at
actor `+0x110`. That table's `+0x1F8` word at `0x005E0AF8` is live
`0x00787E40`, the metric-producing callback. The table's RTTI points through
live `0x008CE890` to live name `0x008BB498`, exact internal name
`ccSkillKBW001`. This is a concrete registered route; table header
`0x005E08F0` belongs to the preceding interface and must not be used as
this callback's slot origin.

The callback stores the selected value at actor `+0x5F8` before its virtual
work. Only value `0` with a present battle manager adds metric `15`, using
actor `+0x350 + 1`; value `1` and tie value `2` do not add. The routine has
no fighter terminal-gate check or duplicate-credit guard of its own. After the add it
invokes slots `+0x1CC` and `+0x1BC`, clears `+0xF06 & 1` and halfwords
`+0xF08/+0xF0A`, then invokes `+0x1B0`. Those callback side effects are
ordered after the count, so the count is not conditional on their later
response. The resolver separately clears both actors' `+0xF0C` and replaces
context `+0x11D0/+0x11D4` with its selected hit-route flags. These actor-local
outcomes are separate from the match result at `0x00607670`.

**Producer lifetime:** actor-pair admission at live `0x0077A750`
(`D0x0077A710`) requires both actors present with `+0x14 & 3` clear. It
clears their contest receivers/flags through live `0x00787DC0`, invokes
each start slot `+0x1C8`, performs pair positioning and slot `+0x240` work,
then enters the shared setup. Setup live `0x0077A8F0` sets active context
`+0xA74 & 1`, clears timer `+0xA76`, phase `+0xA78`, and both side counters
`+0xA7A/+0xA7C` (`D0x0077A92C..0x0077A970`). Shared update
`D0x00778960` calls live clash driver `0x0077C270` only while that active
bit is set; the encoded driver call is `D0x00778AA4`.

Driver phase `0` advances to phase `1` when the timer is exactly `5`,
resetting the timer at that transition. Phase `1` increments each side's
counter from the logical-input intersection with context `+0xB50`, or from
the side's AI predicate. It resolves once the old timer is at least `150`,
then calls cleanup live `0x0077B4C0`, which clears `+0xA74 & 1`. The phase, count, terminal call, and active-bit clear are at
`D0x0077C280..0x0077C2FC`, `D0x0077C404..0x0077C4E8`,
`D0x0077C61C..0x0077C650`, and `D0x0077B510..0x0077B524`. This supplies a one-resolution-per-active-clash route, rather
than relying on the callback to deduplicate. The constants describe update
counts, not measured presentation duration.

**Bounds:** the actor-pair route and this concrete installed callback are
confirmed. The actor/projectile admission variant at live `0x0077A590`
also enters shared clash setup, but every derived callback override and every
authored simultaneous actor/projectile combination has not been reconstructed.
Counter comparison guarantees only the values sent to the selected callbacks;
it does not prove that every table implements metric credit in the same way.
No condition-menu or broader match-outcome name is inferred from the internal
class name. [Action commands](action_commands.md#logical-mask-translation)
owns logical input translation, and [Battle AI](battle_ai.md) owns AI behavior.

### Ultimate and support producers

Resident `FUN_0035B3B0(side_zero_based)` supplies three direct bank adds
and a qualifying linked-Ultimate call, with mode `6` excluded.
If `FUN_00373790()` returns `2`, site `0x0035B44C` adds one to
metric `14` for the opposite side and returns.
[Ultimate Jutsu](ultimate_jutsu.md) establishes that getter value as the
defender's successful interruption. Otherwise the post-Ultimate tail adds
one to metric `1` at `0x0035B60C` and the reward chosen by live BTL
`0x00715EE0` to metric `21` at `0x0035B62C`.
Resident halfwords `0x00604CF8..0x00604CFD` are `100/200/300`.
Conditions `0x3D/0x3E/0x3F` receive status `1` for the selected class.
Metric `21` retains its source tally until bank reset, although import
forces its result record to zero. The two metric-`1` producers have distinct
record and lifecycle gates, recovered below.

#### Metric-1 entry, cleanup, and possible double credit

**Entry producer:** the sole direct resident caller of `FUN_00245340` is
`FUN_0023BAC0` at `0x0023BB08`. It requires an active record at fighter
`+0xA4C`, record `+0x10 & 0x00F00000` nonzero, and record
`+0x14 & 0x00010000` **set**. The callee further requires major `+0x18E == 8`,
nonnegative `+0x18A`, phase `+0x192 == 0`, and
`FUN_00211A20(fighter+0x1DC, 0)` true. For marker argument zero, that predicate
requires the marker object's `+0x02 & 2`, integer `+0x0C == 0`, and float
`+0x1C == 0.0`; it is not an unconditional per-update count.
Raw `0x0023BAE0..0x0023BB0C` and `0x0024535C..0x00245410` establish
these caller/callee gates and the selector-`4`, delta-`1` call at
`0x0024540C`. `FUN_00223360` translates that selector to metric `1` for
`1 + (fighter[+0x60]&1)`.

The bank add precedes the fighter `+0x62 & 1` check (E) at
`0x00245414..0x00245424`; E does not suppress this source credit.
Only the subsequent separate fighter pair
`+0x514/+0x516` is E-gated, incremented, saturated at `9,999`, and max-updated.
The producer does not set a credit latch or change phase after adding. Its
phase/marker eligibility limits admission; the routine itself does not prove
one invocation per activation. Its preceding `FUN_002040D0(...,0x1F,-1,1)`
dispatches the fighter's event entry through the sound/event interface; this
call does not itself establish a cinematic-start route. Chakra handling in
phase `2` belongs to [Chakra and guard](chakra_and_guard.md).

**Cleanup producer:** `FUN_0035CF00` installs `FUN_0035AF20` at player
`+0x94` and stores the supplied zero-based attacker side in skill-play record
`+0x28`. At `0x0035B158..0x0035B160`, that end callback passes the retained
side to `FUN_0035B3B0`. The manager/mode/interruption branches at
`0x0035B3D8..0x0035B458` are decisive: an absent manager or mode `6` skips
the tail; interruption getter value `2` adds only opposite-side metric `14`
and returns; any other getter value reaches same-side metric `1` at
`0x0035B60C`. There is no E, HP-loss, successful-hit, or prior-metric-`1`
test in that branch. In particular, an entry credit is neither subtracted nor
consulted when cleanup credits metric `1`, and the interruption branch does
not undo any earlier source-bank event.

The end callback is per played request, not one callback for every path in
the constructor's loading list. `FUN_001CE410` supplies player `+0x94` to
`FUN_001A0890`, and `FUN_001A0120` invokes it on its stop/teardown path before
returning. [CCS runtime](../game/files/ccs_runtime.md#request-table-source)
establishes that all 184 retail SINF rows have zero or one stream request;
the extra `0x1000` main/body paths are resident loads, not additional played
requests. They therefore cannot manufacture two cleanup credits merely by
being extra paths. The [per-request lifecycle](../game/files/ccs_runtime.md#per-request-lifecycle-in-playdecode)
and [play task](../game/files/ccs_runtime.md#the-play-task) own the transport
and callback timing. This is a bounded ordinary skill-player lifetime, not
a duplicate-call guard inside `FUN_0035B3B0`.

**Contradiction to an automatic double-credit interpretation:** the normal
connecting-hit route `FUN_00244F80` requires the same record's
`+0x14 & 0x00010000` **clear**, along with its hit-provenance gates, before
calling `FUN_00216EA0` and selecting the Ultimate presentation. Thus an
unchanged active record cannot pass both the inspected marker caller and the
ordinary connection route. A concrete authored example is Naruto's source
array: slots `4/5/6` secondary words are `0x85/0x85/0x89`, whereas slots
`7/8/9` are `0x10001`; the six records occupy resident
`0x004D9EA0..0x004DA097`. Common selector `FUN_002449C0` updates their
category/name/cost and selects slots `7..9` only for skill class `7`; its
rewrite does not toggle that secondary bit. These bytes demonstrate distinct
record families without proving which skill is selected in every battle.
[Ultimate Jutsu](ultimate_jutsu.md#start) owns the connecting-hit and
presentation chain; [Action commands](action_commands.md#representative-chakrajutsu-path)
owns action selection.

**Inference and remaining lead:** if one marker event and one qualifying
cleanup event do reach the same side within one bank lifetime, their two adds
sum to `+2`; neither producer deduplicates against the other. The scoped
generic caller, selector rewrite, connection route, and retail request-list
checks do not establish a single activation that does so. No supported
same-activation double-credit example was recovered. Establishing one still
requires a concrete authored/scripted transition from the marker-eligible
record to a cinematic-producing route, or another actual end-callback
invocation. This is not evidence that such a route is impossible, and two
independent source sites alone are not evidence that it occurs.

#### Linked Ultimate and support credit

When the selected skill helper returns a value other than `-1` and
`FUN_00372C00` returns `2`, that tail calls live BTL `0x00886B80`.
Its entire body adds one to metric `27` for the supplied side plus one.
The decoded label identifies linked-Ultimate credit.

Live BTL `0x00886A40` adds to `2` only after support notification
deduplication. Identifier zero requires an active object with
`+0x50C & 1` clear; nonzero identifiers use a four-entry ring at
`0x008DCFF0 + side*0x14`, rejecting an existing identifier.
Accepted notification sets the active object's bit when it exists; common
reason-`2` entry clears it. [Support mechanics](support_mechanics.md) owns
ring reset, identifier allocation, and attack lifetime.

Support manager pass `1`, live BTL `0x00886ED0`, consumes constructor
flag `manager+0x20`. Each side's resolved support code is passed to
live `0x00885B70`; a true return adds one to bank `24`, then the flag
is cleared. The predicate scans the `0x86`-byte delimiter table at live
`0x008D1B20`: skip each group's leading byte, match the member code,
return whether its ordinal is greater than zero. Codes `>= 0x44` and
absent codes return false. This proves setup-time combination qualification
without assigning character names to numeric codes. Import uses it to transfer
source `2` to result `25` and zero result `2`; result `24` is then
recomputed as its separate 100-point bonus from contributions `25..27`.

### Inventory snapshot and statistic lifetimes

Resident `FUN_003747C0` writes bank `18` at `0x00374894` when the
observed phase becomes `3` from a phase other than `-1` or `3`, a manager exists, and the
result is `1` or `2`. It selects the winning inventory panel and calls
live BTL `0x0070FE70`. That helper counts occupied entries in exactly
three slots: item code and quantity must both be nonzero. It counts slots,
not quantities; quantity `-1` is occupied. [Battle item inventory](battle_item_inventory.md#na2-panel-layout)
owns the layout. The natural snapshot range is `0..3`, although the
imported floor table also contains thresholds `4` and `5`.

Module initialization at live BTL `0x008D5E60..0x008D5EF0` zeroes both
28-slot banks and registers the destructor. Ordinary startup clears them
through `0x00715F60`; continuation phase `2` preserves them.
Source `18` is overwritten at the phase transition, `17` is set when the
resident combo record rises and max-updated on BTL flush, `7` is overwritten
in both sides by ordinary import, and other audited events add.
No wholesale result-to-source-bank copy occurs in the importer.

Fighter statistics at `+0x4F0` are separate 24 count/max pairs, saved to and
reloaded from per-side block `0x006B31D0 + side*0x2D6` as described in
[Battle lifecycle](battle_lifecycle.md#fighter-statistics-across-reconstruction)
and [Hit response](hit_response.md#hit-count); pair index 13 is detailed under
[Paired-response condition count](#paired-response-condition-count-at-fighter-0x524).
Result import clears its own 28 value/contribution pairs while retaining
descriptor pointers, then reads the selected bank and live fighter HP before
fighter destruction. Reusing that result object resets neither bank nor
fighter pairs.

## Statistic-derived conditions

Resident `FUN_002242D0(fighter)` walks only the configured condition list
and calls `FUN_00223450(fighter,id)`. Return `0` leaves status alone;
return `1` writes status `1`; return `2` writes status `0`.
Raw site `0x00224344` supplies the otherwise omitted success argument
`a2=1`. The status writer can change either direction when the value differs;
there is no universal sticky-success rule. Only explicit case-level status
checks preserve an earlier success.

Its sole direct resident caller, `FUN_001F0B10` at `0x001F0E74`, evaluates
each present fighter after its special KO/time condition assignments and
before unresolved-status completion and the result-`5` scan. This ordering
connects the producers to the result-`5` condition outcome described in
[Match outcomes](match_outcomes.md#terminal-detector-and-classifier), without
changing the ordinary KO/time classifier.

For the tables below, **E** means fighter `+0x62 & 1` is set, the terminal
condition gate. “Threshold” cases return success as soon as their predicate
holds; while below threshold they wait, then fail on E. “Avoid” cases fail
immediately once their disallowed count/threshold is reached; otherwise they
wait, then succeed on E. All listed fighter counter reads are signed halfwords.
A bare numeric field does not imply a recovered player-facing condition name.

| Condition ID(s) | Statistic or predicate | Evaluation |
| --- | --- | --- |
| `0x0C/0x0D/0x0E` | Own chakra `+0x70 >= 5/10/15` | End-only success/failure on E. |
| `0x0F` | Own HP `+0x6C <= 0.1` | End-only. |
| `0x10/0x11/0x12` | Own HP `>= 0.3/0.5/0.8` | End-only. |
| `0x13/0x14` | Opponent HP `<= 0.3/0.5` | End-only. |
| `0x15` | Own `+0x4F4 == 0` | Avoid any nonzero count. |
| `0x16` | Own jump-event count `+0x518 == 0` | Avoid any nonzero count. |
| `0x17` | Own `+0x50C == 0` | Avoid any nonzero count. |
| `0x18` | Own Ultimate action-marker count `+0x514 != 0` | Fail immediately; success is assigned by the separate terminal default in [Match outcomes](match_outcomes.md#terminal-detector-and-classifier). |
| `0x19` | Own guarded-hit count `+0x53C < 1` | Avoid one or more guarded hits. |
| `0x1A` | Opponent Ultimate action-marker count `+0x514 > 0` | Fail immediately; separate terminal default supplies success. |
| `0x1B` | Own accepted-hit count `+0x538 < 1` | Avoid one or more ordinary accepted hits. |
| `0x1D` | Own `+0x4F8 == 0` | Avoid any nonzero count. |
| `0x1E` | Own accepted-action count `+0x4F0 == 0` | Avoid any nonzero count. |
| `0x1F/0x20` | Own surface-movement maximum `+0x546 / 60 >= 4/6` | Threshold. |
| `0x21` | Own input/debit-path maximum `+0x542 / 60 >= 60` | Threshold. |
| `0x22/0x23` | Own gated sequence maximum `+0x54A / 60 < 1/3` | Avoid converted count `>= 1/3`. |
| `0x24/0x25` | Own substitution count `+0x51C >= 3/6` | Threshold. |
| `0x26` | Own paired-response count `+0x524 >= 3` | Threshold; producer and continuation lifetime below, retail condition name unresolved. |
| `0x27` | Own recovery-event count `+0x520 >= 3` | Threshold. |
| `0x28/0x29` | Own record-category count `+0x500 >= 3/6` | Threshold. |
| `0x2F..0x38` | Own combo maximum `+0x54E >= 5,10,15,20,25,30,35,40,45,50` | Threshold, in ID order. |
| `0x39/0x3A` | Opponent recovery-substate count `+0x52C >= 3/6` | Threshold. |
| `0x3B` | Own taunt count `+0x530 != 0` | Immediate success; zero fails on E. |
| `0x3C` | Own awakening count `+0x534 != 0` | Immediate success; zero fails on E. |
| `0x40` | Support creation counter returned by live `0x00886C20(side)` is nonzero | Immediate success; zero fails on E. |

The five `FUN_001EBB70` calls divide the signed halfword by `60`,
truncating toward zero. [Timer primitives](../runtime/timer_primitives.md#integer-time-unit-conversion)
owns this arithmetic. These comparisons do not establish seconds or scheduler
frequency. Surface handler `FUN_0022E320` increments current `+0x544`
and raises maximum `+0x546`; exit `FUN_0022E5D0` clears the current
field while retaining its maximum. [Movement](movement_and_physics.md) owns
the `ACT_WMV_0..2` family. `FUN_00249D70` increments `+0x540` and
raises `+0x542` inside its admitted input/affordability path. Its surrounding
guards differ from its chakra-debit guards, as documented in
[Chakra and guard](chakra_and_guard.md); the statistic is not proof of a debit
on every counted invocation. `FUN_0024D5E0` clears current `+0x548` for
its auxiliary-state gate or major `7/8`; otherwise its role, exchange, BTL
predicate, and E gates control increment and max update `+0x54A`.
That establishes a gated sequence count, without a recovered UI name.

Other count producers explain why these condition fields are not aliases for
the 28 result metrics. Accepted record dispatch `FUN_0023A9A0` increments
`+0x4F0` only when record `+0x10 & 2` and `+0x14 & 0x10000` are clear;
its indexed category path maps record `+0x10 == 0x1000` to pair
`+0x500/+0x502`, and `0x40000/0x80000` to `+0x50C/+0x50E`.
Its separate `+0x4F8` path depends on record `+0x14/+0x1C` masks.
Action exit `FUN_00238D00` has a separately guarded `+0x4F4` increment.
These are exact record/exit classifications, not proof that the corresponding
condition texts say “normal attack,” “miss,” or “support.”

Jump impulse handler `FUN_0022FAD0` increments `+0x518`.
Recovery entry `FUN_0022AAB0` increments `+0x520`; additional direct
stores occur in `FUN_0022AF10` and `FUN_00233870`.
Recovery substate `0x61` handler `FUN_00235C60` increments `+0x52C`.
[Hit response](hit_response.md) owns recovery and accepted/guarded hit paths;
their counts use the same current/max saturation contract as the other fighter
pairs and are suppressed by E.

### Paired-response condition count at fighter +0x524

**Observation:** resident `FUN_00221120` supplies the concrete producer for
pair index `13`: calls `0x00221294` and `0x002212A8` pass `(fighter, 0x0D, 0)`
to `FUN_00223140` for the local fighter and its paired fighter at `+0x20`.
The default pair base is `+0x4F0`, so these update current `+0x524` and
high-water `+0x526`. Each helper independently rejects fighter `+0x62 & 1`,
increments the signed current halfword, caps a valid rising count at `9,999`,
and raises the maximum only when the new current count exceeds it. Neither
call publishes a BTL result-bank metric. Condition `0x26` reads the current
count, not `+0x526`, and requires at least three; below three it waits until
the terminal gate E, then fails.

The producer runs after both response-state entries and their coordination
call. Its sole direct resident caller is `FUN_0021ED70` at `0x0021F2AC`:
the earlier special arbitration must not have consumed the pair, both attack
records must exist, the local incoming/outgoing flags `1` and `0x100` must
both be set, and neither fighter may have a positive `+0x230` countdown.
It then clears the ordinary pair flags after recording the responses.
[Hit response](hit_response.md#accepted-hit-rejection-countdown) owns that
arbitration and response eligibility; [Damage](damage.md#simultaneous-hits-and-knockout-boundaries)
owns the later damage path. Here the counted event is the admitted paired
response, not proof of two HP debits or a double knockout. The two increments
can differ when only one fighter has E set.

**Lifetime:** fighter initialization `FUN_00214A40` calls `FUN_00222F00` at
`0x00214E9C`. That helper clears all 24 local current/max pairs, clears their
side backing pairs only when `FUN_001EC2C0()` is false, then calls
`FUN_002230A0` to copy the backing pairs into the fighter. The predicate is
exactly continuation phase `0x00607678 == 2`. Index 13 therefore reloads
backing offsets `+0x34/+0x36` in
`0x006B31D0 + (fighter[+0x60]&1)*0x2D6`. Cleanup `FUN_00215720` calls
`FUN_00223040` at `0x00215740` before destroying fighter internals; that
copies both halves back. An ordinary construction clears this count and its
maximum; a phase-2 reconstruction preserves the saved pair. The condition
status table has its separate type/route reset exception described in
[Terminal detector and classifier](match_outcomes.md#terminal-detector-and-classifier), so
preserved fighter counts and preserved condition status are not identical
contracts.

**Bounds:** encoded helper-call searches found six physical resident calls to
`FUN_00223140` and no direct BTL calls; only the two paired-response calls use
index 13. The aligned `+0x524` immediate reads in the scoped resident image
include the condition evaluator, while the inspected BTL occurrences are
actor motion/configuration words rather than this fighter halfword. This
establishes the concrete direct producer and lifecycle, not the absence of
unrestricted indirect writes or computed pair indices. No exact in-scope
retail condition string was joined to ID `0x26`; calling it a player-facing
"simultaneous hit" condition would exceed this evidence.

### Terminal provenance predicates

The remaining implemented cases in `FUN_00223450` consume terminal flags
and retained attack/source records rather than a result-bank count. Cases
`5/6/9/0x0B` require E and opponent `+0x61 & 8` clear. Their attack is
opponent `+0x7CC`, falling back to `+0xA54`; their source is
opponent `+0x7C8`, falling back to the opponent itself.

| ID | Success predicate / preservation |
| ---: | --- |
| `5` | Source category `+0x0C == 0` and attack `+0x10 & 0xF00` nonzero; otherwise fail. |
| `6` | Opponent `+0x830 == 0`, excluding source category `0` with attack `+0x14 & 1` and `+0x10 & 0xF00`; otherwise fail. |
| `8` | On E, own `+0x63 & 0x20` succeeds; absent bit fails only if prior status is not already `1`. |
| `9` | Source category `0` and attack `+0x10 & 0xF0000`; failing provenance preserves prior status `1`, otherwise fails. |
| `0x0A` | On E, opponent `+0x61 & 8` clear and opponent chakra `<= 0`; otherwise fail. |
| `0x0B` | Source category `2`; failing provenance preserves prior status `1`, otherwise fails. |

These exact predicates do not supply the absent condition menu strings.
ID `7` and the terminal assignments for `1..4` are described in
[Match outcomes](match_outcomes.md#terminal-detector-and-classifier). IDs without a switch case return zero from this
evaluator; that does not mean they lack an external producer.

### Direct overlay condition events

The already inventoried BTL condition calls also have these producer meanings:

- Live `0x00713680` is the distinct used-code tracker described in
  [Battle item inventory](battle_item_inventory.md#dispatch-and-consumption-boundary);
  its third unique code writes condition `0x2A = 1`. Its initializer at live
  `0x007135C0` clears list, counter, and flags; its callers are live
  `0x00711670/0x007116B0/0x007116CC`; and resident item-manager constructor
  `FUN_00373AB0` allocates it and owns it at manager `+0x80`, separate from
  the inventory panels.
- Live `0x00713770` uses its one-shot `+0x7D` flag, checks the relevant
  primary fighter, obtains each side's inventory panel, and writes condition
  `0x2B = 1` when all three item slots are occupied. This shares the
  occupied-slot predicate of metric `18`. Its sole direct resident call,
  `0x003748E8`, is in the same phase-`3` branch, after metric `18` is sampled
  and the item-object list is removed. It can check both sides, whereas
  metric `18` writes only the selected winner's bank.

### Direct BTL condition-status writers

One BTL producer family is exact. Live `0x006C3250` (raw `0x00F350`, preserved
bytes at `0x006C3210`), called at live `0x006C1868`, checks configured IDs
`0x2C`, `0x2D`, and `0x2E`. It reads the manager-selected side's BTL metric
bank index `19` and writes condition status `1` when the count has reached
`3`, `5`, or `7`, respectively. This proves a BTL-stat-to-condition handoff;
it does not establish the player-facing names of those conditions or imply
that status zero always means the same thing for every condition ID.

A full direct-call scan of clean BTL finds ten `jal 0x001FD850` status-writer
sites in executable functions. The first three are the threshold family above;
the other seven close these additional mechanical producer paths:

| Live call (raw offset) | Status write and proven trigger |
| ---: | --- |
| `0x006C3308` (`0x00F408`) | Selected side, ID `0x2C`, value `1` when metric `19 >= 3` |
| `0x006C3340` (`0x00F440`) | Selected side, ID `0x2D`, value `1` when metric `19 >= 5` |
| `0x006C3378` (`0x00F478`) | Selected side, ID `0x2E`, value `1` when metric `19 >= 7` |
| `0x00713744` (`0x05F844`) | Side argument plus one, ID `0x2A`, value `1` when live helper `0x00713680` inserts a previously unseen nonzero token and its counter at object `+0x74` becomes exactly `3` |
| `0x00713854`, `0x00713924` (`0x05F954`, `0x05FA24`) | Side `1` or `2`, ID `0x2B`, value `1` when all three inventory slots have nonzero item codes and quantities; live helper `0x00713770` checks once per tracker, guarded by byte `+0x7D` |
| `0x0072F304` (`0x07B404`) | Side returned by live `0x00734130` plus one, configured ID `9` or `0x0B`, value `1`; ID `9` requires object signed halfword `+0x24A != -1`, while ID `0x0B` requires byte `+0x284 == 1` |
| `0x0076A720` (`0x0B6820`) | Object's zero-based side index plus one, ID `0x18`, value `0`, when that index equals manager selector `+0x18` |
| `0x0076A744`, `0x0076A760` (`0x0B6844`, `0x0B6860`) | Opposite side, ID `0x1A`, value `0`, when the same zero-based index differs from manager selector `+0x18` |

The last three calls are inside live function `0x00769790`; its side index is
the signed byte at `*(object+0x08)+0x0C`. Unlike the value-`1` satisfaction
writes, their value `0` is directly eligible for `FUN_001FCF00`'s outcome-`5`
scan when the corresponding ID is configured and the target side is active.
No other direct condition-status-writer call occurs in clean BTL. This is a
direct-call result; it does not exclude an indirect call or resident producer.

## BTL score, tier, and point-accumulator handoff

The two-side source bank at BTL BSS `0x008D6A80` is managed by these live
overlay wrappers:

| Live entry | Raw file | Operation |
| ---: | ---: | --- |
| `0x00715F60` | `0x062060` | Clear both sides' 28 signed-16 metric slots |
| `0x00715F90` | `0x062090` | Add a signed-16 delta to `(side, metric)` |
| `0x00715FD0` | `0x0620D0` | Set `(side, metric)` |
| `0x00716010` | `0x062110` | Replace `(side, metric)` only when the new signed value is greater |
| `0x00716050` | `0x062150` | Read `(side, metric)` as signed-16 |

Each wrapper converts one-based side `1..2` to a zero-based record and uses a
`0x38`-byte side stride. `FUN_001EC3B0` is the resident caller of the clear
wrapper while creating a new inner battle-cycle object. Clean BTL itself has no
direct call to either clear or set. Resident code does call set at
`0x00223428` for metric `17` and at `0x00374894` for metric `18`; the remaining
scoped producers use add or max-update. The result-`8` continuation phase
([Match outcomes](match_outcomes.md#higher-level-sequence-counter-and-result-8-continuation))
is the verified new-inner-cycle reset exception.

The underlying storage operations are unsaturated signed-16 arithmetic. Add
sign-extends its input to 16 bits, adds it to the signed-16 slot, and stores the
low halfword; set stores the supplied low halfword; max compares the current
sign-extended halfword with the supplied integer before storing the latter's
low halfword. The wrappers do not validate side or metric ranges, so their
documented `1..2` / `0..27` domains are caller contracts rather than enforced
bounds.

The score bank is not wholesale-cleared by the state-`3` timer reset,
state-`0x10` metric import, or state-`0x11` resource teardown. A state-`0x15`
or `0x16` restart initially remains in the same outer controller, but it later
passes through state `0x0E`; `FUN_001EC3B0` then clears the bank before creating
the next inner battle-cycle object unless continuation phase is `2`. The bank
therefore has an ordinary inner-cycle/sample lifetime, with an explicit
result-`8` preservation exception, rather than an unconditional outer-controller
lifetime. The importer has one proven bank side effect before that boundary:
on its normal non-timeout/non-special-time path it writes computed remaining
whole units to metric slot `7` in both side records at live `0x008D6A8E` and
`0x008D6AC6`.

The six-word session outcome block has the longer lifetime: it resets only in
initial outer state `2` and is updated after each completed cycle. The reusable
BTL result object has the outer controller's allocation lifetime, but its
metric values and presentation internals are cleared/rebuilt per result
presentation; it is a transformation of the source bank rather than its owner.

The outer controller calls live `0x00719580` after the end presentation but
before state-`0x11` resource teardown. The BTL result object contains a
28-entry metric-record array beginning at `+0x14`, with `0x0C` bytes per
record: descriptor pointer at `+0x00`, value at `+0x04`, and contribution at
`+0x08`. Thus metric values begin at object `+0x18` and contributions at
object `+0x1C`. The importer clears every value/contribution pair, obtains the
latched result with resident `FUN_001EC280`, and chooses a side record as
follows:

```text
selected_side = (result == 1) ? 1 : 2
```

This exact condition means draws and special result `5` select the side-2
record. It is not evidence that side 2 “won”; it is simply the importer branch
used by flows that reach it. Outer state `0x10` imports results `1..5`, but
state `0x12` only permits its field-qualified result `1` or `2` paths to create
the score presentation. Therefore an imported draw, double-zero, or result-`5`
sample is not subsequently committed through this result screen in the proven
outer flow.

The source records are two `0x38`-byte runtime records beginning at BTL BSS
`0x008D6A80`. Twenty-eight initial metric values are copied for the selected
side and then several are recomputed/bucketed. The generic weighted helper at
live `0x00719A60` uses descriptor byte `+0x04` to select a signed-16 cap from
live `0x008C3CB0`, applies that cap only as an upper bound (there is no lower
floor in the helper), and stores
`descriptor_signed_i16[0] * capped_value` as its contribution. The beginning
of that cap/rank table is `999, 99, 100, 0, 0, 300, 450, 550, 700`.

The 28 descriptors themselves begin at live `0x008C3DE0` (raw
`0x20FEE0`), stride `0x0C`. The coefficient and cap-selector bytes used by the
weighted helper are:

| Metric indices | `(coefficient, cap selector -> maximum)` |
| --- | --- |
| `0` | `(5, 0 -> 999)` |
| `1` | `(100, 1 -> 99)` |
| `2` | `(10, 0 -> 999)` |
| `3` | `(5, 0 -> 999)` |
| `4` | `(10, 0 -> 999)` |
| `5` | `(1, 0 -> 999)` |
| `6` | `(5, 0 -> 999)` |
| `7` | `(1, 1 -> 99)` |
| `8` | `(1, 2 -> 100)` |
| `9` | `(50, 0 -> 999)` |
| `10` | `(100, 1 -> 99)` |
| `11` | `(5, 0 -> 999)` |
| `12` | `(5, 0 -> 999)` |
| `13` | `(0, 0 -> 999)` |
| `14`, `15` | `(100, 1 -> 99)` |
| `16` | `(10, 1 -> 99)` |
| `17..24` | `(0, 0 -> 999)`; their relevant custom helpers replace the generic contribution |
| `25` | `(20, 0 -> 999)` |
| `26` | `(100, 0 -> 999)` |
| `27` | `(400, 1 -> 99)` |

The importer then performs these verified overrides:

- metric index `7`: configured limit minus elapsed whole units, clamped to
  zero; auxiliary flag `0x00607674` and one mode/configuration combination
  force it to zero;
- metric index `8`: selected fighter HP multiplied by `100` and converted to a
  word with MIPS `cvt.w.s` (there is no explicit `trunc.w.s`); HP below `0.05`
  receives an additional one after that conversion;
- metric index `5`: selected-side record signed-16 value at `+0x22`;
- metric index `17`: the same `+0x22` source through floor table
  `0x008C3CD0`;
- metric index `18`: selected-side record `+0x24` through floor table
  `0x008C3D10`;
- metric index `19`: selected-side record `+0x26`, contributing `50` when at
  least one;
- metric index `20`: selected-side record `+0x28`, contributing `20` when at
  least one;
- metric index `21`: forced to zero;
- metric index `22`: elapsed whole units through ceiling table
  `0x008C3D30`; timeout marker `0x00607674`, or the conjunction of manager
  mode `2` and configuration selector `6 == 100`, forces it to zero;
- metric index `23`: selected HP integer, contributing `500` when at least
  `100`;
- if selected-side record `+0x30` is nonzero, metric `25` receives record
  `+0x04` and metric `2` is forced to zero; and
- metric index `24` contributes `100` when any of metrics `25`, `26`, or `27`
  has a positive contribution, otherwise zero.

The encoded bucket rows are exact pairs of `(threshold, contribution)`:

| Live table | Selection rule | Rows |
| ---: | --- | --- |
| `0x008C3CD0` | Last threshold `<=` input | `(30,50)`, `(40,100)`, `(50,200)`, `(60,300)`, `(70,400)`, `(80,500)`, `(90,1000)` |
| `0x008C3D10` | Last threshold `<=` input | `(2,10)`, `(3,20)`, `(4,30)`, `(5,50)` |
| `0x008C3D30` | First threshold `>=` input | `(10,400)`, `(20,200)`, `(30,100)` |

These transformations apply to the retail labels decoded above; source-event
counts and imported result values must be distinguished.

Live `0x00719C00` finishes special component caps, sets result object `+0x04`
to zero, and sums the 28 contribution words at
`object + 0x1C + index*0x0C` into that total. Before summing, it sets metric
`9` to `3` when manager `+0x1C == 0`; otherwise it uses
`FUN_001F6EA0(manager) + 1`, where that resident wrapper reads configuration
selector `0x0B`. The value is upper-capped through metric `9`'s descriptor and
weighted by its coefficient `50`. [Battle AI](battle_ai.md#configuration-and-behavior-profiles)
establishes key `0x0B` as the COM Strength level (`0..5`) that selects the AI
profile, and manager `+0x1C == 0` is the no-COM control assignment. Metric `9`
is therefore a COM-strength bonus of `50 * (strength + 1)` points (`50..300`),
with a fixed `150` when neither side is COM. It also sums the contributions of metrics
`14`, `15`, and `16`, writes that sum as metric `13`'s value, and gives metric
`13` no additional contribution because its coefficient is zero. Live
`0x00719ED0` then:

1. initializes the result/tier view;
2. copies resident manager accumulator `FUN_001F6F60(manager)` to object
   `+0x08`;
3. records side `1` only for result `2`, otherwise side `0`, for presentation;
4. invokes the contribution finalizer;
5. clamps object `+0x04` to `9,999`; and
6. computes tier byte `+0x0C` from four signed-16 thresholds.

The encoded live tier table is `0x008C3CBA` (raw `0x20FDBA`), containing
`300, 450, 550, 700`. The resulting tier is:

| Total | Tier byte |
| ---: | ---: |
| `< 300` | `0` |
| `300..449` | `1` |
| `450..549` | `2` |
| `550..699` | `3` |
| `>= 700` | `4` |

No letter/rank names are assigned because this code stores only numeric tier
`0..4`.

Live `0x0071A2C0` is the acceptance/commit function. Its predicate at live
`0x0071A380` checks bit `0x20` in the selected side's runtime input/status
record. Once accepted, it plays event/sound `0x34` and returns `1`. With a live
manager it advances the result-object to state `3` and computes:

```text
new_accumulator = object[+0x08] + object[+0x04]
new_accumulator = min(new_accumulator, FUN_001F7870())
FUN_001F6F00(manager, new_accumulator)
```

`FUN_001F7870()` returns `9,999,999`. `FUN_001F6F60` reads and
`FUN_001F6F00` writes the field at `*(manager + 4) + 0x34`; the writer also
enforces the same maximum. Neither the result-total clamp nor accumulator
writer applies a lower floor. If the manager is absent at acceptance, the
object instead moves directly to state `4` and skips the accumulator write.
The normal routed score path has a live manager, but this distinction is part
of the function's exact contract. The accumulator is the profile's ryo
counter: [Save data](../game/save_data.md) identifies the same getter/setter
pair and its `0x34` field as the saved ryo currency, whose UI formatter
appends `両`. A Free Battle win by a human side therefore adds the capped
result-screen total to ryo. No direct item or unlock grant was found in this
handoff; when that in-memory ryo value reaches the memory card is outside this
document.

The summary dispatcher at live `0x0071A0A0` calls that acceptance function only
once its summary child byte `+0x18` permits acceptance. Before that, native
Circle can accelerate the tally in child states 2 and 3. The details dispatcher
at live `0x0071A1D0` also calls the same acceptance function. The predicate reads
the newly pressed input word at `input_context + 0x84 + selected_side * 0x78`,
where the result object's `+0x02` halfword is the zero-based selected side.
The call, input mask, and commit stores are at raw `0x0663C0..0x06648F`.

The surrounding result object has halfword state at `+0x00`, selected-side
halfword at `+0x02`, total at `+0x04`, pre-result accumulator at `+0x08`, tier
byte at `+0x0C`, and fade handle at `+0x10`. Live dispatcher `0x00719D80`
implements states `0..5`: state `0` runs total/tier initialization and enters
`1`; states `1` and `2` update the two result subobjects and can invoke the
accept/commit function; state `3` waits for a fade and enters `4`; dispatcher
state `4` returns completion value `1`; and state `5` returns value `2`.

Resident `FUN_001EE9C0` accepts only dispatcher return `1`. After resource
readiness, it clears the metric object through live `0x00719500`, destroys it
current presentation internals through live `0x00719140`, unloads the
associated result resource, and moves the outer controller from state `0x14`
to `0x15`. It does not free or clear the `0x188`-byte allocation stored at
controller `+0x3C`; later cycles reuse it. Controller teardown
`FUN_001EC890` calls `0x00719140` again, then frees the allocation through
`FUN_00117000` and clears `+0x3C`. Thus the accumulator write occurs before
presentation teardown, and the result object is not the persistent owner of
the committed total.

Dispatcher state `5` returns `2`, but the resident owner does not treat `2` as
completion and remains in outer state `0x14`. No direct write of `5` to result
object halfword `+0x00` was found in the constructor, clear/import functions,
dispatcher state handlers, or resident owner: the verified writes are states
`0..4`. Consequently state `5` and return `2` are a recognized interface branch
whose scoped reachability is unproven, not a second proven cleanup route.
