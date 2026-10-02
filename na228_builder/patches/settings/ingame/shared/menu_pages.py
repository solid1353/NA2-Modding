"""Infer menu structure from the catalog and row order from configuration, and encode
the settings-menu schemas."""
from __future__ import annotations

import struct
from dataclasses import dataclass, replace
from functools import partial

from na228_builder.infrastructure.modules.payload_builder.operations import PayloadFragment, PayloadRelocation
from na228_builder.infrastructure.orchestration.catalog_format import ContainerNode, SettingNode, ObjectType, LiteralType, UnionType
from .menu_options import PAGE_TITLES, items_mode_option, menu_option_bindings
from ..battle_mechanics.battle_settings_runtime import (
    BATTLE_MECHANICS_PATH,
    CHAKRA_REGEN_LABELS,
    CHAKRA_STATIC_LABELS,
    EXTRA_HIT_LABELS,
    SUBSTITUTION_INPUT_LABELS,
    SUPPORT_LABELS,
    ULTIMATE_JUTSU_NATIVE_MODE_COUNT,
    XDASH_CHAKRA_COST_LABELS,
    chakra_default,
    extra_hit_default,
    shadowblur_default,
    substitution_default,
    substitution_input_default,
    support_default,
    ultimate_jutsu_default,
    xdash_chakra_cost_option_default,
)
from na228_builder.patches.localization.mod_strings import Message, ModStrings, message


SUBMENU_FLAG = 0x4000
SUBMENU_SUFFIX = "_submenu"
ROW_LOCAL_CUSTOM = 0xFFFFFFFF
NATIVE_HELP_SET = 0x0037F760
SCHEMA_HEADER_SIZE = 84
PAGE_SIZE = 8 * 4
# Runtime providers and texts at schema header offsets 16 through 76.
HEADER_SYMBOLS = (
    "substitution_gauge_mode_get",
    "substitution_gauge_mode_set",
    "ultimate_jutsu_mode_get",
    "ultimate_jutsu_mode_set",
    "mod_text_settings__no_contest",
    "mod_text_settings__no_hud",
    "shadowblur_get",
    "shadowblur_set",
    "extra_hit_get",
    "extra_hit_set",
    "substitution_input_get",
    "substitution_input_set",
    "xdash_chakra_cost_option_get",
    "xdash_chakra_cost_option_set",
    "support_get",
    "support_set",
)
# Value tables appended after the rows: name, entries pointing at mod text symbols
# (None is supplied by a value-linked child page), then entries pointing at texts
# pooled after the tables.
VALUE_TABLES = (
    ("chakra", CHAKRA_STATIC_LABELS, CHAKRA_REGEN_LABELS),
    ("substitution", (None, None, "mod_text_common__free"), ()),
    ("toggle", ("mod_text_common__off", "mod_text_common__on"), ()),
    ("substitution_input", (), SUBSTITUTION_INPUT_LABELS),
    ("xdash_chakra_cost", (), XDASH_CHAKRA_COST_LABELS),
    ("support", (), SUPPORT_LABELS),
    ("extra_hit", (), EXTRA_HIT_LABELS),
)
VALUE_TABLE_SIZES = {name: len(symbols) + len(texts) for name, symbols, texts in VALUE_TABLES}
# Battle Mechanics rows labeled by mod text, in custom row ID order: field, value
# table, and default.
CUSTOM_ROWS = (
    ("substitution_resource", "substitution", substitution_default),
    ("shadowblur", "toggle", shadowblur_default),
    ("extra_hit", "extra_hit", extra_hit_default),
    ("substitution_input", "substitution_input", substitution_input_default),
    ("xdash_chakra_cost", "xdash_chakra_cost", xdash_chakra_cost_option_default),
    ("support", "support", support_default),
)


@dataclass(frozen=True)
class RowLayout:
    """What differs between the menus' schema rows."""
    row_type: type
    field_count: int
    # Index of the label reference field; the help and value-table references follow it.
    references: int
    first_custom_row_id: int
    items_row_id: int
    chakra_row_id: int
    ultimate_jutsu_row_id: int
    values_slot_flag: int
    # Row flag for each custom Battle Mechanics field.
    custom_flags: dict[str, int]


