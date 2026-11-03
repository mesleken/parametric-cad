"""IPC Protocol dataclasses and JSON serialization for UI-Worker communication."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field
from pcad.domain.template import CheckResult, PhysicsResult

class BuildRequest(BaseModel):
    req_id: str
    source: Literal["template", "code"] = "template"
    template_id: Optional[str] = None
    template_version: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    code: Optional[str] = None
    material_id: str = "Al7075-T6"
    loads: Dict[str, float] = Field(default_factory=dict)
    quality: Literal["preview", "export"] = "preview"

class BuildResult(BaseModel):
    req_id: str
    model_hash: str
    mesh_path: str
    physics: PhysicsResult
    checks: List[CheckResult] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    timings_ms: Dict[str, float] = Field(default_factory=dict)

class WorkerError(BaseModel):
    req_id: str
    kind: Literal["param_invalid", "geometry_invalid", "code_error", "timeout", "memory", "kernel_crash"]
    message_key: str
    detail: str = ""
    line_no: Optional[int] = None
    line_text: Optional[str] = None
    hint: Optional[str] = None

class ExportRequest(BaseModel):
    req_id: str
    model_hash: str
    export_format: Literal["step", "stl", "png", "pdf"]
    output_path: str
    linear_deflection: float = 0.05
    angular_deflection: float = 0.1
    # On-demand rebuild metadata if cache miss (B18, B19)
    source: Literal["template", "code"] = "template"
    template_id: Optional[str] = None
    template_version: Optional[str] = None
    params: Dict[str, Any] = Field(default_factory=dict)
    code: Optional[str] = None
    material_id: str = "Al7075-T6"
    loads: Dict[str, float] = Field(default_factory=dict)

class ExportResult(BaseModel):
    req_id: str
    output_path: str
    success: bool
    error: str = ""
