from __future__ import annotations

from pathlib import Path, PurePosixPath
from typing import Protocol

from .cvm import CvmIso
from ..image_assembler.iso9660 import Iso9660, IsoRecord, normalize_iso_path


class IsoFileView(Protocol):
    by_path: dict[str, IsoRecord]

    def read_file(self, record: IsoRecord) -> bytes: ...


def read_root_file(root: Path, path: str | PurePosixPath) -> bytes:
    """Read one normalized game file from an extraction or original ISO."""
    normalized = normalize_iso_path(PurePosixPath(path).as_posix())
    root = root.resolve()
    if root.is_dir():
        candidate = root.joinpath(*PurePosixPath(normalized).parts)
        if not candidate.is_file():
            raise FileNotFoundError(f"Extracted root has no file {normalized}: {root}")
        return candidate.read_bytes()
    if root.is_file():
        image = Iso9660(root)
        record = image.by_path.get(normalized)
        if record is None or record.is_dir:
            raise FileNotFoundError(f"ISO has no file {normalized}: {root}")
        return image.read_file(record)
    raise FileNotFoundError(root)


def cvm_members(root: Path) -> tuple[IsoFileView, bytes]:
    """Open DATA.CVM members from an extraction or directly from an outer ISO."""
    root = root.resolve()
    if root.is_dir():
        cvm_root = root / "DATA" / "DATA.CVM.files"
        return (
            Iso9660(cvm_root / "DATA.CVM.iso"),
            (cvm_root / "DATA.CVM.hdr").read_bytes(),
        )
    if root.is_file():
        inner = CvmIso.from_iso(Iso9660(root))
        return inner, inner.header
    raise FileNotFoundError(root)