@dataclass(frozen=True)
class MenuPage:
    rows: tuple
    parent_page: int
    parent_row: int
    heading_symbol: str | None
    heading_text: Message | str | None
    reset_symbol: str
    reset_text: Message | str


def font_layout_enabled(selection) -> bool:
    return any(node.patch == "localization.font.layout" and node.enabled
               for node in selection.patch_nodes)


def point_font_routine(payload, relocations, offset, font_layout, localized, native):
    """Point at the localized font routine when its layout is built, else the native one."""
    if font_layout:
        relocations.append(PayloadRelocation(offset=offset, kind="abs32", symbol=localized))
    else:
        struct.pack_into("<I", payload, offset, native)


def menu_title(name):
    return message(f"page.{name}.title")


def _new_row(layout, section, **fields):
    if "section" in layout.row_type.__dataclass_fields__:
        fields["section"] = section
    return layout.row_type(local_offset=ROW_LOCAL_CUSTOM, **fields)


def native_rows(rows, configured_defaults):
    """Look up native rows with their configured defaults."""
    def native_row(row_id):
        return replace(rows[row_id], default_value=configured_defaults.get(
            row_id, rows[row_id].default_value))
    return native_row


def mechanic_row_bindings(selection, layout, native_row):
    """Bind the Battle Mechanics rows that every settings menu shares."""
    def items():
        option = items_mode_option(selection)
        return _new_row(layout, 0, row_id=layout.items_row_id, option_count=option.count,
                        default_value=option.default, flags=0, runtime_option=option)

    def chakra():
        row = native_row(layout.chakra_row_id)
        return replace(row, local_offset=ROW_LOCAL_CUSTOM,
                       option_count=VALUE_TABLE_SIZES["chakra"],
                       default_value=chakra_default(selection),
                       flags=(row.flags & ~layout.values_slot_flag) | layout.custom_flags["chakra"])

    def ultimate_jutsu():
        row = native_row(layout.ultimate_jutsu_row_id)
        return replace(row, option_count=ULTIMATE_JUTSU_NATIVE_MODE_COUNT + 2,
                       default_value=ultimate_jutsu_default(selection),
                       flags=row.flags | layout.custom_flags["ultimate_jutsu"])

    def custom(row_id, field, table, default):
        return _new_row(layout, 0, row_id=row_id, option_count=VALUE_TABLE_SIZES[table],
                        default_value=default(selection), flags=layout.custom_flags[field])

    bindings = {
        BATTLE_MECHANICS_PATH + ("items",): items,
        BATTLE_MECHANICS_PATH + ("chakra",): chakra,
        BATTLE_MECHANICS_PATH + ("ultimate_jutsu",): ultimate_jutsu,
    }
    for index, (field, table, default) in enumerate(CUSTOM_ROWS):
        bindings[BATTLE_MECHANICS_PATH + (field,)] = partial(
            custom, layout.first_custom_row_id + index, field, table, default)
    return bindings


