from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    data_raw: Path
    data_processed: Path
    db_path: Path
    outputs: Path
    models: Path


def get_project_root() -> Path:
    current = Path(__file__).resolve()
    # src/parcelflow/config.py -> repo root
    return current.parents[2]


def get_paths(root: Path | None = None) -> ProjectPaths:
    root = root or get_project_root()
    data_raw = root / "data" / "raw"
    data_processed = root / "data" / "processed"
    outputs = root / "outputs"
    models = root / "models"
    db_path = root / "data" / "parcelflow.sqlite"
    return ProjectPaths(
        root=root,
        data_raw=data_raw,
        data_processed=data_processed,
        db_path=db_path,
        outputs=outputs,
        models=models,
    )


def ensure_dirs(paths: ProjectPaths) -> None:
    for path in [paths.data_raw, paths.data_processed, paths.outputs, paths.models, paths.db_path.parent]:
        path.mkdir(parents=True, exist_ok=True)
