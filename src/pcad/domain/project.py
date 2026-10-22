"""Project file management (.pcad format)."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict
from pydantic import BaseModel, Field

from pcad.domain.errors import ProjectFileError

CURRENT_PROJECT_SCHEMA_VERSION = 1

class ProjectData(BaseModel):
    schema_version: int = CURRENT_PROJECT_SCHEMA_VERSION
    template_id: str
    template_version: str
    params: Dict[str, Any]
    material_id: str = "Al7075-T6"
    loads: Dict[str, float] = Field(default_factory=dict)
    app_version: str = "0.1.0"
    model_hash: str = ""
    created_at: str = Field(default_factory=lambda: datetime.now().isoformat())
    notes: str = ""

def save_project(project: ProjectData, path: Path) -> None:
    try:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            f.write(project.model_dump_json(indent=2))
    except Exception as e:
        raise ProjectFileError("err.project_save_failed", str(e))

def load_project(path: Path) -> ProjectData:
    try:
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"Project file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            raw_data = json.load(f)
        
        # Schema migration hook if schema_version differs
        schema_v = raw_data.get("schema_version", 1)
        if schema_v == 1:
            return ProjectData(**raw_data)
        else:
            raise ValueError(f"Unsupported project schema version: {schema_v}")
    except Exception as e:
        raise ProjectFileError("err.project_load_failed", str(e))