def build_menu_pages(selection, root_path, row_bindings, layout, prefix,
                     external_launchers=None):
    """Discover topology independently of native row and gameplay bindings."""
    settings = selection.catalog["defaults"]
    settings_definitions = {field.name: field.node for field in settings.fields}
    definition = settings
    for name in root_path[2:]:
        definition = next(field.node for field in definition.fields
                          if field.name == name)
    selected = selection.nodes_by_path
    options = menu_option_bindings(selection)
    pages = []
    # Generated rows follow the native and custom IDs that the menu stages by ID.
    next_id = layout.first_custom_row_id + len(CUSTOM_ROWS)
    external_launchers = external_launchers or {}

    def allocate_row(**kwargs):
        nonlocal next_id
        row = _new_row(layout, 1, row_id=next_id, **kwargs)
        next_id += 1
        return row

    def leaf_row(path):
        if path in row_bindings:
            return row_bindings[path]()
        if path not in options:
            raise ValueError(f"No menu value handler for {'.'.join(path)}")
        option = options[path]
        return allocate_row(option_count=option.count, default_value=option.default,
                            flags=0, runtime_option=option)

    def fields_of(definition):
        if isinstance(definition, ContainerNode):
            return tuple((field.name, field.node) for field in definition.fields)
        if isinstance(definition, SettingNode):
            definition = definition.value_type
        if isinstance(definition, ObjectType):
            return tuple((field.name, field.value_type) for field in definition.fields)
        return None

    def ordered_fields(definition, path):
        fields = dict(fields_of(definition))
        target = selected.get(path)
        if target is not None and isinstance(target.configured_value, dict):
            configured = target.configured_value
        else:
            configured = {}
            for length in range(len(path) - 1, 1, -1):
                ancestor = selected.get(path[:length])
                if ancestor is None:
                    continue
                configured = ancestor.configured_value
                for key in path[length:]:
                    if not isinstance(configured, dict):
                        configured = {}
                        break
                    configured = configured.get(key, {})
                break
        names = tuple(configured) if isinstance(configured, dict) else ()
        # Omitted optional values still expose their existing default rows.
        names += tuple(name for name in fields if name not in configured)
        return tuple((name, fields[name]) for name in names)

    def launcher_target(name, definition):
        """A plain `<target>_submenu` switch opens a shared group or native screen."""
        if not (isinstance(definition, SettingNode) and definition.value_type is None
                and name.endswith(SUBMENU_SUFFIX)):
            return None
        target = name[:-len(SUBMENU_SUFFIX)]
        if target not in external_launchers and target not in settings_definitions:
            raise ValueError(f"Unknown submenu target: {name}")
        return target

    def literal_choices(value_type):
        if isinstance(value_type, LiteralType):
            return (value_type.value,)
        if isinstance(value_type, UnionType):
            return tuple(value for branch in value_type.branches for value in literal_choices(branch))
        raise ValueError("A value-linked menu requires literal selector choices")

    def add_page(definition, path, parent_page=0, parent_row=0, ancestors=()):
        if path in ancestors:
            raise ValueError(f"Cyclic menu reference: {'.'.join(path)}")
        page_index = len(pages)
        heading = PAGE_TITLES.get(path, menu_title(path[-1]))
        pages.append(MenuPage(rows=(),
            parent_page=parent_page, parent_row=parent_row,
            heading_symbol=f"{prefix}_page_{page_index}_heading" if page_index else None,
            heading_text=heading if page_index else None,
            reset_symbol=f"{prefix}_page_{page_index}_reset",
            reset_text=message("settings.reset", menu=heading)))
        rows = []
        for name, child in ordered_fields(definition, path):
            child_path = path + (name,)
            target = selected.get(child_path)
            if target is not None and not target.enabled:
                continue
            target_name = launcher_target(name, child)
            if target_name is not None:
                # Launchers belong to their own menu's root page; a shared page
                # opened from another menu does not repeat them.
                if page_index != 0:
                    continue
                if target_name in external_launchers:
                    rows.append(allocate_row(
                        option_count=1, default_value=0,
                        flags=SUBMENU_FLAG | external_launchers[target_name],
                        label=menu_title(target_name),
                        help=message(f"page.{target_name}.help"),
                    ))
                    continue
                shared_path = ("features", "defaults", target_name)
                subpage = add_page(settings_definitions[target_name], shared_path, page_index,
                                   len(rows), ancestors + (path,))
                rows.append(allocate_row(option_count=1, default_value=0, flags=SUBMENU_FLAG,
                    label=menu_title(target_name), help=message(f"page.{target_name}.help"),
                    value_pages=((0, subpage, None),)))
                continue
            fields = fields_of(child)
            if fields is None:
                rows.append(leaf_row(child_path))
                continue
            object_fields = dict(fields)
            if "value" in object_fields:
                row = leaf_row(child_path)
                value_type = object_fields["value"]
                if isinstance(value_type, SettingNode):
                    value_type = value_type.value_type
                choices = literal_choices(value_type)
                links = []
                for value_name, value_child in ordered_fields(child, child_path):
                    if value_name == "value":
                        continue
                    if fields_of(value_child) is None or value_name not in choices:
                        raise ValueError(f"Invalid value submenu: {'.'.join(child_path + (value_name,))}")
                    subpage = add_page(value_child, child_path + (value_name,), page_index,
                                       len(rows), ancestors + (path,))
                    links.append((choices.index(value_name), subpage, menu_title(value_name)))
                rows.append(replace(row, value_pages=tuple(links)))
            else:
                subpage = add_page(child, child_path, page_index, len(rows), ancestors + (path,))
                label = menu_title(name)
                rows.append(allocate_row(option_count=1, default_value=0, flags=SUBMENU_FLAG,
                    label=label, help=message(f"page.{name}.help"),
                    value_pages=((0, subpage, None),)))
        if page_index == 0 and "section" in layout.row_type.__dataclass_fields__:
            rows = [replace(row, section=0) for row in rows]
        pages[page_index] = replace(pages[page_index], rows=tuple(rows))
        return page_index

    add_page(definition, root_path)
    return tuple(pages)


