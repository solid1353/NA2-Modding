from __future__ import annotations

import json
import math
import re
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path
from typing import TypeAlias


IDENTIFIER = re.compile(r"[a-z][a-z0-9_]*\Z")
NUMBER = re.compile(r"-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?(?:[eE][+-]?[0-9]+)?")


class CatalogSyntaxError(ValueError):
    pass


@dataclass(frozen=True)
class Token:
    kind: str
    value: object
    text: str
    line: int
    column: int


@dataclass(frozen=True)
class PrimitiveType:
    name: str


@dataclass(frozen=True)
class LiteralType:
    value: str | int | float | bool


@dataclass(frozen=True)
class NumericConstraint:
    operator: str
    first: int | float
    second: int | float | None = None


@dataclass(frozen=True)
class ConstrainedType:
    base: TypeExpression
    constraints: tuple[NumericConstraint, ...]


@dataclass(frozen=True)
class ObjectField:
    name: str
    value_type: TypeExpression
    optional: bool


@dataclass(frozen=True)
class ObjectType:
    fields: tuple[ObjectField, ...]


@dataclass(frozen=True)
class UnionType:
    branches: tuple[TypeExpression, ...]


TypeExpression: TypeAlias = (
    PrimitiveType | LiteralType | ConstrainedType | ObjectType | UnionType
)


@dataclass(frozen=True)
class SettingNode:
    value_type: TypeExpression | None
    description: str
    patches: tuple[str, ...]


@dataclass(frozen=True)
class ContainerField:
    name: str
    node: CatalogNodeExpression


@dataclass(frozen=True)
class ContainerNode:
    fields: tuple[ContainerField, ...]
    description: str = ""


@dataclass(frozen=True)
class UnionNode:
    branches: tuple[CatalogNodeExpression, ...]


CatalogNodeExpression: TypeAlias = SettingNode | ContainerNode | UnionNode


def _syntax(path: Path, token: Token, message: str) -> CatalogSyntaxError:
    return CatalogSyntaxError(
        f"{path}:{token.line}:{token.column}: {message}"
    )


def _tokens(path: Path, text: str) -> tuple[Token, ...]:
    result: list[Token] = []
    index = 0
    line = 1
    column = 1
    symbols = set("{}[]:,<>?|&()")
    while index < len(text):
        character = text[index]
        if character in " \t\r\n":
            if character == "\n":
                line += 1
                column = 1
            else:
                column += 1
            index += 1
            continue
        if text.startswith("//", index):
            newline = text.find("\n", index + 2)
            if newline < 0:
                break
            column = 1
            line += 1
            index = newline + 1
            continue
        token_line = line
        token_column = column
        if text.startswith("..", index):
            result.append(Token("..", "..", "..", line, column))
            index += 2
            column += 2
            continue
        if text.startswith(">=", index) or text.startswith("<=", index):
            value = text[index : index + 2]
            result.append(Token(value, value, value, line, column))
            index += 2
            column += 2
            continue
        if character in symbols:
            result.append(Token(character, character, character, line, column))
            index += 1
            column += 1
            continue
        if character == '"':
            end = index + 1
            escaped = False
            while end < len(text):
                current = text[end]
                if current == "\n" and not escaped:
                    raise CatalogSyntaxError(
                        f"{path}:{line}:{column}: unterminated string literal"
                    )
                if current == '"' and not escaped:
                    break
                if current == "\\" and not escaped:
                    escaped = True
                else:
                    escaped = False
                end += 1
            if end >= len(text):
                raise CatalogSyntaxError(
                    f"{path}:{line}:{column}: unterminated string literal"
                )
            raw = text[index : end + 1]
            try:
                value = json.loads(raw)
            except json.JSONDecodeError as exc:
                raise CatalogSyntaxError(
                    f"{path}:{line}:{column}: invalid string literal"
                ) from exc
            result.append(Token("STRING", value, raw, line, column))
            index = end + 1
            column += len(raw)
            continue
        number = NUMBER.match(text, index)
        if number is not None:
            raw = number.group(0)
            if any(marker in raw for marker in ".eE"):
                value: int | float = float(raw)
                if not math.isfinite(value):
                    raise CatalogSyntaxError(
                        f"{path}:{line}:{column}: numeric literal must be finite"
                    )
            else:
                value = int(raw)
            result.append(Token("NUMBER", value, raw, line, column))
            index = number.end()
            column += len(raw)
            continue
        if character.isalpha() or character == "_":
            end = index + 1
            while end < len(text) and (
                text[end].isalnum() or text[end] == "_"
            ):
                end += 1
            raw = text[index:end]
            if raw == "true":
                result.append(Token("BOOL", True, raw, line, column))
            elif raw == "false":
                result.append(Token("BOOL", False, raw, line, column))
            else:
                result.append(Token("IDENT", raw, raw, line, column))
            index = end
            column += len(raw)
            continue
        raise CatalogSyntaxError(
            f"{path}:{line}:{column}: unsupported character {character!r}"
        )
    result.append(Token("EOF", None, "", line, column))
    return tuple(result)


