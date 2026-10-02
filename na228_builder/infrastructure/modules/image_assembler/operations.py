from __future__ import annotations

from dataclasses import dataclass

from .iso9660 import IsoInsertion
from .udf import UdfRename


@dataclass(frozen=True)
class FileReplacement:
    path: str
    expected: bytes
    replacement: bytes
    owner: str
    reason: str


@dataclass(frozen=True)
class FileInsertion:
    path: str
    payload: bytes
    owner: str
    reason: str


@dataclass(frozen=True)
class FileRename:
    source_path: str
    replacement_path: str
    owner: str
    reason: str


@dataclass(frozen=True)
class AssemblyPlan:
    replacements: tuple[FileReplacement, ...] = ()
    insertions: tuple[FileInsertion, ...] = ()
    renames: tuple[FileRename, ...] = ()


@dataclass(frozen=True)
class AssemblyResult:
    insertions: tuple[IsoInsertion, ...]
    iso9660_renames: tuple[dict[str, object], ...]
    udf_renames: tuple[UdfRename, ...]
