"""Final physical image assembly and verification infrastructure."""

from .assembler import assemble_image, staged_output_image
from .operations import (
    AssemblyPlan,
    AssemblyResult,
    FileInsertion,
    FileRename,
    FileReplacement,
    IsoFileRef,
    IsoRangeRef,
)

__all__ = [
    "AssemblyPlan",
    "AssemblyResult",
    "FileInsertion",
    "FileRename",
    "FileReplacement",
    "IsoFileRef",
    "IsoRangeRef",
    "assemble_image",
    "staged_output_image",
]