class _Parser:
    def __init__(self, path: Path, text: str):
        self.path = path
        self.tokens = _tokens(path, text)
        self.index = 0

    @property
    def current(self) -> Token:
        return self.tokens[self.index]

    def accept(self, kind: str) -> Token | None:
        if self.current.kind != kind:
            return None
        token = self.current
        self.index += 1
        return token

    def expect(self, kind: str, message: str | None = None) -> Token:
        token = self.accept(kind)
        if token is None:
            raise _syntax(
                self.path,
                self.current,
                message or f"expected {kind!r}, found {self.current.text!r}",
            )
        return token

    def key(self) -> str:
        token = self.current
        if token.kind not in {"IDENT", "STRING"}:
            raise _syntax(self.path, token, "expected an object key")
        self.index += 1
        value = str(token.value)
        if not value:
            raise _syntax(self.path, token, "object key must be nonempty")
        return value

    def parse(self) -> ContainerNode:
        node = self.node_object()
        self.expect("EOF", "unexpected content after catalog root")
        validate_node(node, str(self.path))
        return node

    def node_expression(self) -> CatalogNodeExpression:
        branches = [self.node_primary()]
        while self.accept("|") is not None:
            branches.append(self.node_primary())
        if len(branches) == 1:
            return branches[0]
        flattened: list[CatalogNodeExpression] = []
        for branch in branches:
            if isinstance(branch, UnionNode):
                flattened.extend(branch.branches)
            else:
                flattened.append(branch)
        return UnionNode(tuple(flattened))

    def node_primary(self) -> CatalogNodeExpression:
        if self.current.kind == "IDENT" and self.current.value == "setting":
            return self.setting()
        if self.current.kind == "{":
            return self.node_object()
        if self.accept("(") is not None:
            node = self.node_expression()
            self.expect(")")
            return node
        raise _syntax(
            self.path,
            self.current,
            "expected setting, object, or parenthesized catalog node",
        )

    def setting(self) -> SettingNode:
        self.expect("IDENT")
        value_type: TypeExpression | None = None
        if self.accept("<") is not None:
            value_type = self.type_expression()
            self.expect(">", "expected '>' after setting type")
        self.expect("{", "expected setting body")
        description: str | None = None
        patches: tuple[str, ...] | None = None
        seen: set[str] = set()
        while self.current.kind != "}":
            key_token = self.current
            key = self.key()
            if key in seen:
                raise _syntax(self.path, key_token, f"duplicate setting field {key!r}")
            seen.add(key)
            self.expect(":")
            if key == "description":
                description = str(
                    self.expect("STRING", "setting description must be a string").value
                )
            elif key == "patches":
                patches = self.string_array()
            else:
                raise _syntax(
                    self.path,
                    key_token,
                    f"unsupported setting field {key!r}",
                )
            if self.accept(",") is None and self.current.kind != "}":
                raise _syntax(self.path, self.current, "expected ',' or '}'")
        self.expect("}")
        if description is None or not description.strip():
            raise _syntax(
                self.path,
                self.current,
                "every setting requires a nonempty description",
            )
        if patches is None or not patches:
            raise _syntax(
                self.path,
                self.current,
                "every setting requires a nonempty patches array",
            )
        if len(patches) != len(set(patches)):
            raise _syntax(self.path, self.current, "setting patches must be unique")
        return SettingNode(value_type, description, patches)

    def string_array(self) -> tuple[str, ...]:
        self.expect("[")
        result: list[str] = []
        while self.current.kind != "]":
            result.append(
                str(self.expect("STRING", "array items must be strings").value)
            )
            if self.accept(",") is None and self.current.kind != "]":
                raise _syntax(self.path, self.current, "expected ',' or ']'")
        self.expect("]")
        return tuple(result)

    def node_object(self) -> ContainerNode:
        self.expect("{")
        fields: list[ContainerField] = []
        description = ""
        seen: set[str] = set()
        while self.current.kind != "}":
            key_token = self.current
            key = self.key()
            if key in seen:
                raise _syntax(self.path, key_token, f"duplicate object key {key!r}")
            seen.add(key)
            self.expect(":")
            if key == "description":
                description = str(
                    self.expect("STRING", "description must be a string").value
                )
                if not description.strip():
                    raise _syntax(
                        self.path, key_token, "description must be nonempty"
                    )
            else:
                fields.append(ContainerField(key, self.node_expression()))
            if self.accept(",") is None and self.current.kind != "}":
                raise _syntax(self.path, self.current, "expected ',' or '}'")
        self.expect("}")
        if not fields:
            raise _syntax(
                self.path,
                self.current,
                "catalog object must contain at least one selectable field",
            )
        return ContainerNode(tuple(fields), description)

    def type_expression(self) -> TypeExpression:
        branches = [self.intersection_type()]
        while self.accept("|") is not None:
            branches.append(self.intersection_type())
        if len(branches) == 1:
            return branches[0]
        flattened: list[TypeExpression] = []
        for branch in branches:
            if isinstance(branch, UnionType):
                flattened.extend(branch.branches)
            else:
                flattened.append(branch)
        return UnionType(tuple(flattened))

    def intersection_type(self) -> TypeExpression:
        value = self.type_primary()
        constraints: list[NumericConstraint] = []
        while self.accept("&") is not None:
            constraints.append(self.numeric_constraint())
        if constraints:
            return ConstrainedType(value, tuple(constraints))
        return value

    def type_primary(self) -> TypeExpression:
        token = self.current
        if token.kind == "IDENT":
            self.index += 1
            if token.value not in {"bool", "int", "decimal", "string"}:
                raise _syntax(
                    self.path, token, f"unsupported type name {token.value!r}"
                )
            return PrimitiveType(str(token.value))
        if token.kind in {"STRING", "NUMBER", "BOOL"}:
            self.index += 1
            return LiteralType(token.value)  # type: ignore[arg-type]
        if token.kind == "{":
            return self.object_type()
        if self.accept("(") is not None:
            value = self.type_expression()
            self.expect(")", "expected ')' after type expression")
            return value
        raise _syntax(self.path, token, "expected a type expression")

    def object_type(self) -> ObjectType:
        self.expect("{")
        fields: list[ObjectField] = []
        seen: set[str] = set()
        while self.current.kind != "}":
            key_token = self.current
            key = self.key()
            if key in seen:
                raise _syntax(self.path, key_token, f"duplicate type field {key!r}")
            seen.add(key)
            optional = self.accept("?") is not None
            self.expect(":")
            fields.append(ObjectField(key, self.type_expression(), optional))
            if self.accept(",") is None and self.current.kind != "}":
                raise _syntax(self.path, self.current, "expected ',' or '}'")
        self.expect("}")
        if not fields:
            raise _syntax(self.path, self.current, "object type must not be empty")
        return ObjectType(tuple(fields))

    def numeric_constraint(self) -> NumericConstraint:
        token = self.current
        if token.kind == "IDENT" and token.value == "step":
            self.index += 1
            number = self.expect("NUMBER", "step constraint requires a number")
            return NumericConstraint("step", number.value)  # type: ignore[arg-type]
        if token.kind in {">", ">=", "<", "<="}:
            self.index += 1
            number = self.expect("NUMBER", "numeric comparison requires a number")
            return NumericConstraint(token.kind, number.value)  # type: ignore[arg-type]
        first = self.expect("NUMBER", "numeric constraint requires a comparison or range")
        self.expect("..", "numeric range requires '..'")
        second = self.expect("NUMBER", "numeric range requires an upper bound")
        return NumericConstraint(
            "range",
            first.value,  # type: ignore[arg-type]
            second.value,  # type: ignore[arg-type]
        )


