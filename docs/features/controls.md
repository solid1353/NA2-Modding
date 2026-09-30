# Controls

`features.general.new_controls` owns the default binding map, the extended
Control Settings editor, and the battle input for the added actions. It is
independent of the substitution gauge and of Extended Items.

## Actions

| Index | Action | Storage |
| ---: | --- | --- |
| `0..3` | Native face-button actions | Native profile |
| `4` | Native Item Select | Native profile |
| `5` | Linked Attack | Native profile |
| `6` | Guard/Sub 1 | Native profile |
| `7` | Guard/Sub 2 | Native profile |
| `8` | Guard | Save appendix |
| `9` | Substitution | Save appendix |
| `10` | Item Select L | Save appendix |
| `11` | Item Select R | Save appendix |
| `12` | Unbound | Editor only; the button stores no binding |

Guard/Sub 1 and 2 are the two native combined actions. Either one blocks and
substitutes; the added Guard action only blocks, and the added Substitution
action only substitutes. Item Select L moves the battle-item selection to the
next item, like native Item Select, and Item Select R moves it to the previous
item. Native Item Select and Guard/Sub 1 and 2 cannot be chosen in Control
Settings, but a binding already stored in the native profile keeps working.

[`@builder/resources/default_controls.tsv`](../../na228_builder/resources/default_controls.tsv)
defines the default layout for both players as one action per button. It
binds L1 to Substitution, R1 to Guard, L2 to Item Select L, and R2 to Item
Select R, with the retail face-button actions; native Item Select, Linked
Attack, and both Guard/Sub actions start unbound. The builder rejects an
unknown button or action, an action used twice, and a face action on a
shoulder button or the reverse. It generates three tables from the file: the
native-action button masks, which the resident and BTL default readers use
instead of the retail tables; the rows that the Control Settings Select reset
restores; and the initial added-action bindings, which are also the save
defaults.

## Control Settings editor

Face-button rows step through Unbound, Attack, Ultimate Jutsu Prep, Item Use,
and Jump, the order in which the default rows appear.
Shoulder rows step through Unbound, Substitution, Guard, Item Select L, Item
Select R, and Linked Attack. In both orders Right moves forward, Left moves
back, and both wrap. Native Item Select and Guard/Sub 1 and 2 are not in the
order. A row holding an
action outside its order moves to Unbound on its first step. The native
assignment helper couples its two Guard choices, so the feature replaces it
with a single-choice assignment: choosing an action already on another button
makes that button Unbound. Any number of buttons can be Unbound.

The editor reconstructs its eight button rows from the native action masks and
the four added masks for each player; a button with no binding opens as
Unbound. Confirmation writes the original eight actions, including both
Guard/Sub bindings, to the native profile and stores the added Guard,
Substitution, Item Select L, and Item Select R masks in the save appendix. Unbound buttons
write nothing, so their actions keep a zero binding. This avoids the native
confirmation loop, which indexes an eight-entry array by action ID.

The native action-label table holds only eight pointers. The feature redirects
its renderer to a thirteen-pointer table and supplies localized labels for the
two Guard/Sub actions, Substitution, Item Select L, Item Select R, and Unbound. On
opening Control Settings, the new table takes its first pointer from the native
table, whose Ultimate Jutsu Prep entry may be redirected by the English
translation importer.

## Battle input

After the attack's native timing admission, the held-input shortcut checks only
the added Substitution binding. Both native Guard/Sub bindings preserve the
vanilla 16-frame held-Guard limit and enter through the buffered input-history
search. Zero bindings are skipped so an unbound action cannot pass the history
match. The BTL translator retains both native Guard/Sub actions as block sources
and adds the separate Guard binding. The added Guard action cannot substitute;
the added Substitution action cannot block.

