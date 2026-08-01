from __future__ import annotations

import sys
from pathlib import Path


REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
if str(REPOSITORY_ROOT) not in sys.path:
    sys.path.insert(0, str(REPOSITORY_ROOT))

from scripts.lib.project_paths import ProjectPaths, load_project_paths


PROJECT_PATHS: ProjectPaths = load_project_paths(REPOSITORY_ROOT)

__all__ = ["PROJECT_PATHS", "ProjectPaths", "load_project_paths"]