def parse_catalog(path: Path) -> ContainerNode:
    path = path.resolve()
    try:
        text = path.read_text(encoding="utf-8")
    except UnicodeError as exc:
        raise ValueError(f"Catalog source is not UTF-8: {path}") from exc
    return _Parser(path, text).parse()


def _json_equal(left: object, right: object) -> bool:
    if isinstance(left, bool) or isinstance(right, bool):
        return type(left) is type(right) and left == right
    return left == right


def _number(value: object) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    result = float(value)
    return result if math.isfinite(result) else None


def _fraction(value: int | float) -> Fraction:
    return Fraction(str(value))


def _constraint_matches(constraint: NumericConstraint, value: int | float) -> bool:
    numeric = _fraction(value)
    first = _fraction(constraint.first)
    if constraint.operator == "range":
        assert constraint.second is not None
        return first <= numeric <= _fraction(constraint.second)
    if constraint.operator == ">":
        return numeric > first
    if constraint.operator == ">=":
        return numeric >= first
    if constraint.operator == "<":
        return numeric < first
    if constraint.operator == "<=":
        return numeric <= first
    if constraint.operator == "step":
        return first > 0 and numeric % first == 0
    raise ValueError(f"Unsupported numeric constraint: {constraint.operator}")


def matches_type(value_type: TypeExpression, value: object) -> bool:
    if isinstance(value_type, PrimitiveType):
        if value_type.name == "bool":
            return isinstance(value, bool)
        if value_type.name == "string":
            return isinstance(value, str)
        number = _number(value)
        if number is None:
            return False
        if value_type.name == "int":
            return number.is_integer()
        if value_type.name == "decimal":
            return True
        raise ValueError(f"Unsupported primitive type: {value_type.name}")
    if isinstance(value_type, LiteralType):
        return _json_equal(value_type.value, value)
    if isinstance(value_type, ConstrainedType):
        number = _number(value)
        return (
            number is not None
            and matches_type(value_type.base, value)
            and all(_constraint_matches(item, number) for item in value_type.constraints)
        )
    if isinstance(value_type, ObjectType):
        if not isinstance(value, dict):
            return False
        fields = {field.name: field for field in value_type.fields}
        if set(value) - set(fields):
            return False
        if any(not field.optional and field.name not in value for field in fields.values()):
            return False
        return all(
            key in fields and matches_type(fields[key].value_type, item)
            for key, item in value.items()
        )
    if isinstance(value_type, UnionType):
        return sum(matches_type(branch, value) for branch in value_type.branches) == 1
    raise TypeError(type(value_type))