Item Select L and R use the same pressed-button mask as native Item Select.
The translator delivers Item Select L as the native item-select input
`0x02000000`, so the native advance runs unchanged, and Item Select R as
fighter input `0x04000000`, which retail never
produces from player input; the native fighter input gate already routes that
bit to resident `0x00375570`. The feature replaces `0x00375570` with a reverse
step that uses the native advance gates, subtracts `1.0` from the wheel
animation offset, steps one occupied slot back, and plays the native select
sound. It does not set the native badge's press flag at panel `+0x62`. When both
item-select actions are pressed on one frame, the native gate handles Item
Select L. The retail input path is
documented in
[Battle item inventory](../knowledge/gameplay/battle_item_inventory.md#na2-selection).

The feature replaces the native item-select badge draw. Retail reads the badge's
binding for P1 on both panels, so P2's badge would show P1's button; the
feature reads each panel's own Item Select L and R bindings instead. Each badge
is drawn only while its action is bound, so an unbound Item Select L leaves no
empty frame. The Item Select L badge keeps the native position and press
animation.

While Item Select R is bound, its button badge mirrors the Item Select L badge
across the wheel: with the native badge position, bottom-right of the wheel for
P1 and bottom-left for P2. [Extended Items](battle.md#extended-items), when on,
moves Item Select L to the left for both players, so Item Select R is then on
the right. Both
badges use the native badge frame (`0x7B`) and the native button-sprite table
at `0x005B00B0`, and both are drawn just before the wheel. While fewer than two
items are held, both badges, frame and button, are drawn with opacity `0.2`, as
in NUN4. Retail NA2 instead keeps the frame opaque and draws only the button
at `0.8`.
Item Select R has its own press animation with the native badge's timing: a
press shrinks it by `0.1` per frame down to `0.8`, and it recovers by `0.1` per
frame to `1.0`. Reverse select drives only this animation, so each badge reacts
only to its own button.

The native support-bar draw uses Linked Attack at index `5`, so it shows no
button while Linked Attack is unbound. The independent substitution gauge draws
no button prompt.

## Builder hook map

Use `general.new_controls` in `@builder/patches/general/general.json`. Its
guarded entries are:

| Purpose | Target/offset | Behavior |
| --- | --- | --- |
| Controls entry help | ELF `0x287C5C` | Queue the instruction during the shared Controls reset, before the banner's first draw |
| Default layout readers | ELF `0xE7B2C`, `0xF3EF4`, `0xF3F54`; BTL `0x3B888` | Point the three resident readers of the retail defaults at `0x005C06A0` and the BTL reader of `0x00898150` at the generated native-action masks |
| Select reset | ELF `0x28818C` | Replace the retail reset copy from `0x005D5250` with the generated rows |
| Open and commit | ELF `0x287A50`, `0x288044` | Read/write native masks and the added masks for each player |
| Assignment | ELF `0x287C90`, `0x287FBC` | Make the button that held the chosen action Unbound; keep Guard/Sub 2 when the selector opens |
| Selector order | ELF `0x2883DC`, `0x2883F8` | Step face and shoulder rows through their fixed action orders |
| Action labels | ELF `0x288830`, `0x288834` | Draw from the thirteen-action localized label table |
| Held and buffered substitution | ELF `0x129720`, `0x12973C` | Give added Substitution its held-input shortcut; apply the vanilla held-Guard limit to both native Guard/Sub bindings |
| Logical Guard and zero bindings | BTL `0x3C02C`, `0x3B8F0` | Add separate Guard alongside both native Guard/Sub bindings and prevent unbound matches |
| Item Select L and R input | BTL `0x3C6AC` | Set fighter input `0x02000000` for an Item Select L press and `0x04000000` for an Item Select R press, then reproduce the displaced `0x40000000` step |
| Reverse item select | ELF `0x275670` | Replace resident `0x00375570` with the reverse step |
| Item-select badges | BTL `0x5E950`, `0x5EA88` | Branch past the native badge draw; draw the bound Item Select L and R badges for the panel's side, then call the native wheel draw |

The logical-Guard bridge preserves the translator's accumulated input mask
while it checks native Guard/Sub 2 and the added Guard binding. Eight appendix
values store added Guard, Substitution, Item Select L, and Item Select R for
each player.

| Purpose | Canonical location |
| --- | --- |
| Editor, bindings, and input | `@builder/patches/general/new_controls/control_settings.c` and `control_settings_abi.S` |
| Default layout | `@builder/resources/default_controls.tsv`, read by `@builder/patches/general/new_controls/control_defaults.py` |
| Appendix fields | `@builder/resources/save_appendix.tsv` and `@builder/patches/memory_card/save_appendix.py` |
| Control Settings ownership and composition tests | `tests/na228_builder/test_control_settings.py` |

## Remaining runtime validation

| Scenario | Expected observation |
| --- | --- |
| Control Settings | Face rows cycle Unbound, Attack, Ultimate Jutsu Prep, Item Use, Jump; shoulder rows cycle Unbound, Substitution, Guard, Item Select L, Item Select R, Linked Attack; assigning an action already on another button makes that button Unbound; Select restores L1 Substitution, R1 Guard, L2 Item Select L, and R2 Item Select R for both players |