def settings_schema_fragment(selection, pages, layout, *, owner, symbol) -> PayloadFragment:
    strings = ModStrings(selection)
    rows = tuple(row for page in pages for row in page.rows)
    row_size = layout.field_count * 4
    rows_offset = SCHEMA_HEADER_SIZE + len(pages) * PAGE_SIZE
    references = range(layout.references, layout.references + 3)
    label_field, help_field, value_field = references
    custom_tables = {layout.first_custom_row_id + index: (field, table)
                     for index, (field, table, _default) in enumerate(CUSTOM_ROWS)}

    def relocation(offset, target, addend=0):
        return PayloadRelocation(offset=offset, kind="abs32", symbol=target, addend=addend)

    payload = bytearray(SCHEMA_HEADER_SIZE)
    struct.pack_into("<2I", payload, 0, len(rows), len(pages))
    relocations = [
        relocation(8, symbol, SCHEMA_HEADER_SIZE),
        relocation(12, symbol, rows_offset),
    ]
    point_font_routine(payload, relocations, 80, font_layout_enabled(selection),
                       "v2_help_set", NATIVE_HELP_SET)
    row_start = 0
    for index, page in enumerate(pages):
        page_offset = len(payload)
        # The root page's rows form the first section and every child page's the second.
        sections = (len(page.rows), 0) if index == 0 else (0, len(page.rows))
        payload.extend(struct.pack("<8I", row_start, len(page.rows), *sections,
                                   page.parent_page, page.parent_row, 0, 0))
        if page.heading_symbol is not None:
            relocations.append(relocation(page_offset + 6 * 4, page.heading_symbol))
        relocations.append(relocation(page_offset + 7 * 4, page.reset_symbol))
        row_start += len(page.rows)
    relocations.extend(relocation(16 + index * 4, name)
                       for index, name in enumerate(HEADER_SYMBOLS))

    table_offsets = {}
    offset = rows_offset + len(rows) * row_size
    for name, _symbols, _texts in VALUE_TABLES:
        table_offsets[name] = offset
        offset += VALUE_TABLE_SIZES[name] * 4
    text_pool_offset = offset

    for index, row in enumerate(rows):
        fields = list(row.encoded_fields())
        row_offset = rows_offset + index * row_size
        if row.runtime_option is not None or row.label is not None:
            option = row.runtime_option
            fields[label_field] = (option.label_reference if option is not None else 0) or 0
            fields[help_field] = (option.help_reference if option is not None else 0) or 0
            fields[value_field] = (option.values_reference if option is not None else 0) or 0
        elif row.flags & layout.custom_flags["chakra"]:
            fields[value_field] = 0
            relocations.append(relocation(row_offset + value_field * 4, symbol,
                                          table_offsets["chakra"]))
        elif row.row_id in custom_tables:
            field, table = custom_tables[row.row_id]
            for reference in references:
                fields[reference] = 0
            relocations.extend((
                relocation(row_offset + label_field * 4, f"mod_text_settings__{field}__label"),
                relocation(row_offset + help_field * 4, f"mod_text_settings__{field}__help"),
                relocation(row_offset + value_field * 4, symbol, table_offsets[table]),
            ))
        payload.extend(struct.pack(f"<{layout.field_count}I", *fields))

    if any(row.row_id in custom_tables or row.flags & layout.custom_flags["chakra"]
           for row in rows):
        text_pool = bytearray()
        for _name, symbols, texts in VALUE_TABLES:
            for label in symbols:
                if label is not None:
                    relocations.append(relocation(len(payload), label))
                payload.extend(bytes(4))
            for text in texts:
                relocations.append(relocation(len(payload), symbol,
                                              text_pool_offset + len(text_pool)))
                payload.extend(bytes(4))
                text_pool.extend(strings.encode(text) + b"\0")
        payload.extend(text_pool)

    _append_row_extensions(payload, relocations, rows, rows_offset, row_size,
                           references, symbol, strings)
    return PayloadFragment(
        owner=owner,
        symbol=symbol,
        kind="rodata",
        alignment=4,
        payload=bytes(payload),
        relocations=tuple(relocations),
    )