@dataclass(frozen=True)
class _Interval:
    lower: Fraction | None = None
    lower_inclusive: bool = True
    upper: Fraction | None = None
    upper_inclusive: bool = True
    step: Fraction | None = None


def _common_step(left: Fraction, right: Fraction) -> Fraction:
    return Fraction(
        math.lcm(left.numerator, right.numerator),
        math.gcd(left.denominator, right.denominator),
    )


def _numeric_interval(value_type: TypeExpression) -> _Interval | None:
    if isinstance(value_type, PrimitiveType) and value_type.name in {"int", "decimal"}:
        return _Interval(
            step=Fraction(1) if value_type.name == "int" else None,
        )
    if not isinstance(value_type, ConstrainedType):
        return None
    base = _numeric_interval(value_type.base)
    if base is None:
        return None
    lower = base.lower
    lower_inclusive = base.lower_inclusive
    upper = base.upper
    upper_inclusive = base.upper_inclusive
    step = base.step
    for constraint in value_type.constraints:
        first = _fraction(constraint.first)
        if constraint.operator == "range":
            assert constraint.second is not None
            candidate_upper = _fraction(constraint.second)
            if lower is None or first > lower:
                lower = first
                lower_inclusive = True
            if upper is None or candidate_upper < upper:
                upper = candidate_upper
                upper_inclusive = True
        elif constraint.operator in {">", ">="}:
            inclusive = constraint.operator == ">="
            if lower is None or first > lower:
                lower = first
                lower_inclusive = inclusive
            elif first == lower:
                lower_inclusive = lower_inclusive and inclusive
        elif constraint.operator in {"<", "<="}:
            inclusive = constraint.operator == "<="
            if upper is None or first < upper:
                upper = first
                upper_inclusive = inclusive
            elif first == upper:
                upper_inclusive = upper_inclusive and inclusive
        elif constraint.operator == "step":
            assert first > 0
            step = first if step is None else _common_step(step, first)
        else:
            raise ValueError(f"Unsupported numeric constraint: {constraint.operator}")
    return _Interval(
        lower=lower,
        lower_inclusive=lower_inclusive,
        upper=upper,
        upper_inclusive=upper_inclusive,
        step=step,
    )


