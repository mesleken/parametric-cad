"""Project file management (.pcad format)."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from pcad.domain.errors import ProjectFileError

CURRENT_PROJECT_SCHEMA_VERSION = 2

class ProjectData(BaseModel):
    schema_version: int = CURRENT_PROJECT_SCHEMA_VERSION
    kind: str = "template"  # "template" or "code"
    template_id: Optional[str] = None
    template_version: Optional[str] = None
    code: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    material_id: str = "Al7075-T6"
    loads: Dict[str, float] = Field(default_factory=dict)
    app_version: str = "0.3.0"
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
        
        schema_v = raw_data.get("schema_version", 1)
        if schema_v == 1:
            # Upgrade v1 project
            raw_data["schema_version"] = 2
            raw_data.setdefault("kind", "template")
            return ProjectData(**raw_data)
        elif schema_v == 2:
            return ProjectData(**raw_data)
        else:
            raise ValueError(f"Unsupported project schema version: {schema_v}")
    except Exception as e:
        raise ProjectFileError("err.project_load_failed", str(e))