def _append_row_extensions(payload, relocations, rows, rows_offset, row_size,
                           references, symbol, strings):
    label_field, help_field, value_field = references

    def pointer(offset, target=None, addend=0):
        struct.pack_into("<I", payload, offset, 0)
        relocations.append(PayloadRelocation(offset=offset, kind="abs32",
                                            symbol=target or symbol, addend=addend))

    def text(value):
        offset = len(payload)
        payload.extend(strings.encode(value) + b"\0")
        return offset

    def align():
        payload.extend(b"\0" * (-len(payload) % 4))

    for index, row in enumerate(rows):
        offset = rows_offset + index * row_size
        links = row.value_pages
        if row.label is not None:
            pointer(offset + label_field * 4, addend=text(row.label))
            pointer(offset + help_field * 4, addend=text(row.help))
        if row.runtime_option is not None:
            option = row.runtime_option
            if option.label_reference is None:
                pointer(offset + label_field * 4, addend=text(option.label))
            if option.help_reference is None:
                pointer(offset + help_field * 4, addend=text(option.help))
            if option.values_reference is None:
                align()
                table = len(payload)
                payload.extend(b"\0" * (option.count * 4))
                pointer(offset + value_field * 4, addend=table)
                for value, label in enumerate(option.values):
                    pointer(table + value * 4, addend=text(label))
            pointer(offset + row_size - 4, target=f"{symbol}_option_{index}")

        if links:
            align()
            table = len(payload)
            targets = [0xFFFFFFFF] * row.option_count
            for value, page, _label in links:
                targets[value] = page
            payload.extend(struct.pack(f"<{len(targets)}I", *targets))
            pointer(offset + row_size - 8, addend=table)
            for value, _page, label in links:
                if label is None:
                    continue
                values = next(r for r in relocations
                              if r.offset == offset + value_field * 4)
                entry = values.addend + value * 4
                relocations[:] = [r for r in relocations if r.offset != entry]
                pointer(entry, addend=text(message("menu.open_value", label=label)))


def page_resource_fragments(pages, owner, symbol, selection):
    strings = ModStrings(selection)
    fragments = []
    for page in pages:
        if page.heading_text is not None:
            fragments.append(PayloadFragment(owner=owner, symbol=page.heading_symbol,
                kind="rodata", alignment=4, payload=strings.encode(page.heading_text) + b"\0"))
        fragments.append(PayloadFragment(owner=owner, symbol=page.reset_symbol,
            kind="rodata", alignment=4, payload=strings.encode(page.reset_text) + b"\0"))
    rows = tuple(row for page in pages for row in page.rows)
    option_symbols = {
        (row.runtime_option.getter, row.runtime_option.argument): f"{symbol}_option_{index}"
        for index, row in enumerate(rows) if row.runtime_option is not None
    }
    for index, row in enumerate(rows):
        option = row.runtime_option
        if option is not None:
            relocations = [
                PayloadRelocation(offset=0, kind="abs32", symbol=option.getter),
                PayloadRelocation(offset=4, kind="abs32", symbol=option.setter),
            ]
            if option.enabled_by is not None:
                relocations.append(PayloadRelocation(
                    offset=16, kind="abs32", symbol=option_symbols[option.enabled_by]))
            fragments.append(PayloadFragment(owner=owner, symbol=f"{symbol}_option_{index}",
                kind="data", alignment=4,
                payload=struct.pack("<5I", 0, 0, option.argument, option.default, 0),
                relocations=tuple(relocations)))
    return tuple(fragments)