def _intersect_intervals(left: _Interval, right: _Interval) -> bool:
    lower = left.lower
    lower_inclusive = left.lower_inclusive
    if right.lower is not None and (
        lower is None or right.lower > lower
    ):
        lower = right.lower
        lower_inclusive = right.lower_inclusive
    elif right.lower is not None and right.lower == lower:
        lower_inclusive = lower_inclusive and right.lower_inclusive
    upper = left.upper
    upper_inclusive = left.upper_inclusive
    if right.upper is not None and (
        upper is None or right.upper < upper
    ):
        upper = right.upper
        upper_inclusive = right.upper_inclusive
    elif right.upper is not None and right.upper == upper:
        upper_inclusive = upper_inclusive and right.upper_inclusive
    if lower is not None and upper is not None:
        if lower > upper:
            return False
        if lower == upper:
            if not (lower_inclusive and upper_inclusive):
                return False
    if left.step is None:
        step = right.step
    elif right.step is None:
        step = left.step
    else:
        step = _common_step(left.step, right.step)
    if step is None:
        return True
    minimum: int | None = None
    maximum: int | None = None
    if lower is not None:
        scaled_lower = lower / step
        minimum = math.ceil(scaled_lower)
        if minimum == scaled_lower and not lower_inclusive:
            minimum += 1
    if upper is not None:
        scaled_upper = upper / step
        maximum = math.floor(scaled_upper)
        if maximum == scaled_upper and not upper_inclusive:
            maximum -= 1
    return minimum is None or maximum is None or minimum <= maximum


def types_overlap(left: TypeExpression, right: TypeExpression) -> bool:
    if isinstance(left, UnionType):
        return any(types_overlap(branch, right) for branch in left.branches)
    if isinstance(right, UnionType):
        return any(types_overlap(left, branch) for branch in right.branches)
    if isinstance(left, LiteralType):
        return matches_type(right, left.value)
    if isinstance(right, LiteralType):
        return matches_type(left, right.value)
    left_interval = _numeric_interval(left)
    right_interval = _numeric_interval(right)
    if left_interval is not None or right_interval is not None:
        return (
            left_interval is not None
            and right_interval is not None
            and _intersect_intervals(left_interval, right_interval)
        )
    if isinstance(left, PrimitiveType) and isinstance(right, PrimitiveType):
        return left.name == right.name
    if isinstance(left, ObjectType) and isinstance(right, ObjectType):
        left_fields = {field.name: field for field in left.fields}
        right_fields = {field.name: field for field in right.fields}
        left_required = {field.name for field in left.fields if not field.optional}
        right_required = {field.name for field in right.fields if not field.optional}
        if not left_required <= set(right_fields):
            return False
        if not right_required <= set(left_fields):
            return False
        for key in left_required | right_required:
            if not types_overlap(
                left_fields[key].value_type, right_fields[key].value_type
            ):
                return False
        return True
    return False


