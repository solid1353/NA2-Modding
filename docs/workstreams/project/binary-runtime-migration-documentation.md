# Binary and runtime migration documentation
This document preserves review material removed from executable builder data during the integrated catalog migration.
## localization: binary_patcher
### Selectable node `localization.font_glyphs`
Description: Static native-font glyph, metric-table, and geometry inputs.
### Selectable node `localization.font_layout`
Description: Static font layout, contextual presentation, alignment, and formatting call-site inputs.
### Selectable node `localization.font_numeric_formatting`
Description: Static ASCII numeric-formatting data and call-site inputs.
### Selectable node `localization.ui_layout`
Description: Localized graphical UI layout and geometry.
### Selectable node `localization.regional_input`
Description: Regional menu, overlay, setup, result, and audio input behavior.
#### Patch `localization.font_glyphs.font_glyphs_native`
Legacy ID: `font_glyphs_native`
Name: Native NUN5 secondary font data and static geometry
Description: Use NUN5's native 14x20 raster geometry and packed metrics for every same-semantic English glyph, reconstruct unsupported punctuation from clean NA2, preserve clean GF4C, bound the secondary atlas, and use descriptor height only for the secondary glyph quad.
Evidence ID: `NUN5-GF4-NATIVE-14X20`
Review notes: Runtime: Runtime-proven across matched Controls, Practice, Save/Load, and character-modal captures. The final guarded Controls run on worker ISO CRC 9B7C20AE retained the accepted 24x28 presentation, width, spacing, bearing, and fit behavior; median height and center-Y deltas against NUN5 were both zero. | Generated from hash-pinned clean NA2 and official NUN5 only. Composition-time C in the runtime injector now owns packed-metric decoding and horizontal leading-bearing scaling. Fullwidth Shift-JIS Save/Load digits remain on the primary 24-pixel path. The rejected m01, palette-swap, 10x22 resample, global-parser, and shared 28x28 approaches are not implementation parents.
#### Patch `localization.font_layout.font_layout_character_modal`
Legacy ID: `font_layout_character_modal`
Name: Character-modal alignment
Description: Use independently measured local X positions for all five Back to Game Mode Screen modal rows and place the structural fifth-row footer at local Y 115.
Evidence ID: `NUN5-CHARACTER-MODAL-MATCHED-CAPTURES`
Review notes: Runtime: captures 50 and 51 isolate and verify the fifth row in both draw states. The shared producer moves from local Y 116 to 115; the selected renderer changes its own compensation from -2 to -1 so its final position remains unchanged, while the ordinary footer moves up one local unit. Rows one through four retain their existing coordinates. The regenerated integrated capture history was accepted for publication on 2026-08-03.
#### Patch `localization.font_layout.font_layout_linked_mode_modal`
Legacy ID: `font_layout_linked_mode_modal`
Name: Linked Mode selector vertical alignment
Description: Match the dedicated Linked Mode title and both selector rows to NUN5 with one local title origin and one shared choice base and interval; the paired runtime hook owns the centered width correction and selected color.
Evidence ID: `NUN5-LINKED-MODE-VERTICAL-MATCH`
Review notes: Static: main-ELF FUN_003B8F40 owns the center modal independently of the adjacent five-row family. The current candidate retains title Y 8 and shared formula 45 + 22*i, while both draw states share the centered 1.05 scale session. | Runtime: final-red captures 18 and 19 show red selected Auto and Manual with accepted geometry and no large Font discrepancy. Every unrelated list and renderer path remains native; explicit user acceptance is pending.
#### Patch `localization.font_numeric_formatting.font_numeric_save_load_separator`
Legacy ID: `font_numeric_save_load_separator`
Name: Save/Load ASCII time separators
Description: Replace the Save/Load-only fullwidth time colon with ASCII colon; the compiled-C runtime package owns all numeric formatting behavior.
Evidence ID: `NUN5-SAVE-LOAD-EU-DATETIME`
Review notes: Runtime: resident | The user accepted the ASCII Save/Load result and EU order. This declarative patch now contains only the local separator constant; six symbolic call-site hooks and all DD/MM/YYYY, two-digit, and 99-hour behavior live in the runtime injector.
#### Patch `localization.font_layout.font_layout_on_off_context`
Legacy ID: `font_layout_on_off_context`
Name: Practice Settings title-case ON/OFF selection
Description: Route the Commands, Damage, and Guide Ninja Sound Practice Settings rows to the existing title-case Off/On selector table.
Evidence ID: `NUN5-ON-OFF-CONTEXT-SPLIT`
Review notes: Runtime: The three Practice Settings selector rows only; user-verified working. | Special Controls already receives ASCII Off/On from canonical T1956/T1957 mappings, so no Special renderer or table redirect is retained. Three guarded BTL row pointers keep Practice on the title-case table without changing renderer metrics, spacing, scale, or draw calls.
#### Patch `localization.font_layout.font_layout_command_relationships`
Legacy ID: `font_layout_command_relationships`
Name: Command Chart relationship composition
Description: Suppress only the second native Command Chart auxiliary-string draw after the runtime-injector adapter combines both optional relationship strings.
Evidence ID: `NUN5-V2-COMMAND-RELATIONSHIPS`
Review notes: Static: NA2 FUN_0087A700 draws record bytes +4 and +5 separately; NUN5 homolog FUN_00896E70 combines both strings. BTL file 0x1C6ABC is suppressed after the generated-C first-call adapter renders the complete relationship once. | Icon-row positioning is owned by the runtime injector because NUN5 selects distinct offsets for relationship and plain rows. User acceptance is pending.
#### Patch `localization.regional_input.regional_input_candidate_001`
Legacy ID: `regional_input_candidate_001`
Name: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M001`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_001_01, regional_input_candidate_001_02, regional_input_candidate_001_03, regional_input_candidate_001_04. | Review/apply as a handler set with regional_input_candidate_001_01, regional_input_candidate_001_02, regional_input_candidate_001_03, regional_input_candidate_001_05. | Review/apply as a handler set with regional_input_candidate_001_01, regional_input_candidate_001_02, regional_input_candidate_001_04, regional_input_candidate_001_05. | Review/apply as a handler set with regional_input_candidate_001_01, regional_input_candidate_001_03, regional_input_candidate_001_04, regional_input_candidate_001_05. | Review/apply as a handler set with regional_input_candidate_001_02, regional_input_candidate_001_03, regional_input_candidate_001_04, regional_input_candidate_001_05.
#### Patch `localization.regional_input.regional_input_candidate_002`
Legacy ID: `regional_input_candidate_002`
Name: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M002`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_002_01, regional_input_candidate_002_02, regional_input_candidate_002_03. | Review/apply as a handler set with regional_input_candidate_002_01, regional_input_candidate_002_02, regional_input_candidate_002_04. | Review/apply as a handler set with regional_input_candidate_002_01, regional_input_candidate_002_03, regional_input_candidate_002_04. | Review/apply as a handler set with regional_input_candidate_002_02, regional_input_candidate_002_03, regional_input_candidate_002_04.
#### Patch `localization.regional_input.regional_input_candidate_003`
Legacy ID: `regional_input_candidate_003`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M003`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_003_01. | Review/apply as a handler set with regional_input_candidate_003_02.
#### Patch `localization.regional_input.regional_input_candidate_004`
Legacy ID: `regional_input_candidate_004`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M004`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_004_01. | Review/apply as a handler set with regional_input_candidate_004_02.
#### Patch `localization.regional_input.regional_input_candidate_005`
Legacy ID: `regional_input_candidate_005`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M005`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_005_01. | Review/apply as a handler set with regional_input_candidate_005_02.
#### Patch `localization.regional_input.regional_input_candidate_006`
Legacy ID: `regional_input_candidate_006`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M006`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_006_01. | Review/apply as a handler set with regional_input_candidate_006_02.
#### Patch `localization.regional_input.regional_input_candidate_007`
Legacy ID: `regional_input_candidate_007`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M007`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_008`
Legacy ID: `regional_input_candidate_008`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M008`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_008_01. | Review/apply as a handler set with regional_input_candidate_008_02.
#### Patch `localization.regional_input.regional_input_candidate_009`
Legacy ID: `regional_input_candidate_009`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M009`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_009_01. | Review/apply as a handler set with regional_input_candidate_009_02.
#### Patch `localization.regional_input.regional_input_candidate_010`
Legacy ID: `regional_input_candidate_010`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M010`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_011`
Legacy ID: `regional_input_candidate_011`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M011`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_011_01. | Review/apply as a handler set with regional_input_candidate_011_02.
#### Patch `localization.regional_input.regional_input_candidate_012`
Legacy ID: `regional_input_candidate_012`
Name: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M012`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_012_01, regional_input_candidate_012_02. | Review/apply as a handler set with regional_input_candidate_012_01, regional_input_candidate_012_03. | Review/apply as a handler set with regional_input_candidate_012_02, regional_input_candidate_012_03.
#### Patch `localization.regional_input.regional_input_candidate_013`
Legacy ID: `regional_input_candidate_013`
Name: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M013`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_013_01, regional_input_candidate_013_02. | Review/apply as a handler set with regional_input_candidate_013_01, regional_input_candidate_013_03. | Review/apply as a handler set with regional_input_candidate_013_02, regional_input_candidate_013_03.
#### Patch `localization.regional_input.regional_input_candidate_014`
Legacy ID: `regional_input_candidate_014`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M014`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_014_01. | Review/apply as a handler set with regional_input_candidate_014_02.
#### Patch `localization.regional_input.regional_input_candidate_015`
Legacy ID: `regional_input_candidate_015`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M015`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_015_01. | Review/apply as a handler set with regional_input_candidate_015_02.
#### Patch `localization.regional_input.regional_input_candidate_016`
Legacy ID: `regional_input_candidate_016`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M016`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_017`
Legacy ID: `regional_input_candidate_017`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M017`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_018`
Legacy ID: `regional_input_candidate_018`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M018`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_pause_commands`
Legacy ID: `regional_input_pause_commands`
Name: Pause command overlay handler (ccStartMenuPrivateCmd).
Description: Shared Practice and Free Battle command-list and command-chart controller. The complete regional function alignment rotates entry/player routing from Circle to Cross and close from Cross to Triangle without changing battle-input encoding.
Evidence ID: `BTL-M019`
Review notes: Runtime: practice_free_battle_command_overlays | Runtime screenshots isolated both remaining failures to the two ccStartMenuPrivateCmd views. Complete-function comparison maps the reordered NUN5 branches structurally rather than by face-mask ordinal.
#### Patch `localization.regional_input.regional_input_candidate_019`
Legacy ID: `regional_input_candidate_019`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M020`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_019_01. | Review/apply as a handler set with regional_input_candidate_019_02.
#### Patch `localization.regional_input.regional_input_candidate_020`
Legacy ID: `regional_input_candidate_020`
Name: BTL-owned battle-adjacent UI/state input range.
Description: Likely battle setup, pause, result, tutorial, mission, or other BTL-owned menu. Exact runtime screen is unclassified; gameplay-input overlap must be ruled out.
Evidence ID: `BTL-M021`
Review notes: BTL may share these state fields with gameplay. Runtime screen classification is mandatory before approval. | Review/apply as a handler set with regional_input_candidate_020_01. | Review/apply as a handler set with regional_input_candidate_020_02.
#### Patch `localization.regional_input.regional_input_save_load_parent`
Legacy ID: `regional_input_save_load_parent`
Name: Save/load and memory-card parent controller.
Description: Multi-state save/load subsystem controller with six confirm-only branches.
Evidence ID: `ELF-M001`
Review notes: Runtime: Independent runtime test produced no changes anywhere in the tested title/load/save matrix. | The combined M001/M002/M003 test changed load/save menu selection and confirm-save, so M001 may still participate in a multi-handler input path. Do not enable alone or classify as proven.
#### Patch `localization.regional_input.regional_input_save_load_confirmation`
Legacy ID: `regional_input_save_load_confirmation`
Name: Save/load confirmation child handler.
Description: Paired confirm/cancel modal used by the save/load parent controller.
Evidence ID: `ELF-M002`
Review notes: Runtime: Independent runtime test produced no changes anywhere in the tested title/load/save matrix. | The combined M001/M002/M003 test changed load/save menu selection and confirm-save, so M002 may still participate in a multi-handler input path. Do not enable alone or classify as proven.
#### Patch `localization.regional_input.regional_input_save_load_acknowledgment`
Legacy ID: `regional_input_save_load_acknowledgment`
Name: Save/load acknowledgment child handler.
Description: Confirm-to-close/advance prompt used by the save/load parent controller.
Evidence ID: `ELF-M003`
Review notes: Runtime: Independent runtime test produced no changes anywhere in the tested title/load/save matrix. | All three family patches are inert alone while the combined M001/M002/M003 build changed load/save menu selection and confirm-save. Preserve this candidate for later interaction testing; do not enable alone or classify as proven.
#### Patch `localization.regional_input.regional_input_animated_transition`
Legacy ID: `regional_input_animated_transition`
Name: Confirm-gated state transition after an animation/object becomes active.
Description: Front-end transition prompt.
Evidence ID: `ELF-M004`
Review notes: Complete-function review confirms a frontend transition state machine with no active battle-action handling. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_player_transition`
Legacy ID: `regional_input_player_transition`
Name: Player-indexed confirm-gated transition handler.
Description: Multiplayer/front-end transition prompt.
Evidence ID: `ELF-M005`
Review notes: Complete-function review confirms a player-indexed frontend transition state machine with no active battle-action handling. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_timed_prompt`
Legacy ID: `regional_input_timed_prompt`
Name: Two-state timed prompt controller with confirm acceleration/advance.
Description: Timed prompt or result/message transition.
Evidence ID: `ELF-M006`
Review notes: Complete-function review confirms a timed prompt/result transition handler. Apply regional_input_timed_prompt_01 and regional_input_timed_prompt_02 atomically. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_player_list`
Legacy ID: `regional_input_player_list`
Name: Player-indexed list/prompt handler with confirm and directional navigation.
Description: Front-end selectable list.
Evidence ID: `ELF-M007`
Review notes: Complete-function review confirms a player-indexed frontend list/prompt handler with no active battle-action handling. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_selectable_modal`
Legacy ID: `regional_input_selectable_modal`
Name: Generic selectable-list/modal input decoder. It sets distinct result flags for accept, cancel, and navigation.
Description: Shared selectable-list/modal handler used across major front-end menus.
Evidence ID: `ELF-M008`
Review notes: Runtime: Confirmed correct in Collection, Shop, all Free Battle menus, all Practice menus, and the Main Menu leave dialog. | Cross accepts and Triangle cancels correctly in confirmed screens. Save dialog, post-Main-Menu-leave save dialog, and loading remain unchanged and therefore use separate handlers. Master Mode is intentionally out of scope.
#### Patch `localization.regional_input.regional_input_menu_parent`
Legacy ID: `regional_input_menu_parent`
Name: Parent menu state machine wrapping child selectable objects and confirm/cancel transitions.
Description: Front-end selection screen using the generic widget family.
Evidence ID: `ELF-M009`
Review notes: Complete-function review confirms a parent frontend menu state machine. Apply regional_input_menu_parent_01 and regional_input_menu_parent_02 atomically. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_control_assignment`
Legacy ID: `regional_input_control_assignment`
Name: Controller/button-assignment options handler with reset, confirm, cancel, and directional edits.
Description: Controls/options menu.
Evidence ID: `ELF-M010`
Review notes: Complete-function review confirms the controller-assignment UI handler. It changes menu confirmation semantics only; stored battle bindings change solely through the user's normal menu choices. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_numeric_adjustment`
Legacy ID: `regional_input_numeric_adjustment`
Name: Two-axis numeric adjustment handler with reset, confirm, cancel, and directional edits.
Description: Position/calibration-style options screen.
Evidence ID: `ELF-M011`
Review notes: Complete-function review confirms a calibration/options UI handler with no combat-action path. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_four_way_options`
Legacy ID: `regional_input_four_way_options`
Name: Four-way options/submenu handler with confirm/cancel state transitions.
Description: Options or configuration submenu.
Evidence ID: `ELF-M012`
Review notes: Complete-function review confirms an options/submenu state handler with no combat-action path. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_numeric_selector`
Legacy ID: `regional_input_numeric_selector`
Name: Numeric/list selector with confirm, cancel, and vertical navigation.
Description: Options/list modal.
Evidence ID: `ELF-M013`
Review notes: Complete-function review confirms an options/list modal handler with no combat-action path. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_player_join`
Legacy ID: `regional_input_player_join`
Name: Two-player join/selection state machine; the differing checks are cancel/back actions.
Description: Multiplayer player-join or character-selection UI.
Evidence ID: `ELF-M014`
Review notes: Complete-function review confirms a two-player join/selection UI; both edits affect cancel/back checks only. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_five_item_selector`
Legacy ID: `regional_input_five_item_selector`
Name: Five-item selector with confirm, cancel, and cyclic vertical navigation.
Description: Multiplayer/front-end selection list.
Evidence ID: `ELF-M015`
Review notes: Complete-function review confirms a five-item frontend selector with no combat-action path. Approved only for the broad ELF-only runtime test.
#### Patch `localization.regional_input.regional_input_save_load_confirm`
Legacy ID: `regional_input_save_load_confirm`
Name: Save/load confirm-only helper used repeatedly by the parent controller.
Description: Save/load helper prompt.
Evidence ID: `FRESH-ELF-N001`
Review notes: Fresh independent structural match. Exact NA2 and NUN5 instruction bytes were validated against clean regional ELFs.
#### Patch `localization.regional_input.regional_input_save_load_prompt`
Legacy ID: `regional_input_save_load_prompt`
Name: Blocking memory-card/save-load prompt loop with confirm-to-advance behavior.
Description: Save/load or memory-card prompt.
Evidence ID: `FRESH-ELF-N002`
Review notes: Fresh independent structural match. Exact NA2 and NUN5 instruction bytes were validated against clean regional ELFs.
#### Patch `localization.regional_input.regional_input_overlay_close`
Legacy ID: `regional_input_overlay_close`
Name: Confirm-to-close overlay rendered inside another front-end object.
Description: Unclassified front-end overlay.
Evidence ID: `FRESH-ELF-N003`
Review notes: Fresh independent structural match. Runtime screen remains unclassified; keep separately selectable.
#### Patch `localization.regional_input.regional_input_player_action_decoder`
Legacy ID: `regional_input_player_action_decoder`
Name: Two-player multi-action front-end input decoder with distinct navigation, accept, cancel, and Start actions.
Description: Free/Practice setup or selection controller.
Evidence ID: `FRESH-ELF-N004`
Review notes: Fresh independent structural match. Apply regional_input_player_action_decoder_01, regional_input_player_action_decoder_02, and regional_input_player_action_decoder_03 atomically.
#### Patch `localization.regional_input.regional_input_control_assignment_player`
Legacy ID: `regional_input_control_assignment_player`
Name: Second controller-assignment subhandler used for both players.
Description: Control Settings.
Evidence ID: `FRESH-ELF-N005`
Review notes: Fresh independent structural match. Apply regional_input_control_assignment_player_01 and regional_input_control_assignment_player_02 atomically.
#### Patch `localization.regional_input.regional_input_sound_settings`
Legacy ID: `regional_input_sound_settings`
Name: Sound Settings handler with accept, rollback/cancel, reset, and directional edits.
Description: Sound Settings.
Evidence ID: `FRESH-ELF-N006`
Review notes: Fresh independent structural match. Apply regional_input_sound_settings_01 and regional_input_sound_settings_02 atomically.
#### Patch `localization.regional_input.regional_input_delayed_advance`
Legacy ID: `regional_input_delayed_advance`
Name: Timed confirm-to-advance state after a short input delay.
Description: Unclassified proceed/result prompt.
Evidence ID: `FRESH-ELF-N007`
Review notes: Fresh independent structural match. Runtime screen remains unclassified; keep separately selectable.
#### Patch `localization.regional_input.regional_input_two_item_submenu`
Legacy ID: `regional_input_two_item_submenu`
Name: Two-item front-end/setup submenu with cyclic navigation, accept, and cancel.
Description: Free/Practice setup submenu.
Evidence ID: `FRESH-ELF-N008`
Review notes: Fresh independent structural match. Apply regional_input_two_item_submenu_01 and regional_input_two_item_submenu_02 atomically.
#### Patch `localization.regional_input.regional_input_yes_no_modal`
Legacy ID: `regional_input_yes_no_modal`
Name: Shared two-choice Yes/No modal handler with accept, cancel, and directional selection.
Description: Save/load, overwrite, and return-to-title confirmation prompts.
Evidence ID: `FRESH-ELF-N009`
Review notes: Fresh complete-function comparison: NA2 FUN_001e6ce0 uses Circle accept and Cross cancel; NUN5 FUN_001ecad0 uses Cross accept and Triangle cancel. Apply regional_input_yes_no_modal_01 and regional_input_yes_no_modal_02 atomically.
#### Patch `localization.regional_input.regional_input_title_controller`
Legacy ID: `regional_input_title_controller`
Name: Title-screen state controller with combined Start, accept, and cancel masks.
Description: Title zoom/advance and New Game/Continue title flow.
Evidence ID: `FRESH-ELF-N010`
Review notes: Fresh complete-function comparison: NA2 FUN_001df690 uses Start|Circle and Start|Circle|Cross; NUN5 FUN_001e5300 uses Start|Cross and Start|Cross|Triangle. Apply regional_input_title_controller_01 and regional_input_title_controller_02 atomically.
#### Patch `localization.regional_input.regional_input_character_selection`
Legacy ID: `regional_input_character_selection`
Name: Per-player character and linked-character selection handler with two internal interaction states.
Description: Free Battle and Practice character/linked-character selection.
Evidence ID: `FRESH-ELF-N011`
Review notes: Fresh complete-function comparison: NA2 FUN_003b5df0 and NUN5 FUN_003c8880 preserve independent controller routing while rotating Circle/Cross/Triangle roles. Square operation2 is unchanged. Apply regional_input_character_selection_01 through regional_input_character_selection_06 atomically.
#### Patch `localization.regional_input.regional_input_new_game_continue`
Legacy ID: `regional_input_new_game_continue`
Name: Title New Game/Continue selector with combined Start and accept input.
Description: Title-screen New Game/Continue list.
Evidence ID: `FRESH-ELF-N012`
Review notes: Fresh complete-function comparison: NA2 FUN_001df140 uses Start|Circle while NUN5 FUN_001e4d90 uses Start|Cross.
#### Patch `localization.regional_input.regional_input_support_selection`
Legacy ID: `regional_input_support_selection`
Name: Per-player support selection handler with two internal interaction states.
Description: Free Battle and Practice support selection.
Evidence ID: `FRESH-ELF-N013`
Review notes: Fresh complete-function comparison: NA2 FUN_003b6910 and NUN5 FUN_003c9400 rotate accept, cancel, and operation1 in both states while preserving controller routing. Apply regional_input_support_selection_01 through regional_input_support_selection_06 atomically.
#### Patch `localization.regional_input.regional_input_candidate_021`
Legacy ID: `regional_input_candidate_021`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M001`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_021_01. | Review/apply as a handler set with regional_input_candidate_021_02.
#### Patch `localization.regional_input.regional_input_candidate_022`
Legacy ID: `regional_input_candidate_022`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M002`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_022_01. | Review/apply as a handler set with regional_input_candidate_022_02.
#### Patch `localization.regional_input.regional_input_candidate_023`
Legacy ID: `regional_input_candidate_023`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M003`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_023_01. | Review/apply as a handler set with regional_input_candidate_023_02.
#### Patch `localization.regional_input.regional_input_candidate_024`
Legacy ID: `regional_input_candidate_024`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M004`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_024_01. | Review/apply as a handler set with regional_input_candidate_024_02.
#### Patch `localization.regional_input.regional_input_candidate_025`
Legacy ID: `regional_input_candidate_025`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M005`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_025_01. | Review/apply as a handler set with regional_input_candidate_025_02.
#### Patch `localization.regional_input.regional_input_candidate_026`
Legacy ID: `regional_input_candidate_026`
Name: ETC-owned front-end input decision range. Includes the regional secondary-action Triangle-to-Square move.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M006`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_026_01. | Review/apply as a handler set with regional_input_candidate_026_02.
#### Patch `localization.regional_input.regional_input_candidate_027`
Legacy ID: `regional_input_candidate_027`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M007`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_027_01. | Review/apply as a handler set with regional_input_candidate_027_02.
#### Patch `localization.regional_input.regional_input_candidate_028`
Legacy ID: `regional_input_candidate_028`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M008`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_028_01. | Review/apply as a handler set with regional_input_candidate_028_02.
#### Patch `localization.regional_input.regional_input_candidate_029`
Legacy ID: `regional_input_candidate_029`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M009`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_030`
Legacy ID: `regional_input_candidate_030`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M010`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_030_01. | Review/apply as a handler set with regional_input_candidate_030_02.
#### Patch `localization.regional_input.regional_input_candidate_031`
Legacy ID: `regional_input_candidate_031`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M011`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_031_01. | Review/apply as a handler set with regional_input_candidate_031_02.
#### Patch `localization.regional_input.regional_input_candidate_032`
Legacy ID: `regional_input_candidate_032`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M012`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_032_01. | Review/apply as a handler set with regional_input_candidate_032_02.
#### Patch `localization.regional_input.regional_input_candidate_033`
Legacy ID: `regional_input_candidate_033`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M013`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_034`
Legacy ID: `regional_input_candidate_034`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M014`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_034_01. | Review/apply as a handler set with regional_input_candidate_034_02.
#### Patch `localization.regional_input.regional_input_candidate_035`
Legacy ID: `regional_input_candidate_035`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M015`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_035_01. | Review/apply as a handler set with regional_input_candidate_035_02.
#### Patch `localization.regional_input.regional_input_candidate_036`
Legacy ID: `regional_input_candidate_036`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M016`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | Review/apply as a handler set with regional_input_candidate_036_01. | Review/apply as a handler set with regional_input_candidate_036_02.
#### Patch `localization.regional_input.regional_input_candidate_037`
Legacy ID: `regional_input_candidate_037`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M017`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_038`
Legacy ID: `regional_input_candidate_038`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M018`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_candidate_039`
Legacy ID: `regional_input_candidate_039`
Name: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Description: ETC front-end UI. Runtime confirms ETC ownership in Collection and Shop; the individual screen for this range remains unclassified.
Evidence ID: `ETC-M019`
Review notes: Exact screen ownership is pending runtime classification; no competing ordinal/register match exists inside ETC. | No same-range literal partner identified; correlate with the runtime screen before approval.
#### Patch `localization.regional_input.regional_input_battle_results_tally`
Legacy ID: `regional_input_battle_results_tally`
Name: Battle-results tally fast-forward handler.
Description: During the animated post-battle score and currency calculation, Cross fast-forwards the tally to its final values. The later result-menu proceed handler remains separate.
Evidence ID: `BTL-M022`
Review notes: Runtime: battle_results_tally_skip | Slot-2 replay and runtime-only binary search isolated BTL offset 0x00066210. Replacing only its Circle mask 0x20 with Cross mask 0x40 made Cross immediately complete the tally; Circle is retained by the corresponding NUN5 routine and is treated as an upstream oversight.
#### Patch `localization.ui_layout.ui_layout_ultimate_jutsu_label`
Legacy ID: `ui_layout_ultimate_jutsu_label`
Name: Use one-part Ultimate Jutsu label
Description: Make the OUGI label constructor instantiate one 128x64 regional label instead of two 64x64 Japanese halves.
Evidence ID: `UI-OUGI-LAYOUT-001`
Review notes: Runtime: overlay | The NUN5 one-part behavior is semantically ported into NA2's different compiled loop; the exact replacement instruction does not occur in canonical NUN5 ELF, BTL, ETC, or ADV, so this remains an authored adaptation paired with the whole NUN5 OUGI.CCS import. The user reviewed the completed runtime pass and directed that screens absent from the remaining defect captures be treated as fixed; no OUGI defect remained.
#### Patch `localization.ui_layout.ui_layout_stage_select`
Legacy ID: `ui_layout_stage_select`
Name: Use localized Stage Select layout
Description: Use the official NUN5 stage-name UV table, horizontal fit, Random-prompt position, effective OK/Back anchors, and correct preview indexing while preserving NA2's 16-byte stage records.
Evidence ID: `UI-STAGE-LAYOUT-001`
Review notes: Runtime: overlay | Stage IDs and preview indices equal rows 0..23 in both games. The scale-word port redirects both preview-index consumers, keeps vertical name scale at 1.0, and loads only horizontal fit from the inline record. Two Random constants copy exact NUN5 BTL instructions. NUN5 derives effective OK/Back anchors 388/462 from nominal 400/470 plus regional -12/-8 offsets; authored same-register constants reproduce those positions because NA2 lacks the regional additions. Guarded task-owned Slot 5 captures match all bottom prompts to the NUN5 reference.
#### Patch `localization.ui_layout.ui_layout_character_name_rectangles`
Legacy ID: `ui_layout_character_name_rectangles`
Name: Use localized character-name atlas rectangles
Description: Replace the 96-entry Japanese character-name UV table with the complete official NUN5 English table used by CHARSEL1.CCS and the shared character-name atlases.
Evidence ID: `UI-CHAR-LAYOUT-001`
Review notes: Runtime: resident | NUN5 FUN_0038c350 obtains this table through localized accessor FUN_003d45d0; English pointer-table entry 0 resolves to ELF file offset 0x4DDDD0. Of 96 records, 44 already match NA2 and 52 require localization. A guarded live write was read back exactly, and the user verified the full Character Select roster. The rejected 0x4DC120 range is the separate uniform 38x46 portrait-grid table.
#### Patch `localization.ui_layout.ui_layout_options_labels`
Legacy ID: `ui_layout_options_labels`
Name: Use localized Options label rectangles
Description: Replace the five Japanese Options-menu and six difficulty-label UV rectangles with the complete official NUN5 English tables used by OPTION.CCS.
Evidence ID: `UI-OPTION-LAYOUT-001`
Review notes: Runtime: resident | The live table matched the complete donor block exactly, and the five Options labels plus all four reachable difficulty values rendered with the official English rectangles.
#### Patch `localization.ui_layout.ui_layout_difficulty_sprite`
Legacy ID: `ui_layout_difficulty_sprite`
Name: Route wide difficulty values through the alternate sprite
Description: Match NUN5's Options renderer by using the alternate sprite object for difficulty indices 0, 4, and 5 instead of only 0 and 5.
Evidence ID: `UI-OPTION-LAYOUT-002`
Review notes: Runtime: resident | A guarded two-word live write changed the corrupt selected value to a clean centered INSANE label. HARD, EASY, and SIMPLE plus both arrow endpoints were then captured cleanly; the valid index domain is 0..5 and file size is preserved.
#### Patch `localization.ui_layout.ui_layout_battle_hud_names`
Legacy ID: `ui_layout_battle_hud_names`
Name: Fit localized battle-HUD character names
Description: Cap the battle-HUD character-name display width at 160 pixels, matching NUN5 while preserving the full atlas source rectangle.
Evidence ID: `UI-BATTLE-NAME-LAYOUT-001`
Review notes: Runtime: overlay | The official NUN5 renderer applies min(width,160) before the common scale. A guarded live hook in the homologous NA2 path was read back exactly; forcing a 208-pixel source width produced a 160-pixel display width, and restoring the 112-pixel source restored a 112-pixel display width without altering the source rectangle.
#### Patch `localization.ui_layout.ui_layout_practice_settings_prompt`
Legacy ID: `ui_layout_practice_settings_prompt`
Name: Use localized Practice Settings prompt layout
Description: Use the official NUN5 English prompt rectangle and X anchor so the full label and Square icon fit the VS screen.
Evidence ID: `UI-PRACTICE-LAYOUT-001`
Review notes: Runtime: overlay | NUN5 FUN_006d4170 obtains rectangle (0,280,176,24) through localized accessor FUN_003d46c0 and draws it at X=100. The homologous NA2 path used static rectangle (1,281,112,22) at X=60. Guarded live writes changed both values; after redraw the object was exactly X=276, Y=356, 176x24, UV (0,280), and the captured prompt matched NUN5 with no clipping.
#### Patch `localization.ui_layout.ui_layout_battle_hud_name_rectangles`
Legacy ID: `ui_layout_battle_hud_name_rectangles`
Name: Use localized battle-HUD character-name rectangles
Description: Replace the separate 95-entry Japanese battle-HUD UV table with the official NUN5 English table used by CMN/GAUGE.CCS.
Evidence ID: `UI-BATTLE-NAME-LAYOUT-002`
Review notes: Runtime: resident | A guarded live write replaced all 760 bytes with exact readback. Naruto and Shikamaru object widths then matched the donor records, and both formerly clipped top-HUD names rendered in full.
#### Patch `localization.ui_layout.ui_layout_vs_confirmation`
Legacy ID: `ui_layout_vs_confirmation`
Name: Use localized VS confirmation labels, inputs, and prompts
Description: Use the official NUN5 Customize Jutsu, Battle Settings, arrows, input-glyph, Jutsu-label, OK, and Back records with NA2-specific anchor corrections where the two renderers differ.
Evidence ID: `UI-VS-CONFIRM-LAYOUT-001`
Review notes: Runtime: overlay | Nineteen guarded live edits restore both Jutsu labels, all three input glyphs, the two-arrow control, the full Battle Settings and Customize Jutsu prompts, and the complete Cross/OK and Triangle/Back legends. NUN5 X=260 works exactly after the final selector correction and is imported as a register-preserving two-byte donor copy. The bottom records are exact NUN5 ELF copies; NA2's redundant regional-icon draws are disabled, and evidence-calibrated X=388/X=462 anchors reproduce NUN5's X=400/X=470 raster positions at dx=0,dy=0. Text/font rendering remains out of scope and no text bytes are changed.
#### Patch `localization.ui_layout.ui_layout_round_label`
Legacy ID: `ui_layout_round_label`
Name: Use localized Round label layout
Description: Replace the two Japanese Round glyphs with the official one-part NUN5 English label and match its position and 1.2 scale.
Evidence ID: `UI-VS-ROUND-LAYOUT-001`
Review notes: Runtime: overlay | Eight guarded live writes replaced the two-glyph source with the official 94x30 Round rectangle, disabled the second glyph, and matched NUN5's X, Y, centering, render, and spacing constants. The archived slot-7 capture matches the NUN5 Round label apart from normal pulsation.
#### Patch `localization.ui_layout.ui_layout_jutsu_selector_arrows`
Legacy ID: `ui_layout_jutsu_selector_arrows`
Name: Use localized open Jutsu-selector arrows
Description: Omit NA2's two closed-selector horizontal-arrow draws and render the official NUN5 arrow record vertically through a draw-scoped NA2 compatibility helper.
Evidence ID: `UI-VS-JUTSU-SELECTOR-LAYOUT-001`
Review notes: Runtime: overlay | Paired code proves NUN5 omits the horizontal draws, imports record (145,385,22,38), and supplies +pi/2/-pi/2. Direct field writes failed because NA2 mode 0 ignores rotation; persistent NUN5-mode transplants damaged unrelated UI. The verified helper instead enables NA2 sprite mode 1 only for one arrow, applies lower flip from the signed angle, draws and flushes before restoring mode 0, and lives inside the replaced dead horizontal blocks rather than the shared header cave. Four angle words and the record are exact NUN5 copies; the scoped helper and call redirects are documented NA2-specific ports. The accepted paired capture has correct upper/lower arrows, no horizontal arrows, no bottom fragment, and no collateral label changes.
#### Patch `localization.ui_layout.ui_layout_command_scroll_arrows`
Legacy ID: `ui_layout_command_scroll_arrows`
Name: Use localized command-list scroll arrows
Description: Copy the official NUN5 vertical-scroll triangle rectangle used by the shared Command Menu and Command Chart renderer.
Evidence ID: `UI-COMMAND-SCROLL-LAYOUT-001`
Review notes: Runtime: overlay | NA2 FUN_00878820 and NUN5 homolog FUN_00894f60 each draw one shared TEX_xselect record twice, rotating the first draw by pi. The NA2 record selects imported-atlas garbage at (194,195,20,20); NUN5 selects the orange scroll triangle at (1,225,20,22). Paired Slots 5 and 6 reuse the same runtime sprite object, so one exact donor copy covers both screens. The user verified both Command Menu and Command Chart after the integrated Current build and accepted them as good.
#### Patch `localization.ui_layout.ui_layout_item_status_paired`
Legacy ID: `ui_layout_item_status_paired`
Name: Use localized paired item-status labels
Description: Import the official NUN5 paired item-status records and rank offsets, then port the anisotropic bubble and foreground layout contract without changing NA2's object ABI.
Evidence ID: `UI-ITEM-PAIR-LAYOUT-001`
Review notes: Runtime: overlay | The canonical pair path is reconstructed from NA2/NUN5 BTL and boot-ELF homologs. Official NUN5 records 0x8F..0x94 and 0x9B..0x9C plus the complete rank table are copied directly. NA2-specific glue retains NA2's object layout while reproducing donor width scaling, centering, row spacing, rotation, clamp, and common origin. Its foreground helper takes explicit caller-owned anchor, row, and angle-output arguments so the numeric class can reuse it without changing the accepted pair result. The resident renderer's final centered-offset calculation now copies NUN5's exact f22 scale-register instruction; using f21 alpha there made every partial-alpha foreground slide even though its anchor and dimensions were already correct. Settled pair placement remains unchanged apart from normal pulse timing.
#### Patch `localization.ui_layout.ui_layout_item_status_numeric`
Legacy ID: `ui_layout_item_status_numeric`
Name: Use localized numeric item-status labels
Description: Import the official NUN5 Health, Chakra, and Recovery records and port the complete numeric top-label, lower-label, and one/two/three-digit layout through the shared NA2-compatible item helper.
Evidence ID: `UI-ITEM-NUMERIC-LAYOUT-001`
Review notes: Runtime: overlay | The official NUN5 records are exact donor copies. NUN5 numeric functions FUN_00723360, FUN_00723570, and FUN_00723930 center the localized records, apply code-specific quarter-turns, and position 1/2/3 digit values from a negative-50 X origin. NA2 functions FUN_0070E200, FUN_0070E350, and FUN_0070E660 use an incompatible object ABI, so the implementation passes the donor anchors and rotation through the existing NA2-safe helper and ports the six digit positions into the corrected NA2 coordinate frame. The paired slot-7 regression remains intact, and the numeric slot-3 Health/Chakra/Recovery checkpoint matches NUN5.
#### Patch `localization.ui_layout.ui_layout_item_status_single`
Legacy ID: `ui_layout_item_status_single`
Name: Use localized single item-status labels
Description: Import the official NUN5 single-status records and port the shared origin, donor width scales, and record-specific quarter-turn without changing NA2's object ABI.
Evidence ID: `UI-ITEM-SINGLE-LAYOUT-001`
Review notes: Runtime: overlay | Official NUN5 records 0x96 through 0x9A are copied directly. NA2 and NUN5 use identical object-code-to-record tables, but the single draw functions differ in regional origin and rotation setup. The bounded NA2 port retains the homologous wrapper, moves the origin to NUN5's 0/+33 contract, and restores the quarter-turn only for records 0x82 and 0x99 after resource lookup. Paired Slots 10 and 12 prove ordinary single and poison/status placement; the uncaptured 0x99 branch is verified statically from both complete functions, so confidence remains high rather than verified.
#### Patch `localization.ui_layout.ui_layout_item_status_fixed`
Legacy ID: `ui_layout_item_status_fixed`
Name: Use localized fixed item-status labels
Description: Reuse the donor-backed item records and shared width helper to center both fixed-class labels at NUN5's exact row positions without changing NA2's object ABI.
Evidence ID: `UI-ITEM-FIXED-LAYOUT-001`
Review notes: Runtime: overlay | The fixed class always draws records 0x8E and 0x8D, already imported by UI-BTL-009 and UI-BTL-010. NA2 uses regional fixed X/Y offsets; NUN5 centers each record from its live width at +20/+37 Y. Two bounded call-site adaptations reuse the established shared width helper with zero X bias and +2/+17 row bias. A matched synthetic fixed-vtable checkpoint proves identical label-to-bubble centering; confidence remains high because the live object was transformed from a paired notification rather than naturally spawned.
#### Patch `localization.ui_layout.ui_layout_item_pickup_doll`
Legacy ID: `ui_layout_item_pickup_doll`
Name: Use the localized substitution-doll pickup icon
Description: Copy NUN5's exact substitution-doll item record over the homologous NA2 record selected by the live pickup updater.
Evidence ID: `UI-ITEM-PICKUP-DOLL-001`
Review notes: Runtime: resident | Matched slot 4 states contain the same live logical effect code 0x0A and homologous TEX_xselect sprite-pool entry with identical 30x30 source dimensions, flags, and near-identical placement. A restored NA2 frame briefly retains record 0x2E geometry, but the next updater pass selects NA2 record 0x0A, whose rectangle (161,193,30,30) samples the green Recovery label from the imported NUN5 atlas. NUN5 record 0x0A uses (161,225,30,30) and selects the doll. Copying the complete same-index NUN5 record preserves the renderer ABI, effect selection, timing, and gameplay behavior. The superseded cross-index 0x0A-to-0x2E candidate changed only transient restored geometry and had no visible effect in a fresh normal build.
#### Patch `localization.ui_layout.ui_layout_mash_prompts`
Legacy ID: `ui_layout_mash_prompts`
Name: Use localized battle Mash prompt rectangles
Description: Copy the complete official NUN5 English seven-record main-prompt rectangle table used by the battle input overlay.
Evidence ID: `UI-MASH-PROMPT-LAYOUT-001`
Review notes: Runtime: overlay | NUN5 routes prompt IDs below 7 through its regional boot-ELF accessor. NA2 instead reads its Japanese BTL table directly, so one guarded donor copy ports all seven regional records without changing the renderer or the adjacent controller-glyph table. A patched paired savestate rendered both Mash labels horizontally at the NUN5 positions; the rejected adjacent-table test corrupted only controller glyphs and is retained as a documented negative result.
#### Patch `localization.ui_layout.ui_layout_mode_select`
Legacy ID: `ui_layout_mode_select`
Name: Use localized Mode Select layout
Description: Copy the official NUN5 English START-label rectangle, port its draw anchor, and reproduce NUN5's effective OK and Back anchors without changing NA2's renderer ABI.
Evidence ID: `UI-MODE-SELECT-LAYOUT-001`
Review notes: Runtime: resident | NUN5 Mode Select renderer FUN_003972e0 obtains localized rectangle (1,393,254,26) through accessor FUN_003d4bc0 and draws it at X=150. Its OK and Back calls start at X=400/470 and apply shared regional offsets -12/-8, for effective anchors 388/462. NA2 FUN_00385c00 used static START rectangle (1,397,206,22) at X=130 and passed unadjusted 400/470 prompt anchors. The rectangle is an exact NUN5 donor copy. The START and prompt constants are authored same-register NA2 ports because the homologous NUN5 instruction/register flow and extra offset loads cannot be copied safely into NA2. A guarded task-owned slot-1 state rendered both prompts at +1 X/+1 Y versus NUN5, consistent with normal prompt pulsation. The user accepted the final Mode Select footer on 2026-07-26.
#### Patch `localization.ui_layout.ui_layout_controls_vibration`
Legacy ID: `ui_layout_controls_vibration`
Name: Use localized Controls Vibration-label rectangle
Description: Copy the official NUN5 English Vibration-label rectangle used by the imported common UI atlas over NA2's narrow Japanese rectangle.
Evidence ID: `UI-CONTROLS-LAYOUT-001`
Review notes: Runtime: resident | NUN5's localized rectangle table selects (64,88,64,20) for TEX_xmenu, while NA2's static table selects (1,69,42,22). The exact eight-byte donor and destination ranges are statically verified; OFF/On text and font rendering remain out of scope.
#### Patch `localization.ui_layout.ui_layout_character_select_footer`
Legacy ID: `ui_layout_character_select_footer`
Name: Use localized Character Select footer anchors
Description: Copy NUN5's exact Select Color and Random X-anchor instructions into the homologous NA2 Character Select footer renderer and reproduce NUN5's effective OK and Back anchors without changing NA2's renderer ABI.
Evidence ID: `UI-CHAR-FOOTER-LAYOUT-001`
Review notes: Runtime: resident | NA2 FUN_003bc470 draws Random at X=300 and Select Color at X=160; NUN5 homolog FUN_003cf0d0 draws the same imported CHARSEL1.CCS records at X=260 and X=100. Both artwork-anchor instructions retain the same v0 destination register, so exact donor copies are valid. NUN5 also adds regional offsets -12/-8 to nominal OK/Back anchors 400/470; NA2 lacks those additions, so authored same-register constants X=388/X=462 reproduce the effective positions. Guarded task-owned captures place all four footer groups at the NUN5 positions within normal one-pixel pulse variance.
#### Patch `localization.ui_layout.ui_layout_common_prompts`
Legacy ID: `ui_layout_common_prompts`
Name: Use localized shared common prompts
Description: Copy NUN5's exact Next, Triangle icon, Cancel label, empty-tail, and Stop records into NA2's shared compositor data, and reproduce NUN5's effective Options-root and Collection-footer anchors without changing NA2's renderer ABI.
Evidence ID: `UI-COMMON-CANCEL-LAYOUT-001`
Review notes: Runtime: resident | NA2 FUN_0037c980 case 4 composes three Japanese records totaling 182 logical pixels; NUN5 homolog FUN_0038bb10 case 4 composes localized records 6, 4, and 5 totaling 80 logical pixels around the same caller anchor. Exact donor copies in a guarded task-owned savestate move the Options Cancel bounds from 99..201 to 165..259, versus NUN5 164..258; the one-pixel X/Y difference is normal pulse timing. Record 2 is the shared Next label: NUN5 uses 66 pixels while NA2 retained 70, and the exact donor record plus the NUN5 Battle Results anchor reproduces the reference object's X=353 and 66x22 geometry. The Options-root caller loads nominal OK/Back X=400/470 directly, whereas its NUN5 homolog applies regional offsets -12/-8 before calling the same semantic compositor. Authored same-register NA2 constants X=388/462 reproduce those effective anchors; a guarded task-owned slot-1 render matches the NUN5 prompt positions. The Collection state renderer uses a separate nominal X=380/460 table at ETC offsets 0x2F010/0x2F018, while its NUN5 homolog adds the same -12/-8 regional offsets. Authored X=368/452 values in that dedicated NA2 table produce guarded slot-2 parity. The HOME action helper at NA2 FUN_006b44b0 is a different consumer: NUN5 homolog FUN_006c7250 applies state-specific regional geometry of -12 for Cross, localized-width-derived -24 for Play, -8 for Back, and width-derived state-4 Stop geometry. A 16-byte tail-call wrapper in runtime-proven MWO3 header padding plus four guarded call redirects and exact state-2/state-4 label compensation reproduce those effective anchors across every caller of this helper. State 4 also copies NUN5's exact `(144,48,76,24)` Stop rectangle. NUN5's GP-relative language globals and rectangle accessors are ABI-incompatible with NA2, so the wrapper redirects and label compensations are authored ports rather than literal donor code. A guarded task-owned ss10 runtime capture matches the NUN5 Triangle/Stop footer anchor and preserves the matched Cross/Play group; the user explicitly accepted the final comparison on 2026-07-27.
#### Patch `localization.ui_layout.ui_layout_options_footers`
Legacy ID: `ui_layout_options_footers`
Name: Align shared Options footer legends
Description: Copy NUN5's exact X-anchor instructions into the homologous Controls and Music Options Select calls, and reproduce NUN5's effective OK/Back anchors in both resident renderers.
Evidence ID: `UI-OPTIONS-SELECT-LAYOUT-001`
Review notes: Runtime: resident | NA2 FUN_00388b90 and FUN_0038a1f0 each load 230.0 for both Select footer calls; NUN5 homologs FUN_0039a450 and FUN_0039bb00 load 200.0 through same-register instructions. Both NA2 functions also load nominal OK/Back X=400/470 directly, whereas both NUN5 homologs apply the same regional -12/-8 additions. Four exact donor copies align both Select pairs; four authored same-register constants X=388/X=462 reproduce the effective Controls and Music anchors. Guarded task-owned captures match both complete footers while preserving vertical placement and internal spacing.
#### Patch `localization.ui_layout.ui_layout_collection_submenu`
Legacy ID: `ui_layout_collection_submenu`
Name: Use localized Collection submenu layout
Description: Copy NUN5's Characters, Movie, Music, Play, Previous Page, Next Page, and Collection viewer-control draw records into NA2's Collection tables.
Evidence ID: `UI-COLLECTION-SUBMENU-LAYOUT-001`
Review notes: Runtime: overlay | NA2 ccHomeIspSelectChar draw routine FUN_006b6ee0 uses centers 100/220 and 118-pixel page rectangles; NUN5 homolog FUN_006c9f90 uses centers 87/233 and 144-pixel rectangles. NA2's static category-title records overshoot or miss the imported NUN5 title rows, and its Play rectangle begins 24 pixels before the imported English control. The Collection viewer renderer FUN_006bafc0 places all four lower controls on Y=360 and retains two narrow Japanese rectangles; NUN5 homolog FUN_006ce150 uses the exact 2x2 English layout and four matching localized rectangles. NUN5 accessors FUN_003d4170 and FUN_003d4210 provide the other localized records. Whole HOME.CCS import supplies the English pixels but not these ETC-owned draw records. All eight edits are exact NUN5 donor copies; runtime acceptance is pending.
#### Patch `localization.ui_layout.ui_layout_victory_names`
Legacy ID: `ui_layout_victory_names`
Name: Use localized Victory character-name layouts
Description: Derive every compatible NA2 prebuilt Victory name rectangle from the official NUN5 frame templates and English character-width table.
Evidence ID: `UI-VICTORY-NAME-LAYOUT-001`
Review notes: Runtime: overlay | NUN5 builds each 24-byte rectangle at runtime from a localized width row and frame template, whereas NA2's BTL callback returns a pointer to a prebuilt rectangle. Each replacement is therefore the complete official frame template plus the verified NUN5 width minus the renderer's two-pixel border; zero-only aliases remain untouched.
#### Patch `localization.ui_layout.ui_layout_settings_footers`
Legacy ID: `ui_layout_settings_footers`
Name: Align localized settings footer legends
Description: Import NUN5's exact Select anchors and reproduce its effective OK and Back anchors in NA2's homologous Battle and Practice Settings footer renderers.
Evidence ID: `UI-SETTINGS-FOOTER-LAYOUT-001`
Review notes: Runtime: overlay | NA2 FUN_008807a0/FUN_00882250 and NUN5 FUN_0089d280/FUN_0089f130 draw the same four-call footer contract. Every NUN5 Select call uses X=200 and is an exact same-register donor copy. NUN5 starts OK/Back at 400/470 but then applies runtime offsets -12/-8; NA2 lacks those additions, so authored X=388/X=462 constants reproduce the same effective positions. Guarded task-owned slot-6 and slot-10 states rendered Select, OK, and Back aligned with NUN5 while leaving the accepted Customize Jutsu footer untouched.
#### Patch `localization.ui_layout.ui_layout_battle_results`
Legacy ID: `ui_layout_battle_results`
Name: Use localized Battle Results summary, details, and rank layout
Description: Copy the official NUN5 result-label, rank-atlas, title, moving-cloud, footer, and shared-prompt geometry into the homologous NA2 screens, and reproduce the NUN5 regional Ninja Song details-footer anchors while preserving NA2 renderer ABIs.
Evidence ID: `UI-BATTLE-RESULTS-LAYOUT-001`
Review notes: Runtime: overlay | NA2 FUN_007168F0/FUN_00719D40 and NUN5 FUN_0072C440/FUN_0072FBC0 share the same result-screen objects and moving-cloud loop. A guarded task-owned slot-1 state was transitioned hidden into screen 2 after applying the exact candidate bytes: Health, Time, Bonus, Money, Next, and Display Details match; the five clouds retain their motion while sampling cloud art instead of animated Ninja Song letters. The title uses the identical pulse helper with the NUN5 rectangle and X offset; static size differences between captures are pulse phase, not clipping. Matched ss2-ss6 prove the visible rank selector sequence is 4,0,1,2,3 in both games. NA2's BTL table at file 0x2100B0 uses 64x56 Japanese cells, while NUN5's English table at SLES file 0x4DDCE0 uses 96x44 cells. ui_layout_battle_results_11 copies all five records and retains index 3 as the shared delta baseline. Raw BTL bytes confirm both games already apply the computed offset through homologous model setters, so no renderer code port is required. The user verified the normal-pipeline result for all five rank stamps on 2026-07-26. Paired ss8 pixels and the complete NA2 FUN_007182E0/NUN5 FUN_0072DEA0 draw paths isolate the details footer: NA2 uses literal X=395/470, while NUN5 adds regional globals -20/-8 before the homologous calls. The authored effective X=375/462 ports remove the measured +25/+10 output-pixel displacement at the 640-to-512 render scale. Existing summary-footer call sites remain untouched.
## localization: runtime_injector
### Selectable node `localization.font_glyphs`
Description: Resident native-font metric decoding and draw adjustment.
Review notes: Generated C is linked into the shared payload; only two guarded hooks remain in the boot ELF.
### Selectable node `localization.font_layout`
Description: Resident font measurement, fitting, wrapping, positioning, and caller adapters.
Review notes: Generated code is linked into the shared payload; only guarded hooks remain in game executables.
### Selectable node `localization.font_numeric_formatting`
Description: Resident ASCII numeric formatting for dynamic UI values.
Review notes: Generated code is linked into the shared payload; guarded hooks select only accepted numeric fields.
#### Patch `localization.font_glyphs.font_glyphs_metrics`
Legacy ID: `font_glyphs_metrics`
Name: Compiled-C native secondary metrics
Description: Decode the accepted packed 14x20 metric rows for measurement and drawing from composition-time C in 228.BIN, leaving only guarded register-setup hooks in the fixed boot ELF.
Evidence ID: `NUN5-GF4-NATIVE-14X20`
Review notes: Runtime: Static composition preserves the accepted lookup, nibble expansion, horizontal leading-bearing scale, vertical-mode selection, trailing trim, and native cleanup destinations; fresh user regression is required for the relocated control flow. | The atlas and packed-map assets remain unchanged. The former 316-byte decoder and 24-byte measurement-hook blobs are retired rather than recompiled into fixed ELF space.
#### Patch `localization.font_layout.font_layout_core`
Legacy ID: `font_layout_core`
Name: Resident v2 shared layout core
Description: Provide independent NUN5-compatible printable-ASCII measurement, shrink-only fitting, box positioning, explicit line measurement, and session-guarded renderer hooks for accepted caller-family adapters.
Evidence ID: `NUN5-V2-SHARED-LAYOUT-CORE`
Review notes: Runtime: Matched Controls review proves the generated core uses the accepted 95-entry metric table, never enlarges text, restores renderer state, and remains resident through a real title-to-Load transition. | A dedicated 0x40 session flag may replace only the active glyph bottom edge. The corrected conditional delay slot loads session glyph_height only on the flagged path; null and unflagged sessions retain the displaced native edge and continue through the accepted primary/secondary helper.
#### Patch `localization.font_layout.font_layout_global_selected_style`
Legacy ID: `font_layout_global_selected_style`
Name: Global selected-text stable origin
Description: Apply one origin rule across every native NA2 gray-shadow selected renderer: keep the colored glyph at its ordinary origin and place its shadow one unit right and two units below.
Evidence ID: `NUN5-GLOBAL-SELECTED-STYLE`
Review notes: Static: a function-level scan of clean SLPS_258.37 plus ADV, BTL, and ETC finds six implementations and no overlay-local implementation: central primitives 0x00379040/0x00379150, fixed two-choice primitive 0x00379C30, and record-based components 0x001E6060/0x001E6370/0x001E6CE0. Two guarded register hooks share one 48-byte correction; seven exact inline gray-draw calls share one 56-byte record adapter; the fixed two-choice primitive delegates selected rows to the corrected central primitive and ordinary rows to the native plain primitive. | Historical isolation with screen-specific patches disabled first proved the one-primitive candidate partial, then the two-central-primitive candidate partial on the Save data prompt. The current default enables the bounded caller families on top of this global dispatcher; the dispatcher itself changes no text bytes, colors, scales, or per-screen coordinates.
#### Patch `localization.font_layout.font_layout_controls`
Legacy ID: `font_layout_controls`
Name: Resident v2 Controls boxed fit
Description: Route the first eight Control Settings action labels through the v2 128-unit NUN5 box.
Evidence ID: `NUN5-V2-CONTROLS-BOXED-FIT`
Review notes: Runtime: Matched 640x480 review proves the first eight label bounds and centers, full-width Linked Attack, 128/178 Ultimate Jutsu Prep fitting, exact caller-center-minus-64 positioning, and complete transient-state restoration. | The user accepted the first eight rows on 2026-07-26. The unrelated ninth Control Settings vibration call remains native; the battle Special Controls modal uses separate Shift-JIS slots handled by canonical mappings T2203/T2204.
#### Patch `localization.font_layout.font_layout_titles`
Legacy ID: `font_layout_titles`
Name: Resident v2 Command Chart and Practice title boxes
Description: Route the two title-only BTL draw calls through one configurable v2 adapter with distinct 288-unit Command Chart and 352-unit Practice containers.
Evidence ID: `NUN5-V2-TITLE-BOXES`
Review notes: Runtime: Matched hidden worker captures prove shrink-only fit and NUN5-aligned title origins in both modes; guarded BTL call sites isolate title rows from Practice explanations and Command Chart auxiliary strings. | The user accepted Command Chart on 2026-07-27; Practice title acceptance remains pending, and this title patch selects no Practice explanation or Command Chart auxiliary call.
#### Patch `localization.font_layout.font_layout_command_relationships`
Legacy ID: `font_layout_command_relationships`
Name: Resident v2 Command Chart relationship and input rows
Description: Combine each Command Chart row's two optional relationship strings and render them once through one bounded two-line layout, then select the homologous icon-row offset according to whether the row has relationship text.
Evidence ID: `NUN5-V2-COMMAND-RELATIONSHIPS`
Review notes: Static: NA2 FUN_0087A700 draws record bytes +4 and +5 separately through BTL file calls 0x1C6A70 and 0x1C6ABC; NUN5 homolog FUN_00896E70 concatenates both tokens into one 0x100-byte buffer. NUN5 then uses base +46 for relationship-row icons and base +38 for plain-row icons; the generated-C offset entry replaces NA2's single fixed +20 load without replacing either native icon branch. | The earlier candidate's shared +16 binary constant matched relationship rows but left plain rows 22 local units too high and collided its new scale flag with the existing premeasured flag. The distinct flag and row-aware icon offset await the user's integrated review.
#### Patch `localization.font_layout.font_layout_pause_controls`
Legacy ID: `font_layout_pause_controls`
Name: Resident v2 Pause Controls list fit
Description: Route both normal and selected Pause Controls rows through one shared 216-unit shrink-only box with the retained NUN5 four-unit Y correction.
Evidence ID: `NUN5-V2-PAUSE-CONTROLS-LIST`
Review notes: Runtime: The exact BTL calls at files 0x1C97D8 and 0x1C9794 are isolated from the shared boot-ELF list helper; static guards and adapter tests preserve each native ABI, including the selected red style and proven two-unit selected-helper X compensation. | The user verified both the normal ss2 state and corrected selected ss3 state on 2026-07-27; no ss4 confirmation-body or Yes/No caller is selected.
#### Patch `localization.font_layout.font_layout_quit_confirmation`
Legacy ID: `font_layout_quit_confirmation`
Name: Resident v2 shared modal row adapters and Battle or Practice quit confirmation layout
Description: Route the shared quit-confirmation body and Yes/No list through draw-time wrapping and scoped NUN5 coordinate adapters, while exact Special Controls string-pointer guards reuse the same selected/unselected hooks.
Evidence ID: `NUN5-V2-QUIT-CONFIRMATION`
Review notes: Runtime: The exact BTL body and list calls delimit the quit modal; outside its transient scope, both shared hooks recognize both Special Controls ON/OFF pointers so each row retains its measured coordinates when selection swaps. | The user verified the combined quit-confirmation result across Battle and Practice returns to Game Mode and Character Select on 2026-07-27. Matched ON- and OFF-highlight ss1 captures prove the pointer-specific positions; every other list remains native. Replacement ss1 evidence on 2026-08-01 adds one shared geometry formula per native draw state, not per row: selected X +1.0 and scale 1.02, ordinary scale 1.01, with glyph height 26 on both. The guarded hidden-worker core-glyph bounds align with NUN5 without writing text; integrated user acceptance of this refinement remains pending.
#### Patch `localization.font_layout.font_layout_mode_select_confirmation`
Legacy ID: `font_layout_mode_select_confirmation`
Name: Resident v2 Mode Select confirmation layout
Description: Route the dedicated Return to Title Screen body draw through NUN5 renderer state and retain the scoped Yes/No coordinate mapper for the top selector.
Evidence ID: `NUN5-V2-MODE-SELECT-CONFIRMATION`
Review notes: Static: Mode Select FUN_00385C00 draws the body through FUN_003825B0 at file 0x285E68 and the live choice object +0xCC through FUN_00383600 at file 0x285E98; both exact guards preserve the native ABIs. | Runtime: the prior top selector remains user-verified. The body adapter changes only its local Y from 16 to 12 and activates tracking-zero/native-space behavior without glyph scaling; fresh native-resolution NUN5 and injected NA2 captures have identical ink bounds X 194-909 and Y 1042-1078. The user verified the exact live result on 2026-07-31.
#### Patch `localization.font_layout.font_layout_character_select_modal`
Legacy ID: `font_layout_character_select_modal`
Name: Resident v2 Character Select modal text
Description: Route both selected and ordinary five-row entries through one bounded NUN5-metric session, render the return-confirmation body through NUN5's 368x24 secondary-font box, and scope only that confirmation's top Yes/No list through the shared NUN5 coordinate mapper.
Evidence ID: `NUN5-V2-CHARACTER-SELECT-MODAL-TEXT`
Review notes: Static: exact main-ELF callers at file offsets 0x2BC984 and 0x2BC9BC isolate the selected and ordinary five-row draws; files 0x2BCAAC and 0x2BCB54 isolate the top confirmation list and body. | Runtime: captures 50 and 51 verify the shared structural fifth-row producer: the declarative table supplies local Y 115, the selected helper applies a one-unit phase compensation, and the ordinary adapter preserves the produced coordinate. Rows one through four retain their accepted placement. The regenerated integrated capture history was accepted for publication on 2026-08-03.
#### Patch `localization.font_layout.font_layout_collection_confirmation`
Legacy ID: `font_layout_collection_confirmation`
Name: Resident v2 Collection exit confirmation
Description: Route both Collection exit-confirmation body consumers and the bounded Yes/No list through NUN5-matched C geometry.
Evidence ID: `NUN5-V2-COLLECTION-CONFIRMATION`
Review notes: Static: ETC files 0x12680 and 0x148C8 are guarded native body calls; file 0x126A0 is the bounded choice-list call. | Runtime: live tracing proved the later render-state call at 0x006C87C8 produces the visible body. Both body paths now use local (24.8,12), native horizontal scale, and the literal colored-word separator; Collection-local Yes/No targets are (64.2,29.85)/(68.1,48.2). Native-resolution bounds match scaled NUN5 exactly for black ink and within one pixel for red ink. The user verified the live result on 2026-07-31; every unrelated ETC caller remains native.
#### Patch `localization.font_layout.font_layout_collection_lists`
Legacy ID: `font_layout_collection_lists`
Name: Resident v2 Collection text lists
Description: Route the shared Collection row draw through family boxes and move the three character-header callers through two shared plaque-origin formulas without changing any displayed string.
Evidence ID: `NUN5-V2-COLLECTION-LISTS`
Review notes: Static: NA2 ETC FUN_006B4D30 draws Movie and character-detail rows through the single guarded call at file 0xFD8; NUN5 homolog FUN_006C7CA0 uses the same boxed compositor stage with 192x32 Movie and relationship boxes and a 152x32 move box. Figure and Music headers use calls 0x7640 and 0xF2B8. The visible ordinary and legacy Jutsu plaque is the parent FUN_006C11E0 call at 0xD4B4; the previously targeted child/VCR call at 0xA31C is unrelated and remains native. | Runtime: synchronized final-red font2 captures 1-7 cover Sakura and Classic Naruto character-detail variants plus Figure, Music, and Movie pages without a large Font discrepancy. Captures 8-13 desynchronized into Free Battle and are excluded from Ninja evidence.
#### Patch `localization.font_layout.font_layout_jutsu_selector`
Legacy ID: `font_layout_jutsu_selector`
Name: Resident v2 Jutsu selector rows
Description: Route the exact Battle Settings Jutsu-row draw through a selective C entry that preserves native one-line rendering and uses the NUN5-homologous 186x32 two-line compositor only when wrapping is required.
Evidence ID: `NUN5-V2-JUTSU-SELECTOR`
Review notes: Static: NA2 BTL FUN_006BCB70 draws every visible Jutsu row through the single guarded call at file 0x90DC, while NUN5 homolog FUN_006CFE70 uses a 186x32 two-line box at the same stage. | Runtime: supplemental ss3 proves the long selected title matches NUN5's wrapped bounds while the short Great Ball Rasengan row remains byte-for-byte on the native draw path and retains its exact baseline bounds. Earlier direct ss5 and ss6 loads retain the same long-row compositor. User acceptance remains pending.
#### Patch `localization.font_layout.font_layout_special_controls_body`
Legacy ID: `font_layout_special_controls_body`
Name: Resident v2 Special Controls explanatory body
Description: Route only the exact Special Controls explanatory-body call through the shared draw-time word wrapper using the NUN5 400x60 two-line container.
Evidence ID: `NUN5-V2-SPECIAL-CONTROLS-BODY`
Review notes: Runtime: The supplied ss1 pair and exact wrapper telemetry identify BTL file 0x1C3D38; NUN5 keeps the canonical source string unbroken and creates a transient line break before for inside a 400-unit, two-line box. | An exact-guarded converted ss1 state proves the two lines share NUN5's break and origins; the direct call preserves every other shared UI body and reuses the existing v2 native measure, wrap, and adapter-session primitives.
#### Patch `localization.font_layout.font_layout_practice_explanations`
Legacy ID: `font_layout_practice_explanations`
Name: Resident v2 Practice explanation flow
Description: Replace the per-token Practice explanation renderer with one NUN5-equivalent mixed text/icon buffer, unlimited word wrapping inside the 364x48 box, and call-local icon callbacks.
Evidence ID: `NUN5-V2-PRACTICE-EXPLANATIONS`
Review notes: Runtime: Matched hidden captures across supplied Practice slots 2-7 prove NUN5-equivalent one-, two-, and three-line wrapping, line spacing, placement, and native D-pad, face, plus, and shoulder icons. | Controls and Command Chart regression captures remain intact; the composed NUN5-left/current-right Practice grids await user acceptance before the next caller family begins.
#### Patch `localization.font_numeric_formatting.font_numeric_ninja_song`
Legacy ID: `font_numeric_ninja_song`
Name: Ninja Song ASCII dynamic numbers
Description: Route all five dynamic Ninja Song decimal fields through one NUN5-compatible ASCII formatter while preserving each caller's width and padding mode.
Evidence ID: `NUN5-NINJA-SONG-ASCII-NUMBERS`
Review notes: Runtime: The user built and tested the integrated fix across Ninja Song ss2–ss5 and declared the task done; static guards prove all five dynamic fields share the same formatter helper. | The canonical T2195 ASCII multiplication separator remains reachable and correct; unseen decimal values use the same width-aware helper rather than separate string mappings.
#### Patch `localization.font_numeric_formatting.font_numeric_save_load`
Legacy ID: `font_numeric_save_load`
Name: Compiled-C EU Save/Load date and time
Description: Route the six accepted Save/Load numeric fields through typed C entries while retaining only register setup and symbolic hooks at the native call sites.
Evidence ID: `NUN5-SAVE-LOAD-EU-DATETIME`
Review notes: Runtime: The user verified the corrected compiled-C Load and Save paths after a fresh build: both open without freezing and retain DD/MM/YYYY, ASCII HH:MM:SS, and NUN5's 99-hour cap. | The first entry reads day and year from the live record, returns year for the existing callee-saved s6 lifetime, and all seven numeric call-site hooks use linking jal26 so their C entries resume the native functions. Native variadic sprintf ABI remains isolated in two minimal bridges.
#### Patch `localization.font_numeric_formatting.font_numeric_battle_settings`
Legacy ID: `font_numeric_battle_settings`
Name: Compiled-C Battle Settings time
Description: Route only ordinary Battle Settings Time through the shared ASCII C formatting layer while preserving the special 100/infinity path.
Evidence ID: `NUN5-BATTLE-SETTINGS-ASCII-DIGITS`
Review notes: Runtime: The user verified the ordinary below-100 value and the separate 100/infinity behavior after the corrected compiled-C build. | The exact guarded call block uses linking jal26; the preceding infinity branch, selector state, timer value, all other rows, and every other fullwidth formatter caller remain untouched.
#### Patch `localization.font_layout.font_layout_settings_rows`
Legacy ID: `font_layout_settings_rows`
Name: NUN5 Battle and Practice Settings rows
Description: Route the exact Battle Settings and Practice Settings loops through page-level label, heading, compact-token value, descriptive-phrase value, and digit-leading value templates.
Evidence ID: `NUN5-SETTINGS-ROW-BOXES`
Review notes: Static: verified NUN5 BTL FUN_0089CBD0 and FUN_0089EA80 both draw values through the X 304, width 104 boxed renderer; NUN5 selects ASCII font mode for the special Battle time value and clears it for ordinary decimal values. | Runtime: the user accepted the Practice and special Battle value results from captures 20260731224508 and 20260731224409. Supplemental Current/NUN5 slot-1 states both display Time 10; pre-fix Current bounds (432,104)-(455,114) were shorter than NUN5 (433,105)-(457,117). Numeric-only scale 1.02, glyph height 26.0, X +1.8, and Y +1.875 produce exact NUN5 bounds at thresholds 96 and 128 without writing text; all four nonnumeric rows retain their exact pre-change bounds and occupied columns. The user verified the exact supplemental Time 10 result on 2026-07-31.
#### Patch `localization.font_layout.font_layout_ninja_song_details`
Legacy ID: `font_layout_ninja_song_details`
Name: NUN5 Ninja Song objective and arithmetic layout
Description: Replace the shared data-driven formula renderer used by all fifteen rows, retaining its three native formula variants while applying the NUN5 term boxes and positions; wrap every objective through one separate 288x32 prose template.
Evidence ID: `NUN5-NINJA-SONG-DETAIL-BOXES`
Review notes: Static: NA2 FUN_00718C60 draws objectives as unbounded one-line text; NUN5 FUN_0072E9C0 uses a 288x32 two-line box with line-count-dependent baseline placement. NA2 FUN_00718920 is the shared renderer called with per-instance row data and index; NUN5 FUN_0072E5B0 preserves expanded, total-only, and N/A variants while using shared term geometry. | Runtime: the earlier fresh ss3 injection proves the continuously redrawn arithmetic function and its N/A branch. The final-red font2 replay desynchronized before Ninja Song, so the final objective hook remains statically verified but not runtime-proven by that replay.
#### Patch `localization.font_layout.font_layout_linked_mode_modal`
Legacy ID: `font_layout_linked_mode_modal`
Name: Resident Linked Mode centered choices
Description: Apply one shared centered 1.05 horizontal-scale session to both Linked Mode choices while retaining the accepted title, base-row, and interval geometry.
Evidence ID: `NUN5-LINKED-MODE-CENTERED-CHOICES`
Review notes: Static: main-ELF FUN_003B8F40 owns both guarded calls. The selected native call supplies only object, X, Y, and text; its helper always selects red 0xFF0000D4, so the adapter ignores undefined t0 and supplies that native color without changing geometry. The ordinary call shares the same scale and centering. | Runtime: final-red captures 18 and 19 show red selected Auto and Manual with the accepted geometry and no large Font discrepancy; explicit user acceptance of the final color correction is pending.
## qol: binary_patcher
### Selectable node `qol.startup`
Description: Independent startup-sequence skips.
### Selectable node `qol.practice`
Description: Independent Practice-mode default settings.
### Selectable node `qol.mode_select`
Description: Mode availability and selection behavior.
### Selectable node `qol.save_load`
Description: Save and load modal presentation.
#### Patch `qol.startup.skip_cc2_intro`
Legacy ID: `ELF-Q001`
Name: Skip CC2 intro
Description: Skip the CyberConnect2 intro.
Evidence ID: `pnach_intro_skips`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Exact file-backed conversion.
#### Patch `qol.startup.skip_opening`
Legacy ID: `ELF-Q005`
Name: Skip opening
Description: Skip the opening sequence.
Evidence ID: `pnach_intro_skips`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Enabled so the early loading-screen path proceeds directly to the menu transition.
#### Patch `qol.startup.loading_screen_then_main_menu`
Legacy ID: `ELF-Q009`
Name: Loading screen then main menu
Description: Skip the four splash screens and opening, preserve required startup loading, bypass the title, and enter the native main-menu path after the existing loading screen has been shown.
Evidence ID: `startup_splash_controller`
Review notes: Static and savestate-memory evidence identifies the splash, loader, opening, title, loading-screen, and native post-Start state transitions. The runtime-injector hook owns early loading-screen presentation; this binary patch owns the native state transitions. Integrated runtime validation remains pending.
#### Patch `qol.practice.voice_off_by_default`
Legacy ID: `ELF-Q002`
Name: Voice off by default
Description: Start Practice with voice disabled.
Evidence ID: `pnach_practice_qol`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Exact file-backed conversion.
#### Patch `qol.practice.support_off_by_default`
Legacy ID: `ELF-Q006`
Name: Support off by default
Description: Start Practice with support disabled.
Evidence ID: `pnach_practice_qol`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Exact file-backed conversion.
#### Patch `qol.practice.command_display_off_by_default`
Legacy ID: `ELF-Q007`
Name: Command display off by default
Description: Start Practice with command display disabled.
Evidence ID: `pnach_practice_qol`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Exact file-backed conversion.
#### Patch `qol.practice.simple_display_off`
Legacy ID: `ELF-Q003`
Name: Simple display off
Description: Simple-display default control.
Evidence ID: `pnach_simple_display`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Exact file-backed conversion.
#### Patch `qol.mode_select.remove_adventure_mode`
Legacy ID: `ELF-Q004`
Name: Remove Adventure mode
Description: Omit Adventure from Mode Select using the NUN6 negative availability sentinel.
Evidence ID: `nun6_adventure_mode_omission`
Review notes: Runtime: Runtime-proven in the integrated Current ISO: Adventure is absent and the remaining modes work normally. | NUN6 also omits entries 4 and 5; this patch deliberately ports only Adventure at entry 0.
#### Patch `qol.mode_select.remove_shop`
Legacy ID: `ELF-Q008`
Name: Remove Shop
Description: Omit Shop from Mode Select using the same negative availability sentinel as the Adventure omission.
Evidence ID: `na2_shop_mode_omission`
Review notes: Shop is entry 4 of the same seven-entry table; the canonical Restore Shop cheat writes its original value 5 back at runtime.
#### Patch `qol.save_load.display_only_first_save`
Legacy ID: `ELF-Q010`
Name: Display only first save
Description: Render only the first record in the shared Save/Load slot modal.
Evidence ID: `save_load_first_row`
Review notes: Static analysis isolates the row-render loop from the unchanged three-slot occupancy scan and selection handler. Runtime validation remains pending.
## qol: runtime_injector
### Selectable node `qol.startup_loading`
Description: Present a timed loading counter during the boot loader wait.
Review notes: Generated C reuses the proven splash draw phase and its solid-primitive renderer without displaying the original splash sprites, then returns control to the native menu path after startup state 0.
#### Patch `qol.startup_loading.startup_loading_screen`
Legacy ID: `startup_loading_screen`
Name: Timed startup loading screen
Description: Replace the boot splashes with a large primitive percentage and progress bar paced across the measured 25-second load while the original startup loaders run.
Evidence ID: `startup_loading_screen`
Review notes: Both native text paths remained invisible. The first solid-primitive candidate joined separate rectangles into one triangle strip. This candidate submits each rectangle independently and retains the real loader completion checks. Integrated runtime validation remains pending.
## battle_logic: binary_patcher
### Selectable node `battle_logic`
Description: Runtime-proven battle behavior and substitution settings.
Review notes: All Battle Logic patches share one organizational group.
#### Patch `battle_logic.disable_shadowblur_extra_hit`
Legacy ID: `ELF-B001`
Name: Disable Shadowblur Extra Hit
Description: Shadowblur extra-hit behavior.
Evidence ID: `pnach_shadowblur_extra_hit`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Exact file-backed conversion.
#### Patch `battle_logic.disable_extra_hit_with_aura_punishment_for_initiator`
Legacy ID: `ELF-B002`
Name: Disable extra hit with aura punishment for initiator
Description: Extra-hit and aura-punishment behavior.
Evidence ID: `pnach_aura_punishment`
Review notes: Runtime: Runtime-proven in PNACH and confirmed after static migration. | Exact file-backed conversion.
#### Patch `battle_logic.sub_cost_3_15`
Legacy ID: `ELF-S001`
Name: Sub cost = 3/15
Description: Substitution cost setting.
Evidence ID: `pnach_sub_cost`
Review notes: Runtime: Runtime-proven PNACH option; not enabled in the current profile. | Converted from a disabled 16-bit EE write.
## rendering: binary_patcher
### Selectable node `rendering.display`
Description: Game-wide rendering and output geometry.
Review notes: No group-level exceptions.
#### Patch `rendering.display.native_16_9_horizontal_scale`
Legacy ID: `ELF-R001`
Name: Native 16:9 horizontal scale
Description: Force the renderer's horizontal-scale field to 0.75 through its object pointer.
Evidence ID: `official_na2_widescreen_heap_write`
Review notes: Runtime: Static rendering-state writer; replaces the relocation-sensitive heap-address PNACH write. | Good-enough verified implementation; preserves caller-provided vertical scale.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_01` reason: Replace the two open-state horizontal-arrow blocks with a branch plus a draw-scoped helper: enable NA2 sprite mode 1, apply the lower-arrow flip from the signed NUN5 angle, draw and flush while that mode is active, restore mode 0, and return without using the shared header cave.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_02` reason: Copy NUN5's exact +pi/2 upper-arrow rotation load into an otherwise unused NA2 pipeline slot.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_03` reason: Copy NUN5's exact +pi/2 upper-arrow immediate.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_04` reason: Route the upper vertical-arrow draw through the draw-scoped helper at loaded BTL address 0x006BD9C4.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_05` reason: Store the exact loaded +pi/2 value in the arrow sprite before entering the helper.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_06` reason: Copy NUN5's exact -pi/2 lower-arrow rotation load into an otherwise unused NA2 pipeline slot.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_07` reason: Copy NUN5's exact -pi/2 lower-arrow immediate.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_08` reason: Route the lower vertical-arrow draw through the same draw-scoped helper.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_09` reason: Store the exact loaded -pi/2 value in the arrow sprite before entering the helper.
Edit `localization.ui_layout.ui_layout_jutsu_selector_arrows.edits.ui_layout_jutsu_selector_arrows_10` reason: Copy the official NUN5 localized green-arrow record (145,385,22,38) used by both rotated indicators.
Edit `localization.ui_layout.ui_layout_command_scroll_arrows.edits.ui_layout_command_scroll_arrows_01` reason: Copy NUN5's shared TEX_xselect vertical-scroll triangle rectangle (1,225,20,22) for both Command Menu and Command Chart.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_01` reason: Set the secondary descriptor to native 14x20 packed cells with a 140-byte stride and 123 reachable entries while retaining its original 24x28 output quad.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_02` reason: Pack each NUN5-format secondary metric row into the value word of one ascending empty primary hash slot while preserving every key and every occupied primary entry.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_03` reason: Import exact NUN5 14x20 geometry for same-semantic English glyphs, relocate its at-sign cell, reconstruct unsupported cells from clean NA2, and quantize donor coverage into the unchanged clean GF4C palette.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_04` reason: Bound only the secondary draw-path cell index to 0..122 and use blank cell 0 for negative or larger indices; preserve the shared parser and primary font.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_05` reason: Route the secondary raster lookup through its local 123-cell guard while retaining the displaced descriptor load in the jump delay slot.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_06` reason: Initialize the decoder's local horizontal scale word to 1.0 so the native glyph patch remains correct when applied without Controls auto-fit.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_07` reason: Select descriptor width for primary/fullwidth glyphs or descriptor height for secondary glyphs, compute only the normal quad bottom edge, and rejoin the untouched renderer path from guarded linker padding.
Edit `localization.font_glyphs.font_glyphs_native.edits.font_glyphs_native_08` reason: Route only the normal glyph bottom-edge calculation through the glyph-owned secondary-height helper while reading the existing secondary-font mode bit in the jump delay slot.
Edit `localization.font_layout.font_layout_character_modal.edits.font_layout_character_modal_01` reason: Store the five user-reviewed native-font row X positions 81.75, 73.375, 72.375, 63.5, and 3.5 in proven cross-game linker padding outside external-translation ownership.
Edit `localization.font_layout.font_layout_character_modal.edits.font_layout_character_modal_02` reason: Load every row X from the user-reviewed local table, retain the clean ordinary-row Y origin, and place the fifth row at local Y 115.
Edit `localization.font_layout.font_layout_linked_mode_modal.edits.font_layout_linked_mode_modal_01` reason: Move only the Linked Mode title origin from local Y 12 to local Y 8.
Edit `localization.font_layout.font_layout_linked_mode_modal.edits.font_layout_linked_mode_modal_02` reason: Set the shared Linked Mode choice interval to 22 local units so both highlight states retain the NUN5 row separation.
Edit `localization.font_layout.font_layout_linked_mode_modal.edits.font_layout_linked_mode_modal_03` reason: Set the Linked Mode choice-list base to local Y 45; both choices retain one shared interval and no state-specific position.
Edit `localization.font_numeric_formatting.font_numeric_save_load_separator.edits.font_numeric_save_load_separator_01` reason: Replace the Save/Load-only fullwidth colon constant with ASCII colon for the now-ASCII time fields.
Edit `localization.font_layout.font_layout_on_off_context.edits.font_layout_on_off_context_01` reason: Point the Practice Settings Commands row at the existing title-case Off/On selector table.
Edit `localization.font_layout.font_layout_on_off_context.edits.font_layout_on_off_context_02` reason: Point the Practice Settings Damage row at the existing title-case Off/On selector table.
Edit `localization.font_layout.font_layout_on_off_context.edits.font_layout_on_off_context_03` reason: Point the Practice Settings Guide Ninja Sound row at the existing title-case Off/On selector table.
Edit `localization.font_layout.font_layout_command_relationships.edits.font_layout_command_relationships_01` reason: Suppress the second exact native Command Chart auxiliary-string draw after the generated-C first-call adapter has combined record bytes +4 and +5; preserve the surrounding setup and following native icon loop.
Edit `localization.regional_input.regional_input_candidate_001.edits.regional_input_candidate_001_01` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_001.edits.regional_input_candidate_001_02` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_001.edits.regional_input_candidate_001_03` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_001.edits.regional_input_candidate_001_04` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_001.edits.regional_input_candidate_001_05` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_002.edits.regional_input_candidate_002_01` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_002.edits.regional_input_candidate_002_02` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_002.edits.regional_input_candidate_002_03` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_002.edits.regional_input_candidate_002_04` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_003.edits.regional_input_candidate_003_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_003.edits.regional_input_candidate_003_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_004.edits.regional_input_candidate_004_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_004.edits.regional_input_candidate_004_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_005.edits.regional_input_candidate_005_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_005.edits.regional_input_candidate_005_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_006.edits.regional_input_candidate_006_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_006.edits.regional_input_candidate_006_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_007.edits.regional_input_candidate_007_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_008.edits.regional_input_candidate_008_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_008.edits.regional_input_candidate_008_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_009.edits.regional_input_candidate_009_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_009.edits.regional_input_candidate_009_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_010.edits.regional_input_candidate_010_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_011.edits.regional_input_candidate_011_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_011.edits.regional_input_candidate_011_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_012.edits.regional_input_candidate_012_01` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_012.edits.regional_input_candidate_012_02` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_012.edits.regional_input_candidate_012_03` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_013.edits.regional_input_candidate_013_01` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_013.edits.regional_input_candidate_013_02` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_013.edits.regional_input_candidate_013_03` reason: BTL-owned battle-adjacent UI/state input range. Contains a multi-button regional permutation, not merely a single confirm literal.
Edit `localization.regional_input.regional_input_candidate_014.edits.regional_input_candidate_014_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_014.edits.regional_input_candidate_014_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_015.edits.regional_input_candidate_015_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_015.edits.regional_input_candidate_015_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_016.edits.regional_input_candidate_016_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_017.edits.regional_input_candidate_017_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_018.edits.regional_input_candidate_018_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_pause_commands.edits.regional_input_pause_commands_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_pause_commands.edits.regional_input_pause_commands_02` reason: ccStartMenuPrivateCmd player/view branch: use Cross for the NUN5 operation path.
Edit `localization.regional_input.regional_input_pause_commands.edits.regional_input_pause_commands_03` reason: ccStartMenuPrivateCmd close branch: use Triangle for NUN5 cancel.
Edit `localization.regional_input.regional_input_candidate_019.edits.regional_input_candidate_019_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_019.edits.regional_input_candidate_019_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_020.edits.regional_input_candidate_020_01` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_candidate_020.edits.regional_input_candidate_020_02` reason: BTL-owned battle-adjacent UI/state input range.
Edit `localization.regional_input.regional_input_save_load_parent.edits.regional_input_save_load_parent_01` reason: Multi-state front-end prompt/message controller with six confirm-only branches.
Edit `localization.regional_input.regional_input_save_load_parent.edits.regional_input_save_load_parent_02` reason: Multi-state front-end prompt/message controller with six confirm-only branches.
Edit `localization.regional_input.regional_input_save_load_parent.edits.regional_input_save_load_parent_03` reason: Multi-state front-end prompt/message controller with six confirm-only branches.
Edit `localization.regional_input.regional_input_save_load_parent.edits.regional_input_save_load_parent_04` reason: Multi-state front-end prompt/message controller with six confirm-only branches.
Edit `localization.regional_input.regional_input_save_load_parent.edits.regional_input_save_load_parent_05` reason: Multi-state front-end prompt/message controller with six confirm-only branches.
Edit `localization.regional_input.regional_input_save_load_parent.edits.regional_input_save_load_parent_06` reason: Multi-state front-end prompt/message controller with six confirm-only branches.
Edit `localization.regional_input.regional_input_save_load_confirmation.edits.regional_input_save_load_confirmation_01` reason: Paired confirm/cancel modal or list-state handler.
Edit `localization.regional_input.regional_input_save_load_confirmation.edits.regional_input_save_load_confirmation_02` reason: Paired confirm/cancel modal or list-state handler.
Edit `localization.regional_input.regional_input_save_load_acknowledgment.edits.regional_input_save_load_acknowledgment_01` reason: Simple confirm-to-close/advance handler.
Edit `localization.regional_input.regional_input_animated_transition.edits.regional_input_animated_transition_01` reason: Confirm-gated state transition after an animation/object becomes active.
Edit `localization.regional_input.regional_input_player_transition.edits.regional_input_player_transition_01` reason: Player-indexed confirm-gated transition handler.
Edit `localization.regional_input.regional_input_timed_prompt.edits.regional_input_timed_prompt_01` reason: Two-state timed prompt controller with confirm acceleration/advance.
Edit `localization.regional_input.regional_input_timed_prompt.edits.regional_input_timed_prompt_02` reason: Two-state timed prompt controller with confirm acceleration/advance.
Edit `localization.regional_input.regional_input_player_list.edits.regional_input_player_list_01` reason: Player-indexed list/prompt handler with confirm and directional navigation.
Edit `localization.regional_input.regional_input_selectable_modal.edits.regional_input_selectable_modal_01` reason: Generic selectable-list/modal input decoder. It sets distinct result flags for accept, cancel, and navigation.
Edit `localization.regional_input.regional_input_selectable_modal.edits.regional_input_selectable_modal_02` reason: Generic selectable-list/modal input decoder. It sets distinct result flags for accept, cancel, and navigation.
Edit `localization.regional_input.regional_input_menu_parent.edits.regional_input_menu_parent_01` reason: Parent menu state machine wrapping child selectable objects and confirm/cancel transitions.
Edit `localization.regional_input.regional_input_menu_parent.edits.regional_input_menu_parent_02` reason: Parent menu state machine wrapping child selectable objects and confirm/cancel transitions.
Edit `localization.regional_input.regional_input_control_assignment.edits.regional_input_control_assignment_01` reason: Controller/button-assignment options handler with reset, confirm, cancel, and directional edits.
Edit `localization.regional_input.regional_input_control_assignment.edits.regional_input_control_assignment_02` reason: Controller/button-assignment options handler with reset, confirm, cancel, and directional edits.
Edit `localization.regional_input.regional_input_numeric_adjustment.edits.regional_input_numeric_adjustment_01` reason: Two-axis numeric adjustment handler with reset, confirm, cancel, and directional edits.
Edit `localization.regional_input.regional_input_numeric_adjustment.edits.regional_input_numeric_adjustment_02` reason: Two-axis numeric adjustment handler with reset, confirm, cancel, and directional edits.
Edit `localization.regional_input.regional_input_four_way_options.edits.regional_input_four_way_options_01` reason: Four-way options/submenu handler with confirm/cancel state transitions.
Edit `localization.regional_input.regional_input_four_way_options.edits.regional_input_four_way_options_02` reason: Four-way options/submenu handler with confirm/cancel state transitions.
Edit `localization.regional_input.regional_input_numeric_selector.edits.regional_input_numeric_selector_01` reason: Numeric/list selector with confirm, cancel, and vertical navigation.
Edit `localization.regional_input.regional_input_numeric_selector.edits.regional_input_numeric_selector_02` reason: Numeric/list selector with confirm, cancel, and vertical navigation.
Edit `localization.regional_input.regional_input_player_join.edits.regional_input_player_join_01` reason: Two-player join/selection state machine; the differing checks are cancel/back actions.
Edit `localization.regional_input.regional_input_player_join.edits.regional_input_player_join_02` reason: Two-player join/selection state machine; the differing checks are cancel/back actions.
Edit `localization.regional_input.regional_input_five_item_selector.edits.regional_input_five_item_selector_01` reason: Five-item selector with confirm, cancel, and cyclic vertical navigation.
Edit `localization.regional_input.regional_input_five_item_selector.edits.regional_input_five_item_selector_02` reason: Five-item selector with confirm, cancel, and cyclic vertical navigation.
Edit `localization.regional_input.regional_input_save_load_confirm.edits.regional_input_save_load_confirm_01` reason: Save/load confirm-only helper used repeatedly by the parent controller.
Edit `localization.regional_input.regional_input_save_load_prompt.edits.regional_input_save_load_prompt_01` reason: Blocking memory-card/save-load prompt loop with confirm-to-advance behavior.
Edit `localization.regional_input.regional_input_overlay_close.edits.regional_input_overlay_close_01` reason: Confirm-to-close overlay rendered inside another front-end object.
Edit `localization.regional_input.regional_input_player_action_decoder.edits.regional_input_player_action_decoder_01` reason: Two-player multi-action front-end input decoder: first accept path.
Edit `localization.regional_input.regional_input_player_action_decoder.edits.regional_input_player_action_decoder_02` reason: Two-player multi-action front-end input decoder: second accept path.
Edit `localization.regional_input.regional_input_player_action_decoder.edits.regional_input_player_action_decoder_03` reason: Two-player multi-action front-end input decoder: cancel path.
Edit `localization.regional_input.regional_input_control_assignment_player.edits.regional_input_control_assignment_player_01` reason: Second controller-assignment subhandler: accept path.
Edit `localization.regional_input.regional_input_control_assignment_player.edits.regional_input_control_assignment_player_02` reason: Second controller-assignment subhandler: cancel path.
Edit `localization.regional_input.regional_input_sound_settings.edits.regional_input_sound_settings_01` reason: Sound Settings handler: accept path.
Edit `localization.regional_input.regional_input_sound_settings.edits.regional_input_sound_settings_02` reason: Sound Settings handler: rollback/cancel path.
Edit `localization.regional_input.regional_input_delayed_advance.edits.regional_input_delayed_advance_01` reason: Timed confirm-to-advance state after a short input delay.
Edit `localization.regional_input.regional_input_two_item_submenu.edits.regional_input_two_item_submenu_01` reason: Two-item front-end/setup submenu: accept path.
Edit `localization.regional_input.regional_input_two_item_submenu.edits.regional_input_two_item_submenu_02` reason: Two-item front-end/setup submenu: cancel path.
Edit `localization.regional_input.regional_input_yes_no_modal.edits.regional_input_yes_no_modal_01` reason: Shared two-choice Yes/No modal accept check.
Edit `localization.regional_input.regional_input_yes_no_modal.edits.regional_input_yes_no_modal_02` reason: Shared two-choice Yes/No modal cancel check.
Edit `localization.regional_input.regional_input_title_controller.edits.regional_input_title_controller_01` reason: Title controller combined Start/accept check.
Edit `localization.regional_input.regional_input_title_controller.edits.regional_input_title_controller_02` reason: Title controller combined Start/accept/cancel check.
Edit `localization.regional_input.regional_input_character_selection.edits.regional_input_character_selection_01` reason: Character-selection primary-state accept check.
Edit `localization.regional_input.regional_input_character_selection.edits.regional_input_character_selection_02` reason: Character-selection primary-state cancel check.
Edit `localization.regional_input.regional_input_character_selection.edits.regional_input_character_selection_03` reason: Character-selection primary-state operation1 check.
Edit `localization.regional_input.regional_input_character_selection.edits.regional_input_character_selection_04` reason: Character-selection secondary-state accept check.
Edit `localization.regional_input.regional_input_character_selection.edits.regional_input_character_selection_05` reason: Character-selection secondary-state cancel check.
Edit `localization.regional_input.regional_input_character_selection.edits.regional_input_character_selection_06` reason: Character-selection secondary-state operation1 check.
Edit `localization.regional_input.regional_input_new_game_continue.edits.regional_input_new_game_continue_01` reason: Title New Game/Continue combined Start/accept check.
Edit `localization.regional_input.regional_input_support_selection.edits.regional_input_support_selection_01` reason: Support-selection first-state accept check.
Edit `localization.regional_input.regional_input_support_selection.edits.regional_input_support_selection_02` reason: Support-selection first-state cancel check.
Edit `localization.regional_input.regional_input_support_selection.edits.regional_input_support_selection_03` reason: Support-selection first-state operation1 check.
Edit `localization.regional_input.regional_input_support_selection.edits.regional_input_support_selection_04` reason: Support-selection second-state accept check.
Edit `localization.regional_input.regional_input_support_selection.edits.regional_input_support_selection_05` reason: Support-selection second-state cancel check.
Edit `localization.regional_input.regional_input_support_selection.edits.regional_input_support_selection_06` reason: Support-selection second-state operation1 check.
Edit `localization.regional_input.regional_input_candidate_021.edits.regional_input_candidate_021_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_021.edits.regional_input_candidate_021_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_022.edits.regional_input_candidate_022_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_022.edits.regional_input_candidate_022_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_023.edits.regional_input_candidate_023_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_023.edits.regional_input_candidate_023_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_024.edits.regional_input_candidate_024_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_024.edits.regional_input_candidate_024_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_025.edits.regional_input_candidate_025_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_025.edits.regional_input_candidate_025_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_026.edits.regional_input_candidate_026_01` reason: ETC-owned front-end input decision range. Includes the regional secondary-action Triangle-to-Square move.
Edit `localization.regional_input.regional_input_candidate_026.edits.regional_input_candidate_026_02` reason: ETC-owned front-end input decision range. Includes the regional secondary-action Triangle-to-Square move.
Edit `localization.regional_input.regional_input_candidate_027.edits.regional_input_candidate_027_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_027.edits.regional_input_candidate_027_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_028.edits.regional_input_candidate_028_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_028.edits.regional_input_candidate_028_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_029.edits.regional_input_candidate_029_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_030.edits.regional_input_candidate_030_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_030.edits.regional_input_candidate_030_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_031.edits.regional_input_candidate_031_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_031.edits.regional_input_candidate_031_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_032.edits.regional_input_candidate_032_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_032.edits.regional_input_candidate_032_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_033.edits.regional_input_candidate_033_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_034.edits.regional_input_candidate_034_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_034.edits.regional_input_candidate_034_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_035.edits.regional_input_candidate_035_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_035.edits.regional_input_candidate_035_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_036.edits.regional_input_candidate_036_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_036.edits.regional_input_candidate_036_02` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_037.edits.regional_input_candidate_037_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_038.edits.regional_input_candidate_038_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_candidate_039.edits.regional_input_candidate_039_01` reason: ETC-owned front-end input decision range. Implements regional accept/cancel or confirm-only behavior.
Edit `localization.regional_input.regional_input_battle_results_tally.edits.regional_input_battle_results_tally_01` reason: Battle-results tally fast-forward: use Cross instead of the inherited Circle check; NUN5 retains the same Circle oversight at BTL offset 0x000692B0.
Edit `localization.ui_layout.ui_layout_ultimate_jutsu_label.edits.ui_layout_ultimate_jutsu_label_01` reason: Match the one-part English OUGI label layout used by both NUN5 and NUN6.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_01` reason: Use the matched loop index directly so the redundant per-record index word can hold the stage-name scale.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_02` reason: Preserve the original 1.0 vertical stage-name scale in f15 instead of copying the horizontal fit into both axes.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_03` reason: Load the precomputed NUN5-equivalent horizontal fit from the selected 16-byte stage record into f14.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_04` reason: Recover the preview index as row_offset >> 4 instead of interpreting the repurposed scale word as an atlas index.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_05` reason: Copy the exact NUN5 X=260 instruction for the Random prompt item.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_06` reason: Copy the exact NUN5 X=260 instruction for the Random prompt companion sprite.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_07` reason: Use X=388 for the Stage Select OK prompt, reproducing NUN5's effective 400-12 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_08` reason: Use X=462 for the Stage Select Back prompt, reproducing NUN5's effective 470-8 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_09` reason: Store the NUN5-equivalent horizontal scale for stage row 0 (232px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_10` reason: Store the NUN5-equivalent horizontal scale for stage row 1 (232px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_11` reason: Store the NUN5-equivalent horizontal scale for stage row 2 (272px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_12` reason: Store the NUN5-equivalent horizontal scale for stage row 3 (208px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_13` reason: Store the NUN5-equivalent horizontal scale for stage row 4 (344px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_14` reason: Store the NUN5-equivalent horizontal scale for stage row 5 (160px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_15` reason: Store the NUN5-equivalent horizontal scale for stage row 6 (168px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_16` reason: Store the NUN5-equivalent horizontal scale for stage row 7 (240px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_17` reason: Store the NUN5-equivalent horizontal scale for stage row 8 (288px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_18` reason: Store the NUN5-equivalent horizontal scale for stage row 9 (200px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_19` reason: Store the NUN5-equivalent horizontal scale for stage row 10 (216px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_20` reason: Store the NUN5-equivalent horizontal scale for stage row 11 (216px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_21` reason: Store the NUN5-equivalent horizontal scale for stage row 12 (256px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_22` reason: Store the NUN5-equivalent horizontal scale for stage row 13 (256px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_23` reason: Store the NUN5-equivalent horizontal scale for stage row 14 (304px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_24` reason: Store the NUN5-equivalent horizontal scale for stage row 15 (152px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_25` reason: Store the NUN5-equivalent horizontal scale for stage row 16 (168px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_26` reason: Store the NUN5-equivalent horizontal scale for stage row 17 (176px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_27` reason: Store the NUN5-equivalent horizontal scale for stage row 18 (264px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_28` reason: Store the NUN5-equivalent horizontal scale for stage row 19 (256px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_29` reason: Store the NUN5-equivalent horizontal scale for stage row 20 (192px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_30` reason: Store the NUN5-equivalent horizontal scale for stage row 21 (168px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_31` reason: Store the NUN5-equivalent horizontal scale for stage row 22 (280px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_32` reason: Store the NUN5-equivalent horizontal scale for stage row 23 (184px source width).
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_33` reason: Copy official NUN5 stage-name UV rectangle row 0.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_34` reason: Copy official NUN5 stage-name UV rectangle row 1.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_35` reason: Copy official NUN5 stage-name UV rectangle row 2.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_36` reason: Copy official NUN5 stage-name UV rectangle row 3.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_37` reason: Copy official NUN5 stage-name UV rectangle row 4.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_38` reason: Copy official NUN5 stage-name UV rectangle row 5.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_39` reason: Copy official NUN5 stage-name UV rectangle row 6.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_40` reason: Copy official NUN5 stage-name UV rectangle row 7.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_41` reason: Copy official NUN5 stage-name UV rectangle row 8.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_42` reason: Copy official NUN5 stage-name UV rectangle row 9.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_43` reason: Copy official NUN5 stage-name UV rectangle row 10.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_44` reason: Copy official NUN5 stage-name UV rectangle row 11.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_45` reason: Copy official NUN5 stage-name UV rectangle row 12.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_46` reason: Copy official NUN5 stage-name UV rectangle row 13.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_47` reason: Copy official NUN5 stage-name UV rectangle row 14.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_48` reason: Copy official NUN5 stage-name UV rectangle row 15.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_49` reason: Copy official NUN5 stage-name UV rectangle row 16.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_50` reason: Copy official NUN5 stage-name UV rectangle row 17.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_51` reason: Copy official NUN5 stage-name UV rectangle row 18.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_52` reason: Copy official NUN5 stage-name UV rectangle row 19.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_53` reason: Copy official NUN5 stage-name UV rectangle row 20.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_54` reason: Copy official NUN5 stage-name UV rectangle row 21.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_55` reason: Copy official NUN5 stage-name UV rectangle row 22.
Edit `localization.ui_layout.ui_layout_stage_select.edits.ui_layout_stage_select_56` reason: Copy official NUN5 stage-name UV rectangle row 23.
Edit `localization.ui_layout.ui_layout_character_name_rectangles.edits.ui_layout_character_name_rectangles_01` reason: Copy the complete official NUN5 English 96-entry character-name atlas rectangle table selected by the localized name accessor.
Edit `localization.ui_layout.ui_layout_options_labels.edits.ui_layout_options_labels_01` reason: Copy the complete official NUN5 English Options-menu and difficulty-label atlas rectangle tables, including their shared zero separator.
Edit `localization.ui_layout.ui_layout_difficulty_sprite.edits.ui_layout_difficulty_sprite_01` reason: Route valid difficulty indices 4 and 5, plus 0, through the alternate sprite object exactly as NUN5 does.
Edit `localization.ui_layout.ui_layout_battle_hud_names.edits.ui_layout_battle_hud_names_01` reason: Install a size-preserving helper in verified loaded zero padding that computes display width as min(source width, 160) times the existing scale.
Edit `localization.ui_layout.ui_layout_battle_hud_names.edits.ui_layout_battle_hud_names_02` reason: Call the width-fitting helper at live EE 0x006B3F40 and pass the official NUN5 160-pixel cap in the original height-load delay slot.
Edit `localization.ui_layout.ui_layout_practice_settings_prompt.edits.ui_layout_practice_settings_prompt_01` reason: Copy the structurally equivalent official NUN5 Practice Settings X=100 instruction.
Edit `localization.ui_layout.ui_layout_practice_settings_prompt.edits.ui_layout_practice_settings_prompt_02` reason: Copy the official NUN5 English Practice Settings UV rectangle (0, 280, 176, 24).
Edit `localization.ui_layout.ui_layout_battle_hud_name_rectangles.edits.ui_layout_battle_hud_name_rectangles_01` reason: Copy the complete official NUN5 English 95-entry battle-HUD character-name atlas rectangle table selected by the localized accessor.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_01` reason: Install the size-preserving Jutsu-label placement helper in verified loaded zero padding immediately before the disjoint stage-width helper.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_02` reason: Call the relocated localized Jutsu-label placement helper instead of copying the unadjusted base X coordinate.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_03` reason: Copy the structurally equivalent official NUN5 instruction that loads the 40-pixel input-glyph offset.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_04` reason: Copy the structurally equivalent official NUN5 instruction that moves the 40-pixel offset into the input accumulator.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_05` reason: Copy only NUN5's X=260 immediate halfword while preserving NA2's v0 destination register; exact runtime testing proved the full prompt does not wrap.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_06` reason: Move Battle Settings from X=60 to the official NUN5 X=94 anchor so the localized 160-pixel prompt is not clipped.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_07` reason: Copy the official NUN5 Customize Jutsu rectangle (0,232,168,24).
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_08` reason: Copy the official NUN5 Battle Settings rectangle (0,256,160,24).
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_09` reason: Copy the official NUN5 two-arrow control rectangle and remove the unrelated atlas strip drawn by NA2's regional coordinates.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_10` reason: Copy official NUN5 Jutsu input-glyph rectangle 1.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_11` reason: Copy official NUN5 Jutsu input-glyph rectangle 2.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_12` reason: Copy official NUN5 Jutsu input-glyph rectangle 3.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_13` reason: Copy the official NUN5 Jutsu1 label rectangle (1,1,62,26).
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_14` reason: Copy the official NUN5 Jutsu2 label rectangle (65,1,62,26).
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_15` reason: Copy the complete official NUN5 Cross/OK and Triangle/Back records (56x22 and 64x22) into NA2's homologous boot-ELF table.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_16` reason: Disable NA2's separate regional input-glyph draw for OK because the imported NUN5 record already contains the complete glyph and label.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_17` reason: Disable the same redundant regional input-glyph draw for Back.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_18` reason: Use the calibrated NA2 OK anchor X=388; paired rendering proves this produces the same raster position as NUN5's X=400 path.
Edit `localization.ui_layout.ui_layout_vs_confirmation.edits.ui_layout_vs_confirmation_19` reason: Use the calibrated NA2 Back anchor X=462; paired rendering proves this produces the same raster position as NUN5's X=470 path.
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_01` reason: Move the Round label base X from 216 to the official NUN5 X=256.
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_02` reason: Move the Round label base Y from 44 to the official NUN5 Y=24.
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_03` reason: Replace the first Japanese Round glyph rectangle with the official one-part NUN5 English Round rectangle (129,1,94,30).
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_04` reason: Disable the second Japanese Round glyph after replacing the first with the one-part English label.
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_05` reason: Copy the structurally equivalent official NUN5 1.2 Round centering-scale instructions.
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_06` reason: Copy the structurally equivalent official NUN5 Y=64 Round render instruction.
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_07` reason: Copy the structurally equivalent official NUN5 1.2 Round render-scale instructions.
Edit `localization.ui_layout.ui_layout_round_label.edits.ui_layout_round_label_08` reason: Copy the structurally equivalent official NUN5 1.2 Round spacing-scale instructions.
Edit `localization.ui_layout.ui_layout_mode_select.edits.ui_layout_mode_select_01` reason: Copy the official NUN5 English Mode Select START-label rectangle (1,393,254,26).
Edit `localization.ui_layout.ui_layout_mode_select.edits.ui_layout_mode_select_02` reason: Move the START label from X=130 to NUN5's X=150 while retaining NA2's v0 destination register required by the following instruction.
Edit `localization.ui_layout.ui_layout_mode_select.edits.ui_layout_mode_select_03` reason: Use X=388 for the Mode Select OK prompt, reproducing NUN5's effective 400-12 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_mode_select.edits.ui_layout_mode_select_04` reason: Use X=462 for the Mode Select Back prompt, reproducing NUN5's effective 470-8 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_controls_vibration.edits.ui_layout_controls_vibration_01` reason: Copy the official NUN5 English Vibration-label rectangle (64, 88, 64, 20) used by the imported common UI atlas.
Edit `localization.ui_layout.ui_layout_character_select_footer.edits.ui_layout_character_select_footer_01` reason: Copy NUN5's exact `lui v0,0x4382` instruction, moving the imported Random footer record from X=300 to X=260.
Edit `localization.ui_layout.ui_layout_character_select_footer.edits.ui_layout_character_select_footer_02` reason: Copy NUN5's exact `lui v0,0x42c8` instruction, moving the imported Select Color footer record from X=160 to X=100.
Edit `localization.ui_layout.ui_layout_character_select_footer.edits.ui_layout_character_select_footer_03` reason: Use X=388 for the Character Select OK prompt, reproducing NUN5's effective 400-12 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_character_select_footer.edits.ui_layout_character_select_footer_04` reason: Use X=462 for the Character Select Back prompt, reproducing NUN5's effective 470-8 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_01` reason: Copy NUN5 localized common-prompt record 6, replacing the Japanese Triangle-icon rectangle used first by the shared Cancel compositor.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_02` reason: Copy NUN5 localized common-prompt record 4, replacing the 114-pixel Japanese Cancel label with the 56-pixel English label.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_03` reason: Copy NUN5 localized common-prompt record 5, removing the Japanese-only 42-pixel tail from the shared Cancel compositor.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_04` reason: Copy NUN5 localized common-prompt record 2, narrowing the shared Next label from 70 to 66 pixels so its donor atlas geometry and centered anchor match.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_05` reason: Use X=388 for the Options-root OK prompt, reproducing NUN5's effective 400-12 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_06` reason: Use X=462 for the Options-root Back prompt, reproducing NUN5's effective 470-8 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_07` reason: Use X=368 for the Collection-root Cross prompt, reproducing NUN5's effective 380-12 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_08` reason: Use X=452 for the Collection-root Triangle prompt, reproducing NUN5's effective 460-8 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_09` reason: Install a four-instruction HOME prompt tail-call wrapper in load-preserved MWO3 header padding: move the caller's exact float delta from v1 to f0, add it to f12, and tail-call NA2's existing common compositor. NUN5's GP-relative regional globals and language accessors are not ABI-compatible donor code.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_10` reason: Route HOME helper state 1 through the guarded wrapper and load -12.0 in its delay slot, reproducing NUN5's Cross regional X offset for every caller.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_11` reason: Route HOME helper state 2 through the guarded wrapper and load -24.0 in its delay slot, reproducing NUN5's localized Play icon/label centering result without porting incompatible language accessors.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_12` reason: Route HOME helper state 3 through the guarded wrapper and load -8.0 in its delay slot, reproducing NUN5's Triangle regional X offset for every caller.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_13` reason: Use -59.0 for the HOME state-2 label-local X offset so the Play label follows the same 24-pixel localized centering shift as its icon.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_14` reason: Copy the official NUN5 Stop rectangle (144,48,76,24) over NA2's Japanese-atlas rectangle (120,48,72,24).
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_15` reason: Route HOME helper state 4 through the existing guarded wrapper with -2.0, reproducing NUN5's effective Triangle-prompt anchor 460 + (76-64)/2 - 8 = 458.
Edit `localization.ui_layout.ui_layout_common_prompts.edits.ui_layout_common_prompts_16` reason: Use -40.0 for the HOME state-4 label-local X offset, reproducing NUN5's Stop-label anchor 458 - 76/2 = 420 while retaining the already-matching Y=348.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_01` reason: Copy NUN5's exact `lui v0,0x4348` instruction for the Controls Select-icon call, moving its X anchor from 230 to 200.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_02` reason: Copy NUN5's exact `lui v0,0x4348` instruction for the Controls Select-legend call, keeping the texture paired with its icon.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_03` reason: Copy NUN5's exact `lui v0,0x4348` instruction for the Music Options Select-icon call, moving its X anchor from 230 to 200.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_04` reason: Copy NUN5's exact `lui v0,0x4348` instruction for the Music Options Select-legend call, keeping the texture paired with its icon.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_05` reason: Use X=388 for the Music Settings OK prompt, reproducing NUN5's effective 400-12 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_06` reason: Use X=462 for the Music Settings Back prompt, reproducing NUN5's effective 470-8 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_07` reason: Use X=388 for the Control Settings OK prompt, reproducing NUN5's effective 400-12 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_options_footers.edits.ui_layout_options_footers_08` reason: Use X=462 for the Control Settings Back prompt, reproducing NUN5's effective 470-8 anchor where NA2 lacks the regional offset addition.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_01` reason: Copy NUN5's complete paired Collection page-prompt center table: Previous Page X=87, Next Page X=233, both Y=360.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_02` reason: Copy NUN5's complete paired Collection page-prompt atlas rectangles, widening both entries from 118 to 144 pixels.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_03` reason: Copy NUN5's Characters rectangle (0,0,192,28), excluding the Movie-row pixels selected by NA2's 34-pixel source height.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_04` reason: Copy NUN5's Movie rectangle (0,28,96,28), preventing NA2's 34-pixel rectangle from sampling the Music row.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_05` reason: Copy NUN5's Music rectangle (0,56,96,28), replacing NA2's source range outside the imported English title rows.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_06` reason: Copy NUN5's Play rectangle (144,24,72,24); NA2's X=120 rectangle starts 24 pixels before the imported English control and clips the label.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_07` reason: Copy NUN5's complete four-record Collection viewer-control position table, changing NA2's single bottom row into the official 2x2 Zoom In/Zoom Out and Move/Rotate layout.
Edit `localization.ui_layout.ui_layout_collection_submenu.edits.ui_layout_collection_submenu_08` reason: Copy NUN5's complete four-record Collection viewer-control rectangle table so Zoom In and Zoom Out select the full English artwork; Move and Rotate remain paired in the same semantic block.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_01` reason: Port the NUN5 anisotropic sprite-call contract into NA2's homologous resident renderer while preserving NA2 register and stack layout.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_02` reason: Use the ported horizontal scale register in renderer branch 1.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_03` reason: Use the ported horizontal scale register in renderer branch 2.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_04` reason: Use the ported horizontal scale register in renderer branch 3.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_05` reason: Use the ported horizontal scale register in renderer branch 4.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_06` reason: Preserve the additional floating-point renderer parameter in the existing stack frame.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_07` reason: Store the second anisotropic scale component in the ported renderer frame.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_08` reason: Restore the saved renderer parameter before returning.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_09` reason: Copy official NUN5 paired item-status records 0x8E through 0x94.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_10` reason: Copy official NUN5 paired item-status records 0x9B and 0x9C.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_11` reason: Copy the complete official NUN5 three-rank item-bubble offset table.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_12` reason: Retain the accepted pair width path while assigning the traced donor scales to every concrete class: 1.90625/1.0 for single labels, exactly 1.59375 for fixed labels, and 1.25 for numeric recovery.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_13` reason: Store the pair-event scale table derived exactly from official NUN5 record widths and its 65-pixel normalization threshold.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_14` reason: Install the NA2-ABI wrapper that passes donor horizontal scale, neutral vertical scale, and the donor quarter-turn to the lower sprite renderer.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_15` reason: Generalize the runtime-proven pair helper so pair and numeric callers explicitly supply X anchor, Y bias, row, and angle-output storage while preserving the NA2 object ABI.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_16` reason: Call the ABI-safe width-scale helper from the common item-bubble update.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_17` reason: Clamp the bubble center using the helper-produced display width without changing NA2 object fields.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_18` reason: Remove NA2's regional negative 33-pixel X origin shift.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_19` reason: Use the official NUN5 negative 33-pixel Y origin instead of NA2's negative 42-pixel origin.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_20` reason: Route the bubble background through the anisotropic compatibility wrapper and resume the common draw path.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_21` reason: Route paired row 1 through the generalized helper with neutral X/Y adjustments and stack-local angle output.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_22` reason: Load the helper-produced paired-row 1 rotation in the renderer delay slot.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_23` reason: Route paired row 2 through the generalized helper with neutral X/Y adjustments and stack-local angle output.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_24` reason: Load the helper-produced paired-row 2 rotation in the renderer delay slot.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_25` reason: Clear the new rotation argument for the first fixed-status foreground caller.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_26` reason: Clear the new rotation argument for the second fixed-status foreground caller.
Edit `localization.ui_layout.ui_layout_item_status_paired.edits.ui_layout_item_status_paired_27` reason: Copy NUN5's scale-register centering instruction so item foregrounds fade in place instead of moving with alpha.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_01` reason: Copy the complete official NUN5 Health item record, including its localized rectangle and flags.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_02` reason: Copy the complete official NUN5 Chakra item record, including its localized rectangle and flags.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_03` reason: Copy the complete official NUN5 Recovery item record, including its localized rectangle and flags.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_04` reason: Pass row zero to the shared numeric top-label layout helper.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_05` reason: Route the numeric top label through the shared donor-width helper with the NUN5 X/Y anchors and stack-local rotation output while preserving NA2's object ABI.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_06` reason: Load the helper-produced numeric top-label rotation in the renderer delay slot.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_07` reason: Route both numeric lower-label variants through the shared donor-width helper with the class-specific NUN5 row and anchor contract.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_08` reason: Read the numeric item code from the preserved NA2 object register after preparing the shared-helper arguments.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_09` reason: Load the first helper-produced numeric lower-label rotation in the renderer delay slot.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_10` reason: Load the second helper-produced numeric lower-label rotation in the renderer delay slot.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_11` reason: Port the NUN5 three-digit first-column position into NA2 coordinates after the shared negative-50 X-origin correction.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_12` reason: Port the NUN5 three-digit second-column position into NA2 coordinates after the shared negative-50 X-origin correction.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_13` reason: Port the NUN5 three-digit third-column position into NA2 coordinates after the shared negative-50 X-origin correction.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_14` reason: Port the NUN5 two-digit first-column position into NA2 coordinates after the shared negative-50 X-origin correction.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_15` reason: Port the NUN5 two-digit second-column position into NA2 coordinates after the shared negative-50 X-origin correction.
Edit `localization.ui_layout.ui_layout_item_status_numeric.edits.ui_layout_item_status_numeric_16` reason: Port the NUN5 one-digit position into NA2 coordinates after the shared negative-50 X-origin correction.
Edit `localization.ui_layout.ui_layout_item_status_single.edits.ui_layout_item_status_single_01` reason: Copy complete official NUN5 single-status records 0x96 through 0x9A as one guarded donor range.
Edit `localization.ui_layout.ui_layout_item_status_single.edits.ui_layout_item_status_single_02` reason: Remove NA2's regional positive 33-pixel single-label X shift to match NUN5.
Edit `localization.ui_layout.ui_layout_item_status_single.edits.ui_layout_item_status_single_03` reason: Use NUN5's positive 33-pixel single-label Y shift instead of NA2's positive 42-pixel shift.
Edit `localization.ui_layout.ui_layout_item_status_single.edits.ui_layout_item_status_single_04` reason: Call the bounded single-label rotation helper after the resource lookup and renderer-variant selection.
Edit `localization.ui_layout.ui_layout_item_status_single.edits.ui_layout_item_status_single_05` reason: Clear rotation in the helper-call delay slot after resource lookup; the helper restores a quarter-turn only for donor records that require it.
Edit `localization.ui_layout.ui_layout_item_status_single.edits.ui_layout_item_status_single_06` reason: Install the bounded record-aware rotation helper in the final verified zero span before the shared scale slot; preserve v0 and restore a0 in the return delay slot.
Edit `localization.ui_layout.ui_layout_item_status_fixed.edits.ui_layout_item_status_fixed_01` reason: Center fixed record 0x8E through the established shared donor-width helper and adapt its top-row base to NUN5's positive 20-pixel Y offset.
Edit `localization.ui_layout.ui_layout_item_status_fixed.edits.ui_layout_item_status_fixed_02` reason: Center fixed record 0x8D through the same shared donor-width helper and adapt its lower-row base to NUN5's positive 37-pixel Y offset.
Edit `localization.ui_layout.ui_layout_item_pickup_doll.edits.ui_layout_item_pickup_doll_01` reason: Copy NUN5 record 0x0A's complete substitution-doll rectangle over homologous NA2 record 0x0A, the record selected by the live per-frame pickup updater.
Edit `localization.ui_layout.ui_layout_mash_prompts.edits.ui_layout_mash_prompts_01` reason: Copy the complete official NUN5 English main-prompt rectangle table for localized battle input labels; leave the adjacent controller-glyph table at BTL offset 0x1DB770 untouched.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_01` reason: NUN5 English width row(s) 1/f0, 47/f0, 57/f0, 73/f0 supply atlas width 156; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 156-2=154.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_02` reason: NUN5 English width row(s) 1/f1, 47/f1, 57/f1, 73/f1 supply atlas width 192; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 192-2=190.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_03` reason: NUN5 English width row(s) 2/f0, 48/f0, 93/f0 supply atlas width 164; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 164-2=162.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_04` reason: NUN5 English width row(s) 2/f1, 48/f1, 93/f1 supply atlas width 160; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 160-2=158.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_05` reason: NUN5 English width row(s) 3/f0, 49/f0, 67/f0 supply atlas width 120; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 120-2=118.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_06` reason: NUN5 English width row(s) 3/f1, 49/f1, 67/f1 supply atlas width 88; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 88-2=86.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_07` reason: NUN5 English width row(s) 4/f0, 50/f0 supply atlas width 192; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 192-2=190.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_08` reason: NUN5 English width row(s) 4/f1, 50/f1 supply atlas width 204; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 204-2=202.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_09` reason: NUN5 English width row(s) 5/f0, 68/f0 supply atlas width 236; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 236-2=234.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_10` reason: NUN5 English width row(s) 5/f1, 68/f1 supply atlas width 112; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 112-2=110.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_11` reason: NUN5 English width row(s) 6/f0, 65/f0 supply atlas width 92; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 92-2=90.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_12` reason: NUN5 English width row(s) 6/f1, 65/f1 supply atlas width 148; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 148-2=146.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_13` reason: NUN5 English width row(s) 7/f0, 58/f0 supply atlas width 160; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 160-2=158.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_14` reason: NUN5 English width row(s) 7/f1, 58/f1 supply atlas width 168; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 168-2=166.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_15` reason: NUN5 English width row(s) 70/f0 supply atlas width 176; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 176-2=174.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_16` reason: NUN5 English width row(s) 70/f1 supply atlas width 160; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 160-2=158.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_17` reason: NUN5 English width row(s) 89/f0 supply atlas width 256; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 256-2=254.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_18` reason: NUN5 English width row(s) 10/f0 supply atlas width 120; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 120-2=118.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_19` reason: NUN5 English width row(s) 11/f0 supply atlas width 168; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 168-2=166.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_20` reason: NUN5 English width row(s) 11/f1 supply atlas width 204; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 204-2=202.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_21` reason: NUN5 English width row(s) 12/f0, 80/f0 supply atlas width 148; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 148-2=146.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_22` reason: NUN5 English width row(s) 12/f1, 80/f1 supply atlas width 148; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 148-2=146.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_23` reason: NUN5 English width row(s) 13/f0, 66/f0 supply atlas width 160; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 160-2=158.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_24` reason: NUN5 English width row(s) 14/f0, 51/f0, 81/f0 supply atlas width 120; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 120-2=118.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_25` reason: NUN5 English width row(s) 14/f1, 51/f1, 81/f1 supply atlas width 196; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 196-2=194.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_26` reason: NUN5 English width row(s) 15/f0, 82/f0 supply atlas width 76; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 76-2=74.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_27` reason: NUN5 English width row(s) 15/f1, 82/f1 supply atlas width 228; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 228-2=226.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_28` reason: NUN5 English width row(s) 16/f0, 78/f0 supply atlas width 104; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 104-2=102.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_29` reason: NUN5 English width row(s) 16/f1, 78/f1 supply atlas width 176; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 176-2=174.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_30` reason: NUN5 English width row(s) 17/f0, 79/f0 supply atlas width 132; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 132-2=130.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_31` reason: NUN5 English width row(s) 17/f1, 79/f1 supply atlas width 204; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 204-2=202.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_32` reason: NUN5 English width row(s) 18/f0, 60/f0 supply atlas width 184; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 184-2=182.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_33` reason: NUN5 English width row(s) 19/f0, 61/f0 supply atlas width 156; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 156-2=154.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_34` reason: NUN5 English width row(s) 69/f0 supply atlas width 132; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 132-2=130.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_35` reason: NUN5 English width row(s) 69/f1 supply atlas width 96; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 96-2=94.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_36` reason: NUN5 English width row(s) 83/f0 supply atlas width 152; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 152-2=150.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_37` reason: NUN5 English width row(s) 22/f1 supply atlas width 200; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 200-2=198.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_38` reason: NUN5 English width row(s) 71/f0 supply atlas width 128; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 128-2=126.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_39` reason: NUN5 English width row(s) 71/f1 supply atlas width 160; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 160-2=158.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_40` reason: NUN5 English width row(s) 84/f0 supply atlas width 196; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 196-2=194.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_41` reason: NUN5 English width row(s) 85/f0 supply atlas width 184; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 184-2=182.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_42` reason: NUN5 English width row(s) 90/f0 supply atlas width 160; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 160-2=158.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_43` reason: NUN5 English width row(s) 90/f1 supply atlas width 180; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 180-2=178.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_44` reason: NUN5 English width row(s) 34/f0, 52/f0 supply atlas width 236; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 236-2=234.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_45` reason: NUN5 English width row(s) 34/f1, 52/f1 supply atlas width 212; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 212-2=210.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_46` reason: NUN5 English width row(s) 35/f0, 53/f0 supply atlas width 228; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 228-2=226.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_47` reason: NUN5 English width row(s) 35/f1, 53/f1 supply atlas width 256; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 256-2=254.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_48` reason: NUN5 English width row(s) 36/f0, 54/f0 supply atlas width 188; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 188-2=186.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_49` reason: NUN5 English width row(s) 36/f1, 54/f1 supply atlas width 208; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 208-2=206.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_50` reason: NUN5 English width row(s) 37/f0, 55/f0 supply atlas width 236; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 236-2=234.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_51` reason: NUN5 English width row(s) 37/f1, 55/f1 supply atlas width 196; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 196-2=194.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_52` reason: NUN5 English width row(s) 38/f0, 56/f0 supply atlas width 208; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 208-2=206.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_53` reason: NUN5 English width row(s) 39/f0 supply atlas width 244; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 244-2=242.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_54` reason: NUN5 English width row(s) 39/f1 supply atlas width 124; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 124-2=122.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_55` reason: NUN5 English width row(s) 40/f0 supply atlas width 236; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 236-2=234.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_56` reason: NUN5 English width row(s) 40/f1 supply atlas width 228; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 228-2=226.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_57` reason: NUN5 English width row(s) 41/f0 supply atlas width 156; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 156-2=154.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_58` reason: NUN5 English width row(s) 41/f1 supply atlas width 148; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 148-2=146.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_59` reason: NUN5 English width row(s) 42/f0 supply atlas width 204; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 204-2=202.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_60` reason: NUN5 English width row(s) 42/f1 supply atlas width 172; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 172-2=170.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_61` reason: NUN5 English width row(s) 43/f0 supply atlas width 248; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 248-2=246.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_62` reason: NUN5 English width row(s) 43/f1 supply atlas width 160; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 160-2=158.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_63` reason: NUN5 English width row(s) 86/f0 supply atlas width 156; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 156-2=154.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_64` reason: NUN5 English width row(s) 86/f1 supply atlas width 192; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 192-2=190.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_65` reason: NUN5 English width row(s) 87/f0 supply atlas width 172; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 172-2=170.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_66` reason: NUN5 English width row(s) 87/f1 supply atlas width 108; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 108-2=106.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_67` reason: NUN5 English width row(s) 46/f0 supply atlas width 120; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 120-2=118.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_68` reason: NUN5 English width row(s) 46/f1 supply atlas width 208; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 208-2=206.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_69` reason: NUN5 English width row(s) 59/f1 supply atlas width 180; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 180-2=178.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_70` reason: NUN5 English width row(s) 62/f0, 77/f0 supply atlas width 164; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 164-2=162.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_71` reason: NUN5 English width row(s) 62/f1, 77/f1 supply atlas width 132; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 132-2=130.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_72` reason: NUN5 English width row(s) 63/f0, 75/f0, 76/f0 supply atlas width 236; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 236-2=234.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_73` reason: NUN5 English width row(s) 63/f1, 75/f1, 76/f1 supply atlas width 188; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 188-2=186.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_74` reason: NUN5 English width row(s) 64/f0 supply atlas width 176; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 176-2=174.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_75` reason: NUN5 English width row(s) 72/f0 supply atlas width 164; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 164-2=162.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_76` reason: NUN5 English width row(s) 72/f1 supply atlas width 220; derive the complete NA2 descriptor from NUN5 frame-1 template 0x21B9E0 and its renderer width 220-2=218.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_77` reason: NUN5 English width row(s) 91/f0 supply atlas width 172; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 172-2=170.
Edit `localization.ui_layout.ui_layout_victory_names.edits.ui_layout_victory_names_78` reason: NUN5 English width row(s) 92/f0 supply atlas width 76; derive the complete NA2 descriptor from NUN5 frame-0 template 0x21B9C0 and its renderer width 76-2=74.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_01` reason: Use X=388 for Practice Settings OK because NA2 lacks the NUN5 homolog's runtime -12 offset after its nominal X=400 load.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_02` reason: Use X=462 for Practice Settings Back because NA2 lacks the NUN5 homolog's runtime -8 offset after its nominal X=470 load.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_03` reason: Copy NUN5's exact X=200 instruction for the Practice Settings Select-icon call over NA2 X=230.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_04` reason: Copy NUN5's exact X=200 instruction for the paired Practice Settings Select-label call over NA2 X=230.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_05` reason: Use X=388 for Battle Settings OK because NA2 lacks the NUN5 homolog's runtime -12 offset after its nominal X=400 load.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_06` reason: Use X=462 for Battle Settings Back because NA2 lacks the NUN5 homolog's runtime -8 offset after its nominal X=470 load.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_07` reason: Copy NUN5's exact X=200 instruction for the Battle Settings Select-icon call over NA2 X=230.
Edit `localization.ui_layout.ui_layout_settings_footers.edits.ui_layout_settings_footers_08` reason: Copy NUN5's exact X=200 instruction for the paired Battle Settings Select-label call over NA2 X=230.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_01` reason: Copy the complete six-record NUN5 English Battle Results label table, including the already-equal Money and Total Money records so the screen remains one coherent donor table.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_02` reason: Copy the paired NUN5 Ninja Song title and moving-cloud atlas rectangles.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_03` reason: Copy NUN5's complete Display Details rectangle so the imported label uses its 154x22 English extent.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_04` reason: Copy NUN5's complete five-cloud motion/geometry table; positions, speeds, and heights are equal while all five widths match the localized cloud strip.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_05` reason: Copy NUN5's exact same-register -23.0 X-offset instruction for the pulsing Ninja Song title over NA2's -43.0 offset.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_06` reason: Copy only NUN5's X=342 immediate halfword for Display Details while preserving NA2's v0 destination register.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_07` reason: Encode NUN5's exact Y=345 anchor in NA2 and move its existing object load into the safe JAL delay slot; NUN5 uses v1 plus a language accessor, so its instruction sequence is not ABI-compatible for a direct copy.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_08` reason: Copy NUN5's exact same-register X=287 instruction pair for the Next prompt.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_09` reason: Copy NUN5's exact same-register Y=356 high-word instruction for the Next prompt.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_10` reason: Clear NA2's obsolete 0x8000 low half after importing NUN5's exact integral Y=356 anchor.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_11` reason: Copy the complete five-record NUN5 rank-stamp atlas table so every result value selects one whole 96x44 English cell while retaining the shared index-3 delta baseline.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_12` reason: Use X=375 for the Ninja Song details X/Next prompt, reproducing NUN5's effective 395-20 regional anchor where NA2 lacks the GP-relative offset.
Edit `localization.ui_layout.ui_layout_battle_results.edits.ui_layout_battle_results_13` reason: Use X=462 for the Ninja Song details Triangle/Back prompt, reproducing NUN5's effective 470-8 regional anchor where NA2 lacks the GP-relative offset.
Hook `localization.font_glyphs.font_glyphs_metrics.hooks.font_glyphs_metrics_01` reason: Pass the live renderer context, secondary cell, and native flags to the compiled metric application entry, then rejoin the original function cleanup.
Hook `localization.font_glyphs.font_glyphs_metrics.hooks.font_glyphs_metrics_02` reason: Expand the current secondary byte through the compiled packed-metric lookup, store the native four-byte row, and rejoin the original measurement cleanup.
Hook `localization.font_layout.font_layout_core.hooks.font_layout_core_01` reason: Route ordinary ASCII-space advance through the v2 session guard; a null session reproduces the two displaced NA2 instructions.
Hook `localization.font_layout.font_layout_core.hooks.font_layout_core_02` reason: Route newline advance through the v2 session guard; a null session reproduces the two displaced NA2 instructions.
Hook `localization.font_layout.font_layout_core.hooks.font_layout_core_03` reason: Route normal glyph right-edge geometry through the v2 session guard without changing the unscaled vertical edge.
Hook `localization.font_layout.font_layout_core.hooks.font_layout_core_04` reason: Route inline-markup half-space advance through the v2 session guard while preserving the original accumulator and store when inactive.
Hook `localization.font_layout.font_layout_core.hooks.font_layout_core_05` reason: Route ordinary glyph advance through the v2 session guard; a null session reproduces the displaced add and coordinate load.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_01` reason: Route the selected branch of NA2's state-aware primitive through the shared origin correction after it has saved X and Y; ordinary text remains native.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_02` reason: Route NA2's caller-colored selected primitive through the same shared origin correction after it has saved X and Y.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_03` reason: Replace the third fixed two-choice primitive with a shared dispatcher that delegates its selected row to the corrected central selected primitive and its other row to the native ordinary primitive.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_04` reason: Move the first selected record shadow below and right before the shared list component draws it; the native following subtraction restores the colored row to its ordinary origin.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_05` reason: Apply the same record-origin formula to the second branch of the shared list component.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_06` reason: Apply the shared selected-record formula to the first field in the reusable three-record save/load row.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_07` reason: Apply the shared selected-record formula to the second field in the reusable three-record save/load row.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_08` reason: Apply the shared selected-record formula to the third field in the reusable three-record save/load row.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_09` reason: Apply the shared selected-record formula to the first branch of the reusable save/load Yes/No prompt.
Hook `localization.font_layout.font_layout_global_selected_style.hooks.font_layout_global_selected_style_10` reason: Apply the shared selected-record formula to the second branch of the reusable save/load Yes/No prompt.
Hook `localization.font_layout.font_layout_controls.hooks.font_layout_controls_01` reason: Replace the shared first-eight-label Controls draw call with the v2 128-unit boxed adapter.
Hook `localization.font_layout.font_layout_titles.hooks.font_layout_titles_01` reason: Route only the Command Chart title draw through the shared v2 title adapter; the two following auxiliary-string draws remain native.
Hook `localization.font_layout.font_layout_titles.hooks.font_layout_titles_02` reason: Route only the Practice command-title draw through the shared v2 title adapter; the later explanation loop remains native.
Hook `localization.font_layout.font_layout_command_relationships.hooks.font_layout_command_relationships_01` reason: Route the first exact Command Chart auxiliary draw through the live-register shim; generated C resolves record bytes +4/+5, combines both strings, wraps them in the final 226x32 family box, and retains the native style and row object.
Hook `localization.font_layout.font_layout_command_relationships.hooks.font_layout_command_relationships_02` reason: Replace only the native fixed +20 icon-row offset load with a row-aware C offset: +16 after a relationship row and +38 when the row has no relationship, matching the NUN5 homolog while retaining both native icon branches.
Hook `localization.font_layout.font_layout_pause_controls.hooks.font_layout_pause_controls_01` reason: Route only the Pause Controls list-row draw through the v2 216-unit shrink-only adapter with the retained four-unit NUN5 Y correction.
Hook `localization.font_layout.font_layout_pause_controls.hooks.font_layout_pause_controls_02` reason: Route the selected Pause Controls row through the same 216-unit shrink-only box, retaining its native red style while compensating the selected helper by two X units and the shared NUN5 Y correction.
Hook `localization.font_layout.font_layout_quit_confirmation.hooks.font_layout_quit_confirmation_01` reason: Publish the transient ss4 scope only around the native Battle quit Yes/No list draw.
Hook `localization.font_layout.font_layout_quit_confirmation.hooks.font_layout_quit_confirmation_02` reason: Copy and wrap the exact ss4 confirmation body at draw time without changing canonical mappings or the source buffer.
Hook `localization.font_layout.font_layout_quit_confirmation.hooks.font_layout_quit_confirmation_03` reason: Map selected Yes or No while the exact ss4 scope is active, or the exact Special Controls ON pointer outside it; every other selected row remains native.
Hook `localization.font_layout.font_layout_quit_confirmation.hooks.font_layout_quit_confirmation_04` reason: Temporarily map unselected Yes or No while the exact ss4 scope is active, or the exact Special Controls OFF pointer outside it, then restore native coordinates.
Hook `localization.font_layout.font_layout_mode_select_confirmation.hooks.font_layout_mode_select_confirmation_01` reason: Publish the existing C-owned Yes/No scope only around the live Mode Select Return to Title Screen confirmation list.
Hook `localization.font_layout.font_layout_mode_select_confirmation.hooks.font_layout_mode_select_confirmation_02` reason: Route the dedicated Return to Title Screen body call through the shared native body adapter; exact text selects the Mode Select 420x40 box at local (24,12) without publishing Collection choice scope.
Hook `localization.font_layout.font_layout_character_select_modal.hooks.font_layout_character_select_modal_01` reason: Route the selected five-row modal entry through the shared 240-unit metric session; only its structural fifth-row footer receives the selected helper's one-unit Y correction.
Hook `localization.font_layout.font_layout_character_select_modal.hooks.font_layout_character_select_modal_02` reason: Route only the Character Select return-confirmation body through the C-owned NUN5 368x24 secondary-renderer box; the Yes/No selector and every other main-ELF body caller remain native.
Hook `localization.font_layout.font_layout_character_select_modal.hooks.font_layout_character_select_modal_03` reason: Publish a Character-only confirmation scope around its Yes/No list so both draw states receive the container's shared one-pixel Y correction without changing Mode Select or Collection.
Hook `localization.font_layout.font_layout_character_select_modal.hooks.font_layout_character_select_modal_04` reason: Route ordinary five-row modal entries through the same 240-unit metric session while preserving the row coordinates produced by the declarative Character-modal table patch.
Hook `localization.font_layout.font_layout_collection_confirmation.hooks.font_layout_collection_confirmation_01` reason: Route the first Collection exit-confirmation body call through its C-owned native-scale 400x60 body box at (24.8,12).
Hook `localization.font_layout.font_layout_collection_confirmation.hooks.font_layout_collection_confirmation_02` reason: Publish the existing C-owned NUN5 Yes/No coordinate scope only around the Collection exit-confirmation list; every other ETC list caller remains native.
Hook `localization.font_layout.font_layout_collection_confirmation.hooks.font_layout_collection_confirmation_03` reason: Route the Collection render-state body call that produces the visible exit-confirmation prompt through the same C-owned body adapter.
Hook `localization.font_layout.font_layout_collection_lists.hooks.font_layout_collection_lists_01` reason: Route the shared Collection row draw through one native-X classifier: Figure rows use the retained 152x32 box, every other target list uses the retained 192x32 box, companion lists stay native, and fitting one-line rows retain the native glyph draw at family X +1.2 and Y -4.0.
Hook `localization.font_layout.font_layout_collection_lists.hooks.font_layout_collection_lists_02` reason: Move every Figure character header through the shared Figure/Music origin formula without changing its text, style, scale, or renderer.
Hook `localization.font_layout.font_layout_collection_lists.hooks.font_layout_collection_lists_03` reason: Move every ordinary or legacy Ultimate Jutsu plaque through the one shared parent-record origin formula; the unrelated child/VCR text call at 0xA31C remains native.
Hook `localization.font_layout.font_layout_collection_lists.hooks.font_layout_collection_lists_04` reason: Move every character-specific Music header through the shared Figure/Music origin formula without changing its text, style, scale, or renderer.
Hook `localization.font_layout.font_layout_jutsu_selector.hooks.font_layout_jutsu_selector_01` reason: Route only the final visible Jutsu-row text draw through the selective C entry: fitting rows use the scale-1.0 family session and one-line origin, while measured overflow uses the 186x32 compositor; row construction, sprites, colors, and every unrelated BTL draw remain native.
Hook `localization.font_layout.font_layout_special_controls_body.hooks.font_layout_special_controls_body_01` reason: Copy and wrap only the exact ss1 Special Controls explanatory body at draw time without changing the canonical source string or shared UI wrapper.
Hook `localization.font_layout.font_layout_practice_explanations.hooks.font_layout_practice_explanations_01` reason: Route every Practice explanation row through one bounded NUN5-equivalent mixed text/icon wrapping call and skip the superseded per-token loop.
Hook `localization.font_numeric_formatting.font_numeric_ninja_song.hooks.font_numeric_ninja_song_01` reason: Render the left Ninja Song arithmetic factor as right-aligned ASCII width 3.
Hook `localization.font_numeric_formatting.font_numeric_ninja_song.hooks.font_numeric_ninja_song_02` reason: Render the right Ninja Song arithmetic factor as right-aligned ASCII width 3.
Hook `localization.font_numeric_formatting.font_numeric_ninja_song.hooks.font_numeric_ninja_song_03` reason: Render the Ninja Song arithmetic total as right-aligned ASCII width 5.
Hook `localization.font_numeric_formatting.font_numeric_ninja_song.hooks.font_numeric_ninja_song_04` reason: Render the Ninja Song label placeholder as unpadded ASCII decimal.
Hook `localization.font_numeric_formatting.font_numeric_ninja_song.hooks.font_numeric_ninja_song_05` reason: Render the Ninja Song detail score as right-aligned ASCII width 4.
Hook `localization.font_numeric_formatting.font_numeric_save_load.hooks.font_numeric_save_load_01` reason: Call the EU-day C formatter and resume the native function before preserving the returned year in s6.
Hook `localization.font_numeric_formatting.font_numeric_save_load.hooks.font_numeric_save_load_02` reason: Call the shared C two-digit month formatter and resume the native function.
Hook `localization.font_numeric_formatting.font_numeric_save_load.hooks.font_numeric_save_load_03` reason: Call the C four-digit year formatter and resume the native function.
Hook `localization.font_numeric_formatting.font_numeric_save_load.hooks.font_numeric_save_load_04` reason: Call the accepted signed 99-hour C formatter and resume the native function.
Hook `localization.font_numeric_formatting.font_numeric_save_load.hooks.font_numeric_save_load_05` reason: Call the shared C two-digit minute formatter and resume the native function.
Hook `localization.font_numeric_formatting.font_numeric_save_load.hooks.font_numeric_save_load_06` reason: Call the shared C two-digit second formatter and resume the native function.
Hook `localization.font_numeric_formatting.font_numeric_battle_settings.hooks.font_numeric_battle_settings_01` reason: Call the ordinary Battle Settings Time C formatter and resume the native function while preserving the separate 100/infinity branch.
Hook `localization.font_layout.font_layout_settings_rows.hooks.font_layout_settings_rows_01` reason: Route the exact Battle Settings label draw through the NUN5 92x158 box.
Hook `localization.font_layout.font_layout_settings_rows.hooks.font_layout_settings_rows_02` reason: Route the ordinary Battle Settings value draw through the centered token-or-phrase template with the Battle-only raster phase.
Hook `localization.font_layout.font_layout_settings_rows.hooks.font_layout_settings_rows_03` reason: Route the alternate Battle Settings value branch through the same Battle-only structural value template.
Hook `localization.font_layout.font_layout_settings_rows.hooks.font_layout_settings_rows_04` reason: Route the Practice Settings section heading through the NUN5 84x158 box.
Hook `localization.font_layout.font_layout_settings_rows.hooks.font_layout_settings_rows_05` reason: Route each Practice Settings label through the NUN5 92x150 box.
Hook `localization.font_layout.font_layout_settings_rows.hooks.font_layout_settings_rows_06` reason: Route each Practice Settings value through the same centered token-or-phrase value template.
Hook `localization.font_layout.font_layout_ninja_song_details.hooks.font_layout_ninja_song_details_01` reason: Replace the shared data-driven Ninja Song arithmetic function once so its native row data and branches render all fifteen formula rows through the NUN5 layout template.
Hook `localization.font_layout.font_layout_ninja_song_details.hooks.font_layout_ninja_song_details_02` reason: Replace the visible numbered-objective row block once, independently positioning its existing index and marker and wrapping its existing prose through the NUN5 288x32 two-line box without modifying any string bytes.
Hook `localization.font_layout.font_layout_linked_mode_modal.hooks.font_layout_linked_mode_modal_01` reason: Route every selected Linked Mode choice through one centered 1.05 horizontal-scale session, supply the native red selected color, and preserve its text and structural row formula.
Hook `localization.font_layout.font_layout_linked_mode_modal.hooks.font_layout_linked_mode_modal_02` reason: Route every ordinary Linked Mode choice through the same centered 1.05 horizontal-scale session; Manual and Auto share the renderer unchanged.
Entry `localization.font.v2.controls_adapter` from `font_v2_core`: ABI `text_style_center_x_draw_y`; purpose: Controls and Special Controls one-line labels
Entry `localization.font.v2.command_relationship_adapter` from `font_v2_core`: ABI `command_relationship_native`; purpose: Command Chart relationship row
Entry `localization.font.v2.command_title_entry` from `font_v2_core`: ABI `arg0_text_arg2_native_x_native_y`; purpose: Command Chart title
Entry `localization.font.v2.practice_title_entry` from `font_v2_core`: ABI `arg0_text_arg2_native_x_native_y`; purpose: Practice title
Entry `localization.font.v2.pause_list_adapter` from `font_v2_core`: ABI `arg0_text_arg2_native_x_native_y`; purpose: Pause-list row
Entry `localization.font.v2.character_selected_adapter` from `font_v2_core`: ABI `object_draw_x_draw_y_text`; purpose: Character Select selected modal row
Entry `localization.font.v2.quit_unselected_adapter` from `font_v2_core`: ABI `arg0_record_arg2_arg3`; purpose: Quit choice not selected
Entry `localization.font.v2.quit_body_adapter` from `font_v2_core`: ABI `arg0_text_arg2`; purpose: Quit confirmation body
Entry `localization.font.v2.character_confirmation_body_adapter` from `font_v2_core`: ABI `arg0_text_arg2`; purpose: Character Select return-confirmation body
Entry `localization.font.v2.special_controls_body_adapter` from `font_v2_core`: ABI `arg0_text_arg2`; purpose: Special Controls explanatory body
Entry `localization.font.v2.collection_list_entry` from `font_v2_core`: ABI `text_highlight_native_x_native_y`; purpose: Shared Collection list row classifier
Entry `localization.font.v2.collection_figure_music_header_adapter` from `font_v2_core`: ABI `native_x_native_y_text_style`; purpose: Shared Collection Figure and Music header origin formula
Entry `localization.font.v2.collection_jutsu_header_adapter` from `font_v2_core`: ABI `native_x_native_y_text_style`; purpose: Shared Collection Ultimate Jutsu header origin formula
Entry `localization.font.v2.battle_settings_label_adapter` from `font_v2_core`: ABI `text_style_native_x_native_y`; purpose: Battle Settings label row
Entry `localization.font.v2.practice_settings_label_adapter` from `font_v2_core`: ABI `text_style_native_x_native_y`; purpose: Practice Settings label row
Entry `localization.font.v2.battle_settings_value_adapter` from `font_v2_core`: ABI `text_color_native_x_native_y`; purpose: Battle Settings centered value with page-local raster phase
Entry `localization.font.v2.settings_value_adapter` from `font_v2_core`: ABI `text_color_native_x_native_y`; purpose: Practice Settings centered value
Entry `localization.font.v2.practice_settings_heading_adapter` from `font_v2_core`: ABI `text_color_native_x_native_y`; purpose: Practice Settings section heading
Entry `localization.font.v2.ninja_arithmetic_template` from `font_v2_core`: ABI `native_x_native_y_row_set_row_index`; purpose: Shared data-driven Ninja Song formula renderer for all fifteen rows
Entry `localization.font.v2.ninja_objective_row_adapter` from `font_v2_core`: ABI `page_row_record_display_index_row_y_bits`; purpose: Shared Ninja Song visible objective-row renderer preserving the native index, marker, and prose strings
Entry `localization.font.v2.linked_choice_unselected_adapter` from `font_v2_core`: ABI `arg0_text_arg2_native_x_native_y`; purpose: Linked Mode ordinary centered choice
Edit `qol.startup.skip_cc2_intro.edits.skip_cc2_intro` reason: Skip CC2 intro.
Edit `qol.startup.skip_opening.edits.skip_opening` reason: Skip opening.
Edit `qol.startup.loading_screen_then_main_menu.edits.enter_the_title_input_state_immediately_after_required_startup_loading_and_splash_cleanup_bypassing_the_post_splash_sequence` reason: Enter the title-input state immediately after required startup loading and splash cleanup, bypassing the post-splash sequence.
Edit `qol.startup.loading_screen_then_main_menu.edits.return_the_native_start_accepted_result_without_constructing_or_displaying_the_title_screen_selecting_main_menu_state_4_substate_1_through_the_existing_caller` reason: Return the native Start-accepted result without constructing or displaying the title screen, selecting main-menu state 4 substate 1 through the existing caller.
Edit `qol.practice.voice_off_by_default.edits.voice_off_by_default` reason: Voice off by default.
Edit `qol.practice.support_off_by_default.edits.force_support_off_instead_of_leaving_the_previous_settings_block_value_unchanged` reason: Force support off instead of leaving the previous settings-block value unchanged.
Edit `qol.practice.command_display_off_by_default.edits.force_command_display_off_while_preserving_the_following_settings_field_reload` reason: Force command display off while preserving the following settings-field reload.
Edit `qol.practice.simple_display_off.edits.simple_display_off_by_default` reason: Simple display off by default.
Edit `qol.mode_select.remove_adventure_mode.edits.mark_only_the_adventure_mode_select_entry_unavailable_matching_nun6_s_filtered_carousel_behavior` reason: Mark only the Adventure Mode Select entry unavailable, matching NUN6's filtered-carousel behavior.
Edit `qol.mode_select.remove_shop.edits.mark_only_the_shop_mode_select_entry_unavailable_using_the_existing_filtered_carousel_behavior` reason: Mark only the Shop Mode Select entry unavailable using the existing filtered-carousel behavior.
Edit `qol.save_load.display_only_first_save.edits.limit_the_shared_save_load_slot_row_renderer_to_its_first_record` reason: Limit the shared Save/Load slot-row renderer to its first record.
Edit `qol.save_load.display_only_first_save.edits.ignore_downward_slot_navigation_before_it_changes_selection_or_plays_the_navigation_sound` reason: Ignore downward slot navigation before it changes selection or plays the navigation sound.
Edit `qol.save_load.display_only_first_save.edits.ignore_upward_slot_navigation_before_it_changes_selection_or_plays_the_navigation_sound` reason: Ignore upward slot navigation before it changes selection or plays the navigation sound.
Edit `qol.save_load.display_only_first_save.edits.center_the_date_and_play_time_block_at_local_x_45_inside_the_compact_panel` reason: Center the date and play-time block at local X 45 inside the compact panel.
Edit `qol.save_load.display_only_first_save.edits.center_the_single_save_record_at_local_y_20_inside_the_compact_panel` reason: Center the single save record at local Y 20 inside the compact panel.
Edit `qol.save_load.display_only_first_save.edits.move_the_redundant_slot_number_record_outside_the_viewport` reason: Move the redundant slot-number record outside the viewport.
Edit `qol.save_load.display_only_first_save.edits.suppress_row_separators_when_only_one_record_is_rendered` reason: Suppress row separators when only one record is rendered.
Edit `qol.save_load.display_only_first_save.edits.move_the_upper_save_load_panel_to_centered_x_146` reason: Move the upper Save/Load panel to centered X 146.
Edit `qol.save_load.display_only_first_save.edits.move_the_upper_save_load_panel_to_detached_y_90_above_the_lower_panel` reason: Move the upper Save/Load panel to detached Y 90 above the lower panel.
Edit `qol.save_load.display_only_first_save.edits.shrink_the_upper_save_load_panel_width_from_400_to_224` reason: Shrink the upper Save/Load panel width from 400 to 224.
Edit `qol.save_load.display_only_first_save.edits.shrink_the_upper_save_load_panel_height_from_224_to_96` reason: Shrink the upper Save/Load panel height from 224 to 96.
Edit `qol.save_load.display_only_first_save.edits.suppress_the_obsolete_independent_save_slot_cursor_model_draw` reason: Suppress the obsolete independent save-slot cursor model draw.
Edit `qol.save_load.display_only_first_save.edits.enter_the_sole_slot_save_path_before_constructing_the_redundant_slot_list_screen` reason: Enter the sole-slot save path before constructing the redundant slot-list screen.
Edit `qol.save_load.display_only_first_save.edits.select_slot_zero_and_enter_its_native_save_confirmation_without_rendering_the_slot_list` reason: Select slot zero and enter its native save confirmation without rendering the slot list.
Edit `qol.save_load.display_only_first_save.edits.route_memory_card_status_dispatch_through_the_unformatted_screen_bypass` reason: Route memory-card status dispatch through the unformatted-screen bypass.
Edit `qol.save_load.display_only_first_save.edits.advance_status_0x0a_without_constructing_its_informational_screen_then_retain_native_dispatch_for_every_other_status` reason: Advance status 0x0A without constructing its informational screen, then retain native dispatch for every other status.
Edit `qol.save_load.display_only_first_save.edits.exit_the_save_controller_when_the_final_confirmation_returns_no_instead_of_reopening_the_removed_slot_list` reason: Exit the save controller when the final confirmation returns No instead of reopening the removed slot list.
Edit `qol.save_load.display_only_first_save.edits.prepare_the_status_0x0a_modal_helper_argument_before_its_save_flow_bypass` reason: Prepare the status-0x0A modal-helper argument before its save-flow bypass.
Edit `qol.save_load.display_only_first_save.edits.skip_the_unformatted_card_informational_modal_helper_and_supply_its_completed_result_in_the_save_flow` reason: Skip the unformatted-card informational modal helper and supply its completed result in the save flow.
Edit `qol.save_load.display_only_first_save.edits.retain_the_helper_s_zero_second_argument_when_the_unformatted_save_flow_bypass_is_not_taken` reason: Retain the helper's zero second argument when the unformatted save-flow bypass is not taken.
Edit `qol.save_load.display_only_first_save.edits.return_to_the_main_menu_when_the_unformatted_format_confirmation_returns_no_instead_of_entering_the_save_restart_state` reason: Return to the Main Menu when the unformatted format confirmation returns No instead of entering the save restart state.
Edit `qol.save_load.display_only_first_save.edits.exit_the_save_controller_when_the_no_save_data_confirmation_returns_no_instead_of_resetting_the_save_flow_to_its_initial_prompt` reason: Exit the save controller when the no-save-data confirmation returns No instead of resetting the save flow to its initial prompt.
Hook `qol.startup_loading.startup_loading_screen.hooks.startup_loading_screen_01` reason: Initialize and hold the splash controller's first boot-safe draw slot while preserving the startup loop's real loader checks.
Hook `qol.startup_loading.startup_loading_screen.hooks.startup_loading_screen_02` reason: Replace the visible splash sprite draw with independent boot-safe primitives for a percentage and progress bar paced across the measured 25-second load.
Edit `battle_logic.disable_shadowblur_extra_hit.edits.change_the_shadowblur_extra_hit_condition_branch` reason: Change the Shadowblur extra-hit condition branch.
Edit `battle_logic.disable_shadowblur_extra_hit.edits.skip_the_shadowblur_extra_hit_path` reason: Skip the Shadowblur extra-hit path.
Edit `battle_logic.disable_shadowblur_extra_hit.edits.clear_the_shadowblur_branch_delay_slot` reason: Clear the Shadowblur branch delay slot.
Edit `battle_logic.disable_extra_hit_with_aura_punishment_for_initiator.edits.disable_the_extra_hit_while_retaining_aura_punishment_for_the_initiator` reason: Disable the extra hit while retaining aura punishment for the initiator.
Edit `battle_logic.sub_cost_3_15.edits.set_substitution_cost_to_3_15` reason: Set substitution cost to 3/15.
Edit `rendering.display.native_16_9_horizontal_scale.edits.force_0_75f_at_the_renderer_s_horizontal_scale_store_while_preserving_the_caller_provided_vertical_scale` reason: Force 0.75f at the renderer's horizontal-scale store while preserving the caller-provided vertical scale.
