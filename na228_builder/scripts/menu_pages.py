"""Infer menu structure from the catalog and row order from configuration."""
from __future__ import annotations

import struct
from dataclasses import replace

from ..payload_builder.operations import PayloadFragment, PayloadRelocation
from .catalog_format import ContainerNode, SettingNode, ObjectType, LiteralType, UnionType
from .menu_options import PAGE_TITLES, menu_option_bindings


INGAME_PATH = ("features", "settings", "ingame")
SUBMENU_FLAG = 0x4000


def menu_title(name):
    return name.replace("_", " ").title()


def build_menu_pages(selection, root_path, row_bindings, row_type, page_type,
                     section_fields, prefix, first_generated_id):
    """Discover topology independently of native row and gameplay bindings."""
    ingame = next(field.node for field in selection.catalog["settings"].fields
                  if field.name == "ingame")
    definitions = {field.name: field.node for field in ingame.fields}
    selected = {node.path: node for node in selection.nodes}
    configuration = selected[INGAME_PATH].configured_value
    options = menu_option_bindings(selection)
    pages = []
    next_id = first_generated_id

    def allocate_row(**kwargs):
        nonlocal next_id
        if "section" in row_type.__dataclass_fields__:
            kwargs["section"] = 1
        row = row_type(row_id=next_id, local_offset=0xFFFFFFFF, **kwargs)
        next_id += 1
        return row

    def leaf_row(path):
        if path in row_bindings:
            return row_bindings[path]()
        if path not in options:
            raise ValueError(f"No menu value handler for {'.'.join(path)}")
        option = options[path]
        return allocate_row(option_count=len(option.values), default_value=option.default,
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
        configured = configuration
        for key in path[len(INGAME_PATH):]:
            configured = configured.get(key, {})
        names = tuple(configured)
        # Omitted optional values still expose their existing default rows.
        names += tuple(name for name in fields if name not in configured)
        return tuple((name, fields[name]) for name in names)

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
        pages.append(page_type(rows=(), **{field: 0 for field in section_fields},
            parent_page=parent_page, parent_row=parent_row,
            heading_symbol=f"{prefix}_page_{page_index}_heading" if page_index else None,
            heading_text=heading if page_index else None))
        rows = []
        for name, child in ordered_fields(definition, path):
            child_path = path + (name,)
            target = selected.get(child_path)
            reference = isinstance(child, SettingNode) and child.value_type is None
            if reference and (name not in definitions or name.endswith("_mode")):
                raise ValueError(f"No shared ingame definition for {'.'.join(child_path)}")
            if target is not None and not target.enabled:
                continue
            if reference:
                child_path = INGAME_PATH + (name,)
                child = definitions[name]
                if not selected[child_path].enabled:
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
                    label=label, help=f"Configure {label.lower()}.",
                    value_pages=((0, subpage, None),)))
        if page_index == 0 and "section" in row_type.__dataclass_fields__:
            rows = [replace(row, section=0) for row in rows]
        pages[page_index] = replace(pages[page_index], rows=tuple(rows),
            **{section_fields[0]: len(rows) if page_index == 0 else 0,
               section_fields[1]: len(rows) if page_index != 0 else 0})
        return page_index

    add_page(definitions[root_path[-1]], root_path)
    return tuple(pages)


def append_row_extensions(payload, relocations, rows, rows_offset, row_size,
                          label_field, help_field, value_field, symbol):
    def pointer(offset, target=None, addend=0):
        struct.pack_into("<I", payload, offset, 0)
        relocations.append(PayloadRelocation(offset=offset, kind="abs32",
                                            symbol=target or symbol, addend=addend))

    def text(value):
        offset = len(payload)
        payload.extend(value.encode("ascii") + b"\0")
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
            pointer(offset + label_field * 4, addend=text(option.label))
            pointer(offset + help_field * 4, addend=text(option.help))
            align()
            table = len(payload)
            payload.extend(b"\0" * (len(option.values) * 4))
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
                pointer(entry, addend=text(f"{label} <iconSQUARE>"))


def page_resource_fragments(pages, owner, symbol):
    fragments = []
    for page in pages:
        if page.heading_text is not None:
            fragments.append(PayloadFragment(owner=owner, symbol=page.heading_symbol,
                kind="rodata", alignment=4, payload=page.heading_text.encode("ascii") + b"\0"))
    for index, row in enumerate(row for page in pages for row in page.rows):
        option = row.runtime_option
        if option is not None:
            fragments.append(PayloadFragment(owner=owner, symbol=f"{symbol}_option_{index}",
                kind="data", alignment=4,
                payload=struct.pack("<4I", 0, 0, option.argument, option.default),
                relocations=(
                    PayloadRelocation(offset=0, kind="abs32", symbol=option.getter),
                    PayloadRelocation(offset=4, kind="abs32", symbol=option.setter),
                )))
    return tuple(fragments)