def _validate_type(value_type: TypeExpression, label: str) -> None:
    if isinstance(value_type, PrimitiveType):
        return
    if isinstance(value_type, LiteralType):
        return
    if isinstance(value_type, ConstrainedType):
        _validate_type(value_type.base, label)
        for constraint in value_type.constraints:
            if constraint.operator == "step" and constraint.first <= 0:
                raise ValueError(f"{label}: step constraint must be positive")
        interval = _numeric_interval(value_type)
        if interval is None:
            raise ValueError(f"{label}: '&' constraints require int or decimal")
        if not _intersect_intervals(interval, interval):
            raise ValueError(f"{label}: numeric constraints accept no values")
        return
    if isinstance(value_type, ObjectType):
        for field in value_type.fields:
            _validate_type(field.value_type, f"{label}.{field.name}")
        return
    if isinstance(value_type, UnionType):
        for index, branch in enumerate(value_type.branches):
            _validate_type(branch, f"{label} branch {index + 1}")
        for left_index, left in enumerate(value_type.branches):
            for right_index in range(left_index + 1, len(value_type.branches)):
                if types_overlap(left, value_type.branches[right_index]):
                    raise ValueError(
                        f"{label}: union branches {left_index + 1} and "
                        f"{right_index + 1} overlap"
                    )
        return
    raise TypeError(type(value_type))


def _accepts_top_level_boolean(value_type: TypeExpression) -> bool:
    return types_overlap(value_type, PrimitiveType("bool"))


def active_type(node: CatalogNodeExpression) -> TypeExpression:
    if isinstance(node, SettingNode):
        return LiteralType(True) if node.value_type is None else node.value_type
    if isinstance(node, ContainerNode):
        return ObjectType(
            tuple(
                ObjectField(
                    field.name,
                    UnionType((LiteralType(False), active_type(field.node))),
                    False,
                )
                for field in node.fields
            )
        )
    if isinstance(node, UnionNode):
        return UnionType(tuple(active_type(branch) for branch in node.branches))
    raise TypeError(type(node))


def validate_node(node: CatalogNodeExpression, label: str) -> None:
    if isinstance(node, SettingNode):
        if node.value_type is not None:
            _validate_type(node.value_type, label)
            if _accepts_top_level_boolean(node.value_type):
                raise ValueError(
                    f"{label}: direct boolean setting types are forbidden; "
                    "wrap bool in an object type"
                )
        return
    if isinstance(node, ContainerNode):
        for field in node.fields:
            if not IDENTIFIER.fullmatch(field.name):
                raise ValueError(
                    f"{label}: catalog key must be meaningful snake_case: "
                    f"{field.name!r}"
                )
            validate_node(field.node, f"{label}.{field.name}")
        return
    if isinstance(node, UnionNode):
        for index, branch in enumerate(node.branches):
            validate_node(branch, f"{label} branch {index + 1}")
        domains = [active_type(branch) for branch in node.branches]
        for left_index, left in enumerate(domains):
            for right_index in range(left_index + 1, len(domains)):
                if types_overlap(left, domains[right_index]):
                    raise ValueError(
                        f"{label}: catalog union branches {left_index + 1} and "
                        f"{right_index + 1} overlap"
                    )
        return
    raise TypeError(type(node))


def _type_text(value_type: TypeExpression, indent: int, precedence: int = 0) -> str:
    if isinstance(value_type, PrimitiveType):
        return value_type.name
    if isinstance(value_type, LiteralType):
        if isinstance(value_type.value, str):
            return json.dumps(value_type.value, ensure_ascii=False)
        if isinstance(value_type.value, bool):
            return "true" if value_type.value else "false"
        return str(value_type.value)
    if isinstance(value_type, ObjectType):
        lines = ["{"]
        for field in value_type.fields:
            optional = "?" if field.optional else ""
            lines.append(
                " " * (indent + 2)
                + f"{field.name}{optional}: "
                + _type_text(field.value_type, indent + 2)
                + ","
            )
        lines.append(" " * indent + "}")
        return "\n".join(lines)
    if isinstance(value_type, ConstrainedType):
        text = _type_text(value_type.base, indent, 2)
        for constraint in value_type.constraints:
            if constraint.operator == "range":
                text += f" & {constraint.first}..{constraint.second}"
            elif constraint.operator == "step":
                text += f" & step {constraint.first}"
            else:
                text += f" & {constraint.operator}{constraint.first}"
        return f"({text})" if precedence > 2 else text
    if isinstance(value_type, UnionType):
        text = " | ".join(_type_text(branch, indent, 1) for branch in value_type.branches)
        return f"({text})" if precedence > 1 else text
    raise TypeError(type(value_type))


def type_text(value_type: TypeExpression) -> str:
    """Return the canonical user-facing spelling of a catalog value type."""
    return _type_text(value_type, 0)


def _node_lines(
    node: CatalogNodeExpression,
    indent: int,
    *,
    include_patches: bool,
) -> list[str]:
    prefix = " " * indent
    if isinstance(node, SettingNode):
        setting = "setting"
        if node.value_type is not None:
            setting += f"<{_type_text(node.value_type, indent + 2)}>"
        lines = [setting + " {"]
        lines.append(
            " " * (indent + 2)
            + "description: "
            + json.dumps(node.description, ensure_ascii=False)
            + ","
        )
        if include_patches:
            lines.append(" " * (indent + 2) + "patches: [")
            for patch in node.patches:
                lines.append(
                    " " * (indent + 4)
                    + json.dumps(patch, ensure_ascii=False)
                    + ","
                )
            lines.append(" " * (indent + 2) + "],")
        lines.append(prefix + "}")
        return lines
    if isinstance(node, ContainerNode):
        lines = ["{"]
        if node.description:
            lines.append(
                " " * (indent + 2)
                + "description: "
                + json.dumps(node.description, ensure_ascii=False)
                + ","
            )
        for field in node.fields:
            child = _node_lines(field.node, indent + 2, include_patches=include_patches)
            lines.append(" " * (indent + 2) + f"{field.name}: " + child[0])
            lines.extend(child[1:-1])
            lines.append(child[-1] + ",")
        lines.append(prefix + "}")
        return lines
    if isinstance(node, UnionNode):
        lines: list[str] = []
        for index, branch in enumerate(node.branches):
            branch_lines = _node_lines(
                branch, indent, include_patches=include_patches
            )
            if index:
                lines.append(prefix + "|")
                lines.append(prefix + branch_lines[0])
                lines.extend(branch_lines[1:])
            else:
                lines.extend(branch_lines)
        return lines
    raise TypeError(type(node))


def serialize_catalog(
    features: dict[str, ContainerNode],
    *,
    include_patches: bool,
) -> str:
    lines = ["{", "  features: {"]
    for feature_id in sorted(features):
        node_lines = _node_lines(
            features[feature_id], 4, include_patches=include_patches
        )
        lines.append(f"    {feature_id}: " + node_lines[0])
        lines.extend(node_lines[1:-1])
        lines.append(node_lines[-1] + ",")
    lines.extend(["  },", "}", ""])
    return "\n".join(lines)


def serialize_feature(
    feature: ContainerNode,
    *,
    include_patches: bool = True,
) -> str:
    """Serialize one canonical per-feature catalog source."""
    return "\n".join(
        [*_node_lines(feature, 0, include_patches=include_patches), ""]
    )
